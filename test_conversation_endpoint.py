#!/usr/bin/env python3
"""
Test script for OMEGA /conversation endpoint
"""
import requests
import json

def test_conversation_endpoint():
    base_url = "https://3d3qeju30hdkjcsse1ra48oeuo.ingress.akashprovid.com"
    
    # Test cases
    test_cases = [
        {
            "message": "Hola, necesito predicciones para hoy",
            "include_predictions": True
        },
        {
            "message": "¿Cuál es tu algoritmo más efectivo?",
            "include_predictions": False
        },
        {
            "message": "Genera 5 combinaciones para la Kabala",
            "include_predictions": True
        }
    ]
    
    print("🧪 Testing OMEGA /conversation endpoint")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['message'][:30]}...")
        
        try:
            response = requests.post(
                f"{base_url}/conversation",
                json=test_case,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Success!")
                print(f"   Response: {result.get('response', '')[:100]}...")
                
                if test_case.get('include_predictions'):
                    predictions_count = result.get('predictions_count', 0)
                    print(f"   Predictions included: {predictions_count}")
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_conversation_endpoint()
