#!/usr/bin/env python3
"""
OMEGA Security Monitoring System
Comprehensive security monitoring, MITM detection, and incident response
"""

import asyncio
import ssl
import socket
import hashlib
import json
import time
import logging
import certifi
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import aiohttp
import cryptography
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import OpenSSL
from OpenSSL import SSL, crypto

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security_monitoring.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class SecurityAlert:
    """Security alert data structure"""
    alert_id: str
    alert_type: str
    severity: str  # critical, high, medium, low
    domain: str
    details: str
    timestamp: datetime
    resolved: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class CertificateInfo:
    """Certificate information structure"""
    domain: str
    fingerprint: str
    subject: str
    issuer: str
    valid_from: datetime
    valid_until: datetime
    serial_number: str
    signature_algorithm: str
    public_key_hash: str
    
    def to_dict(self) -> Dict:
        return asdict(self)

class SecurityMonitoringSystem:
    """Main security monitoring system"""
    
    def __init__(self, config_path: str = "security_config.json"):
        self.config = self.load_config(config_path)
        self.alerts: List[SecurityAlert] = []
        self.certificate_cache: Dict[str, CertificateInfo] = {}
        self.monitoring_active = False
        self.blocked_domains: set = set()
        
    def load_config(self, config_path: str) -> Dict:
        """Load security monitoring configuration"""
        default_config = {
            "monitored_domains": [
                "a17d0f2p7pbkp4bc0pjgbsmp8o.ingress.paradigmapolitico.online"
            ],
            "certificate_transparency_logs": [
                "https://ct.googleapis.com/logs/argon2024/ct/v1/get-entries",
                "https://ct.cloudflare.com/logs/nimbus2024/ct/v1/get-entries"
            ],
            "monitoring_interval": 300,  # 5 minutes
            "certificate_rotation_webhook": "/webhook/cert-rotation",
            "security_headers": {
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; object-src 'none';"
            },
            "alert_thresholds": {
                "certificate_expiry_days": 30,
                "max_failed_validations": 3,
                "mitm_detection_threshold": 2
            }
        }
        
        try:
            if Path(config_path).exists():
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
        except Exception as e:
            logger.warning(f"Could not load config from {config_path}: {e}")
        
        return default_config
    
    async def start_monitoring(self):
        """Start the security monitoring system"""
        logger.info("🛡️  Starting OMEGA Security Monitoring System")
        self.monitoring_active = True
        
        # Start monitoring tasks
        tasks = [
            self.certificate_monitoring_loop(),
            self.mitm_detection_loop(),
            self.security_headers_monitoring(),
            self.certificate_transparency_monitoring()
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def certificate_monitoring_loop(self):
        """Monitor SSL certificates for changes and issues"""
        while self.monitoring_active:
            try:
                for domain in self.config["monitored_domains"]:
                    await self.check_certificate_security(domain)
                    await asyncio.sleep(10)  # Space out certificate checks
                
                await asyncio.sleep(self.config["monitoring_interval"])
                
            except Exception as e:
                logger.error(f"Certificate monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def check_certificate_security(self, domain: str):
        """Comprehensive certificate security check"""
        try:
            # Get certificate information
            cert_info = await self.get_certificate_info(domain)
            
            if not cert_info:
                await self.create_alert(
                    "certificate_unavailable",
                    "critical",
                    domain,
                    "Could not retrieve certificate information"
                )
                return
            
            # Check for certificate changes (potential MITM)
            if domain in self.certificate_cache:
                cached_cert = self.certificate_cache[domain]
                if cached_cert.fingerprint != cert_info.fingerprint:
                    await self.create_alert(
                        "certificate_changed",
                        "critical",
                        domain,
                        f"Certificate fingerprint changed from {cached_cert.fingerprint} to {cert_info.fingerprint}"
                    )
            
            # Check certificate expiration
            days_until_expiry = (cert_info.valid_until - datetime.now()).days
            if days_until_expiry <= self.config["alert_thresholds"]["certificate_expiry_days"]:
                severity = "critical" if days_until_expiry <= 7 else "high"
                await self.create_alert(
                    "certificate_expiring",
                    severity,
                    domain,
                    f"Certificate expires in {days_until_expiry} days"
                )
            
            # Validate certificate chain
            await self.validate_certificate_chain(domain, cert_info)
            
            # Check certificate in CT logs
            await self.validate_certificate_transparency(domain, cert_info)
            
            # Cache certificate info
            self.certificate_cache[domain] = cert_info
            
        except Exception as e:
            logger.error(f"Certificate security check failed for {domain}: {e}")
            await self.create_alert(
                "certificate_check_failed",
                "medium",
                domain,
                f"Certificate security check failed: {str(e)}"
            )
    
    async def get_certificate_info(self, domain: str, port: int = 443) -> Optional[CertificateInfo]:
        """Get detailed certificate information"""
        try:
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect and get certificate
            with socket.create_connection((domain, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert_der = ssock.getpeercert(binary_form=True)
                    cert_info = ssock.getpeercert()
            
            # Parse certificate with cryptography library
            cert = x509.load_der_x509_certificate(cert_der)
            
            # Extract certificate information
            fingerprint = hashlib.sha256(cert_der).hexdigest()
            subject = cert.subject.rfc4514_string()
            issuer = cert.issuer.rfc4514_string()
            valid_from = cert.not_valid_before
            valid_until = cert.not_valid_after
            serial_number = str(cert.serial_number)
            
            # Get public key hash
            public_key = cert.public_key()
            public_key_der = public_key.public_key().public_bytes(
                Encoding.DER,
                PublicFormat.SubjectPublicKeyInfo
            )
            public_key_hash = hashlib.sha256(public_key_der).hexdigest()
            
            return CertificateInfo(
                domain=domain,
                fingerprint=fingerprint,
                subject=subject,
                issuer=issuer,
                valid_from=valid_from,
                valid_until=valid_until,
                serial_number=serial_number,
                signature_algorithm=cert.signature_algorithm_oid._name,
                public_key_hash=public_key_hash
            )
            
        except Exception as e:
            logger.error(f"Failed to get certificate info for {domain}: {e}")
            return None
    
    async def validate_certificate_chain(self, domain: str, cert_info: CertificateInfo):
        """Validate certificate chain and trust"""
        try:
            # This would implement comprehensive certificate chain validation
            # For now, we perform basic checks
            
            # Check if certificate is self-signed
            if cert_info.subject == cert_info.issuer:
                await self.create_alert(
                    "self_signed_certificate",
                    "medium",
                    domain,
                    "Certificate is self-signed"
                )
            
            # Check certificate validity period
            if cert_info.valid_from > datetime.now():
                await self.create_alert(
                    "certificate_not_yet_valid",
                    "high",
                    domain,
                    f"Certificate not valid until {cert_info.valid_from}"
                )
            
            if cert_info.valid_until < datetime.now():
                await self.create_alert(
                    "certificate_expired",
                    "critical",
                    domain,
                    f"Certificate expired on {cert_info.valid_until}"
                )
                
        except Exception as e:
            logger.error(f"Certificate chain validation failed for {domain}: {e}")
    
    async def validate_certificate_transparency(self, domain: str, cert_info: CertificateInfo):
        """Validate certificate in Certificate Transparency logs"""
        try:
            for ct_log_url in self.config["certificate_transparency_logs"]:
                if await self.check_certificate_in_ct_log(ct_log_url, cert_info):
                    logger.info(f"Certificate for {domain} found in CT log: {ct_log_url}")
                    return
            
            # Certificate not found in CT logs
            await self.create_alert(
                "certificate_not_in_ct_logs",
                "medium",
                domain,
                "Certificate not found in Certificate Transparency logs"
            )
            
        except Exception as e:
            logger.error(f"CT validation failed for {domain}: {e}")
    
    async def check_certificate_in_ct_log(self, ct_log_url: str, cert_info: CertificateInfo) -> bool:
        """Check if certificate exists in a specific CT log"""
        try:
            async with aiohttp.ClientSession() as session:
                query_data = {
                    "fingerprint": cert_info.fingerprint,
                    "domain": cert_info.domain
                }
                
                async with session.post(ct_log_url, json=query_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("found", False)
            
            return False
            
        except Exception as e:
            logger.debug(f"CT log query failed for {ct_log_url}: {e}")
            return False
    
    async def mitm_detection_loop(self):
        """Monitor for potential MITM attacks"""
        while self.monitoring_active:
            try:
                for domain in self.config["monitored_domains"]:
                    await self.detect_mitm_attack(domain)
                    await asyncio.sleep(5)
                
                await asyncio.sleep(self.config["monitoring_interval"])
                
            except Exception as e:
                logger.error(f"MITM detection error: {e}")
                await asyncio.sleep(60)
    
    async def detect_mitm_attack(self, domain: str):
        """Detect potential MITM attacks through multiple validation paths"""
        try:
            # Get certificates from multiple network paths
            cert_results = []
            
            # Method 1: Direct SSL connection
            cert1 = await self.get_certificate_info(domain)
            if cert1:
                cert_results.append(cert1)
            
            # Method 2: Through different DNS servers (if implemented)
            # This would use different DNS resolvers to detect DNS-based MITM
            
            # Method 3: Through VPN/proxy (if available)
            # This would check certificate consistency across different network paths
            
            # Analyze results for inconsistencies
            if len(cert_results) > 1:
                fingerprints = set(cert.fingerprint for cert in cert_results)
                
                if len(fingerprints) > 1:
                    # Different certificates from different paths - potential MITM
                    await self.create_alert(
                        "potential_mitm_attack",
                        "critical",
                        domain,
                        f"Certificate inconsistency detected: {len(fingerprints)} different certificates"
                    )
                    
                    # Temporarily block domain
                    await self.block_domain_temporarily(domain)
            
        except Exception as e:
            logger.error(f"MITM detection failed for {domain}: {e}")
    
    async def security_headers_monitoring(self):
        """Monitor security headers on responses"""
        while self.monitoring_active:
            try:
                for domain in self.config["monitored_domains"]:
                    await self.check_security_headers(domain)
                
                await asyncio.sleep(self.config["monitoring_interval"] * 2)  # Less frequent
                
            except Exception as e:
                logger.error(f"Security headers monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def check_security_headers(self, domain: str):
        """Check security headers on HTTP responses"""
        try:
            url = f"https://{domain}/"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    headers = response.headers
                    
                    # Check required security headers
                    for header_name, expected_value in self.config["security_headers"].items():
                        if header_name not in headers:
                            await self.create_alert(
                                "missing_security_header",
                                "medium",
                                domain,
                                f"Missing security header: {header_name}"
                            )
                        else:
                            # Validate header value strength
                            actual_value = headers[header_name]
                            if not self.validate_security_header_strength(header_name, actual_value):
                                await self.create_alert(
                                    "weak_security_header",
                                    "medium",
                                    domain,
                                    f"Weak {header_name} header: {actual_value}"
                                )
                    
                    # Check for unsafe CSP policies
                    if "Content-Security-Policy" in headers:
                        csp = headers["Content-Security-Policy"]
                        if "'unsafe-eval'" in csp or "'unsafe-inline'" in csp:
                            await self.create_alert(
                                "unsafe_csp_policy",
                                "high",
                                domain,
                                f"Unsafe CSP directives detected: {csp}"
                            )
        
        except Exception as e:
            logger.error(f"Security headers check failed for {domain}: {e}")
    
    def validate_security_header_strength(self, header_name: str, value: str) -> bool:
        """Validate strength of security header values"""
        if header_name == "Strict-Transport-Security":
            # Check for minimum max-age and includeSubDomains
            return "max-age=" in value and "includeSubDomains" in value and \
                   self.extract_max_age(value) >= 31536000
        
        elif header_name == "X-Content-Type-Options":
            return value.lower() == "nosniff"
        
        elif header_name == "X-Frame-Options":
            return value.upper() in ["DENY", "SAMEORIGIN"]
        
        elif header_name == "X-XSS-Protection":
            return "1" in value and "mode=block" in value
        
        return True
    
    def extract_max_age(self, hsts_header: str) -> int:
        """Extract max-age value from HSTS header"""
        import re
        match = re.search(r'max-age=(\d+)', hsts_header)
        return int(match.group(1)) if match else 0
    
    async def certificate_transparency_monitoring(self):
        """Monitor Certificate Transparency logs for new certificates"""
        while self.monitoring_active:
            try:
                for domain in self.config["monitored_domains"]:
                    await self.monitor_ct_logs_for_domain(domain)
                
                await asyncio.sleep(self.config["monitoring_interval"] * 3)  # Less frequent
                
            except Exception as e:
                logger.error(f"CT monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def monitor_ct_logs_for_domain(self, domain: str):
        """Monitor CT logs for unauthorized certificates"""
        try:
            # This would implement monitoring of CT logs for new certificates
            # that might indicate unauthorized certificate issuance
            
            for ct_log_url in self.config["certificate_transparency_logs"]:
                # Query for recent certificates for the domain
                # This is a simplified implementation
                pass
                
        except Exception as e:
            logger.error(f"CT log monitoring failed for {domain}: {e}")
    
    async def create_alert(self, alert_type: str, severity: str, domain: str, details: str):
        """Create and process security alert"""
        alert = SecurityAlert(
            alert_id=hashlib.md5(f"{alert_type}-{domain}-{time.time()}".encode()).hexdigest(),
            alert_type=alert_type,
            severity=severity,
            domain=domain,
            details=details,
            timestamp=datetime.now()
        )
        
        self.alerts.append(alert)
        
        # Log alert
        log_level = logging.CRITICAL if severity == "critical" else \
                   logging.ERROR if severity == "high" else \
                   logging.WARNING if severity == "medium" else logging.INFO
        
        logger.log(log_level, f"🚨 SECURITY ALERT [{severity.upper()}]: {alert_type} for {domain} - {details}")
        
        # Process alert based on severity
        if severity == "critical":
            await self.handle_critical_alert(alert)
        
        # Save alerts to file
        await self.save_alerts()
    
    async def handle_critical_alert(self, alert: SecurityAlert):
        """Handle critical security alerts"""
        logger.critical(f"🔥 CRITICAL SECURITY ALERT: {alert.alert_type} for {alert.domain}")
        
        # For critical alerts, implement immediate response
        if alert.alert_type in ["potential_mitm_attack", "certificate_changed"]:
            await self.block_domain_temporarily(alert.domain)
            
        # Send notifications (would implement webhook/email notifications)
        await self.send_alert_notification(alert)
    
    async def block_domain_temporarily(self, domain: str):
        """Temporarily block connections to potentially compromised domain"""
        self.blocked_domains.add(domain)
        logger.error(f"🚫 DOMAIN TEMPORARILY BLOCKED: {domain} due to security concerns")
        
        # Schedule unblock after investigation period (e.g., 1 hour)
        asyncio.create_task(self.schedule_domain_unblock(domain, 3600))
    
    async def schedule_domain_unblock(self, domain: str, delay_seconds: int):
        """Schedule domain unblock after specified delay"""
        await asyncio.sleep(delay_seconds)
        if domain in self.blocked_domains:
            self.blocked_domains.remove(domain)
            logger.info(f"✅ DOMAIN UNBLOCKED: {domain} after security review period")
    
    async def send_alert_notification(self, alert: SecurityAlert):
        """Send alert notifications (implement webhook/email)"""
        try:
            # This would implement actual notification delivery
            notification_data = {
                "alert_id": alert.alert_id,
                "type": alert.alert_type,
                "severity": alert.severity,
                "domain": alert.domain,
                "details": alert.details,
                "timestamp": alert.timestamp.isoformat()
            }
            
            # Log notification (would actually send to webhook/email)
            logger.info(f"📧 Alert notification prepared: {json.dumps(notification_data, indent=2)}")
            
        except Exception as e:
            logger.error(f"Failed to send alert notification: {e}")
    
    async def save_alerts(self):
        """Save alerts to persistent storage"""
        try:
            alerts_data = [alert.to_dict() for alert in self.alerts[-100:]]  # Keep last 100
            
            with open("security_alerts.json", "w") as f:
                json.dump(alerts_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to save alerts: {e}")
    
    def get_security_status(self) -> Dict:
        """Get current security monitoring status"""
        recent_alerts = [alert for alert in self.alerts 
                        if alert.timestamp > datetime.now() - timedelta(hours=24)]
        
        critical_alerts = [alert for alert in recent_alerts if alert.severity == "critical"]
        
        return {
            "monitoring_active": self.monitoring_active,
            "monitored_domains": self.config["monitored_domains"],
            "total_alerts": len(self.alerts),
            "recent_alerts_24h": len(recent_alerts),
            "critical_alerts_24h": len(critical_alerts),
            "blocked_domains": list(self.blocked_domains),
            "certificate_cache_size": len(self.certificate_cache),
            "last_check": datetime.now().isoformat()
        }
    
    async def generate_security_report(self) -> str:
        """Generate comprehensive security report"""
        status = self.get_security_status()
        
        report = f"""
🛡️  OMEGA Security Monitoring Report
=====================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SYSTEM STATUS
-------------
Monitoring Active: {'✅' if status['monitoring_active'] else '❌'}
Monitored Domains: {len(status['monitored_domains'])}
Blocked Domains: {len(status['blocked_domains'])}

ALERT SUMMARY (Last 24 hours)
------------------------------
Total Alerts: {status['recent_alerts_24h']}
Critical Alerts: {status['critical_alerts_24h']}

MONITORED DOMAINS
-----------------
"""
        
        for domain in self.config["monitored_domains"]:
            if domain in self.certificate_cache:
                cert = self.certificate_cache[domain]
                days_until_expiry = (cert.valid_until - datetime.now()).days
                status_icon = "🔒" if days_until_expiry > 30 else "⚠️" if days_until_expiry > 7 else "🚨"
                
                report += f"{status_icon} {domain}\n"
                report += f"   Certificate: {cert.fingerprint[:16]}...\n"
                report += f"   Expires: {cert.valid_until.strftime('%Y-%m-%d')} ({days_until_expiry} days)\n"
                report += f"   Issuer: {cert.issuer}\n\n"
        
        if status['blocked_domains']:
            report += "🚫 BLOCKED DOMAINS\n"
            report += "-" * 17 + "\n"
            for domain in status['blocked_domains']:
                report += f"❌ {domain} (Security concern)\n"
        
        return report

async def main():
    """Main function to run security monitoring system"""
    monitor = SecurityMonitoringSystem()
    
    try:
        # Start monitoring
        await monitor.start_monitoring()
        
    except KeyboardInterrupt:
        logger.info("🛑 Security monitoring stopped by user")
    except Exception as e:
        logger.error(f"Security monitoring system error: {e}")
    finally:
        monitor.monitoring_active = False
        
        # Generate final report
        report = await monitor.generate_security_report()
        logger.info(f"Final Security Report:\n{report}")

if __name__ == "__main__":
    asyncio.run(main())