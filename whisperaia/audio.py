import sounddevice as sd
import numpy as np


class AudioRecorder:
    SAMPLE_RATE = 16000

    def __init__(self):
        self._frames = []
        self._stream = None

    def start(self):
        self._frames = []
        self._stream = sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=1,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if not self._frames:
            return np.array([], dtype=np.float32)
        return np.concatenate(self._frames).flatten()

    def _callback(self, indata, frames, time, status):
        self._frames.append(indata.copy())
