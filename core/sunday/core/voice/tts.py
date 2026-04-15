"""Text-to-Speech engine using Piper TTS.

Piper runs entirely locally, no API costs, no internet needed.
Uses the 'amy' voice — clear female English speaker.

Architecture:
- Accepts text (full sentences or chunks)
- Returns raw audio bytes (WAV format, 22050 Hz)
- Supports sentence-level streaming for real-time feel
"""

import io
import re
import wave
from pathlib import Path

from sunday.config.settings import settings
from sunday.utils.logging import log

# Lazy-loaded to avoid import overhead at startup
_tts_engine = None
_tts_ready = False


def _get_engine():
    """Lazy-initialize the Piper TTS engine."""
    global _tts_engine, _tts_ready

    if _tts_ready:
        return _tts_engine

    try:
        from piper import PiperVoice

        voice_name = settings.voice.tts_voice

        # Piper downloads models on first use to ~/.local/share/piper-voices/
        # We'll use piper's built-in model downloading via piper-tts package
        # The model will be auto-downloaded when first used
        data_dir = Path.home() / ".local" / "share" / "piper-voices"
        data_dir.mkdir(parents=True, exist_ok=True)

        model_path = data_dir / f"{voice_name}.onnx"
        config_path = data_dir / f"{voice_name}.onnx.json"

        if model_path.exists() and config_path.exists():
            _tts_engine = PiperVoice.load(str(model_path), config_path=str(config_path))
            _tts_ready = True
            log.info("tts.loaded", voice=voice_name)
        else:
            log.warning(
                "tts.model_not_found",
                voice=voice_name,
                hint=f"Download from https://huggingface.co/rhasspy/piper-voices — "
                f"place .onnx and .onnx.json in {data_dir}",
            )
            _tts_engine = None
            _tts_ready = True  # Mark as "tried" to avoid repeated attempts

    except ImportError:
        log.warning("tts.piper_not_installed", hint="pip install piper-tts")
        _tts_engine = None
        _tts_ready = True

    return _tts_engine


# Regex to split text into sentences
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|(?<=\n)\s*")


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences for chunked TTS."""
    sentences = _SENTENCE_SPLIT.split(text.strip())
    return [s.strip() for s in sentences if s.strip()]


def synthesize(text: str) -> bytes | None:
    """Convert text to WAV audio bytes.

    Returns None if TTS is not available.
    """
    engine = _get_engine()
    if engine is None:
        return None

    try:
        audio_buffer = io.BytesIO()

        with wave.open(audio_buffer, "wb") as wav_file:
            engine.synthesize(text, wav_file)

        return audio_buffer.getvalue()

    except Exception as e:
        log.error("tts.synthesis_failed", error=str(e), text_length=len(text))
        return None


def synthesize_streaming(text: str):
    """Generator that yields WAV audio bytes sentence by sentence.

    This allows the frontend to start playing audio immediately
    while the rest of the text is still being synthesized.
    """
    sentences = split_into_sentences(text)

    for sentence in sentences:
        audio = synthesize(sentence)
        if audio:
            yield audio


def is_available() -> bool:
    """Check if TTS engine is ready."""
    engine = _get_engine()
    return engine is not None
