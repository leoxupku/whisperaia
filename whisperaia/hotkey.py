from typing import Callable
from pynput import keyboard


class HotkeyListener:
    """Push-to-talk listener. Calls on_press when hotkey goes down, on_release when it comes up."""

    def __init__(self, on_press: Callable, on_release: Callable, key=keyboard.Key.alt_r):
        self.on_press = on_press
        self.on_release = on_release
        self.key = key
        self._held = False
        self._listener = keyboard.Listener(
            on_press=self._handle_press,
            on_release=self._handle_release,
        )

    def start(self):
        self._listener.start()

    def stop(self):
        self._listener.stop()

    def _handle_press(self, key):
        if key == self.key and not self._held:
            self._held = True
            self.on_press()

    def _handle_release(self, key):
        if key == self.key and self._held:
            self._held = False
            self.on_release()
