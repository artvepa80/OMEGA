#!/usr/bin/env python3
"""
🕐 AUTONOMOUS SCHEDULER - Fase 4 del Sistema Agéntico
Programador inteligente con gestión de recursos y optimización temporal
Maneja operaciones autónomas sin intervención humana
"""

import json
import time
import logging
import asyncio
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
try:
    import schedule
except Exception:
    # Fallback mínimo para pruebas: define stubs no operativos
    class _Stub:
        def __getattr__(self, _):
            return self
        def do(self, *a, **kw):
            return self
        def seconds(self):
            return self
        def minutes(self):
            return self
        def hours(self):
            return self
        def days(self):
            return self
    schedule = _Stub()
try:
    import psutil
except Exception:
    psutil = None
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """Prioridades de tareas del sistema"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5

class TaskStatus(Enum):
    """Estados de tareas"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"

@dataclass
class AutonomousTask:
    """Definición de tarea autónoma"""
    task_id: str
    name: str
    function: Callable
    priority: TaskPriority
    schedule_pattern: str  # cron-like or interval
    max_duration: int  # seconds
    dependencies: List[str]
    resource_requirements: Dict[str, Any]
    retry_count: int = 0
    max_retries: int = 3
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

class ResourceManager:
    """Gestor de recursos del sistema"""
    
    def __init__(self):
        self.cpu_threshold = 80.0  # %
        self.memory_threshold = 85.0  # %
        self.disk_threshold = 90.0  # %
        self.concurrent_tasks_limit = 3
        self.running_tasks = {}
        
        logger.info("🔧 ResourceManager inicializado")
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Verifica recursos disponibles del sistema"""
        
        try:
            cpu_usage = psutil.cpu_percent(interval=1) if psutil else 0.0
            memory = psutil.virtual_memory() if psutil else type("M", (), {"percent": 0.0, "available": 8*1024**3})()
            disk = psutil.disk_usage('/') if psutil else type("D", (), {"percent": 0.0, "free": 100*1024**3})()
            
            return {
                "cpu_usage": cpu_usage,
                "memory_usage": memory.percent,
                "disk_usage": disk.percent,
                "available_memory_gb": memory.available / (1024**3),
                "available_disk_gb": disk.free / (1024**3),
                "system_healthy": (
                    cpu_usage < self.cpu_threshold and 
                    memory.percent < self.memory_threshold and 
                    disk.percent < self.disk_threshold
                ),
                "concurrent_tasks": len(self.running_tasks),
                "can_run_task": len(self.running_tasks) < self.concurrent_tasks_limit
            }
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return {
                "system_healthy": False,
                "can_run_task": False,
                "error": str(e)
            }
    
    def reserve_resources(self, task: AutonomousTask) -> bool:
        """Reserva recursos para una tarea"""
        
        system_status = self.check_system_resources()
        
        if not system_status["system_healthy"]:
            logger.warning(f"⚠️ Sistema sobrecargado - no se puede ejecutar {task.name}")
            return False
        
        if not system_status["can_run_task"]:
            logger.warning(f"⚠️ Límite de tareas concurrentes alcanzado - no se puede ejecutar {task.name}")
            return False
        
        # Verificar requisitos específicos de la tarea
        requirements = task.resource_requirements
        
        if requirements.get("min_memory_gb", 0) > system_status["available_memory_gb"]:
            logger.warning(f"⚠️ Memoria insuficiente para {task.name}")
            return False
        
        if requirements.get("min_disk_gb", 0) > system_status["available_disk_gb"]:
            logger.warning(f"⚠️ Espacio en disco insuficiente para {task.name}")
            return False
        
        # Reservar recursos
        self.running_tasks[task.task_id] = {
            "task": task,
            "started_at": datetime.now(),
            "resources": requirements
        }
        
        logger.info(f"🔧 Recursos reservados para {task.name}")
        return True
    
    def release_resources(self, task_id: str):
        """Libera recursos de una tarea completada"""
        
        if task_id in self.running_tasks:
            task_info = self.running_tasks.pop(task_id)
            task_name = task_info["task"].name
            duration = (datetime.now() - task_info["started_at"]).total_seconds()
            
            logger.info(f"🔧 Recursos liberados para {task_name} (duración: {duration:.1f}s)")

class AutonomousScheduler:
    """Programador autónomo inteligente"""
    
    def __init__(self):
        self.resource_manager = ResourceManager()
        self.task_registry = {}
        self.execution_history = []
        self.is_running = False
        self.scheduler_thread = None
        
        # Configuración del scheduler
        self.config = {
            "heartbeat_interval": 30,  # seconds
            "max_task_history": 1000,
            "auto_cleanup_days": 7,
            "adaptive_scheduling": True,
            "learning_enabled": True
        }
        
        # Métricas del scheduler
        self.metrics = {
            "tasks_executed": 0,
            "tasks_successful": 0,
            "tasks_failed": 0,
            "average_execution_time": 0,
            "system_uptime": datetime.now(),
            "last_cleanup": datetime.now()
        }
        
        logger.info("🕐 AutonomousScheduler inicializado")
    
    def register_task(self, task: AutonomousTask):
        """Registra una nueva tarea autónoma"""
        
        self.task_registry[task.task_id] = task
        
        # Programar según el patrón
        self._schedule_task(task)
        
        logger.info(f"📋 Tarea registrada: {task.name} (ID: {task.task_id})")
        logger.info(f"   ⏰ Schedule: {task.schedule_pattern}")
        logger.info(f"   🎯 Priority: {task.priority.name}")
    
    def _schedule_task(self, task: AutonomousTask):
        """Programa una tarea según su patrón"""
        
        pattern = task.schedule_pattern.lower()
        
        if pattern == "continuous":
            # Tarea continua (se ejecuta constantemente)
            schedule.every(30).seconds.do(self._execute_task_wrapper, task.task_id)
        
        elif pattern.startswith("every_"):
            # Patrones de intervalo: every_5min, every_1hour, etc.
            parts = pattern.split("_")
            if len(parts) >= 2:
                interval_str = parts[1]
                
                if "min" in interval_str:
                    minutes = int(interval_str.replace("min", ""))
                    schedule.every(minutes).minutes.do(self._execute_task_wrapper, task.task_id)
                
                elif "hour" in interval_str:
                    hours = int(interval_str.replace("hour", ""))
                    schedule.every(hours).hours.do(self._execute_task_wrapper, task.task_id)
                
                elif "day" in interval_str:
                    days = int(interval_str.replace("day", ""))
                    schedule.every(days).days.do(self._execute_task_wrapper, task.task_id)
        
        elif ":" in pattern:
            # Tiempo específico: "14:30", "09:00"
            schedule.every().day.at(pattern).do(self._execute_task_wrapper, task.task_id)
        
        elif pattern == "startup":
            # Ejecutar una vez al inicio
            schedule.every().second.do(self._execute_task_wrapper, task.task_id).tag("startup")
        
        else:
            logger.warning(f"⚠️ Patrón de schedule no reconocido: {pattern}")
    
    def _execute_task_wrapper(self, task_id: str):
        """Wrapper para ejecución de tareas con manejo de errores"""
        
        if task_id not in self.task_registry:
            logger.error(f"❌ Tarea no encontrada: {task_id}")
            return schedule.CancelJob
        
        task = self.task_registry[task_id]
        
        # Verificar dependencias
        if not self._check_dependencies(task):
            logger.warning(f"⚠️ Dependencias no satisfechas para {task.name}")
            return
        
        # Verificar recursos
        if not self.resource_manager.reserve_resources(task):
            logger.warning(f"⚠️ Recursos no disponibles para {task.name}")
            return
        
        # Ejecutar tarea en thread separado
        execution_thread = threading.Thread(
            target=self._execute_task,
            args=(task,),
            name=f"Task-{task.name}"
        )
        execution_thread.daemon = True
        execution_thread.start()
        
        # Cancelar tareas de startup después de primera ejecución
        if "startup" in [tag for tag in schedule.get_jobs() if task_id in str(tag)]:
            return schedule.CancelJob
    
    def _execute_task(self, task: AutonomousTask):
        """Ejecuta una tarea específica"""
        
        start_time = datetime.now()
        task.status = TaskStatus.RUNNING
        task.started_at = start_time.isoformat()
        
        logger.info(f"🚀 Ejecutando tarea: {task.name}")
        
        try:
            # Timeout para la ejecución
            def timeout_handler():
                logger.error(f"⏰ Timeout en tarea {task.name} (max: {task.max_duration}s)")
                task.status = TaskStatus.FAILED
                task.error_message = f"Timeout after {task.max_duration}s"
            
            # Configurar timeout
            timeout_timer = threading.Timer(task.max_duration, timeout_handler)
            timeout_timer.start()
            
            # Ejecutar función de la tarea
            result = task.function()
            
            # Cancelar timeout si completó a tiempo
            timeout_timer.cancel()
            
            # Marcar como completada
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = end_time.isoformat()
            
            # Actualizar métricas
            self.metrics["tasks_executed"] += 1
            self.metrics["tasks_successful"] += 1
            self._update_average_execution_time(duration)
            
            # Registrar en historial
            self.execution_history.append({
                "task_id": task.task_id,
                "task_name": task.name,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "duration": duration,
                "status": TaskStatus.COMPLETED.value,
                "result": result
            })
            
            logger.info(f"✅ Tarea completada: {task.name} (duración: {duration:.1f}s)")
            
        except Exception as e:
            # Manejar errores
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.retry_count += 1
            
            # Actualizar métricas
            self.metrics["tasks_executed"] += 1
            self.metrics["tasks_failed"] += 1
            
            # Registrar fallo en historial
            self.execution_history.append({
                "task_id": task.task_id,
                "task_name": task.name,
                "started_at": task.started_at,
                "completed_at": end_time.isoformat(),
                "duration": duration,
                "status": TaskStatus.FAILED.value,
                "error": str(e)
            })
            
            logger.error(f"❌ Error en tarea {task.name}: {e}")
            
            # Programar retry si es posible
            if task.retry_count < task.max_retries:
                retry_delay = min(60 * (2 ** task.retry_count), 300)  # Exponential backoff
                logger.info(f"🔄 Programando retry {task.retry_count}/{task.max_retries} en {retry_delay}s")
                
                threading.Timer(
                    retry_delay, 
                    lambda: self._execute_task(task)
                ).start()
        
        finally:
            # Liberar recursos
            self.resource_manager.release_resources(task.task_id)
    
    def _check_dependencies(self, task: AutonomousTask) -> bool:
        """Verifica si las dependencias de una tarea están satisfechas"""
        
        for dep_id in task.dependencies:
            if dep_id not in self.task_registry:
                return False
            
            dep_task = self.task_registry[dep_id]
            if dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    def _update_average_execution_time(self, duration: float):
        """Actualiza tiempo promedio de ejecución"""
        
        current_avg = self.metrics["average_execution_time"]
        total_successful = self.metrics["tasks_successful"]
        
        if total_successful == 1:
            self.metrics["average_execution_time"] = duration
        else:
            # Rolling average
            self.metrics["average_execution_time"] = (
                (current_avg * (total_successful - 1) + duration) / total_successful
            )
    
    def start(self):
        """Inicia el scheduler autónomo"""
        
        if self.is_running:
            logger.warning("⚠️ Scheduler ya está ejecutándose")
            return
        
        self.is_running = True
        
        # Thread principal del scheduler
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="AutonomousScheduler"
        )
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logger.info("🕐 Scheduler autónomo iniciado")
    
    def stop(self):
        """Detiene el scheduler autónomo"""
        
        self.is_running = False
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=10)
        
        # Cancelar tareas programadas
        schedule.clear()
        
        logger.info("🛑 Scheduler autónomo detenido")
    
    def _scheduler_loop(self):
        """Loop principal del scheduler"""
        
        logger.info("🔄 Iniciando loop del scheduler")
        
        while self.is_running:
            try:
                # Ejecutar tareas programadas
                schedule.run_pending()
                
                # Heartbeat
                if self.config["heartbeat_interval"] > 0:
                    time.sleep(self.config["heartbeat_interval"])
                else:
                    time.sleep(1)
                
                # Cleanup periódico
                self._periodic_cleanup()
                
            except Exception as e:
                logger.error(f"❌ Error en scheduler loop: {e}")
                time.sleep(5)  # Esperar antes de continuar
    
    def _periodic_cleanup(self):
        """Limpieza periódica del sistema"""
        
        now = datetime.now()
        
        # Cleanup cada día
        if (now - self.metrics["last_cleanup"]).days >= 1:
            self._cleanup_old_history()
            self._cleanup_completed_tasks()
            self.metrics["last_cleanup"] = now
    
    def _cleanup_old_history(self):
        """Limpia historial antiguo"""
        
        cutoff_date = datetime.now() - timedelta(days=self.config["auto_cleanup_days"])
        
        original_count = len(self.execution_history)
        
        self.execution_history = [
            entry for entry in self.execution_history
            if datetime.fromisoformat(entry.get("started_at", "")) > cutoff_date
        ]
        
        cleaned_count = original_count - len(self.execution_history)
        
        if cleaned_count > 0:
            logger.info(f"🧹 Limpieza: {cleaned_count} entradas de historial eliminadas")
    
    def _cleanup_completed_tasks(self):
        """Limpia tareas completadas de registro"""
        
        # Mantener solo tareas activas o que necesiten reintento
        active_tasks = {}
        
        for task_id, task in self.task_registry.items():
            if (task.status in [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.SCHEDULED] or
                (task.status == TaskStatus.FAILED and task.retry_count < task.max_retries)):
                active_tasks[task_id] = task
        
        removed_count = len(self.task_registry) - len(active_tasks)
        self.task_registry = active_tasks
        
        if removed_count > 0:
            logger.info(f"🧹 Limpieza: {removed_count} tareas completadas eliminadas")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene estado completo del scheduler"""
        
        system_resources = self.resource_manager.check_system_resources()
        
        # Estadísticas de tareas
        task_stats = {
            "total_registered": len(self.task_registry),
            "pending": len([t for t in self.task_registry.values() if t.status == TaskStatus.PENDING]),
            "running": len([t for t in self.task_registry.values() if t.status == TaskStatus.RUNNING]),
            "completed": len([t for t in self.task_registry.values() if t.status == TaskStatus.COMPLETED]),
            "failed": len([t for t in self.task_registry.values() if t.status == TaskStatus.FAILED])
        }
        
        return {
            "scheduler_running": self.is_running,
            "uptime_hours": (datetime.now() - self.metrics["system_uptime"]).total_seconds() / 3600,
            "system_resources": system_resources,
            "task_statistics": task_stats,
            "execution_metrics": self.metrics,
            "recent_executions": self.execution_history[-10:],  # Últimas 10
            "scheduled_jobs_count": len(schedule.jobs),
            "config": self.config
        }
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene estado de una tarea específica"""
        
        if task_id not in self.task_registry:
            return None
        
        task = self.task_registry[task_id]
        
        # Buscar ejecuciones en historial
        executions = [
            entry for entry in self.execution_history
            if entry["task_id"] == task_id
        ]
        
        return {
            "task": asdict(task),
            "execution_count": len(executions),
            "last_execution": executions[-1] if executions else None,
            "success_rate": len([e for e in executions if e["status"] == "completed"]) / max(len(executions), 1)
        }

# Funciones de conveniencia para tareas comunes del agente
def create_agent_cycle_task(agent_controller, priority: TaskPriority = TaskPriority.HIGH) -> AutonomousTask:
    """Crea tarea para ciclos del agente"""
    
    def agent_cycle_function():
        try:
            result = agent_controller.cycle_v3()
            return {"success": True, "cycle_result": result}
        except Exception as e:
            logger.error(f"Error en ciclo del agente: {e}")
            return {"success": False, "error": str(e)}
    
    return AutonomousTask(
        task_id="agent_cycle",
        name="Agent Cycle V3",
        function=agent_cycle_function,
        priority=priority,
        schedule_pattern="every_2hour",  # Cada 2 horas
        max_duration=3600,  # 1 hora max
        dependencies=[],
        resource_requirements={
            "min_memory_gb": 2.0,
            "min_disk_gb": 1.0,
            "cpu_intensive": True
        }
    )

def create_system_monitoring_task() -> AutonomousTask:
    """Crea tarea de monitoreo del sistema"""
    
    def monitoring_function():
        try:
            import psutil
            
            status = {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "process_count": len(psutil.pids())
            }
            
            # Guardar estado
            status_file = Path("results/system_status.json")
            status_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(status_file, 'w') as f:
                json.dump(status, f, indent=2)
            
            return {"success": True, "status": status}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    return AutonomousTask(
        task_id="system_monitoring",
        name="System Monitoring",
        function=monitoring_function,
        priority=TaskPriority.BACKGROUND,
        schedule_pattern="every_15min",
        max_duration=60,
        dependencies=[],
        resource_requirements={
            "min_memory_gb": 0.1,
            "min_disk_gb": 0.1
        }
    )

def create_data_backup_task() -> AutonomousTask:
    """Crea tarea de backup de datos"""
    
    def backup_function():
        try:
            from shutil import copytree
            import tempfile
            
            # Backup de resultados importantes
            source_dirs = ["results", "outputs", "config"]
            backup_dir = Path(f"backups/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            backed_up = []
            for source in source_dirs:
                source_path = Path(source)
                if source_path.exists():
                    dest_path = backup_dir / source
                    copytree(source_path, dest_path, dirs_exist_ok=True)
                    backed_up.append(source)
            
            return {"success": True, "backed_up": backed_up, "backup_path": str(backup_dir)}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    return AutonomousTask(
        task_id="data_backup",
        name="Data Backup",
        function=backup_function,
        priority=TaskPriority.LOW,
        schedule_pattern="every_1day",
        max_duration=600,  # 10 minutos max
        dependencies=[],
        resource_requirements={
            "min_memory_gb": 0.5,
            "min_disk_gb": 5.0
        }
    )

# Función de conveniencia principal
def create_autonomous_scheduler() -> AutonomousScheduler:
    """Crea scheduler autónomo configurado"""
    return AutonomousScheduler()

if __name__ == '__main__':
    # Test básico del scheduler
    print("🕐 Testing Autonomous Scheduler...")
    
    scheduler = create_autonomous_scheduler()
    
    # Crear tarea de prueba
    def test_function():
        print(f"   🔄 Test task ejecutada a las {datetime.now().strftime('%H:%M:%S')}")
        return {"test": "success"}
    
    test_task = AutonomousTask(
        task_id="test_task",
        name="Test Task",
        function=test_function,
        priority=TaskPriority.MEDIUM,
        schedule_pattern="every_5min",
        max_duration=10,
        dependencies=[],
        resource_requirements={"min_memory_gb": 0.1}
    )
    
    # Registrar y probar
    scheduler.register_task(test_task)
    scheduler.start()
    
    try:
        print("   ⏰ Scheduler ejecutándose... (press Ctrl+C to stop)")
        time.sleep(30)  # Ejecutar por 30 segundos
        
        # Mostrar estado
        status = scheduler.get_status()
        print(f"\n   ✅ Test completado:")
        print(f"      📊 Tareas registradas: {status['task_statistics']['total_registered']}")
        print(f"      🔄 Jobs programados: {status['scheduled_jobs_count']}")
        print(f"      💾 Memoria del sistema: {status['system_resources']['memory_usage']:.1f}%")
        
    except KeyboardInterrupt:
        print("\n   🛑 Stopping scheduler...")
    finally:
        scheduler.stop()
        print("   ✅ Scheduler detenido")
