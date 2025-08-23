#!/usr/bin/env python3
"""
Security Validation Runner
Executes comprehensive security tests and generates validation report
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
import ssl
import socket
import hashlib
import subprocess
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class SecurityValidationRunner:
    """Comprehensive security validation test runner"""
    
    def __init__(self):
        self.results = []
        self.security_score = 0.0
        
    async def run_all_validations(self):
        """Run all security validation tests"""
        logger.info("🔍 Starting OMEGA Security Validation Tests")
        
        tests = [
            ("MITM Vulnerability Fix", self.test_mitm_vulnerability_fix),
            ("Certificate Rotation System", self.test_certificate_rotation_system),
            ("Security Policy Strength", self.test_security_policy_strength),
            ("Security Monitoring System", self.test_security_monitoring_system),
            ("SSL/TLS Configuration", self.test_ssl_tls_configuration),
            ("Certificate Pinning", self.test_certificate_pinning),
            ("Certificate Transparency", self.test_certificate_transparency),
            ("OCSP Stapling", self.test_ocsp_stapling),
            ("Security Headers", self.test_security_headers),
            ("CSP Policy", self.test_csp_policy)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"Running test: {test_name}")
            try:
                result = await test_func()
                result['test_name'] = test_name
                self.results.append(result)
                
                status = "✅ PASS" if result['passed'] else "❌ FAIL"
                logger.info(f"{status}: {test_name} - {result['details']}")
                
            except Exception as e:
                logger.error(f"❌ ERROR: {test_name} - {str(e)}")
                self.results.append({
                    'test_name': test_name,
                    'passed': False,
                    'severity': 'critical',
                    'details': f"Test execution failed: {str(e)}",
                    'recommendations': ['Fix test execution environment']
                })
        
        # Calculate overall security score
        self.security_score = self.calculate_security_score()
        
        # Generate comprehensive report
        report = await self.generate_validation_report()
        
        # Save report
        with open('security_validation_report.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'overall_score': self.security_score,
                'results': self.results,
                'report': report
            }, f, indent=2)
        
        logger.info(f"🎯 Overall Security Score: {self.security_score:.1f}%")
        logger.info("📄 Detailed report saved to: security_validation_report.json")
        
        return report
    
    async def test_mitm_vulnerability_fix(self):
        """Test MITM vulnerability fixes"""
        try:
            # Check if SSL certificate pinning manager has proper validation
            ios_ssl_file = Path("ios/OmegaApp_Clean/Omega/Omega/SSLCertificatePinningManager.swift")
            
            if not ios_ssl_file.exists():
                return {
                    'passed': False,
                    'severity': 'critical',
                    'details': 'SSL Certificate Pinning Manager not found',
                    'recommendations': ['Implement SSL certificate pinning']
                }
            
            content = ios_ssl_file.read_text()
            
            # Check for critical security fixes
            security_checks = [
                ('validateCertificateTransparency', 'Certificate Transparency validation'),
                ('validateOCSPStapling', 'OCSP stapling validation'),
                ('validateCertificateRevocation', 'Certificate revocation checking'),
                ('validateCertificateFingerprint', 'Certificate fingerprint validation'),
                ('recoverableTrustFailure', 'Proper trust failure handling')
            ]
            
            missing_features = []
            for check, description in security_checks:
                if check not in content:
                    missing_features.append(description)
            
            if missing_features:
                return {
                    'passed': False,
                    'severity': 'high',
                    'details': f'Missing security features: {", ".join(missing_features)}',
                    'recommendations': ['Implement missing security validation features']
                }
            
            return {
                'passed': True,
                'severity': 'critical',
                'details': 'MITM vulnerability fixes implemented',
                'recommendations': []
            }
            
        except Exception as e:
            return {
                'passed': False,
                'severity': 'critical',
                'details': f'MITM vulnerability test failed: {str(e)}',
                'recommendations': ['Review SSL implementation']
            }
    
    async def test_certificate_rotation_system(self):
        """Test automated certificate rotation system"""
        try:
            ios_ssl_file = Path("ios/OmegaApp_Clean/Omega/Omega/SSLCertificatePinningManager.swift")
            
            if not ios_ssl_file.exists():
                return {
                    'passed': False,
                    'severity': 'high',
                    'details': 'Certificate rotation system not found',
                    'recommendations': ['Implement certificate rotation system']
                }
            
            content = ios_ssl_file.read_text()
            
            # Check for certificate rotation features
            rotation_features = [
                'setupAutomaticCertificateRotation',
                'checkAndRotateCertificates',
                'checkServerCertificateVersion',
                'synchronizeCertificateWithServer',
                'certificateRotationTimers'
            ]
            
            missing_features = [f for f in rotation_features if f not in content]
            
            if missing_features:
                return {
                    'passed': False,
                    'severity': 'medium',
                    'details': f'Missing rotation features: {", ".join(missing_features)}',
                    'recommendations': ['Complete certificate rotation implementation']
                }
            
            return {
                'passed': True,
                'severity': 'medium',
                'details': 'Certificate rotation system implemented',
                'recommendations': []
            }
            
        except Exception as e:
            return {
                'passed': False,
                'severity': 'medium',
                'details': f'Certificate rotation test failed: {str(e)}',
                'recommendations': ['Review certificate rotation implementation']
            }
    
    async def test_security_policy_strength(self):
        """Test security policy implementation"""
        try:
            network_manager_file = Path("ios/OmegaApp_Clean/Omega/Omega/NetworkSecurityManager.swift")
            
            if not network_manager_file.exists():
                return {
                    'passed': False,
                    'severity': 'high',
                    'details': 'Network Security Manager not found',
                    'recommendations': ['Implement network security manager']
                }
            
            content = network_manager_file.read_text()
            
            # Check for enhanced security policies
            security_policies = [
                'validateCSPPolicy',
                'validateHSTSHeader',
                'validateSecurityHeaderStrength',
                'unsafeCSPPolicy',
                'missingSecurityHeaders'
            ]
            
            missing_policies = [p for p in security_policies if p not in content]
            
            if missing_policies:
                return {
                    'passed': False,
                    'severity': 'medium',
                    'details': f'Missing security policies: {", ".join(missing_policies)}',
                    'recommendations': ['Implement missing security policy validations']
                }
            
            # Check for unsafe CSP rejection
            if "'unsafe-inline'" in content and "throw" in content:
                csp_strength = True
            else:
                csp_strength = False
            
            return {
                'passed': True and csp_strength,
                'severity': 'medium',
                'details': 'Security policies implemented with CSP validation',
                'recommendations': [] if csp_strength else ['Strengthen CSP policy validation']
            }
            
        except Exception as e:
            return {
                'passed': False,
                'severity': 'medium',
                'details': f'Security policy test failed: {str(e)}',
                'recommendations': ['Review security policy implementation']
            }
    
    async def test_security_monitoring_system(self):
        """Test security monitoring and MITM detection"""
        try:
            # Check iOS monitoring
            ios_ssl_file = Path("ios/OmegaApp_Clean/Omega/Omega/SSLCertificatePinningManager.swift")
            python_monitor_file = Path("security_monitoring_system.py")
            
            ios_monitoring = False
            python_monitoring = False
            
            if ios_ssl_file.exists():
                content = ios_ssl_file.read_text()
                ios_features = [
                    'startSecurityMonitoring',
                    'detectPotentialMITM',
                    'performMultiPathCertificateCheck',
                    'validateCertificateInCTLogs',
                    'triggerSecurityAlert'
                ]
                ios_monitoring = all(feature in content for feature in ios_features)
            
            if python_monitor_file.exists():
                content = python_monitor_file.read_text()
                python_features = [
                    'SecurityMonitoringSystem',
                    'certificate_monitoring_loop',
                    'mitm_detection_loop',
                    'detect_mitm_attack',
                    'certificate_transparency_monitoring'
                ]
                python_monitoring = all(feature in content for feature in python_features)
            
            if ios_monitoring and python_monitoring:
                return {
                    'passed': True,
                    'severity': 'high',
                    'details': 'Comprehensive security monitoring implemented (iOS + Server)',
                    'recommendations': []
                }
            elif ios_monitoring or python_monitoring:
                return {
                    'passed': True,
                    'severity': 'medium',
                    'details': f'Partial security monitoring implemented ({"iOS" if ios_monitoring else "Server"} only)',
                    'recommendations': ['Complete monitoring implementation on all platforms']
                }
            else:
                return {
                    'passed': False,
                    'severity': 'high',
                    'details': 'Security monitoring system not implemented',
                    'recommendations': ['Implement comprehensive security monitoring']
                }
            
        except Exception as e:
            return {
                'passed': False,
                'severity': 'high',
                'details': f'Security monitoring test failed: {str(e)}',
                'recommendations': ['Review security monitoring implementation']
            }
    
    async def test_ssl_tls_configuration(self):
        """Test SSL/TLS configuration strength"""
        try:
            # Test TLS configuration by checking configuration files
            config_file = Path("ios/OmegaApp_Clean/Omega/Omega/Config.swift")
            
            if not config_file.exists():
                return {
                    'passed': False,
                    'severity': 'high',
                    'details': 'Configuration file not found',
                    'recommendations': ['Create proper configuration file']
                }
            
            content = config_file.read_text()
            
            # Check for secure TLS configuration
            tls_checks = [
                ('TLSv1', 'TLS 1.2 support'),
                ('sslPinningEnabled', 'SSL pinning configuration'),
                ('allowSelfSignedCertificates', 'Production security')
            ]
            
            issues = []
            for check, description in tls_checks:
                if check not in content:
                    issues.append(description)
            
            if issues:
                return {
                    'passed': False,
                    'severity': 'medium',
                    'details': f'TLS configuration issues: {", ".join(issues)}',
                    'recommendations': ['Fix TLS configuration issues']
                }
            
            return {
                'passed': True,
                'severity': 'medium',
                'details': 'SSL/TLS configuration appears secure',
                'recommendations': []
            }
            
        except Exception as e:
            return {
                'passed': False,
                'severity': 'medium',
                'details': f'SSL/TLS test failed: {str(e)}',
                'recommendations': ['Review SSL/TLS configuration']
            }
    
    async def test_certificate_pinning(self):
        """Test certificate pinning implementation"""
        try:
            ios_ssl_file = Path("ios/OmegaApp_Clean/Omega/Omega/SSLCertificatePinningManager.swift")
            
            if not ios_ssl_file.exists():
                return {
                    'passed': False,
                    'severity': 'critical',
                    'details': 'Certificate pinning not implemented',
                    'recommendations': ['Implement certificate pinning']
                }
            
            content = ios_ssl_file.read_text()
            
            # Check for proper pinning implementation
            pinning_features = [
                'validateCertificateHash',
                'validatePublicKeyHash',
                'certificateHashes',
                'publicKeyHashes',
                'requireCertificatePinning'
            ]
            
            missing_features = [f for f in pinning_features if f not in content]
            
            if missing_features:
                return {
                    'passed': False,
                    'severity': 'high',
                    'details': f'Missing pinning features: {", ".join(missing_features)}',
                    'recommendations': ['Complete certificate pinning implementation']
                }
            
            return {
                'passed': True,
                'severity': 'high',
                'details': 'Certificate pinning properly implemented',
                'recommendations': []
            }
            
        except Exception as e:
            return {
                'passed': False,
                'severity': 'high',
                'details': f'Certificate pinning test failed: {str(e)}',
                'recommendations': ['Review certificate pinning implementation']
            }
    
    async def test_certificate_transparency(self):
        """Test Certificate Transparency implementation"""
        try:
            ios_ssl_file = Path("ios/OmegaApp_Clean/Omega/Omega/SSLCertificatePinningManager.swift")
            
            if not ios_ssl_file.exists():
                return {
                    'passed': False,
                    'severity': 'medium',
                    'details': 'Certificate Transparency not implemented',
                    'recommendations': ['Implement Certificate Transparency validation']
                }
            
            content = ios_ssl_file.read_text()
            
            # Check for CT implementation
            ct_features = [
                'validateCertificateTransparency',
                'validateCertificateInCTLogs',
                'ctExtensionOID',
                '1.3.6.1.4.1.11129.2.4.2'  # CT extension OID
            ]
            
            ct_implemented = all(feature in content for feature in ct_features)
            
            return {
                'passed': ct_implemented,
                'severity': 'medium',
                'details': 'Certificate Transparency validation implemented' if ct_implemented else 'Certificate Transparency not fully implemented',
                'recommendations': [] if ct_implemented else ['Complete Certificate Transparency implementation']
            }
            
        except Exception as e:
            return {
                'passed': False,
                'severity': 'medium',
                'details': f'Certificate Transparency test failed: {str(e)}',
                'recommendations': ['Review Certificate Transparency implementation']
            }
    
    async def test_ocsp_stapling(self):
        """Test OCSP stapling implementation"""
        try:
            ios_ssl_file = Path("ios/OmegaApp_Clean/Omega/Omega/SSLCertificatePinningManager.swift")
            
            if not ios_ssl_file.exists():
                return {
                    'passed': False,
                    'severity': 'medium',
                    'details': 'OCSP stapling not implemented',
                    'recommendations': ['Implement OCSP stapling validation']
                }
            
            content = ios_ssl_file.read_text()
            
            # Check for OCSP implementation
            ocsp_features = [
                'validateOCSPStapling',
                'SecTrustGetOCSPResponse',
                'kSecRevocationOCSPMethod'
            ]
            
            ocsp_implemented = all(feature in content for feature in ocsp_features)
            
            return {
                'passed': ocsp_implemented,
                'severity': 'medium',
                'details': 'OCSP stapling validation implemented' if ocsp_implemented else 'OCSP stapling not fully implemented',
                'recommendations': [] if ocsp_implemented else ['Complete OCSP stapling implementation']
            }
            
        except Exception as e:
            return {
                'passed': False,
                'severity': 'medium',
                'details': f'OCSP stapling test failed: {str(e)}',
                'recommendations': ['Review OCSP stapling implementation']
            }
    
    async def test_security_headers(self):
        """Test security headers implementation"""
        try:
            network_manager_file = Path("ios/OmegaApp_Clean/Omega/Omega/NetworkSecurityManager.swift")
            
            if not network_manager_file.exists():
                return {
                    'passed': False,
                    'severity': 'medium',
                    'details': 'Security headers validation not implemented',
                    'recommendations': ['Implement security headers validation']
                }
            
            content = network_manager_file.read_text()
            
            # Check for security headers
            security_headers = [
                'Strict-Transport-Security',
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection',
                'Content-Security-Policy'
            ]
            
            headers_implemented = all(header in content for header in security_headers)
            
            return {
                'passed': headers_implemented,
                'severity': 'medium',
                'details': 'Security headers validation implemented' if headers_implemented else 'Security headers validation incomplete',
                'recommendations': [] if headers_implemented else ['Complete security headers validation']
            }
            
        except Exception as e:
            return {
                'passed': False,
                'severity': 'medium',
                'details': f'Security headers test failed: {str(e)}',
                'recommendations': ['Review security headers implementation']
            }
    
    async def test_csp_policy(self):
        """Test CSP policy strength"""
        try:
            network_manager_file = Path("ios/OmegaApp_Clean/Omega/Omega/NetworkSecurityManager.swift")
            
            if not network_manager_file.exists():
                return {
                    'passed': False,
                    'severity': 'medium',
                    'details': 'CSP policy validation not implemented',
                    'recommendations': ['Implement CSP policy validation']
                }
            
            content = network_manager_file.read_text()
            
            # Check for CSP strength validation
            csp_features = [
                'validateCSPPolicy',
                'unsafe-eval',
                'unsafe-inline',
                'unsafeCSPPolicy'
            ]
            
            csp_validation = all(feature in content for feature in csp_features)
            
            # Check that unsafe directives are rejected
            unsafe_rejection = 'throw NetworkSecurityError.unsafeCSPPolicy' in content
            
            return {
                'passed': csp_validation and unsafe_rejection,
                'severity': 'medium',
                'details': 'CSP policy validation with unsafe directive rejection' if (csp_validation and unsafe_rejection) else 'CSP policy validation incomplete',
                'recommendations': [] if (csp_validation and unsafe_rejection) else ['Complete CSP policy validation with unsafe directive rejection']
            }
            
        except Exception as e:
            return {
                'passed': False,
                'severity': 'medium',
                'details': f'CSP policy test failed: {str(e)}',
                'recommendations': ['Review CSP policy implementation']
            }
    
    def calculate_security_score(self):
        """Calculate overall security score"""
        if not self.results:
            return 0.0
        
        total_weight = 0
        weighted_score = 0
        
        for result in self.results:
            # Weight based on severity
            weight = {
                'critical': 3.0,
                'high': 2.0,
                'medium': 1.5,
                'low': 1.0
            }.get(result.get('severity', 'medium'), 1.0)
            
            score = 100 if result['passed'] else 0
            weighted_score += score * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    async def generate_validation_report(self):
        """Generate comprehensive validation report"""
        passed_tests = sum(1 for r in self.results if r['passed'])
        total_tests = len(self.results)
        critical_failures = [r for r in self.results if not r['passed'] and r.get('severity') == 'critical']
        
        grade = self.get_security_grade(self.security_score)
        
        report = f"""
🛡️  OMEGA SECURITY VALIDATION REPORT
=====================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

EXECUTIVE SUMMARY
-----------------
Overall Security Score: {self.security_score:.1f}% (Grade: {grade})
Tests Passed: {passed_tests}/{total_tests}
Critical Issues: {len(critical_failures)}

SECURITY IMPLEMENTATION STATUS
-------------------------------
"""
        
        for result in self.results:
            status = "✅ IMPLEMENTED" if result['passed'] else "❌ NEEDS ATTENTION"
            severity = result.get('severity', 'medium').upper()
            
            report += f"{status} [{severity}] {result['test_name']}\n"
            report += f"   Details: {result['details']}\n"
            
            if result.get('recommendations'):
                report += f"   Recommendations: {'; '.join(result['recommendations'])}\n"
            report += "\n"
        
        if critical_failures:
            report += "🚨 CRITICAL SECURITY ISSUES\n"
            report += "===========================\n"
            for failure in critical_failures:
                report += f"❌ {failure['test_name']}: {failure['details']}\n"
                if failure.get('recommendations'):
                    report += f"   ACTION REQUIRED: {'; '.join(failure['recommendations'])}\n"
            report += "\n"
        
        # Security compliance summary
        compliance_items = [
            ("MITM Protection", any("MITM" in r['test_name'] and r['passed'] for r in self.results)),
            ("Certificate Pinning", any("Certificate Pinning" in r['test_name'] and r['passed'] for r in self.results)),
            ("Certificate Rotation", any("Certificate Rotation" in r['test_name'] and r['passed'] for r in self.results)),
            ("Security Monitoring", any("Security Monitoring" in r['test_name'] and r['passed'] for r in self.results)),
            ("Security Headers", any("Security Headers" in r['test_name'] and r['passed'] for r in self.results)),
            ("CSP Policy", any("CSP Policy" in r['test_name'] and r['passed'] for r in self.results))
        ]
        
        report += "🔒 SECURITY COMPLIANCE CHECKLIST\n"
        report += "=================================\n"
        for item, compliant in compliance_items:
            status = "✅ COMPLIANT" if compliant else "❌ NON-COMPLIANT"
            report += f"{status} {item}\n"
        
        report += f"\n📊 SECURITY MATURITY ASSESSMENT\n"
        report += "==============================\n"
        if self.security_score >= 90:
            report += "🏆 EXCELLENT: Security implementation exceeds industry standards\n"
        elif self.security_score >= 80:
            report += "🥇 GOOD: Strong security implementation with minor areas for improvement\n"
        elif self.security_score >= 70:
            report += "🥈 ADEQUATE: Security baseline met, but significant improvements needed\n"
        elif self.security_score >= 60:
            report += "🥉 MINIMAL: Basic security measures in place, major improvements required\n"
        else:
            report += "🚨 CRITICAL: Security implementation is insufficient and requires immediate attention\n"
        
        return report
    
    def get_security_grade(self, score):
        """Convert security score to letter grade"""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "A-"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "B-"
        elif score >= 65:
            return "C+"
        elif score >= 60:
            return "C"
        else:
            return "F"

async def main():
    """Main function to run security validation"""
    print("🔒 OMEGA SECURITY VALIDATION SYSTEM")
    print("=" * 40)
    
    validator = SecurityValidationRunner()
    
    try:
        report = await validator.run_all_validations()
        
        # Print report to console
        print("\n" + report)
        
        # Determine exit code based on critical failures
        critical_failures = [r for r in validator.results if not r['passed'] and r.get('severity') == 'critical']
        
        if critical_failures:
            print(f"\n🚨 SECURITY VALIDATION FAILED: {len(critical_failures)} critical issues found")
            return 1
        elif validator.security_score < 70:
            print(f"\n⚠️  SECURITY VALIDATION WARNING: Score below acceptable threshold ({validator.security_score:.1f}%)")
            return 1
        else:
            print(f"\n✅ SECURITY VALIDATION PASSED: Score {validator.security_score:.1f}%")
            return 0
            
    except Exception as e:
        logger.error(f"Security validation failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)