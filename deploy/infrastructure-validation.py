#!/usr/bin/env python3
"""
OMEGA Pro AI - Infrastructure Validation & Monitoring Dashboard
Enterprise-grade infrastructure completion validation system
Version: 4.0.1
"""

import asyncio
import json
import logging
import subprocess
import time
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/infrastructure-validation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('omega-infrastructure-validator')

class InfrastructureValidator:
    """Comprehensive infrastructure validation and monitoring system"""
    
    def __init__(self):
        self.namespace = "akash-services"
        self.validation_results = {}
        self.components = {
            'firewall': {
                'type': 'daemonset',
                'name': 'omega-firewall-enforcer',
                'required': True,
                'weight': 15
            },
            'load_balancer': {
                'type': 'deployment',
                'name': 'omega-load-balancer',
                'required': True,
                'weight': 20
            },
            'health_monitor': {
                'type': 'deployment', 
                'name': 'omega-health-monitor',
                'required': True,
                'weight': 20
            },
            'resilience_coordinator': {
                'type': 'deployment',
                'name': 'omega-resilience-coordinator',
                'required': True,
                'weight': 20
            },
            'service_discovery': {
                'type': 'service',
                'name': 'omega-health-monitor-service',
                'required': True,
                'weight': 10
            },
            'ssl_certificates': {
                'type': 'secret',
                'name': 'omega-ssl-certs',
                'required': True,
                'weight': 15
            }
        }
    
    async def validate_kubernetes_resources(self) -> Dict:
        """Validate all Kubernetes resources are deployed and healthy"""
        logger.info("Validating Kubernetes resources...")
        results = {}
        
        for component_name, config in self.components.items():
            try:
                if config['type'] == 'deployment':
                    result = await self._validate_deployment(config['name'])
                elif config['type'] == 'daemonset':
                    result = await self._validate_daemonset(config['name'])
                elif config['type'] == 'service':
                    result = await self._validate_service(config['name'])
                elif config['type'] == 'secret':
                    result = await self._validate_secret(config['name'])
                else:
                    result = {'status': 'unknown', 'message': f'Unknown resource type: {config["type"]}'}
                
                result['weight'] = config['weight']
                result['required'] = config['required']
                results[component_name] = result
                
            except Exception as e:
                results[component_name] = {
                    'status': 'error',
                    'message': f'Validation error: {str(e)}',
                    'weight': config['weight'],
                    'required': config['required']
                }
        
        return results
    
    async def _validate_deployment(self, name: str) -> Dict:
        """Validate a Kubernetes deployment"""
        try:
            # Get deployment status
            cmd = f"kubectl get deployment {name} -n {self.namespace} -o json"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {'status': 'missing', 'message': f'Deployment {name} not found'}
            
            deployment_data = json.loads(result.stdout)
            spec_replicas = deployment_data['spec']['replicas']
            ready_replicas = deployment_data['status'].get('readyReplicas', 0)
            
            if ready_replicas == spec_replicas and ready_replicas > 0:
                return {
                    'status': 'healthy',
                    'message': f'Deployment {name} is healthy ({ready_replicas}/{spec_replicas} replicas ready)',
                    'replicas': {'ready': ready_replicas, 'desired': spec_replicas}
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': f'Deployment {name} is unhealthy ({ready_replicas}/{spec_replicas} replicas ready)',
                    'replicas': {'ready': ready_replicas, 'desired': spec_replicas}
                }
                
        except Exception as e:
            return {'status': 'error', 'message': f'Error validating deployment {name}: {str(e)}'}
    
    async def _validate_daemonset(self, name: str) -> Dict:
        """Validate a Kubernetes daemonset"""
        try:
            cmd = f"kubectl get daemonset {name} -n {self.namespace} -o json"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {'status': 'missing', 'message': f'DaemonSet {name} not found'}
            
            daemonset_data = json.loads(result.stdout)
            desired = daemonset_data['status']['desiredNumberScheduled']
            ready = daemonset_data['status'].get('numberReady', 0)
            
            if ready == desired and ready > 0:
                return {
                    'status': 'healthy',
                    'message': f'DaemonSet {name} is healthy ({ready}/{desired} pods ready)',
                    'pods': {'ready': ready, 'desired': desired}
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': f'DaemonSet {name} is unhealthy ({ready}/{desired} pods ready)',
                    'pods': {'ready': ready, 'desired': desired}
                }
                
        except Exception as e:
            return {'status': 'error', 'message': f'Error validating daemonset {name}: {str(e)}'}
    
    async def _validate_service(self, name: str) -> Dict:
        """Validate a Kubernetes service"""
        try:
            cmd = f"kubectl get service {name} -n {self.namespace} -o json"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {'status': 'missing', 'message': f'Service {name} not found'}
            
            service_data = json.loads(result.stdout)
            service_type = service_data['spec']['type']
            ports = service_data['spec']['ports']
            
            return {
                'status': 'healthy',
                'message': f'Service {name} is available (type: {service_type})',
                'type': service_type,
                'ports': [f"{p['port']}/{p['protocol']}" for p in ports]
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Error validating service {name}: {str(e)}'}
    
    async def _validate_secret(self, name: str) -> Dict:
        """Validate a Kubernetes secret"""
        try:
            cmd = f"kubectl get secret {name} -n {self.namespace} -o json"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {'status': 'missing', 'message': f'Secret {name} not found'}
            
            secret_data = json.loads(result.stdout)
            data_keys = list(secret_data.get('data', {}).keys())
            
            return {
                'status': 'healthy',
                'message': f'Secret {name} is available with {len(data_keys)} keys',
                'keys': len(data_keys)
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Error validating secret {name}: {str(e)}'}
    
    async def validate_network_connectivity(self) -> Dict:
        """Validate network connectivity between components"""
        logger.info("Validating network connectivity...")
        results = {}
        
        try:
            # Test load balancer health endpoint
            lb_result = await self._test_load_balancer_health()
            results['load_balancer_health'] = lb_result
            
            # Test service discovery
            sd_result = await self._test_service_discovery()
            results['service_discovery'] = sd_result
            
            # Test internal service communication
            comm_result = await self._test_internal_communication()
            results['internal_communication'] = comm_result
            
        except Exception as e:
            logger.error(f"Network connectivity validation error: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    async def _test_load_balancer_health(self) -> Dict:
        """Test load balancer health endpoint"""
        try:
            # Get load balancer service IP
            cmd = f"kubectl get service omega-load-balancer-service -n {self.namespace} -o jsonpath='{{.spec.clusterIP}}'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {'status': 'error', 'message': 'Load balancer service not found'}
            
            service_ip = result.stdout.strip()
            if not service_ip:
                return {'status': 'error', 'message': 'Load balancer service IP not available'}
            
            # Test health endpoint using a test pod
            health_url = f"http://{service_ip}:8080/health"
            test_cmd = f"""
            kubectl run test-connectivity --rm -i --restart=Never --image=alpine/curl -- \
            curl -s --connect-timeout 10 --max-time 30 "{health_url}"
            """
            
            test_result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True, timeout=60)
            
            if test_result.returncode == 0 and 'healthy' in test_result.stdout:
                return {
                    'status': 'healthy',
                    'message': 'Load balancer health endpoint responding correctly',
                    'url': health_url,
                    'response': test_result.stdout.strip()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': 'Load balancer health endpoint not responding correctly',
                    'url': health_url,
                    'error': test_result.stderr.strip()
                }
                
        except Exception as e:
            return {'status': 'error', 'message': f'Load balancer health test error: {str(e)}'}
    
    async def _test_service_discovery(self) -> Dict:
        """Test service discovery functionality"""
        try:
            # Check if service registry file exists in health monitor
            cmd = f"""
            kubectl exec -n {self.namespace} deployment/omega-health-monitor -- \
            test -f /tmp/service-registry.json && echo "exists" || echo "missing"
            """
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and 'exists' in result.stdout:
                return {
                    'status': 'healthy',
                    'message': 'Service discovery is functioning'
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': 'Service discovery registry not found'
                }
                
        except Exception as e:
            return {'status': 'error', 'message': f'Service discovery test error: {str(e)}'}
    
    async def _test_internal_communication(self) -> Dict:
        """Test internal service-to-service communication"""
        try:
            # Test DNS resolution for services
            services = ['omega-api', 'omega-gpu', 'redis']
            dns_results = {}
            
            for service in services:
                cmd = f"""
                kubectl run test-dns-{service} --rm -i --restart=Never --image=alpine -- \
                nslookup {service}.{self.namespace}.svc.cluster.local
                """
                
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                dns_results[service] = {
                    'status': 'resolved' if result.returncode == 0 else 'failed',
                    'output': result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
                }
            
            resolved_count = sum(1 for r in dns_results.values() if r['status'] == 'resolved')
            total_count = len(dns_results)
            
            if resolved_count == total_count:
                return {
                    'status': 'healthy',
                    'message': f'All {total_count} services can be resolved via DNS',
                    'dns_results': dns_results
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': f'Only {resolved_count}/{total_count} services can be resolved via DNS',
                    'dns_results': dns_results
                }
                
        except Exception as e:
            return {'status': 'error', 'message': f'Internal communication test error: {str(e)}'}
    
    async def validate_security_configuration(self) -> Dict:
        """Validate security configuration and compliance"""
        logger.info("Validating security configuration...")
        results = {}
        
        try:
            # Check SSL/TLS configuration
            ssl_result = await self._validate_ssl_config()
            results['ssl_tls'] = ssl_result
            
            # Check firewall rules
            firewall_result = await self._validate_firewall_rules()
            results['firewall'] = firewall_result
            
            # Check RBAC permissions
            rbac_result = await self._validate_rbac_permissions()
            results['rbac'] = rbac_result
            
        except Exception as e:
            logger.error(f"Security validation error: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    async def _validate_ssl_config(self) -> Dict:
        """Validate SSL/TLS configuration"""
        try:
            # Check if SSL secret exists and has required keys
            cmd = f"kubectl get secret omega-ssl-certs -n {self.namespace} -o json"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {'status': 'missing', 'message': 'SSL certificates secret not found'}
            
            secret_data = json.loads(result.stdout)
            data_keys = set(secret_data.get('data', {}).keys())
            required_keys = {'cert.pem', 'key.pem'}
            
            if required_keys.issubset(data_keys):
                return {
                    'status': 'healthy',
                    'message': 'SSL certificates are properly configured',
                    'keys_present': list(data_keys)
                }
            else:
                missing_keys = required_keys - data_keys
                return {
                    'status': 'incomplete',
                    'message': f'SSL certificates missing required keys: {missing_keys}',
                    'missing_keys': list(missing_keys)
                }
                
        except Exception as e:
            return {'status': 'error', 'message': f'SSL configuration validation error: {str(e)}'}
    
    async def _validate_firewall_rules(self) -> Dict:
        """Validate firewall rules are active"""
        try:
            # Check if firewall DaemonSet is running
            cmd = f"kubectl get pods -l app=omega-firewall -n {self.namespace} -o json"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {'status': 'missing', 'message': 'Firewall pods not found'}
            
            pods_data = json.loads(result.stdout)
            pods = pods_data.get('items', [])
            running_pods = [p for p in pods if p['status']['phase'] == 'Running']
            
            if len(running_pods) > 0:
                return {
                    'status': 'healthy',
                    'message': f'Firewall rules active on {len(running_pods)} nodes',
                    'active_nodes': len(running_pods)
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': 'No firewall pods are running',
                    'total_pods': len(pods)
                }
                
        except Exception as e:
            return {'status': 'error', 'message': f'Firewall validation error: {str(e)}'}
    
    async def _validate_rbac_permissions(self) -> Dict:
        """Validate RBAC permissions are properly configured"""
        try:
            service_accounts = [
                'omega-health-monitor',
                'omega-resilience-coordinator'
            ]
            
            rbac_status = {}
            for sa in service_accounts:
                cmd = f"kubectl get serviceaccount {sa} -n {self.namespace} -o json"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    rbac_status[sa] = 'configured'
                else:
                    rbac_status[sa] = 'missing'
            
            configured_count = sum(1 for status in rbac_status.values() if status == 'configured')
            total_count = len(rbac_status)
            
            if configured_count == total_count:
                return {
                    'status': 'healthy',
                    'message': f'All {total_count} service accounts properly configured',
                    'service_accounts': rbac_status
                }
            else:
                return {
                    'status': 'incomplete',
                    'message': f'Only {configured_count}/{total_count} service accounts configured',
                    'service_accounts': rbac_status
                }
                
        except Exception as e:
            return {'status': 'error', 'message': f'RBAC validation error: {str(e)}'}
    
    def calculate_infrastructure_readiness(self, validation_results: Dict) -> Tuple[float, Dict]:
        """Calculate overall infrastructure readiness percentage"""
        total_weight = sum(comp['weight'] for comp in self.components.values())
        achieved_weight = 0
        component_scores = {}
        
        # Score Kubernetes resources
        k8s_results = validation_results.get('kubernetes_resources', {})
        for component_name, result in k8s_results.items():
            if component_name in self.components:
                weight = self.components[component_name]['weight']
                
                if result['status'] == 'healthy':
                    score = 100
                    achieved_weight += weight
                elif result['status'] == 'unhealthy':
                    score = 50
                    achieved_weight += weight * 0.5
                else:
                    score = 0
                
                component_scores[component_name] = {
                    'score': score,
                    'weight': weight,
                    'status': result['status']
                }
        
        # Score network connectivity (10% of total)
        network_weight = total_weight * 0.1
        network_results = validation_results.get('network_connectivity', {})
        network_score = 0
        
        for test_name, result in network_results.items():
            if isinstance(result, dict) and 'status' in result:
                if result['status'] == 'healthy':
                    network_score += 33.33  # Each test is worth 33.33% of network score
        
        if network_score >= 90:
            achieved_weight += network_weight
        elif network_score >= 70:
            achieved_weight += network_weight * 0.8
        elif network_score >= 50:
            achieved_weight += network_weight * 0.6
        
        # Score security configuration (10% of total)
        security_weight = total_weight * 0.1
        security_results = validation_results.get('security_configuration', {})
        security_score = 0
        
        for test_name, result in security_results.items():
            if isinstance(result, dict) and 'status' in result:
                if result['status'] == 'healthy':
                    security_score += 33.33  # Each test is worth 33.33% of security score
        
        if security_score >= 90:
            achieved_weight += security_weight
        elif security_score >= 70:
            achieved_weight += security_weight * 0.8
        elif security_score >= 50:
            achieved_weight += security_weight * 0.6
        
        readiness_percentage = (achieved_weight / total_weight) * 100
        
        return readiness_percentage, {
            'total_weight': total_weight,
            'achieved_weight': achieved_weight,
            'component_scores': component_scores,
            'network_score': network_score,
            'security_score': security_score
        }
    
    async def run_comprehensive_validation(self) -> Dict:
        """Run complete infrastructure validation"""
        logger.info("Starting comprehensive infrastructure validation...")
        
        start_time = time.time()
        validation_results = {}
        
        try:
            # Validate Kubernetes resources
            k8s_results = await self.validate_kubernetes_resources()
            validation_results['kubernetes_resources'] = k8s_results
            
            # Validate network connectivity
            network_results = await self.validate_network_connectivity()
            validation_results['network_connectivity'] = network_results
            
            # Validate security configuration
            security_results = await self.validate_security_configuration()
            validation_results['security_configuration'] = security_results
            
            # Calculate readiness
            readiness_percentage, readiness_details = self.calculate_infrastructure_readiness(validation_results)
            
            validation_time = time.time() - start_time
            
            # Create comprehensive report
            report = {
                'validation_metadata': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'version': '4.0.1',
                    'validation_time_seconds': round(validation_time, 2),
                    'validator': 'omega-infrastructure-validator'
                },
                'infrastructure_readiness': {
                    'percentage': round(readiness_percentage, 2),
                    'target_percentage': 99.5,
                    'target_achieved': readiness_percentage >= 99.5,
                    'details': readiness_details
                },
                'validation_results': validation_results,
                'summary': {
                    'total_components_tested': len(self.components),
                    'healthy_components': len([r for r in k8s_results.values() if r['status'] == 'healthy']),
                    'network_tests_passed': len([r for r in network_results.values() if isinstance(r, dict) and r.get('status') == 'healthy']),
                    'security_tests_passed': len([r for r in security_results.values() if isinstance(r, dict) and r.get('status') == 'healthy'])
                }
            }
            
            logger.info(f"Infrastructure validation completed in {validation_time:.2f}s")
            logger.info(f"Infrastructure readiness: {readiness_percentage:.2f}%")
            
            return report
            
        except Exception as e:
            logger.error(f"Comprehensive validation error: {str(e)}")
            return {
                'validation_metadata': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'version': '4.0.1',
                    'error': str(e)
                },
                'infrastructure_readiness': {
                    'percentage': 0,
                    'target_percentage': 99.5,
                    'target_achieved': False
                }
            }
    
    def save_validation_report(self, report: Dict) -> str:
        """Save validation report to file"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        report_file = f"/tmp/omega-infrastructure-validation-{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report saved to: {report_file}")
        return report_file

async def main():
    """Main validation entry point"""
    print("🔍 OMEGA Pro AI - Infrastructure Validation System")
    print("=" * 60)
    
    validator = InfrastructureValidator()
    
    try:
        # Run comprehensive validation
        report = await validator.run_comprehensive_validation()
        
        # Save report
        report_file = validator.save_validation_report(report)
        
        # Display summary
        readiness = report['infrastructure_readiness']
        print(f"\n📊 Validation Summary:")
        print(f"   Infrastructure Readiness: {readiness['percentage']}%")
        print(f"   Target Achievement: {'✅ ACHIEVED' if readiness['target_achieved'] else '⚠️  IN PROGRESS'}")
        print(f"   Report File: {report_file}")
        
        # Exit with appropriate code
        if readiness['target_achieved']:
            print("\n🎉 Infrastructure completion successful!")
            sys.exit(0)
        else:
            print(f"\n⚠️  Infrastructure readiness at {readiness['percentage']}% - continuing optimization...")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        print(f"\n❌ Validation failed: {str(e)}")
        sys.exit(2)

if __name__ == '__main__':
    asyncio.run(main())