#!/usr/bin/env python3
'''
Security Monitoring and Alerting System for OMEGA Pro AI
'''

import time
import subprocess
import json
import requests
import re
import os
from datetime import datetime, timedelta
from collections import defaultdict

class SecurityMonitor:
    def __init__(self):
        self.alert_thresholds = {
            'failed_requests_per_minute': 50,
            'error_rate_percentage': 5.0,
            'blocked_requests_per_minute': 20,
            'concurrent_connections': 1000,
            'bandwidth_mbps': 100
        }
        
        self.log_files = {
            'access': '/var/log/nginx/access.log',
            'error': '/var/log/nginx/error.log'
        }
        
        self.metrics = defaultdict(int)
        self.last_alert_time = defaultdict(lambda: datetime.min)
        
    def analyze_logs(self):
        '''Analyze nginx logs for security threats'''
        
        # Read recent access log entries
        try:
            result = subprocess.run(['tail', '-1000', self.log_files['access']], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.analyze_access_log(result.stdout)
                
        except Exception as e:
            print(f"Error reading access logs: {e}")
        
        # Read recent error log entries
        try:
            result = subprocess.run(['tail', '-100', self.log_files['error']], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.analyze_error_log(result.stdout)
                
        except Exception as e:
            print(f"Error reading error logs: {e}")
    
    def analyze_access_log(self, log_content):
        '''Analyze access log for security patterns'''
        
        lines = log_content.strip().split('\n')
        recent_time = datetime.now() - timedelta(minutes=1)
        
        for line in lines:
            if not line:
                continue
                
            # Parse log line
            match = re.search(r'(\d+\.\d+\.\d+\.\d+).*"([A-Z]+)\s+([^"]+)"\s+(\d+)', line)
            if not match:
                continue
                
            ip, method, path, status = match.groups()
            status_code = int(status)
            
            # Count various metrics
            if status_code >= 400:
                self.metrics['failed_requests'] += 1
                
            if status_code == 429:
                self.metrics['rate_limited_requests'] += 1
                
            if status_code == 444:  # Blocked requests
                self.metrics['blocked_requests'] += 1
                
            # Check for common attack patterns
            if self.is_suspicious_request(path, method):
                self.metrics['suspicious_requests'] += 1
                self.alert(f"Suspicious request from {ip}: {method} {path}")
    
    def analyze_error_log(self, log_content):
        '''Analyze error log for security issues'''
        
        lines = log_content.strip().split('\n')
        
        for line in lines:
            if 'limit_req' in line:
                self.metrics['rate_limit_violations'] += 1
            elif 'limit_conn' in line:
                self.metrics['connection_limit_violations'] += 1
            elif 'SSL' in line and 'error' in line.lower():
                self.metrics['ssl_errors'] += 1
    
    def is_suspicious_request(self, path, method):
        '''Check if request is suspicious'''
        
        suspicious_patterns = [
            r'/\.\./.*',  # Directory traversal
            r'/wp-admin.*',  # WordPress attacks
            r'/admin.*',  # Admin panel probing
            r'/phpmyadmin.*',  # Database admin attacks
            r'\.(php|asp|jsp)$',  # Script file access
            r'/\.env',  # Environment file access
            r'/config.*',  # Config file access
            r'select.*from.*',  # SQL injection patterns
            r'union.*select.*',  # SQL injection
            r'<script.*>.*',  # XSS patterns
            r'javascript:.*',  # XSS
        ]
        
        path_lower = path.lower()
        
        for pattern in suspicious_patterns:
            if re.search(pattern, path_lower):
                return True
                
        return False
    
    def check_system_health(self):
        '''Check system health metrics'''
        
        try:
            # Check nginx status
            result = subprocess.run(['curl', '-s', 'http://localhost:9090/nginx_status'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.parse_nginx_status(result.stdout)
                
        except Exception as e:
            print(f"Error checking nginx status: {e}")
    
    def parse_nginx_status(self, status_output):
        '''Parse nginx status output'''
        
        lines = status_output.strip().split('\n')
        
        for line in lines:
            if 'Active connections:' in line:
                connections = int(line.split(':')[1].strip())
                self.metrics['active_connections'] = connections
                
                if connections > self.alert_thresholds['concurrent_connections']:
                    self.alert(f"High connection count: {connections}")
    
    def alert(self, message):
        '''Send security alert'''
        
        alert_type = message.split(':')[0].lower()
        now = datetime.now()
        
        # Rate limit alerts (max 1 per type per 5 minutes)
        if now - self.last_alert_time[alert_type] < timedelta(minutes=5):
            return
            
        self.last_alert_time[alert_type] = now
        
        print(f"SECURITY ALERT: {message}")
        
        # Send webhook alert if configured
        webhook_url = os.getenv('SECURITY_WEBHOOK_URL')
        if webhook_url:
            try:
                requests.post(webhook_url, json={
                    'text': f'OMEGA Security Alert: {message}',
                    'timestamp': now.isoformat(),
                    'severity': 'high' if 'attack' in message.lower() else 'medium'
                }, timeout=10)
            except Exception as e:
                print(f"Failed to send webhook alert: {e}")
    
    def generate_report(self):
        '''Generate security report'''
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics': dict(self.metrics),
            'alerts_generated': len(self.last_alert_time),
            'status': 'healthy' if self.metrics['suspicious_requests'] < 10 else 'warning'
        }
        
        # Save report
        with open('/tmp/security_report.json', 'w') as f:
            json.dump(report, f, indent=2)
            
        return report
    
    def monitor_loop(self):
        '''Main monitoring loop'''
        
        print("Starting OMEGA security monitoring...")
        
        while True:
            try:
                # Reset metrics for this iteration
                self.metrics.clear()
                
                # Analyze logs
                self.analyze_logs()
                
                # Check system health
                self.check_system_health()
                
                # Generate report
                report = self.generate_report()
                print(f"Security scan complete: {report['status']}")
                
                # Sleep for 60 seconds
                time.sleep(60)
                
            except KeyboardInterrupt:
                print("Security monitoring stopped by user")
                break
            except Exception as e:
                print(f"Security monitoring error: {e}")
                time.sleep(30)

if __name__ == '__main__':
    monitor = SecurityMonitor()
    monitor.monitor_loop()
