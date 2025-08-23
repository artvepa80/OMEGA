#!/usr/bin/env python3
"""
OMEGA PRO AI v10.1 - Akash Deployment Connector
Conecta con el despliegue activo de OMEGA en Akash Network
"""

import requests
import json
import sys
from datetime import datetime

class OmegaAkashConnector:
    def __init__(self):
        self.dseq = "22849193"
        self.api_key = "ac.sk.production.a16cbf***c4cad7"  # Tu API key
        self.possible_urls = [
            f"https://{self.dseq}.ingress.akashnet.net",
            f"http://{self.dseq}.ingress.akashnet.net",
            f"https://omega-api-{self.dseq}.akashnet.net",
            f"https://{self.dseq}.provider.akash.network",
            f"https://app-{self.dseq}.akash.network",
        ]
        
    def test_connection(self, url, endpoint=""):
        """Probar conexión a una URL específica"""
        full_url = f"{url}{endpoint}"
        headers = {
            'User-Agent': 'OMEGA-Connector/1.0',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        try:
            print(f"🔄 Probando: {full_url}")
            response = requests.get(full_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ ÉXITO: {full_url}")
                print(f"📊 Status: {response.status_code}")
                try:
                    data = response.json()
                    print(f"📋 Respuesta: {json.dumps(data, indent=2)}")
                    return full_url, data
                except:
                    print(f"📋 Respuesta (text): {response.text[:200]}...")
                    return full_url, response.text
            else:
                print(f"❌ Error {response.status_code}: {full_url}")
                return None, None
                
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout: {full_url}")
            return None, None
        except requests.exceptions.ConnectionError:
            print(f"🚫 Sin conexión: {full_url}")
            return None, None
        except Exception as e:
            print(f"💥 Error: {full_url} - {e}")
            return None, None
    
    def find_active_endpoint(self):
        """Buscar el endpoint activo de OMEGA"""
        print("🚀 OMEGA PRO AI v10.1 - Buscando despliegue activo en Akash")
        print("=" * 60)
        print(f"📡 DSEQ: {self.dseq}")
        print(f"🔑 API Key: {self.api_key[:20]}...")
        print(f"⏰ Timestamp: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Endpoints típicos de aplicaciones
        endpoints_to_test = [
            "",           # Root
            "/",          # Root con slash
            "/health",    # Health check
            "/info",      # Info endpoint
            "/api/v1",    # API versioned
            "/predict",   # OMEGA prediction endpoint
        ]
        
        active_endpoints = []
        
        for url in self.possible_urls:
            print(f"\n🌐 Probando base URL: {url}")
            
            for endpoint in endpoints_to_test:
                result_url, result_data = self.test_connection(url, endpoint)
                if result_url:
                    active_endpoints.append({
                        'url': result_url,
                        'data': result_data,
                        'endpoint': endpoint or '/'
                    })
        
        if active_endpoints:
            print(f"\n🎉 ¡ENCONTRADOS {len(active_endpoints)} ENDPOINTS ACTIVOS!")
            print("=" * 60)
            
            for i, endpoint in enumerate(active_endpoints, 1):
                print(f"\n{i}. {endpoint['url']}")
                print(f"   Endpoint: {endpoint['endpoint']}")
                if isinstance(endpoint['data'], dict):
                    print(f"   Tipo: JSON Response")
                else:
                    print(f"   Tipo: Text Response")
            
            return active_endpoints
        else:
            print("\n❌ No se encontraron endpoints activos")
            print("\n💡 SUGERENCIAS:")
            print("1. Verifica que el despliegue esté realmente activo en Akash Console")
            print("2. Busca la URL exacta en la sección 'Endpoints' del Console")
            print("3. Algunos despliegues pueden tardar unos minutos en estar disponibles")
            return []
    
    def test_omega_functionality(self, base_url):
        """Probar funcionalidad específica de OMEGA"""
        print(f"\n🧪 PROBANDO FUNCIONALIDAD OMEGA EN: {base_url}")
        print("=" * 50)
        
        omega_endpoints = [
            "/",
            "/health", 
            "/info",
            "/predict",
            "/predict/advanced",
            "/api/predict",
            "/api/health"
        ]
        
        working_endpoints = []
        
        for endpoint in omega_endpoints:
            url, data = self.test_connection(base_url, endpoint)
            if url:
                working_endpoints.append({
                    'endpoint': endpoint,
                    'url': url,
                    'response': data
                })
        
        if working_endpoints:
            print(f"\n✅ OMEGA FUNCIONAL - {len(working_endpoints)} endpoints disponibles:")
            for ep in working_endpoints:
                print(f"  • {ep['endpoint']} -> ✅")
        
        return working_endpoints

def main():
    connector = OmegaAkashConnector()
    
    # Buscar endpoints activos
    active_endpoints = connector.find_active_endpoint()
    
    if active_endpoints:
        # Probar funcionalidad OMEGA en el primer endpoint encontrado
        base_url = active_endpoints[0]['url'].split('/health')[0].split('/info')[0].split('/predict')[0]
        omega_endpoints = connector.test_omega_functionality(base_url)
        
        print("\n🎯 RESUMEN FINAL:")
        print("=" * 40)
        print(f"✅ Base URL: {base_url}")
        print(f"🔑 API Key: {connector.api_key}")
        print(f"📊 DSEQ: {connector.dseq}")
        
        if omega_endpoints:
            print("📋 Endpoints disponibles:")
            for ep in omega_endpoints:
                print(f"  • {ep['endpoint']}")
        
        # Guardar configuración
        config = {
            'base_url': base_url,
            'api_key': connector.api_key,
            'dseq': connector.dseq,
            'active_endpoints': [ep['endpoint'] for ep in omega_endpoints],
            'timestamp': datetime.now().isoformat()
        }
        
        with open('akash_omega_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n💾 Configuración guardada en: akash_omega_config.json")
    else:
        print("\n❌ No se pudo conectar al despliegue OMEGA")
        print("📋 Verifica la URL exacta en Akash Console")

if __name__ == "__main__":
    main()