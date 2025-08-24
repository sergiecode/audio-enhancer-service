"""
Test configuration and fixtures
Created by Sergie Code
"""

import pytest
import tempfile
import shutil
import wave
import numpy as np
from pathlib import Path
import os
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the FastAPI app
import sys
sys.path.append(str(Path(__file__).parent.parent))

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_audio_file(temp_dir):
    """Create a sample WAV audio file for testing"""
    filename = os.path.join(temp_dir, "test_audio.wav")
    
    # Generate test audio data
    sample_rate = 44100
    duration = 2.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    frequency = 440  # A4 note
    audio_data = np.sin(2 * np.pi * frequency * t)
    audio_data = (audio_data * 32767 * 0.8).astype(np.int16)
    
    # Write WAV file
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes = 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    return filename


@pytest.fixture
def large_audio_file(temp_dir):
    """Create a larger audio file for testing file size limits"""
    filename = os.path.join(temp_dir, "large_audio.wav")
    
    # Generate longer test audio
    sample_rate = 44100
    duration = 10.0  # 10 seconds
    t = np.linspace(0, duration, int(sample_rate * duration))
    frequency = 440
    audio_data = np.sin(2 * np.pi * frequency * t)
    audio_data = (audio_data * 32767 * 0.8).astype(np.int16)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(2)  # Stereo
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        # Duplicate mono to stereo
        stereo_data = np.column_stack((audio_data, audio_data))
        wav_file.writeframes(stereo_data.tobytes())
    
    return filename


@pytest.fixture
def invalid_file(temp_dir):
    """Create an invalid file (not audio) for testing"""
    filename = os.path.join(temp_dir, "invalid.txt")
    with open(filename, 'w') as f:
        f.write("This is not an audio file")
    return filename


@pytest.fixture
def mp3_audio_file(temp_dir):
    """Create a mock MP3 file for testing different formats"""
    filename = os.path.join(temp_dir, "test_audio.mp3")
    # Create a dummy MP3 file (just for filename testing)
    with open(filename, 'wb') as f:
        f.write(b"fake mp3 data for testing")
    return filename


@pytest.fixture
def setup_test_directories():
    """Setup test directories and cleanup after tests"""
    # Create test directories
    test_upload_dir = Path("test_uploads")
    test_output_dir = Path("test_outputs")
    
    test_upload_dir.mkdir(exist_ok=True)
    test_output_dir.mkdir(exist_ok=True)
    
    yield test_upload_dir, test_output_dir
    
    # Cleanup
    if test_upload_dir.exists():
        shutil.rmtree(test_upload_dir)
    if test_output_dir.exists():
        shutil.rmtree(test_output_dir)


@pytest.fixture
def mock_processing_success():
    """Mock successful audio processing"""
    with patch('app.inference.process_audio') as mock_process:
        mock_process.return_value = {
            "status": "success",
            "processing_time": 1.5,
            "file_size_mb": 2.1,
            "enhancement_applied": "test_enhancement",
            "models_used": ["test_model"],
            "input_path": "/test/input.wav",
            "output_path": "/test/output.wav",
            "output_exists": True,
            "message": "Test processing completed"
        }
        yield mock_process


@pytest.fixture
def mock_processing_failure():
    """Mock failed audio processing"""
    with patch('app.inference.process_audio') as mock_process:
        mock_process.side_effect = Exception("Test processing error")
        yield mock_process


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test data for various scenarios
TEST_AUDIO_FORMATS = [
    ("test.wav", "audio/wav"),
    ("test.mp3", "audio/mpeg"),
    ("test.flac", "audio/flac"),
    ("test.m4a", "audio/mp4"),
    ("test.aac", "audio/aac"),
    ("test.ogg", "audio/ogg")
]

INVALID_AUDIO_FORMATS = [
    ("test.txt", "text/plain"),
    ("test.pdf", "application/pdf"),
    ("test.jpg", "image/jpeg"),
    ("test.zip", "application/zip")
]

# Mock response data
MOCK_HEALTH_RESPONSE = {
    "status": "healthy",
    "service": "audio-enhancer",
    "timestamp": "2025-08-23T00:00:00Z"
}

MOCK_FORMATS_RESPONSE = {
    "supported_formats": [".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg"],
    "description": "Audio formats supported for processing"
}

MOCK_ROOT_RESPONSE = {
    "service": "Audio Enhancement Service",
    "status": "active",
    "version": "1.0.0",
    "author": "Sergie Code",
    "description": "AI-powered audio enhancement for musicians"
}
