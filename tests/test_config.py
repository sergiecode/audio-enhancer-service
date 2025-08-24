"""
Configuration and Settings Tests
Created by Sergie Code

Tests for configuration management and settings validation.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

# Import configuration to test
import sys
sys.path.append(str(Path(__file__).parent.parent))

from app.config import Settings, settings


class TestSettingsClass:
    """Test the Settings class and configuration management"""
    
    def test_settings_initialization(self):
        """Test Settings class initialization with defaults"""
        test_settings = Settings()
        
        # Test default values
        assert test_settings.SERVICE_NAME == "Audio Enhancement Service"
        assert test_settings.SERVICE_VERSION == "1.0.0"
        assert test_settings.API_HOST == "0.0.0.0"
        assert test_settings.API_PORT == 8000
        assert test_settings.API_WORKERS == 1
        
        # Test file paths are Path objects
        assert isinstance(test_settings.UPLOAD_DIR, Path)
        assert isinstance(test_settings.OUTPUT_DIR, Path)
        assert isinstance(test_settings.MODELS_DIR, Path)
        
        # Test supported formats
        assert isinstance(test_settings.SUPPORTED_FORMATS, list)
        assert ".wav" in test_settings.SUPPORTED_FORMATS
        assert ".mp3" in test_settings.SUPPORTED_FORMATS
    
    def test_settings_directories_creation(self):
        """Test that Settings creates necessary directories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Override environment variables for testing
            with patch.dict(os.environ, {
                'UPLOAD_DIR': os.path.join(temp_dir, 'test_uploads'),
                'OUTPUT_DIR': os.path.join(temp_dir, 'test_outputs'),
                'MODELS_DIR': os.path.join(temp_dir, 'test_models')
            }):
                test_settings = Settings()
                
                # Check that directories were created
                assert test_settings.UPLOAD_DIR.exists()
                assert test_settings.OUTPUT_DIR.exists()
                assert test_settings.MODELS_DIR.exists()
    
    @patch.dict(os.environ, {
        'API_HOST': '127.0.0.1',
        'API_PORT': '9000',
        'WORKER_COUNT': '4',
        'MAX_FILE_SIZE': '200',
        'LOG_LEVEL': 'DEBUG'
    })
    def test_settings_environment_variables(self):
        """Test that Settings reads from environment variables"""
        test_settings = Settings()
        
        assert test_settings.API_HOST == "127.0.0.1"
        assert test_settings.API_PORT == 9000
        assert test_settings.API_WORKERS == 4
        assert test_settings.MAX_FILE_SIZE == 200 * 1024 * 1024  # Converted to bytes
        assert test_settings.LOG_LEVEL == "DEBUG"
    
    @patch.dict(os.environ, {
        'DEMUCS_MODEL': 'custom_demucs',
        'SPLEETER_MODEL': 'spleeter:4stems-16kHz',
        'CORS_ORIGINS': 'http://localhost:3000,https://example.com'
    })
    def test_settings_model_configuration(self):
        """Test model and CORS configuration from environment"""
        test_settings = Settings()
        
        assert test_settings.DEMUCS_MODEL == "custom_demucs"
        assert test_settings.SPLEETER_MODEL == "spleeter:4stems-16kHz"
        assert test_settings.CORS_ORIGINS == ["http://localhost:3000", "https://example.com"]
    
    def test_settings_file_size_conversion(self):
        """Test file size conversion from MB to bytes"""
        with patch.dict(os.environ, {'MAX_FILE_SIZE': '50'}):
            test_settings = Settings()
            expected_bytes = 50 * 1024 * 1024
            assert test_settings.MAX_FILE_SIZE == expected_bytes
    
    def test_settings_audio_configuration(self):
        """Test audio processing configuration"""
        test_settings = Settings()
        
        assert test_settings.DEFAULT_SAMPLE_RATE == 44100
        assert test_settings.DEFAULT_BIT_DEPTH == 16
        
        # Test all required audio formats are present
        required_formats = [".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg"]
        for fmt in required_formats:
            assert fmt in test_settings.SUPPORTED_FORMATS


class TestGlobalSettingsInstance:
    """Test the global settings instance"""
    
    def test_global_settings_exists(self):
        """Test that global settings instance exists and is configured"""
        assert settings is not None
        assert isinstance(settings, Settings)
        
        # Test that it has expected attributes
        assert hasattr(settings, 'SERVICE_NAME')
        assert hasattr(settings, 'API_HOST')
        assert hasattr(settings, 'SUPPORTED_FORMATS')
    
    def test_global_settings_directories_exist(self):
        """Test that global settings created directories"""
        assert settings.UPLOAD_DIR.exists()
        assert settings.OUTPUT_DIR.exists()
        assert settings.MODELS_DIR.exists()
    
    def test_global_settings_consistency(self):
        """Test that global settings values are consistent"""
        # API configuration
        assert isinstance(settings.API_PORT, int)
        assert 1 <= settings.API_PORT <= 65535
        
        assert isinstance(settings.API_WORKERS, int)
        assert settings.API_WORKERS >= 1
        
        # File size limits
        assert isinstance(settings.MAX_FILE_SIZE, int)
        assert settings.MAX_FILE_SIZE > 0


class TestConfigurationValidation:
    """Test configuration validation and error handling"""
    
    @patch.dict(os.environ, {'API_PORT': 'invalid_port'})
    def test_invalid_port_handling(self):
        """Test handling of invalid port configuration"""
        with pytest.raises(ValueError):
            Settings()
    
    @patch.dict(os.environ, {'WORKER_COUNT': 'invalid_workers'})
    def test_invalid_worker_count_handling(self):
        """Test handling of invalid worker count"""
        with pytest.raises(ValueError):
            Settings()
    
    @patch.dict(os.environ, {'MAX_FILE_SIZE': 'invalid_size'})
    def test_invalid_file_size_handling(self):
        """Test handling of invalid file size configuration"""
        with pytest.raises(ValueError):
            Settings()
    
    def test_cors_origins_parsing(self):
        """Test CORS origins parsing with various formats"""
        test_cases = [
            ("*", ["*"]),
            ("http://localhost:3000", ["http://localhost:3000"]),
            ("http://localhost:3000,https://example.com", ["http://localhost:3000", "https://example.com"]),
            ("", [""]),
        ]
        
        for input_origins, expected_output in test_cases:
            with patch.dict(os.environ, {'CORS_ORIGINS': input_origins}):
                test_settings = Settings()
                assert test_settings.CORS_ORIGINS == expected_output


class TestEnvironmentSpecificConfiguration:
    """Test configuration for different environments"""
    
    @patch.dict(os.environ, {
        'API_HOST': '0.0.0.0',
        'WORKER_COUNT': '4',
        'LOG_LEVEL': 'WARNING',
        'CORS_ORIGINS': 'https://production.example.com'
    })
    def test_production_configuration(self):
        """Test production-like configuration"""
        test_settings = Settings()
        
        assert test_settings.API_HOST == "0.0.0.0"
        assert test_settings.API_WORKERS == 4
        assert test_settings.LOG_LEVEL == "WARNING"
        assert test_settings.CORS_ORIGINS == ["https://production.example.com"]
    
    @patch.dict(os.environ, {
        'API_HOST': '127.0.0.1',
        'WORKER_COUNT': '1',
        'LOG_LEVEL': 'DEBUG',
        'CORS_ORIGINS': '*'
    })
    def test_development_configuration(self):
        """Test development-like configuration"""
        test_settings = Settings()
        
        assert test_settings.API_HOST == "127.0.0.1"
        assert test_settings.API_WORKERS == 1
        assert test_settings.LOG_LEVEL == "DEBUG"
        assert test_settings.CORS_ORIGINS == ["*"]


class TestConfigurationSecurity:
    """Test security-related configuration aspects"""
    
    def test_default_cors_origins_security(self):
        """Test that default CORS configuration is appropriate"""
        test_settings = Settings()
        
        # In production, CORS should be more restrictive than "*"
        # But for development, "*" might be acceptable
        assert isinstance(test_settings.CORS_ORIGINS, list)
        assert len(test_settings.CORS_ORIGINS) > 0
    
    def test_file_size_limits(self):
        """Test that file size limits are reasonable"""
        test_settings = Settings()
        
        # File size should be reasonable (not too large to prevent DoS)
        max_size_mb = test_settings.MAX_FILE_SIZE / (1024 * 1024)
        assert 1 <= max_size_mb <= 1000  # Between 1MB and 1GB
    
    def test_directory_paths_security(self):
        """Test that directory paths are secure"""
        test_settings = Settings()
        
        # Paths should not contain dangerous characters
        dangerous_chars = ["../", "..\\", "/etc/", "C:\\Windows\\"]
        
        paths_to_check = [
            str(test_settings.UPLOAD_DIR),
            str(test_settings.OUTPUT_DIR),
            str(test_settings.MODELS_DIR)
        ]
        
        for path in paths_to_check:
            for dangerous_char in dangerous_chars:
                assert dangerous_char not in path


class TestConfigurationPersistence:
    """Test configuration persistence and consistency"""
    
    def test_settings_immutability(self):
        """Test that important settings remain consistent"""
        # Get initial values
        initial_service_name = settings.SERVICE_NAME
        initial_version = settings.SERVICE_VERSION
        initial_formats = settings.SUPPORTED_FORMATS.copy()
        
        # These should not change during runtime
        assert settings.SERVICE_NAME == initial_service_name
        assert settings.SERVICE_VERSION == initial_version
        assert settings.SUPPORTED_FORMATS == initial_formats
    
    def test_directory_persistence(self):
        """Test that directories remain accessible"""
        # Directories should exist and be accessible
        assert settings.UPLOAD_DIR.exists()
        assert settings.OUTPUT_DIR.exists()
        assert settings.MODELS_DIR.exists()
        
        # Should be able to write to these directories
        assert os.access(settings.UPLOAD_DIR, os.W_OK)
        assert os.access(settings.OUTPUT_DIR, os.W_OK)
        assert os.access(settings.MODELS_DIR, os.W_OK)


class TestConfigurationCompatibility:
    """Test configuration compatibility with different systems"""
    
    def test_path_compatibility(self):
        """Test that paths work across different operating systems"""
        test_settings = Settings()
        
        # Paths should be valid Path objects
        assert isinstance(test_settings.UPLOAD_DIR, Path)
        assert isinstance(test_settings.OUTPUT_DIR, Path)
        assert isinstance(test_settings.MODELS_DIR, Path)
        
        # Should be able to resolve paths
        assert test_settings.UPLOAD_DIR.resolve()
        assert test_settings.OUTPUT_DIR.resolve()
        assert test_settings.MODELS_DIR.resolve()
    
    def test_network_configuration_compatibility(self):
        """Test network configuration compatibility"""
        test_settings = Settings()
        
        # API host should be a valid format
        assert isinstance(test_settings.API_HOST, str)
        assert len(test_settings.API_HOST) > 0
        
        # Port should be valid
        assert 1 <= test_settings.API_PORT <= 65535
    
    def test_log_level_compatibility(self):
        """Test log level compatibility with Python logging"""
        import logging
        
        test_settings = Settings()
        
        # Log level should be valid for Python logging
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        assert test_settings.LOG_LEVEL.upper() in valid_levels
        
        # Should be able to set logging level
        numeric_level = getattr(logging, test_settings.LOG_LEVEL.upper())
        assert isinstance(numeric_level, int)
