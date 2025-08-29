"""
Health monitoring and alerting system for Dexter v3 production environment.
"""

import asyncio
import json
import logging
import os
import smtplib
import subprocess
import time
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from pathlib import Path
from typing import Dict, List, Optional

import aiofiles
import aiohttp
import psutil
import sqlite3


class HealthMonitor:
    """Production health monitoring system."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.alerts_sent = set()
        self.last_check = {}
        
    def _load_config(self) -> dict:
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            # Fallback configuration
            return {
                "monitoring": {
                    "check_interval": 300,
                    "alert_cooldown": 3600,
                    "thresholds": {
                        "cpu_percent": 80,
                        "memory_percent": 85,
                        "disk_percent": 90,
                        "response_time_ms": 5000
                    },
                    "email": {
                        "enabled": False,
                        "smtp_server": "smtp.gmail.com",
                        "smtp_port": 587,
                        "username": "",
                        "password": "",
                        "to_addresses": []
                    }
                }
            }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger("dexter_monitor")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # File handler
            log_path = Path("m:/gliksbot/logs/health_monitor.log")
            log_path.parent.mkdir(exist_ok=True)
            
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(logging.INFO)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    async def check_system_health(self) -> Dict[str, any]:
        """Check overall system health."""
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "checks": {}
        }
        
        # System resources
        health_status["checks"]["cpu"] = await self._check_cpu()
        health_status["checks"]["memory"] = await self._check_memory()
        health_status["checks"]["disk"] = await self._check_disk()
        
        # Services
        health_status["checks"]["dexter_service"] = await self._check_service("DexterService")
        health_status["checks"]["iis"] = await self._check_service("W3SVC")
        
        # Application health
        health_status["checks"]["api"] = await self._check_api()
        health_status["checks"]["database"] = await self._check_database()
        health_status["checks"]["vm"] = await self._check_vm()
        
        # Website accessibility
        health_status["checks"]["website"] = await self._check_website()
        
        # Determine overall status
        failed_checks = [
            name for name, check in health_status["checks"].items()
            if not check.get("healthy", False)
        ]
        
        if failed_checks:
            health_status["status"] = "unhealthy"
            health_status["failed_checks"] = failed_checks
        
        return health_status
    
    async def _check_cpu(self) -> Dict[str, any]:
        """Check CPU usage."""
        cpu_percent = psutil.cpu_percent(interval=1)
        threshold = self.config.get("monitoring", {}).get("thresholds", {}).get("cpu_percent", 80)
        
        return {
            "healthy": cpu_percent < threshold,
            "value": cpu_percent,
            "threshold": threshold,
            "unit": "percent"
        }
    
    async def _check_memory(self) -> Dict[str, any]:
        """Check memory usage."""
        memory = psutil.virtual_memory()
        threshold = self.config.get("monitoring", {}).get("thresholds", {}).get("memory_percent", 85)
        
        return {
            "healthy": memory.percent < threshold,
            "value": memory.percent,
            "threshold": threshold,
            "unit": "percent",
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2)
        }
    
    async def _check_disk(self) -> Dict[str, any]:
        """Check disk usage."""
        disk = psutil.disk_usage("m:/")
        threshold = self.config.get("monitoring", {}).get("thresholds", {}).get("disk_percent", 90)
        percent_used = (disk.used / disk.total) * 100
        
        return {
            "healthy": percent_used < threshold,
            "value": round(percent_used, 2),
            "threshold": threshold,
            "unit": "percent",
            "total_gb": round(disk.total / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2)
        }
    
    async def _check_service(self, service_name: str) -> Dict[str, any]:
        """Check Windows service status."""
        try:
            result = subprocess.run([
                "powershell", "-Command",
                f"Get-Service -Name '{service_name}' -ErrorAction SilentlyContinue | Select-Object Status"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and "Running" in result.stdout:
                return {"healthy": True, "status": "running"}
            else:
                return {"healthy": False, "status": "stopped", "error": result.stderr}
        except Exception as e:
            return {"healthy": False, "status": "unknown", "error": str(e)}
    
    async def _check_api(self) -> Dict[str, any]:
        """Check Dexter API health."""
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:8000/api/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    threshold = self.config.get("monitoring", {}).get("thresholds", {}).get("response_time_ms", 5000)
                    
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "healthy": response_time < threshold,
                            "status_code": response.status,
                            "response_time_ms": round(response_time, 2),
                            "threshold_ms": threshold,
                            "data": data
                        }
                    else:
                        return {
                            "healthy": False,
                            "status_code": response.status,
                            "response_time_ms": round(response_time, 2)
                        }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _check_database(self) -> Dict[str, any]:
        """Check database connectivity and integrity."""
        try:
            db_path = self.config.get("runtime", {}).get("db_path", "./dexter.db")
            
            if not os.path.exists(db_path):
                return {"healthy": False, "error": "Database file not found"}
            
            # Check database integrity
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Simple integrity check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            # Check table counts
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "healthy": result[0] == "ok",
                "integrity": result[0],
                "table_count": table_count,
                "size_mb": round(os.path.getsize(db_path) / (1024**2), 2)
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _check_vm(self) -> Dict[str, any]:
        """Check Hyper-V VM status."""
        try:
            vm_name = self.config.get("runtime", {}).get("sandbox", {}).get("hyperv", {}).get("vm_name", "DexterVM")
            
            result = subprocess.run([
                "powershell", "-Command",
                f"Get-VM -Name '{vm_name}' -ErrorAction SilentlyContinue | Select-Object State"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and "Running" in result.stdout:
                return {"healthy": True, "state": "running"}
            elif "Off" in result.stdout:
                return {"healthy": False, "state": "stopped"}
            else:
                return {"healthy": False, "state": "not_found", "error": result.stderr}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _check_website(self) -> Dict[str, any]:
        """Check website accessibility."""
        try:
            domain = self.config.get("domain", {}).get("name", "www.gliksbot.com")
            
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{domain}",
                    timeout=aiohttp.ClientTimeout(total=15),
                    ssl=False  # Skip SSL verification for self-signed certs
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    return {
                        "healthy": response.status == 200,
                        "status_code": response.status,
                        "response_time_ms": round(response_time, 2)
                    }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def send_alert(self, health_status: Dict[str, any]):
        """Send alert if health check fails."""
        if health_status["status"] == "healthy":
            return
        
        # Check cooldown period
        alert_key = str(sorted(health_status.get("failed_checks", [])))
        cooldown = self.config.get("monitoring", {}).get("alert_cooldown", 3600)
        
        if alert_key in self.alerts_sent:
            last_sent = self.alerts_sent[alert_key]
            if time.time() - last_sent < cooldown:
                return
        
        # Send email alert
        email_config = self.config.get("monitoring", {}).get("email", {})
        if email_config.get("enabled", False):
            await self._send_email_alert(health_status, email_config)
        
        # Log alert
        self.logger.warning(f"Health check failed: {health_status['failed_checks']}")
        
        # Update alert tracking
        self.alerts_sent[alert_key] = time.time()
    
    async def _send_email_alert(self, health_status: Dict[str, any], email_config: Dict[str, any]):
        """Send email alert."""
        try:
            msg = MimeMultipart()
            msg['From'] = email_config['username']
            msg['To'] = ', '.join(email_config['to_addresses'])
            msg['Subject'] = f"Dexter v3 Health Alert - {health_status['status'].upper()}"
            
            # Create email body
            body = f"""
Dexter v3 Health Check Alert

Status: {health_status['status'].upper()}
Timestamp: {health_status['timestamp']}
Failed Checks: {', '.join(health_status.get('failed_checks', []))}

Detailed Results:
{json.dumps(health_status['checks'], indent=2)}

Please check the system immediately.
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            server.send_message(msg)
            server.quit()
            
            self.logger.info("Alert email sent successfully")
        except Exception as e:
            self.logger.error(f"Failed to send alert email: {e}")
    
    async def save_health_report(self, health_status: Dict[str, any]):
        """Save health report to file."""
        try:
            reports_dir = Path("m:/gliksbot/logs/health_reports")
            reports_dir.mkdir(exist_ok=True)
            
            # Save current report
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            report_path = reports_dir / f"health_{timestamp}.json"
            
            async with aiofiles.open(report_path, 'w') as f:
                await f.write(json.dumps(health_status, indent=2))
            
            # Cleanup old reports (keep last 7 days)
            cutoff_time = time.time() - (7 * 24 * 3600)
            for report_file in reports_dir.glob("health_*.json"):
                if report_file.stat().st_mtime < cutoff_time:
                    report_file.unlink()
            
        except Exception as e:
            self.logger.error(f"Failed to save health report: {e}")
    
    async def run_monitoring_loop(self):
        """Main monitoring loop."""
        self.logger.info("Starting Dexter v3 health monitoring")
        
        check_interval = self.config.get("monitoring", {}).get("check_interval", 300)
        
        while True:
            try:
                # Run health check
                health_status = await self.check_system_health()
                
                # Save report
                await self.save_health_report(health_status)
                
                # Send alerts if needed
                await self.send_alert(health_status)
                
                # Log status
                if health_status["status"] == "healthy":
                    self.logger.info("Health check passed")
                else:
                    self.logger.warning(f"Health check failed: {health_status['failed_checks']}")
                
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
            
            # Wait for next check
            await asyncio.sleep(check_interval)


async def main():
    """Main entry point for health monitoring."""
    monitor = HealthMonitor()
    await monitor.run_monitoring_loop()


if __name__ == "__main__":
    asyncio.run(main())
