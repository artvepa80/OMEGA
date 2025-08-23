#!/usr/bin/env python3
"""
🎯 OMEGA Core Orchestrator - Coordinador Principal Refactorizado
Versión mejorada del main.py original con arquitectura modular
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.core.pipeline import PredictionPipeline
from src.core.config_manager import ConfigManager
from src.services.prediction_service import PredictionService
from src.services.data_service import DataService
from src.services.export_service import ExportService
from src.ai.ensemble_manager import EnsembleManager
from src.ai.learning_engine import LearningEngine
from src.monitoring.metrics_collector import MetricsCollector
from src.utils.logger_factory import LoggerFactory

class OmegaOrchestrator:
    """
    Coordinador principal del sistema OMEGA Pro AI
    Arquitectura refactorizada y optimizada
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.start_time = time.time()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Inicializar componentes core
        self.config_manager = ConfigManager(config_path)
        self.logger = LoggerFactory.get_logger("OmegaOrchestrator")
        self.metrics = MetricsCollector()
        
        # Servicios principales
        self.data_service = DataService(self.config_manager)
        self.prediction_service = PredictionService(self.config_manager)
        self.export_service = ExportService(self.config_manager)
        
        # Componentes de IA
        self.ensemble_manager = EnsembleManager(self.config_manager)
        self.learning_engine = LearningEngine(self.config_manager)
        
        # Pipeline principal
        self.pipeline = PredictionPipeline(
            data_service=self.data_service,
            prediction_service=self.prediction_service,
            ensemble_manager=self.ensemble_manager,
            learning_engine=self.learning_engine,
            metrics=self.metrics
        )
        
        self.logger.info(f"🚀 OMEGA Orchestrator inicializado - Sesión: {self.session_id}")
    
    async def run_prediction_cycle(self, 
                                 top_n: int = 8,
                                 enable_learning: bool = True,
                                 export_formats: List[str] = ["csv", "json"]) -> Dict[str, Any]:
        """
        Ejecuta un ciclo completo de predicción
        
        Args:
            top_n: Número de predicciones a generar
            enable_learning: Activar aprendizaje adaptativo
            export_formats: Formatos de exportación
            
        Returns:
            Resultados de predicción y métricas
        """
        try:
            self.metrics.start_timing("prediction_cycle")
            self.logger.info(f"🎯 Iniciando ciclo de predicción - {top_n} series")
            
            # Fase 1: Preparación de datos
            historical_data = await self.data_service.load_and_prepare_data()
            self.metrics.record("data_records", len(historical_data))
            
            # Fase 2: Generación de predicciones
            predictions = await self.pipeline.generate_predictions(
                historical_data=historical_data,
                target_count=top_n
            )
            
            # Fase 3: Aplicar aprendizaje (si está habilitado)
            if enable_learning:
                predictions = await self.learning_engine.enhance_predictions(
                    predictions, historical_data
                )
            
            # Fase 4: Exportar resultados
            export_results = await self.export_service.export_predictions(
                predictions, export_formats
            )
            
            # Métricas finales
            cycle_time = self.metrics.end_timing("prediction_cycle")
            
            results = {
                "session_id": self.session_id,
                "predictions": predictions,
                "export_paths": export_results,
                "metrics": {
                    "cycle_time": cycle_time,
                    "predictions_generated": len(predictions),
                    "data_records_processed": len(historical_data),
                    "models_used": self.ensemble_manager.get_active_models()
                },
                "status": "success"
            }
            
            self.logger.info(f"✅ Ciclo completado en {cycle_time:.2f}s - {len(predictions)} predicciones")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error en ciclo de predicción: {e}")
            self.metrics.record_error("prediction_cycle_error", str(e))
            raise
    
    async def run_interactive_mode(self):
        """Modo interactivo con IA avanzada"""
        self.logger.info("🤖 Iniciando modo interactivo")
        
        # Implementar interfaz interactiva
        while True:
            try:
                user_input = input("\n🔤 Ingresa tu consulta (o 'salir' para terminar): ").strip()
                
                if user_input.lower() in ['salir', 'exit', 'quit']:
                    self.logger.info("👋 Finalizando modo interactivo")
                    break
                
                if not user_input:
                    continue
                
                # Procesar consulta con IA
                response = await self.prediction_service.process_ai_query(user_input)
                print(f"\n🤖 OMEGA AI: {response}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Error en modo interactivo: {e}")
    
    async def run_learning_from_result(self, official_result: List[int]):
        """Ejecuta aprendizaje adaptativo desde resultado oficial"""
        self.logger.info(f"🧠 Iniciando aprendizaje desde resultado: {official_result}")
        
        try:
            # Cargar predicciones anteriores
            previous_predictions = await self.data_service.load_recent_predictions()
            
            # Ejecutar aprendizaje
            learning_results = await self.learning_engine.learn_from_result(
                official_result, previous_predictions
            )
            
            # Actualizar modelos
            await self.ensemble_manager.update_model_weights(learning_results.model_adjustments)
            
            self.logger.info(f"✅ Aprendizaje completado - Score: {learning_results.learning_score:.3f}")
            return learning_results
            
        except Exception as e:
            self.logger.error(f"❌ Error en aprendizaje: {e}")
            raise
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtiene estado completo del sistema"""
        uptime = time.time() - self.start_time
        
        return {
            "session_id": self.session_id,
            "uptime_seconds": uptime,
            "system_health": {
                "orchestrator": "healthy",
                "data_service": self.data_service.get_health_status(),
                "prediction_service": self.prediction_service.get_health_status(),
                "ensemble_manager": self.ensemble_manager.get_health_status()
            },
            "metrics": self.metrics.get_summary(),
            "active_models": self.ensemble_manager.get_active_models(),
            "memory_usage": self.metrics.get_memory_usage()
        }
    
    async def shutdown_gracefully(self):
        """Cierre ordenado del sistema"""
        self.logger.info("🔄 Iniciando cierre ordenado del sistema")
        
        try:
            # Guardar estado de modelos
            await self.ensemble_manager.save_model_states()
            
            # Exportar métricas finales
            await self.metrics.export_session_metrics(self.session_id)
            
            # Limpiar recursos
            await self.data_service.cleanup()
            await self.prediction_service.cleanup()
            
            self.logger.info("✅ Sistema cerrado correctamente")
            
        except Exception as e:
            self.logger.error(f"⚠️ Error durante cierre: {e}")

# Factory function para compatibilidad con main.py original
async def run_omega_orchestrator(**kwargs) -> List[Dict[str, Any]]:
    """
    Función de compatibilidad con la interfaz original de main.py
    """
    orchestrator = OmegaOrchestrator()
    
    try:
        results = await orchestrator.run_prediction_cycle(
            top_n=kwargs.get('top_n', 8),
            enable_learning=kwargs.get('learn_from_sorteo', False),
            export_formats=kwargs.get('export_formats', ['csv', 'json'])
        )
        
        return results['predictions']
        
    finally:
        await orchestrator.shutdown_gracefully()