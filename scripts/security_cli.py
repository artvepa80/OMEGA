#!/usr/bin/env python3
"""
🔒 OMEGA Security CLI - Herramienta de línea de comandos para seguridad
"""

import asyncio
import click
import json
import sys
from pathlib import Path
from datetime import datetime

# Añadir src al path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from security.security_manager import SecurityManager
from security.vulnerability_scanner import VulnerabilityScanner

@click.group()
def security_cli():
    """OMEGA Security Command Line Interface"""
    pass

@security_cli.group()
def scan():
    """Security scanning commands"""
    pass

@scan.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output file for the report')
@click.option('--format', '-f', type=click.Choice(['json', 'markdown']), 
              default='json', help='Output format')
@click.option('--severity', '-s', 
              type=click.Choice(['info', 'low', 'medium', 'high', 'critical']),
              help='Minimum severity level to report')
def vulnerabilities(project_path, output, format, severity):
    """Scan project for security vulnerabilities"""
    click.echo(f"🔍 Scanning {project_path} for vulnerabilities...")
    
    async def run_scan():
        scanner = VulnerabilityScanner()
        results = await scanner.scan_project(project_path)
        
        # Filtrar por severidad si se especifica
        if severity:
            severity_order = ['info', 'low', 'medium', 'high', 'critical']
            min_level = severity_order.index(severity)
            
            filtered_vulns = []
            for vuln in results['vulnerabilities']:
                vuln_level = severity_order.index(vuln['severity'])
                if vuln_level >= min_level:
                    filtered_vulns.append(vuln)
            
            results['vulnerabilities'] = filtered_vulns
            results['summary']['total_vulnerabilities'] = len(filtered_vulns)
        
        if format == 'json':
            output_content = json.dumps(results, indent=2, default=str)
        else:  # markdown
            output_content = await scanner.generate_security_report(results)
        
        if output:
            with open(output, 'w') as f:
                f.write(output_content)
            click.echo(f"📄 Report saved to {output}")
        else:
            click.echo(output_content)
        
        # Resumen en CLI
        summary = results['summary']
        click.echo(f"\n📊 Scan Summary:")
        click.echo(f"   Security Score: {summary['security_score']}/100")
        click.echo(f"   Risk Level: {summary['risk_level']}")
        click.echo(f"   Total Vulnerabilities: {summary['total_vulnerabilities']}")
        
        if summary['security_score'] < 70:
            click.echo("⚠️  Security score is below recommended threshold (70)")
            sys.exit(1)
    
    asyncio.run(run_scan())

@security_cli.group()
def auth():
    """Authentication and token management"""
    pass

@auth.command()
@click.argument('user_id')
@click.option('--permissions', '-p', multiple=True, 
              help='User permissions (can specify multiple)')
@click.option('--expires', '-e', type=int, default=24,
              help='Token expiry in hours (default: 24)')
@click.option('--ip', help='Bind token to specific IP address')
def create_token(user_id, permissions, expires, ip):
    """Create JWT token for user"""
    security_manager = SecurityManager()
    security_manager.config['token_expiry_hours'] = expires
    
    tokens = security_manager.create_jwt_token(
        user_id=user_id,
        permissions=list(permissions),
        ip_address=ip
    )
    
    click.echo(f"✅ Token created for user: {user_id}")
    click.echo(f"Access Token: {tokens['access_token']}")
    click.echo(f"Refresh Token: {tokens['refresh_token']}")
    click.echo(f"Expires in: {expires} hours")
    
    if permissions:
        click.echo(f"Permissions: {', '.join(permissions)}")
    if ip:
        click.echo(f"Bound to IP: {ip}")

@auth.command()
@click.argument('token')
@click.option('--ip', help='IP address to verify against')
def verify_token(token, ip):
    """Verify JWT token"""
    security_manager = SecurityManager()
    
    result = security_manager.verify_jwt_token(token, ip_address=ip)
    
    if result['valid']:
        click.echo("✅ Token is valid")
        click.echo(f"User ID: {result['user_id']}")
        click.echo(f"Token Type: {result['token_type']}")
        click.echo(f"Permissions: {', '.join(result.get('permissions', []))}")
    else:
        click.echo(f"❌ Token is invalid: {result['error']}")
        sys.exit(1)

@auth.command()
@click.argument('user_id')
@click.option('--token-type', '-t', type=click.Choice(['access', 'refresh', 'all']),
              default='all', help='Type of tokens to revoke')
def revoke_token(user_id, token_type):
    """Revoke user tokens"""
    security_manager = SecurityManager()
    
    revoked = security_manager.revoke_token(user_id, token_type)
    
    if revoked:
        click.echo(f"✅ Revoked {token_type} tokens for user: {user_id}")
    else:
        click.echo(f"❌ No tokens found for user: {user_id}")

@security_cli.group()
def validate():
    """Input validation commands"""
    pass

@validate.command()
@click.argument('input_text')
def input(input_text):
    """Validate input for security threats"""
    from security.security_manager import InputValidator
    
    validator = InputValidator()
    result = validator.validate_string(input_text)
    
    if result['valid']:
        click.echo("✅ Input is safe")
    else:
        click.echo("⚠️  Security threats detected:")
        for threat in result['threats']:
            click.echo(f"   - {threat}")
        click.echo(f"Sanitized: {result['sanitized']}")

@validate.command()
@click.argument('password')
def password(password):
    """Validate password strength"""
    security_manager = SecurityManager()
    result = security_manager.validate_password_strength(password)
    
    click.echo(f"Password Strength: {result['strength']}")
    click.echo(f"Score: {result['score']}/100")
    
    if result['valid']:
        click.echo("✅ Password meets security requirements")
    else:
        click.echo("❌ Password issues:")
        for issue in result['issues']:
            click.echo(f"   - {issue}")

@security_cli.group()
def audit():
    """Audit and monitoring commands"""
    pass

@audit.command()
@click.option('--hours', '-h', type=int, default=24,
              help='Hours to look back (default: 24)')
@click.option('--user', '-u', help='Filter by user ID')
@click.option('--event-type', '-t', 
              type=click.Choice(['login', 'logout', 'api_access', 'prediction_request',
                               'config_change', 'security_violation']),
              help='Filter by event type')
@click.option('--format', '-f', type=click.Choice(['json', 'table']),
              default='table', help='Output format')
def events(hours, user, event_type, format):
    """View audit events"""
    security_manager = SecurityManager()
    
    # Simular algunos eventos para demostración
    import time
    from security.security_manager import AuditEventType
    
    if not security_manager.audit_events:
        click.echo("No audit events found. Run some operations first.")
        return
    
    events = security_manager.get_audit_events(
        limit=50,
        hours_back=hours,
        user_id=user,
        event_type=AuditEventType(event_type) if event_type else None
    )
    
    if format == 'json':
        click.echo(json.dumps(events, indent=2, default=str))
    else:
        click.echo(f"📋 Audit Events (last {hours} hours):")
        click.echo("-" * 80)
        
        for event in events:
            timestamp = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
            click.echo(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} | "
                      f"{event['event_type']:15} | "
                      f"{event['user_id'] or 'anonymous':12} | "
                      f"{event['result']:8} | "
                      f"{event['resource']}")

@audit.command()
def summary():
    """Show security summary"""
    security_manager = SecurityManager()
    summary = security_manager.get_security_summary()
    
    click.echo("🔒 Security Status Summary")
    click.echo("=" * 40)
    
    status_icon = "🟢" if summary['security_status'] == 'healthy' else "🟡"
    click.echo(f"Status: {status_icon} {summary['security_status']}")
    click.echo(f"Events (24h): {summary['events_last_24h']}")
    click.echo(f"High Risk Events: {summary['high_risk_events']}")
    click.echo(f"Failed Events: {summary['failed_events']}")
    click.echo(f"Active Tokens: {summary['active_tokens']}")
    click.echo(f"Blocked IPs: {summary['blocked_ips']}")
    click.echo(f"Enabled Policies: {summary['policies_enabled']}")
    
    if summary['event_breakdown']:
        click.echo("\nEvent Breakdown:")
        for event_type, count in summary['event_breakdown'].items():
            click.echo(f"  {event_type}: {count}")

@security_cli.command()
@click.option('--config-file', '-c', help='Security configuration file')
def health_check():
    """Run security health check"""
    async def run_check():
        security_manager = SecurityManager()
        results = await security_manager.perform_security_scan()
        
        click.echo("🏥 Security Health Check")
        click.echo("=" * 40)
        
        score = results['overall_score']
        if score >= 90:
            icon = "🟢"
            status = "EXCELLENT"
        elif score >= 75:
            icon = "🟡"
            status = "GOOD"
        elif score >= 50:
            icon = "🟠"
            status = "NEEDS ATTENTION"
        else:
            icon = "🔴"
            status = "CRITICAL"
        
        click.echo(f"Overall Score: {icon} {score}/100 ({status})")
        
        if results['issues']:
            click.echo("\n⚠️  Issues Found:")
            for issue in results['issues']:
                click.echo(f"  - {issue}")
        
        if results['recommendations']:
            click.echo("\n💡 Recommendations:")
            for rec in results['recommendations']:
                click.echo(f"  - {rec}")
        
        click.echo(f"\nPolicies Status:")
        for policy_name, policy_info in results['policies'].items():
            status_icon = "✅" if policy_info['enabled'] else "❌"
            click.echo(f"  {status_icon} {policy_name} ({policy_info['severity']})")
        
        if score < 75:
            click.echo("\n⚠️  Security score is below recommended threshold")
            sys.exit(1)
    
    asyncio.run(run_check())

@security_cli.group()
def config():
    """Security configuration management"""
    pass

@config.command()
@click.argument('policy_name')
def enable_policy(policy_name):
    """Enable security policy"""
    security_manager = SecurityManager()
    
    if security_manager.enable_policy(policy_name):
        click.echo(f"✅ Enabled policy: {policy_name}")
    else:
        click.echo(f"❌ Policy not found: {policy_name}")

@config.command()
@click.argument('policy_name')
def disable_policy(policy_name):
    """Disable security policy"""
    security_manager = SecurityManager()
    
    if security_manager.disable_policy(policy_name):
        click.echo(f"⚠️  Disabled policy: {policy_name}")
    else:
        click.echo(f"❌ Policy not found: {policy_name}")

@config.command()
def list_policies():
    """List all security policies"""
    security_manager = SecurityManager()
    
    click.echo("📋 Security Policies:")
    click.echo("-" * 40)
    
    for policy_name, policy in security_manager.security_policies.items():
        status_icon = "✅" if policy.enabled else "❌"
        severity_icon = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(policy.severity.value, "⚪")
        
        click.echo(f"{status_icon} {policy_name}")
        click.echo(f"   {severity_icon} Severity: {policy.severity.value}")
        click.echo(f"   📝 {policy.description}")
        click.echo(f"   🎯 Action: {policy.action}")
        click.echo()

if __name__ == '__main__':
    security_cli()