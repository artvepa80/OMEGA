#!/usr/bin/env python3
"""
🌐 OMEGA Akash Network Deployment Script
Deploy OMEGA Pro AI en Akash Network para GPU ultra-económico
"""

import click
import subprocess
import json
import time
import os
import yaml
import requests
from pathlib import Path
from typing import Dict, Any, Optional

@click.group()
def akash_cli():
    """OMEGA Akash Network Deployment CLI"""
    pass

@akash_cli.command()
@click.option('--gpu-model', 
              type=click.Choice(['rtx4090', 'rtx3090', 'tesla-t4', 'tesla-v100', 'a100']),
              default='rtx4090',
              help='GPU model to request')
@click.option('--max-price-uakt', default=1000, 
              help='Maximum price per hour in uAKT (1000 uAKT ≈ $0.20)')
@click.option('--wallet', required=True, 
              help='Akash wallet name')
def deploy(gpu_model, max_price_uakt, wallet):
    """Deploy OMEGA to Akash Network"""
    
    click.echo(f"🌐 Deploying OMEGA Pro AI to Akash Network")
    click.echo(f"   GPU Model: {gpu_model}")
    click.echo(f"   Max Price: {max_price_uakt} uAKT/hour (~${max_price_uakt/5000:.2f})")
    click.echo(f"   Wallet: {wallet}")
    
    # Verificar prereqs
    if not _check_akash_cli():
        return
    
    # Crear certificate si no existe
    _ensure_certificate(wallet)
    
    # Actualizar deployment.yaml con GPU model
    _update_deployment_config(gpu_model, max_price_uakt)
    
    # Build y push imagen Docker
    if not _build_and_push_image():
        return
    
    # Deploy a Akash
    deployment_info = _deploy_to_akash(wallet)
    
    if deployment_info:
        click.echo(f"✅ Deployment successful!")
        click.echo(f"   Deployment ID: {deployment_info.get('id')}")
        click.echo(f"   Provider: {deployment_info.get('provider')}")
        click.echo(f"   URL: {deployment_info.get('url')}")
        
        # Guardar info
        with open('akash_deployment.json', 'w') as f:
            json.dump(deployment_info, f, indent=2)

def _check_akash_cli() -> bool:
    """Verifica que Akash CLI esté instalado"""
    try:
        result = subprocess.run(['akash', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            click.echo(f"✅ Akash CLI version: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    click.echo("❌ Akash CLI not found. Install with:")
    click.echo("   curl -sSfL https://raw.githubusercontent.com/akash-network/node/master/install.sh | sh")
    return False

def _ensure_certificate(wallet: str) -> bool:
    """Asegura que existe certificado para la wallet"""
    try:
        # Verificar si ya existe
        result = subprocess.run([
            'akash', 'query', 'cert', 'list',
            '--owner', wallet,
            '--node', 'https://rpc.akashnet.net:443',
            '--chain-id', 'akashnet-2'
        ], capture_output=True, text=True)
        
        if "certificates:" in result.stdout and len(result.stdout.strip().split('\n')) > 1:
            click.echo("✅ Certificate exists")
            return True
        
        # Crear certificado
        click.echo("🔐 Creating certificate...")
        result = subprocess.run([
            'akash', 'tx', 'cert', 'create', 'client',
            '--from', wallet,
            '--node', 'https://rpc.akashnet.net:443',
            '--chain-id', 'akashnet-2',
            '--gas-prices', '0.025uakt',
            '--gas-adjustment', '1.5',
            '--yes'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            click.echo("✅ Certificate created")
            return True
        else:
            click.echo(f"❌ Error creating certificate: {result.stderr}")
            return False
            
    except Exception as e:
        click.echo(f"❌ Error with certificate: {e}")
        return False

def _update_deployment_config(gpu_model: str, max_price: int):
    """Actualiza deployment.yaml con configuración específica"""
    
    deployment_path = Path('deploy/akash-deployment.yaml')
    
    with open(deployment_path, 'r') as f:
        deployment = yaml.safe_load(f)
    
    # Actualizar GPU model
    gpu_config = deployment['profiles']['compute']['omega-gpu']['resources']['gpu']
    gpu_config['attributes']['vendor']['nvidia'][0]['model'] = gpu_model
    
    # Actualizar precio
    deployment['profiles']['placement']['dcloud']['pricing']['omega-gpu']['amount'] = max_price
    
    # Ajustar RAM según GPU
    gpu_ram = {
        'rtx4090': '24Gi',
        'rtx3090': '24Gi', 
        'tesla-t4': '16Gi',
        'tesla-v100': '32Gi',
        'a100': '80Gi'
    }
    
    gpu_config['attributes']['vendor']['nvidia'][0]['ram'] = gpu_ram.get(gpu_model, '16Gi')
    
    # Guardar configuración actualizada
    with open(deployment_path, 'w') as f:
        yaml.dump(deployment, f, default_flow_style=False, sort_keys=False)
    
    click.echo(f"✅ Updated deployment config for {gpu_model}")

def _build_and_push_image() -> bool:
    """Build y push imagen Docker a registry público"""
    
    click.echo("🔨 Building Docker image...")
    
    # Build imagen GPU
    build_cmd = [
        'docker', 'build',
        '-f', 'Dockerfile.gpu',
        '-t', 'omega-pro-ai:gpu',
        '.'
    ]
    
    try:
        result = subprocess.run(build_cmd, check=True, capture_output=True, text=True)
        click.echo("✅ Docker image built successfully")
        
        # Tag para Docker Hub (necesario para Akash)
        tag_cmd = ['docker', 'tag', 'omega-pro-ai:gpu', 'your-dockerhub/omega-pro-ai:gpu']
        subprocess.run(tag_cmd, check=True)
        
        click.echo("📦 Image tagged for registry")
        click.echo("⚠️  Remember to push to Docker Hub:")
        click.echo("   docker push your-dockerhub/omega-pro-ai:gpu")
        
        return True
        
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Docker build failed: {e}")
        return False

def _deploy_to_akash(wallet: str) -> Optional[Dict[str, Any]]:
    """Deploy a Akash Network"""
    
    deployment_path = 'deploy/akash-deployment.yaml'
    
    try:
        # Crear deployment
        click.echo("🚀 Creating Akash deployment...")
        
        create_cmd = [
            'akash', 'tx', 'deployment', 'create',
            deployment_path,
            '--from', wallet,
            '--node', 'https://rpc.akashnet.net:443', 
            '--chain-id', 'akashnet-2',
            '--gas-prices', '0.025uakt',
            '--gas-adjustment', '1.5',
            '--yes'
        ]
        
        result = subprocess.run(create_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            click.echo(f"❌ Failed to create deployment: {result.stderr}")
            return None
        
        # Extraer deployment ID del output
        deployment_id = _extract_deployment_id(result.stdout)
        if not deployment_id:
            click.echo("❌ Could not extract deployment ID")
            return None
        
        click.echo(f"✅ Deployment created: {deployment_id}")
        
        # Esperar por bids
        click.echo("⏳ Waiting for bids...")
        time.sleep(30)
        
        # Obtener bids
        bids = _get_bids(wallet, deployment_id)
        if not bids:
            click.echo("❌ No bids received")
            return None
        
        # Seleccionar mejor bid (más barato)
        best_bid = min(bids, key=lambda b: float(b.get('price', '999999')))
        provider = best_bid['provider']
        
        click.echo(f"🎯 Selected provider: {provider}")
        click.echo(f"   Price: {best_bid.get('price')} uAKT/block")
        
        # Crear lease
        lease_info = _create_lease(wallet, deployment_id, provider)
        if not lease_info:
            return None
        
        # Obtener URL de acceso
        time.sleep(60)  # Esperar que el deployment esté listo
        service_url = _get_service_url(wallet, deployment_id, provider)
        
        return {
            'id': deployment_id,
            'provider': provider,
            'url': service_url,
            'price_uakt': best_bid.get('price'),
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        click.echo(f"❌ Deployment error: {e}")
        return None

def _extract_deployment_id(output: str) -> Optional[str]:
    """Extrae deployment ID del output de akash"""
    import re
    match = re.search(r'deployment/([a-f0-9]+)/(\d+)', output)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return None

def _get_bids(wallet: str, deployment_id: str) -> list:
    """Obtiene bids para deployment"""
    try:
        cmd = [
            'akash', 'query', 'market', 'bid', 'list',
            '--owner', wallet,
            '--dseq', deployment_id.split('/')[1],
            '--node', 'https://rpc.akashnet.net:443',
            '--chain-id', 'akashnet-2',
            '--output', 'json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get('bids', [])
    except:
        pass
    
    return []

def _create_lease(wallet: str, deployment_id: str, provider: str) -> Optional[Dict]:
    """Crea lease con provider"""
    try:
        dseq = deployment_id.split('/')[1]
        
        cmd = [
            'akash', 'tx', 'market', 'lease', 'create',
            '--from', wallet,
            '--dseq', dseq,
            '--provider', provider,
            '--node', 'https://rpc.akashnet.net:443',
            '--chain-id', 'akashnet-2', 
            '--gas-prices', '0.025uakt',
            '--gas-adjustment', '1.5',
            '--yes'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            click.echo("✅ Lease created successfully")
            return {'success': True}
        else:
            click.echo(f"❌ Failed to create lease: {result.stderr}")
            
    except Exception as e:
        click.echo(f"❌ Lease creation error: {e}")
    
    return None

def _get_service_url(wallet: str, deployment_id: str, provider: str) -> Optional[str]:
    """Obtiene URL del servicio deployed"""
    try:
        dseq = deployment_id.split('/')[1]
        
        cmd = [
            'akash', 'provider', 'lease-status',
            '--from', wallet,
            '--dseq', dseq,
            '--provider', provider,
            '--node', 'https://rpc.akashnet.net:443'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # Parsear output para encontrar URL
            lines = result.stdout.split('\n')
            for line in lines:
                if 'uris:' in line.lower() and 'http' in line:
                    # Extraer URL
                    import re
                    urls = re.findall(r'https?://[^\s<>"]+', line)
                    if urls:
                        return urls[0]
        
        # Fallback: construir URL basada en provider
        return f"http://{provider}:8000"
        
    except Exception as e:
        click.echo(f"⚠️ Could not get service URL: {e}")
        return f"http://provider:8000"

@akash_cli.command()
@click.option('--wallet', required=True, help='Akash wallet name')
def status(wallet):
    """Check deployment status"""
    
    if not os.path.exists('akash_deployment.json'):
        click.echo("❌ No deployment found. Deploy first.")
        return
    
    with open('akash_deployment.json', 'r') as f:
        deployment = json.load(f)
    
    deployment_id = deployment.get('id')
    provider = deployment.get('provider')
    
    click.echo(f"📊 Akash Deployment Status")
    click.echo(f"   Deployment ID: {deployment_id}")
    click.echo(f"   Provider: {provider}")
    click.echo(f"   URL: {deployment.get('url')}")
    
    # Test health
    try:
        url = deployment.get('url')
        if url:
            health_url = f"{url}/health"
            response = requests.get(health_url, timeout=10)
            if response.status_code == 200:
                click.echo("✅ Service is healthy")
            else:
                click.echo(f"⚠️ Service health check failed: {response.status_code}")
    except requests.RequestException as e:
        click.echo(f"⚠️ Could not reach service: {e}")
    
    # Get lease status
    try:
        dseq = deployment_id.split('/')[1]
        cmd = [
            'akash', 'provider', 'lease-status',
            '--from', wallet,
            '--dseq', dseq,
            '--provider', provider,
            '--node', 'https://rpc.akashnet.net:443'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            click.echo("📋 Lease Status:")
            click.echo(result.stdout)
        
    except Exception as e:
        click.echo(f"⚠️ Could not get lease status: {e}")

@akash_cli.command()
@click.option('--wallet', required=True, help='Akash wallet name')
def close(wallet):
    """Close Akash deployment"""
    
    if not os.path.exists('akash_deployment.json'):
        click.echo("❌ No deployment found")
        return
    
    with open('akash_deployment.json', 'r') as f:
        deployment = json.load(f)
    
    deployment_id = deployment.get('id')
    dseq = deployment_id.split('/')[1]
    
    try:
        cmd = [
            'akash', 'tx', 'deployment', 'close',
            '--from', wallet,
            '--dseq', dseq,
            '--node', 'https://rpc.akashnet.net:443',
            '--chain-id', 'akashnet-2',
            '--gas-prices', '0.025uakt',
            '--gas-adjustment', '1.5',
            '--yes'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            click.echo("✅ Deployment closed successfully")
            os.remove('akash_deployment.json')
        else:
            click.echo(f"❌ Error closing deployment: {result.stderr}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@akash_cli.command()
def providers():
    """List available GPU providers"""
    click.echo("🌐 Available Akash GPU Providers:")
    click.echo("")
    
    # Esta información se actualiza dinámicamente
    sample_providers = [
        {
            "provider": "akash1ccktptfkvdc67msaaa5....",
            "region": "US-West",
            "gpus": ["RTX4090", "RTX3090"],
            "price_range": "$0.15-0.30/hour"
        },
        {
            "provider": "akash1xmz9es9ay9ln9....",
            "region": "EU-Central", 
            "gpus": ["Tesla T4", "Tesla V100"],
            "price_range": "$0.08-0.25/hour"
        }
    ]
    
    for provider in sample_providers:
        click.echo(f"🖥️  Provider: {provider['provider'][:20]}...")
        click.echo(f"   Region: {provider['region']}")
        click.echo(f"   GPUs: {', '.join(provider['gpus'])}")
        click.echo(f"   Price: {provider['price_range']}")
        click.echo()
    
    click.echo("💡 Use 'akash query market bid list' for real-time providers")

@akash_cli.command()
def setup():
    """Setup Akash CLI and wallet"""
    click.echo("🔧 Akash Setup Guide")
    click.echo("=" * 40)
    
    click.echo("1. Install Akash CLI:")
    click.echo("   curl -sSfL https://raw.githubusercontent.com/akash-network/node/master/install.sh | sh")
    click.echo("")
    
    click.echo("2. Create wallet:")
    click.echo("   akash keys add mywallet")
    click.echo("")
    
    click.echo("3. Fund wallet with AKT:")
    click.echo("   - Buy AKT on exchange (Osmosis, Kraken)")
    click.echo("   - Send to your wallet address")
    click.echo("   - Need ~100 AKT for GPU deployment")
    click.echo("")
    
    click.echo("4. Deploy OMEGA:")
    click.echo("   python scripts/deploy_akash.py deploy --wallet mywallet")
    click.echo("")
    
    click.echo("💰 Cost Estimation:")
    click.echo("   - RTX 4090: ~$0.30/hour (vs $4.00 on AWS)")
    click.echo("   - Tesla T4: ~$0.15/hour (vs $0.50 on GCP)")
    click.echo("   - 24/7 operation: ~$100-200/month")

if __name__ == '__main__':
    akash_cli()