@echo off
title 🚀 Launching GliksBot
echo ============================================
echo     GliksBot Autonomous AI System
echo ============================================

REM Step 1: Start Backend (FastAPI on port 8080)
echo [1/3] Starting Backend...
start cmd /k "cd gliksbot\backend && pip install -r requirements.txt && uvicorn main:app --reload --host 0.0.0.0 --port 8080"

REM Step 2: Start Frontend (React)
echo [2/3] Starting Frontend...
start cmd /k "cd gliksbot\frontend && npm install && npm run dev"

REM Step 3: Reminder for VM
echo [3/3] Make sure Hyper-V VM 'DexterVM' is running with Python installed.

echo.
echo ✅ Backend running at: http://localhost:8080
echo ✅ Frontend running at: http://localhost:5173
echo ============================================
echo GliksBot is launching... close this window to exit.
pause
