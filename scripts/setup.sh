#!/bin/bash
# Insurabridge Setup Script
# Initializes the development environment

set -e

echo "================================================"
echo "  Insurabridge Setup"
echo "  HIPAA-Compliant AI Health Insurance Platform"
echo "================================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "   Please install Python 3.11+ from https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✅ Python $PYTHON_VERSION found"

# Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    echo "   Please install Node.js 18+ from https://nodejs.org"
    exit 1
fi

NODE_VERSION=$(node -v)
echo "✅ Node.js $NODE_VERSION found"

# Ollama
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama not found. Install from https://ollama.ai"
    echo "   You'll need to run 'ollama pull gemma:7b' before using Insurabridge"
else
    echo "✅ Ollama found"
    
    # Check if Gemma is pulled
    if ollama list | grep -q "gemma"; then
        echo "✅ Gemma model available"
    else
        echo "📥 Pulling Gemma model (this may take a few minutes)..."
        ollama pull gemma:7b
    fi
fi

echo ""
echo "Setting up backend..."

cd "$(dirname "$0")/../backend"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "✅ Backend setup complete"

echo ""
echo "Setting up frontend..."

cd ../frontend

# Install Node dependencies
echo "Installing Node.js dependencies..."
npm install --silent

echo "✅ Frontend setup complete"

echo ""
echo "================================================"
echo "  Setup Complete!"
echo "================================================"
echo ""
echo "To start the application:"
echo ""
echo "  1. Start Ollama (if not running):"
echo "     ollama serve"
echo ""
echo "  2. Start the backend:"
echo "     cd backend && source venv/bin/activate && python -m uvicorn app.main:app --reload"
echo ""
echo "  3. Start the frontend (in another terminal):"
echo "     cd frontend && npm run dev"
echo ""
echo "  4. Open http://localhost:3000"
echo ""
echo "For more information, see README.md"
echo ""

