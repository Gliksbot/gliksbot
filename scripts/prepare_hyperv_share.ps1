# Ensures the Hyper-V host share is ready for Dexter sandbox runs.
# - Creates the host shared directory (from config.json)
# - Copies runner.py into the share root
# - Creates inbox/ and outbox/ subfolders

param(
  [string]$ConfigPath = "./config.json"
)

Write-Host "[prepare-hyperv] Reading config: $ConfigPath"
if (!(Test-Path $ConfigPath)) { throw "Config file not found: $ConfigPath" }

$cfg = Get-Content -Raw -Path $ConfigPath | ConvertFrom-Json
$hv = $cfg.runtime.sandbox.hyperv
if (-not $hv) { throw "No runtime.sandbox.hyperv section in config" }

$hostDir = $hv.host_shared_dir
if (-not $hostDir) { throw "hyperv.host_shared_dir not set in config" }

Write-Host "[prepare-hyperv] Host shared dir: $hostDir"
New-Item -ItemType Directory -Force -Path $hostDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $hostDir 'inbox') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $hostDir 'outbox') | Out-Null

$runnerSrc = Join-Path (Get-Location) 'runner.py'
if (!(Test-Path $runnerSrc)) { throw "runner.py not found in repo root" }
$runnerDst = Join-Path $hostDir 'runner.py'
Copy-Item -Force -Path $runnerSrc -Destination $runnerDst
Write-Host "[prepare-hyperv] Copied runner.py -> $runnerDst"

Write-Host "[prepare-hyperv] Done. Ensure VM sees this dir as $($hv.vm_shared_dir)."

