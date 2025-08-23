#!/usr/bin/env python3
"""
OMEGA PRO AI v10.1 - API Tester
Prueba la funcionalidad de OMEGA una vez tengas la URL exacta
"""

import requests
import json
from datetime import datetime

def test_omega_api(base_url, api_key=None):
    """
    Probar la API de OMEGA con la URL correcta
    """
    print("🚀 OMEGA PRO AI v10.1 - API Test Suite")
    print("=" * 50)
    print(f"🌐 Base URL: {base_url}")
    print(f"🔑 API Key: {api_key[:20] + '...' if api_key else 'None'}")
    print(f"⏰ Test Time: {datetime.now().isoformat()}")
    print("=" * 50)
    
    headers = {
        'User-Agent': 'OMEGA-API-Test/1.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    
    # Test endpoints típicos de OMEGA
    test_cases = [
        {
            'name': 'Health Check',
            'method': 'GET',
            'endpoint': '/health',
            'expected': 'JSON with status'
        },
        {
            'name': 'Root Info',
            'method': 'GET', 
            'endpoint': '/',
            'expected': 'App information'
        },
        {
            'name': 'App Info',
            'method': 'GET',
            'endpoint': '/info',
            'expected': 'Technical details'
        },
        {
            'name': 'Basic Prediction',
            'method': 'POST',
            'endpoint': '/predict',
            'expected': 'Lottery prediction'
        },
        {
            'name': 'Advanced Prediction',
            'method': 'POST',
            'endpoint': '/predict/advanced',
            'expected': 'Advanced prediction with patterns'
        }
    ]
    
    results = []
    
    for test in test_cases:
        print(f"\n🧪 Testing: {test['name']}")
        print(f"   {test['method']} {base_url}{test['endpoint']}")
        
        try:
            if test['method'] == 'GET':
                response = requests.get(f"{base_url}{test['endpoint']}", 
                                      headers=headers, timeout=15)
            else:  # POST
                response = requests.post(f"{base_url}{test['endpoint']}", 
                                       headers=headers, json={}, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ SUCCESS - {response.status_code}")
                    print(f"   📋 Response: {json.dumps(data, indent=6)[:200]}...")
                    results.append({
                        'test': test['name'],
                        'status': 'SUCCESS',
                        'code': response.status_code,
                        'data': data
                    })
                except:
                    print(f"   ✅ SUCCESS - {response.status_code} (TEXT)")
                    print(f"   📋 Response: {response.text[:200]}...")
                    results.append({
                        'test': test['name'],
                        'status': 'SUCCESS',
                        'code': response.status_code,
                        'data': response.text
                    })
            else:
                print(f"   ❌ ERROR - {response.status_code}")
                print(f"   📋 Response: {response.text[:100]}")
                results.append({
                    'test': test['name'],
                    'status': 'ERROR',
                    'code': response.status_code,
                    'error': response.text
                })
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ TIMEOUT")
            results.append({
                'test': test['name'],
                'status': 'TIMEOUT',
                'code': None,
                'error': 'Request timeout'
            })
        except Exception as e:
            print(f"   💥 EXCEPTION: {e}")
            results.append({
                'test': test['name'],
                'status': 'EXCEPTION',
                'code': None,
                'error': str(e)
            })
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    success_count = len([r for r in results if r['status'] == 'SUCCESS'])
    total_count = len(results)
    
    print(f"✅ Successful tests: {success_count}/{total_count}")
    print(f"📈 Success rate: {(success_count/total_count)*100:.1f}%")
    
    if success_count > 0:
        print(f"\n🎉 ¡OMEGA está funcionando en Akash!")
        print(f"🌐 URL de acceso: {base_url}")
        
        # Encontrar endpoints funcionales
        working_endpoints = [r for r in results if r['status'] == 'SUCCESS']
        print(f"\n📋 Endpoints disponibles:")
        for r in working_endpoints:
            endpoint = [t['endpoint'] for t in test_cases if t['name'] == r['test']][0]
            print(f"   • {endpoint} - {r['test']}")
    
    # Guardar resultados
    report = {
        'base_url': base_url,
        'api_key_used': bool(api_key),
        'test_results': results,
        'summary': {
            'total_tests': total_count,
            'successful_tests': success_count,
            'success_rate': (success_count/total_count)*100
        },
        'timestamp': datetime.now().isoformat()
    }
    
    with open('omega_api_test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Reporte guardado en: omega_api_test_report.json")
    
    return results

def main():
    print("🔧 OMEGA API Tester")
    print("Proporciona la URL exacta de tu despliegue Akash")
    print("\nEjemplo de uso:")
    print("python3 test_omega_api.py")
    print("Cuando se ejecute, pega la URL del Console de Akash")
    
    # URL de ejemplo - reemplazar con la real
    example_url = "https://tu-url-exacta-de-akash.com"
    api_key = "ac.sk.production.a16cbf***c4cad7"
    
    print(f"\n⚠️  INSTRUCCIONES:")
    print(f"1. Ve a tu Console de Akash")
    print(f"2. Busca la sección 'Endpoints' o 'URLs'")
    print(f"3. Copia la URL exacta")
    print(f"4. Ejecuta: test_omega_api('URL_COPIADA', '{api_key}')")
    
    return example_url, api_key

if __name__ == "__main__":
    main()