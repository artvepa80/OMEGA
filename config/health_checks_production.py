#!/usr/bin/env python3
"""
OMEGA PRO AI v10.1 - Production Health Checks
Comprehensive health monitoring system for production deployment
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict

import aiohttp
import asyncio
import redis
import psutil
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("omega-health-checks")

@dataclass
class HealthStatus:
    """Health status data structure"""
    service: str
    status: str
    timestamp: str
    response_time_ms: float
    details: Dict = None
    error: Optional[str] = None

class HealthCheckManager:
    """Comprehensive health check management system"""
    
    def __init__(self):
        self.checks = {}
        self.history = []
        self.thresholds = {
            'response_time_ms': 5000,  # 5 seconds
            'cpu_percent': 80,
            'memory_percent': 85,
            'disk_percent': 90
        }
    
    async def register_check(self, name: str, check_func, interval: int = 30):
        """Register a health check"""
        self.checks[name] = {
            'function': check_func,
            'interval': interval,
            'last_check': None,
            'status': 'unknown'
        }
    
    async def check_api_health(self, url: str = "http://localhost:8000") -> HealthStatus:
        """Check API endpoint health"""
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/health", timeout=10) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        return HealthStatus(
                            service="api",
                            status="healthy",
                            timestamp=datetime.utcnow().isoformat(),
                            response_time_ms=response_time,
                            details=data
                        )
                    else:
                        return HealthStatus(
                            service="api",
                            status="unhealthy",
                            timestamp=datetime.utcnow().isoformat(),
                            response_time_ms=response_time,
                            error=f"HTTP {response.status}"
                        )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthStatus(
                service="api",
                status="error",
                timestamp=datetime.utcnow().isoformat(),
                response_time_ms=response_time,
                error=str(e)
            )
    
    async def check_redis_health(self, redis_url: str = "redis://localhost:6379") -> HealthStatus:
        """Check Redis connection health"""
        start_time = time.time()
        try:
            r = redis.from_url(redis_url, decode_responses=True)
            
            # Test basic operations
            test_key = f"health_check_{int(time.time())}"
            r.set(test_key, "test_value", ex=10)
            value = r.get(test_key)
            r.delete(test_key)
            
            response_time = (time.time() - start_time) * 1000
            
            if value == "test_value":
                info = r.info()
                return HealthStatus(
                    service="redis",
                    status="healthy",
                    timestamp=datetime.utcnow().isoformat(),
                    response_time_ms=response_time,
                    details={
                        "connected_clients": info.get("connected_clients", 0),
                        "used_memory_human": info.get("used_memory_human", "0B"),
                        "redis_version": info.get("redis_version", "unknown")
                    }
                )
            else:
                return HealthStatus(
                    service="redis",
                    status="unhealthy",
                    timestamp=datetime.utcnow().isoformat(),
                    response_time_ms=response_time,
                    error="Redis test operation failed"
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthStatus(
                service="redis",
                status="error",
                timestamp=datetime.utcnow().isoformat(),
                response_time_ms=response_time,
                error=str(e)
            )
    
    async def check_system_health(self) -> HealthStatus:
        """Check system resource health"""
        start_time = time.time()
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Network stats
            network = psutil.net_io_counters()
            
            # Load average (Unix only)
            try:
                load_avg = os.getloadavg()
            except AttributeError:
                load_avg = [0, 0, 0]  # Windows doesn't have load average
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine status based on thresholds
            status = "healthy"
            issues = []
            
            if cpu_percent > self.thresholds['cpu_percent']:
                status = "warning"
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            if memory_percent > self.thresholds['memory_percent']:
                status = "warning" if status == "healthy" else "critical"
                issues.append(f"High memory usage: {memory_percent:.1f}%")
            
            if disk_percent > self.thresholds['disk_percent']:
                status = "critical"
                issues.append(f"High disk usage: {disk_percent:.1f}%")
            
            return HealthStatus(
                service="system",
                status=status,
                timestamp=datetime.utcnow().isoformat(),
                response_time_ms=response_time,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_percent": disk_percent,
                    "disk_free_gb": round(disk.free / (1024**3), 2),
                    "load_average": load_avg,
                    "network_bytes_sent": network.bytes_sent,
                    "network_bytes_recv": network.bytes_recv,
                    "uptime_seconds": time.time() - psutil.boot_time()
                },
                error="; ".join(issues) if issues else None
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthStatus(
                service="system",
                status="error",
                timestamp=datetime.utcnow().isoformat(),
                response_time_ms=response_time,
                error=str(e)
            )
    
    async def check_ml_models_health(self) -> HealthStatus:
        """Check ML models availability and health"""
        start_time = time.time()
        try:
            # Check if models directory exists
            models_path = "/app/models"
            if not os.path.exists(models_path):
                models_path = "./models"
            
            model_files = []
            if os.path.exists(models_path):
                for file in os.listdir(models_path):
                    if file.endswith(('.pth', '.pkl', '.joblib', '.h5')):
                        file_path = os.path.join(models_path, file)
                        file_size = os.path.getsize(file_path)
                        model_files.append({
                            "name": file,
                            "size_mb": round(file_size / (1024*1024), 2),
                            "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                        })
            
            # Test model imports
            import_status = {}
            try:
                import torch
                import_status["torch"] = torch.__version__
            except ImportError as e:
                import_status["torch"] = f"Error: {e}"
            
            try:
                import tensorflow as tf
                import_status["tensorflow"] = tf.__version__
            except ImportError as e:
                import_status["tensorflow"] = f"Error: {e}"
            
            try:
                import sklearn
                import_status["sklearn"] = sklearn.__version__
            except ImportError as e:
                import_status["sklearn"] = f"Error: {e}"
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthStatus(
                service="ml_models",
                status="healthy" if model_files else "warning",
                timestamp=datetime.utcnow().isoformat(),
                response_time_ms=response_time,
                details={
                    "model_files_count": len(model_files),
                    "model_files": model_files[:5],  # Limit to first 5
                    "ml_libraries": import_status
                },
                error=None if model_files else "No model files found"
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthStatus(
                service="ml_models",
                status="error",
                timestamp=datetime.utcnow().isoformat(),
                response_time_ms=response_time,
                error=str(e)
            )
    
    async def run_all_checks(self) -> Dict[str, HealthStatus]:
        """Run all health checks"""
        results = {}
        
        # Run checks concurrently
        tasks = [
            ("api", self.check_api_health()),
            ("redis", self.check_redis_health()),
            ("system", self.check_system_health()),
            ("ml_models", self.check_ml_models_health())
        ]
        
        completed_tasks = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
        
        for i, (name, _) in enumerate(tasks):
            result = completed_tasks[i]
            if isinstance(result, Exception):
                results[name] = HealthStatus(
                    service=name,
                    status="error",
                    timestamp=datetime.utcnow().isoformat(),
                    response_time_ms=0,
                    error=str(result)
                )
            else:
                results[name] = result
        
        return results
    
    def get_overall_status(self, results: Dict[str, HealthStatus]) -> str:
        """Determine overall system status"""
        statuses = [result.status for result in results.values()]
        
        if "error" in statuses or "critical" in statuses:
            return "unhealthy"
        elif "warning" in statuses:
            return "degraded"
        elif all(status == "healthy" for status in statuses):
            return "healthy"
        else:
            return "unknown"

# FastAPI health check endpoints
health_manager = HealthCheckManager()

async def health_check_endpoint():
    """Main health check endpoint"""
    try:
        results = await health_manager.run_all_checks()
        overall_status = health_manager.get_overall_status(results)
        
        response = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "10.1",
            "environment": os.getenv("ENVIRONMENT", "production"),
            "checks": {name: asdict(status) for name, status in results.items()}
        }
        
        # Store in history
        health_manager.history.append(response)
        if len(health_manager.history) > 100:
            health_manager.history.pop(0)
        
        return JSONResponse(
            content=response,
            status_code=200 if overall_status in ["healthy", "degraded"] else 503
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            },
            status_code=500
        )

async def readiness_check_endpoint():
    """Kubernetes readiness probe"""
    try:
        # Basic checks for readiness
        api_status = await health_manager.check_api_health()
        
        if api_status.status == "healthy":
            return JSONResponse(
                content={
                    "status": "ready",
                    "timestamp": datetime.utcnow().isoformat()
                },
                status_code=200
            )
        else:
            return JSONResponse(
                content={
                    "status": "not_ready",
                    "timestamp": datetime.utcnow().isoformat(),
                    "reason": api_status.error or "API not healthy"
                },
                status_code=503
            )
            
    except Exception as e:
        logger.error(f"Readiness check error: {e}")
        return JSONResponse(
            content={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            },
            status_code=503
        )

async def liveness_check_endpoint():
    """Kubernetes liveness probe"""
    try:
        # Simple liveness check
        return JSONResponse(
            content={
                "status": "alive",
                "timestamp": datetime.utcnow().isoformat(),
                "uptime": time.time() - psutil.boot_time()
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Liveness check error: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            },
            status_code=500
        )

if __name__ == "__main__":
    # Run health checks as standalone script
    async def main():
        print("🔍 Running OMEGA PRO AI v10.1 Health Checks...")
        results = await health_manager.run_all_checks()
        overall = health_manager.get_overall_status(results)
        
        print(f"\n📊 Overall Status: {overall.upper()}")
        print("-" * 50)
        
        for name, status in results.items():
            print(f"🔧 {name.upper()}: {status.status}")
            print(f"   Response Time: {status.response_time_ms:.2f}ms")
            if status.error:
                print(f"   Error: {status.error}")
            if status.details:
                for key, value in status.details.items():
                    print(f"   {key}: {value}")
            print()
        
        return 0 if overall in ["healthy", "degraded"] else 1
    
    sys.exit(asyncio.run(main()))