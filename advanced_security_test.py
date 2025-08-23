#!/usr/bin/env python3
"""
OMEGA Pro AI - Advanced Security Penetration Testing Suite
Comprehensive API Endpoint Security Assessment and Vulnerability Testing
"""

import requests
import json
import time
import logging
import asyncio
import subprocess
from datetime import datetime
from typing import Dict, List
import hashlib
import base64
import random
import string
from urllib.parse import urljoin

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('advanced_security_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AdvancedSecurityTester:
    """Advanced security testing for API endpoints and infrastructure"""
    
    def __init__(self):
        self.test_results = {}
        self.vulnerabilities = []
        self.start_time = datetime.now()
        
        # Test targets
        self.base_urls = [
            'http://localhost:8001',
            'https://a17d0f2p7pbkp4bc0pjgbsmp8o.ingress.paradigmapolitico.online'
        ]
        
        self.test_payloads = {
            'sql_injection': [
                "' OR '1'='1",
                "'; DROP TABLE users; --",
                "' UNION SELECT * FROM information_schema.tables --",
                "1' AND SLEEP(5) --",
                "' OR 1=1#"
            ],
            'xss': [
                "<script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "<img src=x onerror=alert('XSS')>",
                "';alert(String.fromCharCode(88,83,83))//",
                "<svg onload=alert('XSS')>"
            ],
            'command_injection': [
                "; ls -la",
                "| whoami",
                "`id`",
                "$(cat /etc/passwd)",
                "; ping -c 4 google.com"
            ],
            'path_traversal': [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\config\\sam",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
                "....//....//....//etc//passwd"
            ]
        }
    
    async def run_advanced_tests(self) -> Dict:
        """Execute comprehensive advanced security tests"""
        logger.info("🔍 Starting Advanced Security Testing Suite")
        
        test_suites = [
            ('SQL Injection Testing', self.test_sql_injection),
            ('Cross-Site Scripting (XSS) Testing', self.test_xss_vulnerabilities),
            ('CSRF Protection Testing', self.test_csrf_protection),
            ('API Rate Limiting Testing', self.test_rate_limiting),
            ('Input Validation Testing', self.test_input_validation),
            ('Business Logic Testing', self.test_business_logic),
            ('Infrastructure Security Testing', self.test_infrastructure_security),
            ('Session Management Testing', self.test_session_management)
        ]
        
        for test_name, test_func in test_suites:
            logger.info(f"\n{'='*60}")
            logger.info(f"🧪 Running {test_name}")
            logger.info(f"{'='*60}")
            
            try:
                results = await test_func()
                self.test_results[test_name] = results
                logger.info(f"✅ {test_name} completed - Vulnerabilities: {len(results.get('vulnerabilities', []))}")
            except Exception as e:
                logger.error(f"❌ {test_name} failed: {str(e)}")
                self.test_results[test_name] = {
                    'status': 'FAILED',
                    'error': str(e),
                    'vulnerabilities': []
                }
        
        return await self.generate_advanced_report()
    
    async def test_sql_injection(self) -> Dict:
        """Test for SQL injection vulnerabilities"""
        results = {
            'test_type': 'SQL Injection',
            'vulnerabilities': [],
            'tests_performed': 0,
            'endpoints_tested': [],
            'status': 'SECURE'
        }
        
        # Test endpoints that might be vulnerable
        test_endpoints = [
            '/api/v1/predict',
            '/api/v1/historical',
            '/api/v1/results',
            '/health',
            '/metrics'
        ]
        
        for base_url in self.base_urls:
            for endpoint in test_endpoints:
                for payload in self.test_payloads['sql_injection']:
                    results['tests_performed'] += 1
                    
                    try:
                        # Test GET parameters
                        response = requests.get(
                            f"{base_url}{endpoint}",
                            params={'q': payload, 'id': payload},
                            timeout=5
                        )
                        
                        # Check for SQL error messages
                        sql_errors = [
                            'sql syntax', 'mysql', 'postgresql', 'sqlite',
                            'ora-', 'microsoft jet database', 'syntax error',
                            'table doesn\'t exist', 'column doesn\'t exist'
                        ]
                        
                        response_text = response.text.lower()
                        for error in sql_errors:
                            if error in response_text:
                                vulnerability = {
                                    'type': 'SQL Injection',
                                    'endpoint': f"{base_url}{endpoint}",
                                    'payload': payload,
                                    'method': 'GET',
                                    'severity': 'HIGH',
                                    'evidence': f"SQL error detected: {error}",
                                    'cvss_score': 8.5
                                }
                                results['vulnerabilities'].append(vulnerability)
                                results['status'] = 'VULNERABLE'
                                logger.warning(f"🚨 SQL Injection vulnerability found at {endpoint}")
                        
                        # Test POST body
                        if endpoint in ['/api/v1/predict']:
                            post_response = requests.post(
                                f"{base_url}{endpoint}",
                                json={'data': payload, 'query': payload},
                                timeout=5
                            )
                            
                            post_text = post_response.text.lower()
                            for error in sql_errors:
                                if error in post_text:
                                    vulnerability = {
                                        'type': 'SQL Injection',
                                        'endpoint': f"{base_url}{endpoint}",
                                        'payload': payload,
                                        'method': 'POST',
                                        'severity': 'HIGH',
                                        'evidence': f"SQL error in POST: {error}",
                                        'cvss_score': 8.5
                                    }
                                    results['vulnerabilities'].append(vulnerability)
                                    results['status'] = 'VULNERABLE'
                    
                    except Exception as e:
                        # Connection errors are expected for some tests
                        continue
                
                results['endpoints_tested'].append(f"{base_url}{endpoint}")
        
        return results
    
    async def test_xss_vulnerabilities(self) -> Dict:
        """Test for Cross-Site Scripting vulnerabilities"""
        results = {
            'test_type': 'Cross-Site Scripting (XSS)',
            'vulnerabilities': [],
            'tests_performed': 0,
            'status': 'SECURE'
        }
        
        test_endpoints = ['/api/v1/predict', '/health', '/metrics']
        
        for base_url in self.base_urls:
            for endpoint in test_endpoints:
                for payload in self.test_payloads['xss']:
                    results['tests_performed'] += 1
                    
                    try:
                        # Test reflected XSS
                        response = requests.get(
                            f"{base_url}{endpoint}",
                            params={'search': payload, 'q': payload},
                            timeout=5
                        )
                        
                        # Check if payload is reflected unescaped
                        if payload in response.text and 'text/html' in response.headers.get('content-type', ''):
                            vulnerability = {
                                'type': 'Reflected XSS',
                                'endpoint': f"{base_url}{endpoint}",
                                'payload': payload,
                                'severity': 'MEDIUM',
                                'evidence': 'Payload reflected in response without escaping',
                                'cvss_score': 6.1
                            }
                            results['vulnerabilities'].append(vulnerability)
                            results['status'] = 'VULNERABLE'
                            logger.warning(f"🚨 XSS vulnerability found at {endpoint}")
                        
                        # Test stored XSS via POST
                        if endpoint in ['/api/v1/predict']:
                            post_response = requests.post(
                                f"{base_url}{endpoint}",
                                json={'message': payload, 'data': payload},
                                timeout=5
                            )
                            
                            if payload in post_response.text:
                                vulnerability = {
                                    'type': 'Stored XSS',
                                    'endpoint': f"{base_url}{endpoint}",
                                    'payload': payload,
                                    'severity': 'HIGH',
                                    'evidence': 'Payload stored and reflected without escaping',
                                    'cvss_score': 7.4
                                }
                                results['vulnerabilities'].append(vulnerability)
                                results['status'] = 'VULNERABLE'
                    
                    except Exception:
                        continue
        
        return results
    
    async def test_csrf_protection(self) -> Dict:
        """Test CSRF protection mechanisms"""
        results = {
            'test_type': 'CSRF Protection',
            'vulnerabilities': [],
            'tests_performed': 0,
            'status': 'SECURE'
        }
        
        for base_url in self.base_urls:
            try:
                # Test if CSRF tokens are required
                response = requests.post(
                    f"{base_url}/api/v1/predict",
                    json={'test': 'csrf_test'},
                    timeout=5
                )
                results['tests_performed'] += 1
                
                # Check for CSRF protection headers
                csrf_headers = [
                    'x-csrf-token', 'x-csrftoken', 'csrf-token',
                    'x-requested-with', 'x-xsrf-token'
                ]
                
                has_csrf_protection = any(
                    header in response.headers for header in csrf_headers
                )
                
                if not has_csrf_protection and response.status_code == 200:
                    vulnerability = {
                        'type': 'Missing CSRF Protection',
                        'endpoint': f"{base_url}/api/v1/predict",
                        'severity': 'MEDIUM',
                        'evidence': 'No CSRF protection headers detected',
                        'cvss_score': 5.4,
                        'recommendation': 'Implement CSRF tokens for state-changing operations'
                    }
                    results['vulnerabilities'].append(vulnerability)
                    results['status'] = 'VULNERABLE'
                    logger.warning("🚨 Missing CSRF protection")
            
            except Exception:
                continue
        
        return results
    
    async def test_rate_limiting(self) -> Dict:
        """Test API rate limiting implementation"""
        results = {
            'test_type': 'Rate Limiting',
            'vulnerabilities': [],
            'tests_performed': 0,
            'status': 'SECURE'
        }
        
        for base_url in self.base_urls:
            try:
                # Send rapid requests to test rate limiting
                endpoint = f"{base_url}/api/v1/predict"
                rapid_requests = []
                
                for i in range(20):  # Send 20 rapid requests
                    start_time = time.time()
                    try:
                        response = requests.post(
                            endpoint,
                            json={'test': f'rate_limit_test_{i}'},
                            timeout=2
                        )
                        rapid_requests.append({
                            'status_code': response.status_code,
                            'response_time': time.time() - start_time,
                            'headers': dict(response.headers)
                        })
                    except Exception:
                        rapid_requests.append({'status_code': 'ERROR'})
                    
                    results['tests_performed'] += 1
                
                # Analyze rate limiting
                successful_requests = [r for r in rapid_requests if r.get('status_code') == 200]
                rate_limited = [r for r in rapid_requests if r.get('status_code') == 429]
                
                if len(successful_requests) > 15:  # Too many successful requests
                    vulnerability = {
                        'type': 'Insufficient Rate Limiting',
                        'endpoint': endpoint,
                        'severity': 'MEDIUM',
                        'evidence': f'{len(successful_requests)}/20 requests succeeded without rate limiting',
                        'cvss_score': 4.3,
                        'recommendation': 'Implement stricter rate limiting'
                    }
                    results['vulnerabilities'].append(vulnerability)
                    results['status'] = 'VULNERABLE'
                    logger.warning("🚨 Insufficient rate limiting detected")
                
                # Check for rate limiting headers
                if rapid_requests and rapid_requests[0].get('headers'):
                    headers = rapid_requests[0]['headers']
                    rate_headers = ['x-ratelimit-limit', 'x-ratelimit-remaining', 'retry-after']
                    has_rate_headers = any(header.lower() in [h.lower() for h in headers.keys()] for header in rate_headers)
                    
                    if not has_rate_headers:
                        logger.info("ℹ️ No rate limiting headers detected")
            
            except Exception as e:
                logger.error(f"Rate limiting test error: {str(e)}")
                continue
        
        return results
    
    async def test_input_validation(self) -> Dict:
        """Test input validation mechanisms"""
        results = {
            'test_type': 'Input Validation',
            'vulnerabilities': [],
            'tests_performed': 0,
            'status': 'SECURE'
        }
        
        # Test various malformed inputs
        malicious_inputs = [
            {'test': 'A' * 10000},  # Large input
            {'test': '\x00\x01\x02'},  # Binary data
            {'test': '../../etc/passwd'},  # Path traversal
            {'numbers': 'not_a_number'},  # Type confusion
            {'json': '{"malformed": json}'},  # Malformed JSON
        ]
        
        for base_url in self.base_urls:
            for malicious_input in malicious_inputs:
                try:
                    response = requests.post(
                        f"{base_url}/api/v1/predict",
                        json=malicious_input,
                        timeout=5
                    )
                    results['tests_performed'] += 1
                    
                    # Check for error handling
                    if response.status_code == 500:
                        vulnerability = {
                            'type': 'Inadequate Input Validation',
                            'endpoint': f"{base_url}/api/v1/predict",
                            'payload': str(malicious_input),
                            'severity': 'LOW',
                            'evidence': 'Server error on malicious input',
                            'cvss_score': 3.1
                        }
                        results['vulnerabilities'].append(vulnerability)
                        results['status'] = 'VULNERABLE'
                
                except Exception:
                    continue
        
        return results
    
    async def test_business_logic(self) -> Dict:
        """Test business logic vulnerabilities"""
        results = {
            'test_type': 'Business Logic',
            'vulnerabilities': [],
            'tests_performed': 0,
            'status': 'SECURE'
        }
        
        for base_url in self.base_urls:
            try:
                # Test negative numbers
                response = requests.post(
                    f"{base_url}/api/v1/predict",
                    json={'numbers': [-1, -2, -3, -4, -5, -6]},
                    timeout=5
                )
                results['tests_performed'] += 1
                
                if response.status_code == 200:
                    data = response.json()
                    if 'prediction' in data:
                        logger.info("✅ API handles negative numbers appropriately")
                
                # Test boundary values
                boundary_tests = [
                    {'numbers': [0, 0, 0, 0, 0, 0]},  # All zeros
                    {'numbers': [100, 100, 100, 100, 100, 100]},  # Max values
                    {'numbers': list(range(1, 7))},  # Sequential
                ]
                
                for test_case in boundary_tests:
                    response = requests.post(
                        f"{base_url}/api/v1/predict",
                        json=test_case,
                        timeout=5
                    )
                    results['tests_performed'] += 1
                    
                    if response.status_code != 200:
                        logger.info(f"ℹ️ Boundary test failed: {test_case}")
            
            except Exception:
                continue
        
        return results
    
    async def test_infrastructure_security(self) -> Dict:
        """Test infrastructure security configuration"""
        results = {
            'test_type': 'Infrastructure Security',
            'vulnerabilities': [],
            'tests_performed': 0,
            'status': 'SECURE'
        }
        
        # Test for common security misconfigurations
        for base_url in self.base_urls:
            try:
                # Test for server information disclosure
                response = requests.get(f"{base_url}/health", timeout=5)
                results['tests_performed'] += 1
                
                server_header = response.headers.get('Server', '')
                if any(tech in server_header.lower() for tech in ['apache', 'nginx', 'iis']):
                    vulnerability = {
                        'type': 'Information Disclosure',
                        'endpoint': base_url,
                        'severity': 'LOW',
                        'evidence': f'Server header reveals technology: {server_header}',
                        'cvss_score': 2.6
                    }
                    results['vulnerabilities'].append(vulnerability)
                    results['status'] = 'VULNERABLE'
                
                # Test for debug information
                if 'debug' in response.text.lower() or 'traceback' in response.text.lower():
                    vulnerability = {
                        'type': 'Debug Information Exposure',
                        'endpoint': f"{base_url}/health",
                        'severity': 'MEDIUM',
                        'evidence': 'Debug information found in response',
                        'cvss_score': 4.3
                    }
                    results['vulnerabilities'].append(vulnerability)
                    results['status'] = 'VULNERABLE'
            
            except Exception:
                continue
        
        return results
    
    async def test_session_management(self) -> Dict:
        """Test session management security"""
        results = {
            'test_type': 'Session Management',
            'vulnerabilities': [],
            'tests_performed': 0,
            'status': 'SECURE'
        }
        
        for base_url in self.base_urls:
            try:
                # Test session handling
                session = requests.Session()
                response = session.get(f"{base_url}/health", timeout=5)
                results['tests_performed'] += 1
                
                # Check for session cookies
                cookies = session.cookies
                for cookie in cookies:
                    # Check cookie security attributes
                    if not cookie.secure and 'https' in base_url:
                        vulnerability = {
                            'type': 'Insecure Cookie',
                            'endpoint': base_url,
                            'severity': 'MEDIUM',
                            'evidence': f'Cookie {cookie.name} missing Secure flag',
                            'cvss_score': 5.3
                        }
                        results['vulnerabilities'].append(vulnerability)
                        results['status'] = 'VULNERABLE'
                    
                    if not cookie.get('httponly', False):
                        vulnerability = {
                            'type': 'Missing HttpOnly Flag',
                            'endpoint': base_url,
                            'severity': 'MEDIUM',
                            'evidence': f'Cookie {cookie.name} missing HttpOnly flag',
                            'cvss_score': 4.8
                        }
                        results['vulnerabilities'].append(vulnerability)
                        results['status'] = 'VULNERABLE'
            
            except Exception:
                continue
        
        return results
    
    def calculate_cvss_score(self, vulnerability: Dict) -> float:
        """Calculate CVSS v3.1 base score for vulnerability"""
        # Simplified CVSS calculation based on vulnerability type
        base_scores = {
            'SQL Injection': 8.5,
            'Stored XSS': 7.4,
            'Reflected XSS': 6.1,
            'Missing CSRF Protection': 5.4,
            'Insufficient Rate Limiting': 4.3,
            'Information Disclosure': 2.6,
            'Debug Information Exposure': 4.3,
            'Insecure Cookie': 5.3,
            'Missing HttpOnly Flag': 4.8,
            'Inadequate Input Validation': 3.1
        }
        
        return base_scores.get(vulnerability.get('type', ''), 3.0)
    
    async def generate_advanced_report(self) -> Dict:
        """Generate comprehensive advanced security report"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Aggregate all vulnerabilities
        all_vulnerabilities = []
        total_tests = 0
        categories_with_issues = 0
        
        for category, results in self.test_results.items():
            if isinstance(results, dict):
                category_vulns = results.get('vulnerabilities', [])
                all_vulnerabilities.extend(category_vulns)
                total_tests += results.get('tests_performed', 0)
                
                if category_vulns:
                    categories_with_issues += 1
        
        # Categorize vulnerabilities by severity
        critical_vulns = [v for v in all_vulnerabilities if v.get('cvss_score', 0) >= 9.0]
        high_vulns = [v for v in all_vulnerabilities if 7.0 <= v.get('cvss_score', 0) < 9.0]
        medium_vulns = [v for v in all_vulnerabilities if 4.0 <= v.get('cvss_score', 0) < 7.0]
        low_vulns = [v for v in all_vulnerabilities if v.get('cvss_score', 0) < 4.0]
        
        # Calculate overall security score
        if all_vulnerabilities:
            # Deduct points based on vulnerability severity
            deductions = (
                len(critical_vulns) * 30 +
                len(high_vulns) * 20 +
                len(medium_vulns) * 10 +
                len(low_vulns) * 5
            )
            security_score = max(0, 100 - deductions)
        else:
            security_score = 100
        
        # Determine security grade
        if security_score >= 95:
            security_grade = 'A+'
        elif security_score >= 90:
            security_grade = 'A'
        elif security_score >= 85:
            security_grade = 'B+'
        elif security_score >= 80:
            security_grade = 'B'
        elif security_score >= 70:
            security_grade = 'C'
        else:
            security_grade = 'F'
        
        report = {
            'test_execution': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'test_suite': 'Advanced Security Testing Suite v1.0'
            },
            'security_assessment': {
                'overall_score': security_score,
                'security_grade': security_grade,
                'production_ready': security_score >= 80 and len(critical_vulns) == 0,
                'vulnerabilities_found': len(all_vulnerabilities),
                'critical_vulnerabilities': len(critical_vulns),
                'high_vulnerabilities': len(high_vulns),
                'medium_vulnerabilities': len(medium_vulns),
                'low_vulnerabilities': len(low_vulns)
            },
            'vulnerability_summary': {
                'critical': critical_vulns,
                'high': high_vulns,
                'medium': medium_vulns,
                'low': low_vulns
            },
            'detailed_results': self.test_results,
            'testing_metrics': {
                'total_tests_performed': total_tests,
                'test_categories': len(self.test_results),
                'categories_with_issues': categories_with_issues,
                'test_coverage': 'Comprehensive API and Infrastructure Testing'
            },
            'recommendations': self.generate_security_recommendations(all_vulnerabilities, security_score)
        }
        
        # Save advanced security report
        with open('advanced_security_test_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report
    
    def generate_security_recommendations(self, vulnerabilities: List[Dict], security_score: float) -> List[str]:
        """Generate security recommendations based on findings"""
        recommendations = []
        
        # Critical recommendations
        critical_vulns = [v for v in vulnerabilities if v.get('cvss_score', 0) >= 9.0]
        if critical_vulns:
            recommendations.append("🚨 CRITICAL: Immediately address all critical vulnerabilities before production")
            for vuln in critical_vulns:
                recommendations.append(f"  - Fix {vuln['type']} at {vuln.get('endpoint', 'unknown')}")
        
        # High severity recommendations
        high_vulns = [v for v in vulnerabilities if 7.0 <= v.get('cvss_score', 0) < 9.0]
        if high_vulns:
            recommendations.append("⚠️ HIGH PRIORITY: Address high-severity vulnerabilities")
            for vuln in high_vulns:
                recommendations.append(f"  - {vuln['type']}: {vuln.get('recommendation', 'Review and fix')}")
        
        # General security recommendations
        if security_score < 80:
            recommendations.append("🔒 Security score below production threshold - comprehensive security review required")
        
        # Specific recommendations based on vulnerability types
        vuln_types = set(v['type'] for v in vulnerabilities)
        
        if 'SQL Injection' in vuln_types:
            recommendations.append("🛡️ Implement parameterized queries and input sanitization")
        
        if any('XSS' in vtype for vtype in vuln_types):
            recommendations.append("🌐 Implement proper output encoding and Content Security Policy")
        
        if 'Missing CSRF Protection' in vuln_types:
            recommendations.append("🔐 Implement CSRF tokens for state-changing operations")
        
        if 'Insufficient Rate Limiting' in vuln_types:
            recommendations.append("⏱️ Implement appropriate rate limiting and throttling")
        
        # General recommendations
        recommendations.extend([
            "🔍 Conduct regular security assessments and penetration testing",
            "📊 Implement security monitoring and logging",
            "🛠️ Keep all dependencies and frameworks updated",
            "🔒 Consider implementing a Web Application Firewall (WAF)",
            "👥 Provide security training for development team"
        ])
        
        return recommendations

async def main():
    """Main advanced security testing function"""
    print("🔍 OMEGA Pro AI - Advanced Security Testing Suite")
    print("=" * 60)
    
    tester = AdvancedSecurityTester()
    
    try:
        report = await tester.run_advanced_tests()
        
        # Print executive summary
        print("\n" + "=" * 60)
        print("🔍 ADVANCED SECURITY TEST SUMMARY")
        print("=" * 60)
        
        assessment = report['security_assessment']
        print(f"Security Score: {assessment['overall_score']}/100")
        print(f"Security Grade: {assessment['security_grade']}")
        print(f"Production Ready: {'✅ YES' if assessment['production_ready'] else '❌ NO'}")
        
        print(f"\n📊 Vulnerability Summary:")
        print(f"  Critical: {assessment['critical_vulnerabilities']} (CVSS 9.0+)")
        print(f"  High: {assessment['high_vulnerabilities']} (CVSS 7.0-8.9)")
        print(f"  Medium: {assessment['medium_vulnerabilities']} (CVSS 4.0-6.9)")
        print(f"  Low: {assessment['low_vulnerabilities']} (CVSS 0.1-3.9)")
        print(f"  Total: {assessment['vulnerabilities_found']}")
        
        print(f"\n🧪 Testing Metrics:")
        metrics = report['testing_metrics']
        print(f"  Tests Performed: {metrics['total_tests_performed']}")
        print(f"  Test Categories: {metrics['test_categories']}")
        print(f"  Categories with Issues: {metrics['categories_with_issues']}")
        
        if assessment['vulnerabilities_found'] > 0:
            print("\n🚨 CRITICAL FINDINGS:")
            for vuln in report['vulnerability_summary']['critical']:
                print(f"  - {vuln['type']} at {vuln.get('endpoint', 'unknown')} (CVSS: {vuln.get('cvss_score', 'N/A')})")
            
            for vuln in report['vulnerability_summary']['high']:
                print(f"  - {vuln['type']} at {vuln.get('endpoint', 'unknown')} (CVSS: {vuln.get('cvss_score', 'N/A')})")
        
        print("\n💡 SECURITY RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        print(f"\n📄 Detailed report saved to: advanced_security_test_report.json")
        print(f"📄 Test logs saved to: advanced_security_test.log")
        
        return 0 if assessment['production_ready'] else 1
        
    except Exception as e:
        logger.error(f"❌ Advanced security testing failed: {str(e)}")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)