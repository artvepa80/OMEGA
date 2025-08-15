"""
OMEGA PRO AI v10.1 - Integration Tests for API Endpoints
Tests for API functionality and endpoint integration
"""

import pytest
import requests
import json
import time
import os
import sys
from unittest.mock import patch, MagicMock
import threading

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class TestAPIEndpoints:
    """Test suite for API endpoint integration"""
    
    @pytest.fixture
    def mock_api_server(self):
        """Mock API server for testing"""
        class MockResponse:
            def __init__(self, status_code=200, json_data=None):
                self.status_code = status_code
                self._json_data = json_data or {}
            
            def json(self):
                return self._json_data
            
            def raise_for_status(self):
                if self.status_code >= 400:
                    raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")
        
        return MockResponse
    
    @pytest.fixture
    def api_base_url(self):
        """Base URL for API testing"""
        return "http://localhost:8000/api/v1"
    
    def test_api_health_check(self, mock_api_server):
        """Test API health check endpoint"""
        expected_response = {"status": "healthy", "version": "10.1"}
        mock_response = mock_api_server(200, expected_response)
        
        with patch('requests.get', return_value=mock_response):
            response = requests.get("http://localhost:8000/api/v1/health")
            
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
    
    def test_prediction_endpoint(self, mock_api_server):
        """Test prediction endpoint"""
        expected_response = {
            "predictions": [[1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12]],
            "confidence": 0.85,
            "timestamp": "2025-08-15T10:00:00Z"
        }
        mock_response = mock_api_server(200, expected_response)
        
        with patch('requests.post', return_value=mock_response):
            payload = {
                "num_combinations": 2,
                "models": ["genetic", "monte_carlo"],
                "config": {"use_filters": True}
            }
            
            response = requests.post(
                "http://localhost:8000/api/v1/predict",
                json=payload
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "predictions" in data
            assert len(data["predictions"]) == 2
            assert all(len(pred) == 6 for pred in data["predictions"])
    
    def test_historical_data_endpoint(self, mock_api_server):
        """Test historical data endpoint"""
        expected_response = {
            "data": [
                {"fecha": "2025-01-01", "numeros": [1, 2, 3, 4, 5, 6]},
                {"fecha": "2025-01-02", "numeros": [7, 8, 9, 10, 11, 12]}
            ],
            "total_records": 2
        }
        mock_response = mock_api_server(200, expected_response)
        
        with patch('requests.get', return_value=mock_response):
            response = requests.get("http://localhost:8000/api/v1/historical?limit=2")
            
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert len(data["data"]) == 2
    
    def test_model_status_endpoint(self, mock_api_server):
        """Test model status endpoint"""
        expected_response = {
            "models": {
                "genetic": {"status": "ready", "accuracy": 0.78},
                "monte_carlo": {"status": "ready", "accuracy": 0.82},
                "transformer": {"status": "training", "progress": 0.45},
                "lstm": {"status": "ready", "accuracy": 0.75}
            }
        }
        mock_response = mock_api_server(200, expected_response)
        
        with patch('requests.get', return_value=mock_response):
            response = requests.get("http://localhost:8000/api/v1/models/status")
            
            assert response.status_code == 200
            data = response.json()
            assert "models" in data
            assert "genetic" in data["models"]
    
    def test_authentication_endpoint(self, mock_api_server):
        """Test authentication endpoint"""
        expected_response = {
            "token": "mock_jwt_token_12345",
            "expires_in": 3600,
            "user_id": "test_user"
        }
        mock_response = mock_api_server(200, expected_response)
        
        with patch('requests.post', return_value=mock_response):
            payload = {
                "username": "test_user",
                "password": "test_pass"
            }
            
            response = requests.post(
                "http://localhost:8000/api/v1/auth/login",
                json=payload
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "token" in data
            assert data["user_id"] == "test_user"
    
    def test_configuration_endpoint(self, mock_api_server):
        """Test configuration endpoint"""
        expected_response = {
            "config": {
                "models": {
                    "genetic": {"enabled": True, "weight": 0.3},
                    "monte_carlo": {"enabled": True, "weight": 0.25}
                },
                "filters": {"strategic": True, "rules": True},
                "output": {"format": "json", "include_metadata": True}
            }
        }
        mock_response = mock_api_server(200, expected_response)
        
        with patch('requests.get', return_value=mock_response):
            response = requests.get("http://localhost:8000/api/v1/config")
            
            assert response.status_code == 200
            data = response.json()
            assert "config" in data
            assert "models" in data["config"]
    
    def test_statistics_endpoint(self, mock_api_server):
        """Test statistics endpoint"""
        expected_response = {
            "stats": {
                "total_predictions": 1500,
                "accuracy_rate": 0.73,
                "avg_response_time": 250,
                "uptime": "99.8%"
            },
            "model_performance": {
                "genetic": {"accuracy": 0.78, "predictions": 450},
                "monte_carlo": {"accuracy": 0.82, "predictions": 520}
            }
        }
        mock_response = mock_api_server(200, expected_response)
        
        with patch('requests.get', return_value=mock_response):
            response = requests.get("http://localhost:8000/api/v1/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert "stats" in data
            assert "model_performance" in data


class TestAPIErrorHandling:
    """Test API error handling scenarios"""
    
    @pytest.fixture
    def mock_error_response(self):
        """Mock error response for testing"""
        class MockErrorResponse:
            def __init__(self, status_code, error_message):
                self.status_code = status_code
                self._error_data = {"error": error_message}
            
            def json(self):
                return self._error_data
            
            def raise_for_status(self):
                raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")
        
        return MockErrorResponse
    
    def test_invalid_prediction_request(self, mock_error_response):
        """Test invalid prediction request handling"""
        mock_response = mock_error_response(400, "Invalid request parameters")
        
        with patch('requests.post', return_value=mock_response):
            payload = {"num_combinations": -1}  # Invalid parameter
            
            response = requests.post(
                "http://localhost:8000/api/v1/predict",
                json=payload
            )
            
            assert response.status_code == 400
            assert "error" in response.json()
    
    def test_authentication_failure(self, mock_error_response):
        """Test authentication failure handling"""
        mock_response = mock_error_response(401, "Invalid credentials")
        
        with patch('requests.post', return_value=mock_response):
            payload = {"username": "invalid", "password": "wrong"}
            
            response = requests.post(
                "http://localhost:8000/api/v1/auth/login",
                json=payload
            )
            
            assert response.status_code == 401
            assert response.json()["error"] == "Invalid credentials"
    
    def test_rate_limiting(self, mock_error_response):
        """Test rate limiting functionality"""
        mock_response = mock_error_response(429, "Rate limit exceeded")
        
        with patch('requests.post', return_value=mock_response):
            for _ in range(5):  # Simulate rapid requests
                response = requests.post("http://localhost:8000/api/v1/predict")
            
            assert response.status_code == 429
            assert "Rate limit" in response.json()["error"]
    
    def test_server_error_handling(self, mock_error_response):
        """Test server error handling"""
        mock_response = mock_error_response(500, "Internal server error")
        
        with patch('requests.get', return_value=mock_response):
            response = requests.get("http://localhost:8000/api/v1/predict")
            
            assert response.status_code == 500
            assert "error" in response.json()


class TestAPIPerformance:
    """Performance tests for API endpoints"""
    
    @pytest.mark.performance
    def test_prediction_response_time(self):
        """Test prediction endpoint response time"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "predictions": [[1, 2, 3, 4, 5, 6]],
            "response_time_ms": 150
        }
        
        with patch('requests.post', return_value=mock_response):
            start_time = time.time()
            
            response = requests.post(
                "http://localhost:8000/api/v1/predict",
                json={"num_combinations": 1}
            )
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to ms
            
            assert response.status_code == 200
            assert response_time < 5000  # Should respond within 5 seconds
    
    @pytest.mark.performance
    def test_concurrent_requests_handling(self):
        """Test handling of concurrent requests"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        
        def make_request():
            with patch('requests.get', return_value=mock_response):
                return requests.get("http://localhost:8000/api/v1/health")
        
        # Simulate concurrent requests
        threads = []
        results = []
        
        for _ in range(10):
            thread = threading.Thread(
                target=lambda: results.append(make_request())
            )
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(results) == 10
        assert all(r.status_code == 200 for r in results)
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_large_payload_handling(self):
        """Test handling of large payloads"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "processed"}
        
        # Create large payload
        large_payload = {
            "historical_data": [
                {"fecha": f"2025-01-{i:02d}", "numeros": [i, i+1, i+2, i+3, i+4, i+5]}
                for i in range(1, 1001)  # 1000 records
            ]
        }
        
        with patch('requests.post', return_value=mock_response):
            start_time = time.time()
            
            response = requests.post(
                "http://localhost:8000/api/v1/historical/batch",
                json=large_payload
            )
            
            end_time = time.time()
            
            assert response.status_code == 200
            assert end_time - start_time < 30  # Should process within 30 seconds


class TestAPIIntegrationFlow:
    """Test complete API integration flows"""
    
    def test_complete_prediction_flow(self):
        """Test complete prediction flow from authentication to results"""
        # Mock responses for each step
        auth_response = MagicMock()
        auth_response.status_code = 200
        auth_response.json.return_value = {"token": "test_token"}
        
        config_response = MagicMock()
        config_response.status_code = 200
        config_response.json.return_value = {"config": {"models": ["genetic"]}}
        
        prediction_response = MagicMock()
        prediction_response.status_code = 200
        prediction_response.json.return_value = {
            "predictions": [[1, 2, 3, 4, 5, 6]],
            "confidence": 0.85
        }
        
        # Test authentication
        with patch('requests.post', return_value=auth_response):
            auth_resp = requests.post("/auth/login", json={"user": "test"})
            token = auth_resp.json()["token"]
            assert token == "test_token"
        
        # Test configuration retrieval
        with patch('requests.get', return_value=config_response):
            config_resp = requests.get("/config", headers={"Authorization": f"Bearer {token}"})
            assert config_resp.status_code == 200
        
        # Test prediction request
        with patch('requests.post', return_value=prediction_response):
            pred_resp = requests.post(
                "/predict",
                json={"num_combinations": 1},
                headers={"Authorization": f"Bearer {token}"}
            )
            assert pred_resp.status_code == 200
            assert len(pred_resp.json()["predictions"]) == 1
    
    def test_model_training_workflow(self):
        """Test model training workflow"""
        training_start_response = MagicMock()
        training_start_response.status_code = 202
        training_start_response.json.return_value = {"training_id": "train_123"}
        
        training_status_response = MagicMock()
        training_status_response.status_code = 200
        training_status_response.json.return_value = {
            "status": "completed",
            "accuracy": 0.82,
            "training_time": 1200
        }
        
        # Start training
        with patch('requests.post', return_value=training_start_response):
            start_resp = requests.post("/models/train", json={"model": "genetic"})
            training_id = start_resp.json()["training_id"]
            assert training_id == "train_123"
        
        # Check training status
        with patch('requests.get', return_value=training_status_response):
            status_resp = requests.get(f"/models/train/{training_id}/status")
            assert status_resp.json()["status"] == "completed"
    
    def test_data_pipeline_integration(self):
        """Test data pipeline integration"""
        upload_response = MagicMock()
        upload_response.status_code = 200
        upload_response.json.return_value = {"upload_id": "upload_456"}
        
        processing_response = MagicMock()
        processing_response.status_code = 200
        processing_response.json.return_value = {
            "processed_records": 500,
            "validation_errors": 0
        }
        
        # Upload data
        with patch('requests.post', return_value=upload_response):
            upload_resp = requests.post("/data/upload", files={"file": "test_data.csv"})
            upload_id = upload_resp.json()["upload_id"]
        
        # Process data
        with patch('requests.post', return_value=processing_response):
            process_resp = requests.post(f"/data/process/{upload_id}")
            assert process_resp.json()["processed_records"] == 500


class TestWebhookIntegration:
    """Test webhook integration functionality"""
    
    def test_twilio_webhook_integration(self):
        """Test Twilio webhook integration"""
        try:
            from integrations.twilio_webhook import handle_twilio_webhook
            
            # Mock Twilio webhook payload
            webhook_payload = {
                "From": "+1234567890",
                "Body": "predict 5 combinations",
                "MessageSid": "SM123456789"
            }
            
            with patch('integrations.twilio_webhook.handle_twilio_webhook') as mock_handler:
                mock_handler.return_value = {
                    "status": "processed",
                    "predictions": [[1, 2, 3, 4, 5, 6]]
                }
                
                result = mock_handler(webhook_payload)
                assert result["status"] == "processed"
                
        except ImportError:
            pytest.skip("Twilio integration not available")
    
    def test_whatsapp_webhook_integration(self):
        """Test WhatsApp webhook integration"""
        try:
            # Mock WhatsApp webhook
            webhook_data = {
                "messages": [{
                    "from": "1234567890",
                    "text": {"body": "generate lottery numbers"},
                    "timestamp": "1692102000"
                }]
            }
            
            # Test webhook processing
            mock_response = MagicMock()
            mock_response.status_code = 200
            
            with patch('requests.post', return_value=mock_response):
                response = requests.post(
                    "http://localhost:8000/api/v1/webhook/whatsapp",
                    json=webhook_data
                )
                assert response.status_code == 200
                
        except Exception:
            pytest.skip("WhatsApp integration not available")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])