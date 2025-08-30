# 🎵 Audio Enhancement Microservice

**Created by Sergie Code** - AI Tools for Musicians

A professional Python microservice for offline audio enhancement, featuring AI-powered noise reduction, vocal/instrument separation, and audio quality improvement. Built with FastAPI for seamless integration with .NET backends and other systems.

## 🎯 Project Overview

This microservice provides state-of-the-art audio enhancement capabilities through a REST API, designed specifically for musicians, audio engineers, and content creators. The service leverages cutting-edge AI models to deliver:

- **Noise Reduction**: Intelligent background noise removal
- **Source Separation**: Vocal and instrumental track isolation using Demucs and Spleeter
- **Audio Quality Enhancement**: AI-powered audio restoration and improvement
- **Format Support**: WAV, MP3, FLAC, M4A, AAC, OGG

Perfect for integration with .NET applications, web platforms, and mobile apps requiring professional audio processing capabilities.

## 🚀 Features

- ✅ **FastAPI Framework**: High-performance, async API with automatic documentation
- ✅ **AI Model Integration**: Ready for Demucs, Spleeter, and custom models
- ✅ **Docker Support**: Production-ready containerization
- ✅ **File Management**: Secure upload/download with unique file handling
- ✅ **CORS Support**: Cross-origin requests for web integration
- ✅ **Health Monitoring**: Built-in health checks and processing statistics
- ✅ **Professional Logging**: Comprehensive error handling and monitoring

## 📋 Requirements

- Python 3.11+
- 4GB+ RAM (8GB recommended for AI models)
- 2GB+ disk space for models and temporary files
- Optional: NVIDIA GPU for accelerated processing

## 🛠️ Installation

### Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd audio-enhancer-service
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create necessary directories**:
   ```bash
   mkdir uploads outputs models
   ```

### 🐳 Docker Installation

1. **Build the Docker image**:
   ```bash
   docker build -t audio-enhancer-service .
   ```

2. **Run the container**:
   ```bash
   docker run -d \
     --name audio-enhancer \
     -p 8000:8000 \
     -v $(pwd)/uploads:/app/uploads \
     -v $(pwd)/outputs:/app/outputs \
     audio-enhancer-service
   ```

## 🏃‍♂️ Running the Service

### Local Development

```bash
# Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Using Python module
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The service will be available at: `http://localhost:8000`

- **API Documentation**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

## 📡 API Documentation

### Endpoints

#### `POST /process`
Process an audio file for enhancement.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Audio file (WAV, MP3, FLAC, M4A, AAC, OGG)

**Response:**
```json
{
  "success": true,
  "message": "Audio processing completed successfully",
  "input_file": "original_audio.wav",
  "output_file": "uuid_enhanced.wav",
  "output_path": "/app/outputs/uuid_enhanced.wav",
  "processing_id": "uuid-string",
  "processing_details": {
    "processing_time": 2.45,
    "file_size_mb": 12.3,
    "enhancement_applied": "noise_reduction,source_separation"
  },
  "download_url": "/download/uuid_enhanced.wav"
}
```

#### `GET /download/{filename}`
Download processed audio file.

#### `GET /health`
Service health check endpoint.

#### `GET /formats`
Get supported audio formats.

### 📝 Example Requests

#### Using cURL

```bash
# Process audio file
curl -X POST "http://localhost:8000/process" \
     -F "file=@sample_audio.wav" \
     -H "accept: application/json"

# Download processed file
curl -O "http://localhost:8000/download/processed_audio.wav"

# Health check
curl "http://localhost:8000/health"
```

#### Using Python

```python
import requests

# Upload and process audio
with open('sample_audio.wav', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/process',
        files={'file': f}
    )
    result = response.json()
    print(f"Processing completed: {result['output_file']}")

# Download processed file
download_url = result['download_url']
response = requests.get(f'http://localhost:8000{download_url}')
with open('enhanced_audio.wav', 'wb') as f:
    f.write(response.content)
```

#### Using JavaScript/Node.js

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

async function processAudio(filePath) {
    const form = new FormData();
    form.append('file', fs.createReadStream(filePath));
    
    const response = await axios.post(
        'http://localhost:8000/process',
        form,
        { headers: form.getHeaders() }
    );
    
    console.log('Processing result:', response.data);
    return response.data;
}
```

## 🔗 .NET Backend Integration

### C# Example

```csharp
using System;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;

public class AudioEnhancementService
{
    private readonly HttpClient _httpClient;
    private readonly string _serviceUrl = "http://localhost:8000";

    public AudioEnhancementService()
    {
        _httpClient = new HttpClient();
    }

    public async Task<string> ProcessAudioAsync(string filePath)
    {
        using var form = new MultipartFormDataContent();
        using var fileStream = File.OpenRead(filePath);
        using var fileContent = new StreamContent(fileStream);
        
        fileContent.Headers.ContentType = 
            MediaTypeHeaderValue.Parse("audio/wav");
        form.Add(fileContent, "file", Path.GetFileName(filePath));

        var response = await _httpClient.PostAsync(
            $"{_serviceUrl}/process", form);
        
        var result = await response.Content.ReadAsStringAsync();
        return result;
    }
}
```

### Integration Notes

- **Async Processing**: The service supports async operations for better performance
- **Error Handling**: Comprehensive error responses with HTTP status codes
- **File Management**: Automatic cleanup and unique file naming
- **Monitoring**: Built-in statistics for performance monitoring
- **Scalability**: Docker support for easy deployment and scaling

## 🔧 Configuration

### Environment Variables

```bash
# Optional configuration
export UPLOAD_DIR="/custom/upload/path"
export OUTPUT_DIR="/custom/output/path"
export MAX_FILE_SIZE="100MB"
export WORKER_COUNT="4"
```

### Docker Compose Example

```yaml
version: '3.8'
services:
  audio-enhancer:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
      - ./models:/app/models
    environment:
      - WORKER_COUNT=2
    restart: unless-stopped
```

## 🧪 Development & Testing

```bash
# Run tests
pytest tests/

# Code formatting
black app/

# Linting
flake8 app/

# Type checking
mypy app/
```

## 📈 Performance & Monitoring

- **Processing Time**: Varies by file size (typically 0.5-5 seconds)
- **Memory Usage**: 1-4GB depending on AI models loaded
- **Concurrent Requests**: Supports multiple simultaneous uploads
- **Health Checks**: Built-in monitoring for production deployment

## 🔮 Roadmap

- [ ] **AI Model Integration**: Full Demucs and Spleeter implementation
- [ ] **Real-time Processing**: WebSocket support for live audio
- [ ] **Custom Models**: Support for user-trained models
- [ ] **Batch Processing**: Multiple file processing
- [ ] **Cloud Storage**: S3/Azure Blob integration
- [ ] **Authentication**: JWT-based API security

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 👨‍💻 About the Author

**Sergie Code** - Software Engineer & YouTube Educator

Passionate about creating AI tools for musicians and teaching programming through practical projects. Follow my journey on YouTube where I share tutorials on AI, Python, and software development.

- 📸 Instagram: https://www.instagram.com/sergiecode

- 🧑🏼‍💻 LinkedIn: https://www.linkedin.com/in/sergiecode/

- 📽️Youtube: https://www.youtube.com/@SergieCode

- 😺 Github: https://github.com/sergiecode

- 👤 Facebook: https://www.facebook.com/sergiecodeok

- 🎞️ Tiktok: https://www.tiktok.com/@sergiecode

- 🕊️Twitter: https://twitter.com/sergiecode

- 🧵Threads: https://www.threads.net/@sergiecode

---


*Built with ❤️ for the music and developer community*


