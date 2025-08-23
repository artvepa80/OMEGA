#!/usr/bin/env python3
"""
🚀 OMEGA Pro AI - API Principal Mejorada
FastAPI con documentación completa, validación y seguridad
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Security, status, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field, validator
import uvicorn
import jwt
from passlib.context import CryptContext

from src.core.orchestrator import OmegaOrchestrator
from src.utils.logger_factory import LoggerFactory
from src.monitoring.metrics_collector import MetricsCollector, track_metrics

# Configuración
API_VERSION = "v1"
API_TITLE = "OMEGA Pro AI API"
API_DESCRIPTION = """
🎯 **OMEGA Pro AI - Advanced Lottery Prediction System API**

Sistema avanzado de predicción de lotería usando múltiples modelos de IA.

## Características Principales

- **🧠 Múltiples Modelos de IA**: Neural Networks, LSTM, Transformers, Algoritmos Genéticos
- **📊 Análisis Avanzado**: SVI scoring, pattern recognition, ensemble learning
- **🔄 Aprendizaje Adaptativo**: El sistema aprende de resultados reales
- **⚡ Performance Optimizado**: Lazy loading, caché, procesamiento paralelo
- **📈 Monitoreo Completo**: Métricas detalladas y logging estructurado

## Autenticación

La API utiliza JWT tokens para autenticación. Obtén un token usando el endpoint `/auth/login`.

## Rate Limiting

- **Predicciones**: Máximo 100 requests por hora
- **Consultas generales**: Máximo 1000 requests por hora
- **Health checks**: Sin límite

## Ejemplos de Uso

```python
import requests

# Autenticación
auth_response = requests.post("/api/v1/auth/login", json={
    "username": "omega_user",
    "password": "secure_password"
})
token = auth_response.json()["access_token"]

# Generar predicciones
headers = {"Authorization": f"Bearer {token}"}
prediction_response = requests.post("/api/v1/predictions/generate", 
    json={"count": 8, "models": ["neural_enhanced", "lstm_v2"]},
    headers=headers
)
```
"""

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "omega-super-secret-key-change-in-production")
ALGORITHM = "HS256"

# Global components
logger = LoggerFactory.get_logger("OmegaAPI")
metrics = MetricsCollector()
orchestrator = None

# Pydantic Models
class LoginRequest(BaseModel):
    """Request de login"""
    username: str = Field(..., description="Nombre de usuario")
    password: str = Field(..., description="Contraseña")

class TokenResponse(BaseModel):
    """Response de token"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(..., description="Tiempo de expiración en segundos")

class PredictionRequest(BaseModel):
    """Request para generar predicciones"""
    count: int = Field(8, ge=1, le=50, description="Número de predicciones a generar")
    models: Optional[List[str]] = Field(None, description="Modelos específicos a usar")
    enable_learning: bool = Field(True, description="Activar aprendizaje adaptativo")
    svi_profile: str = Field("default", description="Perfil SVI (default, conservative, aggressive)")
    
    @validator('svi_profile')
    def validate_svi_profile(cls, v):
        valid_profiles = {"default", "conservative", "aggressive", "neural_optimized"}
        if v not in valid_profiles:
            raise ValueError(f"Perfil SVI debe ser uno de: {valid_profiles}")
        return v

class PredictionResult(BaseModel):
    """Resultado de predicción individual"""
    combination: List[int] = Field(..., description="Combinación de 6 números")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza del modelo")
    svi_score: float = Field(..., ge=0.0, le=1.0, description="Score de viabilidad SVI")
    source_model: str = Field(..., description="Modelo que generó la predicción")
    final_score: float = Field(..., ge=0.0, le=1.0, description="Score final combinado")

class PredictionResponse(BaseModel):
    """Response de predicciones"""
    session_id: str = Field(..., description="ID de sesión")
    predictions: List[PredictionResult] = Field(..., description="Lista de predicciones")
    generation_time: float = Field(..., description="Tiempo de generación en segundos")
    models_used: List[str] = Field(..., description="Modelos utilizados")
    metadata: Dict[str, Any] = Field(..., description="Metadata adicional")

class LearningRequest(BaseModel):
    """Request para aprendizaje desde resultado oficial"""
    official_result: List[int] = Field(..., description="Resultado oficial del sorteo")
    date: str = Field(..., description="Fecha del sorteo (YYYY-MM-DD)")
    
    @validator('official_result')
    def validate_result(cls, v):
        if len(v) != 6:
            raise ValueError("El resultado debe tener exactamente 6 números")
        if not all(1 <= n <= 40 for n in v):
            raise ValueError("Los números deben estar entre 1 y 40")
        if len(set(v)) != 6:
            raise ValueError("No puede haber números duplicados")
        return sorted(v)

class SystemStatus(BaseModel):
    """Estado del sistema"""
    status: str = Field(..., description="Estado general (healthy, degraded, unhealthy)")
    uptime_seconds: float = Field(..., description="Tiempo activo en segundos")
    version: str = Field(..., description="Versión de la API")
    models_active: int = Field(..., description="Número de modelos activos")
    memory_usage_mb: float = Field(..., description="Uso de memoria en MB")
    cpu_usage_percent: float = Field(..., description="Uso de CPU en porcentaje")

# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida de la aplicación"""
    global orchestrator
    
    # Startup
    logger.info("🚀 Iniciando OMEGA Pro AI API")
    orchestrator = OmegaOrchestrator()
    
    yield
    
    # Shutdown
    logger.info("🔄 Cerrando OMEGA Pro AI API")
    if orchestrator:
        await orchestrator.shutdown_gracefully()
    metrics.stop()

# FastAPI App
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version="10.1.0",
    openapi_url=f"/api/{API_VERSION}/openapi.json",
    docs_url=f"/api/{API_VERSION}/docs",
    redoc_url=f"/api/{API_VERSION}/redoc",
    lifespan=lifespan,
    contact={
        "name": "OMEGA Pro AI Support",
        "email": "support@omega-ai.com",
        "url": "https://omega-ai.com/support"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Custom middleware para métricas
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware para tracking de métricas"""
    start_time = datetime.now()
    
    # Incrementar requests
    metrics.increment("api_requests_total", labels={
        "method": request.method,
        "endpoint": request.url.path
    })
    
    # Procesar request
    response = await call_next(request)
    
    # Calcular duración
    duration = (datetime.now() - start_time).total_seconds()
    metrics.record_histogram("api_request_duration_seconds", duration, labels={
        "method": request.method,
        "endpoint": request.url.path,
        "status_code": str(response.status_code)
    })
    
    return response

# Authentication functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verifica JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo validar token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# API Endpoints

@app.get("/", 
         summary="Root endpoint",
         description="Información básica de la API")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "🎯 OMEGA Pro AI - Advanced Lottery Prediction System",
        "version": "10.1.0",
        "api_version": API_VERSION,
        "docs_url": f"/api/{API_VERSION}/docs",
        "status": "active",
        "features": [
            "Multi-model AI predictions",
            "Adaptive learning",
            "SVI scoring",
            "Real-time metrics",
            "JWT authentication"
        ]
    }

@app.get("/api/v1/health", 
         response_model=SystemStatus,
         summary="Health check",
         description="Verifica el estado de salud del sistema")
@track_metrics(metrics, "health_check")
async def health_check():
    """Health check endpoint"""
    try:
        system_status = orchestrator.get_system_status()
        memory_usage = metrics.get_memory_usage()
        
        return SystemStatus(
            status="healthy" if system_status["system_health"]["orchestrator"] == "healthy" else "degraded",
            uptime_seconds=system_status["uptime_seconds"],
            version="10.1.0",
            models_active=len(system_status["active_models"]),
            memory_usage_mb=memory_usage.get("rss_mb", 0),
            cpu_usage_percent=metrics.get_gauge("system_cpu_percent") or 0
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.post("/api/v1/auth/login", 
          response_model=TokenResponse,
          summary="User authentication",
          description="Autenticar usuario y obtener JWT token")
@track_metrics(metrics, "auth_login")
async def login(request: LoginRequest):
    """Login endpoint"""
    # En producción, verificar credenciales contra base de datos
    valid_users = {
        "omega_admin": "omega_2024",
        "omega_user": "user_secure_2024"
    }
    
    if request.username not in valid_users or valid_users[request.username] != request.password:
        metrics.increment("auth_failures")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )
    
    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(
        data={"sub": request.username}, 
        expires_delta=access_token_expires
    )
    
    metrics.increment("auth_success")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds())
    )

@app.post("/api/v1/predictions/generate",
          response_model=PredictionResponse,
          summary="Generate predictions",
          description="Genera predicciones usando modelos de IA configurados")
@track_metrics(metrics, "generate_predictions")
async def generate_predictions(
    request: PredictionRequest,
    background_tasks: BackgroundTasks,
    username: str = Depends(verify_token)
):
    """Generar predicciones"""
    try:
        logger.info(f"🎯 Generando {request.count} predicciones para usuario: {username}")
        
        # Ejecutar predicciones
        results = await orchestrator.run_prediction_cycle(
            top_n=request.count,
            enable_learning=request.enable_learning
        )
        
        # Convertir a formato de respuesta
        prediction_results = []
        for pred in results['predictions']:
            prediction_results.append(PredictionResult(
                combination=pred.combination,
                confidence=pred.confidence,
                svi_score=pred.svi_score,
                source_model=pred.source_model,
                final_score=getattr(pred, 'final_score', pred.confidence)
            ))
        
        # Métricas
        metrics.increment("predictions_generated", value=len(prediction_results))
        
        # Log para auditoría
        background_tasks.add_task(
            log_prediction_audit,
            username, request.count, len(prediction_results)
        )
        
        return PredictionResponse(
            session_id=results["session_id"],
            predictions=prediction_results,
            generation_time=results["metrics"]["cycle_time"],
            models_used=results["metrics"]["models_used"],
            metadata=results["metrics"]
        )
        
    except Exception as e:
        logger.error(f"❌ Error generando predicciones: {e}")
        metrics.record_error("prediction_generation_error", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error interno generando predicciones: {str(e)}"
        )

@app.post("/api/v1/learning/learn-from-result",
          summary="Learn from official result",
          description="Ejecuta aprendizaje adaptativo desde resultado oficial")
@track_metrics(metrics, "learn_from_result")
async def learn_from_result(
    request: LearningRequest,
    username: str = Depends(verify_token)
):
    """Aprendizaje desde resultado oficial"""
    try:
        logger.info(f"🧠 Iniciando aprendizaje desde resultado: {request.official_result}")
        
        learning_results = await orchestrator.run_learning_from_result(request.official_result)
        
        metrics.increment("learning_sessions_completed")
        
        return {
            "success": True,
            "learning_score": learning_results.learning_score,
            "improvements": learning_results.improvements,
            "model_adjustments": learning_results.model_adjustments,
            "message": "Aprendizaje completado exitosamente"
        }
        
    except Exception as e:
        logger.error(f"❌ Error en aprendizaje: {e}")
        metrics.record_error("learning_error", str(e))
        raise HTTPException(status_code=500, detail=f"Error en aprendizaje: {str(e)}")

@app.get("/api/v1/system/status",
         response_model=SystemStatus,
         summary="Detailed system status",
         description="Estado detallado del sistema y componentes")
async def system_status(username: str = Depends(verify_token)):
    """Estado detallado del sistema"""
    try:
        status = orchestrator.get_system_status()
        memory = metrics.get_memory_usage()
        
        return SystemStatus(
            status="healthy",
            uptime_seconds=status["uptime_seconds"],
            version="10.1.0",
            models_active=len(status["active_models"]),
            memory_usage_mb=memory.get("rss_mb", 0),
            cpu_usage_percent=metrics.get_gauge("system_cpu_percent") or 0
        )
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estado del sistema")

@app.get("/api/v1/metrics",
         summary="System metrics",
         description="Métricas detalladas del sistema")
async def get_metrics(username: str = Depends(verify_token)):
    """Obtener métricas del sistema"""
    return metrics.get_summary()

@app.get("/api/v1/metrics/prometheus",
         summary="Prometheus metrics",
         description="Métricas en formato Prometheus")
async def get_prometheus_metrics():
    """Métricas en formato Prometheus"""
    return metrics.export_metrics("prometheus")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Manejo personalizado de excepciones HTTP"""
    metrics.increment("api_errors", labels={
        "status_code": str(exc.status_code),
        "endpoint": request.url.path
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Manejo de excepciones generales"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    metrics.record_error("unhandled_exception", str(exc))
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Error interno del servidor",
            "status_code": 500,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    )

# Background tasks
async def log_prediction_audit(username: str, requested: int, generated: int):
    """Log de auditoría para predicciones"""
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "generate_predictions",
        "username": username,
        "requested_count": requested,
        "generated_count": generated,
        "success": generated > 0
    }
    
    logger.info("📋 Prediction audit", extra={"context": audit_entry})

# Custom OpenAPI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=API_TITLE,
        version="10.1.0",
        description=API_DESCRIPTION,
        routes=app.routes,
    )
    
    # Agregar información de seguridad
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Startup
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"🚀 Iniciando OMEGA Pro AI API en puerto {port}")
    
    uvicorn.run(
        "src.api.main_api:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
        reload=False  # True solo para desarrollo
    )