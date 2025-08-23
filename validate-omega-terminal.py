#!/usr/bin/env python3
"""
OMEGA Terminal Validation Script
Tests all endpoints and validates real prediction execution
"""

import requests
import json
import time
import sys
from datetime import datetime

def validate_omega_terminal(base_url):
    """Comprehensive validation of OMEGA Terminal Server"""
    
    print("🔍 OMEGA Terminal Server Validation")
    print("=" * 60)
    print(f"🌐 Testing URL: {base_url}")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    results = {
        "url": base_url,
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    # Test 1: Health Check
    print("\n🔄 Test 1: Health Check")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Health check passed")
            print(f"   Service: {health_data.get('service', 'N/A')}")
            print(f"   Platform: {health_data.get('platform', 'N/A')}")
            print(f"   Uptime: {health_data.get('uptime', 'N/A')}")
            print(f"   Endpoints: {health_data.get('endpoints', [])}")
            results["tests"]["health"] = {"status": "pass", "data": health_data}
        else:
            print(f"❌ Health check failed: HTTP {response.status_code}")
            results["tests"]["health"] = {"status": "fail", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        results["tests"]["health"] = {"status": "error", "error": str(e)}
    
    # Test 2: Web Interface
    print("\n🔄 Test 2: Web Interface")
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200 and "OMEGA Terminal" in response.text:
            print("✅ Web interface accessible")
            print("   Contains terminal interface with buttons")
            results["tests"]["web_interface"] = {"status": "pass"}
        else:
            print(f"❌ Web interface issue: HTTP {response.status_code}")
            results["tests"]["web_interface"] = {"status": "fail", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        print(f"❌ Web interface error: {str(e)}")
        results["tests"]["web_interface"] = {"status": "error", "error": str(e)}
    
    # Test 3: Execute Endpoint
    print("\n🔄 Test 3: Execute Endpoint (Basic Command)")
    try:
        payload = {
            "command": "python3 -c 'print(\"Hello from Akash\")'",
            "timeout": 30
        }
        response = requests.post(f"{base_url}/execute", json=payload, timeout=45)
        if response.status_code == 200:
            result = response.json()
            print("✅ Execute endpoint working")
            print(f"   Return code: {result.get('return_code', 'N/A')}")
            print(f"   Output: {result.get('stdout', '').strip()[:100]}")
            results["tests"]["execute_basic"] = {"status": "pass", "data": result}
        else:
            print(f"❌ Execute endpoint failed: HTTP {response.status_code}")
            results["tests"]["execute_basic"] = {"status": "fail", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        print(f"❌ Execute endpoint error: {str(e)}")
        results["tests"]["execute_basic"] = {"status": "error", "error": str(e)}
    
    # Test 4: Predict Endpoint (Fast Test)
    print("\n🔄 Test 4: Predict Endpoint (Fast Test)")
    try:
        payload = {
            "predictions": 3,
            "ai_combinations": 5,
            "timeout": 60
        }
        
        start_time = time.time()
        response = requests.post(f"{base_url}/predict", json=payload, timeout=90)
        execution_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Predict endpoint working")
            print(f"   Execution time: {execution_time:.2f}s")
            print(f"   Predictions generated: {len(result.get('predictions', []))}")
            print(f"   Status: {result.get('status', 'N/A')}")
            
            # Show first prediction
            if result.get('predictions'):
                first_pred = result['predictions'][0]
                numbers_str = ' - '.join([f"{n:02d}" for n in first_pred.get('numbers', [])])
                print(f"   Sample: [{numbers_str}] ({first_pred.get('confidence', 'N/A')})")
            
            results["tests"]["predict_fast"] = {
                "status": "pass", 
                "data": result,
                "execution_time": execution_time
            }
        else:
            print(f"❌ Predict endpoint failed: HTTP {response.status_code}")
            results["tests"]["predict_fast"] = {"status": "fail", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        print(f"❌ Predict endpoint error: {str(e)}")
        results["tests"]["predict_fast"] = {"status": "error", "error": str(e)}
    
    # Test 5: Full Main.py Execution (if basic tests pass)
    basic_tests_passed = all(
        results["tests"].get(test, {}).get("status") == "pass" 
        for test in ["health", "execute_basic"]
    )
    
    if basic_tests_passed:
        print("\n🔄 Test 5: Full main.py Execution")
        try:
            payload = {
                "command": "python3 main.py --data-info",
                "timeout": 120
            }
            
            start_time = time.time()
            response = requests.post(f"{base_url}/execute", json=payload, timeout=150)
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Full main.py execution working")
                print(f"   Execution time: {execution_time:.2f}s")
                print(f"   Return code: {result.get('return_code', 'N/A')}")
                
                stdout = result.get('stdout', '')
                if stdout and len(stdout) > 100:
                    print(f"   Output preview: {stdout[:200]}...")
                else:
                    print(f"   Output: {stdout}")
                
                results["tests"]["main_execution"] = {
                    "status": "pass", 
                    "data": result,
                    "execution_time": execution_time
                }
            else:
                print(f"❌ Main.py execution failed: HTTP {response.status_code}")
                results["tests"]["main_execution"] = {"status": "fail", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Main.py execution error: {str(e)}")
            results["tests"]["main_execution"] = {"status": "error", "error": str(e)}
    else:
        print("\n⏭️  Test 5: Skipped (basic tests failed)")
        results["tests"]["main_execution"] = {"status": "skipped", "reason": "basic tests failed"}
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    total_tests = len(results["tests"])
    passed_tests = sum(1 for test in results["tests"].values() if test.get("status") == "pass")
    failed_tests = sum(1 for test in results["tests"].values() if test.get("status") == "fail")
    error_tests = sum(1 for test in results["tests"].values() if test.get("status") == "error")
    skipped_tests = sum(1 for test in results["tests"].values() if test.get("status") == "skipped")
    
    print(f"✅ Passed: {passed_tests}/{total_tests}")
    print(f"❌ Failed: {failed_tests}/{total_tests}")
    print(f"⚠️  Errors: {error_tests}/{total_tests}")
    print(f"⏭️  Skipped: {skipped_tests}/{total_tests}")
    
    if passed_tests == total_tests - skipped_tests:
        print("\n🎉 ALL TESTS PASSED! OMEGA Terminal is fully functional")
        print("🚀 Ready for production predictions")
        overall_status = "success"
    elif passed_tests >= 3:  # Health, web, execute basic
        print("\n⚠️  PARTIAL SUCCESS - Core functionality working")
        print("💡 Some advanced features may need attention")
        overall_status = "partial"
    else:
        print("\n❌ VALIDATION FAILED - Critical issues found")
        print("🔧 Review deployment configuration")
        overall_status = "failed"
    
    results["summary"] = {
        "overall_status": overall_status,
        "total_tests": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "errors": error_tests,
        "skipped": skipped_tests
    }
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"omega_terminal_validation_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved: {results_file}")
    
    return overall_status == "success"

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 validate-omega-terminal.py <URL>")
        print("Example: python3 validate-omega-terminal.py https://your-akash-url.com")
        sys.exit(1)
    
    url = sys.argv[1].rstrip('/')
    success = validate_omega_terminal(url)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()