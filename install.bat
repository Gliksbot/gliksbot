@echo off
REM Dexter v3 Installer Script for Windows
REM This script sets up the complete Dexter v3 environment

setlocal EnableDelayedExpansion

echo ============================================
echo   🤖 Dexter v3 - Autonomous AI System
echo ============================================
echo Installing dependencies and setting up environment...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org before running this installer
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [INFO] Python version: %PYTHON_VERSION%

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Node.js is not installed
    echo [INFO] Please install Node.js from https://nodejs.org/
    echo [INFO] You can continue installation and install Node.js later
    set NODE_MISSING=1
) else (
    for /f %%i in ('node --version') do set NODE_VERSION=%%i
    echo [INFO] Node.js version: !NODE_VERSION!
)

REM Install Python dependencies
echo [INFO] Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)
echo [SUCCESS] Python dependencies installed

if not defined NODE_MISSING (
    REM Install frontend dependencies
    echo [INFO] Installing frontend dependencies...
    cd frontend
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install frontend dependencies
        cd ..
        pause
        exit /b 1
    )
    echo [SUCCESS] Frontend dependencies installed

    REM Build frontend
    echo [INFO] Building frontend for production...
    call npm run build
    if errorlevel 1 (
        echo [ERROR] Failed to build frontend
        cd ..
        pause
        exit /b 1
    )
    echo [SUCCESS] Frontend built successfully
    cd ..
) else (
    echo [WARNING] Skipping frontend setup - Node.js not installed
)

REM Check and setup sandbox providers (Hyper-V and Docker)
echo [INFO] Setting up sandbox providers...

REM Check for Hyper-V capabilities
powershell -Command "Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -ErrorAction SilentlyContinue" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Hyper-V not detected - setting up alternatives...
    echo [WARNING] ⚠️  IMPORTANT: If Hyper-V fails, Docker will be used as sandbox
    echo [INFO] To enable Hyper-V on Windows Pro/Enterprise, run as Administrator:
    echo [INFO]   dism /online /enable-feature /featurename:Microsoft-Hyper-V /all /norestart
    echo [INFO]   dism /online /enable-feature /featurename:HypervisorPlatform /all /norestart
) else (
    echo [SUCCESS] Hyper-V capabilities detected
    echo [INFO] Installing Hyper-V Management Tools...
    powershell -Command "Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-Tools-All -All -NoRestart" >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Failed to install Hyper-V Manager - install manually if needed
    ) else (
        echo [SUCCESS] Hyper-V Manager tools installed
    )
)

REM Check Docker installation for sandbox fallback
docker --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Docker not found - sandbox mode will be limited
    echo [WARNING] Install Docker Desktop for full sandbox capabilities
    echo [INFO] 📋 SANDBOX FALLBACK CHAIN: Hyper-V → Docker → Limited Mode
) else (
    echo [INFO] Docker found - sandbox mode available
    echo [INFO] Building Docker sandbox image...
    docker build -f Dockerfile.sandbox -t dexter-sandbox .
    if errorlevel 1 (
        echo [WARNING] Failed to build Docker sandbox
    ) else (
        echo [SUCCESS] Docker sandbox ready
    )
)

REM Create logs directory
if not exist logs mkdir logs
echo [INFO] Created logs directory

REM Set up configuration
if not exist .env (
    if exist .env.template (
        copy .env.template .env >nul
        echo [INFO] Created .env file from template
        echo [WARNING] Please edit .env file with your API keys and configuration
    )
)

echo.
echo [SUCCESS] 🎉 Installation completed successfully!
echo.
echo 📋 SANDBOX CONFIGURATION:
echo • If Hyper-V fails or is unavailable, Docker will be used as fallback
echo • For full sandbox capabilities, ensure either Hyper-V or Docker is working
echo • System will run in limited mode if neither is available
echo.
echo Next steps:
echo 1. Edit .env file with your API keys (optional)
echo 2. Run 'launch.bat' to start the system
echo 3. Open http://localhost:3000 for the web interface
echo 4. Backend API will be available at http://localhost:8000
echo.
echo For testing without dependencies, run: python demo_system.py
echo.
pause