<#
Dexter v3 Setup and Run (Windows)
#>

param([switch]$NoBrowser)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }

function Assert-Admin {
  $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  if (-not $isAdmin) {
    Write-Warn "Re-launching PowerShell as Administrator..."
    Start-Process -FilePath "powershell" -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit 0
  }
}

function Test-Command($n){ $null -ne (Get-Command $n -ErrorAction SilentlyContinue) }
function Ensure-Tool($id,$check,$name){ if(Test-Command $check){Write-Info "$name present";return}; if(Test-Command 'winget'){ winget install --id $id -e --accept-package-agreements --accept-source-agreements | Out-Null } else { Write-Warn "Install $name manually." } }
function Wait-Docker(){ $deadline=(Get-Date).AddMinutes(3); while((Get-Date)-lt $deadline){ try{ docker info | Out-Null; Write-Info "Docker ready"; return } catch { Start-Sleep 3 } }; Write-Warn "Docker not ready, continuing" }

function Setup-Python($root){ Push-Location $root; try { if(-not (Test-Path ".venv")){ python -m venv .venv }; & .\.venv\Scripts\python -m pip install --upgrade pip; if(Test-Path "$root\requirements.txt"){ & .\.venv\Scripts\pip install -r "$root\requirements.txt"} } finally { Pop-Location } }
function Setup-Frontend($dir){ if(-not (Test-Path $dir)){ Write-Warn "No frontend dir"; return }; if(Test-Command 'npm'){ Push-Location $dir; try { npm install } finally { Pop-Location } } else { Write-Warn "npm not found" } }

function Start-Backend($root){ $cmd = "cd `"$root`"; .\\.venv\\Scripts\\python serve_backend.py"; Write-Info "Starting backend (127.0.0.1:8080)..."; Start-Process powershell -ArgumentList "-NoExit","-Command","$cmd" | Out-Null }
function Start-Frontend($root){ $f = Join-Path $root 'frontend'; if(-not (Test-Path $f)){ Write-Warn "No frontend"; return }; $cmd = "cd `"$f`"; npm run dev"; Write-Info "Starting frontend (localhost:3000)..."; Start-Process powershell -ArgumentList "-NoExit","-Command","$cmd" | Out-Null }
function Open-Browser($url){ if($NoBrowser){return}; Start-Process $url | Out-Null }

Assert-Admin
# Determine repo root based on script location
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Write-Info "Root: $root"
Ensure-Tool 'Docker.DockerDesktop' 'docker' 'Docker Desktop'
Ensure-Tool 'OpenJS.NodeJS.LTS' 'node' 'Node.js LTS'
Ensure-Tool 'Python.Python.3.11' 'python' 'Python 3.11'
Wait-Docker
Setup-Python $root
Setup-Frontend (Join-Path $root 'frontend')
Start-Backend $root
Start-Frontend $root
Open-Browser 'http://localhost:3000'
