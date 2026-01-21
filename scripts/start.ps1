# Insurabridge Start Script for Windows

$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootPath = Resolve-Path "$scriptPath\.."

Write-Host "Starting Insurabridge..." -ForegroundColor Cyan

# Check Ollama
try {
    $ollamaStatus = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method Get -ErrorAction SilentlyContinue
    Write-Host "✅ Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Ollama is not running. Starting it..." -ForegroundColor Yellow
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Minimized
    Start-Sleep -Seconds 3
}

# Start Backend
Write-Host "🚀 Launching Backend Server..." -ForegroundColor Cyan
$backendCmd = "cd '$rootPath\backend'; if (Test-Path 'venv\Scripts\Activate.ps1') { . .\venv\Scripts\Activate.ps1 } else { Write-Error 'Venv not found!' }; python -m uvicorn app.main:app --reload --port 8001"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$backendCmd"

# Start Epic Bridge
Write-Host "🚀 Launching Epic FHIR Bridge..." -ForegroundColor Cyan
$bridgeCmd = "cd '$rootPath\epic-fhir-bridge'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$bridgeCmd"

# Start Frontend
Write-Host "🚀 Launching Frontend Server..." -ForegroundColor Cyan
$frontendCmd = "cd '$rootPath\frontend'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$frontendCmd"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Insurabridge is starting!" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Services launching in new windows:"
Write-Host "  1. Backend (Port 8001)"
Write-Host "  2. Epic Bridge (Port 3000)"
Write-Host "  3. Frontend (Port 3001)"
Write-Host ""
Write-Host "  Once ready, open: http://localhost:3001"
Write-Host ""
