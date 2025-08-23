#!/usr/bin/env python3
"""
🌐 OMEGA PRO AI - Akash Network Deployment
Deploy OMEGA to decentralized cloud with GPU support
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

class AkashDeployer:
    def __init__(self, wallet_name: str, deployment_file: str):
        self.wallet_name = wallet_name
        self.deployment_file = deployment_file
        self.deployment_id = None
        
    def check_balance(self) -> float:
        """Verificar balance de AKT en la wallet"""
        try:
            result = subprocess.run([
                'akash', 'query', 'bank', 'balances', 
                '--node', os.environ.get('AKASH_NODE'),
                subprocess.check_output(['akash', 'keys', 'show', self.wallet_name, '-a']).decode().strip()
            ], capture_output=True, text=True, check=True)
            
            # Parsear resultado JSON
            balances = json.loads(result.stdout)
            akt_balance = 0
            for balance in balances.get('balances', []):
                if balance['denom'] == 'uakt':
                    akt_balance = int(balance['amount']) / 1000000  # Convert uakt to akt
            
            return akt_balance
        except Exception as e:
            click.echo(f"❌ Error checking balance: {e}")
            return 0
    
    def build_and_push_image(self):
        """Build and push Docker image"""
        click.echo("🏗️ Building Docker image for Akash...")
        
        try:
            # Build image
            subprocess.run([
                'docker', 'build', 
                '-f', 'Dockerfile.akash',
                '-t', 'omega-pro-ai:latest',
                '.'
            ], check=True)
            
            click.echo("✅ Docker image built successfully")
            
            # Note: For Akash, you might need to push to a public registry
            click.echo("📝 Note: Consider pushing to Docker Hub or GitHub Container Registry for Akash deployment")
            
        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Error building image: {e}")
            return False
            
        return True
    
    def create_deployment(self) -> bool:
        """Create deployment on Akash"""
        try:
            click.echo("🚀 Creating Akash deployment...")
            
            result = subprocess.run([
                'akash', 'tx', 'deployment', 'create',
                self.deployment_file,
                '--from', self.wallet_name,
                '--node', os.environ.get('AKASH_NODE'),
                '--chain-id', os.environ.get('AKASH_CHAIN_ID'),
                '--gas', '200000',
                '--gas-adjustment', '1.5',
                '--gas-prices', '0.025uakt',
                '--broadcast-mode', 'block',
                '--yes'
            ], capture_output=True, text=True, check=True)
            
            # Extract deployment ID from result
            lines = result.stdout.split('\n')
            for line in lines:
                if 'deployment created' in line.lower() or 'dseq' in line:
                    # Extract deployment sequence number
                    import re
                    dseq_match = re.search(r'dseq:?\s*(\d+)', line)
                    if dseq_match:
                        self.deployment_id = dseq_match.group(1)
                        break
            
            if self.deployment_id:
                click.echo(f"✅ Deployment created successfully! ID: {self.deployment_id}")
                return True
            else:
                click.echo("❌ Could not extract deployment ID")
                return False
                
        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Error creating deployment: {e}")
            click.echo(f"Output: {e.stdout}")
            click.echo(f"Error: {e.stderr}")
            return False
    
    def wait_for_bids(self, timeout: int = 300):
        """Wait for provider bids"""
        click.echo("⏳ Waiting for provider bids...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                result = subprocess.run([
                    'akash', 'query', 'market', 'bid', 'list',
                    '--owner', subprocess.check_output(['akash', 'keys', 'show', self.wallet_name, '-a']).decode().strip(),
                    '--dseq', self.deployment_id,
                    '--node', os.environ.get('AKASH_NODE'),
                    '--output', 'json'
                ], capture_output=True, text=True, check=True)
                
                bids = json.loads(result.stdout)
                if bids.get('bids'):
                    click.echo(f"📦 Found {len(bids['bids'])} bids!")
                    
                    # Show bid details
                    for i, bid in enumerate(bids['bids']):
                        price_uakt = int(bid['bid']['price']['amount'])
                        price_akt_hour = (price_uakt * 24) / 1000000  # Convert to AKT per day
                        click.echo(f"  {i+1}. Provider: {bid['bid']['bidder'][:12]}...")
                        click.echo(f"     Price: {price_uakt} uAKT/block (~${price_akt_hour:.2f}/day)")
                    
                    return bids['bids']
                
                click.echo(".", end="", flush=True)
                time.sleep(10)
                
            except Exception as e:
                click.echo(f"❌ Error checking bids: {e}")
                break
        
        click.echo("\n⏰ Timeout waiting for bids")
        return []
    
    def accept_bid(self, provider: str) -> bool:
        """Accept a bid from a provider"""
        try:
            click.echo(f"✅ Accepting bid from provider: {provider[:12]}...")
            
            subprocess.run([
                'akash', 'tx', 'market', 'lease', 'create',
                '--owner', subprocess.check_output(['akash', 'keys', 'show', self.wallet_name, '-a']).decode().strip(),
                '--dseq', self.deployment_id,
                '--gseq', '1',
                '--oseq', '1',
                '--provider', provider,
                '--from', self.wallet_name,
                '--node', os.environ.get('AKASH_NODE'),
                '--chain-id', os.environ.get('AKASH_CHAIN_ID'),
                '--gas', '200000',
                '--gas-adjustment', '1.5',
                '--gas-prices', '0.025uakt',
                '--broadcast-mode', 'block',
                '--yes'
            ], check=True)
            
            click.echo("✅ Lease created successfully!")
            return True
            
        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Error accepting bid: {e}")
            return False
    
    def get_lease_status(self) -> Dict[str, Any]:
        """Get deployment status and URI"""
        try:
            result = subprocess.run([
                'akash', 'provider', 'lease-status',
                '--node', os.environ.get('AKASH_NODE'),
                '--dseq', self.deployment_id,
                '--gseq', '1',
                '--oseq', '1',
                '--provider', self.provider,
                '--from', self.wallet_name
            ], capture_output=True, text=True, check=True)
            
            # Parse lease status
            return json.loads(result.stdout)
            
        except Exception as e:
            click.echo(f"❌ Error getting lease status: {e}")
            return {}

@click.command()
@click.option('--wallet', required=True, help='Akash wallet name')
@click.option('--deployment-file', default='deploy/omega-akash-gpu.yaml', help='SDL deployment file')
@click.option('--build-image', is_flag=True, help='Build Docker image before deploy')
@click.option('--auto-accept', is_flag=True, help='Auto-accept lowest bid')
def deploy(wallet, deployment_file, build_image, auto_accept):
    """Deploy OMEGA PRO AI to Akash Network"""
    
    click.echo("🌐 OMEGA PRO AI - Akash Network Deployment")
    click.echo("=" * 50)
    
    # Check if deployment file exists
    if not Path(deployment_file).exists():
        click.echo(f"❌ Deployment file not found: {deployment_file}")
        return
    
    deployer = AkashDeployer(wallet, deployment_file)
    
    # Check wallet balance
    balance = deployer.check_balance()
    click.echo(f"💰 Wallet balance: {balance:.2f} AKT")
    
    if balance < 5:
        click.echo("⚠️  Low AKT balance! You need at least 5 AKT for deployment.")
        if not click.confirm("Continue anyway?"):
            return
    
    # Build image if requested
    if build_image:
        if not deployer.build_and_push_image():
            return
    
    # Create deployment
    if not deployer.create_deployment():
        return
    
    # Wait for bids
    bids = deployer.wait_for_bids()
    if not bids:
        click.echo("❌ No bids received. Try again later or adjust pricing.")
        return
    
    # Select and accept bid
    if auto_accept:
        # Accept lowest bid
        lowest_bid = min(bids, key=lambda x: int(x['bid']['price']['amount']))
        provider = lowest_bid['bid']['bidder']
    else:
        # Let user choose
        click.echo("\nSelect a provider:")
        for i, bid in enumerate(bids):
            click.echo(f"{i}: {bid['bid']['bidder']}")
        
        choice = click.prompt("Enter provider number", type=int)
        if choice < 0 or choice >= len(bids):
            click.echo("❌ Invalid choice")
            return
        provider = bids[choice]['bid']['bidder']
    
    deployer.provider = provider
    if not deployer.accept_bid(provider):
        return
    
    # Wait a bit for lease to be active
    click.echo("⏳ Waiting for deployment to be active...")
    time.sleep(30)
    
    # Get deployment info
    lease_status = deployer.get_lease_status()
    if lease_status:
        click.echo("\n🎉 OMEGA PRO AI deployed successfully!")
        click.echo("=" * 50)
        click.echo(f"🆔 Deployment ID: {deployer.deployment_id}")
        click.echo(f"🏢 Provider: {provider}")
        
        if 'services' in lease_status:
            for service_name, service_info in lease_status['services'].items():
                if 'uris' in service_info:
                    for uri in service_info['uris']:
                        click.echo(f"🌐 OMEGA API URL: {uri}")
                        click.echo(f"📊 Health check: {uri}/health")
                        click.echo(f"🧠 Predictions: {uri}/predict")
    
    click.echo("\n📝 Useful commands:")
    click.echo(f"akash provider lease-status --dseq {deployer.deployment_id} --provider {provider} --from {wallet}")
    click.echo(f"akash tx deployment close --dseq {deployer.deployment_id} --from {wallet}")

if __name__ == "__main__":
    # Load Akash environment variables
    env_file = Path("akash_env.sh")
    if env_file.exists():
        click.echo("📋 Loading Akash environment...")
        # Note: In production, you'd source this file
        # For now, user needs to source it manually
        pass
    
    deploy()