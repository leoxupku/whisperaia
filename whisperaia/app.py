import threading
import time

import pyperclip
from pynput import keyboard

from .audio import AudioRecorder
from .hotkey import HotkeyListener
from .injector import TextInjector
from .postprocess import OllamaPostProcessor
from .transcribe import WhisperTranscriber
from .vocabulary import PersonalVocabulary

CORRECTION_KEY = keyboard.Key.cmd_r
CORRECTION_WINDOW = 30  # seconds after last transcription to accept correction


class WhisperAIA:
    def __init__(self):
        self._recorder = AudioRecorder()
        self._transcriber = WhisperTranscriber()
        self._postprocessor = OllamaPostProcessor()
        self._injector = TextInjector()
        self._vocab = PersonalVocabulary()
        self._hotkey = HotkeyListener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._correction_listener = keyboard.Listener(on_press=self._on_correction_key)
        self._processing = False
        self._last_raw: str = ""
        self._last_ts: float = 0.0

    def run(self):
        print("\n✅ WhisperAIA 就绪")
        print("按住右 Option 说话，松开自动转写并粘贴")
        print("发现识别错误？改好后选中文本 Cmd+C，再按右 Command 提交纠错\n")
        self._hotkey.start()
        self._correction_listener.start()
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self._hotkey.stop()
            self._correction_listener.stop()
            print("\n已退出")

    def _on_press(self):
        if self._processing:
            return
        print("🎙️  录音中...")
        self._recorder.start()

    def _on_release(self):
        audio = self._recorder.stop()
        self._release_ts = time.perf_counter()
        if not self._processing:
            self._processing = True
            threading.Thread(target=self._process, args=(audio,), daemon=True).start()

    def _process(self, audio):
        try:
            t0 = self._release_ts

            t1 = time.perf_counter()
            raw = self._transcriber.transcribe(audio)
            t2 = time.perf_counter()

            if not raw:
                print("（未检测到语音）")
                return

            # Stage 1: direct dictionary substitution (deterministic, fast)
            substituted = self._vocab.apply_substitutions(raw)
            # Stage 2: LLM with word-level correction examples as context
            word_corrections = self._vocab.get_top_word_corrections(limit=10)
            corrected = self._postprocessor.process(substituted, word_corrections)
            t3 = time.perf_counter()

            self._injector.inject(corrected)
            t4 = time.perf_counter()

            self._last_raw = raw
            self._last_ts = time.time()

            print(f"原始: {raw}")
            print(f"修正: {corrected}")
            print(
                f"⏱  Whisper {t2-t1:.2f}s | LLM {t3-t2:.2f}s | 注入 {t4-t3:.2f}s"
                f" | 总计 {t4-t0:.2f}s\n"
            )
            if corrected != raw:
                self._vocab.record(raw, corrected)
        finally:
            self._processing = False

    def _on_correction_key(self, key):
        if key != CORRECTION_KEY:
            return
        if not self._last_raw:
            return
        if time.time() - self._last_ts > CORRECTION_WINDOW:
            print("[纠错] 距上次转写超过30秒，请重新说话后再提交纠错")
            return
        user_correction = pyperclip.paste().strip()
        if not user_correction:
            print("[纠错] 剪贴板为空，请先选中改好的文本并 Cmd+C")
            return
        if user_correction == self._last_raw:
            print("[纠错] 内容和原始转写相同，无需记录")
            return
        self._vocab.record(self._last_raw, user_correction)
        print(f"[✅ 已记录纠错]")
        print(f"  原始: {self._last_raw}")
        print(f"  修正: {user_correction}\n")
        self._last_raw = ""  # prevent duplicate submissions
