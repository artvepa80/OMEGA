#!/usr/bin/env python3
"""
Verificador de entorno Akash - Determina si se ejecuta en Akash o localmente
"""

import os
import socket
import subprocess
import sys
from pathlib import Path

def get_hostname():
    """Obtiene el hostname del sistema"""
    return socket.gethostname()

def get_username():
    """Obtiene el usuario actual"""
    return os.getenv('USER', 'unknown')

def get_public_ip():
    """Obtiene la IP pública"""
    try:
        result = subprocess.run(['curl', '-s', 'ifconfig.me'], 
                              capture_output=True, text=True, timeout=5)
        return result.stdout.strip()
    except:
        return "No disponible"

def check_container_environment():
    """Verifica si se ejecuta en un contenedor"""
    indicators = []
    
    # Check for container files
    container_files = [
        '/.dockerenv',
        '/proc/1/cgroup'
    ]
    
    for file_path in container_files:
        if Path(file_path).exists():
            indicators.append(f"✓ Encontrado: {file_path}")
    
    # Check cgroup for container info
    try:
        with open('/proc/1/cgroup', 'r') as f:
            cgroup_content = f.read()
            if 'docker' in cgroup_content or 'containerd' in cgroup_content:
                indicators.append("✓ Contenedor detectado en cgroup")
    except:
        pass
    
    return indicators

def check_akash_indicators():
    """Busca indicadores específicos de Akash"""
    akash_indicators = []
    
    # Check environment variables
    akash_env_vars = [
        'AKASH_DEPLOYMENT_ID',
        'AKASH_GROUP_SEQUENCE',
        'AKASH_ORDER_SEQUENCE',
        'AKASH_PROVIDER',
        'KUBERNETES_SERVICE_HOST'
    ]
    
    for var in akash_env_vars:
        if os.getenv(var):
            akash_indicators.append(f"✓ Variable de entorno: {var}={os.getenv(var)}")
    
    # Check for typical Akash/Kubernetes files
    k8s_files = [
        '/var/run/secrets/kubernetes.io',
        '/etc/hostname'
    ]
    
    for file_path in k8s_files:
        if Path(file_path).exists():
            akash_indicators.append(f"✓ Archivo K8s encontrado: {file_path}")
    
    return akash_indicators

def main():
    print("🔍 VERIFICADOR DE ENTORNO AKASH")
    print("=" * 50)
    
    # Información básica
    hostname = get_hostname()
    username = get_username()
    public_ip = get_public_ip()
    
    print(f"🏠 Hostname: {hostname}")
    print(f"👤 Usuario: {username}")
    print(f"🌐 IP Pública: {public_ip}")
    print(f"🐍 Python: {sys.executable}")
    print(f"📁 Directorio: {os.getcwd()}")
    
    print("\n" + "=" * 50)
    print("🐳 INDICADORES DE CONTENEDOR:")
    container_indicators = check_container_environment()
    if container_indicators:
        for indicator in container_indicators:
            print(f"  {indicator}")
    else:
        print("  ❌ No se detectaron indicadores de contenedor")
    
    print("\n" + "=" * 50)
    print("☁️  INDICADORES DE AKASH/KUBERNETES:")
    akash_indicators = check_akash_indicators()
    if akash_indicators:
        for indicator in akash_indicators:
            print(f"  {indicator}")
    else:
        print("  ❌ No se detectaron indicadores de Akash")
    
    print("\n" + "=" * 50)
    print("📝 CONCLUSIÓN:")
    
    is_local = (
        'local' in hostname.lower() or 
        username == 'user' or
        (not container_indicators and not akash_indicators)
    )
    
    is_akash = (
        container_indicators and 
        (akash_indicators or 'akash' in hostname.lower())
    )
    
    if is_akash:
        print("  🚀 EJECUTÁNDOSE EN AKASH")
        print(f"  ✓ Deployment detectado en: {hostname}")
    elif is_local:
        print("  🏠 EJECUTÁNDOSE LOCALMENTE")
        print(f"  ✓ Sistema local: {hostname}")
    else:
        print("  ❓ ENTORNO INDETERMINADO")
        print("  ⚠️  No se pudo determinar el entorno con certeza")
    
    print("=" * 50)

if __name__ == "__main__":
    main()