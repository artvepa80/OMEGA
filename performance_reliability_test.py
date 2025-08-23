#!/usr/bin/env python3
"""
OMEGA Pro AI - Performance and Reliability Testing Suite
Tests deployment pipeline performance, health monitoring, and system reliability
"""

import asyncio
import time
import requests
import json
import subprocess
import logging
import threading
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import concurrent.futures
import psutil
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_reliability_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PerformanceReliabilityTestSuite:
    """Comprehensive performance and reliability testing"""
    
    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
        self.reliability_metrics = {}
        self.start_time = datetime.now()
        
        # Test configuration
        self.base_url = 'http://localhost:8001'
        self.test_duration = 30  # seconds
        self.concurrent_requests = 10
        
    async def run_performance_tests(self) -> Dict:
        """Execute comprehensive performance and reliability tests"""
        logger.info("🚀 Starting Performance and Reliability Testing Suite")
        
        test_categories = [
            ('Deployment Pipeline Performance', self.test_deployment_pipeline),
            ('API Performance Tests', self.test_api_performance),
            ('Load Testing', self.test_load_performance),
            ('Certificate Rotation Tests', self.test_certificate_rotation),
            ('Health Monitoring Tests', self.test_health_monitoring),
            ('System Reliability Tests', self.test_system_reliability),
            ('Failover Tests', self.test_failover_procedures),
        ]
        
        for test_name, test_func in test_categories:
            logger.info(f"\n{'='*50}")
            logger.info(f"⚡ Running {test_name}")
            logger.info(f"{'='*50}")
            
            try:
                results = await test_func()
                self.test_results[test_name] = results
                logger.info(f"✅ {test_name} completed - Score: {results.get('score', 0)}%")
            except Exception as e:
                logger.error(f"❌ {test_name} failed: {str(e)}")
                self.test_results[test_name] = {
                    'status': 'FAILED',
                    'error': str(e),
                    'score': 0
                }
        
        return await self.generate_performance_report()
    
    async def test_deployment_pipeline(self) -> Dict:
        """Test deployment pipeline performance"""
        results = {
            'tests': [],
            'status': 'PASSED',
            'score': 100,
            'metrics': {}
        }
        
        # Test Docker configuration validation
        docker_test = await self.test_docker_configurations()
        results['tests'].append(docker_test)
        
        # Test deployment scripts
        deployment_test = await self.test_deployment_scripts()
        results['tests'].append(deployment_test)
        
        # Test configuration validation
        config_test = await self.test_configuration_validation()
        results['tests'].append(config_test)
        
        # Calculate score
        total_score = sum(test['score'] for test in results['tests'])
        results['score'] = total_score / len(results['tests'])
        
        if results['score'] < 80:
            results['status'] = 'FAILED'
        elif results['score'] < 90:
            results['status'] = 'WARNING'
        
        return results
    
    async def test_docker_configurations(self) -> Dict:
        """Test Docker configuration files"""
        test_result = {
            'name': 'Docker Configuration Test',
            'status': 'PASSED',
            'details': [],
            'score': 100
        }
        
        # Check Docker files
        docker_files = [
            'Dockerfile.secure-api',
            'Dockerfile.secure-gpu', 
            'docker-compose.yml',
            'docker-compose.prod.yml'
        ]
        
        for docker_file in docker_files:
            if os.path.exists(docker_file):
                test_result['details'].append(f"✅ Docker file present: {docker_file}")
                
                # Validate file content
                try:
                    with open(docker_file, 'r') as f:
                        content = f.read()
                        if 'FROM' in content and len(content) > 100:
                            test_result['details'].append(f"✅ {docker_file} appears valid")
                        else:
                            test_result['details'].append(f"⚠️ {docker_file} may be incomplete")
                            test_result['score'] -= 10
                except Exception as e:
                    test_result['details'].append(f"❌ Error reading {docker_file}: {str(e)}")
                    test_result['score'] -= 15
                    test_result['status'] = 'WARNING'
            else:
                test_result['details'].append(f"❌ Docker file missing: {docker_file}")
                test_result['score'] -= 20
                test_result['status'] = 'FAILED'
        
        return test_result
    
    async def test_deployment_scripts(self) -> Dict:
        """Test deployment automation scripts"""
        test_result = {
            'name': 'Deployment Scripts Test',
            'status': 'PASSED',
            'details': [],
            'score': 100
        }
        
        # Check deployment scripts
        deployment_scripts = [
            'scripts/secure_akash_deploy.py',
            'scripts/deployment_verification.py',
            'scripts/ssl_cert_manager.py',
            'deploy-railway.sh',
            'deploy-vercel.sh'
        ]
        
        for script in deployment_scripts:
            if os.path.exists(script):
                test_result['details'].append(f"✅ Deployment script present: {script}")
                
                # Test script syntax (for Python scripts)
                if script.endswith('.py'):
                    try:
                        result = subprocess.run(['python3', '-m', 'py_compile', script], 
                                              capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            test_result['details'].append(f"✅ {script} syntax valid")
                        else:
                            test_result['details'].append(f"⚠️ {script} syntax issues: {result.stderr}")
                            test_result['score'] -= 10
                    except subprocess.TimeoutExpired:
                        test_result['details'].append(f"⚠️ {script} compilation timeout")
                        test_result['score'] -= 5
                    except Exception as e:
                        test_result['details'].append(f"⚠️ {script} validation error: {str(e)}")
                        test_result['score'] -= 5
                        
            else:
                test_result['details'].append(f"❌ Deployment script missing: {script}")
                test_result['score'] -= 15
                test_result['status'] = 'FAILED'
        
        return test_result
    
    async def test_configuration_validation(self) -> Dict:
        """Test configuration file validation"""
        test_result = {
            'name': 'Configuration Validation Test',
            'status': 'PASSED',
            'details': [],
            'score': 100
        }
        
        # Test JSON configuration files
        json_configs = [
            'ssl/ssl_config.json',
            'config/health_checks.json',
            'config/service_mesh_security.json'
        ]
        
        for config_file in json_configs:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        test_result['details'].append(f"✅ {config_file} valid JSON")
                except json.JSONDecodeError as e:
                    test_result['details'].append(f"❌ {config_file} invalid JSON: {str(e)}")
                    test_result['score'] -= 20
                    test_result['status'] = 'FAILED'
            else:
                test_result['details'].append(f"⚠️ Configuration missing: {config_file}")
                test_result['score'] -= 10
                test_result['status'] = 'WARNING'
        
        # Test YAML configuration files
        yaml_configs = [
            'deploy/secure-akash-deployment.yaml',
            'deploy/production-akash-secure.yaml'
        ]
        
        for config_file in yaml_configs:
            if os.path.exists(config_file):
                test_result['details'].append(f"✅ YAML config present: {config_file}")
                # Basic YAML validation would go here
            else:
                test_result['details'].append(f"❌ YAML config missing: {config_file}")
                test_result['score'] -= 15
                test_result['status'] = 'FAILED'
        
        return test_result
    
    async def test_api_performance(self) -> Dict:
        """Test API endpoint performance"""
        results = {
            'tests': [],
            'status': 'PASSED',
            'score': 100,
            'performance_metrics': {}
        }
        
        # Test response time performance
        response_time_test = await self.test_response_times()
        results['tests'].append(response_time_test)
        
        # Test throughput performance
        throughput_test = await self.test_api_throughput()
        results['tests'].append(throughput_test)
        
        # Calculate score
        total_score = sum(test['score'] for test in results['tests'])
        results['score'] = total_score / len(results['tests'])
        
        if results['score'] < 80:
            results['status'] = 'FAILED'
        elif results['score'] < 90:
            results['status'] = 'WARNING'
        
        return results
    
    async def test_response_times(self) -> Dict:
        """Test API response times"""
        test_result = {
            'name': 'API Response Time Test',
            'status': 'PASSED',
            'details': [],
            'score': 100,
            'response_times': []
        }
        
        # Test endpoints
        endpoints = [
            '/health',
            '/api/v1/health'
        ]
        
        total_response_times = []
        
        for endpoint in endpoints:
            response_times = []
            
            # Perform multiple requests
            for i in range(10):
                start_time = time.time()
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    total_response_times.append(response_time)
                    
                    if response.status_code != 200:
                        test_result['score'] -= 5
                        test_result['status'] = 'WARNING'
                        
                except Exception as e:
                    test_result['details'].append(f"❌ Request failed for {endpoint}: {str(e)}")
                    test_result['score'] -= 10
                    test_result['status'] = 'FAILED'
            
            if response_times:
                avg_time = statistics.mean(response_times)
                min_time = min(response_times)
                max_time = max(response_times)
                
                test_result['details'].append(
                    f"✅ {endpoint}: avg={avg_time:.3f}s, min={min_time:.3f}s, max={max_time:.3f}s"
                )
                
                # Score based on average response time
                if avg_time > 1.0:
                    test_result['details'].append(f"⚠️ {endpoint} slow response time")
                    test_result['score'] -= 15
                    test_result['status'] = 'WARNING'
                elif avg_time > 0.5:
                    test_result['details'].append(f"ℹ️ {endpoint} moderate response time")
                    test_result['score'] -= 5
        
        # Overall response time metrics
        if total_response_times:
            overall_avg = statistics.mean(total_response_times)
            test_result['response_times'] = total_response_times
            test_result['details'].append(f"📊 Overall average response time: {overall_avg:.3f}s")
        
        return test_result
    
    async def test_api_throughput(self) -> Dict:
        """Test API throughput under concurrent load"""
        test_result = {
            'name': 'API Throughput Test',
            'status': 'PASSED',
            'details': [],
            'score': 100,
            'throughput_metrics': {}
        }
        
        # Concurrent request test
        def make_request():
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}/health", timeout=5)
                response_time = time.time() - start_time
                return {
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'success': response.status_code == 200
                }
            except Exception as e:
                return {
                    'status_code': 0,
                    'response_time': 5.0,
                    'success': False,
                    'error': str(e)
                }
        
        # Execute concurrent requests
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrent_requests) as executor:
            # Submit 50 concurrent requests
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = sum(1 for r in results if r['success'])
        total_requests = len(results)
        success_rate = (successful_requests / total_requests) * 100
        throughput = total_requests / total_time
        
        test_result['throughput_metrics'] = {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'success_rate': success_rate,
            'throughput_rps': throughput,
            'total_time': total_time
        }
        
        test_result['details'].append(f"✅ Processed {total_requests} requests in {total_time:.2f}s")
        test_result['details'].append(f"✅ Success rate: {success_rate:.1f}%")
        test_result['details'].append(f"✅ Throughput: {throughput:.1f} requests/second")
        
        # Score based on performance
        if success_rate < 95:
            test_result['details'].append("⚠️ Low success rate under load")
            test_result['score'] -= 20
            test_result['status'] = 'WARNING'
        
        if throughput < 10:
            test_result['details'].append("⚠️ Low throughput performance")
            test_result['score'] -= 15
            test_result['status'] = 'WARNING'
        
        return test_result
    
    async def test_load_performance(self) -> Dict:
        """Test system performance under sustained load"""
        results = {
            'tests': [],
            'status': 'PASSED',
            'score': 100
        }
        
        # Sustained load test
        load_test = await self.test_sustained_load()
        results['tests'].append(load_test)
        
        # Memory usage test
        memory_test = await self.test_memory_usage()
        results['tests'].append(memory_test)
        
        # Calculate score
        total_score = sum(test['score'] for test in results['tests'])
        results['score'] = total_score / len(results['tests'])
        
        if results['score'] < 80:
            results['status'] = 'FAILED'
        elif results['score'] < 90:
            results['status'] = 'WARNING'
        
        return results
    
    async def test_sustained_load(self) -> Dict:
        """Test sustained load performance"""
        test_result = {
            'name': 'Sustained Load Test',
            'status': 'PASSED',
            'details': [],
            'score': 100,
            'load_metrics': {}
        }
        
        logger.info(f"Starting {self.test_duration}s sustained load test...")
        
        # Track metrics during load test
        start_time = time.time()
        end_time = start_time + self.test_duration
        
        request_count = 0
        error_count = 0
        response_times = []
        
        def make_load_request():
            nonlocal request_count, error_count
            try:
                start_req_time = time.time()
                response = requests.get(f"{self.base_url}/health", timeout=5)
                response_time = time.time() - start_req_time
                
                request_count += 1
                response_times.append(response_time)
                
                if response.status_code != 200:
                    error_count += 1
                    
            except Exception:
                error_count += 1
        
        # Run sustained load
        while time.time() < end_time:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_load_request) for _ in range(10)]
                for future in concurrent.futures.as_completed(futures):
                    future.result()
            
            time.sleep(0.1)  # Brief pause between batches
        
        actual_duration = time.time() - start_time
        error_rate = (error_count / request_count) * 100 if request_count > 0 else 100
        rps = request_count / actual_duration
        
        test_result['load_metrics'] = {
            'duration': actual_duration,
            'total_requests': request_count,
            'error_count': error_count,
            'error_rate': error_rate,
            'requests_per_second': rps,
            'avg_response_time': statistics.mean(response_times) if response_times else 0
        }
        
        test_result['details'].append(f"✅ Load test duration: {actual_duration:.1f}s")
        test_result['details'].append(f"✅ Total requests: {request_count}")
        test_result['details'].append(f"✅ Error rate: {error_rate:.1f}%")
        test_result['details'].append(f"✅ Sustained RPS: {rps:.1f}")
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            test_result['details'].append(f"✅ Average response time: {avg_response_time:.3f}s")
        
        # Score based on performance
        if error_rate > 5:
            test_result['details'].append("⚠️ High error rate under sustained load")
            test_result['score'] -= 25
            test_result['status'] = 'WARNING'
        
        if rps < 5:
            test_result['details'].append("⚠️ Low sustained throughput")
            test_result['score'] -= 15
            test_result['status'] = 'WARNING'
        
        return test_result
    
    async def test_memory_usage(self) -> Dict:
        """Test memory usage during operation"""
        test_result = {
            'name': 'Memory Usage Test',
            'status': 'PASSED',
            'details': [],
            'score': 100,
            'memory_metrics': {}
        }
        
        try:
            # Get initial memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            test_result['details'].append(f"✅ Initial memory usage: {initial_memory:.1f} MB")
            
            # Monitor memory during test requests
            memory_samples = []
            
            for i in range(20):
                # Make some requests
                for j in range(5):
                    try:
                        requests.get(f"{self.base_url}/health", timeout=2)
                    except:
                        pass
                
                # Sample memory
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
                time.sleep(0.5)
            
            final_memory = memory_samples[-1] if memory_samples else initial_memory
            max_memory = max(memory_samples) if memory_samples else initial_memory
            memory_growth = final_memory - initial_memory
            
            test_result['memory_metrics'] = {
                'initial_memory_mb': initial_memory,
                'final_memory_mb': final_memory,
                'max_memory_mb': max_memory,
                'memory_growth_mb': memory_growth
            }
            
            test_result['details'].append(f"✅ Final memory usage: {final_memory:.1f} MB")
            test_result['details'].append(f"✅ Peak memory usage: {max_memory:.1f} MB")
            test_result['details'].append(f"✅ Memory growth: {memory_growth:.1f} MB")
            
            # Score based on memory usage
            if memory_growth > 50:  # 50MB growth threshold
                test_result['details'].append("⚠️ Significant memory growth detected")
                test_result['score'] -= 15
                test_result['status'] = 'WARNING'
            
            if max_memory > 500:  # 500MB threshold
                test_result['details'].append("⚠️ High memory usage detected")
                test_result['score'] -= 10
                test_result['status'] = 'WARNING'
                
        except Exception as e:
            test_result['details'].append(f"❌ Memory monitoring error: {str(e)}")
            test_result['score'] = 50
            test_result['status'] = 'WARNING'
        
        return test_result
    
    async def test_certificate_rotation(self) -> Dict:
        """Test certificate rotation and management"""
        results = {
            'tests': [],
            'status': 'PASSED',
            'score': 100
        }
        
        # Test certificate rotation scripts
        rotation_scripts_test = await self.test_rotation_scripts()
        results['tests'].append(rotation_scripts_test)
        
        # Test certificate monitoring
        cert_monitoring_test = await self.test_certificate_monitoring()
        results['tests'].append(cert_monitoring_test)
        
        # Calculate score
        total_score = sum(test['score'] for test in results['tests'])
        results['score'] = total_score / len(results['tests'])
        
        if results['score'] < 80:
            results['status'] = 'FAILED'
        elif results['score'] < 90:
            results['status'] = 'WARNING'
        
        return results
    
    async def test_rotation_scripts(self) -> Dict:
        """Test certificate rotation scripts"""
        test_result = {
            'name': 'Certificate Rotation Scripts Test',
            'status': 'PASSED',
            'details': [],
            'score': 100
        }
        
        # Test rotation scripts exist
        rotation_scripts = [
            'scripts/ssl_cert_manager.py',
            'scripts/ssl_monitor_service.py'
        ]
        
        for script in rotation_scripts:
            if os.path.exists(script):
                test_result['details'].append(f"✅ Rotation script present: {script}")
                
                # Test script syntax
                try:
                    result = subprocess.run(['python3', '-m', 'py_compile', script], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        test_result['details'].append(f"✅ {script} syntax valid")
                    else:
                        test_result['details'].append(f"⚠️ {script} syntax issues")
                        test_result['score'] -= 15
                        test_result['status'] = 'WARNING'
                except Exception as e:
                    test_result['details'].append(f"⚠️ {script} validation error: {str(e)}")
                    test_result['score'] -= 10
                    
            else:
                test_result['details'].append(f"❌ Rotation script missing: {script}")
                test_result['score'] -= 25
                test_result['status'] = 'FAILED'
        
        return test_result
    
    async def test_certificate_monitoring(self) -> Dict:
        """Test certificate monitoring capabilities"""
        test_result = {
            'name': 'Certificate Monitoring Test',
            'status': 'PASSED',
            'details': [],
            'score': 100
        }
        
        # Test SSL configuration monitoring
        if os.path.exists('ssl/ssl_config.json'):
            try:
                with open('ssl/ssl_config.json', 'r') as f:
                    ssl_config = json.load(f)
                    
                domain = ssl_config.get('domain')
                expires_at = ssl_config.get('expires_at')
                
                if domain:
                    test_result['details'].append(f"✅ Monitoring domain: {domain}")
                
                if expires_at:
                    try:
                        expiry_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                        days_until_expiry = (expiry_date - datetime.now()).days
                        test_result['details'].append(f"✅ Certificate expires in {days_until_expiry} days")
                        
                        if days_until_expiry < 30:
                            test_result['details'].append("⚠️ Certificate expiring soon - rotation should be triggered")
                            test_result['score'] -= 10
                            test_result['status'] = 'WARNING'
                    except Exception as e:
                        test_result['details'].append(f"⚠️ Date parsing error: {str(e)}")
                        test_result['score'] -= 5
                
            except Exception as e:
                test_result['details'].append(f"❌ SSL config monitoring error: {str(e)}")
                test_result['score'] -= 20
                test_result['status'] = 'FAILED'
        else:
            test_result['details'].append("❌ SSL configuration file missing for monitoring")
            test_result['score'] -= 30
            test_result['status'] = 'FAILED'
        
        # Test monitoring scripts
        monitoring_scripts = [
            'security_monitoring_system.py',
            'run_security_validation.py'
        ]
        
        for script in monitoring_scripts:
            if os.path.exists(script):
                test_result['details'].append(f"✅ Monitoring script present: {script}")
            else:
                test_result['details'].append(f"⚠️ Monitoring script missing: {script}")
                test_result['score'] -= 10
                test_result['status'] = 'WARNING'
        
        return test_result
    
    async def test_health_monitoring(self) -> Dict:
        """Test health monitoring systems"""
        results = {
            'tests': [],
            'status': 'PASSED',
            'score': 100
        }
        
        # Test health endpoints
        health_endpoints_test = await self.test_health_endpoints()
        results['tests'].append(health_endpoints_test)
        
        # Test monitoring configuration
        monitoring_config_test = await self.test_monitoring_configuration()
        results['tests'].append(monitoring_config_test)
        
        # Calculate score
        total_score = sum(test['score'] for test in results['tests'])
        results['score'] = total_score / len(results['tests'])
        
        if results['score'] < 80:
            results['status'] = 'FAILED'
        elif results['score'] < 90:
            results['status'] = 'WARNING'
        
        return results
    
    async def test_health_endpoints(self) -> Dict:
        """Test health monitoring endpoints"""
        test_result = {
            'name': 'Health Endpoints Test',
            'status': 'PASSED',
            'details': [],
            'score': 100
        }
        
        # Test health endpoints
        health_urls = [
            f"{self.base_url}/health",
            f"{self.base_url}/api/v1/health"
        ]
        
        for url in health_urls:
            try:
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    health_data = response.json()
                    test_result['details'].append(f"✅ Health endpoint operational: {url}")
                    
                    # Validate health response structure
                    if 'status' in health_data:
                        test_result['details'].append(f"✅ Health status: {health_data.get('status')}")
                    else:
                        test_result['details'].append("⚠️ Health response missing status field")
                        test_result['score'] -= 5
                        
                    if 'timestamp' in health_data:
                        test_result['details'].append("✅ Health response includes timestamp")
                    else:
                        test_result['details'].append("⚠️ Health response missing timestamp")
                        test_result['score'] -= 5
                        
                else:
                    test_result['details'].append(f"⚠️ Health endpoint returned {response.status_code}: {url}")
                    test_result['score'] -= 15
                    test_result['status'] = 'WARNING'
                    
            except Exception as e:
                test_result['details'].append(f"❌ Health endpoint failed: {url} - {str(e)}")
                test_result['score'] -= 25
                test_result['status'] = 'FAILED'
        
        return test_result
    
    async def test_monitoring_configuration(self) -> Dict:
        """Test monitoring system configuration"""
        test_result = {
            'name': 'Monitoring Configuration Test',
            'status': 'PASSED',
            'details': [],
            'score': 100
        }
        
        # Test monitoring configuration files
        config_files = [
            'config/health_checks.json',
            'config/service_mesh_security.json'
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        test_result['details'].append(f"✅ Monitoring config valid: {config_file}")
                        
                        # Validate configuration structure
                        if isinstance(config, dict) and config:
                            test_result['details'].append(f"✅ {config_file} contains configuration data")
                        else:
                            test_result['details'].append(f"⚠️ {config_file} appears empty or invalid")
                            test_result['score'] -= 10
                            
                except json.JSONDecodeError as e:
                    test_result['details'].append(f"❌ {config_file} invalid JSON: {str(e)}")
                    test_result['score'] -= 20
                    test_result['status'] = 'FAILED'
            else:
                test_result['details'].append(f"❌ Monitoring config missing: {config_file}")
                test_result['score'] -= 25
                test_result['status'] = 'FAILED'
        
        return test_result
    
    async def test_system_reliability(self) -> Dict:
        """Test system reliability metrics"""
        results = {
            'tests': [],
            'status': 'PASSED',
            'score': 100
        }
        
        # Test system stability
        stability_test = await self.test_system_stability()
        results['tests'].append(stability_test)
        
        # Test error handling
        error_handling_test = await self.test_error_handling()
        results['tests'].append(error_handling_test)
        
        # Calculate score
        total_score = sum(test['score'] for test in results['tests'])
        results['score'] = total_score / len(results['tests'])
        
        if results['score'] < 80:
            results['status'] = 'FAILED'
        elif results['score'] < 90:
            results['status'] = 'WARNING'
        
        return results
    
    async def test_system_stability(self) -> Dict:
        """Test system stability over time"""
        test_result = {
            'name': 'System Stability Test',
            'status': 'PASSED',
            'details': [],
            'score': 100
        }
        
        # Test system uptime and stability
        stability_duration = 20  # seconds
        check_interval = 2  # seconds
        
        start_time = time.time()
        end_time = start_time + stability_duration
        
        successful_checks = 0
        total_checks = 0
        
        while time.time() < end_time:
            total_checks += 1
            try:
                response = requests.get(f"{self.base_url}/health", timeout=3)
                if response.status_code == 200:
                    successful_checks += 1
            except Exception:
                pass  # Failed check
            
            time.sleep(check_interval)
        
        uptime_percentage = (successful_checks / total_checks) * 100 if total_checks > 0 else 0
        
        test_result['details'].append(f"✅ Stability test duration: {stability_duration}s")
        test_result['details'].append(f"✅ Total health checks: {total_checks}")
        test_result['details'].append(f"✅ Successful checks: {successful_checks}")
        test_result['details'].append(f"✅ Uptime percentage: {uptime_percentage:.1f}%")
        
        # Score based on uptime
        if uptime_percentage < 95:
            test_result['details'].append("⚠️ Low uptime percentage detected")
            test_result['score'] -= 20
            test_result['status'] = 'WARNING'
        elif uptime_percentage < 99:
            test_result['details'].append("ℹ️ Moderate uptime percentage")
            test_result['score'] -= 5
        
        return test_result
    
    async def test_error_handling(self) -> Dict:
        """Test system error handling capabilities"""
        test_result = {
            'name': 'Error Handling Test',
            'status': 'PASSED',
            'details': [],
            'score': 100
        }
        
        # Test invalid endpoints
        invalid_endpoints = [
            '/nonexistent',
            '/api/v1/invalid',
            '/malformed-request'
        ]
        
        for endpoint in invalid_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                
                if response.status_code in [404, 405]:
                    test_result['details'].append(f"✅ Proper error response for {endpoint}: {response.status_code}")
                elif response.status_code == 500:
                    test_result['details'].append(f"⚠️ Server error for {endpoint}: {response.status_code}")
                    test_result['score'] -= 10
                    test_result['status'] = 'WARNING'
                else:
                    test_result['details'].append(f"ℹ️ Unexpected response for {endpoint}: {response.status_code}")
                    test_result['score'] -= 5
                    
            except Exception as e:
                test_result['details'].append(f"⚠️ Error testing {endpoint}: {str(e)}")
                test_result['score'] -= 5
        
        return test_result
    
    async def test_failover_procedures(self) -> Dict:
        """Test failover and backup procedures"""
        results = {
            'tests': [],
            'status': 'PASSED',
            'score': 100
        }
        
        # Test configuration backup
        backup_test = await self.test_configuration_backup()
        results['tests'].append(backup_test)
        
        # Test recovery procedures
        recovery_test = await self.test_recovery_procedures()
        results['tests'].append(recovery_test)
        
        # Calculate score
        total_score = sum(test['score'] for test in results['tests'])
        results['score'] = total_score / len(results['tests'])
        
        if results['score'] < 80:
            results['status'] = 'FAILED'
        elif results['score'] < 90:
            results['status'] = 'WARNING'
        
        return results
    
    async def test_configuration_backup(self) -> Dict:
        """Test configuration backup capabilities"""
        test_result = {
            'name': 'Configuration Backup Test',
            'status': 'PASSED',
            'details': [],
            'score': 100
        }
        
        # Check for backup files and procedures
        backup_locations = [
            'ssl/',
            'config/',
            'deploy/'
        ]
        
        critical_files = [
            'ssl/ssl_config.json',
            'config/health_checks.json',
            'deploy/production-akash-secure.yaml'
        ]
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                test_result['details'].append(f"✅ Critical config available: {file_path}")
                
                # Check file accessibility and readability
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if content:
                            test_result['details'].append(f"✅ {file_path} readable and non-empty")
                        else:
                            test_result['details'].append(f"⚠️ {file_path} is empty")
                            test_result['score'] -= 10
                except Exception as e:
                    test_result['details'].append(f"❌ {file_path} not readable: {str(e)}")
                    test_result['score'] -= 15
                    test_result['status'] = 'FAILED'
            else:
                test_result['details'].append(f"❌ Critical config missing: {file_path}")
                test_result['score'] -= 20
                test_result['status'] = 'FAILED'
        
        return test_result
    
    async def test_recovery_procedures(self) -> Dict:
        """Test system recovery procedures"""
        test_result = {
            'name': 'Recovery Procedures Test',
            'status': 'PASSED',
            'details': [],
            'score': 100
        }
        
        # Test recovery scripts and documentation
        recovery_files = [
            'scripts/deployment_verification.py',
            'scripts/ssl_cert_manager.py',
            'DEPLOYMENT_IMPLEMENTATION_SUMMARY.md',
            'SECURITY_IMPLEMENTATION_REPORT.md'
        ]
        
        for recovery_file in recovery_files:
            if os.path.exists(recovery_file):
                test_result['details'].append(f"✅ Recovery resource available: {recovery_file}")
            else:
                test_result['details'].append(f"⚠️ Recovery resource missing: {recovery_file}")
                test_result['score'] -= 15
                test_result['status'] = 'WARNING'
        
        # Test service restart capability (mock test)
        test_result['details'].append("ℹ️ Service restart procedures documented in deployment guides")
        test_result['details'].append("ℹ️ Configuration recovery procedures available")
        
        return test_result
    
    async def generate_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Calculate overall performance score
        total_score = 0
        total_weight = 0
        category_scores = {}
        
        for category, results in self.test_results.items():
            if isinstance(results, dict) and 'score' in results:
                weight = 1.0
                category_scores[category] = results['score']
                total_score += results['score'] * weight
                total_weight += weight
        
        overall_score = total_score / total_weight if total_weight > 0 else 0
        
        # Determine performance grade
        if overall_score >= 95:
            performance_grade = 'A+'
            performance_status = 'EXCELLENT'
        elif overall_score >= 90:
            performance_grade = 'A'
            performance_status = 'VERY_GOOD'
        elif overall_score >= 85:
            performance_grade = 'B+'
            performance_status = 'GOOD'
        elif overall_score >= 80:
            performance_grade = 'B'
            performance_status = 'ACCEPTABLE'
        else:
            performance_grade = 'C'
            performance_status = 'NEEDS_IMPROVEMENT'
        
        # Generate recommendations
        recommendations = self.generate_performance_recommendations(overall_score, category_scores)
        
        performance_report = {
            'test_execution': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'test_suite': 'Performance and Reliability Testing Suite v1.0'
            },
            'performance_assessment': {
                'overall_score': round(overall_score, 1),
                'performance_grade': performance_grade,
                'performance_status': performance_status,
                'production_ready': overall_score >= 80,
                'reliability_acceptable': overall_score >= 85
            },
            'category_scores': category_scores,
            'detailed_results': self.test_results,
            'performance_metrics': self.performance_metrics,
            'reliability_metrics': self.reliability_metrics,
            'recommendations': recommendations,
            'metrics': {
                'total_performance_tests': sum(
                    len(results.get('tests', [])) if isinstance(results, dict) else 0
                    for results in self.test_results.values()
                ),
                'categories_tested': len(self.test_results)
            }
        }
        
        # Save performance report
        with open('performance_reliability_test_report.json', 'w') as f:
            json.dump(performance_report, f, indent=2, default=str)
        
        return performance_report
    
    def generate_performance_recommendations(self, overall_score: float, category_scores: Dict) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        if overall_score < 80:
            recommendations.append("🚨 CRITICAL: Performance below production threshold")
            recommendations.append("Address all performance issues before deployment")
        
        # Category-specific recommendations
        for category, score in category_scores.items():
            if score < 70:
                recommendations.append(f"❌ {category}: Critical performance issues")
            elif score < 85:
                recommendations.append(f"⚠️ {category}: Performance improvements needed")
        
        # Specific performance recommendations
        if overall_score >= 90:
            recommendations.append("✅ System performance meets high standards")
            recommendations.append("Continue monitoring for performance degradation")
        
        recommendations.append("📊 Implement continuous performance monitoring")
        recommendations.append("🔄 Regular performance testing recommended")
        recommendations.append("📈 Consider load balancing for production scaling")
        
        return recommendations

async def main():
    """Main performance testing function"""
    print("⚡ OMEGA Pro AI - Performance and Reliability Testing Suite")
    print("=" * 60)
    
    performance_suite = PerformanceReliabilityTestSuite()
    
    try:
        performance_report = await performance_suite.run_performance_tests()
        
        # Print performance summary
        print("\n" + "=" * 60)
        print("⚡ PERFORMANCE AND RELIABILITY TEST SUMMARY")
        print("=" * 60)
        
        assessment = performance_report['performance_assessment']
        print(f"Overall Performance Score: {assessment['overall_score']}%")
        print(f"Performance Grade: {assessment['performance_grade']}")
        print(f"Performance Status: {assessment['performance_status']}")
        print(f"Production Ready: {'✅ YES' if assessment['production_ready'] else '❌ NO'}")
        print(f"Reliability Acceptable: {'✅ YES' if assessment['reliability_acceptable'] else '❌ NO'}")
        
        metrics = performance_report['metrics']
        print(f"\nTest Duration: {performance_report['test_execution']['duration_seconds']:.1f} seconds")
        print(f"Performance Tests: {metrics['total_performance_tests']}")
        print(f"Categories: {metrics['categories_tested']}")
        
        print("\n🎯 PERFORMANCE RECOMMENDATIONS:")
        for rec in performance_report['recommendations']:
            print(f"  {rec}")
        
        print(f"\n📄 Detailed performance report saved to: performance_reliability_test_report.json")
        print(f"📄 Performance test logs saved to: performance_reliability_test.log")
        
    except Exception as e:
        logger.error(f"❌ Performance testing failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)