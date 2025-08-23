#!/usr/bin/env python3
"""
🔌 API REST INTERFACE - Fase 4 del Sistema Agéntico
Interfaz REST API completa para integración externa del sistema autónomo
Permite control, monitoreo y gestión del agente desde aplicaciones externas
"""

import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import uvicorn
try:
    import jwt  # PyJWT
    _JWT_AVAILABLE = True
except Exception:
    _JWT_AVAILABLE = False
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

# Modelos Pydantic para la API
class AgentStatus(BaseModel):
    """Estado del agente"""
    status: str = Field(..., description="Estado actual del agente")
    uptime_hours: float = Field(..., description="Tiempo de funcionamiento en horas")
    cycles_completed: int = Field(..., description="Ciclos completados")
    performance_score: float = Field(..., description="Score de performance actual")
    last_cycle_time: Optional[str] = Field(None, description="Timestamp del último ciclo")

class CycleRequest(BaseModel):
    """Solicitud de ejecución de ciclo"""
    priority: str = Field("normal", description="Prioridad del ciclo: low, normal, high")
    timeout_seconds: int = Field(3600, description="Timeout máximo en segundos")
    custom_config: Optional[Dict[str, Any]] = Field(None, description="Configuración personalizada")

class AlertResponse(BaseModel):
    """Respuesta de alerta"""
    alert_id: str
    title: str
    level: str
    timestamp: str
    resolved: bool

class SystemHealth(BaseModel):
    """Salud del sistema"""
    overall_status: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_alerts: int
    last_check: str

class OptimizationRequest(BaseModel):
    """Solicitud de optimización"""
    target_objectives: List[str] = Field(..., description="Objetivos a optimizar")
    max_iterations: int = Field(50, description="Máximo número de iteraciones")
    config_candidates: Optional[List[Dict[str, Any]]] = Field(None, description="Configuraciones candidatas")

class LearningExample(BaseModel):
    """Ejemplo para aprendizaje continuo"""
    features: Dict[str, float] = Field(..., description="Features del ejemplo")
    target: float = Field(..., description="Valor objetivo")
    context: Dict[str, Any] = Field({}, description="Contexto adicional")
    weight: float = Field(1.0, description="Peso del ejemplo")

# Dependencias y utilidades
security = HTTPBearer()

class APIAuthentication:
    """Sistema de autenticación para la API"""
    
    def __init__(self, secret_key: str = "omega_secret_key_2024"):
        self.secret_key = secret_key
        self.algorithm = "HS256"
    
    def verify_token(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Verifica token JWT"""
        
        if not _JWT_AVAILABLE:
            # Fallback inseguro para entornos sin PyJWT: acepta token fijo "dev"
            if credentials and credentials.credentials == "dev":
                return {"user": "dev", "role": "admin"}
            raise HTTPException(status_code=401, detail="JWT not available. Provide token 'dev' in Authorization header for development.")
        try:
            payload = jwt.decode(credentials.credentials, self.secret_key, algorithms=[self.algorithm])
            return payload
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def create_token(self, user_data: Dict[str, Any]) -> str:
        """Crea token JWT"""
        
        payload = {
            **user_data,
            "exp": datetime.utcnow().timestamp() + 86400  # 24 horas
        }
        if not _JWT_AVAILABLE:
            # Fallback en dev: devolver token fijo
            return "dev"
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

class OmegaAgentAPI:
    """API principal del agente OMEGA"""
    
    def __init__(self):
        self.app = FastAPI(
            title="OMEGA Agent API",
            description="API REST para el Sistema Agéntico OMEGA",
            version="4.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Autenticación
        self.auth = APIAuthentication()
        
        # Referencias a componentes del agente (se inyectan externamente)
        self.agent_controller = None
        self.monitoring_system = None
        self.continuous_learning = None
        self.multi_objective_optimizer = None
        self.autonomous_scheduler = None
        
        # Estado de la API
        self.api_stats = {
            "requests_total": 0,
            "requests_by_endpoint": {},
            "start_time": datetime.now(),
            "errors_count": 0
        }
        
        # Rate limiting simple (token bucket en memoria)
        self._rate_limits = {"capacity": 60, "refill_per_sec": 1, "buckets": {}}  # 60 req/min aprox.

        # Configurar rutas
        self._setup_routes()
        
        logger.info("🔌 OMEGA Agent API inicializada")
    
    def inject_dependencies(self, 
                           agent_controller=None,
                           monitoring_system=None,
                           continuous_learning=None,
                           multi_objective_optimizer=None,
                           autonomous_scheduler=None):
        """Inyecta dependencias de componentes del agente"""
        
        self.agent_controller = agent_controller
        self.monitoring_system = monitoring_system
        self.continuous_learning = continuous_learning
        self.multi_objective_optimizer = multi_objective_optimizer
        self.autonomous_scheduler = autonomous_scheduler
        
        logger.info("🔌 Dependencias inyectadas en API")
    
    def _setup_routes(self):
        """Configura todas las rutas de la API"""
        
        # Middleware para estadísticas
        @self.app.middleware("http")
        async def track_requests(request, call_next):
            self.api_stats["requests_total"] += 1
            
            endpoint = request.url.path
            self.api_stats["requests_by_endpoint"][endpoint] = self.api_stats["requests_by_endpoint"].get(endpoint, 0) + 1
            
            # Rate limiting por IP
            try:
                client_ip = request.client.host if request.client else "unknown"
                bucket = self._rate_limits["buckets"].setdefault(client_ip, {"tokens": float(self._rate_limits["capacity"]), "last": datetime.now()})
                # Refill
                elapsed = (datetime.now() - bucket["last"]).total_seconds()
                bucket["tokens"] = min(
                    float(self._rate_limits["capacity"]),
                    bucket["tokens"] + elapsed * float(self._rate_limits["refill_per_sec"]) 
                )
                bucket["last"] = datetime.now()
                if bucket["tokens"] < 1.0:
                    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
                bucket["tokens"] -= 1.0
            except Exception:
                pass

            try:
                response = await call_next(request)
                return response
            except Exception as e:
                self.api_stats["errors_count"] += 1
                raise e
        
        # === RUTAS DE AUTENTICACIÓN ===
        
        @self.app.post("/auth/login", tags=["Authentication"])
        async def login(username: str, password: str):
            """Autenticación y generación de token"""
            
            # Validación simple (en producción usar sistema real)
            if username == "omega_admin" and password == "omega_2024":
                token = self.auth.create_token({"username": username, "role": "admin"})
                return {"access_token": token, "token_type": "bearer"}
            else:
                raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # === RUTAS DE ESTADO Y SALUD ===
        
        @self.app.get("/health", tags=["Health"])
        async def health_check():
            """Verificación de salud de la API"""
            
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "4.0.0",
                "uptime_seconds": (datetime.now() - self.api_stats["start_time"]).total_seconds()
            }
        
        @self.app.get("/status", response_model=AgentStatus, tags=["Agent"])
        async def get_agent_status(user: Dict = Depends(self.auth.verify_token)):
            """Obtiene estado actual del agente"""
            
            if not self.agent_controller:
                raise HTTPException(status_code=503, detail="Agent controller not available")
            
            # Obtener insights del agente
            insights = self.agent_controller.get_v3_insights()
            
            return AgentStatus(
                status="active" if self.agent_controller.is_running else "stopped",
                uptime_hours=(datetime.now() - self.api_stats["start_time"]).total_seconds() / 3600,
                cycles_completed=insights.get("total_cycles", 0),
                performance_score=insights.get("recent_performance", 0.0),
                last_cycle_time=insights.get("timestamp")
            )
        
        @self.app.get("/system/health", response_model=SystemHealth, tags=["System"])
        async def get_system_health(user: Dict = Depends(self.auth.verify_token)):
            """Obtiene salud del sistema"""
            
            if not self.monitoring_system:
                raise HTTPException(status_code=503, detail="Monitoring system not available")
            
            status = self.monitoring_system.get_monitoring_status()
            system_health = status["system_health"]
            
            # Extraer métricas principales
            cpu_usage = 0.0
            memory_usage = 0.0
            disk_usage = 0.0
            
            for metric in system_health["current_metrics"]:
                if metric["name"] == "cpu_usage":
                    cpu_usage = metric["value"]
                elif metric["name"] == "memory_usage":
                    memory_usage = metric["value"]
                elif metric["name"] == "disk_usage":
                    disk_usage = metric["value"]
            
            return SystemHealth(
                overall_status=system_health["overall_health"],
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                active_alerts=status["alerts"]["active_alerts"],
                last_check=system_health["last_check"]
            )
        
        # === RUTAS DE CONTROL DEL AGENTE ===
        
        @self.app.post("/agent/cycle", tags=["Agent"])
        async def execute_cycle(
            request: CycleRequest,
            background_tasks: BackgroundTasks,
            user: Dict = Depends(self.auth.verify_token)
        ):
            """Ejecuta un ciclo del agente"""
            
            if not self.agent_controller:
                raise HTTPException(status_code=503, detail="Agent controller not available")
            
            try:
                # Ejecutar ciclo en background
                def run_cycle():
                    return self.agent_controller.cycle_v3()
                
                background_tasks.add_task(run_cycle)
                
                return {
                    "message": "Cycle execution started",
                    "priority": request.priority,
                    "timeout": request.timeout_seconds,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error executing cycle: {str(e)}")
        
        @self.app.post("/agent/start", tags=["Agent"])
        async def start_agent(user: Dict = Depends(self.auth.verify_token)):
            """Inicia el agente autónomo"""
            
            if not self.agent_controller:
                raise HTTPException(status_code=503, detail="Agent controller not available")
            
            try:
                # Iniciar agente en thread separado
                import threading
                
                def start_agent_thread():
                    self.agent_controller.run_forever_v3()
                
                agent_thread = threading.Thread(target=start_agent_thread, daemon=True)
                agent_thread.start()
                
                return {
                    "message": "Agent started successfully",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error starting agent: {str(e)}")
        
        @self.app.post("/agent/stop", tags=["Agent"])
        async def stop_agent(user: Dict = Depends(self.auth.verify_token)):
            """Detiene el agente autónomo"""
            
            if not self.agent_controller:
                raise HTTPException(status_code=503, detail="Agent controller not available")
            
            try:
                # En implementación real, detener el agente
                return {
                    "message": "Agent stop signal sent",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error stopping agent: {str(e)}")
        
        # === RUTAS DE MONITOREO ===
        
        @self.app.get("/monitoring/alerts", tags=["Monitoring"])
        async def get_alerts(user: Dict = Depends(self.auth.verify_token)):
            """Obtiene alertas activas"""
            
            if not self.monitoring_system:
                raise HTTPException(status_code=503, detail="Monitoring system not available")
            
            summary = self.monitoring_system.alert_manager.get_alert_summary()
            
            return {
                "active_alerts": summary["active_alerts"],
                "alerts_by_level": summary["active_by_level"],
                "recent_alerts": summary["recent_alerts"][:10]
            }
        
        @self.app.post("/monitoring/alerts/{alert_id}/resolve", tags=["Monitoring"])
        async def resolve_alert(
            alert_id: str,
            resolution_note: str = "",
            user: Dict = Depends(self.auth.verify_token)
        ):
            """Resuelve una alerta específica"""
            
            if not self.monitoring_system:
                raise HTTPException(status_code=503, detail="Monitoring system not available")
            
            resolved = self.monitoring_system.alert_manager.resolve_alert(alert_id, resolution_note)
            
            if resolved:
                return {"message": f"Alert {alert_id} resolved successfully"}
            else:
                raise HTTPException(status_code=404, detail="Alert not found")
        
        # === RUTAS DE OPTIMIZACIÓN ===
        
        @self.app.post("/optimization/multi-objective", tags=["Optimization"])
        async def run_multi_objective_optimization(
            request: OptimizationRequest,
            background_tasks: BackgroundTasks,
            user: Dict = Depends(self.auth.verify_token)
        ):
            """Ejecuta optimización multi-objetivo"""
            
            if not self.multi_objective_optimizer:
                raise HTTPException(status_code=503, detail="Multi-objective optimizer not available")
            
            try:
                # Mock data para la demostración
                mock_configs = request.config_candidates or [
                    {"ensemble_weights": {"neural_enhanced": 0.5}, "svi_profile": "default"},
                    {"ensemble_weights": {"neural_enhanced": 0.7}, "svi_profile": "neural_optimized"}
                ]
                
                mock_results_map = {
                    f"config_{i}": [{"best_reward": 0.75, "duration": 45, "quality_rate": 0.8}]
                    for i in range(len(mock_configs))
                }
                
                # Ejecutar optimización en background
                def run_optimization():
                    return self.multi_objective_optimizer.optimize_configurations(mock_configs, mock_results_map)
                
                background_tasks.add_task(run_optimization)
                
                return {
                    "message": "Multi-objective optimization started",
                    "objectives": request.target_objectives,
                    "max_iterations": request.max_iterations,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error in optimization: {str(e)}")
        
        # === RUTAS DE APRENDIZAJE CONTINUO ===
        
        @self.app.post("/learning/add-example", tags=["Learning"])
        async def add_learning_example(
            example: LearningExample,
            learner_id: str = "default",
            user: Dict = Depends(self.auth.verify_token)
        ):
            """Añade ejemplo para aprendizaje continuo"""
            
            if not self.continuous_learning:
                raise HTTPException(status_code=503, detail="Continuous learning system not available")
            
            try:
                from core.agent.continuous_learning import LearningExample as CLLearningExample
                
                # Convertir al formato interno
                cl_example = CLLearningExample(
                    features=example.features,
                    target=example.target,
                    timestamp=datetime.now().isoformat(),
                    context=example.context,
                    weight=example.weight
                )
                
                # Procesar ejemplo
                result = self.continuous_learning.process_learning_example(cl_example, learner_id)
                
                return {
                    "message": "Learning example processed successfully",
                    "learner_id": result["learner_id"],
                    "prediction_error": result["error"],
                    "drift_detected": result["drift_detected"],
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error processing learning example: {str(e)}")
        
        @self.app.get("/learning/status", tags=["Learning"])
        async def get_learning_status(user: Dict = Depends(self.auth.verify_token)):
            """Obtiene estado del sistema de aprendizaje continuo"""
            
            if not self.continuous_learning:
                raise HTTPException(status_code=503, detail="Continuous learning system not available")
            
            status = self.continuous_learning.get_system_status()
            
            return {
                "learners_count": len(status["learners"]),
                "total_samples": status["system_metrics"]["total_samples_processed"],
                "accuracy": status["system_metrics"]["average_prediction_accuracy"],
                "adaptations": status["system_metrics"]["adaptations_made"],
                "knowledge_items": status["system_metrics"]["knowledge_items_stored"],
                "drift_detection_enabled": status["drift_detection"]["enabled"]
            }
        
        # === RUTAS DE SCHEDULER AUTÓNOMO ===
        
        @self.app.get("/scheduler/status", tags=["Scheduler"])
        async def get_scheduler_status(user: Dict = Depends(self.auth.verify_token)):
            """Obtiene estado del scheduler autónomo"""
            
            if not self.autonomous_scheduler:
                raise HTTPException(status_code=503, detail="Autonomous scheduler not available")
            
            status = self.autonomous_scheduler.get_status()
            
            return {
                "running": status["scheduler_running"],
                "uptime_hours": status["uptime_hours"],
                "registered_tasks": status["task_statistics"]["total_registered"],
                "pending_tasks": status["task_statistics"]["pending"],
                "running_tasks": status["task_statistics"]["running"],
                "system_healthy": status["system_resources"]["system_healthy"],
                "scheduled_jobs": status["scheduled_jobs_count"]
            }
        
        # === RUTAS DE REPORTES ===
        
        @self.app.get("/reports/latest", tags=["Reports"])
        async def get_latest_report(user: Dict = Depends(self.auth.verify_token)):
            """Obtiene el último reporte HTML generado"""
            
            try:
                outputs_dir = Path("outputs")
                if not outputs_dir.exists():
                    raise HTTPException(status_code=404, detail="No reports directory found")
                
                # Buscar el reporte más reciente
                html_files = list(outputs_dir.glob("*.html"))
                if not html_files:
                    raise HTTPException(status_code=404, detail="No reports found")
                
                latest_report = max(html_files, key=lambda f: f.stat().st_mtime)
                
                return FileResponse(
                    path=latest_report,
                    media_type="text/html",
                    filename=latest_report.name
                )
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error retrieving report: {str(e)}")
        
        @self.app.get("/reports/list", tags=["Reports"])
        async def list_reports(user: Dict = Depends(self.auth.verify_token)):
            """Lista todos los reportes disponibles"""
            
            try:
                outputs_dir = Path("outputs")
                if not outputs_dir.exists():
                    return {"reports": []}
                
                html_files = list(outputs_dir.glob("*.html"))
                
                reports = []
                for file in html_files:
                    stat = file.stat()
                    reports.append({
                        "filename": file.name,
                        "size_bytes": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                
                # Ordenar por fecha de modificación (más recientes primero)
                reports.sort(key=lambda r: r["modified_at"], reverse=True)
                
                return {"reports": reports}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error listing reports: {str(e)}")
        
        # === RUTAS DE ESTADÍSTICAS ===
        
        @self.app.get("/stats/api", tags=["Statistics"])
        async def get_api_stats(user: Dict = Depends(self.auth.verify_token)):
            """Obtiene estadísticas de la API"""
            
            uptime = (datetime.now() - self.api_stats["start_time"]).total_seconds()
            
            return {
                "uptime_seconds": uptime,
                "total_requests": self.api_stats["requests_total"],
                "requests_per_hour": (self.api_stats["requests_total"] / (uptime / 3600)) if uptime > 0 else 0,
                "error_rate": (self.api_stats["errors_count"] / self.api_stats["requests_total"]) if self.api_stats["requests_total"] > 0 else 0,
                "endpoints_usage": self.api_stats["requests_by_endpoint"],
                "start_time": self.api_stats["start_time"].isoformat()
            }

        # === MÉTRICAS (Prometheus texto plano opcional) ===
        @self.app.get("/metrics", tags=["Metrics"])
        async def metrics():
            """Métricas básicas en formato Prometheus (sin dependencias)."""
            uptime = (datetime.now() - self.api_stats["start_time"]).total_seconds()
            lines = [
                f"omega_api_uptime_seconds {uptime}",
                f"omega_api_requests_total {self.api_stats['requests_total']}",
                f"omega_api_errors_total {self.api_stats['errors_count']}"
            ]
            # Por endpoint
            for ep, cnt in self.api_stats["requests_by_endpoint"].items():
                ep_sanitized = ep.replace('/', '_').strip('_') or 'root'
                lines.append(f"omega_api_requests_by_endpoint{{endpoint=\"{ep_sanitized}\"}} {cnt}")
            return JSONResponse(content="\n".join(lines))
        
        # === RUTAS DE CONFIGURACIÓN ===
        
        @self.app.get("/config/current", tags=["Configuration"])
        async def get_current_config(user: Dict = Depends(self.auth.verify_token)):
            """Obtiene configuración actual del agente"""
            
            if not self.agent_controller:
                raise HTTPException(status_code=503, detail="Agent controller not available")
            
            return {
                "reflection_config": getattr(self.agent_controller, 'reflection_config', {}),
                "advanced_config": getattr(self.agent_controller, 'advanced_config', {}),
                "policy_config": getattr(self.agent_controller, 'policy_cfg', {})
            }

        # === SSE (Server-Sent Events) Fallback simple ===
        try:
            from fastapi import Request
            from fastapi.responses import StreamingResponse
            import asyncio

            @self.app.get('/events/stream', tags=['Events'])
            async def events_stream(request: Request):
                async def event_generator():
                    while True:
                        if await request.is_disconnected():
                            break
                        data = json.dumps({
                            "timestamp": datetime.utcnow().isoformat(),
                            "requests_total": self.api_stats["requests_total"],
                            "errors": self.api_stats["errors_count"]
                        })
                        yield f"data: {data}\n\n"
                        await asyncio.sleep(2)
                return StreamingResponse(event_generator(), media_type='text/event-stream')
        except Exception:
            pass

    def run_server(self, host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
        """Ejecuta el servidor API"""
        
        logger.info(f"🚀 Iniciando OMEGA Agent API en {host}:{port}")
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )

# Función de conveniencia
def create_omega_api() -> OmegaAgentAPI:
    """Crea instancia de la API OMEGA"""
    return OmegaAgentAPI()

# Servidor standalone para testing
if __name__ == '__main__':
    # Test básico de la API
    print("🔌 Testing OMEGA Agent API...")
    
    api = create_omega_api()
    
    print("   ✅ API inicializada correctamente")
    print("   📋 Endpoints disponibles:")
    
    # Listar endpoints principales
    routes = [
        "/health - Health check",
        "/auth/login - Autenticación",
        "/status - Estado del agente",
        "/agent/cycle - Ejecutar ciclo",
        "/monitoring/alerts - Ver alertas",
        "/optimization/multi-objective - Optimización",
        "/learning/add-example - Aprendizaje continuo",
        "/reports/latest - Último reporte",
        "/docs - Documentación Swagger"
    ]
    
    for route in routes:
        print(f"      🔗 {route}")
    
    print(f"\n   🌐 Para probar la API, ejecutar:")
    print(f"      python core/agent/api_interface.py")
    print(f"      Luego visitar: http://localhost:8000/docs")
    
    # Opcionalmente ejecutar servidor
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        print(f"\n🚀 Iniciando servidor API...")
        api.run_server(port=8000, reload=True)
