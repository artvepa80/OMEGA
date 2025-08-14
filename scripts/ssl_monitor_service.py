#!/usr/bin/env python3
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
