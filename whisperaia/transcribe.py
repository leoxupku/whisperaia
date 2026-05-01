import numpy as np
import mlx_whisper

SAMPLE_RATE = 16000

# Guides Whisper to expect mixed Chinese-English tech content
INITIAL_PROMPT = (
    "以下是中英文混合的技术讨论，包含英文术语如 agent、orchestration、"
    "LLM、API、layer、pipeline、embedding、fine-tune 等，请保留英文原样。"
)

# mlx-community models: whisper-large-v3-mlx (~1.5GB), whisper-large-v3-turbo (~800MB)
MLX_MODEL = "mlx-community/whisper-large-v3-mlx"


class WhisperTranscriber:
    def __init__(self):
        # Warm up: triggers model download + Metal compilation
        mlx_whisper.transcribe(
            np.zeros(SAMPLE_RATE, dtype=np.float32),
            path_or_hf_repo=MLX_MODEL,
            language="zh",
        )

    def transcribe(self, audio: np.ndarray) -> str:
        if len(audio) < SAMPLE_RATE * 0.3:
            return ""
        result = mlx_whisper.transcribe(
            audio,
            path_or_hf_repo=MLX_MODEL,
            language="zh",
            initial_prompt=INITIAL_PROMPT,
        )
        return result["text"].strip()
