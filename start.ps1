#!/usr/bin/env pwsh
# GliksBot Startup Script
# This script starts both the backend and frontend servers

Write-Host "Starting GliksBot System..." -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green

# Check if Python is available
try {
    python --version | Out-Null
    Write-Host "✓ Python found" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Check if Node.js is available
try {
    node --version | Out-Null
    Write-Host "✓ Node.js found" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found. Please install Node.js 16+" -ForegroundColor Red
    exit 1
}

# Check if config.json exists
if (!(Test-Path "config.json")) {
    Write-Host "✗ config.json not found in current directory" -ForegroundColor Red
    Write-Host "Please run this script from the gliksbot root directory" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Configuration file found" -ForegroundColor Green

# Install backend dependencies if needed
if (!(Test-Path "backend\requirements.txt")) {
    Write-Host "✗ Backend requirements.txt not found" -ForegroundColor Red
    exit 1
}

Write-Host "`nInstalling backend dependencies..." -ForegroundColor Yellow
Set-Location backend
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to install backend dependencies" -ForegroundColor Red
    exit 1
}
Set-Location ..
Write-Host "✓ Backend dependencies installed" -ForegroundColor Green

# Install frontend dependencies if needed
if (!(Test-Path "frontend\package.json")) {
    Write-Host "✗ Frontend package.json not found" -ForegroundColor Red
    exit 1
}

Write-Host "`nInstalling frontend dependencies..." -ForegroundColor Yellow
Set-Location frontend
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to install frontend dependencies" -ForegroundColor Red
    exit 1
}
Set-Location ..
Write-Host "✓ Frontend dependencies installed" -ForegroundColor Green

# Create collaboration directories
Write-Host "`nCreating collaboration directories..." -ForegroundColor Yellow
$collaborationDir = "collaboration"
$models = @("dexter", "analyst", "engineer", "researcher", "creative", "specialist1", "specialist2", "validator")

foreach ($model in $models) {
    $modelDir = Join-Path $collaborationDir $model
    if (!(Test-Path $modelDir)) {
        New-Item -ItemType Directory -Path $modelDir -Force | Out-Null
        Write-Host "✓ Created $modelDir" -ForegroundColor Green
    }
}

Write-Host "`n==============================" -ForegroundColor Green
Write-Host "Starting Services..." -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green

# Start backend in background
Write-Host "Starting backend server (http://localhost:8080)..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList "-Command", "cd '$PWD\backend'; python main.py" -WindowStyle Hidden

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start frontend
Write-Host "Starting frontend server (http://localhost:3000)..." -ForegroundColor Yellow
Write-Host "`n✓ GliksBot is starting up!" -ForegroundColor Green
Write-Host "Backend: http://localhost:8080" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Docs: http://localhost:8080/docs" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C to stop the frontend server" -ForegroundColor Yellow
Write-Host "Backend will continue running in the background" -ForegroundColor Yellow

Set-Location frontend
npm run dev
