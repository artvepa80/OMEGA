#!/usr/bin/env python3
"""
✅ OMEGA Pro AI Deployment Verification and Status Dashboard
Comprehensive verification of SSL/TLS and Akash Network implementation
"""

import click
import subprocess
import json
import os
import requests
import socket
import ssl
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

@click.group()
def verify_cli():
    """Deployment Verification CLI"""
    pass

@verify_cli.command()
def verify_ssl_infrastructure():
    """Verify SSL/TLS infrastructure implementation"""
    
    click.echo("🔐 Verifying SSL/TLS Infrastructure...")
    click.echo("=" * 50)
    
    results = {
        'ssl_certificates': False,
        'ssl_manager': False,
        'nginx_security': False,
        'monitoring': False,
        'docker_configs': False
    }
    
    # Check SSL certificates
    ssl_dir = Path("ssl")
    if ssl_dir.exists():
        cert_files = ['cert.pem', 'key.pem', 'bundle.pem', 'ssl_config.json']
        if all((ssl_dir / f).exists() for f in cert_files):
            click.echo("✅ SSL certificates: PRESENT")
            
            # Verify certificate validity
            try:
                result = subprocess.run(['python3', 'scripts/ssl_cert_manager.py', 'status'], 
                                      capture_output=True, text=True)
                if "VALID" in result.stdout:
                    click.echo("✅ SSL certificate status: VALID")
                    results['ssl_certificates'] = True
                else:
                    click.echo("⚠️ SSL certificate status: INVALID")
            except:
                click.echo("⚠️ SSL certificate verification failed")
        else:
            click.echo("❌ SSL certificates: MISSING FILES")
    else:
        click.echo("❌ SSL certificates: DIRECTORY NOT FOUND")
    
    # Check SSL certificate manager
    ssl_manager_path = Path("scripts/ssl_cert_manager.py")
    if ssl_manager_path.exists():
        click.echo("✅ SSL certificate manager: DEPLOYED")
        results['ssl_manager'] = True
    else:
        click.echo("❌ SSL certificate manager: NOT FOUND")
    
    # Check nginx security configurations
    nginx_configs = [
        'docker/nginx-ssl.conf',
        'docker/nginx-security-enhanced.conf',
        'docker/proxy_params'
    ]
    
    nginx_found = all(Path(config).exists() for config in nginx_configs)
    if nginx_found:
        click.echo("✅ Nginx security configurations: DEPLOYED")
        results['nginx_security'] = True
    else:
        click.echo("❌ Nginx security configurations: INCOMPLETE")
    
    # Check monitoring systems
    monitoring_scripts = [
        'scripts/ssl_monitor_service.py',
        'scripts/health_monitor_service.py',
        'scripts/monitoring_dashboard.py',
        'scripts/security_monitor.py'
    ]
    
    monitoring_found = all(Path(script).exists() for script in monitoring_scripts)
    if monitoring_found:
        click.echo("✅ Monitoring systems: DEPLOYED")
        results['monitoring'] = True
    else:
        click.echo("❌ Monitoring systems: INCOMPLETE")
    
    # Check Docker configurations
    docker_configs = [
        'Dockerfile.secure-api',
        'Dockerfile.secure-gpu',
        'docker/ssl-handler.sh',
        'docker/supervisord-ssl.conf',
        '.dockerignore'
    ]
    
    docker_found = all(Path(config).exists() for config in docker_configs)
    if docker_found:
        click.echo("✅ Docker security configurations: DEPLOYED")
        results['docker_configs'] = True
    else:
        click.echo("❌ Docker security configurations: INCOMPLETE")
    
    # Overall assessment
    click.echo("\n📊 SSL Infrastructure Assessment:")
    success_count = sum(results.values())
    total_count = len(results)
    percentage = (success_count / total_count) * 100
    
    if percentage >= 90:
        click.echo(f"✅ EXCELLENT: {success_count}/{total_count} components ({percentage:.1f}%)")
    elif percentage >= 70:
        click.echo(f"⚠️ GOOD: {success_count}/{total_count} components ({percentage:.1f}%)")
    else:
        click.echo(f"❌ NEEDS WORK: {success_count}/{total_count} components ({percentage:.1f}%)")
    
    return results

@verify_cli.command()
def verify_akash_deployment():
    """Verify Akash Network deployment configuration"""
    
    click.echo("🚀 Verifying Akash Network Deployment...")
    click.echo("=" * 50)
    
    results = {
        'deployment_manifests': False,
        'service_mesh_config': False,
        'health_checks': False,
        'security_policies': False,
        'akash_cli_tools': False
    }
    
    # Check deployment manifests
    manifests = [
        'deploy/secure-akash-deployment.yaml',
        'deploy/production-akash-secure.yaml',
        'config/secure-akash-deployment.yaml'
    ]
    
    manifest_found = any(Path(manifest).exists() for manifest in manifests)
    if manifest_found:
        click.echo("✅ Akash deployment manifests: PRESENT")
        results['deployment_manifests'] = True
    else:
        click.echo("❌ Akash deployment manifests: NOT FOUND")
    
    # Check service mesh configuration
    service_mesh_configs = [
        'config/service_mesh_security.json',
        'scripts/service_mesh_security.py'
    ]
    
    mesh_found = all(Path(config).exists() for config in service_mesh_configs)
    if mesh_found:
        click.echo("✅ Service mesh configuration: DEPLOYED")
        results['service_mesh_config'] = True
    else:
        click.echo("❌ Service mesh configuration: INCOMPLETE")
    
    # Check health check configuration
    health_config = Path('config/health_checks.json')
    if health_config.exists():
        click.echo("✅ Health check configuration: DEPLOYED")
        results['health_checks'] = True
        
        # Validate health check config
        try:
            with open(health_config, 'r') as f:
                config = json.load(f)
            
            services = config.get('health_checks', {})
            if len(services) >= 3:  # omega-api, omega-gpu, redis
                click.echo(f"✅ Health checks configured for {len(services)} services")
            else:
                click.echo(f"⚠️ Limited health checks: {len(services)} services")
        except:
            click.echo("⚠️ Health check configuration invalid")
    else:
        click.echo("❌ Health check configuration: NOT FOUND")
    
    # Check security policies
    security_scripts = [
        'scripts/secure_akash_deploy.py',
        'scripts/network_security_deploy.py'
    ]
    
    security_found = all(Path(script).exists() for script in security_scripts)
    if security_found:
        click.echo("✅ Security deployment tools: PRESENT")
        results['security_policies'] = True
    else:
        click.echo("❌ Security deployment tools: MISSING")
    
    # Check Akash CLI tools (optional)
    try:
        result = subprocess.run(['akash', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            click.echo("✅ Akash CLI: AVAILABLE")
            results['akash_cli_tools'] = True
        else:
            click.echo("⚠️ Akash CLI: NOT AVAILABLE (install for deployment)")
    except FileNotFoundError:
        click.echo("⚠️ Akash CLI: NOT INSTALLED (install for deployment)")
    
    # Overall assessment
    click.echo("\n📊 Akash Deployment Assessment:")
    success_count = sum(results.values())
    total_count = len(results)
    percentage = (success_count / total_count) * 100
    
    if percentage >= 90:
        click.echo(f"✅ EXCELLENT: {success_count}/{total_count} components ({percentage:.1f}%)")
    elif percentage >= 70:
        click.echo(f"⚠️ GOOD: {success_count}/{total_count} components ({percentage:.1f}%)")
    else:
        click.echo(f"❌ NEEDS WORK: {success_count}/{total_count} components ({percentage:.1f}%)")
    
    return results

@verify_cli.command()
def verify_network_security():
    """Verify network security implementation"""
    
    click.echo("🛡️ Verifying Network Security Implementation...")
    click.echo("=" * 50)
    
    results = {
        'tls_configuration': False,
        'security_headers': False,
        'rate_limiting': False,
        'firewall_rules': False,
        'monitoring': False
    }
    
    # Check TLS configuration files
    tls_configs = [
        'docker/nginx-security-enhanced.conf',
        'docker/proxy_params'
    ]
    
    tls_found = all(Path(config).exists() for config in tls_configs)
    if tls_found:
        # Verify TLS 1.2+ enforcement
        with open('docker/nginx-security-enhanced.conf', 'r') as f:
            content = f.read()
            if 'TLSv1.2 TLSv1.3' in content:
                click.echo("✅ TLS 1.2+ enforcement: CONFIGURED")
                results['tls_configuration'] = True
            else:
                click.echo("⚠️ TLS configuration: NEEDS REVIEW")
    else:
        click.echo("❌ TLS configuration: NOT FOUND")
    
    # Check security headers
    if tls_found:
        with open('docker/nginx-security-enhanced.conf', 'r') as f:
            content = f.read()
            security_headers = [
                'Strict-Transport-Security',
                'X-Frame-Options',
                'X-Content-Type-Options',
                'Content-Security-Policy'
            ]
            
            headers_found = sum(1 for header in security_headers if header in content)
            if headers_found >= 4:
                click.echo(f"✅ Security headers: {headers_found}/{len(security_headers)} implemented")
                results['security_headers'] = True
            else:
                click.echo(f"⚠️ Security headers: {headers_found}/{len(security_headers)} implemented")
    
    # Check rate limiting configuration
    if tls_found:
        with open('docker/nginx-security-enhanced.conf', 'r') as f:
            content = f.read()
            if 'limit_req_zone' in content and 'limit_conn_zone' in content:
                click.echo("✅ Rate limiting: CONFIGURED")
                results['rate_limiting'] = True
            else:
                click.echo("⚠️ Rate limiting: INCOMPLETE")
    
    # Check firewall setup script
    firewall_script = Path('scripts/setup_firewall.sh')
    if firewall_script.exists():
        click.echo("✅ Firewall configuration script: PRESENT")
        results['firewall_rules'] = True
    else:
        click.echo("❌ Firewall configuration script: NOT FOUND")
    
    # Check security monitoring
    security_monitor = Path('scripts/security_monitor.py')
    if security_monitor.exists():
        click.echo("✅ Security monitoring: DEPLOYED")
        results['monitoring'] = True
    else:
        click.echo("❌ Security monitoring: NOT FOUND")
    
    # Overall assessment
    click.echo("\n📊 Network Security Assessment:")
    success_count = sum(results.values())
    total_count = len(results)
    percentage = (success_count / total_count) * 100
    
    if percentage >= 90:
        click.echo(f"✅ EXCELLENT: {success_count}/{total_count} components ({percentage:.1f}%)")
    elif percentage >= 70:
        click.echo(f"⚠️ GOOD: {success_count}/{total_count} components ({percentage:.1f}%)")
    else:
        click.echo(f"❌ NEEDS WORK: {success_count}/{total_count} components ({percentage:.1f}%)")
    
    return results

@verify_cli.command()
def comprehensive_verification():
    """Run comprehensive verification of all components"""
    
    click.echo("🔍 OMEGA Pro AI - Comprehensive Deployment Verification")
    click.echo("=" * 60)
    click.echo(f"Timestamp: {datetime.now().isoformat()}")
    click.echo("=" * 60)
    
    # Run all verification components
    ssl_results = verify_ssl_infrastructure.callback()
    click.echo()
    
    akash_results = verify_akash_deployment.callback()
    click.echo()
    
    security_results = verify_network_security.callback()
    click.echo()
    
    # Generate comprehensive report
    all_results = {
        'ssl_infrastructure': ssl_results,
        'akash_deployment': akash_results,
        'network_security': security_results
    }
    
    # Calculate overall score
    total_checks = sum(len(category) for category in all_results.values())
    passed_checks = sum(sum(category.values()) for category in all_results.values())
    overall_percentage = (passed_checks / total_checks) * 100
    
    click.echo("📊 COMPREHENSIVE ASSESSMENT")
    click.echo("=" * 30)
    click.echo(f"Total Checks: {total_checks}")
    click.echo(f"Passed Checks: {passed_checks}")
    click.echo(f"Success Rate: {overall_percentage:.1f}%")
    
    if overall_percentage >= 90:
        click.echo("✅ DEPLOYMENT STATUS: EXCELLENT - Ready for production")
        deployment_status = "EXCELLENT"
    elif overall_percentage >= 80:
        click.echo("⚠️ DEPLOYMENT STATUS: GOOD - Minor improvements needed")
        deployment_status = "GOOD"
    elif overall_percentage >= 70:
        click.echo("⚠️ DEPLOYMENT STATUS: ACCEPTABLE - Some issues to address")
        deployment_status = "ACCEPTABLE"
    else:
        click.echo("❌ DEPLOYMENT STATUS: NEEDS WORK - Critical issues found")
        deployment_status = "NEEDS_WORK"
    
    # Save comprehensive report
    report = {
        'timestamp': datetime.now().isoformat(),
        'overall_score': overall_percentage,
        'deployment_status': deployment_status,
        'total_checks': total_checks,
        'passed_checks': passed_checks,
        'detailed_results': all_results,
        'recommendations': generate_recommendations(all_results)
    }
    
    report_file = Path('deployment_verification_report.json')
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    click.echo(f"\n📄 Detailed report saved to: {report_file}")
    
    return report

def generate_recommendations(results: Dict[str, Dict[str, bool]]) -> List[str]:
    """Generate recommendations based on verification results"""
    
    recommendations = []
    
    # SSL Infrastructure recommendations
    ssl_results = results['ssl_infrastructure']
    if not ssl_results.get('ssl_certificates'):
        recommendations.append("Generate SSL certificates using: python3 scripts/ssl_cert_manager.py generate")
    
    if not ssl_results.get('monitoring'):
        recommendations.append("Deploy monitoring systems using: python3 scripts/deploy_monitoring.py deploy-all")
    
    # Akash Deployment recommendations
    akash_results = results['akash_deployment']
    if not akash_results.get('akash_cli_tools'):
        recommendations.append("Install Akash CLI: curl -sSfL https://raw.githubusercontent.com/akash-network/node/master/install.sh | sh")
    
    if not akash_results.get('health_checks'):
        recommendations.append("Configure health checks: python3 scripts/service_mesh_security.py generate-configs")
    
    # Network Security recommendations
    security_results = results['network_security']
    if not security_results.get('firewall_rules'):
        recommendations.append("Setup firewall: sudo scripts/setup_firewall.sh")
    
    if not security_results.get('monitoring'):
        recommendations.append("Enable security monitoring: python3 scripts/security_monitor.py")
    
    # General recommendations
    if len(recommendations) == 0:
        recommendations.append("All components verified successfully! Ready for deployment.")
        recommendations.append("To deploy to Akash: python3 scripts/secure_akash_deploy.py deploy --wallet YOUR_WALLET --domain YOUR_DOMAIN --email YOUR_EMAIL")
    
    return recommendations

@verify_cli.command()
def deployment_status_dashboard():
    """Show real-time deployment status dashboard"""
    
    click.echo("🎯 OMEGA Pro AI - Deployment Status Dashboard")
    click.echo("=" * 50)
    
    # Show current status
    report_file = Path('deployment_verification_report.json')
    if report_file.exists():
        with open(report_file, 'r') as f:
            report = json.load(f)
        
        click.echo(f"Last Verification: {report['timestamp']}")
        click.echo(f"Overall Score: {report['overall_score']:.1f}%")
        click.echo(f"Status: {report['deployment_status']}")
        click.echo()
        
        # Show component status
        for category, results in report['detailed_results'].items():
            click.echo(f"{category.upper()}:")
            for component, status in results.items():
                status_icon = "✅" if status else "❌"
                click.echo(f"   {status_icon} {component.replace('_', ' ').title()}")
            click.echo()
        
        # Show recommendations
        if report['recommendations']:
            click.echo("RECOMMENDATIONS:")
            for i, rec in enumerate(report['recommendations'], 1):
                click.echo(f"   {i}. {rec}")
    else:
        click.echo("❌ No verification report found. Run comprehensive verification first:")
        click.echo("   python3 scripts/deployment_verification.py comprehensive-verification")

if __name__ == '__main__':
    verify_cli()