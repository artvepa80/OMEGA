#!/usr/bin/env python3
"""
API simplificada para testing con iOS
"""
from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os

app = FastAPI(title="OMEGA API for iOS", version="1.0.0")

# CORS para iOS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "🚀 OMEGA API - iOS Test Version",
        "status": "running",
        "port": 8000,
        "endpoints": ["/health", "/auth/login", "/status"]
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": "2025-08-10T15:45:00Z",
        "version": "iOS-test-v1.0",
        "uptime_seconds": 100
    }

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/auth/login")
async def login(username: str = Form(...), password: str = Form(...)):
    """Login endpoint para iOS"""
    print(f"🔐 Login attempt: {username}")
    
    # Validación simple
    if username == "omega_admin" and password == "omega_2024":
        return {
            "access_token": "ios_test_token_12345",
            "token_type": "bearer",
            "message": "Login successful from iOS!"
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/status")
async def status():
    return {
        "ok": True,
        "status": {
            "system_version": "4.0.0",
            "pipeline_version": "10.1",
            "agentic_version": "4.0",
            "current_mode": "hybrid",
            "system_health": {
                "pipeline": True,
                "agentic": True
            },
            "uptime": {
                "days": 0,
                "hours": 0,
                "total_seconds": 100
            },
            "statistics": {
                "pipeline_predictions": 150,
                "agentic_predictions": 75,
                "hybrid_predictions": 50,
                "adaptive_decisions": 25,
                "system_switches": 10,
                "total_predictions": 275,
                "start_time": "2025-08-10T15:00:00Z"
            },
            "performance": 0.92,
            "configuration": {
                "default_mode": "hybrid",
                "pipeline_config": {
                    "data_path": "data/",
                    "svi_profile": "custom",
                    "top_n": 10,
                    "enable_models": ["transformer", "neural"],
                    "export_formats": ["json"],
                    "retrain": True,
                    "evaluate": True,
                    "backtest": True
                },
                "agentic_config": {
                    "enable_autonomous_agent": True,
                    "enable_api_server": True,
                    "enable_predictions": True,
                    "agent_schedule_seconds": 3600,
                    "max_experiments_per_cycle": 5
                }
            }
        }
    }

if __name__ == "__main__":
    print("🚀 Starting OMEGA API for iOS testing...")
    print("🔗 Endpoints:")
    print("   - http://127.0.0.1:8001/")
    print("   - http://127.0.0.1:8001/health")
    print("   - http://127.0.0.1:8001/auth/login")
    print("   - http://127.0.0.1:8001/status")
    print("🧪 Test credentials: omega_admin / omega_2024")
    
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8001,
        log_level="info"
    )
