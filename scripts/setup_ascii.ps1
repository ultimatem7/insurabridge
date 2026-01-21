# Insurabridge Setup Script for Windows
# Initializes the development environment

$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Insurabridge Setup" -ForegroundColor Cyan
Write-Host "  HIPAA-Compliant AI Health Insurance Platform" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] $pythonVersion found" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python 3 is required but not installed." -ForegroundColor Red
    Write-Host "   Please install Python from https://python.org" -ForegroundColor Red
    exit 1
}

# Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "[OK] Node.js $nodeVersion found" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Node.js is required but not installed." -ForegroundColor Red
    Write-Host "   Please install Node.js 18+ from https://nodejs.org" -ForegroundColor Red
    exit 1
}

# Ollama
try {
    $ollamaVersion = ollama --version 2>&1
    Write-Host "[OK] Ollama found" -ForegroundColor Green
    
    # Check if Gemma is available
    $models = ollama list 2>&1
    if ($models -match "gemma") {
        Write-Host "[OK] Gemma model available" -ForegroundColor Green
    } else {
        Write-Host "[INFO] Pulling Gemma model (this may take a few minutes)..." -ForegroundColor Yellow
        ollama pull gemma:7b
    }
} catch {
    Write-Host "[WARN] Ollama not found. Install from https://ollama.ai" -ForegroundColor Yellow
    Write-Host "   You will need to run 'ollama pull gemma:7b' before using Insurabridge" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setting up backend..." -ForegroundColor Yellow

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$scriptPath\..\backend"

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv venv
}

# Activate venv
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    & .\venv\Scripts\Activate.ps1
} else {
    Write-Host "[ERROR] venv activation script not found." -ForegroundColor Red
    Write-Host "   Attempting to recreate venv..."
    Remove-Item -Recurse -Force venv
    python -m venv venv
    & .\venv\Scripts\Activate.ps1
}

# Install dependencies
Write-Host "Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

Write-Host "[OK] Backend setup complete" -ForegroundColor Green

Write-Host ""
Write-Host "Setting up frontend..." -ForegroundColor Yellow

Set-Location "..\frontend"

# Install Node dependencies
Write-Host "Installing Node.js dependencies..."
npm install --silent

Write-Host "[OK] Frontend setup complete" -ForegroundColor Green

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the application:" -ForegroundColor White
Write-Host ""
Write-Host "  1. Start Ollama (if not running):" -ForegroundColor White
Write-Host "     ollama serve" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Start the backend:" -ForegroundColor White
Write-Host "     cd backend; .\venv\Scripts\Activate.ps1; python -m uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Start the frontend (in another terminal):" -ForegroundColor White
Write-Host "     cd frontend; npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Open http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "For more information, see README.md" -ForegroundColor White
Write-Host ""
