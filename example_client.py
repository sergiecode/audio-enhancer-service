"""
Example client for Audio Enhancement Service
Created by Sergie Code

This script demonstrates how to interact with the audio enhancement service
from a Python client application.
"""

import requests
import tempfile
import wave
import numpy as np
import json
import time
from pathlib import Path


class AudioEnhancementClient:
    """Client for interacting with the Audio Enhancement Service"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def check_health(self) -> dict:
        """Check if the service is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "unhealthy"}
    
    def get_supported_formats(self) -> dict:
        """Get list of supported audio formats"""
        try:
            response = self.session.get(f"{self.base_url}/formats")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def process_audio(self, file_path: str) -> dict:
        """
        Process an audio file
        
        Args:
            file_path: Path to the audio file to process
            
        Returns:
            Dictionary with processing results
        """
        try:
            with open(file_path, 'rb') as audio_file:
                files = {'file': (Path(file_path).name, audio_file, 'audio/wav')}
                
                print(f"📤 Uploading: {file_path}")
                start_time = time.time()
                
                response = self.session.post(
                    f"{self.base_url}/process",
                    files=files
                )
                
                upload_time = time.time() - start_time
                response.raise_for_status()
                
                result = response.json()
                result['upload_time'] = round(upload_time, 2)
                
                return result
                
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "success": False}
    
    def download_file(self, filename: str, save_path: str) -> bool:
        """
        Download a processed audio file
        
        Args:
            filename: Name of the file to download
            save_path: Local path where to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/download/{filename}")
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            print(f"📥 Downloaded: {save_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Download failed: {str(e)}")
            return False


def create_sample_audio(filename: str, duration: float = 3.0):
    """Create a sample audio file for testing"""
    
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create a more interesting audio signal
    # Combine multiple frequencies for a richer sound
    frequencies = [440, 554.37, 659.25]  # A, C#, E (A major chord)
    audio_data = np.zeros_like(t)
    
    for freq in frequencies:
        audio_data += np.sin(2 * np.pi * freq * t) / len(frequencies)
    
    # Add some amplitude modulation for interest
    audio_data *= (1 + 0.3 * np.sin(2 * np.pi * 2 * t))
    
    # Convert to 16-bit PCM
    audio_data = (audio_data * 32767 * 0.8).astype(np.int16)
    
    # Write WAV file
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes = 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    print(f"🎵 Created sample audio: {filename}")


def main():
    """Example usage of the Audio Enhancement Client"""
    
    print("🎵 Audio Enhancement Service - Client Example")
    print("=" * 50)
    
    # Initialize client
    client = AudioEnhancementClient()
    
    # Check service health
    print("🏥 Checking service health...")
    health = client.check_health()
    print(f"   Status: {health.get('status', 'unknown')}")
    
    if health.get('status') != 'healthy':
        print("❌ Service is not healthy. Please start the service first.")
        print("   Run: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return
    
    # Get supported formats
    print("\n📋 Getting supported formats...")
    formats = client.get_supported_formats()
    if 'supported_formats' in formats:
        print(f"   Supported: {', '.join(formats['supported_formats'])}")
    
    # Create a test audio file
    print("\n🎵 Creating test audio file...")
    test_file = "test_audio.wav"
    create_sample_audio(test_file, duration=2.0)
    
    try:
        # Process the audio
        print("\n🔄 Processing audio...")
        result = client.process_audio(test_file)
        
        if result.get('success'):
            print("✅ Processing successful!")
            print(f"   Upload time: {result.get('upload_time')} seconds")
            print(f"   Processing time: {result['processing_details'].get('processing_time')} seconds")
            print(f"   Output file: {result.get('output_file')}")
            
            # Download the processed file
            if result.get('output_file'):
                output_filename = result['output_file']
                download_path = f"enhanced_{output_filename}"
                
                print(f"\n📥 Downloading processed file...")
                if client.download_file(output_filename, download_path):
                    print(f"✅ File saved as: {download_path}")
                else:
                    print("❌ Download failed")
        else:
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
    
    finally:
        # Cleanup
        import os
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n🧹 Cleaned up: {test_file}")
    
    print("\n🎯 Example completed!")
    print("\n💡 Integration Tips:")
    print("   - Use the AudioEnhancementClient class in your applications")
    print("   - Handle errors gracefully with try-catch blocks")
    print("   - Monitor processing times for performance optimization")
    print("   - Implement file cleanup for temporary files")


if __name__ == "__main__":
    main()
