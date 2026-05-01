import tkinter as tk
from enum import Enum, auto

# macOS SF Color palette
_BG = "#1c1c1e"
_BG2 = "#2c2c2e"
_FG = "#f2f2f7"
_FG_DIM = "#636366"
_GREEN = "#30d158"
_RED = "#ff453a"
_ORANGE = "#ff9f0a"


class AppState(Enum):
    LOADING = auto()
    IDLE = auto()
    RECORDING = auto()
    PROCESSING = auto()


class WhisperAIAWindow:
    def __init__(self):
        self._root = tk.Tk()
        self._root.title("WhisperAIA")
        self._root.configure(bg=_BG)
        self._root.resizable(False, False)
        self._root.attributes("-topmost", True)

        self._app_state = AppState.LOADING
        self._anim_id = None
        self._anim_step = 0
        self._drag_x = 0
        self._drag_y = 0

        self._build_ui()
        self._root.protocol("WM_DELETE_WINDOW", self._root.destroy)

    def _build_ui(self):
        # Title bar (doubles as drag handle)
        title_bar = tk.Frame(self._root, bg=_BG2)
        title_bar.pack(fill=tk.X)
        title_bar.bind("<ButtonPress-1>", self._drag_start)
        title_bar.bind("<B1-Motion>", self._drag_motion)

        tk.Label(
            title_bar, text="  🎤  WhisperAIA",
            bg=_BG2, fg=_FG, font=("Helvetica", 13, "bold"), pady=9, anchor="w",
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Status row
        status_row = tk.Frame(self._root, bg=_BG)
        status_row.pack(fill=tk.X, padx=14, pady=(10, 4))

        self._dot = tk.Label(
            status_row, text="●", bg=_BG, fg=_FG_DIM, font=("Helvetica", 18),
        )
        self._dot.pack(side=tk.LEFT)

        self._status_var = tk.StringVar(value="模型加载中，请稍候…")
        tk.Label(
            status_row, textvariable=self._status_var,
            bg=_BG, fg=_FG, font=("Helvetica", 12),
        ).pack(side=tk.LEFT, padx=8)

        # Divider
        tk.Frame(self._root, bg="#3a3a3c", height=1).pack(fill=tk.X, padx=14, pady=(2, 6))

        # Transcription area
        txt_frame = tk.Frame(self._root, bg=_BG)
        txt_frame.pack(fill=tk.X, padx=14)

        self._raw_var = tk.StringVar()
        self._raw_label = tk.Label(
            txt_frame, textvariable=self._raw_var,
            bg=_BG, fg=_FG_DIM, font=("Helvetica", 10),
            anchor="w", justify=tk.LEFT, wraplength=390,
        )
        self._raw_label.pack(fill=tk.X)

        self._corrected_var = tk.StringVar()
        tk.Label(
            txt_frame, textvariable=self._corrected_var,
            bg=_BG, fg=_FG, font=("Helvetica", 11),
            anchor="w", justify=tk.LEFT, wraplength=390,
        ).pack(fill=tk.X, pady=(1, 0))

        # Timing footer
        self._timing_var = tk.StringVar()
        tk.Label(
            self._root, textvariable=self._timing_var,
            bg=_BG, fg=_FG_DIM, font=("Helvetica", 9), anchor="w",
        ).pack(fill=tk.X, padx=14, pady=(6, 10))

    # ── Drag ──────────────────────────────────────────────────────────────────

    def _drag_start(self, event):
        self._drag_x = event.x_root - self._root.winfo_x()
        self._drag_y = event.y_root - self._root.winfo_y()

    def _drag_motion(self, event):
        self._root.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")

    # ── Public API (thread-safe) ───────────────────────────────────────────────

    def set_state(self, state: AppState, **kwargs):
        self._root.after(0, self._apply_state, state, kwargs)

    def _apply_state(self, state: AppState, kwargs: dict):
        self._app_state = state
        self._cancel_anim()

        if state == AppState.LOADING:
            self._dot.config(fg=_FG_DIM)
            self._status_var.set("模型加载中，请稍候…")
            self._anim_spinner()

        elif state == AppState.IDLE:
            self._dot.config(fg=_GREEN, text="●")
            self._status_var.set(kwargs.get("message", "就绪  ·  右 Option 说话"))
            if "raw" in kwargs:
                raw, corrected = kwargs["raw"], kwargs.get("corrected", "")
                self._raw_var.set(f"原始: {raw}" if raw != corrected else "")
                self._corrected_var.set(corrected)
            if "timing" in kwargs:
                self._timing_var.set(kwargs["timing"])

        elif state == AppState.RECORDING:
            self._status_var.set("录音中…")
            self._anim_pulse()

        elif state == AppState.PROCESSING:
            self._dot.config(fg=_ORANGE)
            self._status_var.set("转写处理中…")
            self._anim_spinner()

    # ── Animations ────────────────────────────────────────────────────────────

    def _cancel_anim(self):
        if self._anim_id:
            self._root.after_cancel(self._anim_id)
            self._anim_id = None
        self._dot.config(text="●")

    def _anim_spinner(self):
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

        def tick():
            if self._app_state in (AppState.LOADING, AppState.PROCESSING):
                self._dot.config(text=frames[self._anim_step % len(frames)])
                self._anim_step += 1
                self._anim_id = self._root.after(80, tick)

        self._anim_step = 0
        tick()

    def _anim_pulse(self):
        colors = [_RED, "#c43428", _RED, "#c43428"]

        def tick():
            if self._app_state == AppState.RECORDING:
                self._dot.config(fg=colors[self._anim_step % len(colors)])
                self._anim_step += 1
                self._anim_id = self._root.after(350, tick)

        self._anim_step = 0
        self._dot.config(text="●")
        tick()

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self):
        self._root.update_idletasks()
        sw = self._root.winfo_screenwidth()
        self._root.geometry(f"420x175+{sw - 450}+50")
        self._root.mainloop()
