#!/usr/bin/env python3
"""
AWS ECS Deployment Testing Script for OMEGA AI
Tests all endpoints and validates deployment health
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional

class OmegaECSValidator:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'OMEGA-ECS-Validator/1.0'
        })
    
    def test_health_endpoint(self) -> bool:
        """Test the health endpoint"""
        print("🔍 Testing health endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ Health endpoint responding")
                health_data = response.json()
                print(f"   Status: {health_data.get('status', 'unknown')}")
                print(f"   Version: {health_data.get('version', 'unknown')}")
                return True
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health endpoint error: {str(e)}")
            return False
    
    def test_predict_endpoint(self, predictions: int = 5) -> bool:
        """Test the prediction endpoint"""
        print(f"🔮 Testing prediction endpoint ({predictions} predictions)...")
        try:
            payload = {
                "predictions": predictions,
                "ai_combinations": 25
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/predict", 
                data=json.dumps(payload),
                timeout=30
            )
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Prediction endpoint working")
                print(f"   Response time: {end_time - start_time:.2f}s")
                print(f"   Predictions received: {len(data.get('predictions', []))}")
                
                # Show first prediction
                if data.get('predictions'):
                    first_pred = data['predictions'][0]
                    numbers = first_pred.get('numbers', [])
                    score = first_pred.get('score', 0)
                    print(f"   Sample: {numbers} (Score: {score:.3f})")
                
                return True
            else:
                print(f"❌ Prediction endpoint failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Prediction endpoint error: {str(e)}")
            return False
    
    def test_load_balancer_health(self) -> bool:
        """Test load balancer health and response times"""
        print("⚡ Testing load balancer performance...")
        
        response_times = []
        success_count = 0
        total_requests = 5
        
        for i in range(total_requests):
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}/health", timeout=5)
                end_time = time.time()
                
                if response.status_code == 200:
                    success_count += 1
                    response_times.append(end_time - start_time)
                
                print(f"   Request {i+1}: {end_time - start_time:.3f}s")
                time.sleep(1)
                
            except Exception as e:
                print(f"   Request {i+1}: Failed - {str(e)}")
        
        if success_count > 0:
            avg_time = sum(response_times) / len(response_times)
            print(f"✅ Load balancer health: {success_count}/{total_requests} requests successful")
            print(f"   Average response time: {avg_time:.3f}s")
            return success_count >= total_requests * 0.8  # 80% success rate
        else:
            print("❌ Load balancer health: All requests failed")
            return False
    
    def run_full_validation(self) -> bool:
        """Run complete validation suite"""
        print(f"🚀 Starting OMEGA AI ECS Validation")
        print(f"   Target URL: {self.base_url}")
        print("=" * 50)
        
        tests = [
            ("Health Check", self.test_health_endpoint),
            ("Load Balancer Performance", self.test_load_balancer_health),
            ("Prediction API", lambda: self.test_predict_endpoint(3)),
            ("High Volume Test", lambda: self.test_predict_endpoint(10))
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            print("-" * 30)
            
            try:
                result = test_func()
                if result:
                    passed_tests += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {str(e)}")
        
        print("\n" + "=" * 50)
        print(f"📊 VALIDATION SUMMARY")
        print(f"   Tests passed: {passed_tests}/{total_tests}")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - Deployment is healthy!")
            return True
        elif passed_tests >= total_tests * 0.75:
            print("⚠️  MOSTLY WORKING - Minor issues detected")
            return True
        else:
            print("❌ DEPLOYMENT ISSUES - Requires attention")
            return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 test-deployment.py <load_balancer_url>")
        print("Example: python3 test-deployment.py http://omega-alb-123456789.us-east-1.elb.amazonaws.com")
        sys.exit(1)
    
    base_url = sys.argv[1]
    validator = OmegaECSValidator(base_url)
    
    # Wait for load balancer to be ready
    print("⏱️  Waiting for load balancer to be ready...")
    max_retries = 12
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Load balancer is ready!")
                break
        except:
            pass
        
        if attempt < max_retries - 1:
            print(f"   Attempt {attempt + 1}/{max_retries} - waiting 10 seconds...")
            time.sleep(10)
    else:
        print("⚠️  Load balancer not responding, but continuing with tests...")
    
    # Run validation
    success = validator.run_full_validation()
    
    if success:
        print("\n🚀 OMEGA AI is successfully deployed on AWS ECS!")
        print("\nNext steps:")
        print("- Integrate with your applications")
        print("- Set up monitoring and alerting")
        print("- Configure auto-scaling if needed")
    else:
        print("\n🔧 Deployment needs attention. Check ECS logs:")
        print("aws logs tail /ecs/omega-pro-ai --follow")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()