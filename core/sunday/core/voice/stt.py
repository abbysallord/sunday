"""Speech-to-Text engine using Faster-Whisper.

Runs entirely locally on CPU. The 'base.en' model is ~150MB,
optimized for English, and fast enough for real-time on modern CPUs.
"""

import io
import tempfile
from pathlib import Path

import numpy as np

from sunday.config.settings import settings
from sunday.utils.logging import log

# Lazy-loaded
_stt_model = None
_stt_ready = False


def _get_model():
    """Lazy-initialize the Whisper model."""
    global _stt_model, _stt_ready

    if _stt_ready:
        return _stt_model

    try:
        from faster_whisper import WhisperModel

        model_size = settings.voice.stt_model

        log.info("stt.loading", model=model_size)
        _stt_model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",  # Fastest on CPU
        )
        _stt_ready = True
        log.info("stt.loaded", model=model_size)

    except ImportError:
        log.warning("stt.faster_whisper_not_installed", hint="pip install faster-whisper")
        _stt_model = None
        _stt_ready = True

    except Exception as e:
        log.error("stt.load_failed", error=str(e))
        _stt_model = None
        _stt_ready = True

    return _stt_model


def transcribe_audio(audio_bytes: bytes) -> str | None:
    """Transcribe audio bytes to text.

    Accepts raw WAV audio bytes.
    Returns transcribed text, or None if STT is unavailable.
    """
    model = _get_model()
    if model is None:
        return None

    try:
        # Write to temp file (faster-whisper needs a file path or numpy array)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()

            segments, info = model.transcribe(
                tmp.name,
                beam_size=3,  # Balance between speed and accuracy
                language="en",
                vad_filter=True,  # Use built-in VAD to skip silence
            )

            text = " ".join(segment.text.strip() for segment in segments)

        log.info("stt.transcribed", length=len(text), duration=f"{info.duration:.1f}s")
        return text.strip() if text.strip() else None

    except Exception as e:
        log.error("stt.transcription_failed", error=str(e))
        return None


def transcribe_numpy(audio_array: np.ndarray, sample_rate: int = 16000) -> str | None:
    """Transcribe a numpy audio array to text.

    Useful when receiving audio from WebSocket as raw PCM data.
    """
    model = _get_model()
    if model is None:
        return None

    try:
        # Ensure float32 and mono
        if audio_array.dtype != np.float32:
            audio_array = audio_array.astype(np.float32)

        if len(audio_array.shape) > 1:
            audio_array = audio_array.mean(axis=1)

        # Normalize to [-1, 1]
        max_val = np.abs(audio_array).max()
        if max_val > 0:
            audio_array = audio_array / max_val

        segments, info = model.transcribe(
            audio_array,
            beam_size=3,
            language="en",
            vad_filter=True,
        )

        text = " ".join(segment.text.strip() for segment in segments)

        log.info("stt.transcribed", length=len(text), duration=f"{info.duration:.1f}s")
        return text.strip() if text.strip() else None

    except Exception as e:
        log.error("stt.transcription_failed", error=str(e))
        return None


def is_available() -> bool:
    """Check if STT model is ready."""
    model = _get_model()
    return model is not None
