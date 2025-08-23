#!/usr/bin/env python3
"""
🚀 OMEGA GPU Cloud Deployment Script
Despliegue automatizado en proveedores GPU cloud
"""

import click
import subprocess
import json
import time
import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

@click.group()
def deploy_cli():
    """OMEGA GPU Cloud Deployment CLI"""
    pass

@deploy_cli.group()
def gcp():
    """Google Cloud Platform deployment"""
    pass

@gcp.command()
@click.option('--project-id', required=True, help='GCP Project ID')
@click.option('--zone', default='us-central1-a', help='GCP Zone')
@click.option('--instance-type', default='n1-standard-4', help='Instance type')
@click.option('--gpu-type', default='nvidia-tesla-t4', help='GPU type')
@click.option('--gpu-count', default=1, help='Number of GPUs')
@click.option('--disk-size', default=100, help='Boot disk size in GB')
def create_instance(project_id, zone, instance_type, gpu_type, gpu_count, disk_size):
    """Create GCP GPU instance"""
    
    click.echo(f"🚀 Creating GCP GPU instance...")
    click.echo(f"   Project: {project_id}")
    click.echo(f"   Zone: {zone}")
    click.echo(f"   Instance: {instance_type}")
    click.echo(f"   GPU: {gpu_count}x {gpu_type}")
    
    # Crear instancia con GPU
    create_cmd = [
        'gcloud', 'compute', 'instances', 'create', 'omega-gpu-instance',
        '--project', project_id,
        '--zone', zone,
        '--machine-type', instance_type,
        '--accelerator', f'type={gpu_type},count={gpu_count}',
        '--boot-disk-size', str(disk_size),
        '--boot-disk-type', 'pd-ssd',
        '--image-family', 'ubuntu-2004-lts',
        '--image-project', 'ubuntu-os-cloud',
        '--maintenance-policy', 'TERMINATE',
        '--restart-on-failure',
        '--scopes', 'cloud-platform',
        '--tags', 'omega-gpu,http-server,https-server',
        '--metadata', 'startup-script=#!/bin/bash\n' +
                     'apt-get update && apt-get install -y docker.io docker-compose\n' +
                     'systemctl enable docker && systemctl start docker\n' +
                     'usermod -aG docker $(whoami)\n' +
                     'curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -\n' +
                     'distribution=$(. /etc/os-release;echo $ID$VERSION_ID)\n' +
                     'curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list\n' +
                     'apt-get update && apt-get install -y nvidia-docker2\n' +
                     'systemctl restart docker'
    ]
    
    try:
        result = subprocess.run(create_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            click.echo("✅ Instance created successfully!")
            
            # Obtener IP externa
            ip_cmd = [
                'gcloud', 'compute', 'instances', 'describe', 'omega-gpu-instance',
                '--project', project_id,
                '--zone', zone,
                '--format', 'get(networkInterfaces[0].accessConfigs[0].natIP)'
            ]
            
            ip_result = subprocess.run(ip_cmd, capture_output=True, text=True)
            if ip_result.returncode == 0:
                external_ip = ip_result.stdout.strip()
                click.echo(f"🌐 External IP: {external_ip}")
                
                # Guardar información de despliegue
                deployment_info = {
                    'provider': 'gcp',
                    'project_id': project_id,
                    'zone': zone,
                    'instance_name': 'omega-gpu-instance',
                    'instance_type': instance_type,
                    'gpu_type': gpu_type,
                    'gpu_count': gpu_count,
                    'external_ip': external_ip,
                    'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                with open('deployment_info.json', 'w') as f:
                    json.dump(deployment_info, f, indent=2)
                
                click.echo("📄 Deployment info saved to deployment_info.json")
                click.echo("\n🔧 Next steps:")
                click.echo(f"1. SSH to instance: gcloud compute ssh omega-gpu-instance --project {project_id} --zone {zone}")
                click.echo("2. Wait for startup script to complete (~5 minutes)")
                click.echo("3. Clone your repository and run: python scripts/deploy_gpu_cloud.py deploy-app")
            
        else:
            click.echo(f"❌ Error creating instance: {result.stderr}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@gcp.command()
@click.option('--project-id', required=True, help='GCP Project ID')
@click.option('--zone', default='us-central1-a', help='GCP Zone')
def delete_instance(project_id, zone):
    """Delete GCP GPU instance"""
    
    click.echo("🗑️ Deleting GCP GPU instance...")
    
    delete_cmd = [
        'gcloud', 'compute', 'instances', 'delete', 'omega-gpu-instance',
        '--project', project_id,
        '--zone', zone,
        '--quiet'
    ]
    
    try:
        result = subprocess.run(delete_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            click.echo("✅ Instance deleted successfully!")
            
            # Limpiar archivo de deployment
            if os.path.exists('deployment_info.json'):
                os.remove('deployment_info.json')
                click.echo("📄 Deployment info cleaned up")
        else:
            click.echo(f"❌ Error deleting instance: {result.stderr}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@deploy_cli.group()
def aws():
    """Amazon AWS deployment"""
    pass

@aws.command()
@click.option('--region', default='us-west-2', help='AWS Region')
@click.option('--instance-type', default='g4dn.xlarge', help='Instance type')
@click.option('--key-name', required=True, help='EC2 Key Pair name')
@click.option('--security-group', help='Security Group ID (optional)')
def create_instance(region, instance_type, key_name, security_group):
    """Create AWS GPU instance"""
    
    click.echo(f"🚀 Creating AWS GPU instance...")
    click.echo(f"   Region: {region}")
    click.echo(f"   Instance: {instance_type}")
    click.echo(f"   Key: {key_name}")
    
    # AMI optimizada para Deep Learning (Ubuntu con GPU drivers)
    ami_id = "ami-0c2f25c1f66a1ff4d"  # Deep Learning AMI Ubuntu 20.04
    
    user_data_script = """#!/bin/bash
apt-get update
apt-get install -y docker.io docker-compose
systemctl enable docker && systemctl start docker
usermod -aG docker ubuntu

# Install nvidia-docker2
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list
apt-get update && apt-get install -y nvidia-docker2
systemctl restart docker

# Install monitoring tools
pip3 install gpustat nvidia-ml-py
"""
    
    # Crear instancia
    create_cmd = [
        'aws', 'ec2', 'run-instances',
        '--region', region,
        '--image-id', ami_id,
        '--instance-type', instance_type,
        '--key-name', key_name,
        '--user-data', user_data_script,
        '--tag-specifications', 'ResourceType=instance,Tags=[{Key=Name,Value=omega-gpu-instance}]',
        '--block-device-mappings', '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":100,"VolumeType":"gp3"}}]'
    ]
    
    if security_group:
        create_cmd.extend(['--security-group-ids', security_group])
    
    try:
        result = subprocess.run(create_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            response = json.loads(result.stdout)
            instance_id = response['Instances'][0]['InstanceId']
            
            click.echo(f"✅ Instance created: {instance_id}")
            click.echo("⏳ Waiting for instance to be ready...")
            
            # Esperar que la instancia esté running
            wait_cmd = [
                'aws', 'ec2', 'wait', 'instance-running',
                '--region', region,
                '--instance-ids', instance_id
            ]
            subprocess.run(wait_cmd)
            
            # Obtener IP pública
            describe_cmd = [
                'aws', 'ec2', 'describe-instances',
                '--region', region,
                '--instance-ids', instance_id,
                '--query', 'Reservations[0].Instances[0].PublicIpAddress',
                '--output', 'text'
            ]
            
            ip_result = subprocess.run(describe_cmd, capture_output=True, text=True)
            public_ip = ip_result.stdout.strip()
            
            # Guardar información
            deployment_info = {
                'provider': 'aws',
                'region': region,
                'instance_id': instance_id,
                'instance_type': instance_type,
                'public_ip': public_ip,
                'key_name': key_name,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open('deployment_info.json', 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
            click.echo(f"🌐 Public IP: {public_ip}")
            click.echo("📄 Deployment info saved to deployment_info.json")
            click.echo("\n🔧 Next steps:")
            click.echo(f"1. SSH to instance: ssh -i ~/.ssh/{key_name}.pem ubuntu@{public_ip}")
            click.echo("2. Wait for startup script to complete (~5 minutes)")
            click.echo("3. Clone repository and deploy")
            
        else:
            click.echo(f"❌ Error creating instance: {result.stderr}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@deploy_cli.command()
def deploy_app():
    """Deploy OMEGA app on current GPU instance"""
    
    click.echo("🚀 Deploying OMEGA Pro AI on GPU instance...")
    
    # Verificar que Docker esté disponible
    try:
        subprocess.run(['docker', '--version'], check=True, capture_output=True)
        click.echo("✅ Docker is available")
    except:
        click.echo("❌ Docker not found. Please install Docker first.")
        return
    
    # Verificar GPU
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            click.echo("✅ NVIDIA GPU detected")
            click.echo(f"GPU Info:\n{result.stdout}")
        else:
            click.echo("⚠️ No NVIDIA GPU detected")
    except:
        click.echo("⚠️ nvidia-smi not available")
    
    # Build imagen Docker
    click.echo("🔨 Building Docker image...")
    build_cmd = ['docker', 'build', '-f', 'Dockerfile.gpu', '-t', 'omega-pro-gpu', '.']
    
    try:
        subprocess.run(build_cmd, check=True)
        click.echo("✅ Docker image built successfully")
    except subprocess.CalledProcessError:
        click.echo("❌ Docker build failed")
        return
    
    # Instalar nvidia-docker-runtime si no está
    try:
        subprocess.run(['docker', 'run', '--rm', '--gpus', 'all', 'nvidia/cuda:11.8-base-ubuntu20.04', 'nvidia-smi'], check=True, capture_output=True)
        click.echo("✅ GPU Docker runtime is working")
    except:
        click.echo("⚠️ GPU Docker runtime issues detected")
    
    # Ejecutar docker-compose
    click.echo("🚀 Starting services with docker-compose...")
    
    try:
        subprocess.run(['docker-compose', '-f', 'docker-compose.gpu.yml', 'up', '-d'], check=True)
        click.echo("✅ Services started successfully!")
        
        # Esperar que los servicios estén listos
        click.echo("⏳ Waiting for services to be ready...")
        time.sleep(30)
        
        # Verificar estado de los servicios
        status_cmd = ['docker-compose', '-f', 'docker-compose.gpu.yml', 'ps']
        result = subprocess.run(status_cmd, capture_output=True, text=True)
        click.echo("📊 Service Status:")
        click.echo(result.stdout)
        
        # Test de salud
        click.echo("🏥 Testing health endpoints...")
        try:
            import requests
            
            health_response = requests.get('http://localhost:8000/health', timeout=10)
            if health_response.status_code == 200:
                click.echo("✅ API health check passed")
            else:
                click.echo(f"⚠️ API health check failed: {health_response.status_code}")
        
        except ImportError:
            click.echo("⚠️ requests not available for health check")
        except Exception as e:
            click.echo(f"⚠️ Health check failed: {e}")
        
        # Mostrar URLs de acceso
        click.echo("\n🌐 Service URLs:")
        click.echo("   API: http://localhost:8000")
        click.echo("   API Docs: http://localhost:8000/docs")
        click.echo("   Grafana: http://localhost:3000 (admin/omega123)")
        click.echo("   Prometheus: http://localhost:9090")
        click.echo("   GPU Metrics: http://localhost:9400/metrics")
        
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Failed to start services: {e}")

@deploy_cli.command()
def monitor():
    """Monitor GPU instance performance"""
    
    click.echo("📊 GPU Instance Monitoring")
    click.echo("=" * 40)
    
    # GPU Stats
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu', '--format=csv,noheader,nounits'], capture_output=True, text=True)
        if result.returncode == 0:
            click.echo("🔧 GPU Status:")
            for line in result.stdout.strip().split('\n'):
                parts = line.split(', ')
                if len(parts) >= 5:
                    name, total_mem, used_mem, util, temp = parts
                    click.echo(f"   {name}: {used_mem}MB/{total_mem}MB ({util}% util, {temp}°C)")
        else:
            click.echo("⚠️ Could not get GPU stats")
    except:
        click.echo("⚠️ nvidia-smi not available")
    
    # Docker Stats
    try:
        result = subprocess.run(['docker', 'stats', '--no-stream', '--format', 'table {{.Name}}\\t{{.CPUPerc}}\\t{{.MemUsage}}\\t{{.NetIO}}'], capture_output=True, text=True)
        if result.returncode == 0:
            click.echo("\n🐳 Docker Container Stats:")
            click.echo(result.stdout)
    except:
        click.echo("⚠️ Could not get Docker stats")
    
    # System stats
    try:
        import psutil
        
        click.echo(f"\n💻 System Stats:")
        click.echo(f"   CPU: {psutil.cpu_percent()}%")
        click.echo(f"   RAM: {psutil.virtual_memory().percent}%")
        click.echo(f"   Disk: {psutil.disk_usage('/').percent}%")
        
        # Network
        net = psutil.net_io_counters()
        click.echo(f"   Network: {net.bytes_sent//1024//1024}MB sent, {net.bytes_recv//1024//1024}MB recv")
        
    except ImportError:
        click.echo("⚠️ psutil not available for system stats")

@deploy_cli.command()
def logs():
    """Show application logs"""
    
    click.echo("📋 Application Logs")
    click.echo("=" * 40)
    
    try:
        # Logs de la aplicación principal
        result = subprocess.run(['docker', 'logs', '--tail', '50', 'omega-pro-gpu'], capture_output=True, text=True)
        if result.returncode == 0:
            click.echo("🚀 OMEGA Pro GPU Logs:")
            click.echo(result.stdout)
            if result.stderr:
                click.echo("Errors:")
                click.echo(result.stderr)
        
        # Logs de Redis
        click.echo("\n📦 Redis Logs:")
        redis_result = subprocess.run(['docker', 'logs', '--tail', '10', 'omega-redis'], capture_output=True, text=True)
        if redis_result.returncode == 0:
            click.echo(redis_result.stdout)
    
    except Exception as e:
        click.echo(f"❌ Error getting logs: {e}")

@deploy_cli.command()
def stop():
    """Stop all services"""
    
    click.echo("🛑 Stopping OMEGA services...")
    
    try:
        subprocess.run(['docker-compose', '-f', 'docker-compose.gpu.yml', 'down'], check=True)
        click.echo("✅ All services stopped")
    except subprocess.CalledProcessError:
        click.echo("❌ Error stopping services")

@deploy_cli.command()
def benchmark():
    """Run GPU performance benchmark"""
    
    click.echo("🏁 Running GPU Performance Benchmark...")
    
    # Crear script de benchmark temporal
    benchmark_script = """
import torch
import time
import json

def run_benchmark():
    if not torch.cuda.is_available():
        return {"error": "CUDA not available"}
    
    device = torch.device('cuda')
    results = {}
    
    # Test 1: Matrix Multiplication
    size = 2048
    a = torch.randn(size, size, device=device)
    b = torch.randn(size, size, device=device)
    
    torch.cuda.synchronize()
    start = time.time()
    
    for _ in range(100):
        c = torch.matmul(a, b)
    
    torch.cuda.synchronize()
    matmul_time = time.time() - start
    results['matmul_time_ms'] = matmul_time * 10  # per iteration
    
    # Test 2: Memory Bandwidth
    large_tensor = torch.randn(50_000_000, device=device)  # ~200MB
    
    torch.cuda.synchronize()
    start = time.time()
    
    for _ in range(10):
        copied = large_tensor.clone()
    
    torch.cuda.synchronize()
    memory_time = time.time() - start
    bandwidth_gb_s = (200 * 2 * 10) / (memory_time * 1024)  # Read + Write
    results['memory_bandwidth_gb_s'] = bandwidth_gb_s
    
    # GPU Info
    results['gpu_name'] = torch.cuda.get_device_name(0)
    results['gpu_memory_gb'] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    
    return results

if __name__ == "__main__":
    results = run_benchmark()
    print(json.dumps(results, indent=2))
"""
    
    # Ejecutar benchmark dentro del container
    try:
        # Escribir script temporal
        with open('/tmp/gpu_benchmark.py', 'w') as f:
            f.write(benchmark_script)
        
        # Copiar al container y ejecutar
        subprocess.run(['docker', 'cp', '/tmp/gpu_benchmark.py', 'omega-pro-gpu:/tmp/'], check=True)
        
        result = subprocess.run(['docker', 'exec', 'omega-pro-gpu', 'python3', '/tmp/gpu_benchmark.py'], capture_output=True, text=True)
        
        if result.returncode == 0:
            benchmark_data = json.loads(result.stdout)
            
            click.echo("🏁 Benchmark Results:")
            click.echo(f"   GPU: {benchmark_data.get('gpu_name', 'Unknown')}")
            click.echo(f"   Memory: {benchmark_data.get('gpu_memory_gb', 0):.1f} GB")
            click.echo(f"   MatMul Performance: {benchmark_data.get('matmul_time_ms', 0):.2f} ms")
            click.echo(f"   Memory Bandwidth: {benchmark_data.get('memory_bandwidth_gb_s', 0):.1f} GB/s")
        else:
            click.echo(f"❌ Benchmark failed: {result.stderr}")
            
        # Limpiar
        os.remove('/tmp/gpu_benchmark.py')
        
    except Exception as e:
        click.echo(f"❌ Error running benchmark: {e}")

if __name__ == '__main__':
    deploy_cli()