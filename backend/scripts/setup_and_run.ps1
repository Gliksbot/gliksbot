<#
Setup and Run Script for Dexter v3 (Windows / PowerShell)

This script:
- Ensures required tools are installed (Docker Desktop, Node.js LTS, Python 3.11)
- Sets up a Python virtual environment and installs backend deps
- Installs frontend deps
- Starts backend (FastAPI) and frontend (Vite) in separate windows
- Opens the browser to the UI

Requirements:
- Windows 10/11
- PowerShell 5+ or PowerShell 7
- winget available (recommended). If missing, install winget or install tools manually.
#>

param(
  [switch]$NoBrowser
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[ERROR] $msg" -ForegroundColor Red }

function Assert-Admin {
  $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  if (-not $isAdmin) {
    Write-Warn "This script requires Administrator privileges to install Docker Desktop and tools."
    Write-Info "Re-launching PowerShell as Administrator..."
    Start-Process -FilePath "powershell" -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit 0
  }
}

function Test-Command($name) {
  $null -ne (Get-Command $name -ErrorAction SilentlyContinue)
}

function Ensure-Tool-Winget($id, $checkCmd, $displayName) {
  if (Test-Command $checkCmd) {
    Write-Info "$displayName already installed."
    return
  }
  if (-not (Test-Command 'winget')) {
    Write-Warn "winget not found. Please install $displayName manually, then re-run."
    return
  }
  Write-Info "Installing $displayName via winget..."
  winget install --id $id -e --accept-package-agreements --accept-source-agreements | Out-Null
}

function Wait-For-Docker {
  Write-Info "Ensuring Docker Desktop is running..."
  if (-not (Get-Process -Name 'Docker Desktop' -ErrorAction SilentlyContinue)) {
    $dockerPath = "$Env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerPath) {
      Start-Process -FilePath $dockerPath | Out-Null
    }
  }
  $deadline = (Get-Date).AddMinutes(3)
  while ((Get-Date) -lt $deadline) {
    try {
      docker info | Out-Null
      Write-Info "Docker is ready."
      return
    } catch {
      Start-Sleep -Seconds 3
    }
  }
  Write-Warn "Docker did not become ready within timeout. Continuing anyway."
}

function Ensure-Python-Venv-And-Install($root) {
  Write-Info "Setting up Python virtual environment (.venv) and installing requirements..."
  Push-Location $root
  try {
    if (-not (Test-Path ".venv")) {
      Write-Info "Creating virtual environment..."
      python -m venv .venv
    }
    & .\.venv\Scripts\python -m pip install --upgrade pip
    # Install root requirements if present
    if (Test-Path "$root\requirements.txt") {
      Write-Info "Installing root requirements.txt..."
      & .\.venv\Scripts\pip install -r "$root\requirements.txt"
    }
    # Install backend requirements
    if (Test-Path "$root\backend\requirements.txt") {
      Write-Info "Installing backend/requirements.txt..."
      & .\.venv\Scripts\pip install -r "$root\backend\requirements.txt"
    }
  } finally {
    Pop-Location
  }
}

function Ensure-Node-Install($frontendDir) {
  Write-Info "Installing frontend dependencies..."
  Push-Location $frontendDir
  try {
    if (-not (Test-Command 'npm')) {
      Write-Warn "npm not found; Node.js installation may have failed."
    } else {
      npm install
    }
  } finally {
    Pop-Location
  }
}

function Start-Backend($root) {
  $cmd = "cd `"$root`"; .\.venv\Scripts\python serve_backend.py"
  Write-Info "Starting backend (uvicorn on 127.0.0.1:8080) in a new window..."
  Start-Process powershell -ArgumentList "-NoExit","-Command","$cmd" | Out-Null
}

function Start-Frontend($root) {
  $frontendDir = Join-Path $root 'frontend'
  if (-not (Test-Path $frontendDir)) {
    Write-Warn "Frontend directory not found at $frontendDir. Skipping frontend start."
    return
  }
  $cmd = "cd `"$frontendDir`"; npm run dev"
  Write-Info "Starting frontend (npm run dev) in a new window..."
  Start-Process powershell -ArgumentList "-NoExit","-Command","$cmd" | Out-Null
}

function Open-Browser($url) {
  if ($NoBrowser) { return }
  Write-Info "Opening browser at $url"
  Start-Process $url | Out-Null
}

# --- Main ---
Assert-Admin

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Write-Info "Repo root: $repoRoot"

# Install tools
Ensure-Tool-Winget -id 'Docker.DockerDesktop' -checkCmd 'docker' -displayName 'Docker Desktop'
Ensure-Tool-Winget -id 'OpenJS.NodeJS.LTS'   -checkCmd 'node'   -displayName 'Node.js LTS'
Ensure-Tool-Winget -id 'Python.Python.3.11'  -checkCmd 'python' -displayName 'Python 3.11'

Wait-For-Docker

# Backend setup
Ensure-Python-Venv-And-Install -root $repoRoot

# Frontend deps
$frontendDir = Join-Path $repoRoot 'frontend'
if (Test-Path $frontendDir) {
  Ensure-Node-Install -frontendDir $frontendDir
}

# Start services
Start-Backend -root $repoRoot
Start-Frontend -root $repoRoot

# Open UI
# Vite default is 5173; change if your frontend uses another port.
Open-Browser -url 'http://localhost:3000'

Write-Info "All done. If ports differ, adjust the script accordingly."
