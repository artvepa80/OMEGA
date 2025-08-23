from fastapi import FastAPI, Request, HTTPException
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
import time
import os
import hashlib
from typing import Dict, Any

class SecureMLAPI:
    def __init__(self, app: FastAPI = None):
        self.app = app or FastAPI(title="Secure ML API")
        self.api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self._setup_middleware()

    def _setup_middleware(self):
        """
        Setup API middleware for security
        """
        @self.app.middleware("http")
        async def secure_headers_middleware(request: Request, call_next):
            # Add security headers
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Content-Security-Policy"] = "default-src 'self'"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            return response

    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate API key with secure hashing
        
        Args:
            api_key (str): Input API key
        
        Returns:
            bool: Whether API key is valid
        """
        # Load API keys from secure environment or configuration
        valid_keys = os.getenv("VALID_API_KEYS", "").split(",")
        
        # Hash and compare API keys
        hashed_input_key = hashlib.sha256(api_key.encode()).hexdigest()
        return any(
            hashlib.sha256(key.encode()).hexdigest() == hashed_input_key 
            for key in valid_keys
        )

    def rate_limit_endpoint(self, endpoint: str, limit: int = 100, window: int = 3600):
        """
        Apply rate limiting to specific endpoints
        
        Args:
            endpoint (str): Endpoint to rate limit
            limit (int): Maximum requests in time window
            window (int): Time window in seconds
        """
        self.rate_limits[endpoint] = {
            "limit": limit,
            "window": window,
            "requests": {}
        }

    def check_rate_limit(self, request: Request) -> bool:
        """
        Check and enforce rate limiting
        
        Args:
            request (Request): Incoming HTTP request
        
        Returns:
            bool: Whether request is allowed
        """
        current_time = time.time()
        client_ip = request.client.host
        endpoint = request.url.path
        
        if endpoint not in self.rate_limits:
            return True
        
        rate_limit_config = self.rate_limits[endpoint]
        client_requests = rate_limit_config['requests'].get(client_ip, [])
        
        # Remove expired requests
        client_requests = [
            req_time for req_time in client_requests 
            if current_time - req_time < rate_limit_config['window']
        ]
        
        if len(client_requests) >= rate_limit_config['limit']:
            return False
        
        client_requests.append(current_time)
        rate_limit_config['requests'][client_ip] = client_requests
        
        return True

    def log_prediction(self, request: Request, prediction: Any):
        """
        Log ML model predictions for audit trail
        
        Args:
            request (Request): Incoming request
            prediction (Any): Model prediction
        """
        log_entry = {
            "timestamp": time.time(),
            "client_ip": request.client.host,
            "endpoint": request.url.path,
            "prediction_hash": hashlib.sha256(str(prediction).encode()).hexdigest()
        }
        
        # Append to secure log file
        with open("/var/log/ml_predictions.log", "a") as log_file:
            json.dump(log_entry, log_file)
            log_file.write("\n")

    def secure_ml_endpoint(self, model, validation_func=None):
        """
        Decorator to secure ML model endpoints
        
        Args:
            model: ML model to serve
            validation_func (callable): Optional input validation function
        """
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(request: Request, *args, **kwargs):
                # Validate API key
                api_key = await self.api_key_header(request)
                if not api_key or not self.validate_api_key(api_key):
                    raise HTTPException(
                        status_code=HTTP_403_FORBIDDEN, 
                        detail="Invalid or missing API key"
                    )
                
                # Check rate limit
                if not self.check_rate_limit(request):
                    raise HTTPException(
                        status_code=429, 
                        detail="Too many requests"
                    )
                
                # Validate input if function provided
                if validation_func:
                    validation_result = validation_func(*args, **kwargs)
                    if not validation_result:
                        raise HTTPException(
                            status_code=400, 
                            detail="Invalid input data"
                        )
                
                # Execute model prediction
                prediction = func(*args, **kwargs)
                
                # Log prediction
                self.log_prediction(request, prediction)
                
                return prediction
            return wrapper
        return decorator