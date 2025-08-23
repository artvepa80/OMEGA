#!/usr/bin/env python3
"""
🔐 Service Mesh Security Configuration for OMEGA Pro AI
Implements secure inter-service communication and monitoring for Akash deployments
"""

import click
import json
import yaml
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceMeshSecurity:
    """Service mesh security management"""
    
    def __init__(self, config_dir: str = "./config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.security_config = self.config_dir / "service_mesh_security.json"
        self.health_config = self.config_dir / "health_checks.json"
        
    def generate_service_security_config(self) -> Dict[str, Any]:
        """Generate comprehensive service security configuration"""
        
        config = {
            "metadata": {
                "name": "omega-service-mesh-security",
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "description": "OMEGA Pro AI Service Mesh Security Configuration"
            },
            "services": {
                "omega-api": {
                    "port": 8000,
                    "ssl_port": 8443,
                    "internal_port": 8000,
                    "protocol": "https",
                    "ssl_enabled": True,
                    "authentication": {
                        "required": True,
                        "type": "jwt",
                        "timeout": 3600
                    },
                    "rate_limiting": {
                        "enabled": True,
                        "requests_per_second": 20,
                        "burst": 50,
                        "auth_requests_per_second": 5,
                        "auth_burst": 10
                    },
                    "cors": {
                        "enabled": True,
                        "allowed_origins": [
                            "https://*.omega-pro.ai",
                            "https://localhost:*",
                            "capacitor://localhost",
                            "ionic://localhost"
                        ],
                        "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                        "allowed_headers": ["Content-Type", "Authorization", "X-Requested-With"],
                        "credentials": True
                    },
                    "security_headers": {
                        "X-Frame-Options": "DENY",
                        "X-Content-Type-Options": "nosniff",
                        "X-XSS-Protection": "1; mode=block",
                        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                        "Content-Security-Policy": "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval'",
                        "Referrer-Policy": "no-referrer-when-downgrade"
                    },
                    "health_check": {
                        "enabled": True,
                        "path": "/health",
                        "interval": 30,
                        "timeout": 10,
                        "retries": 3
                    }
                },
                "omega-gpu": {
                    "port": 8001,
                    "ssl_port": 8001,
                    "internal_port": 8001,
                    "protocol": "https",
                    "ssl_enabled": True,
                    "authentication": {
                        "required": True,
                        "type": "internal",
                        "allowed_sources": ["omega-api"]
                    },
                    "rate_limiting": {
                        "enabled": True,
                        "requests_per_second": 10,
                        "burst": 20,
                        "max_concurrent": 5
                    },
                    "resource_limits": {
                        "max_memory_usage": 90,
                        "max_gpu_memory": 90,
                        "max_processing_time": 300
                    },
                    "health_check": {
                        "enabled": True,
                        "path": "/gpu/health",
                        "interval": 45,
                        "timeout": 20,
                        "retries": 3,
                        "gpu_check": True
                    }
                },
                "redis": {
                    "port": 6379,
                    "internal_port": 6379,
                    "protocol": "redis",
                    "ssl_enabled": False,
                    "authentication": {
                        "required": True,
                        "type": "password",
                        "password_env": "REDIS_PASSWORD"
                    },
                    "access_control": {
                        "allowed_services": ["omega-api", "omega-gpu"],
                        "denied_external": True
                    },
                    "health_check": {
                        "enabled": True,
                        "command": "PING",
                        "interval": 30,
                        "timeout": 5,
                        "retries": 3
                    }
                }
            },
            "network_policies": {
                "inter_service_communication": {
                    "omega-api_to_omega-gpu": {
                        "allowed": True,
                        "protocol": "https",
                        "authentication_required": True
                    },
                    "omega-api_to_redis": {
                        "allowed": True,
                        "protocol": "redis",
                        "authentication_required": True
                    },
                    "omega-gpu_to_redis": {
                        "allowed": True,
                        "protocol": "redis",
                        "authentication_required": True
                    }
                },
                "external_access": {
                    "omega-api": {
                        "allowed_from": ["internet"],
                        "ports": [80, 443],
                        "ssl_required": True
                    },
                    "omega-gpu": {
                        "allowed_from": ["omega-api"],
                        "ports": [8001],
                        "ssl_required": True
                    },
                    "redis": {
                        "allowed_from": ["omega-api", "omega-gpu"],
                        "ports": [6379],
                        "external_access": False
                    }
                }
            },
            "monitoring": {
                "enabled": True,
                "metrics_port": 9090,
                "log_level": "INFO",
                "alerts": {
                    "high_error_rate": {
                        "threshold": 5.0,
                        "window": "5m"
                    },
                    "high_latency": {
                        "threshold": 2000,
                        "window": "1m"
                    },
                    "service_down": {
                        "threshold": 3,
                        "retries": 3
                    }
                }
            },
            "encryption": {
                "inter_service_tls": {
                    "enabled": True,
                    "min_tls_version": "1.2",
                    "cipher_suites": [
                        "ECDHE-RSA-AES256-GCM-SHA384",
                        "ECDHE-RSA-AES128-GCM-SHA256",
                        "ECDHE-RSA-CHACHA20-POLY1305"
                    ]
                },
                "data_at_rest": {
                    "enabled": True,
                    "algorithm": "AES-256-GCM"
                }
            }
        }
        
        return config
    
    def generate_health_checks(self) -> Dict[str, Any]:
        """Generate health check configurations"""
        
        health_config = {
            "health_checks": {
                "omega-api": {
                    "http": {
                        "url": "https://localhost:8443/health",
                        "method": "GET",
                        "timeout": 10,
                        "interval": 30,
                        "retries": 3,
                        "expected_status": 200,
                        "verify_ssl": False
                    },
                    "dependencies": ["redis"],
                    "custom_checks": [
                        {
                            "name": "database_connection",
                            "command": ["python", "-c", "import redis; r=redis.Redis(host='redis', port=6379); r.ping()"],
                            "timeout": 5
                        }
                    ]
                },
                "omega-gpu": {
                    "http": {
                        "url": "https://localhost:8001/gpu/health",
                        "method": "GET", 
                        "timeout": 20,
                        "interval": 45,
                        "retries": 3,
                        "expected_status": 200,
                        "verify_ssl": False
                    },
                    "dependencies": ["redis"],
                    "custom_checks": [
                        {
                            "name": "gpu_availability",
                            "command": ["python", "-c", "import torch; assert torch.cuda.is_available()"],
                            "timeout": 10
                        },
                        {
                            "name": "gpu_memory",
                            "command": ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
                            "timeout": 5,
                            "min_value": 1000
                        }
                    ]
                },
                "redis": {
                    "tcp": {
                        "host": "localhost",
                        "port": 6379,
                        "timeout": 5,
                        "interval": 30
                    },
                    "custom_checks": [
                        {
                            "name": "redis_ping",
                            "command": ["redis-cli", "ping"],
                            "timeout": 3,
                            "expected_output": "PONG"
                        },
                        {
                            "name": "redis_memory",
                            "command": ["redis-cli", "info", "memory"],
                            "timeout": 5
                        }
                    ]
                }
            },
            "global_settings": {
                "failure_threshold": 3,
                "success_threshold": 1,
                "check_timeout": 30,
                "notification": {
                    "enabled": True,
                    "webhook_url": "${HEALTH_WEBHOOK_URL}",
                    "slack_channel": "${SLACK_CHANNEL}"
                }
            }
        }
        
        return health_config
    
    def save_configurations(self):
        """Save security and health configurations"""
        
        # Generate and save service mesh security config
        security_config = self.generate_service_security_config()
        with open(self.security_config, 'w') as f:
            json.dump(security_config, f, indent=2)
        
        # Generate and save health check config
        health_config = self.generate_health_checks()
        with open(self.health_config, 'w') as f:
            json.dump(health_config, f, indent=2)
        
        logger.info(f"Security config saved to: {self.security_config}")
        logger.info(f"Health check config saved to: {self.health_config}")
    
    def generate_akash_security_manifest(self) -> Dict[str, Any]:
        """Generate Akash deployment manifest with security configurations"""
        
        manifest = {
            "version": "2.0",
            "services": {
                "omega-api": {
                    "image": "ghcr.io/omega-pro-ai/omega-api:latest",
                    "expose": [
                        {
                            "port": 8000,
                            "as": 80,
                            "to": [{"global": True}]
                        },
                        {
                            "port": 8443,
                            "as": 443,
                            "to": [{"global": True}]
                        }
                    ],
                    "env": [
                        "OMEGA_ENV=production",
                        "SSL_ENABLED=true",
                        "SECURITY_HEADERS=true",
                        "CORS_ENABLED=true",
                        "RATE_LIMITING=true",
                        "AUTH_REQUIRED=true",
                        "JWT_SECRET=${JWT_SECRET}",
                        "REDIS_URL=redis://redis:6379",
                        "REDIS_PASSWORD=${REDIS_PASSWORD}",
                        "LOG_LEVEL=INFO",
                        "HEALTH_CHECK_ENABLED=true"
                    ],
                    "resources": {
                        "cpu": {"units": 2.0},
                        "memory": {"size": "4Gi"},
                        "storage": [{"size": "20Gi"}]
                    }
                },
                "omega-gpu": {
                    "image": "ghcr.io/omega-pro-ai/omega-gpu:latest",
                    "expose": [
                        {
                            "port": 8001,
                            "to": [{"service": "omega-api"}]
                        }
                    ],
                    "env": [
                        "CUDA_VISIBLE_DEVICES=0",
                        "NVIDIA_VISIBLE_DEVICES=all",
                        "SSL_ENABLED=true",
                        "INTERNAL_AUTH=true",
                        "REDIS_URL=redis://redis:6379",
                        "REDIS_PASSWORD=${REDIS_PASSWORD}",
                        "MAX_CONCURRENT_REQUESTS=5",
                        "GPU_MEMORY_LIMIT=90",
                        "PROCESSING_TIMEOUT=300",
                        "LOG_LEVEL=INFO"
                    ],
                    "resources": {
                        "cpu": {"units": 4.0},
                        "memory": {"size": "8Gi"},
                        "storage": [{"size": "100Gi"}],
                        "gpu": {
                            "units": 1,
                            "attributes": {
                                "vendor": {
                                    "nvidia": [{
                                        "model": "rtx4090",
                                        "ram": "24Gi"
                                    }]
                                }
                            }
                        }
                    }
                },
                "redis": {
                    "image": "redis:7-alpine",
                    "command": [
                        "redis-server",
                        "--requirepass", "${REDIS_PASSWORD}",
                        "--maxmemory", "1gb",
                        "--maxmemory-policy", "allkeys-lru",
                        "--save", "900", "1",
                        "--save", "300", "10",
                        "--save", "60", "10000"
                    ],
                    "expose": [
                        {
                            "port": 6379,
                            "to": [
                                {"service": "omega-api"},
                                {"service": "omega-gpu"}
                            ]
                        }
                    ],
                    "env": [
                        "REDIS_PASSWORD=${REDIS_PASSWORD}"
                    ],
                    "resources": {
                        "cpu": {"units": 0.5},
                        "memory": {"size": "1Gi"},
                        "storage": [{"size": "10Gi"}]
                    }
                },
                "nginx-security": {
                    "image": "nginx:alpine",
                    "expose": [
                        {
                            "port": 80,
                            "as": 80,
                            "to": [{"global": True}]
                        },
                        {
                            "port": 443,
                            "as": 443,
                            "to": [{"global": True}]
                        }
                    ],
                    "env": [
                        "SSL_ENABLED=true",
                        "SECURITY_HEADERS=true",
                        "RATE_LIMITING=true"
                    ],
                    "resources": {
                        "cpu": {"units": 0.5},
                        "memory": {"size": "512Mi"},
                        "storage": [{"size": "1Gi"}]
                    }
                }
            },
            "profiles": {
                "compute": {
                    "omega-api": {
                        "resources": {
                            "cpu": {"units": 2.0},
                            "memory": {"size": "4Gi"},
                            "storage": [{"size": "20Gi"}]
                        }
                    },
                    "omega-gpu": {
                        "resources": {
                            "cpu": {"units": 4.0},
                            "memory": {"size": "8Gi"},
                            "storage": [{"size": "100Gi"}],
                            "gpu": {
                                "units": 1,
                                "attributes": {
                                    "vendor": {
                                        "nvidia": [{
                                            "model": "rtx4090",
                                            "ram": "24Gi"
                                        }]
                                    }
                                }
                            }
                        }
                    },
                    "redis": {
                        "resources": {
                            "cpu": {"units": 0.5},
                            "memory": {"size": "1Gi"},
                            "storage": [{"size": "10Gi"}]
                        }
                    },
                    "nginx-security": {
                        "resources": {
                            "cpu": {"units": 0.5},
                            "memory": {"size": "512Mi"},
                            "storage": [{"size": "1Gi"}]
                        }
                    }
                },
                "placement": {
                    "dcloud": {
                        "attributes": {
                            "host": "akash",
                            "region": "us-west"
                        },
                        "signedBy": {
                            "anyOf": [
                                "akash1365yvmc4s7awdyj3n2sav7xfx76adc6dnmlx63",
                                "akash18qa2a2ltfyvkyj0ggj3hkvuj6twzyumuaru9s4"
                            ]
                        },
                        "pricing": {
                            "omega-api": {
                                "denom": "uakt",
                                "amount": 500
                            },
                            "omega-gpu": {
                                "denom": "uakt",
                                "amount": 1000
                            },
                            "redis": {
                                "denom": "uakt",
                                "amount": 100
                            },
                            "nginx-security": {
                                "denom": "uakt",
                                "amount": 100
                            }
                        }
                    }
                }
            },
            "deployment": {
                "omega-api": {
                    "dcloud": {
                        "profile": "omega-api",
                        "count": 1
                    }
                },
                "omega-gpu": {
                    "dcloud": {
                        "profile": "omega-gpu",
                        "count": 1
                    }
                },
                "redis": {
                    "dcloud": {
                        "profile": "redis",
                        "count": 1
                    }
                },
                "nginx-security": {
                    "dcloud": {
                        "profile": "nginx-security",
                        "count": 1
                    }
                }
            }
        }
        
        return manifest

class HealthMonitor:
    """Health monitoring and alerting system"""
    
    def __init__(self, config_file: str):
        self.config_file = Path(config_file)
        self.load_config()
        
    def load_config(self):
        """Load health check configuration"""
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            logger.error(f"Health config file not found: {self.config_file}")
            self.config = {}
    
    def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check health of a specific service"""
        
        service_config = self.config.get('health_checks', {}).get(service_name, {})
        
        if not service_config:
            return {"status": "unknown", "error": "No config found"}
        
        results = {
            "service": service_name,
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "checks": []
        }
        
        # HTTP health check
        if 'http' in service_config:
            http_result = self._check_http_health(service_config['http'])
            results['checks'].append(http_result)
            if http_result['status'] != 'pass':
                results['status'] = 'unhealthy'
        
        # TCP health check
        if 'tcp' in service_config:
            tcp_result = self._check_tcp_health(service_config['tcp'])
            results['checks'].append(tcp_result)
            if tcp_result['status'] != 'pass':
                results['status'] = 'unhealthy'
        
        # Custom checks
        for custom_check in service_config.get('custom_checks', []):
            custom_result = self._run_custom_check(custom_check)
            results['checks'].append(custom_result)
            if custom_result['status'] != 'pass':
                results['status'] = 'unhealthy'
        
        return results
    
    def _check_http_health(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform HTTP health check"""
        
        try:
            response = requests.get(
                config['url'],
                timeout=config.get('timeout', 10),
                verify=config.get('verify_ssl', True)
            )
            
            if response.status_code == config.get('expected_status', 200):
                return {
                    "check": "http",
                    "status": "pass",
                    "response_time": response.elapsed.total_seconds(),
                    "status_code": response.status_code
                }
            else:
                return {
                    "check": "http",
                    "status": "fail",
                    "error": f"Unexpected status code: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "check": "http",
                "status": "fail",
                "error": str(e)
            }
    
    def _check_tcp_health(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform TCP health check"""
        
        import socket
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(config.get('timeout', 5))
                result = sock.connect_ex((config['host'], config['port']))
                
                if result == 0:
                    return {
                        "check": "tcp",
                        "status": "pass",
                        "host": config['host'],
                        "port": config['port']
                    }
                else:
                    return {
                        "check": "tcp",
                        "status": "fail",
                        "error": f"Connection failed to {config['host']}:{config['port']}"
                    }
                    
        except Exception as e:
            return {
                "check": "tcp",
                "status": "fail",
                "error": str(e)
            }
    
    def _run_custom_check(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run custom health check command"""
        
        try:
            result = subprocess.run(
                config['command'],
                capture_output=True,
                text=True,
                timeout=config.get('timeout', 30)
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                
                # Check expected output if specified
                if 'expected_output' in config:
                    if output == config['expected_output']:
                        status = "pass"
                    else:
                        status = "fail"
                        return {
                            "check": config['name'],
                            "status": status,
                            "error": f"Expected '{config['expected_output']}', got '{output}'"
                        }
                
                # Check minimum value if specified
                if 'min_value' in config:
                    try:
                        value = float(output)
                        if value >= config['min_value']:
                            status = "pass"
                        else:
                            status = "fail"
                            return {
                                "check": config['name'],
                                "status": status,
                                "error": f"Value {value} below minimum {config['min_value']}"
                            }
                    except ValueError:
                        status = "fail"
                        return {
                            "check": config['name'],
                            "status": status,
                            "error": f"Could not parse value: {output}"
                        }
                else:
                    status = "pass"
                
                return {
                    "check": config['name'],
                    "status": status,
                    "output": output
                }
            else:
                return {
                    "check": config['name'],
                    "status": "fail",
                    "error": result.stderr.strip() or "Command failed"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "check": config['name'],
                "status": "fail",
                "error": "Check timed out"
            }
        except Exception as e:
            return {
                "check": config['name'],
                "status": "fail",
                "error": str(e)
            }

@click.group()
def mesh_cli():
    """Service Mesh Security CLI"""
    pass

@mesh_cli.command()
@click.option('--output-dir', default='./config', help='Output directory for configuration files')
def generate_configs(output_dir):
    """Generate service mesh security configurations"""
    
    click.echo("🔐 Generating service mesh security configurations...")
    
    security_manager = ServiceMeshSecurity(output_dir)
    security_manager.save_configurations()
    
    # Generate Akash manifest with security
    manifest = security_manager.generate_akash_security_manifest()
    manifest_path = Path(output_dir) / "secure-akash-deployment.yaml"
    
    with open(manifest_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
    
    click.echo(f"✅ Security configurations generated:")
    click.echo(f"   - Service mesh config: {security_manager.security_config}")
    click.echo(f"   - Health checks config: {security_manager.health_config}")
    click.echo(f"   - Akash manifest: {manifest_path}")

@mesh_cli.command()
@click.option('--config-file', default='./config/health_checks.json', help='Health check configuration file')
@click.option('--service', help='Specific service to check (optional)')
def health_check(config_file, service):
    """Run health checks on services"""
    
    monitor = HealthMonitor(config_file)
    
    if service:
        result = monitor.check_service_health(service)
        click.echo(f"Health check result for {service}:")
        click.echo(json.dumps(result, indent=2))
    else:
        services = monitor.config.get('health_checks', {}).keys()
        for svc in services:
            result = monitor.check_service_health(svc)
            status_color = 'green' if result['status'] == 'healthy' else 'red'
            click.echo(f"{svc}: {click.style(result['status'], fg=status_color)}")

@mesh_cli.command()
@click.option('--config-file', default='./config/health_checks.json', help='Health check configuration file')
@click.option('--interval', default=60, help='Check interval in seconds')
def monitor(config_file, interval):
    """Continuous health monitoring"""
    
    click.echo(f"🔍 Starting continuous health monitoring (interval: {interval}s)")
    
    monitor = HealthMonitor(config_file)
    
    while True:
        try:
            services = monitor.config.get('health_checks', {}).keys()
            
            for service in services:
                result = monitor.check_service_health(service)
                
                if result['status'] == 'unhealthy':
                    click.echo(f"🚨 {service} is unhealthy: {result}")
                    
                    # Send alert if configured
                    webhook_url = os.getenv('HEALTH_WEBHOOK_URL')
                    if webhook_url:
                        try:
                            requests.post(webhook_url, json={
                                'text': f"Service {service} is unhealthy",
                                'details': result
                            }, timeout=10)
                        except:
                            pass
                else:
                    click.echo(f"✅ {service} is healthy")
            
            time.sleep(interval)
            
        except KeyboardInterrupt:
            click.echo("\n👋 Health monitoring stopped")
            break
        except Exception as e:
            click.echo(f"❌ Monitoring error: {e}")
            time.sleep(30)

if __name__ == '__main__':
    mesh_cli()