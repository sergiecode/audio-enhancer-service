"""
Configuration settings for the Audio Enhancement Service
Created by Sergie Code
"""

import os
from pathlib import Path
from typing import List

class Settings:
    """Application settings and configuration"""
    
    # Service Information
    SERVICE_NAME: str = "Audio Enhancement Service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_DESCRIPTION: str = "AI-powered audio enhancement microservice for musicians"
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_WORKERS: int = int(os.getenv("WORKER_COUNT", "1"))
    
    # File Handling
    UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", "uploads"))
    OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "outputs"))
    MODELS_DIR: Path = Path(os.getenv("MODELS_DIR", "models"))
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "100")) * 1024 * 1024  # MB to bytes
    
    # Supported Audio Formats
    SUPPORTED_FORMATS: List[str] = [".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg"]
    
    # Processing Configuration
    DEFAULT_SAMPLE_RATE: int = 44100
    DEFAULT_BIT_DEPTH: int = 16
    
    # Model Configuration
    DEMUCS_MODEL: str = os.getenv("DEMUCS_MODEL", "htdemucs")
    SPLEETER_MODEL: str = os.getenv("SPLEETER_MODEL", "spleeter:2stems-16kHz")
    
    # CORS Settings
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    def __init__(self):
        """Create directories if they don't exist"""
        self.UPLOAD_DIR.mkdir(exist_ok=True)
        self.OUTPUT_DIR.mkdir(exist_ok=True)
        self.MODELS_DIR.mkdir(exist_ok=True)

# Global settings instance
settings = Settings()
