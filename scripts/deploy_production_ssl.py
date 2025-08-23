#!/usr/bin/env python3
"""
OMEGA Production SSL Deployment Script
Orchestrates complete SSL certificate deployment for production environment
"""

import click
import subprocess
import json
import time
import os
from pathlib import Path
from datetime import datetime
import requests
import hashlib

class ProductionSSLDeployer:
    """Manages production SSL certificate deployment for OMEGA"""
    
    def __init__(self, domain: str = "omega-api.akash.network", email: str = "admin@omega-pro-ai.com"):
        self.domain = domain
        self.email = email
        self.ssl_dir = Path("./ssl")
        self.docker_dir = Path("./docker")
        self.scripts_dir = Path("./scripts")
        self.ios_dir = Path("./ios/OmegaApp_Clean")
        
        # Ensure directories exist
        self.ssl_dir.mkdir(exist_ok=True)
        
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        icon = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}.get(level, "📝")
        click.echo(f"[{timestamp}] {icon} {message}")
    
    def run_command(self, cmd: list, description: str, timeout: int = 300) -> bool:
        """Run command with error handling and logging"""
        
        self.log(f"Executing: {description}")
        self.log(f"Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                self.log(f"SUCCESS: {description}", "SUCCESS")
                if result.stdout.strip():
                    click.echo(f"   Output: {result.stdout.strip()}")
                return True
            else:
                self.log(f"FAILED: {description}", "ERROR")
                if result.stderr.strip():
                    click.echo(f"   Error: {result.stderr.strip()}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log(f"TIMEOUT: {description} (exceeded {timeout}s)", "ERROR")
            return False
        except Exception as e:
            self.log(f"EXCEPTION: {description} - {e}", "ERROR")
            return False
    
    def check_prerequisites(self) -> bool:
        """Check system prerequisites for SSL deployment"""
        
        self.log("Checking system prerequisites...")
        
        # Check for required tools
        tools = ['certbot', 'openssl', 'nginx', 'python3']
        missing_tools = []
        
        for tool in tools:
            if not self.run_command(['which', tool], f"Check {tool}", timeout=10):
                missing_tools.append(tool)
        
        if missing_tools:
            self.log(f"Missing required tools: {', '.join(missing_tools)}", "ERROR")
            self.log("Please install missing tools and retry", "ERROR")
            return False
        
        # Check port 80 availability
        port_check = subprocess.run(['lsof', '-i', ':80'], capture_output=True)
        if port_check.returncode == 0:
            self.log("Port 80 is in use - will attempt to stop conflicting services", "WARNING")
        
        # Check disk space
        statvfs = os.statvfs('.')
        free_bytes = statvfs.f_frsize * statvfs.f_bavail
        free_gb = free_bytes / (1024**3)
        
        if free_gb < 1:
            self.log(f"Low disk space: {free_gb:.1f}GB available", "WARNING")
        else:
            self.log(f"Disk space OK: {free_gb:.1f}GB available")
        
        return True
    
    def generate_dhparams(self) -> bool:
        """Generate Diffie-Hellman parameters"""
        
        dhparam_path = self.ssl_dir / "dhparam.pem"
        
        if dhparam_path.exists():
            self.log("DH parameters already exist, skipping generation")
            return True
        
        self.log("Generating 2048-bit Diffie-Hellman parameters (this may take a while)...")
        
        return self.run_command([
            'python3', str(self.scripts_dir / 'generate_dhparam.py'),
            '--bits', '2048',
            '--output', str(dhparam_path)
        ], "Generate DH parameters", timeout=1800)  # 30 minutes
    
    def deploy_letsencrypt_certificate(self) -> bool:
        """Deploy Let's Encrypt production certificate"""
        
        self.log(f"Deploying Let's Encrypt production certificate for {self.domain}")
        
        return self.run_command([
            'python3', str(self.scripts_dir / 'ssl_cert_manager.py'),
            'generate',
            '--domain', self.domain,
            '--email', self.email,
            '--type', 'letsencrypt',
            '--production'
        ], "Deploy Let's Encrypt certificate", timeout=600)
    
    def update_ios_certificate_pinning(self) -> bool:
        """Update iOS certificate pinning with production certificates"""
        
        self.log("Updating iOS certificate pinning configuration")
        
        return self.run_command([
            'python3', str(self.scripts_dir / 'update_ios_pinning.py'),
            '--domain', self.domain
        ], "Update iOS certificate pinning", timeout=60)
    
    def deploy_nginx_configuration(self) -> bool:
        """Deploy production nginx configuration"""
        
        self.log("Deploying production nginx configuration")
        
        # Copy production nginx config
        src_config = self.docker_dir / "nginx-production-ssl.conf"
        dest_config = self.docker_dir / "nginx.conf"
        
        if not src_config.exists():
            self.log(f"Production nginx config not found: {src_config}", "ERROR")
            return False
        
        try:
            # Backup existing config
            if dest_config.exists():
                backup_config = dest_config.with_suffix('.conf.backup')
                dest_config.rename(backup_config)
                self.log(f"Backed up existing config to: {backup_config}")
            
            # Copy production config
            with open(src_config, 'r') as src, open(dest_config, 'w') as dest:
                dest.write(src.read())
            
            self.log("Production nginx configuration deployed", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Failed to deploy nginx configuration: {e}", "ERROR")
            return False
    
    def test_nginx_configuration(self) -> bool:
        """Test nginx configuration"""
        
        self.log("Testing nginx configuration")
        
        return self.run_command(['nginx', '-t'], "Test nginx configuration", timeout=30)
    
    def restart_services(self) -> bool:
        """Restart nginx and related services"""
        
        self.log("Restarting services")
        
        success = True
        
        # Reload nginx
        if not self.run_command(['nginx', '-s', 'reload'], "Reload nginx", timeout=30):
            # If reload fails, try restart
            if not self.run_command(['systemctl', 'restart', 'nginx'], "Restart nginx", timeout=60):
                success = False
        
        # Wait for nginx to start
        time.sleep(5)
        
        # Check nginx status
        if not self.run_command(['systemctl', 'is-active', 'nginx'], "Check nginx status", timeout=10):
            success = False
        
        return success
    
    def validate_ssl_deployment(self) -> bool:
        """Validate SSL certificate deployment"""
        
        self.log(f"Validating SSL deployment for {self.domain}")
        
        # Test SSL connection using ssl_cert_manager
        if not self.run_command([
            'python3', str(self.scripts_dir / 'ssl_cert_manager.py'),
            'test',
            '--domain', self.domain
        ], "Test SSL connection", timeout=60):
            return False
        
        # Check certificate status
        if not self.run_command([
            'python3', str(self.scripts_dir / 'ssl_cert_manager.py'),
            'status'
        ], "Check certificate status", timeout=30):
            return False
        
        # Test HTTPS endpoint
        try:
            self.log(f"Testing HTTPS endpoint: https://{self.domain}/health")
            
            response = requests.get(f"https://{self.domain}/health", timeout=30, verify=True)
            
            if response.status_code == 200:
                self.log("HTTPS endpoint test successful", "SUCCESS")
                return True
            else:
                self.log(f"HTTPS endpoint returned status {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"HTTPS endpoint test failed: {e}", "ERROR")
            return False
    
    def setup_monitoring(self) -> bool:
        """Setup SSL certificate monitoring"""
        
        self.log("Setting up SSL certificate monitoring")
        
        # Create monitoring service script
        monitor_script = Path("/usr/local/bin/omega_ssl_monitor.py")
        
        script_content = f"""#!/usr/bin/env python3
# OMEGA SSL Certificate Monitor Service
import sys
sys.path.append('{os.getcwd()}')

from scripts.ssl_cert_manager import SSLCertificateManager
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    manager = SSLCertificateManager()
    
    while True:
        try:
            cert_info = manager.check_certificate_validity()
            
            if cert_info['valid']:
                days_left = cert_info['days_until_expiry']
                
                if days_left <= 7:
                    logger.warning(f"Certificate expires in {{days_left}} days - attempting renewal")
                    if manager.renew_certificate('{self.domain}', '{self.email}'):
                        logger.info("Certificate renewed successfully")
                    else:
                        logger.error("Certificate renewal failed")
                elif days_left <= 30:
                    logger.info(f"Certificate expires in {{days_left}} days")
            else:
                logger.error("Certificate is invalid or expired")
                
        except Exception as e:
            logger.error(f"Monitoring error: {{e}}")
        
        time.sleep(3600)  # Check every hour
"""
        
        try:
            with open(monitor_script, 'w') as f:
                f.write(script_content)
            
            os.chmod(monitor_script, 0o755)
            
            # Create systemd service
            service_content = f"""[Unit]
Description=OMEGA SSL Certificate Monitor
After=network.target

[Service]
Type=simple
User=root
ExecStart={monitor_script}
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
"""
            
            service_path = Path("/etc/systemd/system/omega-ssl-monitor.service")
            with open(service_path, 'w') as f:
                f.write(service_content)
            
            # Enable and start service
            if self.run_command(['systemctl', 'daemon-reload'], "Reload systemd", timeout=30):
                if self.run_command(['systemctl', 'enable', 'omega-ssl-monitor.service'], "Enable SSL monitor", timeout=30):
                    if self.run_command(['systemctl', 'start', 'omega-ssl-monitor.service'], "Start SSL monitor", timeout=30):
                        self.log("SSL certificate monitoring service configured", "SUCCESS")
                        return True
            
        except Exception as e:
            self.log(f"Failed to setup monitoring: {e}", "ERROR")
        
        return False
    
    def generate_deployment_report(self) -> dict:
        """Generate deployment report"""
        
        self.log("Generating deployment report")
        
        report = {
            "deployment_timestamp": datetime.now().isoformat(),
            "domain": self.domain,
            "email": self.email,
            "ssl_directory": str(self.ssl_dir),
            "certificate_info": {},
            "nginx_config": str(self.docker_dir / "nginx.conf"),
            "monitoring_enabled": False,
            "ios_pinning_updated": False
        }
        
        # Get certificate information
        try:
            result = subprocess.run([
                'python3', str(self.scripts_dir / 'ssl_cert_manager.py'),
                'status'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Parse certificate status (simplified)
                report["certificate_status"] = "Valid"
            else:
                report["certificate_status"] = "Invalid"
                
        except Exception as e:
            report["certificate_status"] = f"Error: {e}"
        
        # Check if SSL config exists
        ssl_config_path = self.ssl_dir / "ssl_config.json"
        if ssl_config_path.exists():
            try:
                with open(ssl_config_path, 'r') as f:
                    ssl_config = json.load(f)
                    report["certificate_info"] = ssl_config
            except Exception as e:
                report["certificate_info"] = {"error": str(e)}
        
        # Check monitoring service
        monitor_check = subprocess.run(['systemctl', 'is-active', 'omega-ssl-monitor.service'], capture_output=True)
        report["monitoring_enabled"] = monitor_check.returncode == 0
        
        # Check iOS pinning file
        ios_pinning_file = self.ios_dir / "ProductionCertificatePinning.swift"
        report["ios_pinning_updated"] = ios_pinning_file.exists()
        
        return report

@click.command()
@click.option('--domain', default='omega-api.akash.network', help='Domain to deploy SSL for')
@click.option('--email', default='admin@omega-pro-ai.com', help='Admin email for Let\'s Encrypt')
@click.option('--skip-dhparam', is_flag=True, help='Skip DH parameter generation')
@click.option('--skip-monitoring', is_flag=True, help='Skip monitoring setup')
def deploy_production_ssl(domain, email, skip_dhparam, skip_monitoring):
    """Deploy production-grade SSL certificates for OMEGA"""
    
    click.echo("🚀 OMEGA Production SSL Deployment")
    click.echo("=" * 80)
    
    deployer = ProductionSSLDeployer(domain, email)
    
    deployment_steps = [
        ("Checking prerequisites", lambda: deployer.check_prerequisites()),
        ("Generating DH parameters", lambda: skip_dhparam or deployer.generate_dhparams()),
        ("Deploying Let's Encrypt certificate", lambda: deployer.deploy_letsencrypt_certificate()),
        ("Updating iOS certificate pinning", lambda: deployer.update_ios_certificate_pinning()),
        ("Deploying nginx configuration", lambda: deployer.deploy_nginx_configuration()),
        ("Testing nginx configuration", lambda: deployer.test_nginx_configuration()),
        ("Restarting services", lambda: deployer.restart_services()),
        ("Validating SSL deployment", lambda: deployer.validate_ssl_deployment()),
        ("Setting up monitoring", lambda: skip_monitoring or deployer.setup_monitoring())
    ]
    
    failed_steps = []
    
    for step_name, step_func in deployment_steps:
        deployer.log(f"STEP: {step_name}")
        click.echo("-" * 60)
        
        if not step_func():
            deployer.log(f"FAILED: {step_name}", "ERROR")
            failed_steps.append(step_name)
            
            # Ask user if they want to continue
            if not click.confirm(f"\\n⚠️ Step '{step_name}' failed. Continue with deployment?"):
                deployer.log("Deployment aborted by user", "ERROR")
                return
        else:
            deployer.log(f"COMPLETED: {step_name}", "SUCCESS")
        
        click.echo()
    
    # Generate deployment report
    report = deployer.generate_deployment_report()
    
    # Save report
    report_path = Path("ssl_deployment_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Final status
    click.echo("=" * 80)
    
    if failed_steps:
        deployer.log(f"Deployment completed with {len(failed_steps)} failed steps", "WARNING")
        deployer.log(f"Failed steps: {', '.join(failed_steps)}", "WARNING")
    else:
        deployer.log("Production SSL deployment completed successfully!", "SUCCESS")
    
    deployer.log(f"Deployment report saved: {report_path}")
    
    # Show next steps
    click.echo()
    click.echo("🎯 Next Steps:")
    click.echo("   1. Test API endpoints with new SSL certificates")
    click.echo("   2. Update DNS records if necessary")
    click.echo("   3. Test iOS app with new certificate pinning")
    click.echo("   4. Monitor certificate auto-renewal")
    click.echo("   5. Update deployment documentation")
    
    click.echo()
    click.echo("🔗 Key URLs to test:")
    click.echo(f"   - https://{domain}/health")
    click.echo(f"   - https://{domain}/api/status")
    click.echo(f"   - https://{domain}/ssl/info")
    
    click.echo("=" * 80)

if __name__ == '__main__':
    deploy_production_ssl()