#!/usr/bin/env python3
"""
🔍 OMEGA Monitoring Deployment Script
Deploys SSL certificate monitoring and health check systems
"""

import click
import subprocess
import os
import time
import json
from pathlib import Path
from datetime import datetime

@click.group()
def monitor_cli():
    """OMEGA Monitoring Deployment CLI"""
    pass

@monitor_cli.command()
@click.option('--background', is_flag=True, help='Run monitoring in background')
@click.option('--ssl-domain', default='omega-api.akash.network', help='SSL domain to monitor')
@click.option('--ssl-email', default='admin@omega-pro-ai.com', help='SSL email for renewal')
def deploy_ssl_monitoring(background, ssl_domain, ssl_email):
    """Deploy SSL certificate monitoring"""
    
    click.echo("🔐 Deploying SSL certificate monitoring...")
    
    # Create monitoring log directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create SSL monitoring service script
    monitor_script = Path("scripts/ssl_monitor_service.py")
    
    ssl_monitor_content = f'''#!/usr/bin/env python3
"""SSL Certificate Monitoring Service"""

import time
import logging
import json
from pathlib import Path
from datetime import datetime
from ssl_cert_manager import SSLCertificateManager
import requests
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ssl_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SSLMonitoringService:
    def __init__(self, domain="{ssl_domain}", email="{ssl_email}"):
        self.domain = domain
        self.email = email
        self.manager = SSLCertificateManager()
        
    def monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Starting SSL certificate monitoring service")
        
        while True:
            try:
                # Check certificate status
                cert_info = self.manager.check_certificate_validity()
                
                if cert_info['valid']:
                    days_left = cert_info['days_until_expiry']
                    logger.info(f"SSL certificate valid for {{days_left}} days")
                    
                    # Alert if expiring soon
                    if days_left <= 7:
                        self.send_alert(f"URGENT: SSL certificate expires in {{days_left}} days!")
                        
                        # Auto-renew if less than 3 days
                        if days_left <= 3:
                            logger.warning("Auto-renewing SSL certificate")
                            if self.manager.renew_certificate(self.domain, self.email):
                                self.send_alert("SSL certificate auto-renewed successfully")
                            else:
                                self.send_alert("SSL certificate auto-renewal FAILED!")
                    
                    elif days_left <= 30:
                        logger.warning(f"SSL certificate expires in {{days_left}} days")
                        
                else:
                    logger.error(f"SSL certificate is invalid: {{cert_info.get('error')}}")
                    self.send_alert(f"SSL certificate is invalid: {{cert_info.get('error')}}")
                
                # Sleep for 1 hour between checks
                time.sleep(3600)
                
            except KeyboardInterrupt:
                logger.info("SSL monitoring service stopped by user")
                break
            except Exception as e:
                logger.error(f"SSL monitoring error: {{e}}")
                time.sleep(300)  # Sleep 5 minutes on error
    
    def send_alert(self, message):
        """Send alert notification"""
        logger.warning(f"ALERT: {{message}}")
        
        # Try to send webhook notification
        webhook_url = os.getenv('SSL_ALERT_WEBHOOK_URL')
        if webhook_url:
            try:
                requests.post(webhook_url, json={{
                    'text': f'OMEGA SSL Alert: {{message}}',
                    'timestamp': datetime.now().isoformat(),
                    'domain': self.domain
                }}, timeout=10)
            except Exception as e:
                logger.error(f"Failed to send webhook alert: {{e}}")

if __name__ == '__main__':
    service = SSLMonitoringService()
    service.monitor_loop()
'''
    
    with open(monitor_script, 'w') as f:
        f.write(ssl_monitor_content)
    
    os.chmod(monitor_script, 0o755)
    
    if background:
        # Start monitoring in background
        click.echo("Starting SSL monitoring in background...")
        subprocess.Popen([
            'python3', str(monitor_script)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        click.echo("✅ SSL monitoring started in background")
    else:
        click.echo("SSL monitoring script created. Run manually with:")
        click.echo(f"   python3 {monitor_script}")

@monitor_cli.command()
@click.option('--config-file', default='./config/health_checks.json', help='Health check configuration')
@click.option('--background', is_flag=True, help='Run health monitoring in background')
def deploy_health_monitoring(config_file, background):
    """Deploy health monitoring system"""
    
    click.echo("🔍 Deploying health monitoring system...")
    
    # Ensure config file exists
    if not Path(config_file).exists():
        click.echo(f"❌ Health check configuration not found: {config_file}")
        click.echo("Run 'python3 scripts/service_mesh_security.py generate-configs' first")
        return
    
    # Create health monitoring service script
    health_script = Path("scripts/health_monitor_service.py")
    
    health_monitor_content = f'''#!/usr/bin/env python3
"""Health Monitoring Service"""

import time
import logging
import json
import requests
import os
from pathlib import Path
from service_mesh_security import HealthMonitor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/health_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HealthMonitoringService:
    def __init__(self, config_file="{config_file}"):
        self.monitor = HealthMonitor(config_file)
        
    def monitoring_loop(self):
        """Main health monitoring loop"""
        logger.info("Starting health monitoring service")
        
        while True:
            try:
                services = self.monitor.config.get('health_checks', {{}}).keys()
                
                for service in services:
                    result = self.monitor.check_service_health(service)
                    
                    if result['status'] == 'healthy':
                        logger.info(f"✅ {{service}}: healthy")
                    else:
                        logger.error(f"❌ {{service}}: unhealthy")
                        logger.error(f"Details: {{result}}")
                        
                        # Send alert
                        self.send_health_alert(service, result)
                
                # Sleep for 1 minute between checks
                time.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("Health monitoring service stopped by user")
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {{e}}")
                time.sleep(30)  # Sleep 30 seconds on error
    
    def send_health_alert(self, service, result):
        """Send health alert notification"""
        webhook_url = os.getenv('HEALTH_WEBHOOK_URL')
        if webhook_url:
            try:
                requests.post(webhook_url, json={{
                    'text': f'OMEGA Health Alert: {{service}} is unhealthy',
                    'service': service,
                    'details': result
                }}, timeout=10)
            except Exception as e:
                logger.error(f"Failed to send health alert: {{e}}")

if __name__ == '__main__':
    service = HealthMonitoringService()
    service.monitoring_loop()
'''
    
    with open(health_script, 'w') as f:
        f.write(health_monitor_content)
    
    os.chmod(health_script, 0o755)
    
    if background:
        # Start health monitoring in background
        click.echo("Starting health monitoring in background...")
        subprocess.Popen([
            'python3', str(health_script)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        click.echo("✅ Health monitoring started in background")
    else:
        click.echo("Health monitoring script created. Run manually with:")
        click.echo(f"   python3 {health_script}")

@monitor_cli.command()
def deploy_all():
    """Deploy all monitoring systems"""
    
    click.echo("🚀 Deploying complete monitoring infrastructure...")
    
    # Deploy SSL monitoring
    click.echo("🔐 Deploying SSL certificate monitoring...")
    
    # Create monitoring log directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create SSL monitoring service script
    monitor_script = Path("scripts/ssl_monitor_service.py")
    
    ssl_monitor_content = '''#!/usr/bin/env python3
"""SSL Certificate Monitoring Service"""

import time
import logging
import json
from pathlib import Path
from datetime import datetime
import sys
import os

# Add the scripts directory to the path so we can import ssl_cert_manager
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ssl_cert_manager import SSLCertificateManager
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ssl_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SSLMonitoringService:
    def __init__(self, domain="omega-api.akash.network", email="admin@omega-pro-ai.com"):
        self.domain = domain
        self.email = email
        self.manager = SSLCertificateManager()
        
    def monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Starting SSL certificate monitoring service")
        
        while True:
            try:
                # Check certificate status
                cert_info = self.manager.check_certificate_validity()
                
                if cert_info['valid']:
                    days_left = cert_info['days_until_expiry']
                    logger.info(f"SSL certificate valid for {days_left} days")
                    
                    # Alert if expiring soon
                    if days_left <= 7:
                        self.send_alert(f"URGENT: SSL certificate expires in {days_left} days!")
                        
                        # Auto-renew if less than 3 days
                        if days_left <= 3:
                            logger.warning("Auto-renewing SSL certificate")
                            if self.manager.renew_certificate(self.domain, self.email):
                                self.send_alert("SSL certificate auto-renewed successfully")
                            else:
                                self.send_alert("SSL certificate auto-renewal FAILED!")
                    
                    elif days_left <= 30:
                        logger.warning(f"SSL certificate expires in {days_left} days")
                        
                else:
                    logger.error(f"SSL certificate is invalid: {cert_info.get('error')}")
                    self.send_alert(f"SSL certificate is invalid: {cert_info.get('error')}")
                
                # Sleep for 1 hour between checks
                time.sleep(3600)
                
            except KeyboardInterrupt:
                logger.info("SSL monitoring service stopped by user")
                break
            except Exception as e:
                logger.error(f"SSL monitoring error: {e}")
                time.sleep(300)  # Sleep 5 minutes on error
    
    def send_alert(self, message):
        """Send alert notification"""
        logger.warning(f"ALERT: {message}")
        
        # Try to send webhook notification
        webhook_url = os.getenv('SSL_ALERT_WEBHOOK_URL')
        if webhook_url:
            try:
                requests.post(webhook_url, json={
                    'text': f'OMEGA SSL Alert: {message}',
                    'timestamp': datetime.now().isoformat(),
                    'domain': self.domain
                }, timeout=10)
            except Exception as e:
                logger.error(f"Failed to send webhook alert: {e}")

if __name__ == '__main__':
    service = SSLMonitoringService()
    service.monitor_loop()
'''
    
    with open(monitor_script, 'w') as f:
        f.write(ssl_monitor_content)
    
    os.chmod(monitor_script, 0o755)
    
    # Deploy health monitoring
    click.echo("🔍 Deploying health monitoring system...")
    
    # Create health monitoring service script
    health_script = Path("scripts/health_monitor_service.py")
    
    health_monitor_content = '''#!/usr/bin/env python3
"""Health Monitoring Service"""

import time
import logging
import json
import requests
import os
import sys
from pathlib import Path

# Add the scripts directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from service_mesh_security import HealthMonitor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/health_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HealthMonitoringService:
    def __init__(self, config_file="./config/health_checks.json"):
        self.monitor = HealthMonitor(config_file)
        
    def monitoring_loop(self):
        """Main health monitoring loop"""
        logger.info("Starting health monitoring service")
        
        while True:
            try:
                services = self.monitor.config.get('health_checks', {}).keys()
                
                for service in services:
                    result = self.monitor.check_service_health(service)
                    
                    if result['status'] == 'healthy':
                        logger.info(f"✅ {service}: healthy")
                    else:
                        logger.error(f"❌ {service}: unhealthy")
                        logger.error(f"Details: {result}")
                        
                        # Send alert
                        self.send_health_alert(service, result)
                
                # Sleep for 1 minute between checks
                time.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("Health monitoring service stopped by user")
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                time.sleep(30)  # Sleep 30 seconds on error
    
    def send_health_alert(self, service, result):
        """Send health alert notification"""
        webhook_url = os.getenv('HEALTH_WEBHOOK_URL')
        if webhook_url:
            try:
                requests.post(webhook_url, json={
                    'text': f'OMEGA Health Alert: {service} is unhealthy',
                    'service': service,
                    'details': result
                }, timeout=10)
            except Exception as e:
                logger.error(f"Failed to send health alert: {e}")

if __name__ == '__main__':
    service = HealthMonitoringService()
    service.monitoring_loop()
'''
    
    with open(health_script, 'w') as f:
        f.write(health_monitor_content)
    
    os.chmod(health_script, 0o755)
    
    # Create monitoring dashboard script
    dashboard_script = Path("scripts/monitoring_dashboard.py")
    
    dashboard_content = '''#!/usr/bin/env python3
"""Monitoring Dashboard - Real-time status viewer"""

import time
import json
import os
from pathlib import Path
from ssl_cert_manager import SSLCertificateManager
from service_mesh_security import HealthMonitor

def show_dashboard():
    """Display monitoring dashboard"""
    ssl_manager = SSLCertificateManager()
    health_monitor = HealthMonitor('./config/health_checks.json')
    
    while True:
        try:
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print("🔐 OMEGA Pro AI - Monitoring Dashboard")
            print("=" * 50)
            print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            # SSL Certificate Status
            print("🔒 SSL Certificate Status:")
            cert_info = ssl_manager.check_certificate_validity()
            if cert_info['valid']:
                days_left = cert_info['days_until_expiry']
                status_color = "🟢" if days_left > 30 else "🟡" if days_left > 7 else "🔴"
                print(f"   {status_color} Valid - {days_left} days remaining")
                print(f"   Domain: {cert_info['domain']}")
                print(f"   Expires: {cert_info['not_after']}")
            else:
                print(f"   🔴 Invalid - {cert_info.get('error')}")
            print()
            
            # Service Health Status
            print("❤️ Service Health Status:")
            services = health_monitor.config.get('health_checks', {}).keys()
            
            for service in services:
                result = health_monitor.check_service_health(service)
                status_emoji = "🟢" if result['status'] == 'healthy' else "🔴"
                print(f"   {status_emoji} {service}: {result['status']}")
            
            print()
            print("Press Ctrl+C to exit")
            
            time.sleep(30)  # Refresh every 30 seconds
            
        except KeyboardInterrupt:
            print("\\n👋 Dashboard closed")
            break
        except Exception as e:
            print(f"Dashboard error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    show_dashboard()
'''
    
    with open(dashboard_script, 'w') as f:
        f.write(dashboard_content)
    
    os.chmod(dashboard_script, 0o755)
    
    click.echo("✅ Complete monitoring infrastructure deployed!")
    click.echo("")
    click.echo("Monitoring Services:")
    click.echo("   - SSL Certificate Monitoring: Running in background")
    click.echo("   - Health Check Monitoring: Running in background")
    click.echo("")
    click.echo("Dashboard:")
    click.echo(f"   python3 {dashboard_script}")
    click.echo("")
    click.echo("Logs:")
    click.echo("   - SSL Monitor: logs/ssl_monitor.log")
    click.echo("   - Health Monitor: logs/health_monitor.log")

if __name__ == '__main__':
    monitor_cli()