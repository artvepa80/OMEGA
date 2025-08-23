#!/usr/bin/env python3
"""
🔒 OMEGA PRO AI - Security Implementation Validator
Validates all critical security fixes and generates compliance report
"""

import os
import json
import ssl
import socket
import subprocess
import sys
import time
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Any
import xml.etree.ElementTree as ET
from pathlib import Path

class SecurityValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'overall_score': 0,
            'tests': [],
            'critical_issues': [],
            'warnings': [],
            'recommendations': []
        }
    
    def run_all_validations(self) -> Dict[str, Any]:
        """Run all security validations"""
        print("🔒 Starting OMEGA Security Validation...")
        print("=" * 60)
        
        # Test 1: iOS MITM Vulnerability Fix
        self.validate_ios_ssl_config()
        
        # Test 2: Encrypted Certificate Storage
        self.validate_encrypted_certificates()
        
        # Test 3: Content Security Policy
        self.validate_csp_implementation()
        
        # Test 4: OCSP Configuration
        self.validate_ocsp_configuration()
        
        # Test 5: Nginx Security Configuration
        self.validate_nginx_security()
        
        # Test 6: API Security Headers
        self.validate_api_security_headers()
        
        # Calculate overall score
        self.calculate_overall_score()
        
        # Generate final report
        self.generate_security_report()
        
        return self.results
    
    def validate_ios_ssl_config(self):
        """Validate iOS SSL configuration fixes"""
        print("📱 Validating iOS SSL Configuration...")
        
        test_result = {
            'test_name': 'iOS MITM Vulnerability Fix',
            'status': 'UNKNOWN',
            'score': 0,
            'details': [],
            'critical': True
        }
        
        # Check Info.plist files
        info_plist_files = list(self.project_root.glob('ios/**/Info.plist'))
        
        for plist_file in info_plist_files:
            try:
                with open(plist_file, 'r') as f:
                    content = f.read()
                
                # Check for NSExceptionServerTrustEvaluationDisabled
                if '<key>NSExceptionServerTrustEvaluationDisabled</key>' in content:
                    if '<true/>' in content:
                        test_result['details'].append(f"❌ CRITICAL: Trust evaluation disabled in {plist_file}")
                        self.results['critical_issues'].append(f"SSL bypass enabled in {plist_file}")
                    else:
                        test_result['details'].append(f"✅ Trust evaluation properly configured in {plist_file}")
                        test_result['score'] += 25
                
                # Check for Certificate Transparency
                if '<key>NSRequiresCertificateTransparency</key>' in content:
                    if '<true/>' in content:
                        test_result['details'].append(f"✅ Certificate Transparency enabled in {plist_file}")
                        test_result['score'] += 15
                    else:
                        test_result['details'].append(f"⚠️ Certificate Transparency disabled in {plist_file}")
                
                # Check for OCSP stapling requirement
                if '<key>NSExceptionRequiresOCSPStapling</key>' in content:
                    test_result['details'].append(f"✅ OCSP stapling configured in {plist_file}")
                    test_result['score'] += 10
                
            except Exception as e:
                test_result['details'].append(f"❌ Error reading {plist_file}: {e}")
        
        # Check for new SSL managers
        ssl_managers = list(self.project_root.glob('ios/**/*SSL*.swift'))
        if ssl_managers:
            test_result['details'].append(f"✅ Found {len(ssl_managers)} SSL management files")
            test_result['score'] += 20
        
        test_result['status'] = 'PASS' if test_result['score'] >= 50 else 'FAIL'
        self.results['tests'].append(test_result)
        
        print(f"  Score: {test_result['score']}/70")
        for detail in test_result['details']:
            print(f"  {detail}")
    
    def validate_encrypted_certificates(self):
        """Validate encrypted certificate storage implementation"""
        print("🔐 Validating Encrypted Certificate Storage...")
        
        test_result = {
            'test_name': 'Encrypted Certificate Storage',
            'status': 'UNKNOWN',
            'score': 0,
            'details': [],
            'critical': False
        }
        
        # Check for EncryptedCertificates bundle
        encrypted_bundles = list(self.project_root.glob('**/EncryptedCertificates.bundle'))
        if encrypted_bundles:
            test_result['details'].append(f"✅ Found encrypted certificate bundle at {encrypted_bundles[0]}")
            test_result['score'] += 30
            
            # Check bundle contents
            for bundle in encrypted_bundles:
                enc_files = list(bundle.glob('*.enc'))
                if enc_files:
                    test_result['details'].append(f"✅ Found {len(enc_files)} encrypted certificate files")
                    test_result['score'] += 20
                
                info_plist = bundle / 'Info.plist'
                if info_plist.exists():
                    test_result['details'].append(f"✅ Bundle Info.plist present")
                    test_result['score'] += 10
        else:
            test_result['details'].append("❌ No encrypted certificate bundle found")
        
        # Check for certificate encryption utilities
        crypto_utils = list(self.project_root.glob('**/CertificateEncryption*.swift'))
        if crypto_utils:
            test_result['details'].append(f"✅ Certificate encryption utilities found")
            test_result['score'] += 20
        else:
            test_result['details'].append("⚠️ No certificate encryption utilities found")
        
        # Check for enterprise SSL manager
        ssl_managers = list(self.project_root.glob('**/EnterpriseSSL*.swift'))
        if ssl_managers:
            test_result['details'].append(f"✅ Enterprise SSL manager implemented")
            test_result['score'] += 20
        
        test_result['status'] = 'PASS' if test_result['score'] >= 60 else 'FAIL'
        self.results['tests'].append(test_result)
        
        print(f"  Score: {test_result['score']}/100")
        for detail in test_result['details']:
            print(f"  {detail}")
    
    def validate_csp_implementation(self):
        """Validate Content Security Policy implementation"""
        print("🛡️ Validating Content Security Policy...")
        
        test_result = {
            'test_name': 'Content Security Policy',
            'status': 'UNKNOWN',
            'score': 0,
            'details': [],
            'critical': True
        }
        
        # Check nginx configuration
        nginx_config = self.project_root / 'config' / 'nginx.conf'
        if nginx_config.exists():
            with open(nginx_config, 'r') as f:
                content = f.read()
            
            if 'Content-Security-Policy' in content:
                test_result['details'].append("✅ CSP header configured in nginx")
                test_result['score'] += 25
                
                if 'unsafe-inline' not in content:
                    test_result['details'].append("✅ No unsafe-inline directive found")
                    test_result['score'] += 25
                else:
                    test_result['details'].append("❌ CRITICAL: unsafe-inline directive present")
                    self.results['critical_issues'].append("CSP contains unsafe-inline")
                
                if 'unsafe-eval' not in content:
                    test_result['details'].append("✅ No unsafe-eval directive found")
                    test_result['score'] += 25
                else:
                    test_result['details'].append("❌ CRITICAL: unsafe-eval directive present")
                    self.results['critical_issues'].append("CSP contains unsafe-eval")
                
                if 'nonce-' in content:
                    test_result['details'].append("✅ Nonce-based CSP implemented")
                    test_result['score'] += 15
            else:
                test_result['details'].append("❌ No CSP configuration found in nginx")
        else:
            test_result['details'].append("❌ nginx.conf not found")
        
        # Check API security headers
        api_files = list(self.project_root.glob('api*.py'))
        for api_file in api_files:
            with open(api_file, 'r') as f:
                content = f.read()
            
            if 'Content-Security-Policy' in content:
                test_result['details'].append(f"✅ CSP headers in {api_file.name}")
                test_result['score'] += 10
                
                if 'secrets.token_urlsafe' in content:
                    test_result['details'].append(f"✅ Secure nonce generation in {api_file.name}")
                    test_result['score'] += 5
        
        test_result['status'] = 'PASS' if test_result['score'] >= 80 else 'FAIL'
        self.results['tests'].append(test_result)
        
        print(f"  Score: {test_result['score']}/105")
        for detail in test_result['details']:
            print(f"  {detail}")
    
    def validate_ocsp_configuration(self):
        """Validate OCSP configuration"""
        print("📋 Validating OCSP Configuration...")
        
        test_result = {
            'test_name': 'OCSP Certificate Revocation',
            'status': 'UNKNOWN',
            'score': 0,
            'details': [],
            'critical': False
        }
        
        # Check nginx OCSP stapling configuration
        nginx_config = self.project_root / 'config' / 'nginx.conf'
        if nginx_config.exists():
            with open(nginx_config, 'r') as f:
                content = f.read()
            
            if 'ssl_stapling on' in content:
                test_result['details'].append("✅ OCSP stapling enabled in nginx")
                test_result['score'] += 30
            
            if 'ssl_stapling_verify on' in content:
                test_result['details'].append("✅ OCSP stapling verification enabled")
                test_result['score'] += 20
            
            if 'ssl_trusted_certificate' in content:
                test_result['details'].append("✅ Trusted certificate chain configured")
                test_result['score'] += 15
        
        # Check iOS OCSP validation service
        ocsp_services = list(self.project_root.glob('**/OCSP*.swift'))
        if ocsp_services:
            test_result['details'].append(f"✅ OCSP validation service implemented")
            test_result['score'] += 25
            
            # Check service implementation
            for service_file in ocsp_services:
                with open(service_file, 'r') as f:
                    content = f.read()
                
                if 'validateCertificate' in content:
                    test_result['details'].append("✅ Certificate validation method present")
                    test_result['score'] += 10
        else:
            test_result['details'].append("⚠️ No dedicated OCSP service found")
        
        test_result['status'] = 'PASS' if test_result['score'] >= 70 else 'FAIL'
        self.results['tests'].append(test_result)
        
        print(f"  Score: {test_result['score']}/100")
        for detail in test_result['details']:
            print(f"  {detail}")
    
    def validate_nginx_security(self):
        """Validate nginx security configuration"""
        print("⚙️ Validating Nginx Security Configuration...")
        
        test_result = {
            'test_name': 'Nginx Security Configuration',
            'status': 'UNKNOWN',
            'score': 0,
            'details': [],
            'critical': False
        }
        
        nginx_config = self.project_root / 'config' / 'nginx.conf'
        if not nginx_config.exists():
            test_result['details'].append("❌ nginx.conf not found")
            test_result['status'] = 'FAIL'
            self.results['tests'].append(test_result)
            return
        
        with open(nginx_config, 'r') as f:
            content = f.read()
        
        security_headers = [
            ('X-Frame-Options', 20),
            ('X-Content-Type-Options', 15),
            ('X-XSS-Protection', 15),
            ('Strict-Transport-Security', 25),
            ('Referrer-Policy', 10),
            ('Cross-Origin-Embedder-Policy', 5),
            ('Cross-Origin-Opener-Policy', 5),
            ('Expect-CT', 5)
        ]
        
        for header, points in security_headers:
            if header in content:
                test_result['details'].append(f"✅ {header} configured")
                test_result['score'] += points
            else:
                test_result['details'].append(f"⚠️ {header} missing")
        
        # Check SSL configuration
        if 'ssl_protocols TLSv1.2 TLSv1.3' in content:
            test_result['details'].append("✅ Modern TLS protocols configured")
            test_result['score'] += 10
        
        if 'ssl_prefer_server_ciphers on' in content:
            test_result['details'].append("✅ Server cipher preference enabled")
            test_result['score'] += 5
        
        test_result['status'] = 'PASS' if test_result['score'] >= 80 else 'FAIL'
        self.results['tests'].append(test_result)
        
        print(f"  Score: {test_result['score']}/115")
        for detail in test_result['details']:
            print(f"  {detail}")
    
    def validate_api_security_headers(self):
        """Validate API security headers implementation"""
        print("🌐 Validating API Security Headers...")
        
        test_result = {
            'test_name': 'API Security Headers',
            'status': 'UNKNOWN',
            'score': 0,
            'details': [],
            'critical': False
        }
        
        api_files = list(self.project_root.glob('api*.py'))
        
        for api_file in api_files:
            with open(api_file, 'r') as f:
                content = f.read()
            
            security_features = [
                ('TrustedHostMiddleware', 20, 'Trusted host middleware'),
                ('add_security_headers', 25, 'Security headers middleware'),
                ('Content-Security-Policy', 20, 'CSP header'),
                ('X-Frame-Options', 10, 'X-Frame-Options'),
                ('Strict-Transport-Security', 15, 'HSTS header'),
                ('secrets.token_urlsafe', 10, 'Secure nonce generation')
            ]
            
            for feature, points, description in security_features:
                if feature in content:
                    test_result['details'].append(f"✅ {description} in {api_file.name}")
                    test_result['score'] += points
        
        # Check CORS configuration
        for api_file in api_files:
            with open(api_file, 'r') as f:
                content = f.read()
            
            if 'allow_origins=["*"]' in content:
                test_result['details'].append(f"❌ CORS allows all origins in {api_file.name}")
                self.results['warnings'].append(f"Overly permissive CORS in {api_file.name}")
            elif 'allow_origins=' in content:
                test_result['details'].append(f"✅ CORS properly configured in {api_file.name}")
                test_result['score'] += 10
        
        test_result['status'] = 'PASS' if test_result['score'] >= 70 else 'FAIL'
        self.results['tests'].append(test_result)
        
        print(f"  Score: {test_result['score']}/110")
        for detail in test_result['details']:
            print(f"  {detail}")
    
    def calculate_overall_score(self):
        """Calculate overall security score"""
        total_score = 0
        max_score = 0
        critical_failures = 0
        
        for test in self.results['tests']:
            # Weight critical tests more heavily
            weight = 2.0 if test.get('critical', False) else 1.0
            total_score += test['score'] * weight
            
            # Calculate max possible score for this test
            if test['test_name'] == 'iOS MITM Vulnerability Fix':
                max_score += 70 * weight
            elif test['test_name'] == 'Encrypted Certificate Storage':
                max_score += 100 * weight
            elif test['test_name'] == 'Content Security Policy':
                max_score += 105 * weight
            elif test['test_name'] == 'OCSP Certificate Revocation':
                max_score += 100 * weight
            elif test['test_name'] == 'Nginx Security Configuration':
                max_score += 115 * weight
            elif test['test_name'] == 'API Security Headers':
                max_score += 110 * weight
            
            if test.get('critical', False) and test['status'] == 'FAIL':
                critical_failures += 1
        
        # Calculate percentage
        if max_score > 0:
            self.results['overall_score'] = min(100, (total_score / max_score) * 100)
        
        # Penalize for critical failures
        if critical_failures > 0:
            self.results['overall_score'] *= (1.0 - (critical_failures * 0.1))
        
        self.results['critical_failures'] = critical_failures
    
    def generate_security_report(self):
        """Generate final security report"""
        print("\n" + "=" * 60)
        print("🔒 OMEGA SECURITY VALIDATION RESULTS")
        print("=" * 60)
        
        print(f"📊 Overall Security Score: {self.results['overall_score']:.1f}%")
        
        if self.results['overall_score'] >= 95:
            print("✅ Security Status: ENTERPRISE READY")
        elif self.results['overall_score'] >= 80:
            print("⚠️ Security Status: GOOD (Minor issues)")
        elif self.results['overall_score'] >= 60:
            print("🟡 Security Status: NEEDS IMPROVEMENT")
        else:
            print("❌ Security Status: CRITICAL ISSUES")
        
        print(f"\n📋 Test Summary:")
        for test in self.results['tests']:
            status_icon = "✅" if test['status'] == 'PASS' else "❌"
            critical_marker = " [CRITICAL]" if test.get('critical', False) else ""
            print(f"  {status_icon} {test['test_name']}{critical_marker}")
        
        if self.results['critical_issues']:
            print(f"\n🚨 Critical Issues ({len(self.results['critical_issues'])}):")
            for issue in self.results['critical_issues']:
                print(f"  ❌ {issue}")
        
        if self.results['warnings']:
            print(f"\n⚠️ Warnings ({len(self.results['warnings'])}):")
            for warning in self.results['warnings']:
                print(f"  ⚠️ {warning}")
        
        # Save detailed results
        results_file = self.project_root / 'security_validation_results.json'
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")

def main():
    """Main execution function"""
    validator = SecurityValidator()
    results = validator.run_all_validations()
    
    # Exit with appropriate code
    if results['overall_score'] >= 95 and results.get('critical_failures', 0) == 0:
        print("\n🎉 Security validation completed successfully!")
        sys.exit(0)
    elif results.get('critical_failures', 0) > 0:
        print("\n💥 Critical security issues found!")
        sys.exit(2)
    else:
        print("\n⚠️ Security validation completed with warnings")
        sys.exit(1)

if __name__ == "__main__":
    main()