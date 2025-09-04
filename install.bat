@echo off
REM Dexter v3 Installer Script for Windows
REM This script sets up the complete Dexter v3 environment

setlocal EnableDelayedExpansion

echo ============================================
echo   🤖 Dexter v3 - Autonomous AI System
echo ============================================
echo Installing dependencies and setting up environment...
echo.

REM Get current directory for cross-platform compatibility
set "INSTALL_DIR=%~dp0"
echo [INFO] Installation directory: %INSTALL_DIR%

REM Detect Windows version for better compatibility messaging
ver | findstr /i "Windows" >nul
if errorlevel 1 (
    echo [WARNING] This script is designed for Windows systems
    echo [INFO] For Linux/macOS, please use install.sh instead
) else (
    echo [INFO] Windows system detected - proceeding with Windows-specific setup
)

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

REM Check for Hyper-V capabilities (Windows only - gracefully fails on other platforms)
echo [INFO] Checking for Hyper-V support (Windows only)...
powershell -Command "Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -ErrorAction SilentlyContinue" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Hyper-V not available - will use Docker as primary sandbox
    echo [INFO] This is normal on non-Windows systems or Windows Home edition
    echo [INFO] To enable Hyper-V on Windows Pro/Enterprise, run as Administrator:
    echo [INFO]   dism /online /enable-feature /featurename:Microsoft-Hyper-V /all /norestart
    echo [INFO]   dism /online /enable-feature /featurename:HypervisorPlatform /all /norestart
) else (
    echo [SUCCESS] Hyper-V capabilities detected
    echo [INFO] Installing Hyper-V Management Tools...
    powershell -Command "Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-Tools-All -All -NoRestart" >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Failed to install Hyper-V Manager - install manually if needed
        echo [INFO] Docker will be used as fallback sandbox
    ) else (
        echo [SUCCESS] Hyper-V Manager tools installed
    )
)

REM Check Docker installation for sandbox fallback
echo [INFO] Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Docker not found - attempting to install Docker Desktop...
    echo [INFO] Downloading Docker Desktop installer...
    
    REM Try to download Docker Desktop installer with better error handling
    powershell -Command "try { $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://desktop.docker.com/win/main/amd64/Docker%%20Desktop%%20Installer.exe' -OutFile 'DockerDesktopInstaller.exe' -UseBasicParsing -TimeoutSec 60; Write-Host 'Download completed'; exit 0 } catch { Write-Host \"Download failed: $_\"; exit 1 }" 2>nul
    
    if errorlevel 1 (
        echo [WARNING] Could not download Docker Desktop automatically
        echo [WARNING] This may be due to network restrictions or firewall settings
        echo [INFO] Please install Docker Desktop manually:
        echo [INFO]   1. Visit https://docker.com/products/docker-desktop
        echo [INFO]   2. Download Docker Desktop for Windows
        echo [INFO]   3. Run the installer and restart your computer
        echo [INFO] 📋 SANDBOX FALLBACK: Hyper-V → Docker → Limited Mode
    ) else (
        echo [SUCCESS] Docker Desktop installer downloaded
        echo [INFO] Starting Docker Desktop installation...
        echo [WARNING] ⚠️  Installation may require administrator privileges
        echo [WARNING] ⚠️  A system restart will be required after installation
        
        REM Install Docker Desktop with user interaction for admin privileges if needed
        start /wait DockerDesktopInstaller.exe install --quiet --accept-license
        
        if errorlevel 1 (
            echo [WARNING] Automated installation may have failed
            echo [INFO] Please run the installer manually: DockerDesktopInstaller.exe
            echo [INFO] Or download from: https://docker.com/products/docker-desktop
        ) else (
            echo [SUCCESS] Docker Desktop installation initiated
            echo [INFO] Please restart your computer to complete Docker setup
            echo [INFO] After restart, Docker will be available for sandbox execution
        )
        
        REM Clean up installer (keep it if installation failed for manual retry)
        if exist DockerDesktopInstaller.exe (
            echo [INFO] Installer kept for potential manual installation
        )
    )
) else (
    echo [SUCCESS] Docker found - testing sandbox capabilities...
    echo [INFO] Building Docker sandbox image...
    docker build -f Dockerfile.sandbox -t dexter-sandbox . >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Failed to build Docker sandbox image
        echo [INFO] You may need to restart Docker or check Docker daemon status
    ) else (
        echo [SUCCESS] Docker sandbox ready for secure code execution
    )
)

REM Create necessary directories
if not exist logs mkdir logs
if not exist vm_shared mkdir vm_shared
if not exist collaboration mkdir collaboration
echo [INFO] Created required directories

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
echo 📋 CROSS-PLATFORM SANDBOX CONFIGURATION:
echo • Docker: Automatically installed or detected for sandbox execution
echo • Hyper-V: Available on Windows Pro/Enterprise (gracefully fails on other platforms)
echo • Fallback: Limited mode if neither Docker nor Hyper-V is available
echo • All paths are now relative and cross-platform compatible
echo.
echo Next steps:
echo 1. Edit .env file with your API keys (optional)
echo 2. Run 'launch.bat' to start the system
echo 3. Open http://localhost:3000 for the web interface
echo 4. Backend API will be available at http://localhost:8000
echo.
echo 💡 For testing without dependencies: python demo_system.py
echo 🔄 If Docker was installed, restart may be required for full functionality
echo.
pause