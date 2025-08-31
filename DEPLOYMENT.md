# Dexter v3 Production Deployment Guide

## Overview
This guide covers the complete deployment of Dexter v3 on Windows Server 2022 with IIS, SSL, and domain integration for www.gliksbot.com.

## Prerequisites

### System Requirements
- Windows Server 2022 Standard or Datacenter
- Minimum 8GB RAM (16GB recommended)
- 100GB available disk space on M: drive
- Domain controller access (for LDAP integration)
- SSL certificate for www.gliksbot.com

### Required Software
- PowerShell 5.1 or higher
- Internet connection for downloading dependencies
- Administrator privileges

## Deployment Steps

### 1. Initial System Setup

```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine -Force

# Clone or copy Dexter v3 to M:\gliksbot
# Ensure all files are present in m:\gliksbot\
```

### 2. Configure Environment Variables

Copy and edit the environment template:
```powershell
cp m:\gliksbot\.env.template m:\gliksbot\.env.production
```

Update the following variables in `.env.production`:
- `DEXTER_VM_PASSWORD` - Secure password for Hyper-V VM
- `DEXTER_SERVICE_ACCOUNT` - Domain service account (optional)
- `DEXTER_LDAP_BIND_DN` - LDAP service account DN
- `DEXTER_LDAP_BIND_PASSWORD` - LDAP service account password
- `OPENAI_API_KEY` - OpenAI API key (if using)
- `DEXTER_JWT_SECRET` - Secure JWT secret (32+ characters)
- `DEXTER_ENCRYPTION_KEY` - Encryption key (32 characters)

### 3. Run Production Setup

Execute the main setup script:
```powershell
cd m:\gliksbot
.\production_setup.ps1 -DomainName "www.gliksbot.com" -VMPassword "YourSecureVMPassword"
```

The script will:
- Install required Windows features (IIS, Hyper-V)
- Install Python and Node.js
- Create IIS application pool and website
- Install Python dependencies
- Build React frontend
- Configure Windows Firewall
- Install Windows Service
- Set up scheduled backups

### 4. SSL Certificate Installation

If you have an SSL certificate:
```powershell
.\install-ssl.ps1 -CertificatePath "path\to\certificate.pfx" -CertificatePassword "certpassword" -DomainName "www.gliksbot.com"
```

For Let's Encrypt certificates:
1. Install Certbot or win-acme
2. Obtain certificate using HTTP-01 challenge
3. Run the SSL installation script

### 5. Hyper-V VM Setup

Create the DexterVM manually:
1. Open Hyper-V Manager
2. Create new VM named "DexterVM"
3. Allocate 2GB RAM, 40GB disk
4. Install Windows Server Core or Desktop
5. Configure Administrator password
6. Enable PowerShell Direct
7. Create shared folder mapping:
   - Host: `m:\gliksbot\vm_shared`
   - Guest: `C:\HostShare`

### 6. DNS Configuration

Configure DNS to point www.gliksbot.com to your server:
- A record: www.gliksbot.com → [Server IP]
- CNAME record: gliksbot.com → www.gliksbot.com (optional)

### 7. Domain Integration (Optional)

For Active Directory integration:
1. Join the server to the domain
2. Create service account: `svc-dexter`
3. Grant "Log on as a service" right
4. Update LDAP settings in config.json
5. Create security group: "Dexter Users"

### 8. Start Services

Start and verify services:
```powershell
# Start Dexter Windows Service
Start-Service -Name "DexterService"

# Verify IIS website
Get-Website -Name "Dexter"

# Check service status
Get-Service -Name "DexterService"
```

### 9. Health Monitoring

Start the health monitoring system:
```powershell
# Install as Windows Service (optional)
python m:\gliksbot\health_monitor.py install

# Or run manually
python m:\gliksbot\health_monitor.py
```

## Verification Checklist

### Basic Functionality
- [ ] Website loads at https://www.gliksbot.com
- [ ] HTTP redirects to HTTPS
- [ ] API responds at https://www.gliksbot.com/api/health
- [ ] React frontend loads correctly
- [ ] No certificate warnings in browser

### Service Status
- [ ] DexterService is running
- [ ] IIS Application Pool is started
- [ ] Hyper-V VM is accessible
- [ ] Database file exists and is readable

### Security
- [ ] SSL certificate is valid and trusted
- [ ] HTTPS redirect is working
- [ ] Security headers are present
- [ ] VM isolation is functional
- [ ] LDAP authentication works (if configured)

### Performance
- [ ] Page load time < 3 seconds
- [ ] API response time < 1 second
- [ ] CPU usage < 50% under normal load
- [ ] Memory usage < 70%

## Configuration Files

### Key Configuration Files
- `m:\gliksbot\config.json` - Main application configuration
- `m:\gliksbot\.env.production` - Environment variables
- `m:\gliksbot\frontend\dist\web.config` - IIS URL rewrite rules

### Log Files
- `m:\gliksbot\logs\dexter.log` - Application logs
- `m:\gliksbot\logs\health_monitor.log` - Health monitoring logs
- `m:\gliksbot\logs\health_reports\` - Health check reports

### Backup Files
- `m:\gliksbot\backups\` - Automated daily backups
- Retention: 30 days

## Troubleshooting

### Common Issues

**Service won't start:**
- Check event logs: `Get-EventLog -LogName Application -Source DexterService`
- Verify Python installation: `python --version`
- Check dependencies: `pip list`

**Website not accessible:**
- Verify IIS binding: `Get-WebBinding -Name "Dexter"`
- Check firewall rules: `Get-NetFirewallRule -DisplayName "*HTTP*"`
- Test DNS resolution: `nslookup www.gliksbot.com`

**SSL certificate issues:**
- Verify certificate: `Get-ChildItem Cert:\LocalMachine\My`
- Check binding: `netsh http show sslcert`
- Test certificate chain: Use SSL checker tool

**VM communication fails:**
- Check VM state: `Get-VM -Name "DexterVM"`
- Verify shared folder: Test file creation in vm_shared
- Check PowerShell Direct: `Enter-PSSession -VMName "DexterVM"`

### Log Analysis

Check logs in order of priority:
1. Windows Event Log (System and Application)
2. `m:\gliksbot\logs\dexter.log`
3. `m:\gliksbot\logs\health_monitor.log`
4. IIS logs: `C:\inetpub\logs\LogFiles\`

### Performance Tuning

**Database optimization:**
- Enable WAL mode: `PRAGMA journal_mode=WAL`
- Optimize queries with EXPLAIN QUERY PLAN
- Consider database vacuum during maintenance

**IIS optimization:**
- Enable compression in web.config
- Set appropriate cache headers
- Configure application pool recycling

## Maintenance

### Daily Tasks
- Monitor health check reports
- Review error logs
- Check disk space usage

### Weekly Tasks
- Review performance metrics
- Check certificate expiration
- Verify backup integrity

### Monthly Tasks
- Update dependencies
- Review security settings
- Performance optimization review

### Quarterly Tasks
- Security audit
- Disaster recovery test
- Capacity planning review

## Security Considerations

### Network Security
- Configure Windows Firewall
- Use HTTPS only
- Implement proper CORS settings
- Regular security updates

### Application Security
- Secure JWT secret rotation
- Database encryption at rest
- Input validation and sanitization
- Regular dependency updates

### VM Security
- Isolated execution environment
- Limited network access
- Secure file sharing
- Regular VM snapshots

## Disaster Recovery

### Backup Strategy
- Automated daily backups (config.json, database, skills)
- Offsite backup replication
- VM snapshot before major changes
- Configuration documentation backup

### Recovery Procedures
1. Restore from backup
2. Reconfigure DNS if needed
3. Reinstall SSL certificate
4. Restart services
5. Verify functionality

## Support and Updates

### Update Procedure
1. Stop services
2. Backup current configuration
3. Update application files
4. Update dependencies
5. Test in VM first
6. Deploy to production
7. Restart services
8. Verify functionality

### Getting Help
- Check logs first
- Review troubleshooting section
- Check GitHub issues
- Contact system administrator

## License and Legal

Ensure compliance with:
- Software licensing requirements
- SSL certificate terms
- API usage agreements
- Data protection regulations
