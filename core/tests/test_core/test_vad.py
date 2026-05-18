import numpy as np
import pytest
from unittest.mock import patch
from sunday.core.voice.vad import RollingVAD

def test_rolling_vad_initial_state():
    vad = RollingVAD(chunk_size=1024, speech_start_chunks=2, silence_end_chunks=5)
    assert not vad.is_speaking
    assert vad.consecutive_speech == 0
    assert vad.consecutive_silence == 0
    assert vad.residue.size == 0
    assert len(vad.speech_buffer) == 0

def test_rolling_vad_reset():
    vad = RollingVAD(chunk_size=1024, speech_start_chunks=2, silence_end_chunks=5)
    vad.is_speaking = True
    vad.consecutive_speech = 3
    vad.consecutive_silence = 1
    vad.residue = np.zeros(100, dtype=np.float32)
    vad.speech_buffer = [np.zeros(1024, dtype=np.float32)]
    
    vad.reset()
    assert not vad.is_speaking
    assert vad.consecutive_speech == 0
    assert vad.consecutive_silence == 0
    assert vad.residue.size == 0
    assert len(vad.speech_buffer) == 0

@patch("sunday.core.voice.vad.is_speech")
def test_rolling_vad_silent_stream(mock_is_speech):
    mock_is_speech.return_value = False
    
    vad = RollingVAD(chunk_size=1024, speech_start_chunks=2, silence_end_chunks=5)
    
    # Send a chunk smaller than chunk_size
    state, buffer = vad.process_audio(np.zeros(500, dtype=np.float32))
    assert state == "silent"
    assert buffer is None
    
    # Send another chunk so residue exceeds chunk_size
    state, buffer = vad.process_audio(np.zeros(600, dtype=np.float32))
    assert state == "silent"
    assert buffer is None
    assert vad.residue.size == 500 + 600 - 1024
    assert vad.consecutive_silence == 1

@patch("sunday.core.voice.vad.is_speech")
def test_rolling_vad_speech_transitions(mock_is_speech):
    # Simulate speech started -> speech active -> speech ended
    vad = RollingVAD(chunk_size=1024, speech_start_chunks=2, silence_end_chunks=3)
    
    # Frame 1: Speech detected (needs 2 chunks to start)
    mock_is_speech.return_value = True
    state, buffer = vad.process_audio(np.zeros(1024, dtype=np.float32))
    assert state == "silent"  # Only 1 chunk, not started yet
    assert not vad.is_speaking
    
    # Frame 2: Speech detected -> Should transition to speech_started
    state, buffer = vad.process_audio(np.zeros(1024, dtype=np.float32))
    assert state == "speech_started"
    assert vad.is_speaking
    
    # Frame 3: Speech detected -> Should stay speech_active
    state, buffer = vad.process_audio(np.zeros(1024, dtype=np.float32))
    assert state == "speech_active"
    assert vad.is_speaking
    
    # Frame 4: Silence detected
    mock_is_speech.return_value = False
    state, buffer = vad.process_audio(np.zeros(1024, dtype=np.float32))
    assert state == "speech_active"
    assert vad.is_speaking
    assert vad.consecutive_silence == 1
    
    # Frame 5: Silence detected
    state, buffer = vad.process_audio(np.zeros(1024, dtype=np.float32))
    assert state == "speech_active"
    assert vad.is_speaking
    assert vad.consecutive_silence == 2

    # Frame 6: Silence detected (3rd consecutive chunk) -> Should end speech
    state, buffer = vad.process_audio(np.zeros(1024, dtype=np.float32))
    assert state == "speech_ended"
    assert not vad.is_speaking
    assert buffer is not None
    
    # Verify buffer contains all accumulated speech chunks (3 speech + 3 silence)
    assert buffer.size == 6 * 1024
