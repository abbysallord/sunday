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


class RollingVAD:
    """Stateful VAD analyzer for real-time continuous streaming audio."""

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        speech_start_chunks: int = 2,
        silence_end_chunks: int = 15,  # ~960ms of silence at 16kHz with 1024 chunk size
    ):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.speech_start_chunks = speech_start_chunks
        self.silence_end_chunks = silence_end_chunks

        self.residue = np.array([], dtype=np.float32)
        self.speech_buffer = []
        self.pre_roll = []
        self.is_speaking = False

        self.consecutive_speech = 0
        self.consecutive_silence = 0

    def reset(self) -> None:
        """Reset the analyzer state."""
        self.residue = np.array([], dtype=np.float32)
        self.speech_buffer = []
        self.pre_roll = []
        self.is_speaking = False
        self.consecutive_speech = 0
        self.consecutive_silence = 0
        reset()

    def process_audio(self, audio_chunk: np.ndarray) -> tuple[str, np.ndarray | None]:
        """Process incoming raw audio chunk.

        Args:
            audio_chunk: Raw float32 numpy array.

        Returns:
            Tuple of (state, speech_data).
            state can be: "silent", "speech_started", "speech_active", "speech_ended"
            speech_data is the accumulated float32 numpy array of speech, returned ONLY on "speech_ended".
        """
        # Append to residue
        if self.residue.size > 0:
            self.residue = np.concatenate([self.residue, audio_chunk])
        else:
            self.residue = audio_chunk

        state = "silent" if not self.is_speaking else "speech_active"
        completed_buffer = None

        # Process in chunks of self.chunk_size
        while self.residue.size >= self.chunk_size:
            chunk = self.residue[:self.chunk_size]
            self.residue = self.residue[self.chunk_size:]

            speech_detected = is_speech(chunk, self.sample_rate)

            if speech_detected:
                self.consecutive_silence = 0
                self.consecutive_speech += 1

                if not self.is_speaking:
                    self.pre_roll.append(chunk)
                    # Limit pre-roll to the start threshold + 1 chunk of silence context
                    if len(self.pre_roll) > self.speech_start_chunks + 1:
                        self.pre_roll.pop(0)

                    if self.consecutive_speech >= self.speech_start_chunks:
                        self.is_speaking = True
                        state = "speech_started"
                        self.speech_buffer.extend(self.pre_roll)
                        self.pre_roll = []
                else:
                    self.speech_buffer.append(chunk)

            else:
                self.consecutive_speech = 0
                if self.is_speaking:
                    self.speech_buffer.append(chunk)
                    self.consecutive_silence += 1

                    if self.consecutive_silence >= self.silence_end_chunks:
                        # Speech finished!
                        self.is_speaking = False
                        state = "speech_ended"
                        completed_buffer = np.concatenate(self.speech_buffer)
                        self.speech_buffer = []
                        self.consecutive_silence = 0
                        break
                else:
                    # Accumulate a bit of silence context so we don't chop off the start of words
                    self.pre_roll.append(chunk)
                    if len(self.pre_roll) > self.speech_start_chunks + 1:
                        self.pre_roll.pop(0)
                    self.consecutive_silence += 1

        return state, completed_buffer

