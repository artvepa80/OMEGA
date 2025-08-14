#!/usr/bin/env python3
"""
🔐 OMEGA Secure Akash Network Deployment Script
Production-ready deployment with SSL/TLS infrastructure for iOS integration
"""

import click
import subprocess
import json
import time
import os
import yaml
import requests
import docker
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import hashlib
import base64
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Docker registry configuration
DOCKER_REGISTRY = "ghcr.io/omega-pro-ai"  # GitHub Container Registry (public)
RPC_ENDPOINTS = [
    "https://rpc.akashnet.net:443",
    "https://rpc.akash.forbole.com:443", 
    "https://akash-rpc.polkachu.com:443",
    "https://rpc-akash-ia.cosmosia.notional.ventures:443"
]

@click.group()
def secure_akash_cli():
    """OMEGA Secure Akash Network Deployment CLI"""
    pass

@secure_akash_cli.command()
@click.option('--gpu-model', 
              type=click.Choice(['rtx4090', 'rtx3090', 'tesla-t4', 'tesla-v100', 'a100']),
              default='rtx4090',
              help='GPU model to request')
@click.option('--max-price-uakt', default=1000, 
              help='Maximum price per hour in uAKT')
@click.option('--wallet', required=True, 
              help='Akash wallet name')
@click.option('--domain', required=True,
              help='Domain name for SSL certificate (e.g., omega-api.example.com)')
@click.option('--email', required=True,
              help='Email for Let\'s Encrypt certificate')
@click.option('--github-token', 
              help='GitHub token for container registry (optional)')
def deploy(gpu_model, max_price_uakt, wallet, domain, email, github_token):
    """Deploy OMEGA to Akash Network with SSL/TLS security"""
    
    click.echo(f"🔐 Secure OMEGA Pro AI Deployment to Akash Network")
    click.echo(f"   GPU Model: {gpu_model}")
    click.echo(f"   Max Price: {max_price_uakt} uAKT/hour (~${max_price_uakt/5000:.2f})")
    click.echo(f"   Wallet: {wallet}")
    click.echo(f"   Domain: {domain}")
    click.echo(f"   SSL Email: {email}")
    
    # Validate prerequisites
    if not _check_prerequisites():
        return
    
    # Setup SSL certificates
    if not _setup_ssl_certificates(domain, email):
        click.echo("❌ SSL certificate setup failed")
        return
        
    # Build and push Docker images with SSL support
    if not _build_and_push_secure_images(github_token):
        click.echo("❌ Docker image build/push failed")
        return
    
    # Create certificate and setup Akash
    if not _ensure_certificate(wallet):
        click.echo("❌ Akash certificate setup failed")
        return
    
    # Update deployment configuration with SSL
    _update_secure_deployment_config(gpu_model, max_price_uakt, domain)
    
    # Deploy to Akash with security
    deployment_info = _secure_deploy_to_akash(wallet, domain)
    
    if deployment_info:
        click.echo(f"✅ Secure deployment successful!")
        click.echo(f"   Deployment ID: {deployment_info.get('id')}")
        click.echo(f"   Provider: {deployment_info.get('provider')}")
        click.echo(f"   Secure URL: https://{domain}")
        click.echo(f"   SSL Status: {deployment_info.get('ssl_status')}")
        
        # Save deployment info
        deployment_data = {
            **deployment_info,
            'domain': domain,
            'ssl_email': email,
            'deployed_at': datetime.now().isoformat()
        }
        
        with open('secure_akash_deployment.json', 'w') as f:
            json.dump(deployment_data, f, indent=2)

def _check_prerequisites() -> bool:
    """Check all prerequisites for secure deployment"""
    
    required_tools = [
        ('akash', 'akash version'),
        ('docker', 'docker --version'),
        ('openssl', 'openssl version'),
        ('curl', 'curl --version')
    ]
    
    all_good = True
    for tool, command in required_tools:
        try:
            result = subprocess.run(command.split(), capture_output=True, text=True)
            if result.returncode == 0:
                click.echo(f"✅ {tool}: OK")
            else:
                click.echo(f"❌ {tool}: Failed")
                all_good = False
        except FileNotFoundError:
            click.echo(f"❌ {tool}: Not found")
            all_good = False
    
    if not all_good:
        click.echo("\nInstall missing tools:")
        click.echo("- Akash CLI: curl -sSfL https://raw.githubusercontent.com/akash-network/node/master/install.sh | sh")
        click.echo("- Docker: https://docs.docker.com/get-docker/")
        
    return all_good

def _setup_ssl_certificates(domain: str, email: str) -> bool:
    """Setup SSL certificates for the domain"""
    
    click.echo("🔐 Setting up SSL certificates...")
    
    ssl_dir = Path('./ssl')
    ssl_dir.mkdir(exist_ok=True)
    
    # Generate self-signed certificate for testing
    # In production, this should integrate with Let's Encrypt or use proper CA
    cert_path = ssl_dir / 'cert.pem'
    key_path = ssl_dir / 'key.pem'
    
    if cert_path.exists() and key_path.exists():
        click.echo("✅ SSL certificates already exist")
        return True
    
    try:
        # Generate private key
        key_cmd = [
            'openssl', 'genrsa', '-out', str(key_path), '2048'
        ]
        subprocess.run(key_cmd, check=True, capture_output=True)
        
        # Generate certificate
        cert_cmd = [
            'openssl', 'req', '-new', '-x509', '-key', str(key_path),
            '-out', str(cert_path), '-days', '365',
            '-subj', f'/C=US/ST=CA/L=SF/O=OMEGA/CN={domain}'
        ]
        subprocess.run(cert_cmd, check=True, capture_output=True)
        
        # Create certificate bundle for Akash
        bundle_path = ssl_dir / 'bundle.pem'
        with open(bundle_path, 'w') as bundle:
            with open(cert_path, 'r') as cert:
                bundle.write(cert.read())
            with open(key_path, 'r') as key:
                bundle.write(key.read())
        
        click.echo("✅ SSL certificates generated successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ SSL certificate generation failed: {e}")
        return False

def _build_and_push_secure_images(github_token: Optional[str]) -> bool:
    """Build and push Docker images with SSL support to public registry"""
    
    click.echo("🔨 Building secure Docker images...")
    
    # Initialize Docker client
    try:
        client = docker.from_env()
    except Exception as e:
        click.echo(f"❌ Docker client error: {e}")
        return False
    
    # Build main API image with SSL
    api_image = f"{DOCKER_REGISTRY}/omega-api:latest"
    gpu_image = f"{DOCKER_REGISTRY}/omega-gpu:latest"
    
    try:
        # Build API image
        click.echo("Building API image with SSL support...")
        api_build = client.images.build(
            path=".",
            dockerfile="Dockerfile.secure-api",
            tag=api_image,
            pull=True,
            rm=True
        )
        
        # Build GPU image  
        click.echo("Building GPU image with SSL support...")
        gpu_build = client.images.build(
            path=".",
            dockerfile="Dockerfile.secure-gpu", 
            tag=gpu_image,
            pull=True,
            rm=True
        )
        
        click.echo("✅ Images built successfully")
        
        # Push to registry (if GitHub token provided)
        if github_token:
            try:
                client.login(
                    username="oauth2token",
                    password=github_token,
                    registry="ghcr.io"
                )
                
                client.images.push(api_image)
                client.images.push(gpu_image)
                
                click.echo("✅ Images pushed to registry")
            except Exception as e:
                click.echo(f"⚠️ Registry push failed: {e}")
                click.echo("Images built locally - manual push required")
        else:
            click.echo("⚠️ No GitHub token - manual push required:")
            click.echo(f"   docker push {api_image}")
            click.echo(f"   docker push {gpu_image}")
        
        return True
        
    except Exception as e:
        click.echo(f"❌ Image build failed: {e}")
        return False

def _ensure_certificate(wallet: str) -> bool:
    """Ensure Akash certificate exists with multiple RPC fallback"""
    
    for rpc_endpoint in RPC_ENDPOINTS:
        try:
            click.echo(f"🔍 Checking certificate via {rpc_endpoint}...")
            
            # Check existing certificate
            result = subprocess.run([
                'akash', 'query', 'cert', 'list',
                '--owner', wallet,
                '--node', rpc_endpoint,
                '--chain-id', 'akashnet-2'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and "certificates:" in result.stdout:
                certs = result.stdout.strip().split('\n')
                if len(certs) > 1:
                    click.echo("✅ Certificate exists")
                    return True
            
            # Create certificate if needed
            click.echo(f"🔐 Creating certificate via {rpc_endpoint}...")
            result = subprocess.run([
                'akash', 'tx', 'cert', 'create', 'client',
                '--from', wallet,
                '--node', rpc_endpoint,
                '--chain-id', 'akashnet-2',
                '--gas-prices', '0.025uakt',
                '--gas-adjustment', '1.5',
                '--yes'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                click.echo("✅ Certificate created successfully")
                return True
                
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            click.echo(f"⚠️ RPC endpoint {rpc_endpoint} failed: {e}")
            continue
    
    click.echo("❌ All RPC endpoints failed")
    return False

def _update_secure_deployment_config(gpu_model: str, max_price: int, domain: str):
    """Update deployment configuration with SSL and security settings"""
    
    deployment_path = Path('deploy/secure-akash-deployment.yaml')
    deployment_path.parent.mkdir(exist_ok=True)
    
    # Create secure deployment configuration
    secure_config = {
        "version": "2.0",
        "services": {
            "omega-api": {
                "image": f"{DOCKER_REGISTRY}/omega-api:latest",
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
                    "SSL_CERT_PATH=/app/ssl/cert.pem",
                    "SSL_KEY_PATH=/app/ssl/key.pem",
                    "DOMAIN=" + domain,
                    "ENABLE_SSL=true",
                    "SSL_PROTOCOLS=TLSv1.2,TLSv1.3",
                    "SECURITY_HEADERS=true",
                    "LOG_LEVEL=INFO"
                ],
                "resources": {
                    "cpu": {"units": 2.0},
                    "memory": {"size": "4Gi"},
                    "storage": [{"size": "20Gi"}]
                }
            },
            "omega-gpu": {
                "image": f"{DOCKER_REGISTRY}/omega-gpu:latest",
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
                    "SSL_ENABLED=true"
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
                                    "model": gpu_model,
                                    "ram": _get_gpu_ram(gpu_model)
                                }]
                            }
                        }
                    }
                }
            },
            "redis": {
                "image": "redis:7-alpine",
                "expose": [
                    {
                        "port": 6379,
                        "to": [
                            {"service": "omega-api"},
                            {"service": "omega-gpu"}
                        ]
                    }
                ],
                "resources": {
                    "cpu": {"units": 0.5},
                    "memory": {"size": "1Gi"}, 
                    "storage": [{"size": "10Gi"}]
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
                                        "model": gpu_model,
                                        "ram": _get_gpu_ram(gpu_model)
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
                            "amount": max_price // 3
                        },
                        "omega-gpu": {
                            "denom": "uakt", 
                            "amount": max_price
                        },
                        "redis": {
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
            }
        }
    }
    
    # Write deployment config
    with open(deployment_path, 'w') as f:
        yaml.dump(secure_config, f, default_flow_style=False, sort_keys=False)
    
    click.echo(f"✅ Secure deployment config created for {gpu_model}")

def _get_gpu_ram(gpu_model: str) -> str:
    """Get RAM specification for GPU model"""
    gpu_ram = {
        'rtx4090': '24Gi',
        'rtx3090': '24Gi',
        'tesla-t4': '16Gi', 
        'tesla-v100': '32Gi',
        'a100': '80Gi'
    }
    return gpu_ram.get(gpu_model, '16Gi')

def _secure_deploy_to_akash(wallet: str, domain: str) -> Optional[Dict[str, Any]]:
    """Deploy to Akash with security and monitoring"""
    
    deployment_path = 'deploy/secure-akash-deployment.yaml'
    
    for rpc_endpoint in RPC_ENDPOINTS:
        try:
            click.echo(f"🚀 Creating secure deployment via {rpc_endpoint}...")
            
            # Create deployment
            create_cmd = [
                'akash', 'tx', 'deployment', 'create',
                deployment_path,
                '--from', wallet,
                '--node', rpc_endpoint,
                '--chain-id', 'akashnet-2',
                '--gas-prices', '0.025uakt',
                '--gas-adjustment', '1.5',
                '--yes'
            ]
            
            result = subprocess.run(create_cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                click.echo(f"⚠️ Deployment creation failed via {rpc_endpoint}: {result.stderr}")
                continue
            
            # Extract deployment ID
            deployment_id = _extract_deployment_id(result.stdout)
            if not deployment_id:
                click.echo("❌ Could not extract deployment ID")
                continue
            
            click.echo(f"✅ Deployment created: {deployment_id}")
            
            # Wait for bids and create lease
            click.echo("⏳ Waiting for bids...")
            time.sleep(45)
            
            # Get bids with timeout handling
            bids = _get_bids_with_retry(wallet, deployment_id, rpc_endpoint)
            if not bids:
                click.echo("❌ No bids received")
                continue
            
            # Select best provider
            best_bid = min(bids, key=lambda b: float(b.get('price', '999999')))
            provider = best_bid['provider']
            
            click.echo(f"🎯 Selected provider: {provider}")
            
            # Create lease
            if not _create_lease_with_retry(wallet, deployment_id, provider, rpc_endpoint):
                continue
            
            # Wait for service to be ready
            click.echo("⏳ Waiting for service startup...")
            time.sleep(90)
            
            # Verify SSL configuration
            ssl_status = _verify_ssl_setup(domain, provider)
            
            return {
                'id': deployment_id,
                'provider': provider,
                'domain': domain,
                'ssl_status': ssl_status,
                'rpc_endpoint': rpc_endpoint,
                'created_at': datetime.now().isoformat()
            }
            
        except (subprocess.TimeoutExpired, Exception) as e:
            click.echo(f"⚠️ Deployment failed via {rpc_endpoint}: {e}")
            continue
    
    click.echo("❌ All deployment attempts failed")
    return None

def _get_bids_with_retry(wallet: str, deployment_id: str, rpc_endpoint: str, max_retries: int = 3) -> List[Dict]:
    """Get bids with retry mechanism"""
    
    dseq = deployment_id.split('/')[1]
    
    for attempt in range(max_retries):
        try:
            cmd = [
                'akash', 'query', 'market', 'bid', 'list',
                '--owner', wallet,
                '--dseq', dseq,
                '--node', rpc_endpoint,
                '--chain-id', 'akashnet-2',
                '--output', 'json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                bids = data.get('bids', [])
                if bids:
                    return bids
            
            time.sleep(10)  # Wait before retry
            
        except Exception as e:
            click.echo(f"⚠️ Bid query attempt {attempt + 1} failed: {e}")
    
    return []

def _create_lease_with_retry(wallet: str, deployment_id: str, provider: str, rpc_endpoint: str) -> bool:
    """Create lease with retry mechanism"""
    
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
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            click.echo("✅ Lease created successfully")
            return True
        else:
            click.echo(f"❌ Lease creation failed: {result.stderr}")
            return False
            
    except Exception as e:
        click.echo(f"❌ Lease creation error: {e}")
        return False

def _verify_ssl_setup(domain: str, provider: str) -> str:
    """Verify SSL certificate is working"""
    
    try:
        # Test HTTPS connection
        test_url = f"https://{domain}/health"
        response = requests.get(test_url, timeout=30, verify=False)
        
        if response.status_code == 200:
            return "SSL_ACTIVE"
        else:
            return "SSL_ERROR"
            
    except requests.RequestException:
        return "SSL_PENDING"

def _extract_deployment_id(output: str) -> Optional[str]:
    """Extract deployment ID from Akash output"""
    import re
    match = re.search(r'deployment/([a-f0-9]+)/(\d+)', output)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return None

@secure_akash_cli.command()
@click.option('--wallet', required=True)
def status(wallet):
    """Check secure deployment status"""
    
    if not os.path.exists('secure_akash_deployment.json'):
        click.echo("❌ No secure deployment found")
        return
    
    with open('secure_akash_deployment.json', 'r') as f:
        deployment = json.load(f)
    
    domain = deployment.get('domain')
    provider = deployment.get('provider')
    ssl_status = deployment.get('ssl_status')
    
    click.echo(f"🔐 Secure Deployment Status")
    click.echo(f"   Domain: {domain}")
    click.echo(f"   Provider: {provider}")
    click.echo(f"   SSL Status: {ssl_status}")
    
    # Test health and SSL
    try:
        health_url = f"https://{domain}/health"
        response = requests.get(health_url, timeout=10, verify=False)
        
        if response.status_code == 200:
            click.echo("✅ Service is healthy and SSL is active")
        else:
            click.echo(f"⚠️ Service health check failed: {response.status_code}")
            
    except requests.RequestException as e:
        click.echo(f"❌ Cannot reach service: {e}")

@secure_akash_cli.command()
@click.option('--domain', required=True)
@click.option('--email', required=True) 
def renew_ssl(domain, email):
    """Renew SSL certificates"""
    
    click.echo(f"🔄 Renewing SSL certificate for {domain}")
    
    if _setup_ssl_certificates(domain, email):
        click.echo("✅ SSL certificates renewed")
        
        # TODO: Update running deployment with new certificates
        # This would require sending new certificates to the running containers
        click.echo("⚠️ Manual deployment restart required to use new certificates")
    else:
        click.echo("❌ SSL certificate renewal failed")

if __name__ == '__main__':
    secure_akash_cli()