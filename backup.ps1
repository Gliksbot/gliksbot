# Dexter v3 Backup Script
$BackupPath = "m:\gliksbot\backups\backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $BackupPath -Force

# Backup database
Copy-Item "m:\gliksbot\dexter.db" "$BackupPath\dexter.db" -ErrorAction SilentlyContinue

# Backup configuration
Copy-Item "m:\gliksbot\config.json" "$BackupPath\config.json" -ErrorAction SilentlyContinue

# Backup skills
if (Test-Path "m:\gliksbot\skills") {
    Copy-Item "m:\gliksbot\skills" "$BackupPath\skills" -Recurse -ErrorAction SilentlyContinue
}

# Cleanup old backups (keep last 30 days)
Get-ChildItem "m:\gliksbot\backups" | Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-30) } | Remove-Item -Recurse -Force

Write-Host "Backup completed: $BackupPath"
