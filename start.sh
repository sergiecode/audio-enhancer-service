#!/bin/bash

# Audio Enhancement Service Startup Script
# Created by Sergie Code

echo "🎵 Audio Enhancement Service - Startup Script"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads outputs models logs

# Run tests
echo "🧪 Running tests..."
python test_service.py

# Start the service
echo "🚀 Starting Audio Enhancement Service..."
echo "📡 Service will be available at: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the service"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
