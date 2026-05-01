import threading
import time

import pyperclip

from .audio import AudioRecorder
from .gui import AppState, WhisperAIAWindow
from .injector import TextInjector
from .keyboard_monitor import GlobalKeyMonitor, VK_RIGHT_OPTION, VK_RIGHT_COMMAND
from .postprocess import OllamaPostProcessor
from .transcribe import WhisperTranscriber
from .vocabulary import PersonalVocabulary

CORRECTION_WINDOW = 30  # seconds


class WhisperAIA:
    def __init__(self):
        self._window = WhisperAIAWindow()
        self._processing = False
        self._last_raw = ""
        self._last_ts = 0.0
        self._release_ts = 0.0
        self._recorder: AudioRecorder | None = None
        self._transcriber: WhisperTranscriber | None = None
        self._postprocessor: OllamaPostProcessor | None = None
        self._injector: TextInjector | None = None
        self._vocab: PersonalVocabulary | None = None
        self._monitor: GlobalKeyMonitor | None = None

    def run(self):
        threading.Thread(target=self._load_models, daemon=True).start()
        self._window.run()

    def _load_models(self):
        self._recorder = AudioRecorder()
        self._transcriber = WhisperTranscriber()
        self._postprocessor = OllamaPostProcessor()
        self._injector = TextInjector()
        self._vocab = PersonalVocabulary()
        try:
            monitor = GlobalKeyMonitor()
            monitor.register(VK_RIGHT_OPTION, on_press=self._on_press, on_release=self._on_release)
            monitor.register(VK_RIGHT_COMMAND, on_press=self._on_correction)
            monitor.start()
            self._monitor = monitor
            self._window.set_state(AppState.IDLE)
        except PermissionError as e:
            self._window.set_state(AppState.IDLE, message=str(e))

    def _on_press(self):
        if self._processing:
            return
        self._window.set_state(AppState.RECORDING)
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
            self._window.set_state(AppState.PROCESSING)

            t1 = time.perf_counter()
            raw = self._transcriber.transcribe(audio)
            t2 = time.perf_counter()

            if not raw:
                self._window.set_state(AppState.IDLE, message="就绪  ·  未检测到语音")
                return

            substituted = self._vocab.apply_substitutions(raw)
            word_corrections = self._vocab.get_top_word_corrections(limit=10)
            corrected = self._postprocessor.process(substituted, word_corrections)
            t3 = time.perf_counter()

            self._injector.inject(corrected)
            t4 = time.perf_counter()

            self._last_raw = raw
            self._last_ts = time.time()

            timing = (
                f"Whisper {t2 - t1:.2f}s  ·  LLM {t3 - t2:.2f}s  ·  总计 {t4 - t0:.2f}s"
            )
            self._window.set_state(
                AppState.IDLE, raw=raw, corrected=corrected, timing=timing
            )

            if corrected != raw:
                self._vocab.record(raw, corrected)
        finally:
            self._processing = False

    def _on_correction(self):
        if not self._last_raw:
            return
        if time.time() - self._last_ts > CORRECTION_WINDOW:
            self._window.set_state(AppState.IDLE, message="距上次转写超30秒，请重新说话后纠错")
            return
        user_correction = pyperclip.paste().strip()
        if not user_correction:
            self._window.set_state(AppState.IDLE, message="剪贴板为空，请先选中文本并 Cmd+C")
            return
        if user_correction == self._last_raw:
            self._window.set_state(AppState.IDLE, message="内容与原始转写相同，无需记录")
            return
        self._vocab.record(self._last_raw, user_correction)
        self._window.set_state(
            AppState.IDLE,
            message="✅ 纠错已记录",
            raw=self._last_raw,
            corrected=user_correction,
        )
        self._last_raw = ""
