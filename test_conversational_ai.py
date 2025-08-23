#!/usr/bin/env python3
"""
🧪 OMEGA Conversational AI System Test Suite
Comprehensive testing for production readiness
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OmegaAITester:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.api_url = "http://localhost:8000"
        self.session = None
        self.test_results = []
    
    async def setup(self):
        """Setup test session"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        logger.info("🔧 Test session initialized")
    
    async def teardown(self):
        """Cleanup test session"""
        if self.session:
            await self.session.close()
        logger.info("🧹 Test session cleaned up")
    
    async def test_health_checks(self):
        """Test all service health endpoints"""
        logger.info("🏥 Testing health checks...")
        
        health_endpoints = [
            (f"{self.base_url}/health", "Conversational AI"),
            (f"{self.api_url}/health", "OMEGA API"),
            ("http://localhost:9090/-/healthy", "Prometheus"),
            ("http://localhost:3000/api/health", "Grafana")
        ]
        
        results = []
        for endpoint, service in health_endpoints:
            try:
                async with self.session.get(endpoint) as response:
                    if response.status == 200:
                        logger.info(f"✅ {service} health check passed")
                        results.append({"service": service, "status": "healthy", "response_time": 0})
                    else:
                        logger.warning(f"⚠️  {service} health check returned {response.status}")
                        results.append({"service": service, "status": "unhealthy", "response_time": 0})
            except Exception as e:
                logger.error(f"❌ {service} health check failed: {e}")
                results.append({"service": service, "status": "failed", "error": str(e)})
        
        return results
    
    async def test_chat_functionality(self):
        """Test conversational AI chat functionality"""
        logger.info("💬 Testing chat functionality...")
        
        test_messages = [
            # Spanish tests
            {"user_id": "test_user_1", "message": "hola", "expected_intent": "greeting", "language": "es"},
            {"user_id": "test_user_1", "message": "predice numeros de loteria", "expected_intent": "lottery_prediction", "language": "es"},
            {"user_id": "test_user_1", "message": "como funciona el sistema", "expected_intent": "system_info", "language": "es"},
            {"user_id": "test_user_1", "message": "ayuda", "expected_intent": "help", "language": "es"},
            {"user_id": "test_user_1", "message": "adios", "expected_intent": "goodbye", "language": "es"},
            
            # English tests
            {"user_id": "test_user_2", "message": "hello", "expected_intent": "greeting", "language": "en"},
            {"user_id": "test_user_2", "message": "predict lottery numbers", "expected_intent": "lottery_prediction", "language": "en"},
            {"user_id": "test_user_2", "message": "system information", "expected_intent": "system_info", "language": "en"},
            {"user_id": "test_user_2", "message": "help me", "expected_intent": "help", "language": "en"},
            {"user_id": "test_user_2", "message": "goodbye", "expected_intent": "goodbye", "language": "en"},
        ]
        
        results = []
        for i, test_msg in enumerate(test_messages):
            try:
                start_time = time.time()
                
                async with self.session.post(
                    f"{self.base_url}/chat",
                    json=test_msg
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Validate response structure
                        required_fields = ["response", "intent", "confidence", "language", "session_id"]
                        missing_fields = [field for field in required_fields if field not in data]
                        
                        if missing_fields:
                            logger.error(f"❌ Test {i+1}: Missing fields {missing_fields}")
                            results.append({
                                "test": i+1,
                                "status": "failed",
                                "error": f"Missing fields: {missing_fields}",
                                "response_time": response_time
                            })
                            continue
                        
                        # Validate intent classification
                        if data["intent"] == test_msg["expected_intent"]:
                            logger.info(f"✅ Test {i+1}: Intent classification correct ({data['intent']})")
                        else:
                            logger.warning(f"⚠️  Test {i+1}: Intent mismatch. Expected: {test_msg['expected_intent']}, Got: {data['intent']}")
                        
                        # Validate language detection
                        if data["language"] == test_msg["language"]:
                            logger.info(f"✅ Test {i+1}: Language detection correct ({data['language']})")
                        else:
                            logger.warning(f"⚠️  Test {i+1}: Language mismatch. Expected: {test_msg['language']}, Got: {data['language']}")
                        
                        results.append({
                            "test": i+1,
                            "status": "passed",
                            "intent_correct": data["intent"] == test_msg["expected_intent"],
                            "language_correct": data["language"] == test_msg["language"],
                            "confidence": data["confidence"],
                            "response_time": response_time,
                            "response_length": len(data["response"])
                        })
                        
                        # Small delay between tests
                        await asyncio.sleep(1)
                        
                    else:
                        logger.error(f"❌ Test {i+1}: HTTP {response.status}")
                        results.append({
                            "test": i+1,
                            "status": "failed",
                            "error": f"HTTP {response.status}",
                            "response_time": response_time
                        })
                        
            except Exception as e:
                logger.error(f"❌ Test {i+1}: Exception - {e}")
                results.append({
                    "test": i+1,
                    "status": "failed",
                    "error": str(e),
                    "response_time": 0
                })
        
        return results
    
    async def test_whatsapp_webhook(self):
        """Test WhatsApp webhook functionality"""
        logger.info("📱 Testing WhatsApp webhook...")
        
        # Simulate Twilio webhook payload
        webhook_data = {
            "From": "whatsapp:+1234567890",
            "Body": "hola, predice numeros para hoy",
            "MessageSid": "test_message_sid"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/webhook/whatsapp",
                data=webhook_data
            ) as response:
                if response.status == 200:
                    response_text = await response.text()
                    
                    # Check if response is valid Twilio XML
                    if "<Response>" in response_text and "<Message>" in response_text:
                        logger.info("✅ WhatsApp webhook test passed")
                        return {"status": "passed", "response": response_text}
                    else:
                        logger.warning("⚠️  WhatsApp webhook returned invalid XML")
                        return {"status": "failed", "error": "Invalid XML response"}
                else:
                    logger.error(f"❌ WhatsApp webhook failed: HTTP {response.status}")
                    return {"status": "failed", "error": f"HTTP {response.status}"}
                    
        except Exception as e:
            logger.error(f"❌ WhatsApp webhook test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_api_endpoints(self):
        """Test OMEGA API endpoints"""
        logger.info("🎯 Testing OMEGA API endpoints...")
        
        endpoints = [
            ("GET", "/", "Root endpoint"),
            ("GET", "/system/info", "System info"),
            ("POST", "/predict", "Prediction endpoint", {"n_predictions": 5})
        ]
        
        results = []
        for method, endpoint, description, *args in endpoints:
            try:
                json_data = args[0] if args else None
                
                if method == "GET":
                    async with self.session.get(f"{self.api_url}{endpoint}") as response:
                        status = response.status
                        data = await response.json() if response.content_type == 'application/json' else await response.text()
                elif method == "POST":
                    async with self.session.post(f"{self.api_url}{endpoint}", json=json_data) as response:
                        status = response.status
                        data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                if status == 200:
                    logger.info(f"✅ {description} test passed")
                    results.append({"endpoint": endpoint, "status": "passed", "http_status": status})
                else:
                    logger.warning(f"⚠️  {description} returned HTTP {status}")
                    results.append({"endpoint": endpoint, "status": "warning", "http_status": status})
                    
            except Exception as e:
                logger.error(f"❌ {description} test failed: {e}")
                results.append({"endpoint": endpoint, "status": "failed", "error": str(e)})
        
        return results
    
    async def test_performance(self):
        """Test system performance under load"""
        logger.info("⚡ Testing performance...")
        
        # Concurrent chat requests
        concurrent_requests = 10
        test_message = {"user_id": "perf_test", "message": "hello"}
        
        async def make_request(session, i):
            try:
                start_time = time.time()
                async with session.post(f"{self.base_url}/chat", json={**test_message, "user_id": f"perf_test_{i}"}) as response:
                    response_time = time.time() - start_time
                    return {"request": i, "status": response.status, "response_time": response_time}
            except Exception as e:
                return {"request": i, "status": "error", "error": str(e), "response_time": 0}
        
        # Create concurrent requests
        tasks = [make_request(self.session, i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        
        # Analyze results
        successful_requests = [r for r in results if r.get("status") == 200]
        avg_response_time = sum(r["response_time"] for r in successful_requests) / len(successful_requests) if successful_requests else 0
        
        logger.info(f"✅ Performance test: {len(successful_requests)}/{concurrent_requests} requests successful")
        logger.info(f"📊 Average response time: {avg_response_time:.2f}s")
        
        return {
            "total_requests": concurrent_requests,
            "successful_requests": len(successful_requests),
            "success_rate": len(successful_requests) / concurrent_requests * 100,
            "average_response_time": avg_response_time,
            "results": results
        }
    
    async def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint"""
        logger.info("📊 Testing metrics endpoint...")
        
        try:
            async with self.session.get(f"{self.base_url}/metrics") as response:
                if response.status == 200:
                    metrics_text = await response.text()
                    
                    # Check for expected metrics
                    expected_metrics = [
                        "conversational_ai_messages_total",
                        "conversational_ai_response_time_seconds",
                        "conversational_ai_active_sessions",
                        "conversational_ai_intent_confidence"
                    ]
                    
                    found_metrics = []
                    for metric in expected_metrics:
                        if metric in metrics_text:
                            found_metrics.append(metric)
                    
                    logger.info(f"✅ Metrics endpoint: {len(found_metrics)}/{len(expected_metrics)} metrics found")
                    return {
                        "status": "passed",
                        "expected_metrics": len(expected_metrics),
                        "found_metrics": len(found_metrics),
                        "missing_metrics": list(set(expected_metrics) - set(found_metrics))
                    }
                else:
                    logger.error(f"❌ Metrics endpoint failed: HTTP {response.status}")
                    return {"status": "failed", "error": f"HTTP {response.status}"}
                    
        except Exception as e:
            logger.error(f"❌ Metrics endpoint test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def generate_report(self, all_results: Dict):
        """Generate comprehensive test report"""
        logger.info("📋 Generating test report...")
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "warnings": 0
            },
            "results": all_results
        }
        
        # Count test results
        for category, results in all_results.items():
            if isinstance(results, list):
                for result in results:
                    report["summary"]["total_tests"] += 1
                    if result.get("status") == "passed" or result.get("status") == "healthy":
                        report["summary"]["passed_tests"] += 1
                    elif result.get("status") == "failed":
                        report["summary"]["failed_tests"] += 1
                    elif result.get("status") == "warning" or result.get("status") == "unhealthy":
                        report["summary"]["warnings"] += 1
            elif isinstance(results, dict):
                report["summary"]["total_tests"] += 1
                if results.get("status") == "passed":
                    report["summary"]["passed_tests"] += 1
                elif results.get("status") == "failed":
                    report["summary"]["failed_tests"] += 1
        
        # Save report
        report_file = f"test_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("🧪 OMEGA AI SYSTEM TEST REPORT")
        print("="*60)
        print(f"📊 Total Tests: {report['summary']['total_tests']}")
        print(f"✅ Passed: {report['summary']['passed_tests']}")
        print(f"❌ Failed: {report['summary']['failed_tests']}")
        print(f"⚠️  Warnings: {report['summary']['warnings']}")
        print(f"📁 Full report saved to: {report_file}")
        print("="*60)
        
        # Return success status
        return report["summary"]["failed_tests"] == 0

async def main():
    """Run all tests"""
    tester = OmegaAITester()
    
    try:
        await tester.setup()
        
        logger.info("🚀 Starting OMEGA AI System Tests")
        
        # Run all tests
        all_results = {}
        
        all_results["health_checks"] = await tester.test_health_checks()
        all_results["chat_functionality"] = await tester.test_chat_functionality()
        all_results["whatsapp_webhook"] = await tester.test_whatsapp_webhook()
        all_results["api_endpoints"] = await tester.test_api_endpoints()
        all_results["performance"] = await tester.test_performance()
        all_results["metrics"] = await tester.test_metrics_endpoint()
        
        # Generate report
        success = tester.generate_report(all_results)
        
        if success:
            logger.info("🎉 All tests passed! System is ready for production.")
            return 0
        else:
            logger.error("❌ Some tests failed. Please review the report.")
            return 1
            
    finally:
        await tester.teardown()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)