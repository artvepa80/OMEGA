#!/usr/bin/env python3
"""
OMEGA SSL Deployment Validation Script
Comprehensive testing and validation of production SSL certificate deployment
"""

import click
import subprocess
import json
import requests
import ssl
import socket
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import hashlib

class SSLDeploymentValidator:
    """Validates complete SSL certificate deployment"""
    
    def __init__(self, domain: str = "omega-api.akash.network"):
        self.domain = domain
        self.ssl_dir = Path("./ssl")
        self.results = []
        
    def log_result(self, test_name: str, success: bool, message: str, details: Dict = None):
        """Log test result"""
        
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        self.results.append(result)
        
        icon = "✅" if success else "❌"
        click.echo(f"{icon} {test_name}: {message}")
        
        if details and not success:
            for key, value in details.items():
                click.echo(f"   {key}: {value}")
    
    def test_local_certificate_files(self) -> bool:
        """Test local certificate files exist and are valid"""
        
        click.echo("🔍 Testing local certificate files...")
        
        required_files = [
            ("cert.pem", "SSL Certificate"),
            ("key.pem", "Private Key"),
            ("bundle.pem", "Certificate Bundle"),
            ("ssl_config.json", "SSL Configuration")
        ]
        
        missing_files = []
        
        for filename, description in required_files:
            file_path = self.ssl_dir / filename
            
            if not file_path.exists():
                missing_files.append(f"{description} ({filename})")
            else:
                # Check file permissions
                stat = file_path.stat()
                if filename == "key.pem" and oct(stat.st_mode)[-3:] != "600":
                    self.log_result(
                        f"Certificate File Permissions ({filename})",
                        False,
                        f"Insecure permissions: {oct(stat.st_mode)[-3:]} (should be 600)",
                        {"file": str(file_path), "permissions": oct(stat.st_mode)[-3:]}
                    )
                else:
                    self.log_result(
                        f"Certificate File ({filename})",
                        True,
                        f"{description} exists with proper permissions"
                    )
        
        if missing_files:
            self.log_result(
                "Local Certificate Files",
                False,
                f"Missing files: {', '.join(missing_files)}",
                {"missing_files": missing_files}
            )
            return False
        
        # Validate certificate content
        try:
            cert_path = self.ssl_dir / "cert.pem"
            with open(cert_path, 'rb') as f:
                cert_data = f.read()
            
            from cryptography import x509
            cert = x509.load_pem_x509_certificate(cert_data)
            
            # Check certificate validity
            not_before = cert.not_valid_before
            not_after = cert.not_valid_after
            now = datetime.utcnow()
            
            if not_before <= now <= not_after:
                days_left = (not_after - now).days
                self.log_result(
                    "Certificate Validity",
                    True,
                    f"Certificate valid for {days_left} days",
                    {"expires": not_after.isoformat(), "days_left": days_left}
                )
            else:
                self.log_result(
                    "Certificate Validity",
                    False,
                    "Certificate is expired or not yet valid",
                    {"not_before": not_before.isoformat(), "not_after": not_after.isoformat()}
                )
                
        except Exception as e:
            self.log_result(
                "Certificate Content Validation",
                False,
                f"Failed to parse certificate: {e}",
                {"error": str(e)}
            )
        
        return len(missing_files) == 0
    
    def test_ssl_connection(self) -> bool:
        """Test SSL connection to domain"""
        
        click.echo(f"🌐 Testing SSL connection to {self.domain}...")
        
        try:
            context = ssl.create_default_context()
            
            with socket.create_connection((self.domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=self.domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Extract certificate information
                    subject_dict = dict(x[0] for x in cert['subject'])
                    issuer_dict = dict(x[0] for x in cert['issuer'])
                    
                    details = {
                        "subject": subject_dict.get('commonName', 'Unknown'),
                        "issuer": issuer_dict.get('organizationName', 'Unknown'),
                        "version": cert['version'],
                        "serial_number": cert['serialNumber'],
                        "not_before": cert['notBefore'],
                        "not_after": cert['notAfter'],
                        "cipher": ssock.cipher()[0] if ssock.cipher() else 'Unknown',
                        "protocol": ssock.version() or 'Unknown'
                    }
                    
                    self.log_result(
                        "SSL Connection",
                        True,
                        f"Successfully connected to {self.domain}:443",
                        details
                    )
                    
                    return True
                    
        except Exception as e:
            self.log_result(
                "SSL Connection",
                False,
                f"Failed to connect to {self.domain}:443",
                {"error": str(e)}
            )
            return False
    
    def test_certificate_chain(self) -> bool:
        """Test certificate chain validation"""
        
        click.echo("🔗 Testing certificate chain...")
        
        try:
            result = subprocess.run([
                'openssl', 's_client', '-connect', f'{self.domain}:443',
                '-verify_return_error', '-brief'
            ], input='', capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 or 'Verification: OK' in result.stderr:
                self.log_result(
                    "Certificate Chain Validation",
                    True,
                    "Certificate chain is valid"
                )
                return True
            else:
                self.log_result(
                    "Certificate Chain Validation",
                    False,
                    "Certificate chain validation failed",
                    {"stderr": result.stderr, "returncode": result.returncode}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Certificate Chain Validation",
                False,
                f"Failed to validate certificate chain: {e}",
                {"error": str(e)}
            )
            return False
    
    def test_ocsp_stapling(self) -> bool:
        """Test OCSP stapling"""
        
        click.echo("📋 Testing OCSP stapling...")
        
        try:
            result = subprocess.run([
                'openssl', 's_client', '-connect', f'{self.domain}:443',
                '-status', '-tlsextdebug'
            ], input='', capture_output=True, text=True, timeout=15)
            
            if 'OCSP Response Status: successful' in result.stderr:
                self.log_result(
                    "OCSP Stapling",
                    True,
                    "OCSP stapling is working"
                )
                return True
            elif 'OCSP response: no response sent' in result.stderr:
                self.log_result(
                    "OCSP Stapling",
                    False,
                    "OCSP stapling is not configured"
                )
                return False
            else:
                self.log_result(
                    "OCSP Stapling",
                    False,
                    "OCSP stapling status unknown",
                    {"output": result.stderr[:500]}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "OCSP Stapling",
                False,
                f"Failed to check OCSP stapling: {e}",
                {"error": str(e)}
            )
            return False
    
    def test_ssl_labs_rating(self) -> bool:
        """Test SSL Labs rating (simplified)"""
        
        click.echo("🏆 Testing SSL configuration quality...")
        
        # Test TLS version support
        tls_versions = ['TLSv1.2', 'TLSv1.3']
        supported_versions = []
        
        for version in tls_versions:
            try:
                result = subprocess.run([
                    'openssl', 's_client', '-connect', f'{self.domain}:443',
                    f'-{version.lower()}', '-brief'
                ], input='', capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and 'Verification: OK' in result.stderr:
                    supported_versions.append(version)
                    
            except Exception:
                pass
        
        if 'TLSv1.3' in supported_versions:
            self.log_result(
                "TLS Version Support",
                True,
                f"Supports modern TLS versions: {', '.join(supported_versions)}",
                {"supported_versions": supported_versions}
            )
            return True
        elif 'TLSv1.2' in supported_versions:
            self.log_result(
                "TLS Version Support",
                True,
                f"Supports TLS 1.2: {', '.join(supported_versions)}",
                {"supported_versions": supported_versions}
            )
            return True
        else:
            self.log_result(
                "TLS Version Support",
                False,
                "No modern TLS versions supported",
                {"supported_versions": supported_versions}
            )
            return False
    
    def test_endpoints(self) -> bool:
        """Test HTTPS endpoints"""
        
        click.echo("🌐 Testing HTTPS endpoints...")
        
        endpoints = [
            ("/health", "Health Check"),
            ("/api/status", "API Status"),
            ("/ssl/info", "SSL Information")
        ]
        
        all_success = True
        
        for endpoint, description in endpoints:
            url = f"https://{self.domain}{endpoint}"
            
            try:
                response = requests.get(url, timeout=10, verify=True)
                
                if response.status_code == 200:
                    self.log_result(
                        f"Endpoint ({endpoint})",
                        True,
                        f"{description} accessible",
                        {"status_code": response.status_code, "response_time": response.elapsed.total_seconds()}
                    )
                else:
                    self.log_result(
                        f"Endpoint ({endpoint})",
                        False,
                        f"{description} returned status {response.status_code}",
                        {"status_code": response.status_code}
                    )
                    all_success = False
                    
            except requests.exceptions.SSLError as e:
                self.log_result(
                    f"Endpoint ({endpoint})",
                    False,
                    f"{description} SSL error",
                    {"error": str(e)}
                )
                all_success = False
                
            except Exception as e:
                self.log_result(
                    f"Endpoint ({endpoint})",
                    False,
                    f"{description} connection failed",
                    {"error": str(e)}
                )
                all_success = False
        
        return all_success
    
    def test_security_headers(self) -> bool:
        """Test security headers"""
        
        click.echo("🛡️ Testing security headers...")
        
        try:
            response = requests.get(f"https://{self.domain}/health", timeout=10, verify=True)
            headers = response.headers
            
            required_headers = {
                'Strict-Transport-Security': 'HSTS header',
                'X-Frame-Options': 'Clickjacking protection',
                'X-Content-Type-Options': 'MIME type sniffing protection',
                'X-XSS-Protection': 'XSS protection',
                'Content-Security-Policy': 'Content Security Policy'
            }
            
            missing_headers = []
            present_headers = {}
            
            for header, description in required_headers.items():
                if header in headers:
                    present_headers[header] = headers[header]
                else:
                    missing_headers.append(f"{description} ({header})")
            
            if missing_headers:
                self.log_result(
                    "Security Headers",
                    False,
                    f"Missing security headers: {', '.join(missing_headers)}",
                    {"missing": missing_headers, "present": present_headers}
                )
                return False
            else:
                self.log_result(
                    "Security Headers",
                    True,
                    "All security headers present",
                    {"headers": present_headers}
                )
                return True
                
        except Exception as e:
            self.log_result(
                "Security Headers",
                False,
                f"Failed to check security headers: {e}",
                {"error": str(e)}
            )
            return False
    
    def test_certificate_fingerprints(self) -> bool:
        """Test certificate fingerprints for iOS pinning"""
        
        click.echo("📱 Testing certificate fingerprints for iOS pinning...")
        
        try:
            # Get certificate from server
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((self.domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=self.domain) as ssock:
                    cert_der = ssock.getpeercert(binary_form=True)
                    
                    # Calculate fingerprints
                    cert_sha256 = hashlib.sha256(cert_der).hexdigest()
                    
                    # Get public key fingerprint
                    cert_pem = ssl.DER_cert_to_PEM_cert(cert_der)
                    from cryptography import x509
                    from cryptography.hazmat.primitives import serialization
                    
                    cert_obj = x509.load_pem_x509_certificate(cert_pem.encode())
                    public_key = cert_obj.public_key()
                    public_key_der = public_key.public_key_bytes(
                        encoding=serialization.Encoding.DER,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    )
                    public_key_sha256 = hashlib.sha256(public_key_der).hexdigest()
                    
                    fingerprints = {
                        "certificate_sha256": cert_sha256,
                        "public_key_sha256": public_key_sha256
                    }
                    
                    # Check if local config has matching fingerprints
                    ssl_config_path = self.ssl_dir / "ssl_config.json"
                    if ssl_config_path.exists():
                        with open(ssl_config_path, 'r') as f:
                            config = json.load(f)
                        
                        local_fingerprints = config.get('cert_fingerprints', {})
                        
                        if local_fingerprints.get('certificate_sha256') == cert_sha256:
                            self.log_result(
                                "Certificate Fingerprints",
                                True,
                                "Certificate fingerprints match local configuration",
                                fingerprints
                            )
                            return True
                        else:
                            self.log_result(
                                "Certificate Fingerprints",
                                False,
                                "Certificate fingerprints don't match local configuration",
                                {
                                    "server": fingerprints,
                                    "local": local_fingerprints
                                }
                            )
                            return False
                    else:
                        self.log_result(
                            "Certificate Fingerprints",
                            True,
                            "Certificate fingerprints extracted (no local config to compare)",
                            fingerprints
                        )
                        return True
                        
        except Exception as e:
            self.log_result(
                "Certificate Fingerprints",
                False,
                f"Failed to extract certificate fingerprints: {e}",
                {"error": str(e)}
            )
            return False
    
    def test_auto_renewal(self) -> bool:
        """Test certificate auto-renewal setup"""
        
        click.echo("🔄 Testing certificate auto-renewal setup...")
        
        # Check if renewal script exists
        renewal_script = self.ssl_dir / "renew_certificate.sh"
        
        if not renewal_script.exists():
            self.log_result(
                "Auto-Renewal Script",
                False,
                "Renewal script not found",
                {"expected_path": str(renewal_script)}
            )
            return False
        
        # Check cron job
        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            
            if result.returncode == 0:
                cron_content = result.stdout
                
                if str(renewal_script) in cron_content:
                    self.log_result(
                        "Auto-Renewal Cron Job",
                        True,
                        "Certificate auto-renewal cron job is configured"
                    )
                    return True
                else:
                    self.log_result(
                        "Auto-Renewal Cron Job",
                        False,
                        "Certificate auto-renewal cron job not found"
                    )
                    return False
            else:
                self.log_result(
                    "Auto-Renewal Cron Job",
                    False,
                    "Could not check cron jobs",
                    {"error": result.stderr}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Auto-Renewal Check",
                False,
                f"Failed to check auto-renewal setup: {e}",
                {"error": str(e)}
            )
            return False
    
    def generate_validation_report(self) -> dict:
        """Generate comprehensive validation report"""
        
        successful_tests = sum(1 for result in self.results if result["success"])
        total_tests = len(self.results)
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "validation_timestamp": datetime.now().isoformat(),
            "domain": self.domain,
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests,
                "success_rate": success_rate
            },
            "test_results": self.results,
            "deployment_status": "PASSED" if success_rate >= 80 else "FAILED",
            "recommendations": []
        }
        
        # Generate recommendations based on failed tests
        failed_tests = [result for result in self.results if not result["success"]]
        
        for failed_test in failed_tests:
            test_name = failed_test["test"]
            
            if "SSL Connection" in test_name:
                report["recommendations"].append("Check network connectivity and DNS resolution")
            elif "Certificate Chain" in test_name:
                report["recommendations"].append("Verify certificate chain completeness and CA trust")
            elif "OCSP Stapling" in test_name:
                report["recommendations"].append("Configure OCSP stapling in nginx")
            elif "Security Headers" in test_name:
                report["recommendations"].append("Add missing security headers to nginx configuration")
            elif "Auto-Renewal" in test_name:
                report["recommendations"].append("Setup certificate auto-renewal cron job")
        
        return report

@click.command()
@click.option('--domain', default='omega-api.akash.network', help='Domain to validate')
@click.option('--output', help='Output file for validation report')
@click.option('--verbose', is_flag=True, help='Verbose output')
def validate_ssl_deployment(domain, output, verbose):
    """Validate production SSL certificate deployment"""
    
    click.echo("🔍 OMEGA SSL Deployment Validation")
    click.echo("=" * 70)
    
    validator = SSLDeploymentValidator(domain)
    
    # Define validation tests
    tests = [
        ("Local Certificate Files", validator.test_local_certificate_files),
        ("SSL Connection", validator.test_ssl_connection),
        ("Certificate Chain", validator.test_certificate_chain),
        ("OCSP Stapling", validator.test_ocsp_stapling),
        ("TLS Configuration", validator.test_ssl_labs_rating),
        ("HTTPS Endpoints", validator.test_endpoints),
        ("Security Headers", validator.test_security_headers),
        ("Certificate Fingerprints", validator.test_certificate_fingerprints),
        ("Auto-Renewal Setup", validator.test_auto_renewal)
    ]
    
    # Run all tests
    for test_name, test_func in tests:
        click.echo(f"\\n📋 Running: {test_name}")
        click.echo("-" * 50)
        
        try:
            test_func()
        except Exception as e:
            validator.log_result(
                test_name,
                False,
                f"Test execution failed: {e}",
                {"error": str(e)}
            )
        
        if not verbose:
            time.sleep(0.5)  # Small delay for readability
    
    # Generate report
    report = validator.generate_validation_report()
    
    # Display summary
    click.echo("\\n" + "=" * 70)
    click.echo("📊 VALIDATION SUMMARY")
    click.echo("=" * 70)
    
    summary = report["summary"]
    status_icon = "✅" if report["deployment_status"] == "PASSED" else "❌"
    
    click.echo(f"{status_icon} Deployment Status: {report['deployment_status']}")
    click.echo(f"📈 Success Rate: {summary['success_rate']:.1f}%")
    click.echo(f"✅ Successful Tests: {summary['successful_tests']}")
    click.echo(f"❌ Failed Tests: {summary['failed_tests']}")
    click.echo(f"📊 Total Tests: {summary['total_tests']}")
    
    # Show recommendations
    if report["recommendations"]:
        click.echo(f"\\n🎯 RECOMMENDATIONS:")
        for i, recommendation in enumerate(report["recommendations"], 1):
            click.echo(f"   {i}. {recommendation}")
    
    # Save report
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        click.echo(f"\\n📄 Validation report saved: {output_path}")
    
    # Exit with appropriate code
    exit_code = 0 if report["deployment_status"] == "PASSED" else 1
    
    click.echo("=" * 70)
    
    if exit_code == 0:
        click.echo("🎉 SSL deployment validation PASSED!")
    else:
        click.echo("⚠️ SSL deployment validation FAILED - see recommendations above")
    
    exit(exit_code)

if __name__ == '__main__':
    validate_ssl_deployment()