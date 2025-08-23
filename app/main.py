"""
Audio Enhancement Microservice
Created by Sergie Code

A FastAPI-based microservice for audio enhancement including:
- Noise reduction
- Vocal/instrument separation  
- Audio quality improvement

This service provides a REST API for .NET backends and other clients
to process audio files using state-of-the-art AI models.
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Dict, Any
import tempfile

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .config import settings
from .inference import process_audio

# Initialize FastAPI app
app = FastAPI(
    title=settings.SERVICE_NAME,
    description=settings.SERVICE_DESCRIPTION,
    version=settings.SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for cross-origin requests (useful for .NET integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories for file storage
UPLOAD_DIR = settings.UPLOAD_DIR
OUTPUT_DIR = settings.OUTPUT_DIR
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Supported audio formats
SUPPORTED_FORMATS = set(settings.SUPPORTED_FORMATS)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": settings.SERVICE_NAME,
        "status": "active",
        "version": settings.SERVICE_VERSION,
        "author": "Sergie Code",
        "description": "AI-powered audio enhancement for musicians"
    }


@app.get("/health")
async def health_check():
    """Detailed health check for monitoring systems"""
    return {
        "status": "healthy",
        "service": "audio-enhancer",
        "timestamp": "2025-08-23T00:00:00Z"
    }


@app.post("/process")
async def process_audio_endpoint(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Process an audio file for enhancement
    
    Args:
        file: Uploaded audio file (WAV, MP3, FLAC, M4A, AAC, OGG)
    
    Returns:
        JSON response with processed file information
    
    Example:
        curl -X POST "http://localhost:8000/process" \
             -F "file=@input_audio.wav" \
             -H "accept: application/json"
    """
    
    # Validate file format
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format. Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )
    
    # Generate unique filename to avoid conflicts
    unique_id = str(uuid.uuid4())
    input_filename = f"{unique_id}_input{file_extension}"
    output_filename = f"{unique_id}_enhanced{file_extension}"
    
    input_path = UPLOAD_DIR / input_filename
    output_path = OUTPUT_DIR / output_filename
    
    try:
        # Save uploaded file
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process audio file
        processing_result = await process_audio(str(input_path), str(output_path))
        
        # Prepare response
        response_data = {
            "success": True,
            "message": "Audio processing completed successfully",
            "input_file": file.filename,
            "output_file": output_filename,
            "output_path": str(output_path),
            "processing_id": unique_id,
            "processing_details": processing_result,
            "download_url": f"/download/{output_filename}"
        }
        
        return JSONResponse(content=response_data, status_code=200)
    
    except Exception as e:
        # Clean up files on error
        if input_path.exists():
            input_path.unlink()
        if output_path.exists():
            output_path.unlink()
            
        raise HTTPException(
            status_code=500, 
            detail=f"Audio processing failed: {str(e)}"
        )


@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download processed audio file
    
    Args:
        filename: Name of the processed file
    
    Returns:
        File response for download
    """
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="audio/mpeg"
    )


@app.get("/formats")
async def get_supported_formats():
    """Get list of supported audio formats"""
    return {
        "supported_formats": list(SUPPORTED_FORMATS),
        "description": "Audio formats supported for processing"
    }


if __name__ == "__main__":
    # For development purposes
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
