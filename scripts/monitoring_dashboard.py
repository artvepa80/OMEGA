#!/usr/bin/env python3
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
            print("\n👋 Dashboard closed")
            break
        except Exception as e:
            print(f"Dashboard error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    show_dashboard()
