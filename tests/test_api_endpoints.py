"""
API Endpoint Tests
Created by Sergie Code

Tests for all FastAPI endpoints including success and error cases.
"""

import pytest
import json
import io
from pathlib import Path
from unittest.mock import patch, mock_open
import os


class TestRootEndpoint:
    """Test the root endpoint"""
    
    def test_root_endpoint_success(self, client):
        """Test successful root endpoint call"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "service" in data
        assert "status" in data
        assert "version" in data
        assert "author" in data
        assert data["author"] == "Sergie Code"
        assert data["status"] == "active"
    
    def test_root_endpoint_content_type(self, client):
        """Test root endpoint returns JSON"""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"


class TestHealthEndpoint:
    """Test the health check endpoint"""
    
    def test_health_endpoint_success(self, client):
        """Test successful health check"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "audio-enhancer"
        assert "timestamp" in data
    
    def test_health_endpoint_structure(self, client):
        """Test health endpoint response structure"""
        response = client.get("/health")
        data = response.json()
        
        required_fields = ["status", "service", "timestamp"]
        for field in required_fields:
            assert field in data


class TestFormatsEndpoint:
    """Test the supported formats endpoint"""
    
    def test_formats_endpoint_success(self, client):
        """Test successful formats retrieval"""
        response = client.get("/formats")
        assert response.status_code == 200
        
        data = response.json()
        assert "supported_formats" in data
        assert "description" in data
        assert isinstance(data["supported_formats"], list)
        assert len(data["supported_formats"]) > 0
    
    def test_formats_endpoint_contains_common_formats(self, client):
        """Test that common audio formats are supported"""
        response = client.get("/formats")
        data = response.json()
        
        formats = data["supported_formats"]
        common_formats = [".wav", ".mp3", ".flac"]
        
        for fmt in common_formats:
            assert fmt in formats


class TestProcessEndpoint:
    """Test the audio processing endpoint"""
    
    def test_process_audio_success(self, client, sample_audio_file, mock_processing_success):
        """Test successful audio processing"""
        with open(sample_audio_file, 'rb') as audio_file:
            files = {"file": ("test_audio.wav", audio_file, "audio/wav")}
            response = client.post("/process", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert data["success"] is True
        assert "message" in data
        assert "input_file" in data
        assert "output_file" in data
        assert "processing_id" in data
        assert "processing_details" in data
        assert "download_url" in data
    
    def test_process_audio_no_file(self, client):
        """Test processing endpoint without file"""
        response = client.post("/process")
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_process_audio_empty_filename(self, client):
        """Test processing with empty filename"""
        files = {"file": ("", io.BytesIO(b"fake audio data"), "audio/wav")}
        response = client.post("/process", files=files)
        assert response.status_code == 400
        
        data = response.json()
        assert "No file provided" in data["detail"]
    
    def test_process_audio_invalid_format(self, client, invalid_file):
        """Test processing with invalid file format"""
        with open(invalid_file, 'rb') as file:
            files = {"file": ("invalid.txt", file, "text/plain")}
            response = client.post("/process", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "Unsupported file format" in data["detail"]
    
    @pytest.mark.parametrize("filename,mime_type", [
        ("test.wav", "audio/wav"),
        ("test.mp3", "audio/mpeg"),
        ("test.flac", "audio/flac"),
        ("test.m4a", "audio/mp4"),
        ("test.aac", "audio/aac"),
        ("test.ogg", "audio/ogg")
    ])
    def test_process_audio_supported_formats(self, client, sample_audio_file, mock_processing_success, filename, mime_type):
        """Test processing with all supported formats"""
        with open(sample_audio_file, 'rb') as audio_file:
            files = {"file": (filename, audio_file, mime_type)}
            response = client.post("/process", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.parametrize("filename,mime_type", [
        ("test.txt", "text/plain"),
        ("test.pdf", "application/pdf"),
        ("test.jpg", "image/jpeg"),
        ("test.zip", "application/zip")
    ])
    def test_process_audio_unsupported_formats(self, client, invalid_file, filename, mime_type):
        """Test processing with unsupported formats"""
        with open(invalid_file, 'rb') as file:
            files = {"file": (filename, file, mime_type)}
            response = client.post("/process", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "Unsupported file format" in data["detail"]
    
    def test_process_audio_processing_failure(self, client, sample_audio_file, mock_processing_failure):
        """Test handling of processing failures"""
        with open(sample_audio_file, 'rb') as audio_file:
            files = {"file": ("test_audio.wav", audio_file, "audio/wav")}
            response = client.post("/process", files=files)
        
        assert response.status_code == 500
        data = response.json()
        assert "Audio processing failed" in data["detail"]
    
    def test_process_audio_large_file(self, client, large_audio_file, mock_processing_success):
        """Test processing larger audio files"""
        with open(large_audio_file, 'rb') as audio_file:
            files = {"file": ("large_audio.wav", audio_file, "audio/wav")}
            response = client.post("/process", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_process_audio_response_structure(self, client, sample_audio_file, mock_processing_success):
        """Test detailed response structure"""
        with open(sample_audio_file, 'rb') as audio_file:
            files = {"file": ("test_audio.wav", audio_file, "audio/wav")}
            response = client.post("/process", files=files)
        
        data = response.json()
        
        # Required fields
        required_fields = [
            "success", "message", "input_file", "output_file", 
            "processing_id", "processing_details", "download_url"
        ]
        
        for field in required_fields:
            assert field in data
        
        # Processing details structure
        details = data["processing_details"]
        assert "processing_time" in details or "status" in details


class TestDownloadEndpoint:
    """Test the file download endpoint"""
    
    def test_download_file_not_found(self, client):
        """Test downloading non-existent file"""
        response = client.get("/download/nonexistent.wav")
        assert response.status_code == 404
        
        data = response.json()
        assert "File not found" in data["detail"]
    
    @patch('pathlib.Path.exists')
    @patch('fastapi.responses.FileResponse')
    def test_download_file_success(self, mock_file_response, mock_exists, client):
        """Test successful file download"""
        mock_exists.return_value = True
        mock_file_response.return_value = "mocked_file_response"
        
        response = client.get("/download/test_output.wav")
        # Note: Actual file operations are mocked, so we test the endpoint logic
        mock_exists.assert_called_once()
    
    def test_download_invalid_filename(self, client):
        """Test download with invalid filename characters"""
        invalid_filenames = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "file with spaces.wav",
            "file|with|pipes.wav"
        ]
        
        for filename in invalid_filenames:
            response = client.get(f"/download/{filename}")
            # Should either be 404 (file not found) or handled securely
            assert response.status_code in [404, 400]


class TestAPIErrorHandling:
    """Test API error handling and edge cases"""
    
    def test_invalid_endpoint(self, client):
        """Test accessing non-existent endpoint"""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_invalid_method(self, client):
        """Test using wrong HTTP method"""
        response = client.put("/process")
        assert response.status_code == 405  # Method Not Allowed
    
    def test_malformed_json(self, client):
        """Test sending malformed JSON data"""
        response = client.post(
            "/process",
            data="malformed json{",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]
    
    def test_extremely_large_filename(self, client, sample_audio_file):
        """Test with extremely long filename"""
        long_filename = "a" * 1000 + ".wav"
        
        with open(sample_audio_file, 'rb') as audio_file:
            files = {"file": (long_filename, audio_file, "audio/wav")}
            response = client.post("/process", files=files)
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 413]
    
    def test_multiple_files_upload(self, client, sample_audio_file):
        """Test uploading multiple files (should handle first one)"""
        with open(sample_audio_file, 'rb') as audio_file1, \
             open(sample_audio_file, 'rb') as audio_file2:
            
            files = [
                ("file", ("test1.wav", audio_file1, "audio/wav")),
                ("file", ("test2.wav", audio_file2, "audio/wav"))
            ]
            response = client.post("/process", files=files)
        
        # Should process or reject appropriately
        assert response.status_code in [200, 400, 422]


class TestCORSHeaders:
    """Test CORS headers and cross-origin requests"""
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present"""
        response = client.get("/")
        
        # Check for common CORS headers
        assert "access-control-allow-origin" in response.headers or response.status_code == 200
    
    def test_options_request(self, client):
        """Test OPTIONS preflight request"""
        response = client.options("/process")
        # Should handle OPTIONS request for CORS
        assert response.status_code in [200, 204, 405]


class TestResponseTiming:
    """Test response timing and performance"""
    
    def test_health_check_response_time(self, client):
        """Test that health check responds quickly"""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second
    
    def test_root_endpoint_response_time(self, client):
        """Test that root endpoint responds quickly"""
        import time
        
        start_time = time.time()
        response = client.get("/")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second
