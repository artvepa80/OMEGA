#!/usr/bin/env python3
"""
🔐 SSL Certificate Management System for OMEGA Pro AI
Handles certificate generation, rotation, and monitoring for Akash deployments
"""

import click
import subprocess
import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging
import hashlib
import requests
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SSLCertificateManager:
    """SSL Certificate Management System"""
    
    def __init__(self, ssl_dir: str = "./ssl"):
        self.ssl_dir = Path(ssl_dir)
        self.ssl_dir.mkdir(exist_ok=True)
        self.cert_path = self.ssl_dir / "cert.pem"
        self.key_path = self.ssl_dir / "key.pem"
        self.bundle_path = self.ssl_dir / "bundle.pem"
        self.csr_path = self.ssl_dir / "request.csr"
        self.config_path = self.ssl_dir / "ssl_config.json"
    
    def generate_self_signed_certificate(self, 
                                       domain: str, 
                                       email: str,
                                       validity_days: int = 365) -> bool:
        """Generate self-signed SSL certificate"""
        
        try:
            click.echo(f"🔐 Generating self-signed certificate for {domain}")
            
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Create certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "OMEGA Pro AI"),
                x509.NameAttribute(NameOID.COMMON_NAME, domain),
                x509.NameAttribute(NameOID.EMAIL_ADDRESS, email),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=validity_days)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(domain),
                    x509.DNSName(f"*.{domain}"),
                ]),
                critical=False,
            ).add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    key_cert_sign=True,
                    key_agreement=False,
                    content_commitment=False,
                    data_encipherment=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False
                ),
                critical=True,
            ).add_extension(
                x509.ExtendedKeyUsage([
                    x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
                    x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
                ]),
                critical=True,
            ).sign(private_key, hashes.SHA256())
            
            # Write private key
            with open(self.key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Write certificate
            with open(self.cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            # Create bundle
            self._create_certificate_bundle()
            
            # Save configuration
            config = {
                'domain': domain,
                'email': email,
                'type': 'self_signed',
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(days=validity_days)).isoformat(),
                'validity_days': validity_days
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Set secure permissions
            os.chmod(self.key_path, 0o600)
            os.chmod(self.cert_path, 0o644)
            
            click.echo("✅ Self-signed certificate generated successfully")
            return True
            
        except Exception as e:
            click.echo(f"❌ Certificate generation failed: {e}")
            return False
    
    def generate_letsencrypt_certificate(self, 
                                       domain: str, 
                                       email: str,
                                       staging: bool = False) -> bool:
        """Generate Let's Encrypt certificate using certbot with production optimizations"""
        
        try:
            click.echo(f"🔐 Generating Let's Encrypt {'PRODUCTION' if not staging else 'STAGING'} certificate for {domain}")
            
            # Check if certbot is available
            result = subprocess.run(['which', 'certbot'], capture_output=True)
            if result.returncode != 0:
                click.echo("❌ Certbot not found. Installing...")
                # Try to install certbot
                install_result = subprocess.run(['apt-get', 'update', '&&', 'apt-get', 'install', '-y', 'certbot'], 
                                              capture_output=True, text=True, shell=True)
                if install_result.returncode != 0:
                    click.echo("❌ Failed to install certbot automatically")
                    return False
            
            # Ensure port 80 is available for standalone challenge
            click.echo("🔍 Checking port 80 availability...")
            port_check = subprocess.run(['lsof', '-i', ':80'], capture_output=True)
            if port_check.returncode == 0:
                click.echo("⚠️ Port 80 is in use. Attempting to stop services...")
                subprocess.run(['systemctl', 'stop', 'nginx'], capture_output=True)
                subprocess.run(['systemctl', 'stop', 'apache2'], capture_output=True)
            
            # Build certbot command with production optimizations
            cmd = [
                'certbot', 'certonly',
                '--standalone',
                '--preferred-challenges', 'http',
                '--email', email,
                '--agree-tos',
                '--no-eff-email',
                '--expand',  # Allow expanding to cover additional domains
                '--domains', domain,
                '--rsa-key-size', '4096',  # Use 4096-bit RSA keys for production
                '--must-staple',  # Enable OCSP Must-Staple
                '--non-interactive'
            ]
            
            if staging:
                cmd.extend(['--staging'])
            else:
                cmd.extend(['--force-renewal'])  # Force renewal for production
            
            click.echo(f"🚀 Executing: {' '.join(cmd)}")
            
            # Run certbot with timeout
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Copy certificates to our SSL directory
                letsencrypt_path = Path(f'/etc/letsencrypt/live/{domain}')
                
                if letsencrypt_path.exists():
                    # Copy certificate files with proper permissions
                    subprocess.run(['cp', str(letsencrypt_path / 'fullchain.pem'), str(self.cert_path)])
                    subprocess.run(['cp', str(letsencrypt_path / 'privkey.pem'), str(self.key_path)])
                    subprocess.run(['cp', str(letsencrypt_path / 'chain.pem'), str(self.ssl_dir / 'chain.pem')])
                    
                    # Set secure permissions
                    os.chmod(self.key_path, 0o600)
                    os.chmod(self.cert_path, 0o644)
                    
                    # Create enhanced certificate bundle
                    self._create_certificate_bundle()
                    
                    # Extract certificate fingerprints for pinning
                    cert_fingerprints = self._extract_certificate_fingerprints()
                    
                    # Save enhanced configuration
                    config = {
                        'domain': domain,
                        'email': email,
                        'type': 'letsencrypt',
                        'staging': staging,
                        'environment': 'staging' if staging else 'production',
                        'created_at': datetime.now().isoformat(),
                        'letsencrypt_path': str(letsencrypt_path),
                        'cert_fingerprints': cert_fingerprints,
                        'auto_renewal': True,
                        'renewal_days_before': 30,
                        'ocsp_stapling': True,
                        'key_size': 4096
                    }
                    
                    with open(self.config_path, 'w') as f:
                        json.dump(config, f, indent=2)
                    
                    # Setup auto-renewal cron job
                    self._setup_auto_renewal(domain, email)
                    
                    click.echo("✅ Let's Encrypt certificate generated successfully")
                    click.echo(f"📋 Certificate fingerprints: {cert_fingerprints}")
                    
                    # Restart web services
                    subprocess.run(['systemctl', 'start', 'nginx'], capture_output=True)
                    
                    return True
            else:
                click.echo(f"❌ Certbot failed:")
                click.echo(f"   STDOUT: {result.stdout}")
                click.echo(f"   STDERR: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            click.echo("❌ Certbot operation timed out")
            return False
        except Exception as e:
            click.echo(f"❌ Let's Encrypt certificate generation failed: {e}")
            return False
    
    def _create_certificate_bundle(self):
        """Create certificate bundle for deployment"""
        with open(self.bundle_path, 'w') as bundle:
            # Add certificate
            with open(self.cert_path, 'r') as cert:
                bundle.write(cert.read())
            # Add private key
            with open(self.key_path, 'r') as key:
                bundle.write(key.read())
    
    def _extract_certificate_fingerprints(self) -> Dict[str, str]:
        """Extract certificate fingerprints for pinning"""
        fingerprints = {}
        
        try:
            if self.cert_path.exists():
                # Load certificate
                with open(self.cert_path, 'rb') as f:
                    cert_data = f.read()
                
                cert = x509.load_pem_x509_certificate(cert_data)
                
                # SHA256 fingerprint of certificate
                cert_fingerprint = hashlib.sha256(cert_data).hexdigest()
                fingerprints['certificate_sha256'] = cert_fingerprint
                
                # SHA256 fingerprint of public key
                public_key = cert.public_key()
                public_key_der = public_key.public_key_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                public_key_fingerprint = hashlib.sha256(public_key_der).hexdigest()
                fingerprints['public_key_sha256'] = public_key_fingerprint
                
                # SPKI fingerprint (Subject Public Key Info)
                spki_fingerprint = hashlib.sha256(
                    cert.public_key().public_key_bytes(
                        encoding=serialization.Encoding.DER,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    )
                ).hexdigest()
                fingerprints['spki_sha256'] = spki_fingerprint
                
        except Exception as e:
            logger.error(f"Failed to extract certificate fingerprints: {e}")
        
        return fingerprints
    
    def _setup_auto_renewal(self, domain: str, email: str):
        """Setup automatic certificate renewal via cron"""
        
        try:
            # Create renewal script
            renewal_script = self.ssl_dir / "renew_certificate.sh"
            script_content = f"""#!/bin/bash
# Auto-renewal script for {domain}
cd "{os.getcwd()}"
python3 {__file__} renew --domain {domain} --email {email}
systemctl reload nginx
"""
            
            with open(renewal_script, 'w') as f:
                f.write(script_content)
            
            os.chmod(renewal_script, 0o755)
            
            # Add cron job for renewal (check twice daily)
            cron_command = f"0 2,14 * * * {renewal_script} >> /var/log/ssl_renewal.log 2>&1"
            
            # Add to crontab
            subprocess.run([
                'bash', '-c', 
                f'(crontab -l 2>/dev/null | grep -v "{domain}"; echo "{cron_command}") | crontab -'
            ], capture_output=True)
            
            click.echo(f"✅ Auto-renewal configured for {domain}")
            
        except Exception as e:
            click.echo(f"⚠️ Failed to setup auto-renewal: {e}")
    
    def setup_ocsp_stapling(self, domain: str) -> bool:
        """Setup OCSP stapling configuration"""
        
        try:
            # Create OCSP response file
            ocsp_response_path = self.ssl_dir / "ocsp_response"
            
            # Get OCSP responder URL
            with open(self.cert_path, 'rb') as f:
                cert_data = f.read()
            
            cert = x509.load_pem_x509_certificate(cert_data)
            
            # Extract OCSP URL from certificate
            ocsp_url = None
            try:
                aia_ext = cert.extensions.get_extension_for_oid(x509.ExtensionOID.AUTHORITY_INFORMATION_ACCESS)
                for access_description in aia_ext.value:
                    if access_description.access_method == x509.AuthorityInformationAccessOID.OCSP:
                        ocsp_url = access_description.access_location.value
                        break
            except x509.ExtensionNotFound:
                pass
            
            if ocsp_url:
                # Fetch OCSP response
                cmd = [
                    'openssl', 'ocsp',
                    '-issuer', str(self.ssl_dir / 'chain.pem'),
                    '-cert', str(self.cert_path),
                    '-url', ocsp_url,
                    '-respout', str(ocsp_response_path)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    click.echo(f"✅ OCSP stapling configured for {domain}")
                    return True
                else:
                    click.echo(f"⚠️ OCSP stapling failed: {result.stderr}")
                    
        except Exception as e:
            click.echo(f"⚠️ OCSP stapling setup failed: {e}")
        
        return False
    
    def check_certificate_validity(self) -> Dict[str, Any]:
        """Check certificate validity and expiration"""
        
        if not self.cert_path.exists():
            return {'valid': False, 'error': 'Certificate file not found'}
        
        try:
            # Load certificate
            with open(self.cert_path, 'rb') as f:
                cert_data = f.read()
            
            cert = x509.load_pem_x509_certificate(cert_data)
            
            # Get certificate info
            subject = cert.subject
            issuer = cert.issuer
            not_before = cert.not_valid_before
            not_after = cert.not_valid_after
            
            # Check if still valid
            now = datetime.utcnow()
            is_valid = not_before <= now <= not_after
            days_until_expiry = (not_after - now).days
            
            # Get domain from certificate
            common_name = None
            for attribute in subject:
                if attribute.oid == NameOID.COMMON_NAME:
                    common_name = attribute.value
                    break
            
            return {
                'valid': is_valid,
                'domain': common_name,
                'issuer': str(issuer),
                'not_before': not_before.isoformat(),
                'not_after': not_after.isoformat(),
                'days_until_expiry': days_until_expiry,
                'needs_renewal': days_until_expiry < 30
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def renew_certificate(self, domain: str, email: str) -> bool:
        """Renew SSL certificate"""
        
        if not self.config_path.exists():
            click.echo("❌ SSL configuration not found")
            return False
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            cert_type = config.get('type', 'self_signed')
            
            if cert_type == 'letsencrypt':
                return self._renew_letsencrypt_certificate(domain)
            else:
                return self.generate_self_signed_certificate(domain, email)
                
        except Exception as e:
            click.echo(f"❌ Certificate renewal failed: {e}")
            return False
    
    def _renew_letsencrypt_certificate(self, domain: str) -> bool:
        """Renew Let's Encrypt certificate"""
        
        try:
            cmd = ['certbot', 'renew', '--domain', domain]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Copy renewed certificates
                letsencrypt_path = Path(f'/etc/letsencrypt/live/{domain}')
                
                if letsencrypt_path.exists():
                    subprocess.run([
                        'cp', str(letsencrypt_path / 'fullchain.pem'), str(self.cert_path)
                    ])
                    subprocess.run([
                        'cp', str(letsencrypt_path / 'privkey.pem'), str(self.key_path)
                    ])
                    
                    self._create_certificate_bundle()
                    
                    click.echo("✅ Let's Encrypt certificate renewed successfully")
                    return True
            else:
                click.echo(f"❌ Certificate renewal failed: {result.stderr}")
                return False
                
        except Exception as e:
            click.echo(f"❌ Let's Encrypt renewal failed: {e}")
            return False
    
    def test_ssl_connection(self, domain: str, port: int = 443) -> Dict[str, Any]:
        """Test SSL connection to domain"""
        
        try:
            import ssl
            import socket
            
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect and get certificate
            with socket.create_connection((domain, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    return {
                        'connected': True,
                        'subject': dict(x[0] for x in cert['subject']),
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'version': cert['version'],
                        'serialNumber': cert['serialNumber'],
                        'notBefore': cert['notBefore'],
                        'notAfter': cert['notAfter'],
                        'subjectAltName': cert.get('subjectAltName', [])
                    }
                    
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }

@click.group()
def ssl_cli():
    """SSL Certificate Management CLI"""
    pass

@ssl_cli.command()
@click.option('--domain', required=True, help='Domain name for certificate')
@click.option('--email', required=True, help='Email for certificate')
@click.option('--type', type=click.Choice(['self-signed', 'letsencrypt']), 
              default='letsencrypt', help='Certificate type (default: letsencrypt)')
@click.option('--staging', is_flag=True, help='Use Let\'s Encrypt staging (for testing)')
@click.option('--validity-days', default=365, help='Validity days for self-signed certificate')
@click.option('--production', is_flag=True, help='Force production Let\'s Encrypt certificate')
def generate(domain, email, type, staging, validity_days, production):
    """Generate SSL certificate with production-grade configuration"""
    
    manager = SSLCertificateManager()
    
    # Override staging if production flag is set
    if production:
        staging = False
        type = 'letsencrypt'
    
    if type == 'letsencrypt':
        success = manager.generate_letsencrypt_certificate(domain, email, staging)
        
        if success and not staging:
            # Setup OCSP stapling for production certificates
            click.echo("🔧 Setting up OCSP stapling...")
            manager.setup_ocsp_stapling(domain)
    else:
        success = manager.generate_self_signed_certificate(domain, email, validity_days)
    
    if success:
        click.echo(f"✅ SSL certificate generated for {domain}")
        
        # Show certificate info
        cert_info = manager.check_certificate_validity()
        if cert_info['valid']:
            click.echo(f"   Valid until: {cert_info['not_after']}")
            click.echo(f"   Days until expiry: {cert_info['days_until_expiry']}")
            
            # Show fingerprints for certificate pinning
            if manager.config_path.exists():
                with open(manager.config_path, 'r') as f:
                    config = json.load(f)
                    fingerprints = config.get('cert_fingerprints', {})
                    if fingerprints:
                        click.echo("📋 Certificate Fingerprints for Pinning:")
                        for fp_type, fp_value in fingerprints.items():
                            click.echo(f"   {fp_type}: {fp_value}")
    else:
        click.echo(f"❌ SSL certificate generation failed for {domain}")

@ssl_cli.command()
def status():
    """Check certificate status"""
    
    manager = SSLCertificateManager()
    cert_info = manager.check_certificate_validity()
    
    if cert_info['valid']:
        click.echo("✅ SSL Certificate Status: VALID")
        click.echo(f"   Domain: {cert_info['domain']}")
        click.echo(f"   Issuer: {cert_info['issuer']}")
        click.echo(f"   Valid until: {cert_info['not_after']}")
        click.echo(f"   Days until expiry: {cert_info['days_until_expiry']}")
        
        if cert_info['needs_renewal']:
            click.echo("⚠️ Certificate expires within 30 days - renewal recommended")
    else:
        click.echo("❌ SSL Certificate Status: INVALID")
        click.echo(f"   Error: {cert_info.get('error', 'Unknown error')}")

@ssl_cli.command()
@click.option('--domain', required=True, help='Domain name')
@click.option('--email', required=True, help='Email for certificate')
def renew(domain, email):
    """Renew SSL certificate"""
    
    manager = SSLCertificateManager()
    
    if manager.renew_certificate(domain, email):
        click.echo("✅ SSL certificate renewed successfully")
        
        # Show updated certificate info
        cert_info = manager.check_certificate_validity()
        if cert_info['valid']:
            click.echo(f"   New expiry date: {cert_info['not_after']}")
            click.echo(f"   Days until expiry: {cert_info['days_until_expiry']}")
    else:
        click.echo("❌ SSL certificate renewal failed")

@ssl_cli.command()
@click.option('--domain', required=True, help='Domain to test')
@click.option('--port', default=443, help='Port to test')
def test(domain, port):
    """Test SSL connection to domain"""
    
    manager = SSLCertificateManager()
    result = manager.test_ssl_connection(domain, port)
    
    if result['connected']:
        click.echo(f"✅ SSL connection to {domain}:{port} successful")
        click.echo(f"   Subject: {result['subject']}")
        click.echo(f"   Issuer: {result['issuer']}")
        click.echo(f"   Valid until: {result['notAfter']}")
    else:
        click.echo(f"❌ SSL connection to {domain}:{port} failed")
        click.echo(f"   Error: {result['error']}")

@ssl_cli.command()
@click.option('--interval', default=3600, help='Check interval in seconds (default: 1 hour)')
@click.option('--alert-days', default=30, help='Days before expiry to send alerts')
def monitor(interval, alert_days):
    """Monitor certificate expiration and auto-renew with enhanced alerting"""
    
    click.echo("🔍 Starting enhanced SSL certificate monitoring...")
    click.echo(f"   Check interval: {interval} seconds")
    click.echo(f"   Alert threshold: {alert_days} days")
    
    manager = SSLCertificateManager()
    
    while True:
        try:
            cert_info = manager.check_certificate_validity()
            
            if cert_info['valid']:
                days_left = cert_info['days_until_expiry']
                timestamp = datetime.now().isoformat()
                
                if days_left <= 1:
                    click.echo(f"🚨 CRITICAL [{timestamp}]: Certificate expires TODAY!")
                    # Immediate renewal attempt
                    if manager.config_path.exists():
                        with open(manager.config_path, 'r') as f:
                            config = json.load(f)
                        
                        domain = config.get('domain')
                        email = config.get('email')
                        
                        if domain and email:
                            click.echo("🚨 EMERGENCY RENEWAL ATTEMPT...")
                            if manager.renew_certificate(domain, email):
                                click.echo("✅ Emergency certificate renewal successful")
                            else:
                                click.echo("❌ EMERGENCY RENEWAL FAILED - MANUAL INTERVENTION REQUIRED")
                
                elif days_left <= 7:
                    click.echo(f"🚨 URGENT [{timestamp}]: Certificate expires in {days_left} days!")
                    
                    # Auto-renew if configuration exists
                    if manager.config_path.exists():
                        with open(manager.config_path, 'r') as f:
                            config = json.load(f)
                        
                        domain = config.get('domain')
                        email = config.get('email')
                        
                        if domain and email:
                            click.echo("🔄 Auto-renewing certificate...")
                            if manager.renew_certificate(domain, email):
                                click.echo("✅ Certificate auto-renewed successfully")
                            else:
                                click.echo("❌ Auto-renewal failed")
                
                elif days_left <= alert_days:
                    click.echo(f"⚠️ [{timestamp}]: Certificate expires in {days_left} days")
                else:
                    if interval >= 3600:  # Only log status hourly for long intervals
                        click.echo(f"✅ [{timestamp}]: Certificate valid for {days_left} days")
            else:
                click.echo(f"❌ [{datetime.now().isoformat()}]: Certificate is invalid or expired")
                click.echo(f"   Error: {cert_info.get('error', 'Unknown error')}")
            
            # Sleep for specified interval
            time.sleep(interval)
            
        except KeyboardInterrupt:
            click.echo("\n👋 SSL monitoring stopped")
            break
        except Exception as e:
            click.echo(f"❌ [{datetime.now().isoformat()}]: Monitoring error: {e}")
            time.sleep(min(interval, 3600))  # Sleep up to 1 hour on error

@ssl_cli.command()
@click.option('--domain', default='omega-api.akash.network', help='Domain to deploy to')
@click.option('--email', default='admin@omega-pro-ai.com', help='Admin email')
def deploy_production():
    """Deploy production Let's Encrypt certificates for OMEGA"""
    
    click.echo("🚀 Deploying OMEGA Production SSL Certificates")
    click.echo("=" * 60)
    
    manager = SSLCertificateManager()
    
    # Generate production Let's Encrypt certificate
    click.echo(f"🔐 Generating production certificate for {domain}")
    
    success = manager.generate_letsencrypt_certificate(domain, email, staging=False)
    
    if success:
        click.echo("\n✅ Production certificate deployed successfully!")
        
        # Show certificate details
        cert_info = manager.check_certificate_validity()
        if cert_info['valid']:
            click.echo(f"\n📋 Certificate Details:")
            click.echo(f"   Domain: {cert_info['domain']}")
            click.echo(f"   Issuer: {cert_info['issuer']}")
            click.echo(f"   Valid until: {cert_info['not_after']}")
            click.echo(f"   Days remaining: {cert_info['days_until_expiry']}")
        
        # Show fingerprints for iOS certificate pinning
        if manager.config_path.exists():
            with open(manager.config_path, 'r') as f:
                config = json.load(f)
                fingerprints = config.get('cert_fingerprints', {})
                
                if fingerprints:
                    click.echo(f"\n🔗 Certificate Fingerprints (for iOS pinning):")
                    click.echo("   Add these to SSLCertificatePinningManager.swift:")
                    for fp_type, fp_value in fingerprints.items():
                        click.echo(f"   {fp_type}: {fp_value}")
        
        # Setup OCSP stapling
        click.echo(f"\n🔧 Configuring OCSP stapling...")
        if manager.setup_ocsp_stapling(domain):
            click.echo("✅ OCSP stapling configured")
        
        # Test the certificate
        click.echo(f"\n🧪 Testing SSL connection...")
        test_result = manager.test_ssl_connection(domain)
        
        if test_result['connected']:
            click.echo("✅ SSL connection test successful")
            click.echo(f"   Subject: {test_result['subject']}")
            click.echo(f"   Issuer: {test_result['issuer']}")
        else:
            click.echo(f"⚠️ SSL connection test failed: {test_result['error']}")
        
        click.echo(f"\n🎯 Next Steps:")
        click.echo(f"   1. Update nginx configuration to use new certificates")
        click.echo(f"   2. Update iOS app certificate pinning with new fingerprints")
        click.echo(f"   3. Test API endpoints with new certificates")
        click.echo(f"   4. Monitor certificate auto-renewal")
        
    else:
        click.echo("❌ Production certificate deployment failed")
        
    click.echo("=" * 60)

if __name__ == '__main__':
    ssl_cli()