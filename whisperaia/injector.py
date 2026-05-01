import time
import pyperclip
import Quartz

_kVK_ANSI_V = 9  # macOS virtual key code for 'V'


class TextInjector:
    def inject(self, text: str):
        pyperclip.copy(text)
        time.sleep(0.08)  # let clipboard settle
        src = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)
        for key_down in (True, False):
            ev = Quartz.CGEventCreateKeyboardEvent(src, _kVK_ANSI_V, key_down)
            Quartz.CGEventSetFlags(ev, Quartz.kCGEventFlagMaskCommand)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)
