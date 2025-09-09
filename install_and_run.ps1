<#
Install and run Dexter backend (Windows PowerShell).

This script performs the following tasks:
1. Ensures Python 3.11+ is installed.
2. Creates a Python virtual environment in the project root if none exists.
3. Installs all backend dependencies from ``requirements.txt``.
4. Starts the FastAPI backend using uvicorn with the fully qualified module name
   to avoid import errors (``backend.main:app``).

You can save this file to the root of your project and run it from a
PowerShell prompt.  Run with ``-NoBrowser`` to skip launching a browser.
#>

param(
    [switch]$NoBrowser
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[ERROR] $msg" -ForegroundColor Red }

function Ensure-Python {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Err "Python is not installed. Please install Python 3.11 or later and rerun this script."
        exit 1
    }
}

function Setup-Venv-And-Install {
    Write-Info "Setting up Python virtual environment and installing dependencies..."
    # Create venv if not exists
    if (-not (Test-Path ".venv")) {
        Write-Info "Creating virtual environment (.venv)..."
        python -m venv .venv
    }
    $venvPython = Join-Path ".venv" "Scripts\python.exe"
    $venvPip    = Join-Path ".venv" "Scripts\pip.exe"
    # Upgrade pip
    & $venvPython -m pip install --upgrade pip
    # Install project requirements
    $reqFile = "requirements.txt"
    if (Test-Path $reqFile) {
        Write-Info "Installing backend dependencies from $reqFile..."
        & $venvPip install -r $reqFile
    } else {
        Write-Warn "Could not find requirements.txt; skipping installation."
    }
}

# Ensure the backend directory exists.  If there is a ZIP archive but no
# extracted folder, attempt to unpack it before installing dependencies or
# starting the server.  This allows you to simply drop ``backend.zip`` (or
# ``updated_backend.zip``) alongside this script and run it without a manual
# extraction step.
function Ensure-Backend-Unpacked {
    if (-not (Test-Path 'backend')) {
        # Look for a backend archive
        $zipCandidates = @('updated_backend.zip','backend.zip') | Where-Object { Test-Path $_ }
        if ($zipCandidates.Count -gt 0) {
            $zip = $zipCandidates[0]
            Write-Info "Extracting $zip..."
            try {
                Expand-Archive -Path $zip -DestinationPath '.' -Force
            } catch {
                # Use parentheses to correctly interpolate variables inside the message.  Without
                # parentheses, PowerShell treats ``:`` as a member access operator and throws a
                # parser error.  ``$_`` contains the current error record in a catch block.
                Write-Err ("Failed to extract $zip: $($_)")
                exit 1
            }
        } else {
            Write-Err "Could not find a 'backend' directory or a backend ZIP archive."
            exit 1
        }
    }
}

function Start-Backend {
    Write-Info "Starting Dexter backend (uvicorn on http://127.0.0.1:8080)..."
    $venvPython = Join-Path ".venv" "Scripts\python.exe"
    $cmdArgs = @('-m', 'uvicorn', 'backend.main:app', '--host', '0.0.0.0', '--port', '8080')
    & $venvPython @cmdArgs
}

function Open-Browser {
    param([string]$url)
    if ($NoBrowser) { return }
    Write-Info "Opening browser at $url..."
    Start-Process $url | Out-Null
}

# Main script execution
Write-Info "Project root: $(Get-Location)"
Ensure-Python
Setup-Venv-And-Install
Open-Browser -url 'http://127.0.0.1:8080/docs'
Start-Backend