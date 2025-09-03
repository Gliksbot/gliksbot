@echo off
REM Dexter v3 Launch Script for Windows
REM This script starts both frontend and backend services

title Dexter v3 - Autonomous AI System

echo ============================================
echo   🚀 Launching Dexter v3 System
echo ============================================

REM Check if dependencies are installed
if not exist frontend\node_modules (
    echo [WARNING] Frontend dependencies not found. Installing...
    cd frontend
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install frontend dependencies
        pause
        exit /b 1
    )
    cd ..
)

if not exist frontend\dist (
    echo [WARNING] Frontend not built. Building...
    cd frontend
    call npm run build
    if errorlevel 1 (
        echo [ERROR] Failed to build frontend
        pause
        exit /b 1
    )
    cd ..
)

REM Create logs directory if it doesn't exist
if not exist logs mkdir logs

echo [INFO] Starting backend server...
start "Dexter Backend" cmd /k "cd backend && python main.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

echo [INFO] Starting frontend development server...
start "Dexter Frontend" cmd /k "cd frontend && npm run dev"

REM Wait a moment for frontend to start
timeout /t 3 /nobreak >nul

echo.
echo [SUCCESS] Dexter v3 is now running!
echo.
echo 🌐 Frontend: http://localhost:3000
echo 🔧 Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo 📄 Two terminal windows have opened for frontend and backend
echo 🛑 Close the terminal windows to stop the services
echo 💡 For production deployment, use the production_setup.ps1 script
echo.

REM Show quick demo option
echo ========================================== 
echo Quick Test Options:
echo ==========================================
echo 1. Open web interface: http://localhost:3000
echo 2. Test API: http://localhost:8000/docs
echo 3. Run demo: python demo_system.py
echo.

echo Press any key to open the web interface...
pause >nul

REM Try to open the web interface
start http://localhost:3000

echo.
echo Dexter v3 is running in the background.
echo Check the opened terminal windows for logs.
echo Close this window when you're done.
pause