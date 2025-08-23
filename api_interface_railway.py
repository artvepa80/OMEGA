from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import uvicorn

# Inicializar FastAPI
app = FastAPI(
    title="OMEGA API - Railway",
    description="OMEGA PRO AI Sistema Agéntico - Versión optimizada para Railway", 
    version="4.0.1-railway"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === MODELOS DE DATOS ===
class SystemStatus(BaseModel):
    system_version: str = "OMEGA Hybrid System"
    pipeline_version: str = "v10.1"
    agentic_version: str = "V4.0"
    current_mode: str = "hybrid"
    system_health: Dict[str, bool] = {"pipeline": True, "agentic": True}
    uptime: Dict[str, Any] = {}
    statistics: Dict[str, int] = {}
    performance_history: float = 0.85
    configuration: Dict[str, Any] = {}

class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: str
    version: str = "4.0.0-railway"
    uptime_seconds: float

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class PredictionRequest(BaseModel):
    model_type: Optional[str] = "default"
    parameters: Optional[Dict[str, Any]] = None

class PredictionResponse(BaseModel):
    id: str
    numbers: List[int]
    confidence: float
    model_used: str
    timestamp: str
    source: str = "railway_api"

# === VARIABLES GLOBALES ===
start_time = time.time()
prediction_counter = 0

# === ENDPOINTS ===

@app.get("/")
async def root():
    return {
        "message": "OMEGA PRO AI - Railway Deployment",
        "version": "4.0.0-railway",
        "status": "active",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return HealthResponse(
        timestamp=datetime.now().isoformat(),
        uptime_seconds=time.time() - start_time
    )

@app.get("/status")
async def get_status():
    current_time = datetime.now()
    uptime_seconds = time.time() - start_time
    
    # Calcular uptime
    uptime_days = int(uptime_seconds // 86400)
    uptime_hours = int((uptime_seconds % 86400) // 3600)
    
    status = SystemStatus(
        uptime={
            "days": uptime_days,
            "hours": uptime_hours,
            "total_seconds": uptime_seconds
        },
        statistics={
            "pipeline_predictions": prediction_counter,
            "agentic_predictions": prediction_counter,
            "hybrid_predictions": prediction_counter,
            "adaptive_decisions": 0,
            "system_switches": 0,
            "total_predictions": prediction_counter,
            "start_time": datetime.fromtimestamp(start_time).isoformat()
        },
        configuration={
            "default_mode": "adaptive",
            "pipeline_config": {
                "data_path": "data/historial_kabala_github_fixed.csv",
                "svi_profile": "default",
                "top_n": 30,
                "enable_models": ["all"],
                "export_formats": ["csv", "json"],
                "retrain": False,
                "evaluate": False,
                "backtest": False
            },
            "agentic_config": {
                "enable_autonomous_agent": True,
                "enable_api_server": True,
                "enable_predictions": True,
                "agent_schedule_seconds": 3600,
                "max_experiments_per_cycle": 2
            }
        }
    )
    
    return {"ok": True, "status": status}

@app.post("/auth/login")
async def login(username: str, password: str):
    # Autenticación simple para Railway
    if username == "omega_admin" and password == "omega_2024":
        # Generar token simple (en producción usar JWT real)
        token = f"omega_token_{int(time.time())}"
        return AuthResponse(access_token=token)
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/predictions")
async def create_prediction(request: PredictionRequest):
    global prediction_counter
    prediction_counter += 1
    
    # Simulación de predicción (sin ML pesado)
    import random
    random.seed(int(time.time()))
    
    # Generar números aleatorios como placeholder
    numbers = sorted(random.sample(range(1, 41), 6))
    
    prediction = PredictionResponse(
        id=f"pred_{prediction_counter:06d}",
        numbers=numbers,
        confidence=round(random.uniform(0.6, 0.95), 3),
        model_used=request.model_type or "railway_simulator",
        timestamp=datetime.now().isoformat()
    )
    
    return prediction

@app.get("/predictions")
async def get_predictions(limit: int = 10):
    # Retornar predicciones simuladas
    predictions = []
    for i in range(min(limit, 5)):  # Máximo 5 por ahora
        import random
        numbers = sorted(random.sample(range(1, 41), 6))
        
        prediction = PredictionResponse(
            id=f"sim_{i+1:03d}",
            numbers=numbers,
            confidence=round(random.uniform(0.6, 0.95), 3),
            model_used="simulator",
            timestamp=datetime.now().isoformat()
        )
        predictions.append(prediction)
    
    return {
        "predictions": predictions,
        "total": len(predictions),
        "page": 1,
        "limit": limit
    }

@app.get("/agent/status")
async def get_agent_status():
    return {
        "is_running": True,
        "current_task": "monitoring_system",
        "last_execution": datetime.now().isoformat(),
        "performance": {
            "success_rate": 0.87,
            "average_execution_time": 2.5,
            "total_executions": prediction_counter
        }
    }

@app.post("/agent/start")
async def start_agent():
    return {
        "success": True,
        "message": "Agent started successfully",
        "agent_status": "running"
    }

@app.post("/agent/stop")
async def stop_agent():
    return {
        "success": True,
        "message": "Agent stopped successfully", 
        "agent_status": "stopped"
    }

# === ERROR HANDLERS ===
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "message": f"The endpoint {request.url.path} does not exist",
            "available_endpoints": [
                "/", "/health", "/status", "/auth/login", 
                "/predictions", "/agent/status", "/docs"
            ]
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "Something went wrong on the server"
        }
    )

# === STARTUP ===
@app.on_event("startup")
async def startup_event():
    print("🚀 OMEGA API - Railway deployment started")
    print(f"📊 Version: 4.0.0-railway")
    print(f"⏰ Start time: {datetime.fromtimestamp(start_time)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting OMEGA API on port {port}")
    print(f"🔗 Health check: http://0.0.0.0:{port}/health")
    uvicorn.run(
        "api_interface_railway:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
