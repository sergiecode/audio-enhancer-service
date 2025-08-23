# 🎵 Audio Enhancement Service - C# .NET Backend Integration Guide

**Created by Sergie Code** - AI Tools for Musicians

This guide provides comprehensive instructions for integrating the Audio Enhancement Microservice with C# .NET backends. Perfect for developers building music applications, content management systems, or any application requiring professional audio processing capabilities.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Service Setup](#service-setup)
3. [.NET Integration](#net-integration)
4. [Implementation Examples](#implementation-examples)
5. [Advanced Scenarios](#advanced-scenarios)
6. [Error Handling](#error-handling)
7. [Performance Optimization](#performance-optimization)
8. [Deployment Strategies](#deployment-strategies)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### System Requirements
- **.NET 6.0+** (Recommended: .NET 8.0)
- **Python 3.11+** (for the audio service)
- **Docker** (optional, for containerized deployment)
- **4GB+ RAM** (8GB recommended for AI models)
- **Windows 10/11, macOS, or Linux**

### Required NuGet Packages
```xml
<PackageReference Include="Microsoft.Extensions.Http" Version="8.0.0" />
<PackageReference Include="Newtonsoft.Json" Version="13.0.3" />
<PackageReference Include="Microsoft.Extensions.DependencyInjection" Version="8.0.0" />
<PackageReference Include="Microsoft.Extensions.Logging" Version="8.0.0" />
<PackageReference Include="Microsoft.Extensions.Configuration" Version="8.0.0" />
```

## 🚀 Service Setup

### 1. Clone and Start the Audio Service

```bash
# Clone the repository
git clone https://github.com/sergiecode/audio-enhancer-service.git
cd audio-enhancer-service

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
venv\Scripts\Activate.ps1
# Windows Command Prompt:
venv\Scripts\activate.bat
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir uploads, outputs, models -Force  # PowerShell
# or
New-Item -ItemType Directory -Path uploads, outputs, models -Force

# Start the service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Verify Service is Running

Open your browser and navigate to:
- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

## 🔗 .NET Integration

### 1. Create the Audio Enhancement Client

```csharp
using System.Text.Json;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace AudioEnhancement.Services
{
    public class AudioEnhancementOptions
    {
        public string ServiceUrl { get; set; } = "http://localhost:8000";
        public int TimeoutSeconds { get; set; } = 300; // 5 minutes
        public long MaxFileSizeBytes { get; set; } = 100 * 1024 * 1024; // 100MB
    }

    public class AudioProcessingResult
    {
        public bool Success { get; set; }
        public string Message { get; set; } = string.Empty;
        public string InputFile { get; set; } = string.Empty;
        public string OutputFile { get; set; } = string.Empty;
        public string OutputPath { get; set; } = string.Empty;
        public string ProcessingId { get; set; } = string.Empty;
        public ProcessingDetails ProcessingDetails { get; set; } = new();
        public string DownloadUrl { get; set; } = string.Empty;
    }

    public class ProcessingDetails
    {
        public double ProcessingTime { get; set; }
        public double FileSizeMb { get; set; }
        public string EnhancementApplied { get; set; } = string.Empty;
    }

    public class AudioEnhancementService
    {
        private readonly HttpClient _httpClient;
        private readonly ILogger<AudioEnhancementService> _logger;
        private readonly AudioEnhancementOptions _options;

        public AudioEnhancementService(
            HttpClient httpClient, 
            ILogger<AudioEnhancementService> logger,
            IOptions<AudioEnhancementOptions> options)
        {
            _httpClient = httpClient;
            _logger = logger;
            _options = options.Value;
            
            _httpClient.BaseAddress = new Uri(_options.ServiceUrl);
            _httpClient.Timeout = TimeSpan.FromSeconds(_options.TimeoutSeconds);
        }

        public async Task<AudioProcessingResult> ProcessAudioAsync(
            string filePath, 
            CancellationToken cancellationToken = default)
        {
            try
            {
                _logger.LogInformation("Starting audio processing for file: {FilePath}", filePath);

                // Validate file
                var fileInfo = new FileInfo(filePath);
                if (!fileInfo.Exists)
                    throw new FileNotFoundException($"Audio file not found: {filePath}");

                if (fileInfo.Length > _options.MaxFileSizeBytes)
                    throw new ArgumentException($"File size exceeds maximum allowed: {fileInfo.Length} bytes");

                // Prepare multipart form data
                using var form = new MultipartFormDataContent();
                using var fileStream = File.OpenRead(filePath);
                using var fileContent = new StreamContent(fileStream);
                
                fileContent.Headers.ContentType = GetContentType(fileInfo.Extension);
                form.Add(fileContent, "file", fileInfo.Name);

                // Send request
                var response = await _httpClient.PostAsync("/process", form, cancellationToken);
                
                if (!response.IsSuccessStatusCode)
                {
                    var errorContent = await response.Content.ReadAsStringAsync();
                    throw new HttpRequestException($"API request failed: {response.StatusCode} - {errorContent}");
                }

                var jsonResult = await response.Content.ReadAsStringAsync();
                var result = JsonSerializer.Deserialize<AudioProcessingResult>(jsonResult, new JsonSerializerOptions
                {
                    PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower
                });

                _logger.LogInformation("Audio processing completed successfully for {ProcessingId}", result?.ProcessingId);
                return result ?? new AudioProcessingResult { Success = false, Message = "Invalid response format" };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error processing audio file: {FilePath}", filePath);
                return new AudioProcessingResult 
                { 
                    Success = false, 
                    Message = $"Processing failed: {ex.Message}" 
                };
            }
        }

        public async Task<byte[]> DownloadProcessedAudioAsync(
            string downloadUrl, 
            CancellationToken cancellationToken = default)
        {
            try
            {
                _logger.LogInformation("Downloading processed audio from: {DownloadUrl}", downloadUrl);

                var response = await _httpClient.GetAsync(downloadUrl, cancellationToken);
                response.EnsureSuccessStatusCode();

                return await response.Content.ReadAsByteArrayAsync();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error downloading processed audio from: {DownloadUrl}", downloadUrl);
                throw;
            }
        }

        public async Task<bool> IsServiceHealthyAsync(CancellationToken cancellationToken = default)
        {
            try
            {
                var response = await _httpClient.GetAsync("/health", cancellationToken);
                return response.IsSuccessStatusCode;
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Health check failed");
                return false;
            }
        }

        private static MediaTypeHeaderValue GetContentType(string fileExtension)
        {
            return fileExtension.ToLowerInvariant() switch
            {
                ".wav" => MediaTypeHeaderValue.Parse("audio/wav"),
                ".mp3" => MediaTypeHeaderValue.Parse("audio/mpeg"),
                ".flac" => MediaTypeHeaderValue.Parse("audio/flac"),
                ".m4a" => MediaTypeHeaderValue.Parse("audio/mp4"),
                ".aac" => MediaTypeHeaderValue.Parse("audio/aac"),
                ".ogg" => MediaTypeHeaderValue.Parse("audio/ogg"),
                _ => MediaTypeHeaderValue.Parse("application/octet-stream")
            };
        }
    }
}
```

### 2. Dependency Injection Setup

```csharp
// Program.cs (.NET 6+)
using AudioEnhancement.Services;

var builder = WebApplication.CreateBuilder(args);

// Add services
builder.Services.AddHttpClient<AudioEnhancementService>();
builder.Services.Configure<AudioEnhancementOptions>(
    builder.Configuration.GetSection("AudioEnhancement"));

var app = builder.Build();

// Configure the HTTP request pipeline
app.MapControllers();
app.Run();
```

```csharp
// Startup.cs (.NET 5 and earlier)
public void ConfigureServices(IServiceCollection services)
{
    services.AddHttpClient<AudioEnhancementService>();
    services.Configure<AudioEnhancementOptions>(
        Configuration.GetSection("AudioEnhancement"));
    
    services.AddControllers();
}
```

### 3. Configuration (appsettings.json)

```json
{
  "AudioEnhancement": {
    "ServiceUrl": "http://localhost:8000",
    "TimeoutSeconds": 300,
    "MaxFileSizeBytes": 104857600
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "AudioEnhancement": "Debug"
    }
  }
}
```

## 💡 Implementation Examples

### 1. ASP.NET Core Web API Controller

```csharp
using Microsoft.AspNetCore.Mvc;
using AudioEnhancement.Services;

[ApiController]
[Route("api/[controller]")]
public class AudioController : ControllerBase
{
    private readonly AudioEnhancementService _audioService;
    private readonly ILogger<AudioController> _logger;

    public AudioController(AudioEnhancementService audioService, ILogger<AudioController> logger)
    {
        _audioService = audioService;
        _logger = logger;
    }

    [HttpPost("enhance")]
    public async Task<IActionResult> EnhanceAudio(IFormFile audioFile)
    {
        if (audioFile == null || audioFile.Length == 0)
            return BadRequest("No audio file provided");

        try
        {
            // Save uploaded file temporarily
            var tempFilePath = Path.GetTempFileName();
            using (var stream = new FileStream(tempFilePath, FileMode.Create))
            {
                await audioFile.CopyToAsync(stream);
            }

            // Process the audio
            var result = await _audioService.ProcessAudioAsync(tempFilePath);
            
            // Clean up temp file
            System.IO.File.Delete(tempFilePath);

            if (!result.Success)
                return BadRequest(result.Message);

            return Ok(new
            {
                success = true,
                processingId = result.ProcessingId,
                downloadUrl = result.DownloadUrl,
                processingDetails = result.ProcessingDetails
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error enhancing audio file");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("download/{filename}")]
    public async Task<IActionResult> DownloadEnhancedAudio(string filename)
    {
        try
        {
            var audioData = await _audioService.DownloadProcessedAudioAsync($"/download/{filename}");
            return File(audioData, "audio/wav", filename);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error downloading enhanced audio: {Filename}", filename);
            return NotFound();
        }
    }

    [HttpGet("health")]
    public async Task<IActionResult> GetHealthStatus()
    {
        var isHealthy = await _audioService.IsServiceHealthyAsync();
        return Ok(new { healthy = isHealthy });
    }
}
```

### 2. Background Service for Batch Processing

```csharp
using Microsoft.Extensions.Hosting;
using AudioEnhancement.Services;

public class AudioProcessingBackgroundService : BackgroundService
{
    private readonly AudioEnhancementService _audioService;
    private readonly ILogger<AudioProcessingBackgroundService> _logger;
    private readonly string _inputDirectory;
    private readonly string _outputDirectory;

    public AudioProcessingBackgroundService(
        AudioEnhancementService audioService,
        ILogger<AudioProcessingBackgroundService> logger,
        IConfiguration configuration)
    {
        _audioService = audioService;
        _logger = logger;
        _inputDirectory = configuration["BatchProcessing:InputDirectory"];
        _outputDirectory = configuration["BatchProcessing:OutputDirectory"];
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                await ProcessPendingFiles(stoppingToken);
                await Task.Delay(TimeSpan.FromMinutes(1), stoppingToken);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error in background audio processing");
                await Task.Delay(TimeSpan.FromMinutes(5), stoppingToken);
            }
        }
    }

    private async Task ProcessPendingFiles(CancellationToken cancellationToken)
    {
        var audioFiles = Directory.GetFiles(_inputDirectory, "*.*")
            .Where(file => IsAudioFile(file))
            .ToList();

        foreach (var file in audioFiles)
        {
            if (cancellationToken.IsCancellationRequested)
                break;

            try
            {
                _logger.LogInformation("Processing file: {File}", file);
                
                var result = await _audioService.ProcessAudioAsync(file, cancellationToken);
                
                if (result.Success)
                {
                    // Download and save the processed file
                    var processedAudio = await _audioService.DownloadProcessedAudioAsync(
                        result.DownloadUrl, cancellationToken);
                    
                    var outputPath = Path.Combine(_outputDirectory, result.OutputFile);
                    await System.IO.File.WriteAllBytesAsync(outputPath, processedAudio, cancellationToken);
                    
                    // Move original file to processed folder
                    var processedFolder = Path.Combine(_inputDirectory, "processed");
                    Directory.CreateDirectory(processedFolder);
                    System.IO.File.Move(file, Path.Combine(processedFolder, Path.GetFileName(file)));
                    
                    _logger.LogInformation("Successfully processed: {File}", file);
                }
                else
                {
                    _logger.LogWarning("Failed to process file {File}: {Message}", file, result.Message);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error processing file: {File}", file);
            }
        }
    }

    private static bool IsAudioFile(string filePath)
    {
        var extension = Path.GetExtension(filePath).ToLowerInvariant();
        return new[] { ".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg" }.Contains(extension);
    }
}
```

### 3. Minimal API Example

```csharp
// Program.cs
using AudioEnhancement.Services;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddHttpClient<AudioEnhancementService>();
builder.Services.Configure<AudioEnhancementOptions>(
    builder.Configuration.GetSection("AudioEnhancement"));

var app = builder.Build();

app.MapPost("/api/audio/enhance", async (
    IFormFile file,
    AudioEnhancementService audioService,
    ILogger<Program> logger) =>
{
    if (file == null || file.Length == 0)
        return Results.BadRequest("No audio file provided");

    var tempFilePath = Path.GetTempFileName();
    try
    {
        using (var stream = new FileStream(tempFilePath, FileMode.Create))
        {
            await file.CopyToAsync(stream);
        }

        var result = await audioService.ProcessAudioAsync(tempFilePath);
        return result.Success ? Results.Ok(result) : Results.BadRequest(result.Message);
    }
    catch (Exception ex)
    {
        logger.LogError(ex, "Error processing audio");
        return Results.Problem("Internal server error");
    }
    finally
    {
        if (System.IO.File.Exists(tempFilePath))
            System.IO.File.Delete(tempFilePath);
    }
});

app.Run();
```

## 🚀 Advanced Scenarios

### 1. Async Processing with Queues

```csharp
using Microsoft.Extensions.Hosting;
using System.Collections.Concurrent;

public class AudioProcessingQueue
{
    private readonly ConcurrentQueue<AudioProcessingJob> _jobs = new();
    private readonly SemaphoreSlim _semaphore = new(1, 1);

    public void EnqueueJob(AudioProcessingJob job)
    {
        _jobs.Enqueue(job);
    }

    public bool TryDequeue(out AudioProcessingJob job)
    {
        return _jobs.TryDequeue(out job);
    }

    public int Count => _jobs.Count;
}

public class AudioProcessingJob
{
    public string Id { get; set; } = Guid.NewGuid().ToString();
    public string FilePath { get; set; }
    public string UserId { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public AudioProcessingStatus Status { get; set; } = AudioProcessingStatus.Pending;
    public string Result { get; set; }
}

public enum AudioProcessingStatus
{
    Pending,
    Processing,
    Completed,
    Failed
}

public class QueuedAudioProcessingService : BackgroundService
{
    private readonly AudioProcessingQueue _queue;
    private readonly AudioEnhancementService _audioService;
    private readonly ILogger<QueuedAudioProcessingService> _logger;

    public QueuedAudioProcessingService(
        AudioProcessingQueue queue,
        AudioEnhancementService audioService,
        ILogger<QueuedAudioProcessingService> logger)
    {
        _queue = queue;
        _audioService = audioService;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            if (_queue.TryDequeue(out var job))
            {
                await ProcessJob(job, stoppingToken);
            }
            else
            {
                await Task.Delay(1000, stoppingToken);
            }
        }
    }

    private async Task ProcessJob(AudioProcessingJob job, CancellationToken cancellationToken)
    {
        try
        {
            job.Status = AudioProcessingStatus.Processing;
            _logger.LogInformation("Processing job {JobId}", job.Id);

            var result = await _audioService.ProcessAudioAsync(job.FilePath, cancellationToken);
            
            if (result.Success)
            {
                job.Status = AudioProcessingStatus.Completed;
                job.Result = result.DownloadUrl;
                _logger.LogInformation("Job {JobId} completed successfully", job.Id);
            }
            else
            {
                job.Status = AudioProcessingStatus.Failed;
                job.Result = result.Message;
                _logger.LogWarning("Job {JobId} failed: {Message}", job.Id, result.Message);
            }
        }
        catch (Exception ex)
        {
            job.Status = AudioProcessingStatus.Failed;
            job.Result = ex.Message;
            _logger.LogError(ex, "Error processing job {JobId}", job.Id);
        }
    }
}
```

### 2. Caching Enhancement Results

```csharp
using Microsoft.Extensions.Caching.Memory;
using System.Security.Cryptography;
using System.Text;

public class CachedAudioEnhancementService
{
    private readonly AudioEnhancementService _audioService;
    private readonly IMemoryCache _cache;
    private readonly ILogger<CachedAudioEnhancementService> _logger;

    public CachedAudioEnhancementService(
        AudioEnhancementService audioService,
        IMemoryCache cache,
        ILogger<CachedAudioEnhancementService> logger)
    {
        _audioService = audioService;
        _cache = cache;
        _logger = logger;
    }

    public async Task<AudioProcessingResult> ProcessAudioWithCacheAsync(
        string filePath,
        CancellationToken cancellationToken = default)
    {
        var fileHash = await CalculateFileHashAsync(filePath);
        var cacheKey = $"audio_processing_{fileHash}";

        if (_cache.TryGetValue(cacheKey, out AudioProcessingResult cachedResult))
        {
            _logger.LogInformation("Cache hit for file hash: {FileHash}", fileHash);
            return cachedResult;
        }

        _logger.LogInformation("Cache miss for file hash: {FileHash}", fileHash);
        var result = await _audioService.ProcessAudioAsync(filePath, cancellationToken);

        if (result.Success)
        {
            var cacheOptions = new MemoryCacheEntryOptions
            {
                AbsoluteExpirationRelativeToNow = TimeSpan.FromHours(24),
                SlidingExpiration = TimeSpan.FromHours(2)
            };
            _cache.Set(cacheKey, result, cacheOptions);
        }

        return result;
    }

    private static async Task<string> CalculateFileHashAsync(string filePath)
    {
        using var sha256 = SHA256.Create();
        using var stream = File.OpenRead(filePath);
        var hashBytes = await sha256.ComputeHashAsync(stream);
        return Convert.ToBase64String(hashBytes);
    }
}
```

## ⚠️ Error Handling

### Custom Exception Classes

```csharp
public class AudioEnhancementException : Exception
{
    public AudioEnhancementException(string message) : base(message) { }
    public AudioEnhancementException(string message, Exception innerException) : base(message, innerException) { }
}

public class AudioServiceUnavailableException : AudioEnhancementException
{
    public AudioServiceUnavailableException() : base("Audio enhancement service is unavailable") { }
}

public class UnsupportedAudioFormatException : AudioEnhancementException
{
    public UnsupportedAudioFormatException(string format) 
        : base($"Unsupported audio format: {format}") { }
}

public class AudioFileTooLargeException : AudioEnhancementException
{
    public AudioFileTooLargeException(long size, long maxSize) 
        : base($"Audio file size ({size} bytes) exceeds maximum allowed ({maxSize} bytes)") { }
}
```

### Enhanced Error Handling

```csharp
public class RobustAudioEnhancementService
{
    private readonly AudioEnhancementService _audioService;
    private readonly ILogger<RobustAudioEnhancementService> _logger;
    private readonly int _maxRetries = 3;

    public async Task<AudioProcessingResult> ProcessAudioWithRetryAsync(
        string filePath,
        CancellationToken cancellationToken = default)
    {
        var attempt = 0;
        Exception lastException = null;

        while (attempt < _maxRetries)
        {
            try
            {
                // Check service health before processing
                if (!await _audioService.IsServiceHealthyAsync(cancellationToken))
                {
                    throw new AudioServiceUnavailableException();
                }

                return await _audioService.ProcessAudioAsync(filePath, cancellationToken);
            }
            catch (HttpRequestException ex) when (attempt < _maxRetries - 1)
            {
                attempt++;
                lastException = ex;
                var delay = TimeSpan.FromSeconds(Math.Pow(2, attempt)); // Exponential backoff
                _logger.LogWarning("Audio processing attempt {Attempt} failed, retrying in {Delay}s: {Error}", 
                    attempt, delay.TotalSeconds, ex.Message);
                await Task.Delay(delay, cancellationToken);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Audio processing failed on attempt {Attempt}", attempt + 1);
                throw;
            }
        }

        throw new AudioEnhancementException($"Audio processing failed after {_maxRetries} attempts", lastException);
    }
}
```

## 🔧 Performance Optimization

### 1. Connection Pooling and HTTP Client Configuration

```csharp
// Program.cs or Startup.cs
builder.Services.AddHttpClient<AudioEnhancementService>(client =>
{
    client.BaseAddress = new Uri("http://localhost:8000");
    client.Timeout = TimeSpan.FromMinutes(10);
})
.ConfigurePrimaryHttpMessageHandler(() => new HttpClientHandler()
{
    MaxConnectionsPerServer = 10,
    UseCookies = false
});
```

### 2. Parallel Processing

```csharp
public class ParallelAudioProcessor
{
    private readonly AudioEnhancementService _audioService;
    private readonly SemaphoreSlim _semaphore;

    public ParallelAudioProcessor(AudioEnhancementService audioService, int maxConcurrency = 3)
    {
        _audioService = audioService;
        _semaphore = new SemaphoreSlim(maxConcurrency, maxConcurrency);
    }

    public async Task<List<AudioProcessingResult>> ProcessMultipleFilesAsync(
        IEnumerable<string> filePaths,
        CancellationToken cancellationToken = default)
    {
        var tasks = filePaths.Select(async filePath =>
        {
            await _semaphore.WaitAsync(cancellationToken);
            try
            {
                return await _audioService.ProcessAudioAsync(filePath, cancellationToken);
            }
            finally
            {
                _semaphore.Release();
            }
        });

        return (await Task.WhenAll(tasks)).ToList();
    }
}
```

## 🐳 Deployment Strategies

### 1. Docker Compose for Complete Solution

```yaml
# docker-compose.yml
version: '3.8'

services:
  audio-enhancer-api:
    build: ./audio-enhancer-service
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
      - ./models:/app/models
    environment:
      - WORKER_COUNT=2
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  dotnet-api:
    build: ./your-dotnet-api
    ports:
      - "5000:80"
    environment:
      - AudioEnhancement__ServiceUrl=http://audio-enhancer-api:8000
    depends_on:
      - audio-enhancer-api
    restart: unless-stopped

networks:
  default:
    driver: bridge
```

### 2. Kubernetes Deployment

```yaml
# audio-enhancer-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: audio-enhancer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: audio-enhancer
  template:
    metadata:
      labels:
        app: audio-enhancer
    spec:
      containers:
      - name: audio-enhancer
        image: your-registry/audio-enhancer:latest
        ports:
        - containerPort: 8000
        env:
        - name: WORKER_COUNT
          value: "2"
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
---
apiVersion: v1
kind: Service
metadata:
  name: audio-enhancer-service
spec:
  selector:
    app: audio-enhancer
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

## 🧪 Testing

### 1. Unit Tests

```csharp
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Moq;
using Moq.Protected;
using Xunit;

public class AudioEnhancementServiceTests
{
    [Fact]
    public async Task ProcessAudioAsync_ValidFile_ReturnsSuccess()
    {
        // Arrange
        var mockHandler = new Mock<HttpMessageHandler>();
        var mockLogger = new Mock<ILogger<AudioEnhancementService>>();
        var options = Options.Create(new AudioEnhancementOptions());

        var httpClient = new HttpClient(mockHandler.Object)
        {
            BaseAddress = new Uri("http://localhost:8000")
        };

        var service = new AudioEnhancementService(httpClient, mockLogger.Object, options);

        // Mock HTTP response
        var responseContent = """
        {
            "success": true,
            "message": "Audio processing completed successfully",
            "processing_id": "test-123",
            "download_url": "/download/test.wav"
        }
        """;

        mockHandler.Protected()
            .Setup<Task<HttpResponseMessage>>("SendAsync",
                ItExpr.IsAny<HttpRequestMessage>(),
                ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(new HttpResponseMessage
            {
                StatusCode = HttpStatusCode.OK,
                Content = new StringContent(responseContent)
            });

        // Create a test audio file
        var tempFile = Path.GetTempFileName();
        await File.WriteAllBytesAsync(tempFile, new byte[] { 1, 2, 3, 4 });

        // Act
        var result = await service.ProcessAudioAsync(tempFile);

        // Assert
        Assert.True(result.Success);
        Assert.Equal("test-123", result.ProcessingId);

        // Cleanup
        File.Delete(tempFile);
    }
}
```

### 2. Integration Tests

```csharp
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

public class AudioControllerIntegrationTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;
    private readonly HttpClient _client;

    public AudioControllerIntegrationTests(WebApplicationFactory<Program> factory)
    {
        _factory = factory;
        _client = _factory.CreateClient();
    }

    [Fact]
    public async Task EnhanceAudio_ValidFile_ReturnsOk()
    {
        // Arrange
        var content = new MultipartFormDataContent();
        var fileContent = new ByteArrayContent(GenerateTestAudioData());
        fileContent.Headers.ContentType = MediaTypeHeaderValue.Parse("audio/wav");
        content.Add(fileContent, "audioFile", "test.wav");

        // Act
        var response = await _client.PostAsync("/api/audio/enhance", content);

        // Assert
        response.EnsureSuccessStatusCode();
        var result = await response.Content.ReadAsStringAsync();
        Assert.Contains("success", result);
    }

    private static byte[] GenerateTestAudioData()
    {
        // Generate a simple WAV file header + some audio data
        var header = new byte[44]; // WAV header
        var audioData = new byte[1000]; // Sample audio data
        return header.Concat(audioData).ToArray();
    }
}
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. Service Connection Issues
```csharp
public class AudioServiceHealthChecker
{
    private readonly AudioEnhancementService _audioService;
    private readonly ILogger<AudioServiceHealthChecker> _logger;

    public async Task<HealthCheckResult> CheckHealthAsync()
    {
        try
        {
            var isHealthy = await _audioService.IsServiceHealthyAsync();
            return isHealthy ? HealthCheckResult.Healthy() : HealthCheckResult.Unhealthy();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Health check failed");
            return HealthCheckResult.Unhealthy(ex.Message);
        }
    }
}
```

#### 2. File Size and Format Validation
```csharp
public static class AudioFileValidator
{
    private static readonly string[] SupportedExtensions = { ".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg" };
    
    public static ValidationResult ValidateAudioFile(IFormFile file, long maxSizeBytes)
    {
        if (file == null || file.Length == 0)
            return ValidationResult.Invalid("No file provided");
            
        if (file.Length > maxSizeBytes)
            return ValidationResult.Invalid($"File size exceeds maximum of {maxSizeBytes} bytes");
            
        var extension = Path.GetExtension(file.FileName).ToLowerInvariant();
        if (!SupportedExtensions.Contains(extension))
            return ValidationResult.Invalid($"Unsupported file format: {extension}");
            
        return ValidationResult.Valid();
    }
}

public class ValidationResult
{
    public bool IsValid { get; set; }
    public string ErrorMessage { get; set; }
    
    public static ValidationResult Valid() => new() { IsValid = true };
    public static ValidationResult Invalid(string message) => new() { IsValid = false, ErrorMessage = message };
}
```

### Logging Configuration

```csharp
// appsettings.json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "AudioEnhancement": "Debug",
      "System.Net.Http.HttpClient": "Warning"
    }
  }
}
```

## 📚 Additional Resources

### Useful Extensions and Packages

1. **Polly** - For resilience and retry policies
```xml
<PackageReference Include="Polly.Extensions.Http" Version="3.0.0" />
```

2. **FluentValidation** - For input validation
```xml
<PackageReference Include="FluentValidation.AspNetCore" Version="11.3.0" />
```

3. **Serilog** - For structured logging
```xml
<PackageReference Include="Serilog.AspNetCore" Version="8.0.0" />
```

### Example with Polly Retry Policy

```csharp
builder.Services.AddHttpClient<AudioEnhancementService>()
    .AddPolicyHandler(GetRetryPolicy());

static IAsyncPolicy<HttpResponseMessage> GetRetryPolicy()
{
    return HttpPolicyExtensions
        .HandleTransientHttpError()
        .OrResult(msg => !msg.IsSuccessStatusCode)
        .WaitAndRetryAsync(
            retryCount: 3,
            sleepDurationProvider: retryAttempt => TimeSpan.FromSeconds(Math.Pow(2, retryAttempt)),
            onRetry: (outcome, timespan, retryCount, context) =>
            {
                Console.WriteLine($"Retry {retryCount} after {timespan} seconds");
            });
}
```

## 🎯 Best Practices Summary

1. **Always validate input files** before sending to the service
2. **Implement proper error handling** with retry logic
3. **Use dependency injection** for better testability
4. **Configure appropriate timeouts** for large file processing
5. **Implement health checks** to monitor service availability
6. **Use structured logging** for better debugging
7. **Consider caching** for frequently processed files
8. **Implement rate limiting** to prevent service overload
9. **Use background services** for batch processing
10. **Monitor performance** and adjust concurrency limits

---

## 💼 About Sergie Code

**Software Engineer & YouTube Educator**

Passionate about creating AI tools for musicians and teaching programming through practical projects. This audio enhancement service is part of a series of AI tools designed to empower musicians and audio professionals.

**Connect with Sergie Code:**
- 🎥 **YouTube**: [Sergie Code Channel]
- 💼 **LinkedIn**: [Sergie Code Profile]
- 🐙 **GitHub**: [sergiecode]

---

*Built with ❤️ for the music and developer community*

**Happy Coding! 🚀**