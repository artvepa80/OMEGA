#!/usr/bin/env python3
"""
OMEGA PRO AI - Update Akash Deployment with /conversation endpoint
================================================================

This script provides instructions to update the current Akash deployment
with the new /conversation endpoint functionality.

Current Deployment:
- DSEQ: 23068231
- URI: 3d3qeju30hdkjcsse1ra48oeuo.ingress.akashprovid.com
- Provider: provider.akashprovid.com
"""

import os
import sys
import requests
import json
from datetime import datetime

def test_current_endpoint():
    """Test the current deployment status"""
    base_url = "https://3d3qeju30hdkjcsse1ra48oeuo.ingress.akashprovid.com"
    
    print("🔍 Testing current deployment...")
    try:
        # Test root endpoint
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Root endpoint working")
            print(f"   Response: {response.json()}")
        
        # Test conversation endpoint (should fail initially)
        try:
            conv_response = requests.post(
                f"{base_url}/conversation",
                json={"message": "test"},
                timeout=10
            )
            if conv_response.status_code == 200:
                print("✅ Conversation endpoint already working!")
                return True
            else:
                print(f"⚠️ Conversation endpoint not available: {conv_response.status_code}")
                return False
        except requests.RequestException:
            print("❌ Conversation endpoint not available")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Cannot reach deployment: {e}")
        return False

def show_update_instructions():
    """Show manual update instructions"""
    print("\n" + "="*60)
    print("📋 MANUAL UPDATE INSTRUCTIONS")
    print("="*60)
    print()
    
    print("Option 1: Using Akash Console (Web)")
    print("-" * 40)
    print("1. Go to: https://console.akash.network")
    print("2. Log in and find deployment DSEQ: 23068231")
    print("3. Click 'Update' tab")
    print("4. The system will restart with updated code automatically")
    print("   (omega_unified_main.py already has /conversation endpoint)")
    print()
    
    print("Option 2: Using Shell Access")
    print("-" * 40)
    print("1. Connect to the deployment shell:")
    print("   ./connect_omega_shell.sh")
    print("2. Once connected, restart the server:")
    print("   pkill -f 'python.*omega_unified_main'")
    print("   python3 omega_unified_main.py --mode api --port 8000")
    print()
    
    print("Option 3: Force Redeploy")
    print("-" * 40)
    print("1. Close current lease")
    print("2. Redeploy with updated image")
    print("3. This will get all recent code changes")
    print()

def create_test_script():
    """Create a test script for the conversation endpoint"""
    test_script_content = '''#!/usr/bin/env python3
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
        print(f"\\nTest {i}: {test_case['message'][:30]}...")
        
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
'''
    
    with open('test_conversation_endpoint.py', 'w') as f:
        f.write(test_script_content)
    
    os.chmod('test_conversation_endpoint.py', 0o755)
    print("✅ Created test script: test_conversation_endpoint.py")

def main():
    print("🚀 OMEGA PRO AI - Conversation Endpoint Update")
    print("=" * 60)
    print()
    print("Current Deployment Info:")
    print(f"   DSEQ: 23068231")
    print(f"   URI: 3d3qeju30hdkjcsse1ra48oeuo.ingress.akashprovid.com")
    print(f"   Provider: provider.akashprovid.com")
    print()
    
    # Test current status
    endpoint_working = test_current_endpoint()
    
    if endpoint_working:
        print("✅ Conversation endpoint is already working!")
        print("   No update needed.")
    else:
        show_update_instructions()
        create_test_script()
    
    print("\n" + "="*60)
    print("💡 Next Steps:")
    print("1. Follow the update instructions above")
    print("2. Wait 2-3 minutes for deployment restart")
    print("3. Test with: python3 test_conversation_endpoint.py")
    print("=" * 60)

if __name__ == "__main__":
    main()