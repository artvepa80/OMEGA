#!/usr/bin/env python3
"""
API ultra-simple para Railway - garantizada para funcionar
"""
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ===== CONFIGURACIÓN =====
PORT = int(os.getenv("PORT", 8000))
print(f"🚀 Starting OMEGA API on port {PORT}")

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

@app.get("/predictions")
def get_predictions():
    return {
        "predictions": [
            {"id": "1", "numbers": [7, 14, 21, 28, 35, 42], "confidence": 0.85},
            {"id": "2", "numbers": [3, 12, 19, 26, 33, 40], "confidence": 0.78}
        ],
        "message": "Simple predictions working"
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
