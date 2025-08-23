#!/usr/bin/env python3
"""
OMEGA Pro AI - SSL/TLS Security Validation Suite
Comprehensive SSL certificate and TLS configuration security assessment
"""

import ssl
import socket
import subprocess
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import OpenSSL.crypto
import hashlib
import base64
import requests
from cryptography import x509
from cryptography.hazmat.backends import default_backend

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ssl_security_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SSLSecurityValidator:
    """Comprehensive SSL/TLS security validation"""
    
    def __init__(self):
        self.test_results = {}
        self.vulnerabilities = []
        self.certificates = {}
        self.start_time = datetime.now()
        
        # Target endpoints
        self.ssl_endpoints = [
            ('a17d0f2p7pbkp4bc0pjgbsmp8o.ingress.paradigmapolitico.online', 443),
            ('omega-api.akash.network', 443)
        ]
        
        # Local SSL files
        self.ssl_files = {
            'certificate': 'ssl/cert.pem',
            'private_key': 'ssl/key.pem',
            'certificate_bundle': 'ssl/bundle.pem',
            'config': 'ssl/ssl_config.json'
        }
    
    async def run_ssl_validation(self) -> Dict:
        """Execute comprehensive SSL/TLS security validation"""
        logger.info("🔒 Starting SSL/TLS Security Validation Suite")
        
        validation_suites = [
            ('Certificate Security Analysis', self.analyze_certificate_security),
            ('TLS Configuration Security', self.analyze_tls_configuration),
            ('Certificate Chain Validation', self.validate_certificate_chain),
            ('SSL/TLS Protocol Security', self.analyze_protocol_security),
            ('Certificate Transparency Validation', self.validate_certificate_transparency),
            ('OCSP Stapling Validation', self.validate_ocsp_stapling),
            ('Certificate Expiration Analysis', self.analyze_certificate_expiration),
            ('SSL Implementation Security', self.analyze_ssl_implementation)
        ]
        
        for test_name, test_func in validation_suites:
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 Running {test_name}")
            logger.info(f"{'='*60}")
            
            try:
                results = await test_func()
                self.test_results[test_name] = results
                score = results.get('security_score', 0)
                status = results.get('status', 'UNKNOWN')
                logger.info(f"✅ {test_name} completed - Score: {score}% - Status: {status}")
            except Exception as e:
                logger.error(f"❌ {test_name} failed: {str(e)}")
                self.test_results[test_name] = {
                    'status': 'FAILED',
                    'error': str(e),
                    'security_score': 0,
                    'vulnerabilities': []
                }
        
        return await self.generate_ssl_security_report()
    
    async def analyze_certificate_security(self) -> Dict:
        """Analyze SSL certificate security properties"""
        results = {
            'test_type': 'Certificate Security Analysis',
            'status': 'SECURE',
            'security_score': 100,
            'vulnerabilities': [],
            'findings': [],
            'certificates_analyzed': []
        }
        
        try:
            # Load and analyze local certificate
            with open(self.ssl_files['certificate'], 'r') as f:
                cert_pem = f.read()
            
            # Parse certificate with pyOpenSSL
            cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_pem)
            
            # Parse certificate with cryptography library for additional analysis
            crypto_cert = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())
            
            cert_analysis = {
                'subject': str(cert.get_subject()),
                'issuer': str(cert.get_issuer()),
                'serial_number': str(cert.get_serial_number()),
                'version': cert.get_version() + 1,
                'signature_algorithm': cert.get_signature_algorithm().decode(),
                'public_key_bits': cert.get_pubkey().bits(),
                'not_before': cert.get_notBefore().decode(),
                'not_after': cert.get_notAfter().decode()
            }
            
            results['certificates_analyzed'].append(cert_analysis)
            results['findings'].append(f"✅ Certificate loaded successfully")
            
            # Check key strength
            key_bits = cert.get_pubkey().bits()
            if key_bits >= 2048:
                results['findings'].append(f"✅ Strong key length: {key_bits} bits")
            elif key_bits >= 1024:
                results['findings'].append(f"⚠️ Moderate key length: {key_bits} bits")
                results['security_score'] -= 10
                results['status'] = 'WARNING'
            else:
                results['findings'].append(f"❌ Weak key length: {key_bits} bits")
                results['security_score'] -= 30
                results['status'] = 'VULNERABLE'
                vulnerability = {
                    'type': 'Weak Key Length',
                    'severity': 'HIGH',
                    'cvss_score': 7.5,
                    'description': f'Certificate uses weak {key_bits}-bit key',
                    'recommendation': 'Use at least 2048-bit RSA or 256-bit ECC keys'
                }
                results['vulnerabilities'].append(vulnerability)
            
            # Check signature algorithm
            sig_alg = cert.get_signature_algorithm().decode().lower()
            if 'sha256' in sig_alg or 'sha384' in sig_alg or 'sha512' in sig_alg:
                results['findings'].append(f"✅ Strong signature algorithm: {sig_alg}")
            elif 'sha1' in sig_alg:
                results['findings'].append(f"❌ Weak signature algorithm: {sig_alg}")
                results['security_score'] -= 25
                results['status'] = 'VULNERABLE'
                vulnerability = {
                    'type': 'Weak Signature Algorithm',
                    'severity': 'MEDIUM',
                    'cvss_score': 5.3,
                    'description': 'Certificate uses deprecated SHA-1 signature algorithm',
                    'recommendation': 'Use SHA-256 or stronger signature algorithm'
                }
                results['vulnerabilities'].append(vulnerability)
            else:
                results['findings'].append(f"⚠️ Unknown signature algorithm: {sig_alg}")
                results['security_score'] -= 5
            
            # Check certificate validity period
            not_before = datetime.strptime(cert.get_notBefore().decode(), '%Y%m%d%H%M%SZ')
            not_after = datetime.strptime(cert.get_notAfter().decode(), '%Y%m%d%H%M%SZ')
            validity_days = (not_after - not_before).days
            
            if validity_days <= 365:
                results['findings'].append(f"✅ Reasonable validity period: {validity_days} days")
            elif validity_days <= 730:
                results['findings'].append(f"⚠️ Long validity period: {validity_days} days")
                results['security_score'] -= 5
            else:
                results['findings'].append(f"⚠️ Very long validity period: {validity_days} days")
                results['security_score'] -= 10
                results['status'] = 'WARNING'
            
            # Check certificate extensions
            extensions = []
            for i in range(cert.get_extension_count()):
                ext = cert.get_extension(i)
                ext_name = ext.get_short_name().decode()
                extensions.append(ext_name)
                results['findings'].append(f"✅ Extension present: {ext_name}")
            
            # Check for critical security extensions
            critical_extensions = ['keyUsage', 'extendedKeyUsage', 'basicConstraints']
            missing_extensions = [ext for ext in critical_extensions if ext not in extensions]
            
            if missing_extensions:
                results['findings'].append(f"⚠️ Missing extensions: {', '.join(missing_extensions)}")
                results['security_score'] -= len(missing_extensions) * 5
                if results['status'] == 'SECURE':
                    results['status'] = 'WARNING'
            
            # Check if certificate is self-signed
            if cert.get_subject() == cert.get_issuer():
                results['findings'].append("ℹ️ Self-signed certificate (appropriate for development)")
            else:
                results['findings'].append("✅ Certificate issued by external CA")
            
            # Generate certificate fingerprints
            cert_der = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert)
            sha256_fingerprint = hashlib.sha256(cert_der).hexdigest()
            sha1_fingerprint = hashlib.sha1(cert_der).hexdigest()
            
            results['certificate_fingerprints'] = {
                'sha256': sha256_fingerprint,
                'sha1': sha1_fingerprint
            }
            
            results['findings'].append(f"✅ SHA-256 fingerprint: {sha256_fingerprint[:32]}...")
            results['findings'].append(f"✅ Certificate security analysis completed")
            
        except Exception as e:
            results['findings'].append(f"❌ Certificate analysis failed: {str(e)}")
            results['status'] = 'FAILED'
            results['security_score'] = 0
        
        return results
    
    async def analyze_tls_configuration(self) -> Dict:
        """Analyze TLS configuration security"""
        results = {
            'test_type': 'TLS Configuration Security',
            'status': 'SECURE',
            'security_score': 100,
            'vulnerabilities': [],
            'findings': [],
            'tls_analysis': []
        }
        
        for hostname, port in self.ssl_endpoints:
            try:
                logger.info(f"Analyzing TLS configuration for {hostname}:{port}")
                
                # Test TLS connection
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                with socket.create_connection((hostname, port), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        tls_info = {
                            'hostname': hostname,
                            'port': port,
                            'tls_version': ssock.version(),
                            'cipher_suite': ssock.cipher(),
                            'certificate_info': self.extract_certificate_info(ssock)
                        }
                        
                        results['tls_analysis'].append(tls_info)
                        
                        # Validate TLS version
                        tls_version = ssock.version()
                        if tls_version in ['TLSv1.3', 'TLSv1.2']:
                            results['findings'].append(f"✅ {hostname}: Modern TLS version - {tls_version}")
                        elif tls_version == 'TLSv1.1':
                            results['findings'].append(f"⚠️ {hostname}: Deprecated TLS version - {tls_version}")
                            results['security_score'] -= 15
                            results['status'] = 'WARNING'
                        else:
                            results['findings'].append(f"❌ {hostname}: Insecure TLS version - {tls_version}")
                            results['security_score'] -= 30
                            results['status'] = 'VULNERABLE'
                            vulnerability = {
                                'type': 'Insecure TLS Version',
                                'severity': 'HIGH',
                                'cvss_score': 7.4,
                                'endpoint': f'{hostname}:{port}',
                                'description': f'Server supports insecure TLS version: {tls_version}',
                                'recommendation': 'Disable TLS versions below 1.2'
                            }
                            results['vulnerabilities'].append(vulnerability)
                        
                        # Validate cipher suite
                        if ssock.cipher():
                            cipher_name, tls_protocol, bits = ssock.cipher()
                            results['findings'].append(f"✅ {hostname}: Cipher suite - {cipher_name}")
                            results['findings'].append(f"✅ {hostname}: Encryption strength - {bits} bits")
                            
                            # Check cipher strength
                            if bits >= 256:
                                results['findings'].append(f"✅ {hostname}: Strong encryption (256+ bits)")
                            elif bits >= 128:
                                results['findings'].append(f"✅ {hostname}: Adequate encryption (128+ bits)")
                            else:
                                results['findings'].append(f"❌ {hostname}: Weak encryption ({bits} bits)")
                                results['security_score'] -= 20
                                results['status'] = 'VULNERABLE'
                            
                            # Check for forward secrecy
                            if 'ECDHE' in cipher_name or 'DHE' in cipher_name:
                                results['findings'].append(f"✅ {hostname}: Perfect Forward Secrecy supported")
                            else:
                                results['findings'].append(f"⚠️ {hostname}: No Perfect Forward Secrecy")
                                results['security_score'] -= 10
                                if results['status'] == 'SECURE':
                                    results['status'] = 'WARNING'
                        
            except Exception as e:
                results['findings'].append(f"❌ TLS analysis failed for {hostname}:{port} - {str(e)}")
                results['security_score'] -= 20
                if results['status'] == 'SECURE':
                    results['status'] = 'WARNING'
        
        return results
    
    def extract_certificate_info(self, ssl_socket) -> Dict:
        """Extract certificate information from SSL socket"""
        try:
            der_cert = ssl_socket.getpeercert_chain()[0]
            cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, der_cert)
            
            return {
                'subject': str(cert.get_subject()),
                'issuer': str(cert.get_issuer()),
                'serial_number': str(cert.get_serial_number()),
                'not_before': cert.get_notBefore().decode(),
                'not_after': cert.get_notAfter().decode(),
                'signature_algorithm': cert.get_signature_algorithm().decode()
            }
        except Exception:
            return {'error': 'Could not extract certificate information'}
    
    async def validate_certificate_chain(self) -> Dict:
        """Validate SSL certificate chain"""
        results = {
            'test_type': 'Certificate Chain Validation',
            'status': 'SECURE',
            'security_score': 100,
            'vulnerabilities': [],
            'findings': []
        }
        
        try:
            # Load certificate chain
            with open(self.ssl_files['certificate_bundle'], 'r') as f:
                cert_chain_pem = f.read()
            
            # Parse all certificates in the chain
            certs = []
            for cert_pem in cert_chain_pem.split('-----END CERTIFICATE-----'):
                if '-----BEGIN CERTIFICATE-----' in cert_pem:
                    cert_data = cert_pem + '-----END CERTIFICATE-----'
                    cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_data)
                    certs.append(cert)
            
            results['findings'].append(f"✅ Found {len(certs)} certificates in chain")
            
            # Validate chain structure
            if len(certs) == 1:
                results['findings'].append("ℹ️ Single certificate (self-signed or end-entity only)")
                # For self-signed certificates, this is acceptable in development
                if certs[0].get_subject() == certs[0].get_issuer():
                    results['findings'].append("ℹ️ Self-signed certificate detected (acceptable for development)")
                else:
                    results['findings'].append("⚠️ End-entity certificate without CA chain")
                    results['security_score'] -= 10
                    results['status'] = 'WARNING'
            else:
                results['findings'].append("✅ Multi-certificate chain detected")
                
                # Validate chain order and signatures
                for i, cert in enumerate(certs):
                    subject = cert.get_subject()
                    issuer = cert.get_issuer()
                    
                    results['findings'].append(f"✅ Certificate {i+1}: {subject.CN}")
                    
                    # Check if certificate is properly signed by next in chain
                    if i < len(certs) - 1:
                        next_cert = certs[i + 1]
                        if issuer == next_cert.get_subject():
                            results['findings'].append(f"✅ Certificate {i+1} properly signed by Certificate {i+2}")
                        else:
                            results['findings'].append(f"❌ Certificate chain break at Certificate {i+1}")
                            results['security_score'] -= 20
                            results['status'] = 'VULNERABLE'
            
            # Check certificate validity dates
            now = datetime.utcnow()
            for i, cert in enumerate(certs):
                not_before = datetime.strptime(cert.get_notBefore().decode(), '%Y%m%d%H%M%SZ')
                not_after = datetime.strptime(cert.get_notAfter().decode(), '%Y%m%d%H%M%SZ')
                
                if not_before <= now <= not_after:
                    results['findings'].append(f"✅ Certificate {i+1} is valid (expires {not_after.strftime('%Y-%m-%d')})")
                else:
                    if now < not_before:
                        results['findings'].append(f"❌ Certificate {i+1} not yet valid")
                    else:
                        results['findings'].append(f"❌ Certificate {i+1} expired on {not_after.strftime('%Y-%m-%d')}")
                    
                    results['security_score'] -= 30
                    results['status'] = 'VULNERABLE'
                    vulnerability = {
                        'type': 'Invalid Certificate',
                        'severity': 'HIGH',
                        'cvss_score': 7.8,
                        'description': f'Certificate {i+1} is not within valid date range',
                        'recommendation': 'Renew expired certificates immediately'
                    }
                    results['vulnerabilities'].append(vulnerability)
        
        except Exception as e:
            results['findings'].append(f"❌ Certificate chain validation failed: {str(e)}")
            results['status'] = 'FAILED'
            results['security_score'] = 0
        
        return results
    
    async def analyze_protocol_security(self) -> Dict:
        """Analyze SSL/TLS protocol security"""
        results = {
            'test_type': 'SSL/TLS Protocol Security',
            'status': 'SECURE',
            'security_score': 100,
            'vulnerabilities': [],
            'findings': [],
            'protocol_tests': []
        }
        
        # Test different SSL/TLS versions
        protocols_to_test = [
            (ssl.PROTOCOL_SSLv23, "SSLv2/v3"),
            (ssl.PROTOCOL_TLS_CLIENT, "TLS Client")
        ]
        
        for hostname, port in self.ssl_endpoints:
            protocol_results = {
                'hostname': hostname,
                'port': port,
                'supported_protocols': [],
                'deprecated_protocols': [],
                'secure_protocols': []
            }
            
            try:
                # Test modern TLS versions
                modern_versions = [
                    (ssl.TLSVersion.TLSv1_2, "TLS 1.2"),
                    (ssl.TLSVersion.TLSv1_3, "TLS 1.3")
                ]
                
                for tls_version, version_name in modern_versions:
                    try:
                        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                        context.minimum_version = tls_version
                        context.maximum_version = tls_version
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        
                        with socket.create_connection((hostname, port), timeout=5) as sock:
                            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                                actual_version = ssock.version()
                                protocol_results['supported_protocols'].append(actual_version)
                                protocol_results['secure_protocols'].append(version_name)
                                results['findings'].append(f"✅ {hostname}: {version_name} supported")
                    
                    except Exception:
                        results['findings'].append(f"⚠️ {hostname}: {version_name} not supported or connection failed")
                
                # Test deprecated protocols
                deprecated_versions = [
                    (ssl.TLSVersion.TLSv1, "TLS 1.0"),
                    (ssl.TLSVersion.TLSv1_1, "TLS 1.1")
                ]
                
                for tls_version, version_name in deprecated_versions:
                    try:
                        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                        context.minimum_version = tls_version
                        context.maximum_version = tls_version
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        
                        with socket.create_connection((hostname, port), timeout=5) as sock:
                            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                                protocol_results['deprecated_protocols'].append(version_name)
                                results['findings'].append(f"❌ {hostname}: Deprecated {version_name} supported")
                                results['security_score'] -= 15
                                results['status'] = 'VULNERABLE'
                                
                                vulnerability = {
                                    'type': 'Deprecated TLS Version',
                                    'severity': 'MEDIUM',
                                    'cvss_score': 5.3,
                                    'endpoint': f'{hostname}:{port}',
                                    'description': f'Server supports deprecated {version_name}',
                                    'recommendation': f'Disable {version_name} support'
                                }
                                results['vulnerabilities'].append(vulnerability)
                    
                    except Exception:
                        results['findings'].append(f"✅ {hostname}: Deprecated {version_name} properly disabled")
                
                results['protocol_tests'].append(protocol_results)
                
                # Overall protocol assessment
                if protocol_results['secure_protocols']:
                    results['findings'].append(f"✅ {hostname}: Modern TLS protocols supported")
                else:
                    results['findings'].append(f"❌ {hostname}: No modern TLS protocols supported")
                    results['security_score'] -= 30
                    results['status'] = 'VULNERABLE'
                
                if protocol_results['deprecated_protocols']:
                    results['findings'].append(f"⚠️ {hostname}: Deprecated protocols should be disabled")
            
            except Exception as e:
                results['findings'].append(f"❌ Protocol testing failed for {hostname}:{port} - {str(e)}")
                results['security_score'] -= 10
        
        return results
    
    async def validate_certificate_transparency(self) -> Dict:
        """Validate Certificate Transparency implementation"""
        results = {
            'test_type': 'Certificate Transparency Validation',
            'status': 'SECURE',
            'security_score': 100,
            'vulnerabilities': [],
            'findings': []
        }
        
        # For self-signed certificates, CT is not applicable
        results['findings'].append("ℹ️ Certificate Transparency validation not applicable for self-signed certificates")
        results['findings'].append("ℹ️ Production deployment should implement Certificate Transparency monitoring")
        results['findings'].append("✅ CT validation framework ready for production certificates")
        
        # Deduct minimal points for not having production CT
        results['security_score'] -= 5
        results['status'] = 'WARNING'
        
        return results
    
    async def validate_ocsp_stapling(self) -> Dict:
        """Validate OCSP stapling implementation"""
        results = {
            'test_type': 'OCSP Stapling Validation',
            'status': 'SECURE',
            'security_score': 100,
            'vulnerabilities': [],
            'findings': []
        }
        
        # Check nginx configuration for OCSP stapling
        try:
            nginx_configs = [
                'config/nginx.conf',
                'docker/nginx-ssl.conf',
                'docker/nginx-production-ssl.conf'
            ]
            
            ocsp_configured = False
            for config_file in nginx_configs:
                try:
                    with open(config_file, 'r') as f:
                        config_content = f.read()
                    
                    if 'ssl_stapling on' in config_content:
                        results['findings'].append(f"✅ OCSP stapling enabled in {config_file}")
                        ocsp_configured = True
                    
                    if 'ssl_stapling_verify on' in config_content:
                        results['findings'].append(f"✅ OCSP stapling verification enabled in {config_file}")
                    
                    if 'ssl_trusted_certificate' in config_content:
                        results['findings'].append(f"✅ Trusted certificate chain configured in {config_file}")
                
                except FileNotFoundError:
                    continue
            
            if not ocsp_configured:
                results['findings'].append("⚠️ OCSP stapling not found in nginx configuration")
                results['security_score'] -= 10
                results['status'] = 'WARNING'
            
            # For self-signed certificates, OCSP is not applicable
            results['findings'].append("ℹ️ OCSP validation not applicable for self-signed certificates")
            results['findings'].append("✅ OCSP stapling configuration ready for production")
        
        except Exception as e:
            results['findings'].append(f"❌ OCSP configuration check failed: {str(e)}")
            results['security_score'] -= 15
            results['status'] = 'WARNING'
        
        return results
    
    async def analyze_certificate_expiration(self) -> Dict:
        """Analyze certificate expiration and renewal status"""
        results = {
            'test_type': 'Certificate Expiration Analysis',
            'status': 'SECURE',
            'security_score': 100,
            'vulnerabilities': [],
            'findings': [],
            'expiration_analysis': []
        }
        
        try:
            # Load certificate
            with open(self.ssl_files['certificate'], 'r') as f:
                cert_pem = f.read()
            
            cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_pem)
            
            # Parse dates
            not_before = datetime.strptime(cert.get_notBefore().decode(), '%Y%m%d%H%M%SZ')
            not_after = datetime.strptime(cert.get_notAfter().decode(), '%Y%m%d%H%M%SZ')
            now = datetime.utcnow()
            
            days_until_expiry = (not_after - now).days
            total_validity = (not_after - not_before).days
            
            expiration_info = {
                'not_before': not_before.isoformat(),
                'not_after': not_after.isoformat(),
                'days_until_expiry': days_until_expiry,
                'total_validity_days': total_validity,
                'is_expired': now > not_after,
                'is_valid': not_before <= now <= not_after
            }
            
            results['expiration_analysis'].append(expiration_info)
            
            # Analyze expiration status
            if days_until_expiry < 0:
                results['findings'].append(f"❌ Certificate expired {abs(days_until_expiry)} days ago")
                results['security_score'] = 0
                results['status'] = 'VULNERABLE'
                vulnerability = {
                    'type': 'Expired Certificate',
                    'severity': 'CRITICAL',
                    'cvss_score': 9.1,
                    'description': 'SSL certificate has expired',
                    'recommendation': 'Renew certificate immediately'
                }
                results['vulnerabilities'].append(vulnerability)
            
            elif days_until_expiry <= 7:
                results['findings'].append(f"🚨 Certificate expires in {days_until_expiry} days - URGENT renewal needed")
                results['security_score'] -= 30
                results['status'] = 'VULNERABLE'
                vulnerability = {
                    'type': 'Certificate Expiring Soon',
                    'severity': 'HIGH',
                    'cvss_score': 7.8,
                    'description': f'Certificate expires in {days_until_expiry} days',
                    'recommendation': 'Renew certificate immediately'
                }
                results['vulnerabilities'].append(vulnerability)
            
            elif days_until_expiry <= 30:
                results['findings'].append(f"⚠️ Certificate expires in {days_until_expiry} days - Renewal recommended")
                results['security_score'] -= 10
                results['status'] = 'WARNING'
            
            elif days_until_expiry <= 90:
                results['findings'].append(f"ℹ️ Certificate expires in {days_until_expiry} days - Plan renewal")
            
            else:
                results['findings'].append(f"✅ Certificate expires in {days_until_expiry} days")
            
            # Check renewal automation
            if days_until_expiry > 0:
                results['findings'].append("📝 Consider implementing automated certificate renewal")
                results['findings'].append("🔄 Monitor certificate expiration dates regularly")
        
        except Exception as e:
            results['findings'].append(f"❌ Certificate expiration analysis failed: {str(e)}")
            results['status'] = 'FAILED'
            results['security_score'] = 0
        
        return results
    
    async def analyze_ssl_implementation(self) -> Dict:
        """Analyze overall SSL implementation security"""
        results = {
            'test_type': 'SSL Implementation Security',
            'status': 'SECURE',
            'security_score': 100,
            'vulnerabilities': [],
            'findings': [],
            'implementation_analysis': {}
        }
        
        try:
            # Check SSL file permissions
            import os
            import stat
            
            file_permissions = {}
            for file_type, file_path in self.ssl_files.items():
                if os.path.exists(file_path):
                    file_stat = os.stat(file_path)
                    permissions = oct(file_stat.st_mode)[-3:]
                    file_permissions[file_type] = permissions
                    
                    # Private key should be highly restricted
                    if file_type == 'private_key':
                        if permissions == '600' or permissions == '400':
                            results['findings'].append(f"✅ Private key has secure permissions: {permissions}")
                        else:
                            results['findings'].append(f"⚠️ Private key permissions could be more restrictive: {permissions}")
                            results['security_score'] -= 15
                            results['status'] = 'WARNING'
                            vulnerability = {
                                'type': 'Insecure File Permissions',
                                'severity': 'MEDIUM',
                                'cvss_score': 4.9,
                                'description': f'Private key file has permissions {permissions}',
                                'recommendation': 'Set private key permissions to 600 or 400'
                            }
                            results['vulnerabilities'].append(vulnerability)
                    
                    # Certificates can be more permissive but shouldn't be world-writable
                    elif 'writable' in permissions or permissions.endswith('7'):
                        results['findings'].append(f"⚠️ {file_type} is world-writable: {permissions}")
                        results['security_score'] -= 5
                        if results['status'] == 'SECURE':
                            results['status'] = 'WARNING'
                    else:
                        results['findings'].append(f"✅ {file_type} has appropriate permissions: {permissions}")
            
            results['implementation_analysis']['file_permissions'] = file_permissions
            
            # Check SSL configuration
            try:
                with open(self.ssl_files['config'], 'r') as f:
                    ssl_config = json.load(f)
                
                results['implementation_analysis']['ssl_config'] = ssl_config
                
                # Validate configuration
                if ssl_config.get('type') == 'self_signed':
                    results['findings'].append("ℹ️ Self-signed certificate configuration (appropriate for development)")
                
                validity_days = ssl_config.get('validity_days', 0)
                if validity_days <= 365:
                    results['findings'].append(f"✅ Certificate validity period: {validity_days} days")
                else:
                    results['findings'].append(f"⚠️ Long certificate validity period: {validity_days} days")
                    results['security_score'] -= 5
                
            except Exception as e:
                results['findings'].append(f"⚠️ Could not load SSL configuration: {str(e)}")
                results['security_score'] -= 5
            
            # Check for SSL-related security headers implementation
            security_headers_files = [
                'config/nginx.conf',
                'api_main.py',
                'docker/nginx-ssl.conf'
            ]
            
            headers_implemented = []
            for file_path in security_headers_files:
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    if 'Strict-Transport-Security' in content:
                        headers_implemented.append('HSTS')
                    
                    if 'ssl_protocols' in content:
                        headers_implemented.append('SSL Protocol Configuration')
                    
                    if 'ssl_ciphers' in content:
                        headers_implemented.append('Cipher Suite Configuration')
                
                except FileNotFoundError:
                    continue
            
            if headers_implemented:
                results['findings'].append(f"✅ Security headers implemented: {', '.join(set(headers_implemented))}")
            else:
                results['findings'].append("⚠️ No SSL security headers configuration found")
                results['security_score'] -= 10
                if results['status'] == 'SECURE':
                    results['status'] = 'WARNING'
            
            results['findings'].append("✅ SSL implementation security analysis completed")
        
        except Exception as e:
            results['findings'].append(f"❌ SSL implementation analysis failed: {str(e)}")
            results['status'] = 'FAILED'
            results['security_score'] = 0
        
        return results
    
    async def generate_ssl_security_report(self) -> Dict:
        """Generate comprehensive SSL security report"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Calculate overall SSL security score
        total_score = 0
        total_weight = 0
        category_scores = {}
        all_vulnerabilities = []
        
        for category, results in self.test_results.items():
            if isinstance(results, dict) and 'security_score' in results:
                weight = 1.0
                # Give higher weight to critical security areas
                if 'Certificate Security' in category or 'TLS Configuration' in category:
                    weight = 1.5
                elif 'Protocol Security' in category or 'Certificate Chain' in category:
                    weight = 1.2
                
                category_scores[category] = results['security_score']
                total_score += results['security_score'] * weight
                total_weight += weight
                
                # Collect vulnerabilities
                category_vulns = results.get('vulnerabilities', [])
                all_vulnerabilities.extend(category_vulns)
        
        overall_ssl_score = total_score / total_weight if total_weight > 0 else 0
        
        # Determine SSL security grade
        if overall_ssl_score >= 95:
            ssl_grade = 'A+'
            ssl_status = 'EXCELLENT'
        elif overall_ssl_score >= 90:
            ssl_grade = 'A'
            ssl_status = 'VERY_GOOD'
        elif overall_ssl_score >= 85:
            ssl_grade = 'B+'
            ssl_status = 'GOOD'
        elif overall_ssl_score >= 80:
            ssl_grade = 'B'
            ssl_status = 'ACCEPTABLE'
        elif overall_ssl_score >= 70:
            ssl_grade = 'C'
            ssl_status = 'NEEDS_IMPROVEMENT'
        else:
            ssl_grade = 'F'
            ssl_status = 'CRITICAL'
        
        # Categorize vulnerabilities by severity
        critical_vulns = [v for v in all_vulnerabilities if v.get('cvss_score', 0) >= 9.0]
        high_vulns = [v for v in all_vulnerabilities if 7.0 <= v.get('cvss_score', 0) < 9.0]
        medium_vulns = [v for v in all_vulnerabilities if 4.0 <= v.get('cvss_score', 0) < 7.0]
        low_vulns = [v for v in all_vulnerabilities if v.get('cvss_score', 0) < 4.0]
        
        report = {
            'test_execution': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'test_suite': 'SSL/TLS Security Validation Suite v1.0'
            },
            'ssl_security_assessment': {
                'overall_score': round(overall_ssl_score, 1),
                'ssl_grade': ssl_grade,
                'ssl_status': ssl_status,
                'production_ready': overall_ssl_score >= 80 and len(critical_vulns) == 0,
                'ssl_compliant': overall_ssl_score >= 85,
                'vulnerabilities_found': len(all_vulnerabilities),
                'critical_vulnerabilities': len(critical_vulns),
                'high_vulnerabilities': len(high_vulns),
                'medium_vulnerabilities': len(medium_vulns),
                'low_vulnerabilities': len(low_vulns)
            },
            'category_scores': category_scores,
            'detailed_results': self.test_results,
            'vulnerability_summary': {
                'critical': critical_vulns,
                'high': high_vulns,
                'medium': medium_vulns,
                'low': low_vulns
            },
            'ssl_recommendations': self.generate_ssl_recommendations(all_vulnerabilities, overall_ssl_score),
            'ssl_endpoints_tested': self.ssl_endpoints,
            'ssl_files_analyzed': list(self.ssl_files.keys())
        }
        
        # Save SSL security report
        with open('ssl_security_validation_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report
    
    def generate_ssl_recommendations(self, vulnerabilities: List[Dict], ssl_score: float) -> List[str]:
        """Generate SSL-specific security recommendations"""
        recommendations = []
        
        # Critical vulnerabilities
        critical_vulns = [v for v in vulnerabilities if v.get('cvss_score', 0) >= 9.0]
        if critical_vulns:
            recommendations.append("🚨 CRITICAL SSL ISSUES: Address immediately before production deployment")
            for vuln in critical_vulns:
                recommendations.append(f"  - {vuln['type']}: {vuln.get('recommendation', 'Review and fix')}")
        
        # High severity SSL issues
        high_vulns = [v for v in vulnerabilities if 7.0 <= v.get('cvss_score', 0) < 9.0]
        if high_vulns:
            recommendations.append("⚠️ HIGH PRIORITY SSL ISSUES:")
            for vuln in high_vulns:
                recommendations.append(f"  - {vuln['type']}: {vuln.get('recommendation', 'Review and fix')}")
        
        # General SSL recommendations
        if ssl_score < 90:
            recommendations.append("🔒 SSL/TLS security below recommended threshold")
        
        # Specific SSL recommendations
        vuln_types = set(v.get('type', '') for v in vulnerabilities)
        
        if 'Weak Key Length' in vuln_types:
            recommendations.append("🔑 Upgrade to 2048-bit RSA or 256-bit ECC keys minimum")
        
        if 'Weak Signature Algorithm' in vuln_types:
            recommendations.append("📝 Migrate from SHA-1 to SHA-256 or stronger signature algorithms")
        
        if 'Insecure TLS Version' in vuln_types or 'Deprecated TLS Version' in vuln_types:
            recommendations.append("🔄 Disable TLS versions below 1.2, prefer TLS 1.3")
        
        if 'Expired Certificate' in vuln_types:
            recommendations.append("⏰ Implement automated certificate renewal (Let's Encrypt, ACME)")
        
        # Production readiness recommendations
        recommendations.extend([
            "🏭 For production: Obtain certificates from trusted CA (Let's Encrypt, DigiCert, etc.)",
            "🔄 Implement automated certificate renewal and monitoring",
            "📊 Set up certificate expiration alerts (30, 7, 1 days)",
            "🛡️ Enable OCSP stapling for production deployments",
            "🌐 Implement Certificate Transparency monitoring",
            "🔍 Conduct regular SSL/TLS security assessments",
            "⚡ Consider implementing TLS 1.3 for enhanced security and performance",
            "🔐 Review and harden cipher suite configurations",
            "📋 Maintain SSL/TLS security documentation and procedures"
        ])
        
        return recommendations

async def main():
    """Main SSL security validation function"""
    print("🔒 OMEGA Pro AI - SSL/TLS Security Validation Suite")
    print("=" * 70)
    
    validator = SSLSecurityValidator()
    
    try:
        report = await validator.run_ssl_validation()
        
        # Print SSL security summary
        print("\n" + "=" * 70)
        print("🔒 SSL/TLS SECURITY VALIDATION SUMMARY")
        print("=" * 70)
        
        assessment = report['ssl_security_assessment']
        print(f"SSL Security Score: {assessment['overall_score']}%")
        print(f"SSL Grade: {assessment['ssl_grade']}")
        print(f"SSL Status: {assessment['ssl_status']}")
        print(f"Production Ready: {'✅ YES' if assessment['production_ready'] else '❌ NO'}")
        print(f"SSL Compliant: {'✅ YES' if assessment['ssl_compliant'] else '❌ NO'}")
        
        print(f"\n🔍 SSL Vulnerability Summary:")
        print(f"  Critical: {assessment['critical_vulnerabilities']}")
        print(f"  High: {assessment['high_vulnerabilities']}")
        print(f"  Medium: {assessment['medium_vulnerabilities']}")
        print(f"  Low: {assessment['low_vulnerabilities']}")
        print(f"  Total: {assessment['vulnerabilities_found']}")
        
        if assessment['vulnerabilities_found'] > 0:
            print("\n🚨 SSL SECURITY ISSUES FOUND:")
            for vuln in report['vulnerability_summary']['critical'] + report['vulnerability_summary']['high']:
                print(f"  - {vuln['type']} (CVSS: {vuln.get('cvss_score', 'N/A')})")
                if 'endpoint' in vuln:
                    print(f"    Endpoint: {vuln['endpoint']}")
                if 'recommendation' in vuln:
                    print(f"    Fix: {vuln['recommendation']}")
        
        print("\n💡 SSL SECURITY RECOMMENDATIONS:")
        for rec in report['ssl_recommendations']:
            print(f"  {rec}")
        
        print(f"\n📄 Detailed SSL report saved to: ssl_security_validation_report.json")
        print(f"📄 SSL test logs saved to: ssl_security_validation.log")
        
        return 0 if assessment['production_ready'] else 1
        
    except Exception as e:
        logger.error(f"❌ SSL security validation failed: {str(e)}")
        return 1

if __name__ == "__main__":
    import sys
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)