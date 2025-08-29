# IIS Setup and Configuration Script
# Run as Administrator after main production setup

param(
    [Parameter(Mandatory=$false)]
    [string]$DomainName = "www.gliksbot.com"
)

Write-Host "=== IIS Configuration Fix ===" -ForegroundColor Green

# Ensure IIS Management modules are properly loaded
Write-Host "Loading IIS modules..." -ForegroundColor Yellow
Import-Module WebAdministration -Force

# Check if IIS is installed and running
$iisService = Get-Service -Name W3SVC -ErrorAction SilentlyContinue
if (-not $iisService) {
    Write-Error "IIS is not installed. Please install IIS first."
    exit 1
}

if ($iisService.Status -ne "Running") {
    Start-Service W3SVC
    Write-Host "Started IIS service" -ForegroundColor Green
}

# Variables
$ProjectRoot = "m:\gliksbot"
$PoolName = "DexterAppPool"
$SiteName = "Dexter"
$PhysicalPath = "$ProjectRoot\frontend\dist"

# Ensure the physical path exists
if (!(Test-Path $PhysicalPath)) {
    Write-Host "Creating frontend dist directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $PhysicalPath -Force
    
    # Create a basic index.html for testing
    $indexContent = @"
<!DOCTYPE html>
<html>
<head>
    <title>Dexter v3 - Setup in Progress</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #1e293b; color: white; }
        .container { max-width: 600px; margin: 0 auto; }
        .status { background: #059669; padding: 20px; border-radius: 10px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Dexter v3</h1>
        <div class="status">
            <h2>Setup in Progress</h2>
            <p>The system is being configured. Please wait for the frontend build to complete.</p>
        </div>
        <p>Domain: $DomainName</p>
        <p>Status: IIS Configured</p>
    </div>
</body>
</html>
"@
    $indexContent | Out-File -FilePath "$PhysicalPath\index.html" -Encoding UTF8
}

# Remove existing application pool if it exists
Write-Host "Configuring application pool..." -ForegroundColor Yellow
if (Get-IISAppPool -Name $PoolName -ErrorAction SilentlyContinue) {
    Remove-WebAppPool -Name $PoolName -Confirm:$false
    Write-Host "Removed existing application pool" -ForegroundColor Yellow
}

# Create new application pool
New-WebAppPool -Name $PoolName -Force
Set-ItemProperty -Path "IIS:\AppPools\$PoolName" -Name processModel.identityType -Value ApplicationPoolIdentity
Set-ItemProperty -Path "IIS:\AppPools\$PoolName" -Name recycling.periodicRestart.time -Value "00:00:00"
Set-ItemProperty -Path "IIS:\AppPools\$PoolName" -Name processModel.idleTimeout -Value "00:00:00"
Set-ItemProperty -Path "IIS:\AppPools\$PoolName" -Name processModel.loadUserProfile -Value $true
Write-Host "Created application pool: $PoolName" -ForegroundColor Green

# Remove existing website if it exists
if (Get-Website -Name $SiteName -ErrorAction SilentlyContinue) {
    Remove-Website -Name $SiteName -Confirm:$false
    Write-Host "Removed existing website" -ForegroundColor Yellow
}

# Remove default website if it exists
if (Get-Website -Name "Default Web Site" -ErrorAction SilentlyContinue) {
    Remove-Website -Name "Default Web Site" -Confirm:$false
    Write-Host "Removed default website" -ForegroundColor Yellow
}

# Create new website
Write-Host "Creating website..." -ForegroundColor Yellow
New-Website -Name $SiteName -Port 80 -PhysicalPath $PhysicalPath -ApplicationPool $PoolName -Force

# Add HTTPS binding
Write-Host "Adding HTTPS binding..." -ForegroundColor Yellow
try {
    # Remove existing HTTPS binding if it exists
    Get-WebBinding -Name $SiteName -Protocol https -ErrorAction SilentlyContinue | Remove-WebBinding -Confirm:$false
    
    # Add new HTTPS binding
    New-WebBinding -Name $SiteName -Protocol https -Port 443 -HostHeader $DomainName -SslFlags 1
    Write-Host "Added HTTPS binding for $DomainName" -ForegroundColor Green
} catch {
    Write-Warning "HTTPS binding failed: $($_.Exception.Message)"
    Write-Host "You can configure SSL later using install-ssl.ps1" -ForegroundColor Yellow
}

# Create web.config with proper settings
Write-Host "Creating web.config..." -ForegroundColor Yellow
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
            <mimeMap fileExtension=".woff" mimeType="font/woff" />
            <mimeMap fileExtension=".woff2" mimeType="font/woff2" />
        </staticContent>
        <httpHeaders>
            <add name="X-Content-Type-Options" value="nosniff" />
            <add name="X-Frame-Options" value="DENY" />
            <add name="X-XSS-Protection" value="1; mode=block" />
        </httpHeaders>
    </system.webServer>
</configuration>
"@

$webConfigContent | Out-File -FilePath "$PhysicalPath\web.config" -Encoding UTF8
Write-Host "Created web.config" -ForegroundColor Green

# Set proper permissions on the website directory
Write-Host "Setting directory permissions..." -ForegroundColor Yellow
$acl = Get-Acl $PhysicalPath
$accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule("IIS_IUSRS", "ReadAndExecute", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.SetAccessRule($accessRule)
$accessRule2 = New-Object System.Security.AccessControl.FileSystemAccessRule("IUSR", "ReadAndExecute", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.SetAccessRule($accessRule2)
Set-Acl -Path $PhysicalPath -AclObject $acl

# Start the application pool and website
Write-Host "Starting services..." -ForegroundColor Yellow
Start-WebAppPool -Name $PoolName
Start-Website -Name $SiteName

# Test the configuration
Write-Host "Testing configuration..." -ForegroundColor Yellow
$website = Get-Website -Name $SiteName
$appPool = Get-IISAppPool -Name $PoolName

Write-Host ""
Write-Host "=== IIS Configuration Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Website Status:" -ForegroundColor Yellow
Write-Host "  Name: $($website.Name)" -ForegroundColor White
Write-Host "  State: $($website.State)" -ForegroundColor White
Write-Host "  Physical Path: $($website.PhysicalPath)" -ForegroundColor White
Write-Host "  Bindings:" -ForegroundColor White

$bindings = Get-WebBinding -Name $SiteName
foreach ($binding in $bindings) {
    $port = $binding.bindingInformation.Split(':')[1]
    $host = $binding.bindingInformation.Split(':')[2]
    Write-Host "    $($binding.protocol)://$host`:$port" -ForegroundColor White
}

Write-Host ""
Write-Host "Application Pool Status:" -ForegroundColor Yellow
Write-Host "  Name: $($appPool.Name)" -ForegroundColor White
Write-Host "  State: $($appPool.State)" -ForegroundColor White
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Build the frontend: cd frontend && npm run build" -ForegroundColor White
Write-Host "2. Start the backend service" -ForegroundColor White
Write-Host "3. Test access: http://localhost or http://$DomainName" -ForegroundColor White
Write-Host "4. Configure SSL certificate for HTTPS" -ForegroundColor White
