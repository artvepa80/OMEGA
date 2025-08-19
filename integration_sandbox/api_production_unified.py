#!/usr/bin/env python3
"""
OMEGA AI Production API - Unified Endpoint
Consolidates all API functionality into single production interface
Based on Agent Expert recommendations
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import os
from datetime import datetime, date
from typing import Optional, Dict, Any
import logging
import time
import json
from pathlib import Path

# Import specialized components
from omega_scheduler import KabalaScheduler
from health_check import HealthChecker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api_production.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)

class OmegaAPIResponse:
    """Unified API response format"""
    
    def __init__(self, success: bool, data: Any = None, error: str = None, message: str = None):
        self.success = success
        self.data = data
        self.error = error
        self.message = message
        
    def to_dict(self) -> Dict[str, Any]:
        response = {
            "success": self.success,
            "timestamp": datetime.now().isoformat(),
            "version": "10.1",
            "system": "OMEGA AI Unified"
        }
        
        if self.data is not None:
            response["data"] = self.data
        if self.error:
            response["error"] = self.error
        if self.message:
            response["message"] = self.message
            
        return response

class SystemHealthMonitor:
    """Comprehensive system health monitoring"""
    
    def __init__(self):
        self.components = {
            'database': self._check_database,
            'ml_models': self._check_models,
            'scheduler': self._check_scheduler,
            'file_system': self._check_files
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {}
        for component, check_func in self.components.items():
            try:
                status[component] = check_func()
            except Exception as e:
                status[component] = {
                    "status": "unhealthy", 
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        return status
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database accessibility"""
        try:
            db_path = Path("results/omega_optimization.db")
            if db_path.exists():
                return {
                    "status": "healthy",
                    "size_mb": round(db_path.stat().st_size / 1024 / 1024, 2),
                    "last_modified": datetime.fromtimestamp(db_path.stat().st_mtime).isoformat()
                }
            else:
                return {"status": "warning", "message": "Database file not found"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def _check_models(self) -> Dict[str, Any]:
        """Check ML models availability"""
        try:
            models_dir = Path("models")
            modules_dir = Path("modules")
            
            model_files = list(models_dir.glob("*.pkl")) if models_dir.exists() else []
            module_files = list(modules_dir.glob("*.py")) if modules_dir.exists() else []
            
            return {
                "status": "healthy",
                "model_files": len(model_files),
                "module_files": len(module_files),
                "directories_accessible": models_dir.exists() and modules_dir.exists()
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def _check_scheduler(self) -> Dict[str, Any]:
        """Check scheduler functionality"""
        try:
            from omega_scheduler import KabalaScheduler
            scheduler = KabalaScheduler()
            proximo = scheduler.get_sorteo_especifico()
            
            return {
                "status": "healthy",
                "next_sorteo": {
                    "fecha": proximo.fecha.strftime("%Y-%m-%d"),
                    "dia": proximo.dia_semana,
                    "tiempo_restante": proximo.tiempo_restante
                }
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def _check_files(self) -> Dict[str, Any]:
        """Check critical files"""
        critical_files = [
            "main.py",
            "omega_scheduler.py", 
            "data/historial_kabala_github.csv"
        ]
        
        file_status = {}
        for file_path in critical_files:
            path = Path(file_path)
            file_status[file_path] = {
                "exists": path.exists(),
                "size_kb": round(path.stat().st_size / 1024, 2) if path.exists() else 0
            }
        
        all_exist = all(status["exists"] for status in file_status.values())
        
        return {
            "status": "healthy" if all_exist else "warning",
            "files": file_status
        }

# Initialize components
app = FastAPI(
    title="🎯 OMEGA AI Production API",
    description="Sistema unificado de predicción AI para sorteos Kabala - Endpoint de Producción",
    version="10.1",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("ENVIRONMENT") == "development" else [
        "https://omega-ai-prod.railway.app",
        "https://omega-ai.vercel.app",
        "https://omega-ai-staging.railway.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"]
)

# Initialize services
scheduler = KabalaScheduler()
health_monitor = SystemHealthMonitor()

# Middleware for request logging
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"📥 {request.method} {request.url.path} - {request.client.host}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"📤 {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response

# Authentication dependency (optional)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials and os.getenv("REQUIRE_AUTH", "false").lower() == "true":
        raise HTTPException(status_code=401, detail="Authentication required")
    return credentials

# Root endpoint
@app.get("/")
async def root():
    """Endpoint principal con información del sistema unificado"""
    try:
        proximo_sorteo = scheduler.get_sorteo_especifico()
        
        response_data = {
            "sistema": "OMEGA AI Production v10.1",
            "descripcion": "Sistema unificado de predicción AI para sorteos Kabala",
            "loteria": {
                "nombre": "Kabala",
                "dias_sorteo": "Martes, Jueves y Sábados",
                "hora_sorteo": "21:30 (Perú)",
                "proximo_sorteo": {
                    "fecha": proximo_sorteo.fecha.strftime("%Y-%m-%d"),
                    "dia": proximo_sorteo.dia_semana,
                    "fecha_legible": scheduler._formatear_fecha_legible(proximo_sorteo.fecha),
                    "tiempo_restante": proximo_sorteo.tiempo_restante,
                    "numero_sorteo": proximo_sorteo.numero_sorteo
                }
            },
            "endpoints": {
                "prediccion": {
                    "GET /predict": "Predicción para próximo sorteo",
                    "GET /predict/{fecha}": "Predicción para fecha específica",
                    "POST /predict": "Predicción con parámetros personalizados"
                },
                "informacion": {
                    "GET /sorteos": "Próximos sorteos Kabala",
                    "GET /sorteo/hoy": "Información de sorteo de hoy",
                    "GET /status": "Estado detallado del sistema"
                },
                "salud": {
                    "GET /health": "Health check básico",
                    "GET /health/detailed": "Health check detallado"
                }
            },
            "ambiente": os.getenv("ENVIRONMENT", "unknown")
        }
        
        return OmegaAPIResponse(
            success=True,
            data=response_data,
            message="OMEGA AI Production API - Sistema Operativo"
        ).to_dict()
        
    except Exception as e:
        logger.error(f"❌ Error in root endpoint: {e}")
        return OmegaAPIResponse(
            success=False,
            error=str(e),
            message="Error obteniendo información del sistema"
        ).to_dict()

# Health endpoints
@app.get("/health")
async def health_check():
    """Health check básico para balanceadores de carga"""
    try:
        proximo = scheduler.get_sorteo_especifico()
        
        return OmegaAPIResponse(
            success=True,
            data={
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "10.1",
                "environment": os.getenv("ENVIRONMENT", "unknown"),
                "next_sorteo": {
                    "fecha": proximo.fecha.strftime("%Y-%m-%d"),
                    "dia": proximo.dia_semana,
                    "tiempo_restante": proximo.tiempo_restante
                }
            }
        ).to_dict()
        
    except Exception as e:
        return OmegaAPIResponse(
            success=False,
            error=str(e)
        ).to_dict()

@app.get("/health/detailed")
async def detailed_health_check():
    """Health check detallado para monitoreo"""
    try:
        system_status = health_monitor.get_system_status()
        
        # Calculate overall health
        component_statuses = [
            component.get("status", "unhealthy") 
            for component in system_status.values()
        ]
        
        healthy_count = sum(1 for status in component_statuses if status == "healthy")
        overall_status = "healthy" if healthy_count == len(component_statuses) else \
                        "degraded" if healthy_count > 0 else "unhealthy"
        
        integration_score = (healthy_count / len(component_statuses)) * 100
        
        return OmegaAPIResponse(
            success=True,
            data={
                "overall_status": overall_status,
                "integration_score": round(integration_score, 1),
                "components": system_status,
                "timestamp": datetime.now().isoformat(),
                "version": "10.1"
            }
        ).to_dict()
        
    except Exception as e:
        logger.error(f"❌ Detailed health check failed: {e}")
        return OmegaAPIResponse(
            success=False,
            error=str(e)
        ).to_dict()

# Prediction endpoints
@app.get("/predict")
@app.post("/predict")
async def predict_kabala(
    background_tasks: BackgroundTasks,
    fecha: Optional[str] = Query(None, description="Fecha específica (YYYY-MM-DD)"),
    user = Depends(get_current_user)
):
    """
    Predicción principal unificada para sorteos Kabala
    Consolidates functionality from all previous API endpoints
    """
    try:
        logger.info(f"🎯 Generating Kabala prediction for fecha: {fecha or 'next sorteo'}")
        
        # Get prediction using unified scheduler
        result = scheduler.get_prediction_for_api(fecha)
        
        if not result.get('success', False):
            raise HTTPException(status_code=500, detail=result.get('error', 'Error desconocido'))
        
        # Unified response format
        response_data = {
            "loteria": "Kabala",
            "sorteo_info": result['sorteo'],
            "mensaje": result['mensaje'],
            "recordatorio": result['recordatorio'],
            "predicciones": result['predicciones'][:8],  # Top 8
            "estadisticas": {
                "total_combinaciones": result.get('total_combinaciones', 0),
                "predicciones_mostradas": min(8, len(result.get('predicciones', []))),
                "confianza_promedio": round(
                    sum(p.get('confidence', 0) for p in result.get('predicciones', [])[:8]) / 
                    min(8, len(result.get('predicciones', []))), 3
                ) if result.get('predicciones') else 0
            },
            "metadata": {
                "generado_en": result['generado'],
                "sistema": "OMEGA AI Production v10.1",
                "modelos_utilizados": ["LSTM", "Transformer", "Ensemble", "Neural Enhanced"],
                "endpoint": "unified_production_api"
            }
        }
        
        logger.info(f"✅ Prediction generated successfully for {result['sorteo']['dia']} {result['sorteo']['fecha_legible']}")
        
        return OmegaAPIResponse(
            success=True,
            data=response_data,
            message="Predicción generada exitosamente"
        ).to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating prediction: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno del servidor: {str(e)}"
        )

@app.get("/predict/{fecha}")
async def predict_fecha_especifica(
    fecha: str,
    background_tasks: BackgroundTasks,
    user = Depends(get_current_user)
):
    """Predicción para fecha específica con validaciones"""
    try:
        # Validate date format
        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Formato de fecha inválido. Use YYYY-MM-DD"
            )
        
        # Validate it's a Kabala day
        dia_semana = fecha_obj.weekday()
        if dia_semana not in [1, 3, 5]:  # Tuesday, Thursday, Saturday
            nombres_dias = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}
            raise HTTPException(
                status_code=400,
                detail=f"La fecha {fecha} ({nombres_dias[dia_semana]}) no es día de sorteo Kabala. Los sorteos son Martes, Jueves y Sábados."
            )
        
        # Generate prediction using the main predict endpoint
        return await predict_kabala(background_tasks, fecha=fecha, user=user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in specific date prediction {fecha}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Information endpoints
@app.get("/sorteos")
async def proximos_sorteos(
    cantidad: int = Query(5, ge=1, le=10, description="Cantidad de sorteos (1-10)")
):
    """Información de próximos sorteos"""
    try:
        sorteos = scheduler.get_proximos_sorteos(cantidad)
        
        response_data = {
            "loteria": "Kabala",
            "informacion": "Martes, Jueves y Sábados a las 21:30 (Lima, Perú)",
            "proximos_sorteos": [
                {
                    "fecha": sorteo.fecha.strftime("%Y-%m-%d"),
                    "dia_semana": sorteo.dia_semana,
                    "fecha_legible": scheduler._formatear_fecha_legible(sorteo.fecha),
                    "numero_sorteo": sorteo.numero_sorteo,
                    "tiempo_restante": sorteo.tiempo_restante,
                    "es_hoy": sorteo.es_hoy,
                    "es_proximo": sorteo.es_proximo
                }
                for sorteo in sorteos
            ],
            "total_sorteos": len(sorteos)
        }
        
        return OmegaAPIResponse(
            success=True,
            data=response_data
        ).to_dict()
        
    except Exception as e:
        logger.error(f"❌ Error getting sorteos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sorteo/hoy")
async def sorteo_hoy():
    """Verificar si hay sorteo hoy"""
    try:
        hoy = date.today()
        dia_semana = hoy.weekday()
        
        if dia_semana in [1, 3, 5]:  # Kabala days
            sorteo_info = scheduler.get_sorteo_especifico(hoy.strftime("%Y-%m-%d"))
            nombres_dias = {1: "Martes", 3: "Jueves", 5: "Sábado"}
            
            response_data = {
                "hay_sorteo_hoy": True,
                "fecha": hoy.strftime("%Y-%m-%d"),
                "dia": nombres_dias[dia_semana],
                "fecha_legible": scheduler._formatear_fecha_legible(hoy),
                "numero_sorteo": sorteo_info.numero_sorteo,
                "tiempo_restante": sorteo_info.tiempo_restante,
                "hora_sorteo": "21:30",
                "mensaje": f"🎯 ¡Hoy {nombres_dias[dia_semana]} hay sorteo Kabala a las 21:30!"
            }
        else:
            proximo = scheduler.get_sorteo_especifico()
            response_data = {
                "hay_sorteo_hoy": False,
                "mensaje": "Hoy no hay sorteo Kabala",
                "proximo_sorteo": {
                    "fecha": proximo.fecha.strftime("%Y-%m-%d"),
                    "dia": proximo.dia_semana,
                    "fecha_legible": scheduler._formatear_fecha_legible(proximo.fecha),
                    "tiempo_restante": proximo.tiempo_restante
                }
            }
        
        return OmegaAPIResponse(
            success=True,
            data=response_data
        ).to_dict()
            
    except Exception as e:
        logger.error(f"❌ Error checking today's sorteo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def system_status():
    """Estado completo del sistema"""
    try:
        import psutil
        system_status = health_monitor.get_system_status()
        proximo_sorteo = scheduler.get_sorteo_especifico()
        
        response_data = {
            "sistema": {
                "cpu_percent": psutil.cpu_percent() if 'psutil' in globals() else 0,
                "memory_percent": psutil.virtual_memory().percent if 'psutil' in globals() else 0,
                "environment": os.getenv("ENVIRONMENT", "unknown"),
                "version": "10.1",
                "uptime": "N/A"  # Would need process start time tracking
            },
            "kabala": {
                "proximo_sorteo": proximo_sorteo.fecha.strftime("%Y-%m-%d"),
                "dia": proximo_sorteo.dia_semana,
                "tiempo_restante": proximo_sorteo.tiempo_restante,
                "numero_sorteo": proximo_sorteo.numero_sorteo
            },
            "componentes": system_status,
            "scheduler": {
                "configurado": True,
                "timezone": "America/Lima",
                "dias_automaticos": ["Martes", "Jueves", "Sábado"],
                "hora_prediccion": "10:00 AM"
            }
        }
        
        return OmegaAPIResponse(
            success=True,
            data=response_data
        ).to_dict()
        
    except Exception as e:
        logger.error(f"❌ Error getting system status: {e}")
        return OmegaAPIResponse(
            success=False,
            error=str(e)
        ).to_dict()

# Admin endpoints
@app.post("/admin/setup-cron")
async def setup_cron(
    admin_key: str = Query(..., description="Clave de administrador"),
    user = Depends(get_current_user)
):
    """Setup del cron del sistema"""
    if admin_key != os.getenv("ADMIN_KEY", "omega_admin_2025"):
        raise HTTPException(status_code=403, detail="Clave de administrador inválida")
    
    try:
        success = scheduler.setup_system_cron()
        
        response_data = {
            "cron_configurado": success,
            "schedule": "Martes, Jueves, Sábados a las 10:00 AM",
            "timezone": "America/Lima",
            "comando_manual": "python omega_scheduler.py --setup-cron"
        }
        
        return OmegaAPIResponse(
            success=success,
            data=response_data,
            message="Cron configurado exitosamente" if success else "Error configurando cron"
        ).to_dict()
            
    except Exception as e:
        logger.error(f"❌ Error setup cron: {e}")
        raise HTTPException(status_code=500, detail=f"Error setup cron: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    
    # Startup information
    print("🎯 OMEGA AI Production API - Unified System")
    print("=" * 60)
    print("🗓️  Lotería: Kabala (Martes, Jueves, Sábados)")
    print("🕘 Hora sorteo: 21:30 (Lima, Perú)")
    print("🤖 Sistema: OMEGA AI v10.1 Production")
    print("🔗 API: Endpoint Unificado")
    print("🌐 Puerto:", port)
    
    # Show next sorteo
    try:
        scheduler_info = KabalaScheduler()
        proximo = scheduler_info.get_sorteo_especifico()
        print(f"📅 Próximo sorteo: {proximo.dia_semana} {scheduler_info._formatear_fecha_legible(proximo.fecha)}")
        print(f"⏰ Tiempo restante: {proximo.tiempo_restante}")
    except Exception as e:
        print(f"⚠️  Error mostrando próximo sorteo: {e}")
    
    print("=" * 60)
    
    # Run server
    if os.getenv("ENVIRONMENT") == "production":
        uvicorn.run(
            "api_production_unified:app",
            host=host,
            port=port,
            workers=int(os.getenv("WORKERS", 2)),
            log_level="info",
            access_log=True
        )
    else:
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=True,
            log_level="info"
        )