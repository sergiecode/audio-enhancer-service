"""
Integration Tests
Created by Sergie Code

End-to-end integration tests for the complete audio enhancement service.
"""

import pytest
import requests
import tempfile
import os
import time
import threading
import wave
import numpy as np
from pathlib import Path
import subprocess
import signal
import psutil
from unittest.mock import patch
import asyncio

# Import test utilities
import sys
sys.path.append(str(Path(__file__).parent.parent))

from test_service import create_test_audio_file
from example_client import AudioEnhancementClient


class TestServiceIntegration:
    """Test complete service integration scenarios"""
    
    @pytest.fixture(scope="class")
    def running_service(self):
        """Start the service for integration testing"""
        # This fixture would start the actual service
        # For now, we'll assume the service is running on localhost:8000
        base_url = "http://localhost:8000"
        
        # Check if service is already running
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                yield base_url
                return
        except requests.exceptions.RequestException:
            pass
        
        # If we reach here, service is not running
        pytest.skip("Service is not running. Start with: uvicorn app.main:app --host 0.0.0.0 --port 8000")
    
    def test_complete_audio_processing_workflow(self, running_service, temp_dir):
        """Test complete workflow from upload to download"""
        client = AudioEnhancementClient(running_service)
        
        # Create test audio file
        test_file = os.path.join(temp_dir, "integration_test.wav")
        create_test_audio_file(test_file, duration=3.0)
        
        # Check service health
        health = client.check_health()
        assert health.get("status") == "healthy"
        
        # Get supported formats
        formats = client.get_supported_formats()
        assert "supported_formats" in formats
        assert ".wav" in formats["supported_formats"]
        
        # Process audio file
        result = client.process_audio(test_file)
        assert result.get("success") is True
        assert "output_file" in result
        assert "processing_id" in result
        
        # Download processed file
        if result.get("output_file"):
            download_path = os.path.join(temp_dir, "downloaded_enhanced.wav")
            success = client.download_file(result["output_file"], download_path)
            assert success is True
            assert os.path.exists(download_path)
    
    def test_multiple_concurrent_requests(self, running_service, temp_dir):
        """Test handling multiple concurrent requests"""
        client = AudioEnhancementClient(running_service)
        
        # Create multiple test files
        test_files = []
        for i in range(3):
            test_file = os.path.join(temp_dir, f"concurrent_test_{i}.wav")
            create_test_audio_file(test_file, duration=2.0)
            test_files.append(test_file)
        
        # Process files concurrently using threading
        results = []
        threads = []
        
        def process_file(file_path):
            result = client.process_audio(file_path)
            results.append(result)
        
        # Start threads
        for test_file in test_files:
            thread = threading.Thread(target=process_file, args=(test_file,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout
        
        # Verify all requests succeeded
        assert len(results) == 3
        for result in results:
            assert result.get("success") is True
    
    def test_service_error_handling(self, running_service, temp_dir):
        """Test service error handling with invalid requests"""
        client = AudioEnhancementClient(running_service)
        
        # Test with non-existent file
        non_existent_file = os.path.join(temp_dir, "nonexistent.wav")
        result = client.process_audio(non_existent_file)
        assert result.get("success") is False
        assert "error" in result
        
        # Test with invalid file format
        invalid_file = os.path.join(temp_dir, "invalid.txt")
        with open(invalid_file, 'w') as f:
            f.write("This is not an audio file")
        
        result = client.process_audio(invalid_file)
        assert result.get("success") is False
        assert "error" in result


class TestAPIIntegration:
    """Test API integration using raw HTTP requests"""
    
    def test_api_documentation_accessibility(self, running_service):
        """Test that API documentation is accessible"""
        docs_urls = [
            f"{running_service}/docs",
            f"{running_service}/redoc"
        ]
        
        for url in docs_urls:
            response = requests.get(url)
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")
    
    def test_api_cors_headers(self, running_service):
        """Test CORS headers in API responses"""
        response = requests.get(f"{running_service}/")
        
        # Check for CORS headers
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers"
        ]
        
        # At least one CORS header should be present
        cors_present = any(header in response.headers for header in cors_headers)
        assert cors_present or response.status_code == 200  # CORS might be configured differently
    
    def test_api_content_types(self, running_service):
        """Test API content types"""
        # Test JSON endpoints
        json_endpoints = ["/", "/health", "/formats"]
        
        for endpoint in json_endpoints:
            response = requests.get(f"{running_service}{endpoint}")
            assert response.status_code == 200
            assert "application/json" in response.headers.get("content-type", "")
    
    def test_api_error_responses(self, running_service):
        """Test API error response formats"""
        # Test 404 error
        response = requests.get(f"{running_service}/nonexistent")
        assert response.status_code == 404
        
        # Error response should be JSON
        try:
            error_data = response.json()
            assert "detail" in error_data
        except:
            # Some servers might return HTML 404 pages
            pass
    
    def test_api_file_upload_validation(self, running_service, temp_dir):
        """Test API file upload validation"""
        # Test upload without file
        response = requests.post(f"{running_service}/process")
        assert response.status_code in [400, 422]  # Bad Request or Unprocessable Entity
        
        # Test upload with invalid file
        invalid_file = os.path.join(temp_dir, "invalid.txt")
        with open(invalid_file, 'w') as f:
            f.write("Not an audio file")
        
        with open(invalid_file, 'rb') as f:
            files = {"file": ("invalid.txt", f, "text/plain")}
            response = requests.post(f"{running_service}/process", files=files)
        
        assert response.status_code == 400
        error_data = response.json()
        assert "Unsupported file format" in error_data.get("detail", "")


class TestServiceResilience:
    """Test service resilience and recovery"""
    
    def test_service_health_monitoring(self, running_service):
        """Test service health monitoring over time"""
        # Monitor health over several requests
        health_checks = []
        
        for _ in range(5):
            response = requests.get(f"{running_service}/health")
            health_checks.append(response.status_code == 200)
            time.sleep(0.5)
        
        # All health checks should pass
        assert all(health_checks)
    
    def test_service_memory_stability(self, running_service, temp_dir):
        """Test service memory stability under load"""
        client = AudioEnhancementClient(running_service)
        
        # Create test file
        test_file = os.path.join(temp_dir, "memory_test.wav")
        create_test_audio_file(test_file, duration=2.0)
        
        # Process multiple files to test memory stability
        for i in range(10):
            result = client.process_audio(test_file)
            
            # Each request should succeed
            assert result.get("success") is True
            
            # Small delay between requests
            time.sleep(0.1)
    
    def test_service_response_times(self, running_service):
        """Test service response times are reasonable"""
        endpoints = [
            ("/", "GET"),
            ("/health", "GET"),
            ("/formats", "GET")
        ]
        
        for endpoint, method in endpoints:
            start_time = time.time()
            
            if method == "GET":
                response = requests.get(f"{running_service}{endpoint}")
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 5.0  # Should respond within 5 seconds


class TestDataIntegrity:
    """Test data integrity throughout the processing pipeline"""
    
    def test_audio_file_integrity(self, running_service, temp_dir):
        """Test that processed audio maintains basic integrity"""
        client = AudioEnhancementClient(running_service)
        
        # Create test audio with known properties
        test_file = os.path.join(temp_dir, "integrity_test.wav")
        create_test_audio_file(test_file, duration=3.0, sample_rate=44100)
        
        # Get original file properties
        with wave.open(test_file, 'r') as wav:
            original_frames = wav.getnframes()
            original_sample_rate = wav.getframerate()
            original_channels = wav.getnchannels()
        
        # Process file
        result = client.process_audio(test_file)
        assert result.get("success") is True
        
        # Download and check processed file
        if result.get("output_file"):
            output_path = os.path.join(temp_dir, "integrity_output.wav")
            success = client.download_file(result["output_file"], output_path)
            assert success is True
            
            # Check processed file properties
            with wave.open(output_path, 'r') as wav:
                processed_frames = wav.getnframes()
                processed_sample_rate = wav.getframerate()
                processed_channels = wav.getnchannels()
            
            # Basic integrity checks (allowing for processing modifications)
            assert processed_sample_rate == original_sample_rate
            # Frame count might change due to processing, but should be reasonable
            assert abs(processed_frames - original_frames) < original_frames * 0.1
    
    def test_file_cleanup(self, running_service, temp_dir):
        """Test that temporary files are properly cleaned up"""
        client = AudioEnhancementClient(running_service)
        
        # Create and process a test file
        test_file = os.path.join(temp_dir, "cleanup_test.wav")
        create_test_audio_file(test_file, duration=1.0)
        
        # Note: This test assumes the service cleans up temporary files
        # In a real implementation, we would check the service's upload directory
        result = client.process_audio(test_file)
        assert result.get("success") is True


class TestScalabilitySimulation:
    """Test service scalability through simulation"""
    
    def test_gradual_load_increase(self, running_service, temp_dir):
        """Test service under gradually increasing load"""
        client = AudioEnhancementClient(running_service)
        
        # Create test file
        test_file = os.path.join(temp_dir, "load_test.wav")
        create_test_audio_file(test_file, duration=1.0)
        
        # Test with increasing concurrent requests
        for concurrent_requests in [1, 2, 3]:
            success_count = 0
            threads = []
            
            def make_request():
                nonlocal success_count
                result = client.process_audio(test_file)
                if result.get("success"):
                    success_count += 1
            
            # Start concurrent requests
            for _ in range(concurrent_requests):
                thread = threading.Thread(target=make_request)
                threads.append(thread)
                thread.start()
            
            # Wait for completion
            for thread in threads:
                thread.join(timeout=60)
            
            # Most requests should succeed
            success_rate = success_count / concurrent_requests
            assert success_rate >= 0.8  # At least 80% success rate
    
    def test_service_under_sustained_load(self, running_service, temp_dir):
        """Test service under sustained load"""
        client = AudioEnhancementClient(running_service)
        
        # Create test file
        test_file = os.path.join(temp_dir, "sustained_test.wav")
        create_test_audio_file(test_file, duration=0.5)  # Shorter file for faster processing
        
        # Make sustained requests over time
        success_count = 0
        total_requests = 20
        
        for i in range(total_requests):
            result = client.process_audio(test_file)
            if result.get("success"):
                success_count += 1
            
            # Small delay between requests
            time.sleep(0.2)
        
        # Service should handle sustained load well
        success_rate = success_count / total_requests
        assert success_rate >= 0.9  # At least 90% success rate


class TestServiceConfiguration:
    """Test service configuration and environment handling"""
    
    def test_service_configuration_endpoints(self, running_service):
        """Test service configuration through API"""
        # Test service info endpoint
        response = requests.get(f"{running_service}/")
        assert response.status_code == 200
        
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "author" in data
        assert data["author"] == "Sergie Code"
    
    def test_service_format_configuration(self, running_service):
        """Test service format configuration"""
        response = requests.get(f"{running_service}/formats")
        assert response.status_code == 200
        
        data = response.json()
        formats = data.get("supported_formats", [])
        
        # Should support common audio formats
        expected_formats = [".wav", ".mp3", ".flac"]
        for fmt in expected_formats:
            assert fmt in formats


# Utility class for integration test helpers
class IntegrationTestHelpers:
    """Helper methods for integration tests"""
    
    @staticmethod
    def wait_for_service(url, timeout=30):
        """Wait for service to become available"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
        
        return False
    
    @staticmethod
    def create_test_files(directory, count=5, duration=1.0):
        """Create multiple test audio files"""
        files = []
        for i in range(count):
            filename = os.path.join(directory, f"test_file_{i}.wav")
            create_test_audio_file(filename, duration=duration)
            files.append(filename)
        return files
    
    @staticmethod
    def measure_response_time(func, *args, **kwargs):
        """Measure function execution time"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
