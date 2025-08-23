#!/usr/bin/env python3
"""
🐳 Docker Registry Deployment Script for OMEGA Pro AI
Handles secure Docker image building and pushing to public registries
"""

import click
import subprocess
import os
import json
import time
from pathlib import Path
from datetime import datetime

@click.group()
def docker_cli():
    """Docker Registry Deployment CLI"""
    pass

@docker_cli.command()
@click.option('--registry', default='ghcr.io/omega-pro-ai', help='Docker registry URL')
@click.option('--github-token', envvar='GITHUB_TOKEN', help='GitHub token for registry auth')
@click.option('--push', is_flag=True, help='Push images to registry after building')
def build_secure_images(registry, github_token, push):
    """Build secure Docker images with SSL support"""
    
    click.echo("🐳 Building secure Docker images...")
    
    # Check if Docker is available
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            click.echo("❌ Docker not found. Please install Docker Desktop or Docker CLI.")
            return
        click.echo(f"✅ Docker found: {result.stdout.strip()}")
    except FileNotFoundError:
        click.echo("❌ Docker not found. Please install Docker Desktop or Docker CLI.")
        click.echo("   macOS: brew install --cask docker")
        click.echo("   Linux: curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh")
        return
    
    # Define images to build
    images = [
        {
            'name': 'omega-api',
            'dockerfile': 'Dockerfile.secure-api',
            'tag': f"{registry}/omega-api:latest"
        },
        {
            'name': 'omega-gpu',
            'dockerfile': 'Dockerfile.secure-gpu', 
            'tag': f"{registry}/omega-gpu:latest"
        }
    ]
    
    build_results = []
    
    for image in images:
        click.echo(f"📦 Building {image['name']}...")
        
        # Check if Dockerfile exists
        if not Path(image['dockerfile']).exists():
            click.echo(f"❌ Dockerfile not found: {image['dockerfile']}")
            continue
        
        try:
            # Build Docker image
            build_cmd = [
                'docker', 'build',
                '-f', image['dockerfile'],
                '-t', image['tag'],
                '--progress=plain',
                '.'
            ]
            
            click.echo(f"Running: {' '.join(build_cmd)}")
            result = subprocess.run(build_cmd, capture_output=True, text=True, timeout=1800)
            
            if result.returncode == 0:
                click.echo(f"✅ {image['name']} built successfully")
                build_results.append({
                    'image': image['name'],
                    'tag': image['tag'],
                    'status': 'success',
                    'size': _get_image_size(image['tag'])
                })
            else:
                click.echo(f"❌ Failed to build {image['name']}")
                click.echo(f"Error: {result.stderr}")
                build_results.append({
                    'image': image['name'],
                    'tag': image['tag'],
                    'status': 'failed',
                    'error': result.stderr
                })
        except subprocess.TimeoutExpired:
            click.echo(f"❌ Build timeout for {image['name']}")
        except Exception as e:
            click.echo(f"❌ Build error for {image['name']}: {e}")
    
    # Push images if requested and GitHub token provided
    if push and github_token:
        click.echo("🚀 Pushing images to registry...")
        _push_images(registry, github_token, build_results)
    elif push:
        click.echo("⚠️ GitHub token required for pushing. Set GITHUB_TOKEN environment variable.")
    
    # Save build results
    results_file = Path('build_results.json')
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'registry': registry,
            'images': build_results
        }, f, indent=2)
    
    click.echo(f"📊 Build results saved to {results_file}")

def _get_image_size(tag):
    """Get Docker image size"""
    try:
        result = subprocess.run(['docker', 'images', tag, '--format', 'table {{.Size}}'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                return lines[1]
    except:
        pass
    return 'Unknown'

def _push_images(registry, github_token, build_results):
    """Push images to registry"""
    
    # Login to GitHub Container Registry
    try:
        login_cmd = ['docker', 'login', 'ghcr.io', '-u', 'oauth2token', '--password-stdin']
        result = subprocess.run(login_cmd, input=github_token, text=True, capture_output=True)
        
        if result.returncode == 0:
            click.echo("✅ Successfully logged into GitHub Container Registry")
        else:
            click.echo(f"❌ Registry login failed: {result.stderr}")
            return
    except Exception as e:
        click.echo(f"❌ Registry login error: {e}")
        return
    
    # Push each successful build
    for result in build_results:
        if result['status'] == 'success':
            click.echo(f"⬆️ Pushing {result['image']}...")
            
            try:
                push_cmd = ['docker', 'push', result['tag']]
                push_result = subprocess.run(push_cmd, capture_output=True, text=True, timeout=900)
                
                if push_result.returncode == 0:
                    click.echo(f"✅ {result['image']} pushed successfully")
                    result['pushed'] = True
                else:
                    click.echo(f"❌ Failed to push {result['image']}: {push_result.stderr}")
                    result['pushed'] = False
                    result['push_error'] = push_result.stderr
                    
            except subprocess.TimeoutExpired:
                click.echo(f"❌ Push timeout for {result['image']}")
                result['pushed'] = False
                result['push_error'] = 'Timeout'
            except Exception as e:
                click.echo(f"❌ Push error for {result['image']}: {e}")
                result['pushed'] = False
                result['push_error'] = str(e)

@docker_cli.command()
@click.option('--registry', default='ghcr.io/omega-pro-ai', help='Docker registry URL')
def list_images(registry):
    """List built Docker images"""
    
    click.echo("🐳 Docker Images:")
    
    try:
        # List local images
        result = subprocess.run(['docker', 'images', '--format', 'table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if registry in line or 'omega' in line.lower():
                    click.echo(f"   {line}")
        else:
            click.echo("❌ Failed to list Docker images")
            
    except Exception as e:
        click.echo(f"❌ Error listing images: {e}")

@docker_cli.command()
def create_dockerignore():
    """Create optimized .dockerignore file"""
    
    dockerignore_content = """# OMEGA Pro AI - Docker Ignore File
# Ignore development and build artifacts

# Version control
.git/
.gitignore
.github/

# Documentation
*.md
docs/
README*
*.pdf

# Development files
.env
.env.*
*.log
*.bak
*.backup
*.tmp
*.temp

# IDE and editor files
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db
*.desktop

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
.coverage
.pytest_cache/
.mypy_cache/
.dmypy.json
dmypy.json

# Build artifacts
build/
dist/
*.egg-info/
.eggs/

# Node.js (if any)
node_modules/
npm-debug.log*

# Jupyter
.ipynb_checkpoints/

# Data files (large datasets)
data/backups/
data/olds/
*.csv
*.json
!config/*.json

# Logs and output
logs/
output/
outputs/
results/
*.log

# Models and checkpoints (too large for container)
models/
checkpoints/
*.pth
*.h5
*.pkl

# Test files
test/
tests/
*_test.py
test_*.py

# Deployment files (not needed in container)
deploy/
scripts/
docker-compose*.yml
Dockerfile*
!Dockerfile.secure-api
!Dockerfile.secure-gpu

# Temporary files
tmp/
.cache/
"""

    with open('.dockerignore', 'w') as f:
        f.write(dockerignore_content)
    
    click.echo("✅ .dockerignore file created")
    click.echo("   This will reduce Docker build context size and improve build speed")

@docker_cli.command()
def setup_registry_auth():
    """Setup GitHub Container Registry authentication"""
    
    click.echo("🔐 Setting up GitHub Container Registry authentication...")
    
    # Check if GitHub token is available
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        click.echo("❌ GITHUB_TOKEN environment variable not set")
        click.echo("")
        click.echo("To setup authentication:")
        click.echo("1. Go to https://github.com/settings/tokens")
        click.echo("2. Create a new token with 'write:packages' permission")
        click.echo("3. Export the token: export GITHUB_TOKEN=your_token_here")
        click.echo("4. Run this command again")
        return
    
    # Test authentication
    try:
        login_cmd = ['docker', 'login', 'ghcr.io', '-u', 'oauth2token', '--password-stdin']
        result = subprocess.run(login_cmd, input=github_token, text=True, capture_output=True)
        
        if result.returncode == 0:
            click.echo("✅ Successfully authenticated with GitHub Container Registry")
        else:
            click.echo(f"❌ Authentication failed: {result.stderr}")
    except Exception as e:
        click.echo(f"❌ Authentication error: {e}")

if __name__ == '__main__':
    docker_cli()