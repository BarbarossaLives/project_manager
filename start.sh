#!/bin/bash
# Quick start script for Project Manager

echo "🚀 Starting AI-Powered Project Manager..."
echo "📍 Server will be available at: http://localhost:8080"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/lib/python*/site-packages/fastapi" ]; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the application
echo "🚀 Starting Project Manager..."
python start_project_manager.py
