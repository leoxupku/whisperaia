import time
import pyperclip
from pynput.keyboard import Controller, Key


class TextInjector:
    def __init__(self):
        self._keyboard = Controller()

    def inject(self, text: str):
        pyperclip.copy(text)
        time.sleep(0.08)  # let clipboard settle
        with self._keyboard.pressed(Key.cmd):
            self._keyboard.tap("v")
