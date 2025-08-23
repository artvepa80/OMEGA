#!/usr/bin/env python3
"""
OMEGA SSL Health Monitoring System
Comprehensive SSL certificate monitoring, alerting, and health checking
"""

import click
import subprocess
import json
import time
import requests
import ssl
import socket
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import logging

@dataclass
class SSLHealthStatus:
    domain: str
    port: int
    is_valid: bool
    certificate_subject: str
    certificate_issuer: str
    expiry_date: str
    days_until_expiry: int
    cipher_suite: str
    protocol_version: str
    certificate_fingerprint: str
    ocsp_status: str
    chain_valid: bool
    timestamp: str
    errors: List[str]

class SSLHealthMonitor:
    """Comprehensive SSL health monitoring system"""
    
    def __init__(self, config_path: str = "./ssl/monitoring_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.setup_logging()
    
    def _load_config(self) -> dict:
        """Load monitoring configuration"""
        
        default_config = {
            "domains": [
                {
                    "name": "omega-api.akash.network",
                    "port": 443,
                    "endpoints": ["/health", "/api/status", "/ssl/info"]
                }
            ],
            "monitoring": {
                "check_interval": 3600,  # 1 hour
                "alert_threshold_days": 30,
                "urgent_threshold_days": 7,
                "critical_threshold_days": 1
            },
            "notifications": {
                "enabled": False,
                "email": {
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "from_email": "admin@omega-pro-ai.com",
                    "to_emails": ["admin@omega-pro-ai.com"]
                },
                "webhook": {
                    "enabled": False,
                    "url": "",
                    "headers": {}
                }
            },
            "logging": {
                "level": "INFO",
                "file": "./logs/ssl_monitoring.log",
                "max_size_mb": 10,
                "backup_count": 5
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    return {**default_config, **config}
            except Exception as e:
                print(f"Warning: Failed to load config from {self.config_path}: {e}")
        
        # Create default config file
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def setup_logging(self):
        """Setup logging configuration"""
        
        log_config = self.config.get("logging", {})
        log_file = Path(log_config.get("file", "./logs/ssl_monitoring.log"))
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_config.get("level", "INFO")),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def check_ssl_health(self, domain: str, port: int = 443) -> SSLHealthStatus:
        """Comprehensive SSL health check for a domain"""
        
        errors = []
        
        try:
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect and get certificate information
            with socket.create_connection((domain, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Extract certificate information
                    subject_dict = dict(x[0] for x in cert['subject'])
                    issuer_dict = dict(x[0] for x in cert['issuer'])
                    
                    subject = subject_dict.get('commonName', 'Unknown')
                    issuer = issuer_dict.get('organizationName', 'Unknown')
                    
                    # Parse expiry date
                    expiry_str = cert['notAfter']
                    expiry_date = datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y GMT')
                    days_until_expiry = (expiry_date - datetime.utcnow()).days
                    
                    # Get SSL/TLS information
                    cipher_suite = ssock.cipher()[0] if ssock.cipher() else 'Unknown'
                    protocol_version = ssock.version() or 'Unknown'
                    
                    # Get certificate fingerprint
                    cert_der = ssock.getpeercert(binary_form=True)
                    fingerprint = ssl.DER_cert_to_PEM_cert(cert_der).encode()
                    import hashlib
                    cert_fingerprint = hashlib.sha256(cert_der).hexdigest()
                    
                    # Check OCSP status (simplified)
                    ocsp_status = self._check_ocsp_status(domain, port)
                    
                    # Validate certificate chain
                    chain_valid = self._validate_certificate_chain(domain, port)
                    
                    return SSLHealthStatus(
                        domain=domain,
                        port=port,
                        is_valid=days_until_expiry > 0,
                        certificate_subject=subject,
                        certificate_issuer=issuer,
                        expiry_date=expiry_date.isoformat(),
                        days_until_expiry=days_until_expiry,
                        cipher_suite=cipher_suite,
                        protocol_version=protocol_version,
                        certificate_fingerprint=cert_fingerprint,
                        ocsp_status=ocsp_status,
                        chain_valid=chain_valid,
                        timestamp=datetime.now().isoformat(),
                        errors=errors
                    )
                    
        except ssl.SSLError as e:
            errors.append(f"SSL Error: {str(e)}")
        except socket.error as e:
            errors.append(f"Connection Error: {str(e)}")
        except Exception as e:
            errors.append(f"Unknown Error: {str(e)}")
        
        # Return error status
        return SSLHealthStatus(
            domain=domain,
            port=port,
            is_valid=False,
            certificate_subject="Unknown",
            certificate_issuer="Unknown",
            expiry_date="Unknown",
            days_until_expiry=-1,
            cipher_suite="Unknown",
            protocol_version="Unknown",
            certificate_fingerprint="Unknown",
            ocsp_status="Unknown",
            chain_valid=False,
            timestamp=datetime.now().isoformat(),
            errors=errors
        )
    
    def _check_ocsp_status(self, domain: str, port: int) -> str:
        """Check OCSP status (simplified implementation)"""
        
        try:
            # Use openssl to check OCSP status
            result = subprocess.run([
                'openssl', 's_client', '-connect', f'{domain}:{port}',
                '-status', '-verify_return_error'
            ], input='', capture_output=True, text=True, timeout=10)
            
            if 'OCSP Response Status: successful' in result.stderr:
                return 'Valid'
            elif 'OCSP response: no response sent' in result.stderr:
                return 'No Response'
            else:
                return 'Unknown'
                
        except Exception:
            return 'Error'
    
    def _validate_certificate_chain(self, domain: str, port: int) -> bool:
        """Validate certificate chain"""
        
        try:
            result = subprocess.run([
                'openssl', 's_client', '-connect', f'{domain}:{port}',
                '-verify_return_error', '-brief'
            ], input='', capture_output=True, text=True, timeout=10)
            
            return 'Verification: OK' in result.stderr or result.returncode == 0
            
        except Exception:
            return False
    
    def check_endpoint_health(self, domain: str, endpoint: str) -> dict:
        """Check specific endpoint health over HTTPS"""
        
        url = f"https://{domain}{endpoint}"
        
        try:
            response = requests.get(url, timeout=10, verify=True)
            
            return {
                "url": url,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "headers": dict(response.headers),
                "ssl_info": {
                    "version": getattr(response.raw._connection.sock, 'version', lambda: 'Unknown')(),
                    "cipher": getattr(response.raw._connection.sock, 'cipher', lambda: ['Unknown'])()[0] if hasattr(response.raw._connection.sock, 'cipher') else 'Unknown'
                },
                "success": True,
                "error": None
            }
            
        except Exception as e:
            return {
                "url": url,
                "status_code": 0,
                "response_time": 0,
                "headers": {},
                "ssl_info": {},
                "success": False,
                "error": str(e)
            }
    
    def generate_health_report(self) -> dict:
        """Generate comprehensive SSL health report"""
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "domains": [],
            "summary": {
                "total_domains": 0,
                "healthy_domains": 0,
                "expiring_soon": 0,
                "expired": 0,
                "errors": 0
            }
        }
        
        for domain_config in self.config["domains"]:
            domain = domain_config["name"]
            port = domain_config.get("port", 443)
            endpoints = domain_config.get("endpoints", [])
            
            self.logger.info(f"Checking SSL health for {domain}:{port}")
            
            # Check SSL health
            ssl_status = self.check_ssl_health(domain, port)
            
            # Check endpoint health
            endpoint_results = []
            for endpoint in endpoints:
                endpoint_health = self.check_endpoint_health(domain, endpoint)
                endpoint_results.append(endpoint_health)
            
            domain_report = {
                "domain": domain,
                "port": port,
                "ssl_status": asdict(ssl_status),
                "endpoints": endpoint_results
            }
            
            report["domains"].append(domain_report)
            
            # Update summary
            report["summary"]["total_domains"] += 1
            
            if ssl_status.is_valid:
                if ssl_status.days_until_expiry > 30:
                    report["summary"]["healthy_domains"] += 1
                elif ssl_status.days_until_expiry > 0:
                    report["summary"]["expiring_soon"] += 1
                else:
                    report["summary"]["expired"] += 1
            else:
                report["summary"]["errors"] += 1
        
        return report
    
    def send_alert(self, alert_type: str, message: str, details: dict = None):
        """Send alert notifications"""
        
        notifications = self.config.get("notifications", {})
        
        if not notifications.get("enabled", False):
            return
        
        # Email notification
        email_config = notifications.get("email", {})
        if email_config.get("username") and email_config.get("password"):
            self._send_email_alert(alert_type, message, details, email_config)
        
        # Webhook notification
        webhook_config = notifications.get("webhook", {})
        if webhook_config.get("enabled", False) and webhook_config.get("url"):
            self._send_webhook_alert(alert_type, message, details, webhook_config)
    
    def _send_email_alert(self, alert_type: str, message: str, details: dict, config: dict):
        """Send email alert"""
        
        try:
            msg = MimeMultipart()
            msg['From'] = config['from_email']
            msg['To'] = ', '.join(config['to_emails'])
            msg['Subject'] = f"OMEGA SSL Alert: {alert_type}"
            
            body = f"""
SSL Alert: {alert_type}

Message: {message}

Timestamp: {datetime.now().isoformat()}

Details:
{json.dumps(details, indent=2) if details else 'No additional details'}

--
OMEGA SSL Monitoring System
"""
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
            server.login(config['username'], config['password'])
            
            text = msg.as_string()
            server.sendmail(config['from_email'], config['to_emails'], text)
            server.quit()
            
            self.logger.info(f"Email alert sent: {alert_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
    
    def _send_webhook_alert(self, alert_type: str, message: str, details: dict, config: dict):
        """Send webhook alert"""
        
        try:
            payload = {
                "alert_type": alert_type,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "details": details
            }
            
            headers = config.get("headers", {})
            headers["Content-Type"] = "application/json"
            
            response = requests.post(
                config["url"],
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info(f"Webhook alert sent: {alert_type}")
            else:
                self.logger.error(f"Webhook alert failed with status {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")
    
    def process_alerts(self, report: dict):
        """Process health report and send alerts if necessary"""
        
        monitoring_config = self.config.get("monitoring", {})
        alert_threshold = monitoring_config.get("alert_threshold_days", 30)
        urgent_threshold = monitoring_config.get("urgent_threshold_days", 7)
        critical_threshold = monitoring_config.get("critical_threshold_days", 1)
        
        for domain_report in report["domains"]:
            domain = domain_report["domain"]
            ssl_status = domain_report["ssl_status"]
            
            if not ssl_status["is_valid"]:
                self.send_alert(
                    "SSL_ERROR",
                    f"SSL certificate validation failed for {domain}",
                    ssl_status
                )
                continue
            
            days_left = ssl_status["days_until_expiry"]
            
            if days_left <= critical_threshold:
                self.send_alert(
                    "CRITICAL_EXPIRY",
                    f"SSL certificate for {domain} expires in {days_left} day(s)!",
                    ssl_status
                )
            elif days_left <= urgent_threshold:
                self.send_alert(
                    "URGENT_EXPIRY",
                    f"SSL certificate for {domain} expires in {days_left} days",
                    ssl_status
                )
            elif days_left <= alert_threshold:
                self.send_alert(
                    "EXPIRY_WARNING",
                    f"SSL certificate for {domain} expires in {days_left} days",
                    ssl_status
                )

@click.group()
def ssl_monitor():
    """SSL Health Monitoring System for OMEGA"""
    pass

@ssl_monitor.command()
@click.option('--config', help='Configuration file path')
@click.option('--output', help='Output file for health report')
def check(config, output):
    """Perform SSL health check"""
    
    monitor = SSLHealthMonitor(config) if config else SSLHealthMonitor()
    
    click.echo("🔍 Performing SSL health check...")
    
    report = monitor.generate_health_report()
    
    # Display summary
    summary = report["summary"]
    click.echo(f"\n📊 SSL Health Summary:")
    click.echo(f"   Total domains: {summary['total_domains']}")
    click.echo(f"   Healthy: {summary['healthy_domains']}")
    click.echo(f"   Expiring soon: {summary['expiring_soon']}")
    click.echo(f"   Expired: {summary['expired']}")
    click.echo(f"   Errors: {summary['errors']}")
    
    # Display detailed results
    for domain_report in report["domains"]:
        domain = domain_report["domain"]
        ssl_status = domain_report["ssl_status"]
        
        click.echo(f"\n🌐 {domain}:")
        
        if ssl_status["is_valid"]:
            days_left = ssl_status["days_until_expiry"]
            status_icon = "✅" if days_left > 30 else "⚠️" if days_left > 7 else "🚨"
            click.echo(f"   {status_icon} Certificate expires in {days_left} days")
            click.echo(f"   📜 Subject: {ssl_status['certificate_subject']}")
            click.echo(f"   🏢 Issuer: {ssl_status['certificate_issuer']}")
            click.echo(f"   🔒 Protocol: {ssl_status['protocol_version']}")
            click.echo(f"   🔐 Cipher: {ssl_status['cipher_suite']}")
        else:
            click.echo(f"   ❌ SSL validation failed")
            for error in ssl_status["errors"]:
                click.echo(f"      Error: {error}")
    
    # Process alerts
    monitor.process_alerts(report)
    
    # Save report if requested
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        click.echo(f"\n📄 Health report saved: {output_path}")

@ssl_monitor.command()
@click.option('--config', help='Configuration file path')
@click.option('--interval', default=3600, help='Check interval in seconds')
def monitor(config, interval):
    """Start continuous SSL monitoring"""
    
    monitor = SSLHealthMonitor(config) if config else SSLHealthMonitor()
    
    click.echo(f"🔍 Starting SSL monitoring (interval: {interval}s)")
    click.echo("Press Ctrl+C to stop")
    
    try:
        while True:
            try:
                report = monitor.generate_health_report()
                monitor.process_alerts(report)
                
                # Log summary
                summary = report["summary"]
                monitor.logger.info(f"Health check complete - Healthy: {summary['healthy_domains']}, "
                                  f"Expiring: {summary['expiring_soon']}, "
                                  f"Expired: {summary['expired']}, "
                                  f"Errors: {summary['errors']}")
                
                time.sleep(interval)
                
            except Exception as e:
                monitor.logger.error(f"Monitoring error: {e}")
                time.sleep(min(interval, 300))  # Wait at most 5 minutes on error
                
    except KeyboardInterrupt:
        click.echo("\n👋 SSL monitoring stopped")

@ssl_monitor.command()
def config_template():
    """Generate configuration template"""
    
    template = {
        "domains": [
            {
                "name": "omega-api.akash.network",
                "port": 443,
                "endpoints": ["/health", "/api/status", "/ssl/info"]
            }
        ],
        "monitoring": {
            "check_interval": 3600,
            "alert_threshold_days": 30,
            "urgent_threshold_days": 7,
            "critical_threshold_days": 1
        },
        "notifications": {
            "enabled": True,
            "email": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "your-email@gmail.com",
                "password": "your-app-password",
                "from_email": "admin@omega-pro-ai.com",
                "to_emails": ["admin@omega-pro-ai.com"]
            },
            "webhook": {
                "enabled": False,
                "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
                "headers": {
                    "Authorization": "Bearer YOUR_TOKEN"
                }
            }
        },
        "logging": {
            "level": "INFO",
            "file": "./logs/ssl_monitoring.log",
            "max_size_mb": 10,
            "backup_count": 5
        }
    }
    
    config_path = Path("ssl_monitoring_config.json")
    with open(config_path, 'w') as f:
        json.dump(template, f, indent=2)
    
    click.echo(f"📝 Configuration template created: {config_path}")
    click.echo("Edit the file with your specific settings.")

if __name__ == '__main__':
    ssl_monitor()