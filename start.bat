@echo off
REM Audio Enhancement Service Startup Script for Windows
REM Created by Sergie Code

echo 🎵 Audio Enhancement Service - Startup Script
echo ==============================================

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Create necessary directories
echo 📁 Creating directories...
if not exist "uploads" mkdir uploads
if not exist "outputs" mkdir outputs
if not exist "models" mkdir models
if not exist "logs" mkdir logs

REM Run tests
echo 🧪 Running tests...
python test_service.py

REM Start the service
echo 🚀 Starting Audio Enhancement Service...
echo 📡 Service will be available at: http://localhost:8000
echo 📚 API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the service
echo.

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
