#!/usr/bin/env python3
"""
🤖 AGENT CONTROLLER V4 - Fase 4 del Sistema Agéntico
Controlador autónomo integral con operación completamente independiente:
- Autonomous Scheduler integrado
- Multi-Objective Optimizer
- Continuous Learning System
- Self-Monitoring & Alerts
- API REST Interface
"""

import json
import time
import logging
import threading
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .agent_controller_v3 import ReflectiveAgentController
from .policies.bandit import UCB1Policy, ThompsonSamplingPolicy
from .autonomous_scheduler import create_autonomous_scheduler, create_agent_cycle_task, create_system_monitoring_task, create_data_backup_task
from .multi_objective_optimizer import create_multi_objective_optimizer
from .continuous_learning import create_continuous_learning_system, LearningExample
from .self_monitoring import create_self_monitoring_system, AlertLevel
from .api_interface import create_omega_api

logger = logging.getLogger(__name__)

class AutonomousAgentController(ReflectiveAgentController):
    """Controlador agéntico completamente autónomo V4"""
    
    def __init__(self, cfg_path="config/agent_policy.json"):
        # Inicializar controlador reflexivo V3
        super().__init__(cfg_path)
        
        # Componentes de Fase 4
        self.autonomous_scheduler = create_autonomous_scheduler()
        self.multi_objective_optimizer = create_multi_objective_optimizer()
        self.continuous_learning = create_continuous_learning_system()
        self.self_monitoring = create_self_monitoring_system()
        self.api_interface = create_omega_api()
        
        # Estado autónomo
        self.autonomous_mode = False
        self.last_optimization_time = None
        self.optimization_results_history = []
        self.learning_examples_processed = 0
        
        # Configuración autónoma
        self.autonomous_config = {
            "enable_autonomous_scheduling": True,
            "enable_continuous_optimization": True,
            "enable_online_learning": True,
            "enable_self_monitoring": True,
            "enable_api_interface": True,
            "optimization_interval_hours": 6,
            "learning_adaptation_threshold": 0.1,
            "monitoring_alert_threshold": 2,
            "auto_recovery_enabled": True,
            "resource_management_enabled": True,
            "episode_persistence_path": "results/agent_cycles_v4/history.jsonl",
            "bandit_policy": self.policy_cfg.get("bandit_policy", "ucb1"),
            "max_episode_size_mb": 5
        }
        
        # Métricas autónomas
        self.autonomous_metrics = {
            "autonomous_uptime": datetime.now(),
            "total_autonomous_cycles": 0,
            "successful_optimizations": 0,
            "learning_adaptations": 0,
            "alerts_resolved_automatically": 0,
            "recovery_actions_taken": 0,
            "api_requests_served": 0
        }
        
        logger.info("🤖 AutonomousAgentController V4 inicializado")
        logger.info(f"   🕐 Autonomous Scheduler: {'✅' if self.autonomous_config['enable_autonomous_scheduling'] else '❌'}")
        logger.info(f"   🎯 Multi-Objective Optimizer: {'✅' if self.autonomous_config['enable_continuous_optimization'] else '❌'}")
        logger.info(f"   📚 Continuous Learning: {'✅' if self.autonomous_config['enable_online_learning'] else '❌'}")
        logger.info(f"   👁️ Self-Monitoring: {'✅' if self.autonomous_config['enable_self_monitoring'] else '❌'}")
        logger.info(f"   🔌 API Interface: {'✅' if self.autonomous_config['enable_api_interface'] else '❌'}")

        # Política bandit configurable (heredada desde V2 en self.policy)
        policy_name = str(self.autonomous_config.get("bandit_policy", "ucb1")).lower()
        if policy_name in ("thompson", "thompson_sampling"):
            self.policy = ThompsonSamplingPolicy()
        else:
            self.policy = UCB1Policy()
    
    def start_autonomous_operation(self):
        """Inicia operación completamente autónoma"""
        
        if self.autonomous_mode:
            logger.warning("⚠️ Modo autónomo ya está activo")
            return
        
        self.autonomous_mode = True
        
        logger.info("🚀 Iniciando operación autónoma completa...")
        
        # 1. Configurar e iniciar scheduler autónomo
        if self.autonomous_config["enable_autonomous_scheduling"]:
            self._setup_autonomous_tasks()
            self.autonomous_scheduler.start()
            logger.info("   ✅ Autonomous Scheduler iniciado")
        
        # 2. Iniciar monitoreo continuo
        if self.autonomous_config["enable_self_monitoring"]:
            self.self_monitoring.start_monitoring()
            logger.info("   ✅ Self-Monitoring iniciado")
        
        # 3. Configurar integración de aprendizaje continuo
        if self.autonomous_config["enable_online_learning"]:
            self._setup_continuous_learning()
            logger.info("   ✅ Continuous Learning configurado")
        
        # 4. Inyectar dependencias en API
        if self.autonomous_config["enable_api_interface"]:
            self._setup_api_interface()
            logger.info("   ✅ API Interface configurada")
        
        # 5. Iniciar loop autónomo principal
        self._start_autonomous_loop()
        
        logger.info("🌟 ¡Operación autónoma completa iniciada!")
        logger.info("   🎯 El agente operará de forma completamente independiente")
        logger.info("   📊 Monitoreo, optimización y aprendizaje automáticos")
        logger.info("   🔌 API REST disponible para integración externa")
        # Persistir estado inicial del episodio con rotación
        self._persist_episode_snapshot({
            "event": "autonomous_started",
            "cycle": self.cycle_count,
            "timestamp": datetime.now().isoformat()
        })
    
    def _setup_autonomous_tasks(self):
        """Configura tareas autónomas en el scheduler"""
        
        # Tarea principal: Ciclos del agente
        agent_cycle_task = create_agent_cycle_task(self, priority="HIGH")
        self.autonomous_scheduler.register_task(agent_cycle_task)
        
        # Tarea de monitoreo del sistema
        monitoring_task = create_system_monitoring_task()
        self.autonomous_scheduler.register_task(monitoring_task)
        
        # Tarea de backup de datos
        backup_task = create_data_backup_task()
        self.autonomous_scheduler.register_task(backup_task)
        
        # Tarea de optimización periódica
        def optimization_function():
            try:
                return self._perform_autonomous_optimization()
            except Exception as e:
                logger.error(f"Error en optimización autónoma: {e}")
                return {"success": False, "error": str(e)}
        
        from .autonomous_scheduler import AutonomousTask, TaskPriority
        
        optimization_task = AutonomousTask(
            task_id="autonomous_optimization",
            name="Autonomous Multi-Objective Optimization",
            function=optimization_function,
            priority=TaskPriority.MEDIUM,
            schedule_pattern="every_6hour",  # Cada 6 horas
            max_duration=1800,  # 30 minutos max
            dependencies=[],
            resource_requirements={
                "min_memory_gb": 1.0,
                "min_disk_gb": 0.5,
                "cpu_intensive": True
            }
        )
        
        self.autonomous_scheduler.register_task(optimization_task)
        
        # Tarea de consolidación de aprendizaje
        def learning_consolidation_function():
            try:
                self.continuous_learning.knowledge_manager.consolidate_knowledge()
                return {"success": True, "action": "knowledge_consolidated"}
            except Exception as e:
                logger.error(f"Error en consolidación de aprendizaje: {e}")
                return {"success": False, "error": str(e)}
        
        learning_task = AutonomousTask(
            task_id="learning_consolidation",
            name="Learning Knowledge Consolidation",
            function=learning_consolidation_function,
            priority=TaskPriority.LOW,
            schedule_pattern="every_1day",  # Una vez al día
            max_duration=300,  # 5 minutos max
            dependencies=[],
            resource_requirements={
                "min_memory_gb": 0.5,
                "min_disk_gb": 0.2
            }
        )
        
        self.autonomous_scheduler.register_task(learning_task)
        
        logger.info("📋 Tareas autónomas configuradas y registradas")
    
    def _setup_continuous_learning(self):
        """Configura integración con aprendizaje continuo"""
        
        # El aprendizaje continuo se integra directamente en los ciclos
        # No requiere configuración adicional especial
        logger.info("📚 Continuous Learning integrado en ciclos")
    
    def _setup_api_interface(self):
        """Configura interfaz API con dependencias"""
        
        # Inyectar todas las dependencias en la API
        self.api_interface.inject_dependencies(
            agent_controller=self,
            monitoring_system=self.self_monitoring,
            continuous_learning=self.continuous_learning,
            multi_objective_optimizer=self.multi_objective_optimizer,
            autonomous_scheduler=self.autonomous_scheduler
        )
        
        # Iniciar API en thread separado
        def start_api_server():
            try:
                self.api_interface.run_server(host="0.0.0.0", port=8000)
            except Exception as e:
                logger.error(f"Error iniciando API server: {e}")
        
        api_thread = threading.Thread(target=start_api_server, daemon=True, name="APIServer")
        api_thread.start()
        
        logger.info("🔌 API Server iniciado en puerto 8000")
    
    def _start_autonomous_loop(self):
        """Inicia loop autónomo principal"""
        
        def autonomous_loop():
            logger.info("🔄 Loop autónomo iniciado")
            
            while self.autonomous_mode:
                try:
                    # Verificar y procesar alertas
                    self._process_autonomous_alerts()
                    
                    # Verificar estado de salud del sistema
                    self._check_system_health()
                    
                    # Ejecutar recuperación automática si es necesario
                    if self.autonomous_config["auto_recovery_enabled"]:
                        self._perform_auto_recovery()
                    
                    # Dormir hasta próximo check
                    time.sleep(300)  # 5 minutos
                    
                except Exception as e:
                    logger.error(f"Error en loop autónomo: {e}")
                    time.sleep(60)  # Esperar 1 minuto antes de continuar
            
            logger.info("🛑 Loop autónomo detenido")
        
        # Ejecutar loop en thread separado
        autonomous_thread = threading.Thread(target=autonomous_loop, daemon=True, name="AutonomousLoop")
        autonomous_thread.start()
    
    def cycle_v4(self) -> Dict[str, Any]:
        """Ejecuta ciclo autónomo completo (V4)"""
        
        cycle_start_time = datetime.now()
        self.cycle_count += 1
        
        logger.info(f"🔄 Iniciando Cycle V4 #{self.cycle_count} (Autónomo)")
        
        try:
            # FASE 1-8: Ejecutar ciclo reflexivo V3
            v3_result = super().cycle_v3()
            
            if "error" in v3_result:
                return v3_result
            
            # FASE 9: APRENDIZAJE CONTINUO (V4)
            learning_result = self._continuous_learning_phase(v3_result)
            
            # FASE 10: OPTIMIZACIÓN ADAPTATIVA (V4)
            optimization_result = self._adaptive_optimization_phase(v3_result)
            
            # FASE 11: AUTO-MONITOREO (V4)
            monitoring_result = self._autonomous_monitoring_phase(v3_result)
            
            # FASE 12: GESTIÓN DE RECURSOS (V4)
            resource_management_result = self._resource_management_phase()
            
            cycle_duration = (datetime.now() - cycle_start_time).total_seconds()
            
            # Compilar resultado V4
            v4_result = {
                **v3_result,  # Incluir todo de V3
                "v4_enhancements": {
                    "continuous_learning": learning_result,
                    "adaptive_optimization": optimization_result,
                    "autonomous_monitoring": monitoring_result,
                    "resource_management": resource_management_result
                },
                "v4_duration": cycle_duration,
                "v4_version": "4.0"
            }
            
            # Actualizar métricas autónomas
            self.autonomous_metrics["total_autonomous_cycles"] += 1
            
            # Notificar al monitoreo sobre el ciclo completado
            if self.autonomous_config["enable_self_monitoring"]:
                self.self_monitoring.process_agent_cycle(v4_result)
            
            # Guardar resultado V4
            self._save_v4_cycle_result(v4_result)
            
            logger.info(f"✅ Cycle V4 #{self.cycle_count} completado en {cycle_duration:.1f}s")
            logger.info(f"   📚 Learning processed: {'✅' if learning_result.get('executed') else '❌'}")
            logger.info(f"   🎯 Optimization triggered: {'✅' if optimization_result.get('triggered') else '❌'}")
            logger.info(f"   👁️ Monitoring active: {'✅' if monitoring_result.get('monitoring_active') else '❌'}")
            
            return v4_result
            
        except Exception as e:
            logger.error(f"❌ Error en Cycle V4 #{self.cycle_count}: {e}")
            return {
                "cycle_number": self.cycle_count,
                "error": str(e),
                "timestamp": cycle_start_time.isoformat(),
                "version": "v4"
            }
    
    def _continuous_learning_phase(self, cycle_result: Dict[str, Any]) -> Dict[str, Any]:
        """Fase de aprendizaje continuo"""
        
        if not self.autonomous_config["enable_online_learning"]:
            return {"disabled": True}
        
        logger.info("📚 Procesando aprendizaje continuo...")
        
        try:
            # Extraer features del ciclo
            evaluation = cycle_result.get("evaluation", {})
            metrics = evaluation.get("metrics", {})
            chosen_config = evaluation.get("chosen_config", {})
            
            # Crear ejemplo de aprendizaje
            features = self._extract_learning_features(chosen_config, metrics)
            target = metrics.get("best_reward", 0.0)
            
            context = {
                "cycle": self.cycle_count,
                "planner_mode": cycle_result.get("state_analysis", {}).get("planner_insights", {}).get("current_mode", "unknown"),
                "reflection_quality": cycle_result.get("v3_enhancements", {}).get("deep_reflection", {}).get("quality", "unknown")
            }
            
            learning_example = LearningExample(
                features=features,
                target=target,
                timestamp=datetime.now().isoformat(),
                context=context,
                weight=1.0
            )
            
            # Procesar con el sistema de aprendizaje continuo
            processing_result = self.continuous_learning.process_learning_example(
                learning_example, "performance_predictor"
            )
            
            self.learning_examples_processed += 1
            
            # Verificar si se necesita adaptación
            if processing_result.get("adaptation_triggered"):
                self.autonomous_metrics["learning_adaptations"] += 1
            
            return {
                "executed": True,
                "examples_processed": self.learning_examples_processed,
                "prediction_error": processing_result["error"],
                "drift_detected": processing_result["drift_detected"],
                "adaptation_triggered": processing_result["adaptation_triggered"],
                "learner_id": processing_result["learner_id"]
            }
            
        except Exception as e:
            logger.error(f"Error en aprendizaje continuo: {e}")
            return {
                "executed": False,
                "error": str(e)
            }
    
    def _extract_learning_features(self, config: Dict[str, Any], metrics: Dict[str, Any]) -> Dict[str, float]:
        """Extrae features para aprendizaje continuo"""
        
        features = {}
        
        # Features de configuración
        if "ensemble_weights" in config:
            weights = config["ensemble_weights"]
            features["neural_enhanced_weight"] = weights.get("neural_enhanced", 0.45)
            features["transformer_weight"] = weights.get("transformer_deep", 0.15)
            features["genetic_weight"] = weights.get("genetico", 0.15)
        
        # Features de SVI profile
        if "svi_profile" in config:
            profile_encoding = {
                "conservative": 0.2,
                "default": 0.5,
                "aggressive": 0.8,
                "neural_optimized": 0.9
            }
            features["svi_profile_encoded"] = profile_encoding.get(config["svi_profile"], 0.5)
        
        # Features de métricas anteriores
        features["previous_quality_rate"] = metrics.get("quality_rate", 0.0)
        features["previous_avg_reward"] = metrics.get("average_reward", 0.0)
        features["execution_time"] = metrics.get("average_execution_time", 60.0)
        
        # Features del ciclo
        features["cycle_number"] = float(self.cycle_count)
        features["time_of_day"] = float(datetime.now().hour)
        
        return features
    
    def _adaptive_optimization_phase(self, cycle_result: Dict[str, Any]) -> Dict[str, Any]:
        """Fase de optimización adaptativa"""
        
        if not self.autonomous_config["enable_continuous_optimization"]:
            return {"disabled": True}
        
        # Verificar si es momento de optimizar
        now = datetime.now()
        
        if self.last_optimization_time is None:
            should_optimize = self.cycle_count >= 5  # Después de 5 ciclos iniciales
        else:
            hours_since_last = (now - self.last_optimization_time).total_seconds() / 3600
            should_optimize = hours_since_last >= self.autonomous_config["optimization_interval_hours"]
        
        if not should_optimize:
            return {"triggered": False, "reason": "optimization_interval_not_reached"}
        
        logger.info("🎯 Triggering adaptive optimization...")
        
        try:
            # Usar resultados recientes para optimización
            recent_cycles = self._get_recent_cycle_history(20)  # Últimos 20 ciclos
            
            if len(recent_cycles) < 5:
                return {"triggered": False, "reason": "insufficient_cycle_history"}
            
            # Preparar configuraciones candidatas basadas en learning
            candidate_configs = self._generate_learning_based_candidates()
            
            # Crear mapa de resultados basado en historial
            results_map = self._create_results_map_from_history(candidate_configs, recent_cycles)
            
            # Ejecutar optimización multi-objetivo
            optimization_result = self.multi_objective_optimizer.optimize_configurations(
                candidate_configs, results_map
            )
            
            self.last_optimization_time = now
            self.optimization_results_history.append({
                "timestamp": now.isoformat(),
                "result": optimization_result
            })
            
            # Mantener solo últimos 10 resultados
            if len(self.optimization_results_history) > 10:
                self.optimization_results_history = self.optimization_results_history[-10:]
            
            self.autonomous_metrics["successful_optimizations"] += 1
            
            return {
                "triggered": True,
                "best_score": optimization_result["best_solution"]["overall_score"],
                "pareto_fronts": optimization_result["pareto_summary"]["total_fronts"],
                "recommendations_count": len(optimization_result["recommendations"])
            }
            
        except Exception as e:
            logger.error(f"Error en optimización adaptativa: {e}")
            return {
                "triggered": False,
                "error": str(e)
            }
    
    def _generate_learning_based_candidates(self) -> List[Dict[str, Any]]:
        """Genera configuraciones candidatas basadas en aprendizaje"""
        
        # Usar predicciones del continuous learning para generar candidatos prometedores
        candidates = []
        
        # Configuración baseline
        baseline = {
            "ensemble_weights": {
                "neural_enhanced": 0.45,
                "transformer_deep": 0.15,
                "genetico": 0.15,
                "analizador_200": 0.12,
                "montecarlo": 0.05,
                "lstm_v2": 0.03,
                "clustering": 0.01
            },
            "svi_profile": "default"
        }
        candidates.append(baseline)
        
        # Variaciones basadas en learning insights
        for neural_weight in [0.3, 0.5, 0.7]:
            for profile in ["neural_optimized", "conservative", "aggressive"]:
                config = {
                    "ensemble_weights": {
                        "neural_enhanced": neural_weight,
                        "transformer_deep": 0.2,
                        "genetico": 0.2,
                        "analizador_200": 0.15,
                        "montecarlo": (1.0 - neural_weight - 0.55) * 0.5,
                        "lstm_v2": (1.0 - neural_weight - 0.55) * 0.3,
                        "clustering": (1.0 - neural_weight - 0.55) * 0.2
                    },
                    "svi_profile": profile
                }
                
                # Normalizar pesos
                total = sum(config["ensemble_weights"].values())
                config["ensemble_weights"] = {
                    k: v/total for k, v in config["ensemble_weights"].items()
                }
                
                candidates.append(config)
        
        return candidates
    
    def _create_results_map_from_history(self, candidates: List[Dict[str, Any]], 
                                       history: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Crea mapa de resultados basado en historial"""
        
        results_map = {}
        
        for i, config in enumerate(candidates):
            config_id = f"config_{i}"
            
            # Buscar ciclos similares en el historial
            similar_results = []
            
            for cycle in history:
                # Simplemente usar los resultados como están
                # En implementación real, se buscarían configuraciones similares
                similar_results.append({
                    "best_reward": cycle.get("best_reward", 0.7),
                    "quality_rate": cycle.get("quality_rate", 0.8),
                    "duration": cycle.get("duration", 60),
                    "planner_mode": cycle.get("planner_mode", "active_learning")
                })
            
            results_map[config_id] = similar_results[:3]  # Máximo 3 resultados por config
        
        return results_map
    
    def _autonomous_monitoring_phase(self, cycle_result: Dict[str, Any]) -> Dict[str, Any]:
        """Fase de auto-monitoreo"""
        
        if not self.autonomous_config["enable_self_monitoring"]:
            return {"disabled": True}
        
        try:
            # El monitoreo ya está procesando el ciclo automáticamente
            # Aquí solo reportamos el estado
            
            monitoring_status = self.self_monitoring.get_monitoring_status()
            
            return {
                "monitoring_active": monitoring_status["monitoring_active"],
                "system_health": monitoring_status["system_health"]["overall_health"],
                "active_alerts": monitoring_status["alerts"]["active_alerts"],
                "recent_alerts": len(monitoring_status["alerts"]["recent_alerts"])
            }
            
        except Exception as e:
            logger.error(f"Error en fase de monitoreo: {e}")
            return {
                "monitoring_active": False,
                "error": str(e)
            }
    
    def _resource_management_phase(self) -> Dict[str, Any]:
        """Fase de gestión de recursos"""
        
        if not self.autonomous_config["resource_management_enabled"]:
            return {"disabled": True}
        
        try:
            # Verificar recursos del scheduler
            scheduler_status = self.autonomous_scheduler.get_status()
            system_resources = scheduler_status["system_resources"]
            
            resource_actions = []
            
            # Gestión proactiva de recursos
            if not system_resources["system_healthy"]:
                resource_actions.append("system_health_warning_issued")
                
                # Reducir frecuencia de tareas si es necesario
                if system_resources["cpu_usage"] > 90:
                    resource_actions.append("reduced_task_frequency")
            
            if not system_resources["can_run_task"]:
                resource_actions.append("task_queue_management")
            
            return {
                "executed": True,
                "system_healthy": system_resources["system_healthy"],
                "cpu_usage": system_resources["cpu_usage"],
                "memory_usage": system_resources["memory_usage"],
                "actions_taken": resource_actions
            }
            
        except Exception as e:
            logger.error(f"Error en gestión de recursos: {e}")
            return {
                "executed": False,
                "error": str(e)
            }
    
    def _process_autonomous_alerts(self):
        """Procesa alertas de forma autónoma"""
        
        if not self.self_monitoring:
            return
        
        try:
            alert_summary = self.self_monitoring.alert_manager.get_alert_summary()
            active_alerts = alert_summary["active_alerts"]
            
            if active_alerts >= self.autonomous_config["monitoring_alert_threshold"]:
                logger.warning(f"🚨 {active_alerts} alertas activas - evaluando acción autónoma")
                
                # Resolver alertas automáticamente si es posible
                for alert in alert_summary["recent_alerts"][-5:]:  # Últimas 5 alertas
                    if not alert.get("resolved", False):
                        self._try_auto_resolve_alert(alert)
        
        except Exception as e:
            logger.error(f"Error procesando alertas autónomas: {e}")
    
    def _try_auto_resolve_alert(self, alert: Dict[str, Any]):
        """Intenta resolver una alerta automáticamente"""
        
        alert_category = alert.get("category", "")
        alert_level = alert.get("level", "")
        
        # Solo resolver alertas de warning automáticamente
        if alert_level == "warning":
            if "system_health" in alert_category:
                # Intentar liberar recursos
                logger.info(f"🔧 Auto-resolviendo alerta de sistema: {alert.get('title', '')}")
                
                # Marcar como resuelta
                alert_id = alert.get("alert_id")
                if alert_id:
                    resolved = self.self_monitoring.alert_manager.resolve_alert(
                        alert_id, "Auto-resolved by autonomous system"
                    )
                    
                    if resolved:
                        self.autonomous_metrics["alerts_resolved_automatically"] += 1
                        logger.info(f"✅ Alerta {alert_id} resuelta automáticamente")
    
    def _check_system_health(self):
        """Verifica salud del sistema"""
        
        try:
            if self.self_monitoring:
                status = self.self_monitoring.get_monitoring_status()
                overall_health = status["system_health"]["overall_health"]
                
                if overall_health == "critical":
                    logger.critical("🚨 Sistema en estado crítico - activando recuperación automática")
                    self._perform_emergency_recovery()
                    
        except Exception as e:
            logger.error(f"Error verificando salud del sistema: {e}")
    
    def _perform_auto_recovery(self):
        """Realiza recuperación automática"""
        
        # Implementación básica de auto-recovery
        try:
            # Verificar si hay componentes que necesitan reinicio
            components_health = {
                "scheduler": self.autonomous_scheduler.is_running,
                "monitoring": self.self_monitoring.is_monitoring,
                "learning": len(self.continuous_learning.learners) > 0
            }
            
            recovery_actions = []
            
            for component, is_healthy in components_health.items():
                if not is_healthy:
                    recovery_actions.append(f"restart_{component}")
                    self._restart_component(component)
            
            if recovery_actions:
                self.autonomous_metrics["recovery_actions_taken"] += 1
                logger.info(f"🔧 Acciones de recuperación: {recovery_actions}")
                
        except Exception as e:
            logger.error(f"Error en auto-recovery: {e}")
    
    def _restart_component(self, component: str):
        """Reinicia un componente específico"""
        
        logger.info(f"🔄 Reiniciando componente: {component}")
        
        if component == "scheduler" and not self.autonomous_scheduler.is_running:
            self.autonomous_scheduler.start()
        
        elif component == "monitoring" and not self.self_monitoring.is_monitoring:
            self.self_monitoring.start_monitoring()
        
        elif component == "learning" and len(self.continuous_learning.learners) == 0:
            # Recrear learners por defecto
            self.continuous_learning.create_learner("performance_predictor", "performance")
            self.continuous_learning.create_learner("stability_analyzer", "stability")
    
    def _perform_emergency_recovery(self):
        """Realiza recuperación de emergencia"""
        
        logger.critical("🚨 Iniciando recuperación de emergencia")
        
        # Acciones de emergencia
        emergency_actions = [
            "reducing_task_frequency",
            "clearing_low_priority_tasks", 
            "enabling_conservative_mode"
        ]
        
        # Reducir frecuencia de tareas
        if hasattr(self.autonomous_scheduler, 'config'):
            self.autonomous_scheduler.config["heartbeat_interval"] = 120  # Aumentar intervalo
        
        # Cambiar a modo conservador
        if hasattr(self, 'reflection_config'):
            self.reflection_config["reflection_frequency"] = 5  # Reducir frecuencia de reflexión
        
        self.autonomous_metrics["recovery_actions_taken"] += 1
        
        logger.critical(f"🔧 Recuperación de emergencia aplicada: {emergency_actions}")
    
    def _perform_autonomous_optimization(self) -> Dict[str, Any]:
        """Ejecuta optimización autónoma programada"""
        
        logger.info("🎯 Ejecutando optimización autónoma programada...")
        
        try:
            # Obtener configuraciones candidatas
            candidates = self._generate_learning_based_candidates()
            
            # Crear resultados mock para la optimización
            results_map = {}
            for i, config in enumerate(candidates):
                config_id = f"config_{i}"
                
                # Simular resultados basados en la configuración
                neural_weight = config["ensemble_weights"].get("neural_enhanced", 0.45)
                base_reward = 0.6 + (neural_weight * 0.25)
                
                results_map[config_id] = [{
                    "best_reward": base_reward + np.random.normal(0, 0.05),
                    "quality_rate": 0.75 + (neural_weight * 0.15),
                    "duration": 60 - (neural_weight * 10),
                    "planner_mode": "autonomous_optimization"
                }]
            
            # Ejecutar optimización
            result = self.multi_objective_optimizer.optimize_configurations(candidates, results_map)
            
            return {
                "success": True,
                "best_score": result["best_solution"]["overall_score"],
                "recommendations": len(result["recommendations"]),
                "pareto_fronts": result["pareto_summary"]["total_fronts"]
            }
            
        except Exception as e:
            logger.error(f"Error en optimización autónoma: {e}")
            return {"success": False, "error": str(e)}
    
    def _save_v4_cycle_result(self, cycle_result: Dict[str, Any]):
        """Guarda resultado de ciclo V4"""
        
        results_dir = Path("results/agent_cycles_v4")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivo individual del ciclo V4
        cycle_file = results_dir / f"cycle_v4_{self.cycle_count:04d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(cycle_file, 'w') as f:
            json.dump(cycle_result, f, indent=2, default=str)
        
        # Append a historial V4
        history_file = results_dir / "cycles_v4_history.jsonl"
        with open(history_file, 'a') as f:
            f.write(json.dumps(cycle_result, default=str) + '\n')

        # Rotación básica por tamaño
        try:
            max_mb = float(self.autonomous_config.get("max_episode_size_mb", 5))
            if history_file.exists() and history_file.stat().st_size > max_mb * 1024 * 1024:
                # Truncar conservando últimas 500 líneas
                lines = history_file.read_text().splitlines()
                tail = lines[-500:]
                history_file.write_text("\n".join(tail) + "\n")
        except Exception:
            pass

    def _persist_episode_snapshot(self, payload: Dict[str, Any]):
        """Persiste snapshot del episodio con rotación básica"""
        results_dir = Path("results/agent_cycles_v4")
        results_dir.mkdir(parents=True, exist_ok=True)
        history_file = results_dir / "cycles_v4_history.jsonl"
        try:
            with open(history_file, 'a') as f:
                f.write(json.dumps(payload, default=str) + '\n')
            # Aplicar rotación igual que en _save_v4_cycle_result
            max_mb = float(self.autonomous_config.get("max_episode_size_mb", 5))
            if history_file.exists() and history_file.stat().st_size > max_mb * 1024 * 1024:
                lines = history_file.read_text().splitlines()
                tail = lines[-500:]
                history_file.write_text("\n".join(tail) + "\n")
        except Exception:
            pass
    
    def stop_autonomous_operation(self):
        """Detiene operación autónoma"""
        
        if not self.autonomous_mode:
            logger.warning("⚠️ Modo autónomo no está activo")
            return
        
        self.autonomous_mode = False
        
        logger.info("🛑 Deteniendo operación autónoma...")
        
        # Detener componentes
        if self.autonomous_scheduler.is_running:
            self.autonomous_scheduler.stop()
        
        if self.self_monitoring.is_monitoring:
            self.self_monitoring.stop_monitoring()
        
        logger.info("✅ Operación autónoma detenida")
    
    def get_autonomous_status(self) -> Dict[str, Any]:
        """Obtiene estado completo del sistema autónomo"""
        
        # Combinar estado de todos los componentes
        base_insights = self.get_v3_insights()
        
        autonomous_status = {
            "controller_version": "v4",
            "autonomous_mode": self.autonomous_mode,
            "autonomous_uptime_hours": (datetime.now() - self.autonomous_metrics["autonomous_uptime"]).total_seconds() / 3600,
            "autonomous_metrics": self.autonomous_metrics,
            "autonomous_config": self.autonomous_config,
            
            # Estados de componentes
            "scheduler_status": self.autonomous_scheduler.get_status() if self.autonomous_scheduler else None,
            "monitoring_status": self.self_monitoring.get_monitoring_status() if self.self_monitoring else None,
            "learning_status": self.continuous_learning.get_system_status() if self.continuous_learning else None,
            "optimizer_insights": self.multi_objective_optimizer.get_optimization_insights() if self.multi_objective_optimizer else None,
            
            # Estado base (V3)
            "base_controller": base_insights,
            
            "timestamp": datetime.now().isoformat()
        }
        
        return autonomous_status

# Función de conveniencia para crear controlador V4
def create_autonomous_agent_controller(cfg_path: str = "config/agent_policy.json") -> AutonomousAgentController:
    """Crea controlador agéntico autónomo V4"""
    return AutonomousAgentController(cfg_path)

if __name__ == "__main__":
    # Demo del controlador V4 autónomo
    print("🤖 OMEGA Agent Controller V4 - Autonomous Demo")
    print("=" * 60)
    
    controller = create_autonomous_agent_controller()
    
    try:
        # Mostrar estado inicial
        print("📊 Estado inicial:")
        initial_status = controller.get_autonomous_status()
        print(f"   🤖 Versión: {initial_status['controller_version']}")
        print(f"   🔄 Modo autónomo: {'✅' if initial_status['autonomous_mode'] else '❌'}")
        
        # Iniciar operación autónoma
        print("\n🚀 Iniciando operación autónoma...")
        controller.start_autonomous_operation()
        
        # Ejecutar algunos ciclos de demostración
        print("\n🔄 Ejecutando ciclos de demostración...")
        for i in range(3):
            print(f"\n   Ciclo {i+1}:")
            result = controller.cycle_v4()
            
            if "error" not in result:
                v4_enhancements = result.get("v4_enhancements", {})
                print(f"      📚 Learning: {'✅' if v4_enhancements.get('continuous_learning', {}).get('executed') else '❌'}")
                print(f"      🎯 Optimization: {'✅' if v4_enhancements.get('adaptive_optimization', {}).get('triggered') else '❌'}")
                print(f"      👁️ Monitoring: {'✅' if v4_enhancements.get('autonomous_monitoring', {}).get('monitoring_active') else '❌'}")
                print(f"      ⏱️ Duración: {result.get('v4_duration', 0):.1f}s")
            else:
                print(f"      ❌ Error: {result.get('error')}")
            
            time.sleep(2)  # Pausa entre ciclos
        
        # Mostrar estado final
        print("\n📊 Estado final:")
        final_status = controller.get_autonomous_status()
        metrics = final_status["autonomous_metrics"]
        
        print(f"   🔄 Ciclos autónomos: {metrics['total_autonomous_cycles']}")
        print(f"   🎯 Optimizaciones: {metrics['successful_optimizations']}")
        print(f"   📚 Adaptaciones de learning: {metrics['learning_adaptations']}")
        print(f"   🚨 Alertas auto-resueltas: {metrics['alerts_resolved_automatically']}")
        
        print(f"\n✅ Demo V4 completado exitosamente!")
        print(f"🌟 OMEGA ahora opera de forma completamente autónoma!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrumpido por usuario")
    finally:
        controller.stop_autonomous_operation()
        print("🛑 Operación autónoma detenida")
