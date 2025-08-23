#!/usr/bin/env python3
"""
API ultra-simple para Railway - garantizada para funcionar
"""
import os
print("🔧 Importing FastAPI...")
from fastapi import FastAPI
print("🔧 Importing CORS...")
from fastapi.middleware.cors import CORSMiddleware
print("🔧 Importing uvicorn...")
import uvicorn

print("🔧 Setting up configuration...")
# ===== CONFIGURACIÓN =====
PORT = int(os.getenv("PORT", 8000))
print(f"🚀 Starting OMEGA API on port {PORT}")
print(f"🌍 Environment PORT: {os.getenv('PORT', 'Not set')}")

# ===== FASTAPI APP =====
app = FastAPI(
    title="OMEGA API Simple",
    version="1.0.0-simple"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== ENDPOINTS =====

@app.get("/")
def root():
    return {
        "message": "🚀 OMEGA API - Simple Version",
        "status": "running",
        "port": PORT
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "port": PORT,
        "message": "API is running correctly"
    }

@app.get("/status")
def status():
    return {
        "ok": True,
        "status": {
            "system_version": "OMEGA Simple",
            "current_mode": "simple",
            "port": PORT,
            "message": "All systems operational"
        }
    }

@app.post("/auth/login")
def login(username: str = "omega_admin", password: str = "omega_2024"):
    if username == "omega_admin" and password == "omega_2024":
        return {
            "access_token": "simple_token_123",
            "token_type": "bearer",
            "message": "Login successful"
        }
    return {"error": "Invalid credentials"}

@app.post("/predictions")
def predictions():
    return {
        "predictions": [
            {"combination": [8,15,18,19,35,37], "score": 0.947, "svi_score": 0.877, "source": "omega_ensemble"},
            {"combination": [3,23,28,31,35,37], "score": 0.931, "svi_score": 0.853, "source": "omega_ensemble"},
            {"combination": [2,15,21,27,34,36], "score": 0.909, "svi_score": 0.848, "source": "omega_ensemble"},
            {"combination": [6,7,11,16,22,34], "score": 0.904, "svi_score": 0.815, "source": "omega_ensemble"},
            {"combination": [17,18,23,36,39,40], "score": 0.89, "svi_score": 0.76, "source": "omega_ensemble"},
            {"combination": [5,8,9,15,37,39], "score": 0.815, "svi_score": 0.741, "source": "omega_ensemble"},
            {"combination": [1,7,13,16,21,38], "score": 0.699, "svi_score": 0.727, "source": "omega_ensemble"},
            {"combination": [6,11,21,31,35,40], "score": 0.687, "svi_score": 0.689, "source": "omega_ensemble"}
        ],
        "status": "success",
        "count": 8
    }

# ===== STARTUP =====
if __name__ == "__main__":
    print(f"🔗 Health check: http://0.0.0.0:{PORT}/health")
    print(f"📊 Status: http://0.0.0.0:{PORT}/status")
    
    uvicorn.run(
        "api_simple:app",
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )
