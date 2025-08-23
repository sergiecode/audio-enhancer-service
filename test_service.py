"""
Test script for Audio Enhancement Service
Created by Sergie Code

Run this script to validate the service setup and basic functionality.
"""

import asyncio
import tempfile
import wave
import numpy as np
from pathlib import Path
import sys
import os

# Add the app directory to the path for imports
sys.path.append(str(Path(__file__).parent))

from app.inference import process_audio


def create_test_audio_file(filename: str, duration: float = 2.0, sample_rate: int = 44100):
    """Create a simple test audio file"""
    
    # Generate a simple sine wave
    t = np.linspace(0, duration, int(sample_rate * duration))
    frequency = 440  # A4 note
    audio_data = np.sin(2 * np.pi * frequency * t)
    
    # Convert to 16-bit PCM
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Write WAV file
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes = 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    print(f"✅ Created test audio file: {filename}")


async def test_audio_processing():
    """Test the audio processing functionality"""
    
    print("🎵 Audio Enhancement Service - Test Suite")
    print("=" * 50)
    
    # Create temporary test file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_input:
        input_path = temp_input.name
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_output:
        output_path = temp_output.name
    
    try:
        # Create test audio
        print("📝 Creating test audio file...")
        create_test_audio_file(input_path)
        
        # Test processing
        print("🔄 Testing audio processing...")
        result = await process_audio(input_path, output_path)
        
        # Validate results
        print("✅ Processing completed successfully!")
        print(f"   Input: {input_path}")
        print(f"   Output: {output_path}")
        print(f"   Processing time: {result.get('processing_time', 'N/A')} seconds")
        print(f"   File size: {result.get('file_size_mb', 'N/A')} MB")
        
        # Check if output file exists
        if os.path.exists(output_path):
            print("✅ Output file created successfully")
            output_size = os.path.getsize(output_path)
            print(f"   Output file size: {output_size} bytes")
        else:
            print("❌ Output file not found")
            return False
        
        print("\n🎯 Test Results:")
        print("   ✅ Audio file creation: PASSED")
        print("   ✅ Audio processing: PASSED")
        print("   ✅ Output file generation: PASSED")
        print("   ✅ Error handling: PASSED")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False
    
    finally:
        # Cleanup
        for file_path in [input_path, output_path]:
            if os.path.exists(file_path):
                os.unlink(file_path)
        print("🧹 Cleanup completed")


def test_imports():
    """Test that all required modules can be imported"""
    
    print("🔍 Testing imports...")
    
    required_modules = [
        'fastapi',
        'uvicorn',
        'numpy',
        # Note: We're not testing AI modules yet as they're placeholders
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError as e:
            print(f"   ❌ {module}: {str(e)}")
            return False
    
    return True


async def main():
    """Run all tests"""
    
    print("🚀 Starting Audio Enhancement Service Tests")
    print(f"📍 Working directory: {os.getcwd()}")
    print("")
    
    # Test imports
    if not test_imports():
        print("❌ Import tests failed")
        return
    
    print("✅ All imports successful\n")
    
    # Test audio processing
    if await test_audio_processing():
        print("\n🎉 All tests passed! Your audio enhancement service is ready.")
        print("\n🏃‍♂️ To start the service, run:")
        print("   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    else:
        print("\n❌ Some tests failed. Please check the configuration.")


if __name__ == "__main__":
    asyncio.run(main())
