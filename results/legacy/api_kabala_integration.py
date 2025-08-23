#!/usr/bin/env python3
"""
OMEGA AI Kabala API Integration
API optimizada con scheduler integrado para sorteos Kabala
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from datetime import datetime, date
from typing import Optional
import logging

# Importar el scheduler
from omega_scheduler import KabalaScheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="🎯 OMEGA AI Kabala Predictor",
    description="Sistema de predicción AI especializado en sorteos Kabala (Martes, Jueves, Sábados)",
    version="10.1",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("ENVIRONMENT") == "development" else [
        "https://omega-ai-prod.railway.app",
        "https://omega-ai.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

# Inicializar scheduler
scheduler = KabalaScheduler()

@app.get("/health")
async def health_check():
    """Health check con información de próximos sorteos"""
    try:
        proximos_sorteos = scheduler.get_proximos_sorteos(3)
        proximo = proximos_sorteos[0] if proximos_sorteos else None
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "version": "10.1",
            "loteria": "Kabala",
            "proximo_sorteo": {
                "fecha": proximo.fecha.strftime("%Y-%m-%d") if proximo else None,
                "dia": proximo.dia_semana if proximo else None,
                "tiempo_restante": proximo.tiempo_restante if proximo else None
            } if proximo else None
        }
    except Exception as e:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/")
async def root():
    """Endpoint principal con información de Kabala"""
    try:
        proximo_sorteo = scheduler.get_sorteo_especifico()
        
        return {
            "message": "🎯 OMEGA AI v10.1 - Predictor Especializado en Kabala",
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
            "endpoints": [
                "/predict - Predicción para próximo sorteo",
                "/predict/fecha - Predicción para fecha específica", 
                "/sorteos - Información de próximos sorteos",
                "/health - Estado del sistema"
            ],
            "status": "operational"
        }
    except Exception as e:
        return {
            "message": "🎯 OMEGA AI v10.1 - Predictor Kabala",
            "status": "operational",
            "error": str(e)
        }

@app.post("/predict")
@app.get("/predict")
async def predict_kabala(
    background_tasks: BackgroundTasks,
    fecha: Optional[str] = Query(None, description="Fecha específica (YYYY-MM-DD) o automática para próximo sorteo")
):
    """
    Predicción principal para sorteos Kabala
    
    - Sin parámetros: Predice para el próximo sorteo
    - Con fecha: Predice para fecha específica (debe ser Martes, Jueves o Sábado)
    """
    try:
        logger.info(f"🎯 Generando predicción Kabala para fecha: {fecha or 'próximo sorteo'}")
        
        # Obtener predicción usando el scheduler
        result = scheduler.get_prediction_for_api(fecha)
        
        if not result.get('success', False):
            raise HTTPException(status_code=500, detail=result.get('error', 'Error desconocido'))
        
        # Formatear respuesta
        response = {
            "status": "success",
            "loteria": "Kabala",
            "sorteo_info": {
                "fecha": result['sorteo']['fecha'],
                "dia_semana": result['sorteo']['dia'],
                "fecha_legible": result['sorteo']['fecha_legible'],
                "numero_sorteo": result['sorteo']['numero_sorteo'],
                "tiempo_restante": result['sorteo']['tiempo_restante']
            },
            "mensaje_principal": result['mensaje'],
            "recordatorio": result['recordatorio'],
            "predicciones": result['predicciones'][:8],  # Top 8
            "estadisticas": {
                "total_combinaciones_generadas": result.get('total_combinaciones', 0),
                "predicciones_mostradas": min(8, len(result.get('predicciones', []))),
                "confianza_promedio": round(sum(p.get('confidence', 0) for p in result.get('predicciones', [])[:8]) / min(8, len(result.get('predicciones', []))), 3) if result.get('predicciones') else 0
            },
            "metadata": {
                "generado_en": result['generado'],
                "sistema": "OMEGA AI v10.1",
                "modelos_utilizados": ["LSTM", "Transformer", "Ensemble", "Neural Enhanced"],
                "timezone": "America/Lima"
            }
        }
        
        # Log para monitoreo
        logger.info(f"✅ Predicción generada exitosamente para {result['sorteo']['dia']} {result['sorteo']['fecha_legible']}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en predicción Kabala: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno del servidor: {str(e)}"
        )

@app.get("/sorteos")
async def proximos_sorteos(cantidad: int = Query(5, ge=1, le=10, description="Cantidad de sorteos a mostrar (1-10)")):
    """Información de próximos sorteos Kabala"""
    try:
        sorteos = scheduler.get_proximos_sorteos(cantidad)
        
        return {
            "status": "success",
            "loteria": "Kabala",
            "dias_sorteo": "Martes, Jueves y Sábados a las 21:30",
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
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo sorteos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sorteo/hoy")
async def sorteo_hoy():
    """Información si hay sorteo hoy"""
    try:
        hoy = date.today()
        dia_semana = hoy.weekday()
        
        # Verificar si hoy es día de sorteo (Martes=1, Jueves=3, Sábado=5)
        if dia_semana in [1, 3, 5]:
            sorteo_info = scheduler.get_sorteo_especifico(hoy.strftime("%Y-%m-%d"))
            nombres_dias = {1: "Martes", 3: "Jueves", 5: "Sábado"}
            
            return {
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
            # Obtener próximo sorteo
            proximo = scheduler.get_sorteo_especifico()
            return {
                "hay_sorteo_hoy": False,
                "mensaje": "Hoy no hay sorteo Kabala",
                "proximo_sorteo": {
                    "fecha": proximo.fecha.strftime("%Y-%m-%d"),
                    "dia": proximo.dia_semana,
                    "fecha_legible": scheduler._formatear_fecha_legible(proximo.fecha),
                    "tiempo_restante": proximo.tiempo_restante
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error verificando sorteo de hoy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/predict/{fecha}")
async def predict_fecha_especifica(
    fecha: str,
    background_tasks: BackgroundTasks
):
    """
    Predicción para fecha específica
    Formato: YYYY-MM-DD (debe ser Martes, Jueves o Sábado)
    """
    try:
        # Validar formato de fecha
        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Formato de fecha inválido. Use YYYY-MM-DD (ej: 2025-08-15)"
            )
        
        # Validar que sea día de sorteo
        dia_semana = fecha_obj.weekday()
        if dia_semana not in [1, 3, 5]:  # Martes, Jueves, Sábado
            nombres_dias = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}
            raise HTTPException(
                status_code=400,
                detail=f"La fecha {fecha} ({nombres_dias[dia_semana]}) no es día de sorteo Kabala. Los sorteos son Martes, Jueves y Sábados."
            )
        
        # Generar predicción
        result = scheduler.get_prediction_for_api(fecha)
        
        if not result.get('success', False):
            raise HTTPException(status_code=500, detail=result.get('error', 'Error generando predicción'))
        
        return {
            "status": "success",
            "fecha_solicitada": fecha,
            "sorteo_info": result['sorteo'],
            "mensaje": result['mensaje'],
            "recordatorio": result['recordatorio'],
            "predicciones": result['predicciones'],
            "generado_en": result['generado']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en predicción para fecha {fecha}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def system_status():
    """Estado del sistema con información específica de Kabala"""
    try:
        import psutil
        proximo_sorteo = scheduler.get_sorteo_especifico()
        
        return {
            "sistema": {
                "cpu_percent": psutil.cpu_percent() if 'psutil' in globals() else 0,
                "memory_percent": psutil.virtual_memory().percent if 'psutil' in globals() else 0,
                "environment": os.getenv("ENVIRONMENT", "unknown"),
                "version": "10.1"
            },
            "kabala": {
                "proximo_sorteo": proximo_sorteo.fecha.strftime("%Y-%m-%d"),
                "dia": proximo_sorteo.dia_semana,
                "tiempo_restante": proximo_sorteo.tiempo_restante,
                "numero_sorteo": proximo_sorteo.numero_sorteo
            },
            "scheduler": {
                "configurado": True,
                "timezone": "America/Lima",
                "dias_automaticos": ["Martes", "Jueves", "Sábado"],
                "hora_prediccion": "10:00 AM"
            }
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Endpoint para setup inicial del cron
@app.post("/admin/setup-cron")
async def setup_cron(admin_key: str = Query(..., description="Clave de administrador")):
    """Setup del cron del sistema (requiere clave admin)"""
    
    # Validación básica (en producción usar autenticación real)
    if admin_key != os.getenv("ADMIN_KEY", "omega_admin_2025"):
        raise HTTPException(status_code=403, detail="Clave de administrador inválida")
    
    try:
        success = scheduler.setup_system_cron()
        
        if success:
            return {
                "status": "success",
                "message": "Cron configurado exitosamente",
                "schedule": "Martes, Jueves, Sábados a las 10:00 AM",
                "timezone": "America/Lima"
            }
        else:
            return {
                "status": "failed",
                "message": "Error configurando cron",
                "recommendation": "Ejecutar manualmente: python omega_scheduler.py --setup-cron"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setup cron: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    
    # Mostrar información de inicio
    print("🎯 OMEGA AI Kabala Predictor")
    print("=" * 50)
    print("🗓️  Lotería: Kabala (Martes, Jueves, Sábados)")
    print("🕘 Hora sorteo: 21:30 (Lima, Perú)")
    print("🤖 Sistema: OMEGA AI v10.1")
    print("🌐 Puerto:", port)
    
    # Mostrar próximo sorteo
    try:
        scheduler_info = KabalaScheduler()
        proximo = scheduler_info.get_sorteo_especifico()
        print(f"📅 Próximo sorteo: {proximo.dia_semana} {scheduler_info._formatear_fecha_legible(proximo.fecha)}")
        print(f"⏰ Tiempo restante: {proximo.tiempo_restante}")
    except:
        pass
    
    print("=" * 50)
    
    if os.getenv("ENVIRONMENT") == "production":
        uvicorn.run(
            "api_kabala_integration:app",
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