#!/usr/bin/env python3
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
