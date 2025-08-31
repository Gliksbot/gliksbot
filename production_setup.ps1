# Dexter v3 Production Environment Setup Script
# Run as Administrator on Windows Server 2022

param(
    [Parameter(Mandatory=$false)]
    [string]$DomainName = "www.gliksbot.com",
    
    [Parameter(Mandatory=$false)]
    [string]$VMPassword = "",
    
    [Parameter(Mandatory=$false)]
    [string]$ServiceAccount = "GLIKSBOT\svc-dexter"
)

Write-Host "=== Dexter v3 Production Environment Setup ===" -ForegroundColor Green
Write-Host "Setting up production environment for $DomainName" -ForegroundColor Yellow

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "This script must be run as Administrator!"
    exit 1
}

# Set execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine -Force

# Create project directories
$ProjectRoot = "m:\gliksbot"
$Directories = @(
    "$ProjectRoot\vm_shared",
    "$ProjectRoot\logs",
    "$ProjectRoot\backups",
    "$ProjectRoot\ssl",
    "$ProjectRoot\temp"
)

foreach ($dir in $Directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "Created directory: $dir" -ForegroundColor Green
    }
}

# Set up VM shared directory permissions
Write-Host "Configuring VM shared directory permissions..." -ForegroundColor Yellow
$acl = Get-Acl "$ProjectRoot\vm_shared"
$accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.SetAccessRule($accessRule)
Set-Acl -Path "$ProjectRoot\vm_shared" -AclObject $acl

# Install required Windows features
Write-Host "Installing Windows features..." -ForegroundColor Yellow
$Features = @(
    "IIS-WebServerRole",
    "IIS-WebServer",
    "IIS-CommonHttpFeatures",
    "IIS-HttpRedirect",
    "IIS-WebServerManagementTools",
    "IIS-ManagementConsole",
    "IIS-IIS6ManagementCompatibility",
    "IIS-Metabase",
    "IIS-ASPNET45",
    "IIS-NetFxExtensibility45",
    "IIS-ISAPIExtensions",
    "IIS-ISAPIFilter",
    "Microsoft-Hyper-V-All"
)

foreach ($feature in $Features) {
    Enable-WindowsOptionalFeature -Online -FeatureName $feature -All -NoRestart
}

# Install Python if not present
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Python..." -ForegroundColor Yellow
    $pythonUrl = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
    $pythonInstaller = "$env:TEMP\python-installer.exe"
    Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller
    Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
    Remove-Item $pythonInstaller
}

# Install Node.js if not present
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Node.js..." -ForegroundColor Yellow
    $nodeUrl = "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi"
    $nodeInstaller = "$env:TEMP\node-installer.msi"
    Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeInstaller
    Start-Process -FilePath "msiexec.exe" -ArgumentList "/i $nodeInstaller /quiet" -Wait
    Remove-Item $nodeInstaller
}

# Refresh environment variables
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
Set-Location $ProjectRoot
if (Test-Path "requirements.txt") {
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
}

# Install Node.js dependencies and build frontend
Write-Host "Building frontend..." -ForegroundColor Yellow
if (Test-Path "frontend\package.json") {
    Set-Location "$ProjectRoot\frontend"
    npm install
    npm run build
    Set-Location $ProjectRoot
}

# Create IIS Application Pool
Write-Host "Configuring IIS..." -ForegroundColor Yellow
Import-Module WebAdministration

# Remove default website
Remove-Website -Name "Default Web Site" -ErrorAction SilentlyContinue

# Create application pool
$PoolName = "DexterAppPool"
if (Get-IISAppPool -Name $PoolName -ErrorAction SilentlyContinue) {
    Remove-WebAppPool -Name $PoolName
}

New-WebAppPool -Name $PoolName
Set-ItemProperty -Path "IIS:\AppPools\$PoolName" -Name processModel.identityType -Value ApplicationPoolIdentity
Set-ItemProperty -Path "IIS:\AppPools\$PoolName" -Name recycling.periodicRestart.time -Value "00:00:00"
Set-ItemProperty -Path "IIS:\AppPools\$PoolName" -Name processModel.idleTimeout -Value "00:00:00"

# Create website
New-Website -Name "Dexter" -Port 80 -PhysicalPath "$ProjectRoot\frontend\dist" -ApplicationPool $PoolName

# Add HTTPS binding (certificate must be installed separately)
if ($DomainName -ne "localhost") {
    New-WebBinding -Name "Dexter" -Protocol https -Port 443 -HostHeader $DomainName
}

# Configure URL Rewrite for React Router
$webConfigContent = @"
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <rule name="React Router" stopProcessing="true">
                    <match url=".*" />
                    <conditions logicalGrouping="MatchAll">
                        <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
                        <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
                        <add input="{REQUEST_URI}" pattern="^/(api)" negate="true" />
                    </conditions>
                    <action type="Rewrite" url="/" />
                </rule>
                <rule name="API Proxy" stopProcessing="true">
                    <match url="^api/(.*)" />
                    <action type="Rewrite" url="http://localhost:8000/api/{R:1}" />
                </rule>
            </rules>
        </rewrite>
        <defaultDocument>
            <files>
                <clear />
                <add value="index.html" />
            </files>
        </defaultDocument>
        <staticContent>
            <mimeMap fileExtension=".json" mimeType="application/json" />
            <mimeMap fileExtension=".js" mimeType="application/javascript" />
            <mimeMap fileExtension=".css" mimeType="text/css" />
        </staticContent>
    </system.webServer>
</configuration>
"@

$webConfigContent | Out-File -FilePath "$ProjectRoot\frontend\dist\web.config" -Encoding UTF8

# Configure Windows Firewall
Write-Host "Configuring Windows Firewall..." -ForegroundColor Yellow
New-NetFirewallRule -DisplayName "HTTP Inbound" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "HTTPS Inbound" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "Dexter API" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -ErrorAction SilentlyContinue

# Create Windows Service
Write-Host "Installing Dexter Windows Service..." -ForegroundColor Yellow
$ServiceName = "DexterService"

# Stop and remove existing service
Get-Service -Name $ServiceName -ErrorAction SilentlyContinue | Stop-Service -Force
Remove-Service -Name $ServiceName -ErrorAction SilentlyContinue

# Install new service
if (Test-Path "$ProjectRoot\service.py") {
    $pythonPath = (Get-Command python).Source
    $servicePath = "$ProjectRoot\service.py"
    
    # Install pywin32 for Windows service support
    python -m pip install pywin32
    
    # Install the service
    python "$servicePath" install
    
    # Configure service account if provided
    if ($ServiceAccount) {
        $password = Read-Host "Enter password for service account $ServiceAccount" -AsSecureString
        $credential = New-Object System.Management.Automation.PSCredential($ServiceAccount, $password)
        Set-Service -Name $ServiceName -Credential $credential
    }
    
    # Start the service
    Start-Service -Name $ServiceName
    Set-Service -Name $ServiceName -StartupType Automatic
}

# Set up environment variables
Write-Host "Configuring environment variables..." -ForegroundColor Yellow
[Environment]::SetEnvironmentVariable("DEXTER_ENV", "production", "Machine")
[Environment]::SetEnvironmentVariable("DEXTER_ROOT", $ProjectRoot, "Machine")

if ($VMPassword) {
    [Environment]::SetEnvironmentVariable("DEXTER_VM_PASSWORD", $VMPassword, "Machine")
}

# Create Hyper-V VM (optional)
if ($VMPassword) {
    Write-Host "Setting up Hyper-V VM..." -ForegroundColor Yellow
    $VMName = "DexterVM"
    
    # Check if VM exists
    if (Get-VM -Name $VMName -ErrorAction SilentlyContinue) {
        Write-Host "VM $VMName already exists" -ForegroundColor Yellow
    } else {
        # Create VM with basic configuration
        # Note: This requires a Windows ISO and additional configuration
        Write-Host "VM creation requires manual setup. Please create VM '$VMName' manually." -ForegroundColor Yellow
        Write-Host "Requirements:" -ForegroundColor White
        Write-Host "  - Name: $VMName" -ForegroundColor White
        Write-Host "  - Administrator password: [set in environment]" -ForegroundColor White
        Write-Host "  - Shared folder: $ProjectRoot\vm_shared mapped to C:\HostShare" -ForegroundColor White
    }
}

# Create backup script
$backupScript = @"
# Dexter v3 Backup Script
`$BackupPath = "$ProjectRoot\backups\backup_`$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path `$BackupPath -Force

# Backup database
Copy-Item "$ProjectRoot\dexter.db" "`$BackupPath\dexter.db" -ErrorAction SilentlyContinue

# Backup configuration
Copy-Item "$ProjectRoot\config.json" "`$BackupPath\config.json" -ErrorAction SilentlyContinue

# Backup skills
if (Test-Path "$ProjectRoot\skills") {
    Copy-Item "$ProjectRoot\skills" "`$BackupPath\skills" -Recurse -ErrorAction SilentlyContinue
}

# Cleanup old backups (keep last 30 days)
Get-ChildItem "$ProjectRoot\backups" | Where-Object { `$_.CreationTime -lt (Get-Date).AddDays(-30) } | Remove-Item -Recurse -Force

Write-Host "Backup completed: `$BackupPath"
"@

$backupScript | Out-File -FilePath "$ProjectRoot\backup.ps1" -Encoding UTF8

# Schedule daily backup
Write-Host "Scheduling daily backup..." -ForegroundColor Yellow
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$ProjectRoot\backup.ps1`""
$trigger = New-ScheduledTaskTrigger -Daily -At "02:00AM"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "DexterBackup" -Action $action -Trigger $trigger -Settings $settings -User "SYSTEM" -Force

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Configure SSL certificate in IIS Manager for $DomainName"
Write-Host "2. Set up DNS to point $DomainName to this server"
Write-Host "3. Configure LDAP settings in config.json if using Active Directory"
Write-Host "4. Create and configure Hyper-V VM '$VMName' if not already done"
Write-Host "5. Test the application at http://$DomainName"
Write-Host ""
Write-Host "Service Status:" -ForegroundColor Yellow
try {
    $service = Get-Service -Name "DexterService" -ErrorAction Stop
    Write-Host "  Dexter Service: $($service.Status)" -ForegroundColor Green
} catch {
    Write-Host "  Dexter Service: Not installed" -ForegroundColor Red
}

$website = Get-Website -Name "Dexter" -ErrorAction SilentlyContinue
if ($website) {
    Write-Host "  IIS Website: $($website.State)" -ForegroundColor Green
} else {
    Write-Host "  IIS Website: Not found" -ForegroundColor Red
}

Write-Host ""
Write-Host "Configuration files are located at: $ProjectRoot" -ForegroundColor White
Write-Host "Logs will be written to: $ProjectRoot\logs" -ForegroundColor White
Write-Host "VM shared directory: $ProjectRoot\vm_shared" -ForegroundColor White
