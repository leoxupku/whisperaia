import threading
from typing import Callable
import Quartz

# macOS virtual key codes
VK_RIGHT_OPTION = 61
VK_RIGHT_COMMAND = 54

# Device-specific right-side modifier bits (IOLLEvent.h)
# Distinguishes right vs left when both sides are held simultaneously.
_NX_DEVICERCMDKEYMASK = 0x10
_NX_DEVICERALTKEYMASK = 0x40

_KEY_FLAG: dict[int, int] = {
    VK_RIGHT_OPTION: _NX_DEVICERALTKEYMASK,
    VK_RIGHT_COMMAND: _NX_DEVICERCMDKEYMASK,
}


class GlobalKeyMonitor:
    """
    CGEventTap-based global keyboard monitor.

    All Quartz setup runs in a dedicated background thread with its own
    CFRunLoop, so it never interferes with tkinter's run loop.
    Callbacks fire on that background thread; callers must be thread-safe
    (WhisperAIAWindow.set_state uses root.after internally, so it's fine).
    """

    def __init__(self):
        self._handlers: dict[int, dict] = {}
        self._run_loop = None
        self._ready = threading.Event()
        self._start_error: Exception | None = None

    def register(
        self,
        keycode: int,
        on_press: Callable | None = None,
        on_release: Callable | None = None,
    ):
        self._handlers[keycode] = {
            "on_press": on_press,
            "on_release": on_release,
            "held": False,
        }

    def start(self):
        """Start monitoring. Blocks briefly until the tap is set up."""
        threading.Thread(target=self._run, daemon=True).start()
        self._ready.wait(timeout=3)
        if self._start_error:
            raise self._start_error

    def stop(self):
        if self._run_loop:
            Quartz.CFRunLoopStop(self._run_loop)
            self._run_loop = None

    def _run(self):
        mask = Quartz.CGEventMaskBit(Quartz.kCGEventFlagsChanged)
        tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionListenOnly,
            mask,
            self._callback,
            None,
        )
        if tap is None:
            self._start_error = PermissionError(
                "无法创建键盘监听器。\n"
                "请前往「系统设置 → 隐私与安全性 → 辅助功能」授权此应用。"
            )
            self._ready.set()
            return

        self._run_loop = Quartz.CFRunLoopGetCurrent()
        src = Quartz.CFMachPortCreateRunLoopSource(None, tap, 0)
        Quartz.CFRunLoopAddSource(self._run_loop, src, Quartz.kCFRunLoopDefaultMode)
        Quartz.CGEventTapEnable(tap, True)
        self._ready.set()        # unblock start()
        Quartz.CFRunLoopRun()    # blocks until stop()

    def _callback(self, proxy, event_type, event, refcon):
        if event_type != Quartz.kCGEventFlagsChanged:
            return event

        keycode = int(
            Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
        )
        if keycode not in self._handlers:
            return event

        handler = self._handlers[keycode]
        flag_mask = _KEY_FLAG.get(keycode, 0)
        is_pressed = bool(int(Quartz.CGEventGetFlags(event)) & flag_mask)

        if is_pressed and not handler["held"]:
            handler["held"] = True
            if handler["on_press"]:
                handler["on_press"]()
        elif not is_pressed and handler["held"]:
            handler["held"] = False
            if handler["on_release"]:
                handler["on_release"]()

        return event
