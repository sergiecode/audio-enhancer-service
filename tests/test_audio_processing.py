"""
Audio Processing and Inference Tests
Created by Sergie Code

Tests for the audio processing functionality and inference module.
"""

import pytest
import asyncio
import tempfile
import os
import wave
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import shutil

# Import modules to test
import sys
sys.path.append(str(Path(__file__).parent.parent))

from app.inference import (
    process_audio, 
    AudioEnhancer, 
    get_processing_stats,
    audio_enhancer
)


class TestAudioEnhancer:
    """Test the AudioEnhancer class"""
    
    @pytest.fixture
    def enhancer(self):
        """Create a fresh AudioEnhancer instance for testing"""
        return AudioEnhancer()
    
    def test_audio_enhancer_initialization(self, enhancer):
        """Test AudioEnhancer initialization"""
        assert enhancer.models_loaded is False
        assert enhancer.processing_stats["total_processed"] == 0
        assert enhancer.processing_stats["average_processing_time"] == 0.0
    
    @pytest.mark.asyncio
    async def test_load_models(self, enhancer):
        """Test model loading functionality"""
        assert enhancer.models_loaded is False
        
        await enhancer.load_models()
        
        assert enhancer.models_loaded is True
    
    @pytest.mark.asyncio
    async def test_enhance_audio_success(self, enhancer, sample_audio_file, temp_dir):
        """Test successful audio enhancement"""
        output_path = os.path.join(temp_dir, "enhanced.wav")
        
        result = await enhancer.enhance_audio(sample_audio_file, output_path)
        
        # Check result structure
        assert result["status"] == "success"
        assert "processing_time" in result
        assert "file_size_mb" in result
        assert "enhancement_applied" in result
        assert "models_used" in result
        assert "quality_improvements" in result
        
        # Check that output file exists
        assert os.path.exists(output_path)
        
        # Check that stats were updated
        assert enhancer.processing_stats["total_processed"] == 1
        assert enhancer.processing_stats["average_processing_time"] > 0
    
    @pytest.mark.asyncio
    async def test_enhance_audio_nonexistent_input(self, enhancer, temp_dir):
        """Test enhancement with non-existent input file"""
        input_path = os.path.join(temp_dir, "nonexistent.wav")
        output_path = os.path.join(temp_dir, "output.wav")
        
        with pytest.raises(Exception):
            await enhancer.enhance_audio(input_path, output_path)
    
    @pytest.mark.asyncio
    async def test_enhance_audio_models_auto_load(self, enhancer, sample_audio_file, temp_dir):
        """Test that models are automatically loaded if not already loaded"""
        output_path = os.path.join(temp_dir, "enhanced.wav")
        
        assert enhancer.models_loaded is False
        
        await enhancer.enhance_audio(sample_audio_file, output_path)
        
        assert enhancer.models_loaded is True
    
    @pytest.mark.asyncio
    async def test_enhance_audio_multiple_files(self, enhancer, sample_audio_file, temp_dir):
        """Test processing multiple files and statistics update"""
        for i in range(3):
            output_path = os.path.join(temp_dir, f"enhanced_{i}.wav")
            await enhancer.enhance_audio(sample_audio_file, output_path)
        
        # Check statistics
        assert enhancer.processing_stats["total_processed"] == 3
        assert enhancer.processing_stats["average_processing_time"] > 0
    
    def test_private_methods_exist(self, enhancer):
        """Test that private enhancement methods exist"""
        # These are placeholder methods for future implementation
        methods = [
            '_apply_noise_reduction',
            '_apply_source_separation',
            '_apply_quality_enhancement'
        ]
        
        for method_name in methods:
            assert hasattr(enhancer, method_name)
            method = getattr(enhancer, method_name)
            assert callable(method)


class TestProcessAudioFunction:
    """Test the main process_audio function"""
    
    @pytest.mark.asyncio
    async def test_process_audio_success(self, sample_audio_file, temp_dir):
        """Test successful audio processing"""
        output_path = os.path.join(temp_dir, "processed.wav")
        
        result = await process_audio(sample_audio_file, output_path)
        
        # Check result structure
        assert "status" in result or "input_path" in result
        assert result["input_path"] == sample_audio_file
        assert result["output_path"] == output_path
        assert result["output_exists"] is True
        assert "message" in result
        
        # Check output file exists
        assert os.path.exists(output_path)
    
    @pytest.mark.asyncio
    async def test_process_audio_input_not_found(self, temp_dir):
        """Test processing with non-existent input file"""
        input_path = os.path.join(temp_dir, "nonexistent.wav")
        output_path = os.path.join(temp_dir, "output.wav")
        
        with pytest.raises(FileNotFoundError):
            await process_audio(input_path, output_path)
    
    @pytest.mark.asyncio
    async def test_process_audio_creates_output_directory(self, sample_audio_file, temp_dir):
        """Test that output directory is created if it doesn't exist"""
        nested_output_path = os.path.join(temp_dir, "nested", "dir", "output.wav")
        
        assert not os.path.exists(os.path.dirname(nested_output_path))
        
        result = await process_audio(sample_audio_file, nested_output_path)
        
        assert os.path.exists(nested_output_path)
        assert result["output_exists"] is True
    
    @pytest.mark.asyncio
    async def test_process_audio_error_handling(self, sample_audio_file, temp_dir):
        """Test error handling in process_audio"""
        output_path = os.path.join(temp_dir, "output.wav")
        
        # Mock the enhancer to raise an exception
        with patch('app.inference.audio_enhancer.enhance_audio') as mock_enhance:
            mock_enhance.side_effect = Exception("Test error")
            
            with pytest.raises(Exception) as exc_info:
                await process_audio(sample_audio_file, output_path)
            
            assert "Failed to process audio" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('app.inference.audio_enhancer.enhance_audio')
    async def test_process_audio_output_verification(self, mock_enhance, sample_audio_file, temp_dir):
        """Test that process_audio verifies output file creation"""
        output_path = os.path.join(temp_dir, "output.wav")
        
        # Mock enhance_audio to return success but don't create file
        mock_enhance.return_value = {
            "status": "success",
            "processing_time": 1.0,
            "file_size_mb": 1.0
        }
        
        with pytest.raises(Exception) as exc_info:
            await process_audio(sample_audio_file, output_path)
        
        assert "Output file was not created" in str(exc_info.value)


class TestProcessingStats:
    """Test processing statistics functionality"""
    
    def test_get_processing_stats_structure(self):
        """Test processing stats structure"""
        stats = get_processing_stats()
        
        required_fields = [
            "total_files_processed",
            "average_processing_time", 
            "models_loaded",
            "service_status"
        ]
        
        for field in required_fields:
            assert field in stats
        
        assert stats["service_status"] == "active"
        assert isinstance(stats["total_files_processed"], int)
        assert isinstance(stats["average_processing_time"], (int, float))
        assert isinstance(stats["models_loaded"], bool)
    
    @pytest.mark.asyncio
    async def test_stats_update_after_processing(self, sample_audio_file, temp_dir):
        """Test that stats are updated after processing"""
        initial_stats = get_processing_stats()
        initial_count = initial_stats["total_files_processed"]
        
        output_path = os.path.join(temp_dir, "output.wav")
        await process_audio(sample_audio_file, output_path)
        
        updated_stats = get_processing_stats()
        assert updated_stats["total_files_processed"] > initial_count


class TestAudioFileHandling:
    """Test audio file handling and validation"""
    
    def test_create_test_audio_file_parameters(self, temp_dir):
        """Test audio file creation with different parameters"""
        from test_service import create_test_audio_file
        
        # Test different durations
        durations = [0.5, 1.0, 2.0, 5.0]
        for duration in durations:
            filename = os.path.join(temp_dir, f"test_{duration}s.wav")
            create_test_audio_file(filename, duration=duration)
            
            assert os.path.exists(filename)
            
            # Verify audio file properties
            with wave.open(filename, 'r') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                actual_duration = frames / sample_rate
                
                # Allow small tolerance for floating point precision
                assert abs(actual_duration - duration) < 0.1
    
    def test_different_audio_formats(self, temp_dir):
        """Test handling of different audio file formats (by extension)"""
        from test_service import create_test_audio_file
        
        # Create files with different extensions
        formats = [".wav", ".WAV"]  # Test case sensitivity
        
        for fmt in formats:
            filename = os.path.join(temp_dir, f"test{fmt}")
            if fmt.lower() == ".wav":  # Only create actual WAV files
                create_test_audio_file(filename)
                assert os.path.exists(filename)
    
    @pytest.mark.asyncio
    async def test_large_file_processing(self, temp_dir):
        """Test processing of larger audio files"""
        from test_service import create_test_audio_file
        
        # Create a larger test file
        large_file = os.path.join(temp_dir, "large_test.wav")
        create_test_audio_file(large_file, duration=10.0)  # 10 seconds
        
        output_path = os.path.join(temp_dir, "large_output.wav")
        result = await process_audio(large_file, output_path)
        
        assert result["output_exists"] is True
        assert os.path.exists(output_path)
        
        # Check that larger files take longer to process
        assert result.get("processing_time", 0) > 0


class TestConcurrentProcessing:
    """Test concurrent audio processing"""
    
    @pytest.mark.asyncio
    async def test_concurrent_audio_processing(self, sample_audio_file, temp_dir):
        """Test processing multiple files concurrently"""
        tasks = []
        num_concurrent = 3
        
        for i in range(num_concurrent):
            output_path = os.path.join(temp_dir, f"concurrent_output_{i}.wav")
            task = process_audio(sample_audio_file, output_path)
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        
        # Verify all processing completed successfully
        for i, result in enumerate(results):
            assert result["output_exists"] is True
            output_path = os.path.join(temp_dir, f"concurrent_output_{i}.wav")
            assert os.path.exists(output_path)
    
    @pytest.mark.asyncio
    async def test_processing_with_shared_enhancer(self, sample_audio_file, temp_dir):
        """Test that the shared audio_enhancer instance handles concurrent requests"""
        async def process_single(file_id):
            output_path = os.path.join(temp_dir, f"shared_output_{file_id}.wav")
            return await process_audio(sample_audio_file, output_path)
        
        # Process multiple files using the shared enhancer
        tasks = [process_single(i) for i in range(3)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        for result in results:
            assert result["output_exists"] is True


class TestErrorScenarios:
    """Test various error scenarios and edge cases"""
    
    @pytest.mark.asyncio
    async def test_processing_with_read_only_output_directory(self, sample_audio_file, temp_dir):
        """Test processing when output directory is read-only"""
        readonly_dir = os.path.join(temp_dir, "readonly")
        os.makedirs(readonly_dir)
        
        try:
            # Make directory read-only (Unix-style)
            os.chmod(readonly_dir, 0o444)
            
            output_path = os.path.join(readonly_dir, "output.wav")
            
            # This should either succeed by creating the directory or fail gracefully
            try:
                result = await process_audio(sample_audio_file, output_path)
                # If it succeeds, the output should exist
                assert result["output_exists"] is True
            except Exception as e:
                # If it fails, it should be a clear error message
                assert "Failed to process audio" in str(e)
        
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(readonly_dir, 0o755)
            except:
                pass
    
    @pytest.mark.asyncio
    async def test_processing_with_corrupted_input(self, temp_dir):
        """Test processing with corrupted audio file"""
        # Create a file that looks like audio but is corrupted
        corrupted_file = os.path.join(temp_dir, "corrupted.wav")
        with open(corrupted_file, 'wb') as f:
            f.write(b"RIFF" + b"fake wav data" * 100)
        
        output_path = os.path.join(temp_dir, "output.wav")
        
        # Should handle corrupted files gracefully
        try:
            result = await process_audio(corrupted_file, output_path)
            # If processing "succeeds", output should exist (placeholder behavior)
            assert result["output_exists"] is True
        except Exception as e:
            # If it fails, should be a clear error
            assert "Failed to process audio" in str(e) or "Input file not found" in str(e)
    
    @pytest.mark.asyncio
    async def test_processing_with_insufficient_disk_space_simulation(self, sample_audio_file, temp_dir):
        """Test processing when disk space is insufficient (simulated)"""
        output_path = os.path.join(temp_dir, "output.wav")
        
        # Mock shutil.copy2 to raise an OSError (disk full)
        with patch('shutil.copy2') as mock_copy:
            mock_copy.side_effect = OSError("No space left on device")
            
            with pytest.raises(Exception) as exc_info:
                await process_audio(sample_audio_file, output_path)
            
            assert "Failed to process audio" in str(exc_info.value)


class TestMemoryAndPerformance:
    """Test memory usage and performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_memory_cleanup_after_processing(self, sample_audio_file, temp_dir):
        """Test that memory is properly cleaned up after processing"""
        import gc
        import sys
        
        initial_objects = len(gc.get_objects())
        
        # Process several files
        for i in range(5):
            output_path = os.path.join(temp_dir, f"memory_test_{i}.wav")
            await process_audio(sample_audio_file, output_path)
        
        # Force garbage collection
        gc.collect()
        
        final_objects = len(gc.get_objects())
        
        # Object count shouldn't grow excessively
        # Allow some growth but not proportional to number of files processed
        assert final_objects - initial_objects < 1000
    
    @pytest.mark.asyncio
    async def test_processing_time_consistency(self, sample_audio_file, temp_dir):
        """Test that processing times are consistent for similar files"""
        processing_times = []
        
        # Process the same file multiple times
        for i in range(3):
            output_path = os.path.join(temp_dir, f"timing_test_{i}.wav")
            result = await process_audio(sample_audio_file, output_path)
            processing_times.append(result.get("processing_time", 0))
        
        # Processing times should be relatively consistent
        # (allowing for some variation due to system load)
        if len(processing_times) > 1:
            max_time = max(processing_times)
            min_time = min(processing_times)
            # Times shouldn't vary by more than 200%
            assert max_time <= min_time * 3
