import asyncio

import numpy as np

from sunday.utils.logging import log


async def decode_audio(audio_bytes: bytes, target_sr: int = 16000) -> np.ndarray:
    """
    Decode audio bytes (WebM, Opus, etc.) to a float32 numpy array using ffmpeg.

    Args:
        audio_bytes: The raw encoded audio data.
        target_sr: The target sample rate for the output PCM data.

    Returns:
        A mono float32 numpy array of the audio signal.
    """
    cmd = [
        "ffmpeg",
        "-i", "pipe:0",          # Input from stdin
        "-f", "f32le",           # Output format: float 32-bit little endian
        "-acodec", "pcm_f32le",  # Use PCM float 32-bit little endian codec
        "-ar", str(target_sr),   # Set sample rate
        "-ac", "1",              # Set mono channel
        "pipe:1"                 # Output to stdout
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate(input=audio_bytes)

        if process.returncode != 0:
            log.error("audio.decode_failed", stderr=stderr.decode())
            return np.array([], dtype=np.float32)

        # Convert raw bytes output to numpy array
        return np.frombuffer(stdout, dtype=np.float32)

    except Exception as e:
        log.error("audio.decode_error", error=str(e))
        return np.array([], dtype=np.float32)
