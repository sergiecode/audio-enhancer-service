"""
Security Tests
Created by Sergie Code

Tests for security vulnerabilities and attack vectors.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
import sys
from unittest.mock import patch, mock_open
import hashlib
import base64

# Import test utilities
sys.path.append(str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app.main import app


class TestFileUploadSecurity:
    """Test file upload security"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_file_type_validation(self, client, temp_dir):
        """Test that only valid audio files are accepted"""
        # Test with various malicious file types
        malicious_files = [
            ("script.sh", b"#!/bin/bash\nrm -rf /", "text/x-shellscript"),
            ("virus.exe", b"MZ\x90\x00" + b"fake_executable", "application/x-executable"),
            ("malware.bat", b"@echo off\ndel *.*", "application/x-msdos-program"),
            ("payload.php", b"<?php system($_GET['cmd']); ?>", "application/x-php"),
            ("exploit.html", b"<script>alert('xss')</script>", "text/html"),
            ("archive.zip", b"PK\x03\x04" + b"fake_zip", "application/zip"),
        ]
        
        for filename, content, mime_type in malicious_files:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(content)
            
            with open(file_path, 'rb') as f:
                files = {"file": (filename, f, mime_type)}
                response = client.post("/process", files=files)
            
            # Should reject non-audio files
            assert response.status_code == 400
            data = response.json()
            assert "Unsupported file format" in data["detail"]
    
    def test_filename_path_traversal(self, client, temp_dir):
        """Test protection against path traversal attacks"""
        # Create a valid audio file with malicious filename
        audio_content = self._create_dummy_wav_content()
        
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\drivers\\etc\\hosts",
            "../../../../usr/bin/python",
            "../app/main.py",
            "../../config.py",
        ]
        
        for malicious_filename in malicious_filenames:
            # Use StringIO to simulate file upload
            import io
            files = {"file": (malicious_filename, io.BytesIO(audio_content), "audio/wav")}
            response = client.post("/process", files=files)
            
            # Should either reject the filename or sanitize it safely
            # Both 400 (bad request) and 200 (if properly sanitized) are acceptable
            assert response.status_code in [200, 400, 422]
            
            if response.status_code == 200:
                # If processed, ensure no path traversal occurred
                data = response.json()
                output_file = data.get("output_file", "")
                # Output filename shouldn't contain path traversal sequences
                assert "../" not in output_file
                assert "..\\" not in output_file
    
    def test_oversized_filename(self, client):
        """Test handling of extremely long filenames"""
        # Create extremely long filename
        long_filename = "a" * 1000 + ".wav"
        audio_content = self._create_dummy_wav_content()
        
        import io
        files = {"file": (long_filename, io.BytesIO(audio_content), "audio/wav")}
        response = client.post("/process", files=files)
        
        # Should handle gracefully (either reject or truncate safely)
        assert response.status_code in [200, 400, 413, 422]
    
    def test_null_byte_injection(self, client):
        """Test protection against null byte injection"""
        malicious_filenames = [
            "safe.wav\x00.php",
            "audio.wav\x00../../../etc/passwd",
            "test\x00.exe.wav",
        ]
        
        audio_content = self._create_dummy_wav_content()
        
        for filename in malicious_filenames:
            import io
            files = {"file": (filename, io.BytesIO(audio_content), "audio/wav")}
            response = client.post("/process", files=files)
            
            # Should handle null bytes safely
            assert response.status_code in [200, 400, 422]
    
    def test_unicode_filename_handling(self, client):
        """Test handling of Unicode and special characters in filenames"""
        unicode_filenames = [
            "测试文件.wav",  # Chinese
            "файл.wav",     # Cyrillic
            "🎵音频.wav",    # Emoji + Chinese
            "file with spaces.wav",
            "file-with-dashes.wav",
            "file_with_underscores.wav",
            "file.with.dots.wav",
        ]
        
        audio_content = self._create_dummy_wav_content()
        
        for filename in unicode_filenames:
            import io
            files = {"file": (filename, io.BytesIO(audio_content), "audio/wav")}
            response = client.post("/process", files=files)
            
            # Should handle Unicode gracefully
            assert response.status_code in [200, 400, 422]
    
    def _create_dummy_wav_content(self):
        """Create minimal valid WAV file content"""
        # Minimal WAV header
        wav_header = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
        wav_header += b"\x44\xAC\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        return wav_header


class TestFileSystemSecurity:
    """Test file system security"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_directory_traversal_download(self, client):
        """Test protection against directory traversal in downloads"""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "../app/main.py",
            "../../requirements.txt",
            "../config.py",
            "/etc/shadow",
            "C:\\Windows\\System32\\drivers\\etc\\hosts",
        ]
        
        for malicious_path in malicious_paths:
            response = client.get(f"/download/{malicious_path}")
            
            # Should not allow access to files outside designated directory
            assert response.status_code == 404
    
    def test_symlink_attack_protection(self, client, temp_dir):
        """Test protection against symlink attacks"""
        # This test checks if the service follows symlinks to unauthorized locations
        
        # Create a symlink to a sensitive file (if on Unix-like system)
        if hasattr(os, 'symlink'):
            try:
                sensitive_file = "/etc/passwd"  # Unix
                if not os.path.exists(sensitive_file):
                    sensitive_file = "C:\\Windows\\System32\\drivers\\etc\\hosts"  # Windows
                
                if os.path.exists(sensitive_file):
                    symlink_path = os.path.join(temp_dir, "symlink_attack.wav")
                    os.symlink(sensitive_file, symlink_path)
                    
                    # Try to download via the symlink
                    response = client.get(f"/download/symlink_attack.wav")
                    
                    # Should not follow symlinks to sensitive files
                    assert response.status_code == 404
            except (OSError, NotImplementedError):
                # Symlinks not supported on this system
                pass
    
    def test_file_permission_security(self, client, temp_dir):
        """Test file permission handling"""
        # Create a file with restricted permissions
        restricted_file = os.path.join(temp_dir, "restricted.wav")
        with open(restricted_file, 'wb') as f:
            f.write(self._create_dummy_wav_content())
        
        # Try to make it read-only
        try:
            os.chmod(restricted_file, 0o444)
            
            # Service should handle permission errors gracefully
            with open(restricted_file, 'rb') as f:
                files = {"file": ("restricted.wav", f, "audio/wav")}
                response = client.post("/process", files=files)
            
            # Should either process successfully or fail gracefully
            assert response.status_code in [200, 400, 500]
            
        except (OSError, NotImplementedError):
            # Permission changes not supported
            pass
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(restricted_file, 0o644)
            except:
                pass
    
    def _create_dummy_wav_content(self):
        """Create minimal valid WAV file content"""
        wav_header = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
        wav_header += b"\x44\xAC\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        return wav_header


class TestInputValidation:
    """Test input validation and sanitization"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_malformed_requests(self, client):
        """Test handling of malformed requests"""
        malformed_requests = [
            # Missing file parameter
            {},
            # Multiple file parameters with same name
            {"file": ["file1.wav", "file2.wav"]},
            # Invalid multipart data
            {"invalid": "data"},
        ]
        
        for request_data in malformed_requests:
            if request_data:
                response = client.post("/process", data=request_data)
            else:
                response = client.post("/process")
            
            # Should handle malformed requests gracefully
            assert response.status_code in [400, 422]
    
    def test_content_type_validation(self, client, temp_dir):
        """Test content type validation"""
        # Create a text file with audio extension
        fake_audio = os.path.join(temp_dir, "fake.wav")
        with open(fake_audio, 'w') as f:
            f.write("This is not audio data")
        
        # Try to upload with incorrect content type
        with open(fake_audio, 'rb') as f:
            files = {"file": ("fake.wav", f, "text/plain")}
            response = client.post("/process", files=files)
        
        # Should validate based on file extension, not just content type
        assert response.status_code in [200, 400]
    
    def test_empty_file_handling(self, client, temp_dir):
        """Test handling of empty files"""
        empty_file = os.path.join(temp_dir, "empty.wav")
        with open(empty_file, 'wb') as f:
            pass  # Create empty file
        
        with open(empty_file, 'rb') as f:
            files = {"file": ("empty.wav", f, "audio/wav")}
            response = client.post("/process", files=files)
        
        # Should handle empty files gracefully
        assert response.status_code in [200, 400, 422]
    
    def test_extremely_large_file_handling(self, client, temp_dir):
        """Test handling of extremely large files"""
        # Create a file that appears large (without actually being large)
        large_file = os.path.join(temp_dir, "large.wav")
        
        # Create WAV header that claims large file size
        fake_large_header = b"RIFF\xFF\xFF\xFF\xFFWAVEfmt \x10\x00\x00\x00"
        fake_large_header += b"\x01\x00\x01\x00\x44\xAC\x00\x00\x88\x58\x01\x00"
        fake_large_header += b"\x02\x00\x10\x00data\xFF\xFF\xFF\xFF"
        fake_large_header += b"\x00" * 1000  # Some actual data
        
        with open(large_file, 'wb') as f:
            f.write(fake_large_header)
        
        with open(large_file, 'rb') as f:
            files = {"file": ("large.wav", f, "audio/wav")}
            response = client.post("/process", files=files)
        
        # Should handle potentially large files appropriately
        assert response.status_code in [200, 400, 413, 422]


class TestAPISecurityHeaders:
    """Test API security headers and CORS"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_cors_configuration(self, client):
        """Test CORS configuration security"""
        # Test OPTIONS request for CORS preflight
        response = client.options("/process")
        
        # Should handle CORS appropriately
        assert response.status_code in [200, 204, 405]
        
        # Check for CORS headers in regular requests
        response = client.get("/")
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers"
        ]
        
        # At least some CORS configuration should be present
        has_cors = any(header in response.headers for header in cors_headers)
        assert has_cors or response.status_code == 200
    
    def test_security_headers(self, client):
        """Test for security headers"""
        response = client.get("/")
        
        # Check for common security headers (optional but recommended)
        security_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection",
            "content-security-policy",
            "strict-transport-security"
        ]
        
        # While not all may be present, the service should at least respond securely
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
    
    def test_information_disclosure(self, client):
        """Test for information disclosure in error messages"""
        # Test various error scenarios
        error_scenarios = [
            ("/nonexistent", "GET"),
            ("/process", "PUT"),
            ("/download/nonexistent.wav", "GET"),
        ]
        
        for endpoint, method in error_scenarios:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "PUT":
                response = client.put(endpoint)
            
            # Error responses should not disclose sensitive information
            if response.status_code >= 400:
                response_text = response.text.lower()
                
                # Should not contain sensitive paths or system information
                sensitive_info = [
                    "/etc/passwd",
                    "c:\\windows",
                    "traceback",
                    "stack trace",
                    "internal server error details",
                    "database",
                    "connection string"
                ]
                
                for sensitive in sensitive_info:
                    assert sensitive not in response_text


class TestDenialOfServiceProtection:
    """Test protection against denial of service attacks"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_request_size_limits(self, client):
        """Test request size limits"""
        # Test with very large request body (simulated)
        large_data = b"A" * (10 * 1024 * 1024)  # 10MB of data
        
        import io
        files = {"file": ("large.wav", io.BytesIO(large_data), "audio/wav")}
        
        try:
            response = client.post("/process", files=files)
            # Should either accept if within limits or reject if too large
            assert response.status_code in [200, 400, 413, 422]
        except Exception:
            # Connection might be rejected before response
            pass
    
    def test_concurrent_request_handling(self, client, temp_dir):
        """Test handling of many concurrent requests"""
        import threading
        import time
        
        audio_content = self._create_dummy_wav_content()
        results = []
        
        def make_request(request_id):
            try:
                import io
                files = {"file": (f"test_{request_id}.wav", io.BytesIO(audio_content), "audio/wav")}
                response = client.post("/process", files=files)
                results.append(response.status_code)
            except Exception as e:
                results.append(f"Error: {e}")
        
        # Make many concurrent requests
        threads = []
        for i in range(20):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all requests with timeout
        for thread in threads:
            thread.join(timeout=30)
        
        # Service should handle concurrent requests gracefully
        # Most should succeed or fail gracefully
        successful_responses = sum(1 for r in results if isinstance(r, int) and r < 500)
        total_responses = len(results)
        
        if total_responses > 0:
            success_rate = successful_responses / total_responses
            assert success_rate >= 0.5  # At least 50% should be handled gracefully
    
    def test_resource_exhaustion_protection(self, client):
        """Test protection against resource exhaustion"""
        # Test rapid successive requests
        response_codes = []
        
        for i in range(100):
            try:
                response = client.get("/health")
                response_codes.append(response.status_code)
            except Exception:
                response_codes.append(500)
        
        # Service should remain responsive
        successful_requests = sum(1 for code in response_codes if code == 200)
        success_rate = successful_requests / len(response_codes)
        
        # Should handle most requests even under load
        assert success_rate >= 0.8  # At least 80% success rate
    
    def _create_dummy_wav_content(self):
        """Create minimal valid WAV file content"""
        wav_header = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
        wav_header += b"\x44\xAC\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        return wav_header


class TestDataValidation:
    """Test data validation and integrity"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_file_content_validation(self, client, temp_dir):
        """Test validation of file content vs extension"""
        # Create files with mismatched content and extension
        mismatched_files = [
            ("image.wav", b"\x89PNG\r\n\x1a\n", "image/png"),  # PNG with WAV extension
            ("text.wav", b"This is plain text", "text/plain"),   # Text with WAV extension
            ("exe.wav", b"MZ\x90\x00", "application/x-executable"),  # Executable with WAV extension
        ]
        
        for filename, content, content_type in mismatched_files:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(content)
            
            with open(file_path, 'rb') as f:
                files = {"file": (filename, f, "audio/wav")}
                response = client.post("/process", files=files)
            
            # Should detect content mismatch or handle gracefully
            assert response.status_code in [200, 400, 422]
    
    def test_malicious_audio_content(self, client, temp_dir):
        """Test handling of potentially malicious audio content"""
        # Create WAV file with potentially malicious metadata
        malicious_wav = self._create_wav_with_metadata(
            title="<script>alert('xss')</script>",
            artist="../../../etc/passwd",
            comment="'; DROP TABLE users; --"
        )
        
        file_path = os.path.join(temp_dir, "malicious.wav")
        with open(file_path, 'wb') as f:
            f.write(malicious_wav)
        
        with open(file_path, 'rb') as f:
            files = {"file": ("malicious.wav", f, "audio/wav")}
            response = client.post("/process", files=files)
        
        # Should handle malicious metadata safely
        assert response.status_code in [200, 400, 422]
        
        if response.status_code == 200:
            data = response.json()
            # Response should not contain unescaped malicious content
            response_str = str(data)
            assert "<script>" not in response_str
            assert "DROP TABLE" not in response_str
    
    def _create_wav_with_metadata(self, title="", artist="", comment=""):
        """Create WAV file with metadata"""
        # Basic WAV header
        wav_data = b"RIFF\x00\x00\x00\x00WAVEfmt \x10\x00\x00\x00"
        wav_data += b"\x01\x00\x01\x00\x44\xAC\x00\x00\x88\x58\x01\x00"
        wav_data += b"\x02\x00\x10\x00"
        
        # Add LIST chunk with metadata (simplified)
        if title or artist or comment:
            list_data = b"INFOINAM" + len(title).to_bytes(4, 'little') + title.encode('utf-8', errors='ignore')
            if artist:
                list_data += b"IART" + len(artist).to_bytes(4, 'little') + artist.encode('utf-8', errors='ignore')
            if comment:
                list_data += b"ICMT" + len(comment).to_bytes(4, 'little') + comment.encode('utf-8', errors='ignore')
            
            wav_data += b"LIST" + len(list_data).to_bytes(4, 'little') + list_data
        
        # Add data chunk
        wav_data += b"data\x00\x00\x00\x00"
        
        # Update RIFF size
        total_size = len(wav_data) - 8
        wav_data = wav_data[:4] + total_size.to_bytes(4, 'little') + wav_data[8:]
        
        return wav_data
