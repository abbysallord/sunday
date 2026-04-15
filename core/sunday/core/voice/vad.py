"""Voice Activity Detection using Silero VAD.

Determines when the user starts and stops speaking.
This is critical for natural voice conversation —
we need to know WHEN to send audio to STT, not just
stream everything constantly.
"""

import numpy as np

from sunday.config.settings import settings
from sunday.utils.logging import log

_vad_model = None
_vad_ready = False


def _get_model():
    """Lazy-initialize Silero VAD model."""
    global _vad_model, _vad_ready

    if _vad_ready:
        return _vad_model

    try:
        import torch

        model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            trust_repo=True,
        )
        _vad_model = model
        _vad_ready = True
        log.info("vad.loaded")

    except ImportError:
        log.warning("vad.torch_not_installed", hint="pip install silero-vad")
        _vad_model = None
        _vad_ready = True
    except Exception as e:
        log.error("vad.load_failed", error=str(e))
        _vad_model = None
        _vad_ready = True

    return _vad_model


def is_speech(audio_chunk: np.ndarray, sample_rate: int = 16000) -> bool:
    """Detect if an audio chunk contains speech.

    Args:
        audio_chunk: Float32 numpy array of audio samples
        sample_rate: Audio sample rate (must be 8000 or 16000)

    Returns:
        True if speech is detected above the confidence threshold
    """
    model = _get_model()
    if model is None:
        # If VAD isn't available, assume everything is speech
        # (degrades experience but doesn't break functionality)
        return True

    try:
        import torch

        # Ensure correct format
        if audio_chunk.dtype != np.float32:
            audio_chunk = audio_chunk.astype(np.float32)

        tensor = torch.from_numpy(audio_chunk)
        confidence = model(tensor, sample_rate).item()

        return confidence >= settings.voice.vad_threshold

    except Exception as e:
        log.error("vad.detection_failed", error=str(e))
        return True  # Fail open — assume speech


def reset() -> None:
    """Reset VAD model state between utterances."""
    model = _get_model()
    if model is not None:
        model.reset_states()


def is_available() -> bool:
    """Check if VAD model is loaded."""
    model = _get_model()
    return model is not None
