#!/usr/bin/env python3
"""
🔮 OMEGA PRO AI v10.1 - Test Script
Test OMEGA cuando esté listo en Akash
"""

import requests
import json
import time

OMEGA_URL = "http://crfvkrkp5pbab34elothkbqi94.ingress.bdl.computer"

def test_omega_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{OMEGA_URL}/health", timeout=10)
        return response.status_code == 200, response.text
    except Exception as e:
        return False, str(e)

def test_omega_predictions():
    """Test predictions endpoint"""
    try:
        data = {
            "game_type": "kabala",
            "quantity": 5
        }
        response = requests.post(f"{OMEGA_URL}/predict", json=data, timeout=30)
        return response.status_code == 200, response.json()
    except Exception as e:
        return False, str(e)

def main():
    print("🔮 OMEGA PRO AI v10.1 - Test Suite")
    print(f"🌐 URL: {OMEGA_URL}")
    print("=" * 50)
    
    # Test Health
    print("\n💚 Testing Health Endpoint...")
    health_ok, health_result = test_omega_health()
    
    if health_ok:
        print("✅ Health: OK")
        print(f"📄 Response: {health_result}")
        
        # Test Predictions
        print("\n🔮 Testing Predictions...")
        pred_ok, pred_result = test_omega_predictions()
        
        if pred_ok:
            print("✅ Predictions: OK")
            print("🎯 Sample Prediction:")
            print(json.dumps(pred_result, indent=2))
            print("\n🎉 OMEGA IS FULLY OPERATIONAL!")
            print("🚀 Tu sistema está listo para usar desde Akash!")
        else:
            print("❌ Predictions: Error")
            print(f"📄 Error: {pred_result}")
    else:
        print("❌ Health: Not ready")
        print(f"📄 Status: {health_result}")
        print("⏰ System still initializing...")

if __name__ == "__main__":
    main()