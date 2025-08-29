# SSL Certificate Installation Script for Dexter v3
# Run as Administrator after obtaining SSL certificate

param(
    [Parameter(Mandatory=$true)]
    [string]$CertificatePath,
    
    [Parameter(Mandatory=$false)]
    [string]$CertificatePassword = "",
    
    [Parameter(Mandatory=$false)]
    [string]$DomainName = "www.gliksbot.com"
)

Write-Host "=== SSL Certificate Installation ===" -ForegroundColor Green

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "This script must be run as Administrator!"
    exit 1
}

# Verify certificate file exists
if (!(Test-Path $CertificatePath)) {
    Write-Error "Certificate file not found: $CertificatePath"
    exit 1
}

# Import certificate to Windows certificate store
Write-Host "Importing certificate to Windows certificate store..." -ForegroundColor Yellow

try {
    if ($CertificatePassword) {
        $securePassword = ConvertTo-SecureString -String $CertificatePassword -Force -AsPlainText
        $cert = Import-PfxCertificate -FilePath $CertificatePath -CertStoreLocation Cert:\LocalMachine\My -Password $securePassword
    } else {
        $cert = Import-PfxCertificate -FilePath $CertificatePath -CertStoreLocation Cert:\LocalMachine\My
    }
    
    Write-Host "Certificate imported successfully" -ForegroundColor Green
    Write-Host "Certificate Thumbprint: $($cert.Thumbprint)" -ForegroundColor White
} catch {
    Write-Error "Failed to import certificate: $($_.Exception.Message)"
    exit 1
}

# Configure IIS HTTPS binding
Write-Host "Configuring IIS HTTPS binding..." -ForegroundColor Yellow

Import-Module WebAdministration

try {
    # Remove existing HTTPS binding if it exists
    Get-WebBinding -Name "Dexter" -Protocol https -ErrorAction SilentlyContinue | Remove-WebBinding
    
    # Add new HTTPS binding with certificate
    New-WebBinding -Name "Dexter" -Protocol https -Port 443 -HostHeader $DomainName -SslFlags 1
    
    # Bind certificate to HTTPS binding
    $binding = Get-WebBinding -Name "Dexter" -Protocol https
    $binding.AddSslCertificate($cert.Thumbprint, "My")
    
    Write-Host "HTTPS binding configured successfully" -ForegroundColor Green
} catch {
    Write-Error "Failed to configure IIS binding: $($_.Exception.Message)"
    exit 1
}

# Configure HTTP to HTTPS redirect
Write-Host "Configuring HTTP to HTTPS redirect..." -ForegroundColor Yellow

$webConfigPath = "m:\gliksbot\frontend\dist\web.config"
$redirectConfig = @"
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <rule name="HTTP to HTTPS redirect" stopProcessing="true">
                    <match url="(.*)" />
                    <conditions>
                        <add input="{HTTPS}" pattern="off" ignoreCase="true" />
                    </conditions>
                    <action type="Redirect" url="https://{HTTP_HOST}/{R:1}" 
                            redirectType="Permanent" />
                </rule>
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
        <httpHeaders>
            <add name="Strict-Transport-Security" value="max-age=31536000; includeSubDomains" />
            <add name="X-Content-Type-Options" value="nosniff" />
            <add name="X-Frame-Options" value="DENY" />
            <add name="X-XSS-Protection" value="1; mode=block" />
        </httpHeaders>
    </system.webServer>
</configuration>
"@

$redirectConfig | Out-File -FilePath $webConfigPath -Encoding UTF8

# Test certificate
Write-Host "Testing certificate configuration..." -ForegroundColor Yellow

try {
    # Test HTTPS connection
    $response = Invoke-WebRequest -Uri "https://$DomainName" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    Write-Host "HTTPS test successful: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Warning "HTTPS test failed: $($_.Exception.Message)"
    Write-Host "This may be normal if DNS is not yet configured" -ForegroundColor Yellow
}

# Configure certificate auto-renewal (if Let's Encrypt)
if ($CertificatePath -like "*letsencrypt*" -or $CertificatePath -like "*acme*") {
    Write-Host "Setting up certificate auto-renewal..." -ForegroundColor Yellow
    
    # Create renewal script
    $renewalScript = @"
# Certificate Auto-Renewal Script
# Run this monthly via scheduled task

`$Domain = "$DomainName"
`$CertPath = "$CertificatePath"
`$WebRoot = "m:\gliksbot\frontend\dist"

# Check certificate expiration
`$cert = Get-ChildItem Cert:\LocalMachine\My | Where-Object { `$_.Subject -like "*`$Domain*" } | Sort-Object NotAfter -Descending | Select-Object -First 1

if (`$cert -and `$cert.NotAfter -lt (Get-Date).AddDays(30)) {
    Write-Host "Certificate expires soon, attempting renewal..."
    
    # Add your certificate renewal command here
    # Example for Certbot:
    # certbot renew --webroot -w `$WebRoot
    
    # Reimport renewed certificate
    # .\install-ssl.ps1 -CertificatePath `$CertPath -DomainName `$Domain
} else {
    Write-Host "Certificate is still valid until `$(`$cert.NotAfter)"
}
"@
    
    $renewalScript | Out-File -FilePath "m:\gliksbot\renew-ssl.ps1" -Encoding UTF8
    
    # Schedule monthly renewal check
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"m:\gliksbot\renew-ssl.ps1`""
    $trigger = New-ScheduledTaskTrigger -Weekly -WeeksInterval 4 -DaysOfWeek Monday -At "03:00AM"
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName "DexterSSLRenewal" -Action $action -Trigger $trigger -Settings $settings -User "SYSTEM" -Force
    
    Write-Host "Auto-renewal scheduled for monthly execution" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== SSL Configuration Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Certificate Details:" -ForegroundColor Yellow
Write-Host "  Thumbprint: $($cert.Thumbprint)" -ForegroundColor White
Write-Host "  Subject: $($cert.Subject)" -ForegroundColor White
Write-Host "  Issuer: $($cert.Issuer)" -ForegroundColor White
Write-Host "  Valid From: $($cert.NotBefore)" -ForegroundColor White
Write-Host "  Valid Until: $($cert.NotAfter)" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Verify DNS points $DomainName to this server"
Write-Host "2. Test HTTPS access: https://$DomainName"
Write-Host "3. Check certificate in browser for any warnings"
Write-Host "4. Monitor certificate expiration and renewal"
Write-Host ""

# Display website status
$website = Get-Website -Name "Dexter"
Write-Host "Website Status: $($website.State)" -ForegroundColor Green

$bindings = Get-WebBinding -Name "Dexter"
Write-Host "Configured Bindings:" -ForegroundColor Yellow
foreach ($binding in $bindings) {
    Write-Host "  $($binding.Protocol)://$($binding.bindingInformation)" -ForegroundColor White
}
