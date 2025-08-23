"""
Performance and Load Tests
Created by Sergie Code

Tests for performance, load handling, and resource management.
"""

import pytest
import time
import threading
import multiprocessing
import psutil
import os
import gc
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import wave
import numpy as np
from unittest.mock import patch
import asyncio

# Import test utilities
sys.path.append(str(Path(__file__).parent.parent))

from test_service import create_test_audio_file
from app.inference import process_audio, AudioEnhancer, audio_enhancer


class TestPerformanceBaseline:
    """Test performance baselines and benchmarks"""
    
    @pytest.mark.asyncio
    async def test_single_file_processing_time(self, temp_dir):
        """Test baseline processing time for single file"""
        # Create test file
        test_file = os.path.join(temp_dir, "performance_test.wav")
        create_test_audio_file(test_file, duration=2.0)
        output_file = os.path.join(temp_dir, "output.wav")
        
        # Measure processing time
        start_time = time.time()
        result = await process_audio(test_file, output_file)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Performance assertions
        assert result["output_exists"] is True
        assert processing_time < 10.0  # Should complete within 10 seconds
        
        # Log performance for reference
        print(f"Single file processing time: {processing_time:.2f} seconds")
    
    @pytest.mark.parametrize("duration", [0.5, 1.0, 2.0, 5.0, 10.0])
    @pytest.mark.asyncio
    async def test_processing_time_vs_file_duration(self, temp_dir, duration):
        """Test how processing time scales with file duration"""
        test_file = os.path.join(temp_dir, f"duration_test_{duration}s.wav")
        create_test_audio_file(test_file, duration=duration)
        output_file = os.path.join(temp_dir, f"output_{duration}s.wav")
        
        start_time = time.time()
        result = await process_audio(test_file, output_file)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        assert result["output_exists"] is True
        
        # Processing time should scale reasonably with file duration
        # For placeholder implementation, it should be minimal
        assert processing_time < duration * 2 + 5  # Max 2x file duration + 5 seconds overhead
        
        print(f"Duration: {duration}s, Processing time: {processing_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_memory_usage_single_file(self, temp_dir):
        """Test memory usage for single file processing"""
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process file
        test_file = os.path.join(temp_dir, "memory_test.wav")
        create_test_audio_file(test_file, duration=5.0)
        output_file = os.path.join(temp_dir, "output.wav")
        
        result = await process_audio(test_file, output_file)
        
        # Get peak memory usage
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        assert result["output_exists"] is True
        
        # Memory increase should be reasonable
        assert memory_increase < 500  # Less than 500MB increase
        
        print(f"Memory increase: {memory_increase:.2f} MB")


class TestConcurrentProcessing:
    """Test concurrent processing capabilities"""
    
    @pytest.mark.asyncio
    async def test_concurrent_file_processing(self, temp_dir):
        """Test processing multiple files concurrently"""
        num_files = 5
        tasks = []
        
        # Create test files and tasks
        for i in range(num_files):
            test_file = os.path.join(temp_dir, f"concurrent_{i}.wav")
            output_file = os.path.join(temp_dir, f"output_{i}.wav")
            create_test_audio_file(test_file, duration=1.0)
            
            task = process_audio(test_file, output_file)
            tasks.append(task)
        
        # Measure concurrent processing time
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        concurrent_time = end_time - start_time
        
        # All files should be processed successfully
        for result in results:
            assert result["output_exists"] is True
        
        # Concurrent processing should be faster than sequential
        # (though with placeholder implementation, this might not be significant)
        print(f"Concurrent processing time for {num_files} files: {concurrent_time:.2f}s")
        
        # Should complete within reasonable time
        assert concurrent_time < 30.0  # 30 seconds for 5 files
    
    def test_thread_safety(self, temp_dir):
        """Test thread safety of the audio enhancer"""
        num_threads = 10
        results = []
        errors = []
        
        def process_in_thread(thread_id):
            try:
                # Create unique test file for this thread
                test_file = os.path.join(temp_dir, f"thread_{thread_id}.wav")
                output_file = os.path.join(temp_dir, f"thread_output_{thread_id}.wav")
                create_test_audio_file(test_file, duration=1.0)
                
                # Process file (using asyncio.run for thread)
                result = asyncio.run(process_audio(test_file, output_file))
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Start threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=process_in_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=60)
        
        # Check results
        assert len(errors) == 0, f"Errors in threads: {errors}"
        assert len(results) == num_threads
        
        for result in results:
            assert result["output_exists"] is True
    
    def test_resource_cleanup_under_load(self, temp_dir):
        """Test resource cleanup under concurrent load"""
        initial_objects = len(gc.get_objects())
        
        def process_files_batch():
            for i in range(5):
                test_file = os.path.join(temp_dir, f"cleanup_{threading.current_thread().ident}_{i}.wav")
                output_file = os.path.join(temp_dir, f"cleanup_output_{threading.current_thread().ident}_{i}.wav")
                create_test_audio_file(test_file, duration=0.5)
                
                result = asyncio.run(process_audio(test_file, output_file))
                assert result["output_exists"] is True
        
        # Run multiple batches in threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=process_files_batch)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Force garbage collection
        gc.collect()
        
        final_objects = len(gc.get_objects())
        object_increase = final_objects - initial_objects
        
        # Object count shouldn't grow excessively
        assert object_increase < 5000, f"Too many objects created: {object_increase}"


class TestScalabilityLimits:
    """Test service scalability limits"""
    
    @pytest.mark.slow
    def test_maximum_concurrent_files(self, temp_dir):
        """Test maximum number of concurrent files that can be processed"""
        max_concurrent = 20
        success_count = 0
        
        def process_single_file(file_id):
            nonlocal success_count
            try:
                test_file = os.path.join(temp_dir, f"scale_{file_id}.wav")
                output_file = os.path.join(temp_dir, f"scale_output_{file_id}.wav")
                create_test_audio_file(test_file, duration=0.5)
                
                result = asyncio.run(process_audio(test_file, output_file))
                if result["output_exists"]:
                    success_count += 1
            except Exception as e:
                print(f"Error in file {file_id}: {e}")
        
        # Use ThreadPoolExecutor for controlled concurrency
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = [executor.submit(process_single_file, i) for i in range(max_concurrent)]
            
            # Wait for completion with timeout
            for future in as_completed(futures, timeout=120):
                try:
                    future.result()
                except Exception as e:
                    print(f"Future error: {e}")
        
        # Calculate success rate
        success_rate = success_count / max_concurrent
        print(f"Processed {success_count}/{max_concurrent} files successfully ({success_rate:.2%})")
        
        # Should handle most concurrent requests
        assert success_rate >= 0.8  # At least 80% success rate
    
    @pytest.mark.asyncio
    async def test_large_file_processing(self, temp_dir):
        """Test processing of large audio files"""
        # Create large test file (30 seconds)
        large_file = os.path.join(temp_dir, "large_test.wav")
        create_test_audio_file(large_file, duration=30.0)
        output_file = os.path.join(temp_dir, "large_output.wav")
        
        # Monitor memory during processing
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        start_time = time.time()
        result = await process_audio(large_file, output_file)
        end_time = time.time()
        
        peak_memory = process.memory_info().rss / 1024 / 1024
        processing_time = end_time - start_time
        memory_increase = peak_memory - initial_memory
        
        assert result["output_exists"] is True
        
        # Large files should still process in reasonable time
        assert processing_time < 60.0  # 1 minute max
        
        # Memory usage should be reasonable
        assert memory_increase < 1000  # Less than 1GB increase
        
        print(f"Large file processing: {processing_time:.2f}s, Memory: +{memory_increase:.2f}MB")


class TestResourceManagement:
    """Test resource management and limits"""
    
    def test_cpu_usage_monitoring(self, temp_dir):
        """Test CPU usage during processing"""
        # Monitor CPU usage during processing
        cpu_percentages = []
        
        def monitor_cpu():
            for _ in range(10):  # Monitor for 10 samples
                cpu_percentages.append(psutil.cpu_percent(interval=0.1))
        
        def process_files():
            for i in range(3):
                test_file = os.path.join(temp_dir, f"cpu_test_{i}.wav")
                output_file = os.path.join(temp_dir, f"cpu_output_{i}.wav")
                create_test_audio_file(test_file, duration=2.0)
                
                asyncio.run(process_audio(test_file, output_file))
        
        # Start monitoring and processing
        monitor_thread = threading.Thread(target=monitor_cpu)
        process_thread = threading.Thread(target=process_files)
        
        monitor_thread.start()
        process_thread.start()
        
        process_thread.join()
        monitor_thread.join()
        
        # Analyze CPU usage
        if cpu_percentages:
            avg_cpu = sum(cpu_percentages) / len(cpu_percentages)
            max_cpu = max(cpu_percentages)
            
            print(f"CPU usage - Average: {avg_cpu:.1f}%, Peak: {max_cpu:.1f}%")
            
            # CPU usage should be reasonable (not maxing out system)
            assert avg_cpu < 80.0  # Average should be less than 80%
    
    def test_file_descriptor_management(self, temp_dir):
        """Test file descriptor management"""
        initial_fds = len(psutil.Process().open_files())
        
        # Process many files to test file descriptor leaks
        for i in range(20):
            test_file = os.path.join(temp_dir, f"fd_test_{i}.wav")
            output_file = os.path.join(temp_dir, f"fd_output_{i}.wav")
            create_test_audio_file(test_file, duration=0.5)
            
            result = asyncio.run(process_audio(test_file, output_file))
            assert result["output_exists"] is True
        
        final_fds = len(psutil.Process().open_files())
        fd_increase = final_fds - initial_fds
        
        # File descriptor count shouldn't grow significantly
        assert fd_increase < 10, f"Too many file descriptors leaked: {fd_increase}"
    
    def test_temporary_file_cleanup(self, temp_dir):
        """Test temporary file cleanup"""
        # Count files before processing
        initial_file_count = len(list(Path(temp_dir).iterdir()))
        
        # Process files
        for i in range(10):
            test_file = os.path.join(temp_dir, f"temp_test_{i}.wav")
            output_file = os.path.join(temp_dir, f"temp_output_{i}.wav")
            create_test_audio_file(test_file, duration=0.5)
            
            result = asyncio.run(process_audio(test_file, output_file))
            assert result["output_exists"] is True
        
        # Count files after processing
        final_file_count = len(list(Path(temp_dir).iterdir()))
        
        # Should have created exactly 20 files (10 input + 10 output)
        expected_increase = 20
        actual_increase = final_file_count - initial_file_count
        
        assert actual_increase == expected_increase, f"Unexpected file count: {actual_increase} vs {expected_increase}"


class TestPerformanceRegression:
    """Test for performance regressions"""
    
    def test_processing_time_consistency(self, temp_dir):
        """Test that processing times are consistent across runs"""
        test_file = os.path.join(temp_dir, "consistency_test.wav")
        create_test_audio_file(test_file, duration=2.0)
        
        processing_times = []
        
        # Run same processing multiple times
        for i in range(5):
            output_file = os.path.join(temp_dir, f"consistency_output_{i}.wav")
            
            start_time = time.time()
            result = asyncio.run(process_audio(test_file, output_file))
            end_time = time.time()
            
            processing_time = end_time - start_time
            processing_times.append(processing_time)
            
            assert result["output_exists"] is True
        
        # Analyze consistency
        avg_time = sum(processing_times) / len(processing_times)
        max_deviation = max(abs(t - avg_time) for t in processing_times)
        
        print(f"Processing times: {processing_times}")
        print(f"Average: {avg_time:.2f}s, Max deviation: {max_deviation:.2f}s")
        
        # Times should be relatively consistent (within 50% of average)
        assert max_deviation < avg_time * 0.5
    
    @pytest.mark.asyncio
    async def test_memory_stability_over_time(self, temp_dir):
        """Test memory stability over extended processing"""
        process = psutil.Process()
        memory_readings = []
        
        # Process files over time
        for i in range(15):
            # Take memory reading
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_readings.append(current_memory)
            
            # Process a file
            test_file = os.path.join(temp_dir, f"stability_test_{i}.wav")
            output_file = os.path.join(temp_dir, f"stability_output_{i}.wav")
            create_test_audio_file(test_file, duration=1.0)
            
            result = await process_audio(test_file, output_file)
            assert result["output_exists"] is True
            
            # Force garbage collection
            gc.collect()
        
        # Analyze memory trend
        initial_memory = memory_readings[0]
        final_memory = memory_readings[-1]
        memory_growth = final_memory - initial_memory
        
        print(f"Memory growth over {len(memory_readings)} iterations: {memory_growth:.2f}MB")
        
        # Memory shouldn't grow significantly over time (indicates memory leaks)
        assert memory_growth < 100  # Less than 100MB growth over 15 iterations


class TestStressConditions:
    """Test service under stress conditions"""
    
    @pytest.mark.slow
    def test_rapid_successive_requests(self, temp_dir):
        """Test rapid successive processing requests"""
        test_file = os.path.join(temp_dir, "rapid_test.wav")
        create_test_audio_file(test_file, duration=0.5)
        
        success_count = 0
        error_count = 0
        
        # Make rapid successive requests
        for i in range(50):
            try:
                output_file = os.path.join(temp_dir, f"rapid_output_{i}.wav")
                result = asyncio.run(process_audio(test_file, output_file))
                
                if result["output_exists"]:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"Error in request {i}: {e}")
        
        total_requests = success_count + error_count
        success_rate = success_count / total_requests if total_requests > 0 else 0
        
        print(f"Rapid requests: {success_count}/{total_requests} successful ({success_rate:.2%})")
        
        # Should handle most rapid requests successfully
        assert success_rate >= 0.9  # At least 90% success rate
    
    def test_system_resource_exhaustion_simulation(self, temp_dir):
        """Test behavior when system resources are constrained"""
        # This test simulates resource constraints
        # In a real scenario, you might limit memory or CPU
        
        # Create multiple large files to stress the system
        large_files = []
        for i in range(3):
            large_file = os.path.join(temp_dir, f"stress_large_{i}.wav")
            create_test_audio_file(large_file, duration=10.0)
            large_files.append(large_file)
        
        # Process all large files concurrently
        def process_large_file(file_path):
            try:
                output_path = file_path.replace('.wav', '_output.wav')
                result = asyncio.run(process_audio(file_path, output_path))
                return result["output_exists"]
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                return False
        
        # Use threads to simulate concurrent load
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(process_large_file, f) for f in large_files]
            results = [future.result(timeout=180) for future in futures]
        
        # At least some files should process successfully
        success_count = sum(results)
        success_rate = success_count / len(results)
        
        print(f"Stress test: {success_count}/{len(results)} large files processed ({success_rate:.2%})")
        
        # Should handle at least half of the stress load
        assert success_rate >= 0.5
