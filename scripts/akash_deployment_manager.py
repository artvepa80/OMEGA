#!/usr/bin/env python3
"""
🚀 OMEGA Akash Deployment Manager
Complete deployment management system for OMEGA Pro AI on Akash Network
"""

import click
import subprocess
import json
import time
import os
import yaml
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
import hashlib
import tempfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AkashDeploymentManager:
    """Complete Akash deployment management"""
    
    def __init__(self):
        self.deployments_dir = Path('./akash_deployments')
        self.deployments_dir.mkdir(exist_ok=True)
        
        self.rpc_endpoints = [
            "https://rpc.akashnet.net:443",
            "https://rpc.akash.forbole.com:443",
            "https://akash-rpc.polkachu.com:443",
            "https://rpc-akash-ia.cosmosia.notional.ventures:443"
        ]
        
        self.docker_registries = [
            "ghcr.io/omega-pro-ai",  # GitHub Container Registry
            "docker.io/omegaproai",  # Docker Hub fallback
            "registry.akash.network/omega"  # Akash Registry fallback
        ]
    
    def prepare_deployment_environment(self, domain: str, email: str) -> bool:
        """Prepare complete deployment environment"""
        
        click.echo("🔧 Preparing deployment environment...")
        
        # 1. Generate SSL certificates
        from scripts.ssl_cert_manager import SSLCertificateManager
        ssl_manager = SSLCertificateManager()
        
        if not ssl_manager.generate_self_signed_certificate(domain, email):
            click.echo("❌ SSL certificate generation failed")
            return False
        
        # 2. Generate service mesh security configs
        from scripts.service_mesh_security import ServiceMeshSecurity
        security_manager = ServiceMeshSecurity()
        security_manager.save_configurations()
        
        # 3. Validate Docker images
        if not self._validate_docker_images():
            click.echo("❌ Docker image validation failed")
            return False
        
        # 4. Prepare Akash-specific configurations
        self._prepare_akash_configs(domain)
        
        click.echo("✅ Deployment environment prepared successfully")
        return True
    
    def _validate_docker_images(self) -> bool:
        """Validate that required Docker images are accessible"""
        
        required_images = [
            "omega-api:latest",
            "omega-gpu:latest"
        ]
        
        for registry in self.docker_registries:
            click.echo(f"🔍 Checking registry: {registry}")
            
            all_images_found = True
            for image in required_images:
                full_image = f"{registry}/{image}"
                
                try:
                    # Try to inspect the image
                    result = subprocess.run([
                        'docker', 'manifest', 'inspect', full_image
                    ], capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        click.echo(f"   ✅ {image}")
                    else:
                        click.echo(f"   ❌ {image} - not found")
                        all_images_found = False
                        
                except subprocess.TimeoutExpired:
                    click.echo(f"   ⚠️ {image} - timeout checking")
                    all_images_found = False
            
            if all_images_found:
                click.echo(f"✅ All images found in {registry}")
                return True
        
        click.echo("⚠️ Some images not found in public registries")
        click.echo("Building and pushing images to public registry...")
        
        return self._build_and_push_images()
    
    def _build_and_push_images(self) -> bool:
        """Build and push Docker images to public registry"""
        
        import docker
        
        try:
            client = docker.from_env()
            
            # Build API image
            click.echo("🔨 Building API image...")
            api_image = client.images.build(
                path=".",
                dockerfile="Dockerfile.secure-api",
                tag=f"{self.docker_registries[0]}/omega-api:latest",
                pull=True,
                rm=True
            )
            
            # Build GPU image
            click.echo("🔨 Building GPU image...")
            gpu_image = client.images.build(
                path=".",
                dockerfile="Dockerfile.secure-gpu", 
                tag=f"{self.docker_registries[0]}/omega-gpu:latest",
                pull=True,
                rm=True
            )
            
            click.echo("✅ Images built successfully")
            
            # Try to push to first registry (GitHub)
            github_token = os.getenv('GITHUB_TOKEN')
            if github_token:
                try:
                    client.login(
                        username="oauth2token",
                        password=github_token,
                        registry="ghcr.io"
                    )
                    
                    client.images.push(f"{self.docker_registries[0]}/omega-api:latest")
                    client.images.push(f"{self.docker_registries[0]}/omega-gpu:latest")
                    
                    click.echo("✅ Images pushed to GitHub Container Registry")
                    return True
                    
                except Exception as e:
                    click.echo(f"⚠️ GitHub push failed: {e}")
            
            # Manual push instructions
            click.echo("⚠️ Automatic push failed. Manual push required:")
            click.echo(f"   docker push {self.docker_registries[0]}/omega-api:latest")
            click.echo(f"   docker push {self.docker_registries[0]}/omega-gpu:latest")
            
            return True
            
        except Exception as e:
            click.echo(f"❌ Image build failed: {e}")
            return False
    
    def _prepare_akash_configs(self, domain: str):
        """Prepare Akash-specific configuration files"""
        
        # Generate environment-specific deployment manifest
        manifest = self._generate_production_manifest(domain)
        
        manifest_path = self.deployments_dir / f"deployment-{domain}.yaml"
        with open(manifest_path, 'w') as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
        
        # Generate deployment metadata
        metadata = {
            'domain': domain,
            'created_at': datetime.now().isoformat(),
            'manifest_path': str(manifest_path),
            'registry': self.docker_registries[0],
            'ssl_enabled': True,
            'services': ['omega-api', 'omega-gpu', 'redis', 'nginx']
        }
        
        metadata_path = self.deployments_dir / f"metadata-{domain}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        click.echo(f"✅ Akash configs prepared for {domain}")
    
    def _generate_production_manifest(self, domain: str) -> Dict[str, Any]:
        """Generate production-ready Akash deployment manifest"""
        
        return {
            "version": "2.0",
            "services": {
                "omega-api": {
                    "image": f"{self.docker_registries[0]}/omega-api:latest",
                    "expose": [
                        {
                            "port": 80,
                            "as": 80,
                            "to": [{"global": True}],
                            "accept": [domain]
                        },
                        {
                            "port": 443,
                            "as": 443,
                            "to": [{"global": True}],
                            "accept": [domain]
                        }
                    ],
                    "env": [
                        "OMEGA_ENV=production",
                        "DOMAIN=" + domain,
                        "SSL_ENABLED=true",
                        "SECURITY_HEADERS=true",
                        "CORS_ENABLED=true",
                        "RATE_LIMITING=true",
                        "AUTH_REQUIRED=true",
                        "REDIS_URL=redis://redis:6379",
                        "REDIS_PASSWORD=omega_secure_redis_2024",
                        "LOG_LEVEL=INFO",
                        "HEALTH_CHECK_ENABLED=true",
                        "MAX_REQUESTS_PER_SECOND=20",
                        "JWT_SECRET=omega_jwt_secret_2024_secure",
                        "API_VERSION=v1.0"
                    ]
                },
                "omega-gpu": {
                    "image": f"{self.docker_registries[0]}/omega-gpu:latest",
                    "expose": [
                        {
                            "port": 8001,
                            "to": [{"service": "omega-api"}]
                        }
                    ],
                    "env": [
                        "CUDA_VISIBLE_DEVICES=0",
                        "NVIDIA_VISIBLE_DEVICES=all",
                        "GPU_MEMORY_STRATEGY=balanced",
                        "SSL_ENABLED=true",
                        "INTERNAL_AUTH=true",
                        "REDIS_URL=redis://redis:6379",
                        "REDIS_PASSWORD=omega_secure_redis_2024",
                        "MAX_CONCURRENT_REQUESTS=5",
                        "GPU_MEMORY_LIMIT=90",
                        "PROCESSING_TIMEOUT=300",
                        "MODEL_CACHE_SIZE=2GB",
                        "LOG_LEVEL=INFO"
                    ]
                },
                "redis": {
                    "image": "redis:7-alpine",
                    "command": [
                        "redis-server",
                        "--requirepass", "omega_secure_redis_2024",
                        "--maxmemory", "1gb",
                        "--maxmemory-policy", "allkeys-lru",
                        "--save", "900", "1",
                        "--save", "300", "10",
                        "--save", "60", "10000",
                        "--appendonly", "yes"
                    ],
                    "expose": [
                        {
                            "port": 6379,
                            "to": [
                                {"service": "omega-api"},
                                {"service": "omega-gpu"}
                            ]
                        }
                    ]
                },
                "nginx": {
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
                        "DOMAIN=" + domain,
                        "SSL_ENABLED=true",
                        "RATE_LIMITING=true",
                        "SECURITY_HEADERS=true"
                    ]
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
                    "nginx": {
                        "resources": {
                            "cpu": {"units": 0.5},
                            "memory": {"size": "512Mi"},
                            "storage": [{"size": "2Gi"}]
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
                            "omega-api": {"denom": "uakt", "amount": 400},
                            "omega-gpu": {"denom": "uakt", "amount": 1200},
                            "redis": {"denom": "uakt", "amount": 100},
                            "nginx": {"denom": "uakt", "amount": 100}
                        }
                    }
                }
            },
            "deployment": {
                "omega-api": {"dcloud": {"profile": "omega-api", "count": 1}},
                "omega-gpu": {"dcloud": {"profile": "omega-gpu", "count": 1}},
                "redis": {"dcloud": {"profile": "redis", "count": 1}},
                "nginx": {"dcloud": {"profile": "nginx", "count": 1}}
            }
        }
    
    def deploy_to_akash(self, wallet: str, domain: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """Deploy to Akash with comprehensive error handling and retries"""
        
        manifest_path = self.deployments_dir / f"deployment-{domain}.yaml"
        
        if not manifest_path.exists():
            click.echo(f"❌ Deployment manifest not found: {manifest_path}")
            return None
        
        for attempt in range(max_retries):
            click.echo(f"🚀 Deployment attempt {attempt + 1}/{max_retries}")
            
            for rpc_endpoint in self.rpc_endpoints:
                try:
                    result = self._attempt_deployment(wallet, manifest_path, rpc_endpoint, domain)
                    if result:
                        return result
                        
                except Exception as e:
                    click.echo(f"⚠️ Attempt failed with {rpc_endpoint}: {e}")
                    continue
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt * 30  # Exponential backoff
                click.echo(f"⏳ Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
        
        click.echo("❌ All deployment attempts failed")
        return None
    
    def _attempt_deployment(self, wallet: str, manifest_path: Path, rpc_endpoint: str, domain: str) -> Optional[Dict[str, Any]]:
        """Single deployment attempt"""
        
        click.echo(f"🔗 Using RPC endpoint: {rpc_endpoint}")
        
        # Create deployment
        create_cmd = [
            'akash', 'tx', 'deployment', 'create',
            str(manifest_path),
            '--from', wallet,
            '--node', rpc_endpoint,
            '--chain-id', 'akashnet-2',
            '--gas-prices', '0.025uakt',
            '--gas-adjustment', '1.5',
            '--yes'
        ]
        
        result = subprocess.run(create_cmd, capture_output=True, text=True, timeout=180)
        
        if result.returncode != 0:
            raise Exception(f"Deployment creation failed: {result.stderr}")
        
        deployment_id = self._extract_deployment_id(result.stdout)
        if not deployment_id:
            raise Exception("Could not extract deployment ID")
        
        click.echo(f"✅ Deployment created: {deployment_id}")
        
        # Wait for bids
        click.echo("⏳ Waiting for bids...")
        time.sleep(60)
        
        # Get and evaluate bids
        bids = self._get_bids_with_retry(wallet, deployment_id, rpc_endpoint)
        if not bids:
            raise Exception("No bids received")
        
        # Select best provider
        best_bid = self._select_best_provider(bids)
        provider = best_bid['provider']
        
        click.echo(f"🎯 Selected provider: {provider}")
        click.echo(f"   Price: {best_bid.get('price')} uAKT/block")
        
        # Create lease
        if not self._create_lease(wallet, deployment_id, provider, rpc_endpoint):
            raise Exception("Lease creation failed")
        
        # Wait for deployment to be ready
        click.echo("⏳ Waiting for deployment to be ready...")
        time.sleep(120)
        
        # Verify deployment
        deployment_info = {
            'id': deployment_id,
            'provider': provider,
            'domain': domain,
            'rpc_endpoint': rpc_endpoint,
            'price_uakt': best_bid.get('price'),
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        # Test service availability
        if self._verify_deployment(domain):
            deployment_info['health_status'] = 'healthy'
            click.echo("✅ Deployment verification successful")
        else:
            deployment_info['health_status'] = 'degraded'
            click.echo("⚠️ Deployment verification failed - service may need time to start")
        
        # Save deployment information
        deployment_file = self.deployments_dir / f"active-{domain}.json"
        with open(deployment_file, 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        return deployment_info
    
    def _get_bids_with_retry(self, wallet: str, deployment_id: str, rpc_endpoint: str, max_attempts: int = 5) -> List[Dict]:
        """Get bids with multiple retry attempts"""
        
        dseq = deployment_id.split('/')[1]
        
        for attempt in range(max_attempts):
            try:
                cmd = [
                    'akash', 'query', 'market', 'bid', 'list',
                    '--owner', wallet,
                    '--dseq', dseq,
                    '--node', rpc_endpoint,
                    '--chain-id', 'akashnet-2',
                    '--output', 'json'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
                
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    bids = data.get('bids', [])
                    
                    if bids:
                        click.echo(f"📊 Found {len(bids)} bid(s)")
                        return bids
                
                if attempt < max_attempts - 1:
                    time.sleep(15)
                    
            except Exception as e:
                click.echo(f"⚠️ Bid query attempt {attempt + 1} failed: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(15)
        
        return []
    
    def _select_best_provider(self, bids: List[Dict]) -> Dict[str, Any]:
        """Select the best provider based on price and reputation"""
        
        # For now, select the cheapest provider
        # TODO: Add reputation scoring and provider blacklist
        best_bid = min(bids, key=lambda b: float(b.get('price', '999999')))
        
        return best_bid
    
    def _create_lease(self, wallet: str, deployment_id: str, provider: str, rpc_endpoint: str) -> bool:
        """Create lease with provider"""
        
        dseq = deployment_id.split('/')[1]
        
        try:
            cmd = [
                'akash', 'tx', 'market', 'lease', 'create',
                '--from', wallet,
                '--dseq', dseq,
                '--provider', provider,
                '--node', rpc_endpoint,
                '--chain-id', 'akashnet-2',
                '--gas-prices', '0.025uakt',
                '--gas-adjustment', '1.5',
                '--yes'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            
            if result.returncode == 0:
                click.echo("✅ Lease created successfully")
                return True
            else:
                click.echo(f"❌ Lease creation failed: {result.stderr}")
                return False
                
        except Exception as e:
            click.echo(f"❌ Lease creation error: {e}")
            return False
    
    def _verify_deployment(self, domain: str, max_attempts: int = 10) -> bool:
        """Verify that deployment is working"""
        
        test_urls = [
            f"https://{domain}/health",
            f"http://{domain}/health"
        ]
        
        for attempt in range(max_attempts):
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=30, verify=False)
                    if response.status_code == 200:
                        return True
                except requests.RequestException:
                    continue
            
            if attempt < max_attempts - 1:
                time.sleep(30)
        
        return False
    
    def _extract_deployment_id(self, output: str) -> Optional[str]:
        """Extract deployment ID from Akash output"""
        import re
        match = re.search(r'deployment/([a-f0-9]+)/(\d+)', output)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
        return None
    
    def get_deployment_status(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get status of active deployment"""
        
        deployment_file = self.deployments_dir / f"active-{domain}.json"
        
        if not deployment_file.exists():
            return None
        
        with open(deployment_file, 'r') as f:
            deployment = json.load(f)
        
        # Test current health
        if self._verify_deployment(domain):
            deployment['current_health'] = 'healthy'
            deployment['last_checked'] = datetime.now().isoformat()
        else:
            deployment['current_health'] = 'unhealthy'
            deployment['last_checked'] = datetime.now().isoformat()
        
        return deployment
    
    def close_deployment(self, wallet: str, domain: str) -> bool:
        """Close Akash deployment"""
        
        deployment_file = self.deployments_dir / f"active-{domain}.json"
        
        if not deployment_file.exists():
            click.echo(f"❌ No active deployment found for {domain}")
            return False
        
        with open(deployment_file, 'r') as f:
            deployment = json.load(f)
        
        deployment_id = deployment.get('id')
        rpc_endpoint = deployment.get('rpc_endpoint', self.rpc_endpoints[0])
        dseq = deployment_id.split('/')[1]
        
        try:
            cmd = [
                'akash', 'tx', 'deployment', 'close',
                '--from', wallet,
                '--dseq', dseq,
                '--node', rpc_endpoint,
                '--chain-id', 'akashnet-2',
                '--gas-prices', '0.025uakt',
                '--gas-adjustment', '1.5',
                '--yes'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                click.echo("✅ Deployment closed successfully")
                
                # Archive deployment info
                archive_file = self.deployments_dir / f"archived-{domain}-{int(time.time())}.json"
                deployment['closed_at'] = datetime.now().isoformat()
                deployment['status'] = 'closed'
                
                with open(archive_file, 'w') as f:
                    json.dump(deployment, f, indent=2)
                
                os.remove(deployment_file)
                return True
            else:
                click.echo(f"❌ Failed to close deployment: {result.stderr}")
                return False
                
        except Exception as e:
            click.echo(f"❌ Error closing deployment: {e}")
            return False

@click.group()
def akash_cli():
    """OMEGA Akash Deployment Manager"""
    pass

@akash_cli.command()
@click.option('--domain', required=True, help='Domain name for the deployment')
@click.option('--email', required=True, help='Email for SSL certificate')
@click.option('--wallet', required=True, help='Akash wallet name')
@click.option('--skip-build', is_flag=True, help='Skip Docker image building')
def deploy(domain, email, wallet, skip_build):
    """Deploy OMEGA to Akash Network"""
    
    manager = AkashDeploymentManager()
    
    click.echo(f"🚀 Deploying OMEGA Pro AI to Akash Network")
    click.echo(f"   Domain: {domain}")
    click.echo(f"   Wallet: {wallet}")
    
    # Prepare environment
    if not skip_build:
        if not manager.prepare_deployment_environment(domain, email):
            return
    
    # Deploy to Akash
    deployment_info = manager.deploy_to_akash(wallet, domain)
    
    if deployment_info:
        click.echo(f"✅ Deployment successful!")
        click.echo(f"   Deployment ID: {deployment_info['id']}")
        click.echo(f"   Provider: {deployment_info['provider']}")
        click.echo(f"   Domain: https://{domain}")
        click.echo(f"   Health Status: {deployment_info['health_status']}")
    else:
        click.echo("❌ Deployment failed")

@akash_cli.command()
@click.option('--domain', required=True, help='Domain name of the deployment')
def status(domain):
    """Check deployment status"""
    
    manager = AkashDeploymentManager()
    status_info = manager.get_deployment_status(domain)
    
    if status_info:
        click.echo(f"📊 Deployment Status for {domain}:")
        click.echo(f"   ID: {status_info['id']}")
        click.echo(f"   Provider: {status_info['provider']}")
        click.echo(f"   Status: {status_info['status']}")
        click.echo(f"   Health: {status_info['current_health']}")
        click.echo(f"   Created: {status_info['created_at']}")
        click.echo(f"   Last Checked: {status_info['last_checked']}")
    else:
        click.echo(f"❌ No deployment found for {domain}")

@akash_cli.command()
@click.option('--domain', required=True, help='Domain name of the deployment')
@click.option('--wallet', required=True, help='Akash wallet name')
def close(domain, wallet):
    """Close Akash deployment"""
    
    manager = AkashDeploymentManager()
    
    if manager.close_deployment(wallet, domain):
        click.echo(f"✅ Deployment for {domain} closed successfully")
    else:
        click.echo(f"❌ Failed to close deployment for {domain}")

@akash_cli.command()
def list():
    """List all deployments"""
    
    manager = AkashDeploymentManager()
    
    active_files = list(manager.deployments_dir.glob("active-*.json"))
    archived_files = list(manager.deployments_dir.glob("archived-*.json"))
    
    if active_files:
        click.echo("🟢 Active Deployments:")
        for file in active_files:
            with open(file, 'r') as f:
                deployment = json.load(f)
            click.echo(f"   {deployment['domain']} - {deployment['status']} - {deployment['created_at']}")
    
    if archived_files:
        click.echo("\n📦 Archived Deployments:")
        for file in archived_files[-5:]:  # Show last 5
            with open(file, 'r') as f:
                deployment = json.load(f)
            click.echo(f"   {deployment['domain']} - {deployment['status']} - {deployment.get('closed_at', 'N/A')}")

if __name__ == '__main__':
    akash_cli()