# Dexter v3 Deployment Script for Windows Server 2022
# Run as Administrator

param(
    [string]$Domain = "www.gliksbot.com",
    [string]$SiteName = "Dexter",
    [string]$AppPoolName = "DexterAppPool",
    [string]$InstallPath = "M:\gliksbot",
    [switch]$SSL = $true
)

Write-Host "=== Dexter v3 Deployment Script ===" -ForegroundColor Cyan
Write-Host "Domain: $Domain" -ForegroundColor Green
Write-Host "Install Path: $InstallPath" -ForegroundColor Green

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "This script must be run as Administrator!"
    exit 1
}

# Install IIS and required features
Write-Host "Installing IIS and features..." -ForegroundColor Yellow
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole, IIS-WebServer, IIS-CommonHttpFeatures, IIS-HttpErrors, IIS-HttpLogging, IIS-RequestMonitor, IIS-HttpTracing, IIS-Security, IIS-RequestFiltering, IIS-Performance, IIS-WebServerManagementTools, IIS-ManagementConsole, IIS-IIS6ManagementCompatibility, IIS-Metabase, IIS-HttpCompressionStatic, IIS-HttpCompressionDynamic, IIS-StaticContent, IIS-DefaultDocument, IIS-DirectoryBrowsing, IIS-ASPNET45 -All

# Install URL Rewrite module
Write-Host "Installing URL Rewrite module..." -ForegroundColor Yellow
$rewriteUrl = "https://download.microsoft.com/download/1/2/8/128E2E22-C1B9-44A4-BE2A-5859ED1D4592/rewrite_amd64_en-US.msi"
$rewritePath = "$env:TEMP\urlrewrite.msi"
if (-not (Get-Module -ListAvailable -Name WebAdministration)) {
    Invoke-WebRequest -Uri $rewriteUrl -OutFile $rewritePath
    Start-Process msiexec.exe -Wait -ArgumentList "/i $rewritePath /quiet"
}

# Install Python if not present
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Python..." -ForegroundColor Yellow
    $pythonUrl = "https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe"
    $pythonPath = "$env:TEMP\python-installer.exe"
    Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonPath
    Start-Process $pythonPath -Wait -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1"
}

# Install Node.js if not present
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Node.js..." -ForegroundColor Yellow
    $nodeUrl = "https://nodejs.org/dist/v18.17.0/node-v18.17.0-x64.msi"
    $nodePath = "$env:TEMP\node-installer.msi"
    Invoke-WebRequest -Uri $nodeUrl -OutFile $nodePath
    Start-Process msiexec.exe -Wait -ArgumentList "/i $nodePath /quiet"
}

# Create application pool
Write-Host "Creating application pool..." -ForegroundColor Yellow
Import-Module WebAdministration
if (Get-IISAppPool -Name $AppPoolName -ErrorAction SilentlyContinue) {
    Remove-IISAppPool -Name $AppPoolName -Confirm:$false
}
New-IISAppPool -Name $AppPoolName -Force
Set-ItemProperty -Path "IIS:\AppPools\$AppPoolName" -Name processModel.identityType -Value ApplicationPoolIdentity
Set-ItemProperty -Path "IIS:\AppPools\$AppPoolName" -Name recycling.periodicRestart.time -Value "00:00:00"

# Build frontend
Write-Host "Building frontend..." -ForegroundColor Yellow
Set-Location "$InstallPath\frontend"
npm install
npm run build

# Install backend dependencies
Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
Set-Location "$InstallPath\backend"
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn httpx pyyaml ldap3 pyjwt psutil python-multipart pywin32

# Create IIS site
Write-Host "Creating IIS site..." -ForegroundColor Yellow
$sitePath = "$InstallPath\frontend\dist"
if (Get-IISSite -Name $SiteName -ErrorAction SilentlyContinue) {
    Remove-IISSite -Name $SiteName -Confirm:$false
}
New-IISSite -Name $SiteName -PhysicalPath $sitePath -ApplicationPool $AppPoolName -Port 80

# Configure SSL if requested
if ($SSL) {
    Write-Host "Configuring SSL..." -ForegroundColor Yellow
    # Add HTTPS binding (certificate setup required separately)
    New-IISSiteBinding -Name $SiteName -Protocol https -Port 443
    Write-Host "SSL binding created. Configure certificate in IIS Manager." -ForegroundColor Yellow
}

# Set up domain binding
Write-Host "Setting up domain binding..." -ForegroundColor Yellow
New-IISSiteBinding -Name $SiteName -Protocol http -Port 80 -HostHeader $Domain
if ($SSL) {
    New-IISSiteBinding -Name $SiteName -Protocol https -Port 443 -HostHeader $Domain
}

# Install and start backend service
Write-Host "Installing backend service..." -ForegroundColor Yellow
Set-Location "$InstallPath\backend"
python service.py install
python service.py start

# Create firewall rules
Write-Host "Creating firewall rules..." -ForegroundColor Yellow
New-NetFirewallRule -DisplayName "Dexter API" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow
New-NetFirewallRule -DisplayName "HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
New-NetFirewallRule -DisplayName "HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow

# Set environment variables
Write-Host "Setting environment variables..." -ForegroundColor Yellow
[Environment]::SetEnvironmentVariable("DEXTER_CONFIG_FILE", "$InstallPath\config.json", "Machine")
[Environment]::SetEnvironmentVariable("DEXTER_DOWNLOADS_DIR", "$InstallPath\vm_shared", "Machine")

# Create scheduled task for log rotation
Write-Host "Creating maintenance tasks..." -ForegroundColor Yellow
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-Command `"Get-ChildItem '$InstallPath\logs' -Name '*.log' | Where-Object {`$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | Remove-Item -Force`""
$trigger = New-ScheduledTaskTrigger -Daily -At "2:00AM"
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount
Register-ScheduledTask -TaskName "DexterLogCleanup" -Action $action -Trigger $trigger -Principal $principal

Write-Host "=== Deployment Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Configure your VM password: `$env:DEXTER_VM_PASSWORD = 'YourPassword'" -ForegroundColor White
Write-Host "2. Set up SSL certificate in IIS Manager for $Domain" -ForegroundColor White
Write-Host "3. Configure DNS to point $Domain to this server" -ForegroundColor White
Write-Host "4. Update config.json with your LLM API keys" -ForegroundColor White
Write-Host "5. Set up Hyper-V VM and shared folder" -ForegroundColor White
Write-Host ""
Write-Host "Access your deployment at:" -ForegroundColor Green
Write-Host "  HTTP:  http://$Domain" -ForegroundColor White
Write-Host "  HTTPS: https://$Domain" -ForegroundColor White
Write-Host "  API:   http://$Domain/api/health" -ForegroundColor White
