#!/usr/bin/env python3
"""
Generate Diffie-Hellman parameters for enhanced SSL security
"""

import subprocess
import click
import os
from pathlib import Path

@click.command()
@click.option('--bits', default=2048, help='DH parameter size in bits (default: 2048)')
@click.option('--output', default='./ssl/dhparam.pem', help='Output file path')
def generate_dhparam(bits, output):
    """Generate Diffie-Hellman parameters for SSL"""
    
    output_path = Path(output)
    output_path.parent.mkdir(exist_ok=True)
    
    click.echo(f"🔐 Generating {bits}-bit Diffie-Hellman parameters...")
    click.echo("⏳ This may take several minutes...")
    
    try:
        cmd = ['openssl', 'dhparam', '-out', str(output_path), str(bits)]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 minute timeout
        
        if result.returncode == 0:
            # Set secure permissions
            os.chmod(output_path, 0o644)
            
            click.echo(f"✅ DH parameters generated successfully: {output_path}")
            
            # Verify the generated parameters
            verify_cmd = ['openssl', 'dhparam', '-in', str(output_path), '-check', '-noout']
            verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
            
            if verify_result.returncode == 0:
                click.echo("✅ DH parameters verification successful")
            else:
                click.echo("⚠️ DH parameters verification failed")
                click.echo(f"   Error: {verify_result.stderr}")
                
        else:
            click.echo("❌ DH parameter generation failed")
            click.echo(f"   Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        click.echo("❌ DH parameter generation timed out")
    except Exception as e:
        click.echo(f"❌ DH parameter generation failed: {e}")

if __name__ == '__main__':
    generate_dhparam()