#!/usr/bin/env python3
"""
🔄 Production Workflow Automation MCP - AUTONOMOUS OPERATIONS
Smart scheduling and workflow orchestration for OMEGA AI
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import json
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

class ProductionWorkflowAutomationMCP:
    """Production-ready MCP para automatización de workflows"""
    
    def __init__(self, 
                 omega_api_base: str,
                 lottery_data_mcp: 'ProductionLotteryDataMCP',
                 notification_mcp: 'ProductionNotificationMCP'):
        
        self.omega_api_base = omega_api_base.rstrip('/')
        self.lottery_data_mcp = lottery_data_mcp
        self.notification_mcp = notification_mcp
        
        # Scheduler para tareas automáticas
        self.scheduler = AsyncIOScheduler()
        self.scheduler_running = False
        
        # Workflows activos y historial
        self.active_workflows = {}
        self.workflow_history = []
        self.processed_results = set()  # Para idempotencia
        
        # Storage para configuraciones
        self.config_dir = Path("data/workflows")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuración de schedules por defecto
        self.default_schedules = {
            "kabala_pe": {
                "cron": "0 23 * * TUE,THU,SAT",  # Mar, Jue, Sáb 11 PM Lima
                "timezone": "America/Lima",
                "description": "Kábala Perú sorteos"
            },
            "megasena_br": {
                "cron": "0 22 * * WED,SAT",  # Mie, Sáb 10 PM Brasília
                "timezone": "America/Sao_Paulo", 
                "description": "Mega-Sena Brasil"
            },
            "powerball_us": {
                "cron": "0 23 * * MON,WED,SAT",  # Lun, Mie, Sáb 11 PM ET
                "timezone": "America/New_York",
                "description": "Powerball USA"
            }
        }
        
        logger.info("🤖 Workflow Automation MCP initialized")
    
    def start(self):
        """Iniciar scheduler - ✅ Lifecycle management"""
        if not self.scheduler_running:
            self.scheduler.start()
            self.scheduler_running = True
            logger.info("🚀 Workflow scheduler started")
    
    def shutdown(self):
        """Detener scheduler gracefully"""
        if self.scheduler_running:
            self.scheduler.shutdown(wait=False)
            self.scheduler_running = False
            logger.info("🛑 Workflow scheduler stopped")
    
    def _generate_result_key(self, lottery_id: str, result_hash: str, date: str) -> str:
        """Generar clave única para resultado"""
        return f"{lottery_id}:{date}:{result_hash}"
    
    def _already_processed(self, lottery_id: str, result_hash: str, date: str) -> bool:
        """Verificar si ya procesamos este resultado - ✅ Idempotencia"""
        key = self._generate_result_key(lottery_id, result_hash, date)
        
        if key in self.processed_results:
            return True
        
        # También verificar en active_workflows por si está en proceso
        if key in self.active_workflows:
            workflow = self.active_workflows[key]
            created_at = datetime.fromisoformat(workflow["created_at"])
            
            # Si lleva más de 10 minutos procesando, asumir que falló
            if datetime.now() - created_at > timedelta(minutes=10):
                del self.active_workflows[key]
                return False
            
            return True
        
        # Marcar como en proceso
        self.active_workflows[key] = {
            "created_at": datetime.now().isoformat(),
            "lottery_id": lottery_id,
            "status": "processing"
        }
        
        return False
    
    def _mark_processed(self, lottery_id: str, result_hash: str, date: str, success: bool = True):
        """Marcar resultado como procesado"""
        key = self._generate_result_key(lottery_id, result_hash, date)
        
        # Remover de workflows activos
        if key in self.active_workflows:
            del self.active_workflows[key]
        
        # Agregar a procesados solo si exitoso
        if success:
            self.processed_results.add(key)
            
            # Mantener solo últimos 1000 resultados procesados
            if len(self.processed_results) > 1000:
                # Convertir a lista, ordenar por fecha, mantener más recientes
                sorted_results = sorted(list(self.processed_results))
                self.processed_results = set(sorted_results[-1000:])
    
    async def run_lottery_cycle(self, lottery_id: str, user_prefs: Dict[str, Any]) -> Dict[str, Any]:
        """Ciclo completo: fetch → validate → predict → notify - ✅ Enhanced"""
        
        execution_id = str(uuid.uuid4())[:8]
        start_time = datetime.now()
        
        try:
            logger.info(f"🎯 Starting lottery cycle for {lottery_id} [{execution_id}]")
            
            # 1. Fetch lottery result
            result = await self.lottery_data_mcp.fetch_lottery_result(lottery_id)
            
            if not result:
                logger.warning(f"No result available for {lottery_id}")
                return {"success": False, "error": "No result available", "execution_id": execution_id}
            
            # 2. Check if stale
            if result.get("stale"):
                logger.warning(f"Only stale result available for {lottery_id}")
                return {"success": False, "error": "Only stale data available", "execution_id": execution_id}
            
            # 3. Check idempotencia
            result_hash = result.get("result_hash")
            result_date = result.get("date")
            
            if self._already_processed(lottery_id, result_hash, result_date):
                logger.info(f"Result already processed for {lottery_id}: {result_hash}")
                return {"success": True, "skipped": "already_processed", "execution_id": execution_id}
            
            try:
                # 4. Generate predictions using OMEGA API
                prediction_data = await self._omega_predict(lottery_id, result, user_prefs)
                
                # 5. Send notifications
                notification_result = await self.notification_mcp.send_prediction_alert(
                    prediction_data, user_prefs
                )
                
                # 6. Mark as successfully processed
                self._mark_processed(lottery_id, result_hash, result_date, success=True)
                
                # 7. Log to history
                execution_time = (datetime.now() - start_time).total_seconds()
                self._log_workflow_execution(lottery_id, execution_id, True, execution_time, {
                    "result_hash": result_hash,
                    "prediction_count": len(prediction_data.get("items", [])),
                    "notifications_sent": notification_result.get("overall_success", False)
                })
                
                logger.info(f"✅ Lottery cycle completed for {lottery_id} [{execution_id}] in {execution_time:.1f}s")
                
                return {
                    "success": True,
                    "execution_id": execution_id,
                    "lottery_id": lottery_id,
                    "result_hash": result_hash,
                    "predictions_generated": len(prediction_data.get("items", [])),
                    "notifications": notification_result,
                    "execution_time": execution_time
                }
                
            except Exception as e:
                # Mark as failed but don't add to processed (allow retry)
                self._mark_processed(lottery_id, result_hash, result_date, success=False)
                raise
        
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            self._log_workflow_execution(lottery_id, execution_id, False, execution_time, {
                "error": error_msg
            })
            
            logger.error(f"❌ Lottery cycle failed for {lottery_id} [{execution_id}]: {error_msg}")
            
            return {
                "success": False,
                "execution_id": execution_id,
                "error": error_msg,
                "execution_time": execution_time
            }
    
    async def _omega_predict(self, lottery_id: str, lottery_result: Dict[str, Any], user_prefs: Dict[str, Any]) -> Dict[str, Any]:
        """Generar predicciones usando OMEGA API - ✅ Real integration"""
        
        # Build request to OMEGA API
        prediction_request = {
            "game_type": lottery_id,
            "historical_data": {
                "latest_result": lottery_result["numbers"],
                "date": lottery_result["date"],
                "confidence": lottery_result.get("confidence", 0.9)
            },
            "preferences": {
                "top_n": user_prefs.get("prediction_count", 3),
                "include_analysis": user_prefs.get("include_analysis", True),
                "risk_profile": user_prefs.get("risk_profile", "balanced")
            }
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=60)  # Longer timeout for AI processing
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.omega_api_base}/api/v1/predictions/generate",
                    json=prediction_request,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        prediction_data = await response.json()
                        
                        # Enrich with lottery info
                        prediction_data.update({
                            "game_name": lottery_id.replace('_', ' ').title(),
                            "based_on_result": lottery_result["numbers"],
                            "generated_at": datetime.now().isoformat(),
                            "execution_mode": "automated_workflow"
                        })
                        
                        return prediction_data
                    
                    else:
                        error_text = await response.text()
                        raise Exception(f"OMEGA API error {response.status}: {error_text}")
        
        except aiohttp.ClientError as e:
            # If API fails, create fallback prediction
            logger.warning(f"OMEGA API unavailable, using fallback prediction: {e}")
            return self._create_fallback_prediction(lottery_id, lottery_result)
        
        except Exception as e:
            logger.error(f"Error calling OMEGA API: {e}")
            return self._create_fallback_prediction(lottery_id, lottery_result)
    
    def _create_fallback_prediction(self, lottery_id: str, lottery_result: Dict[str, Any]) -> Dict[str, Any]:
        """Crear predicción de fallback si OMEGA API no está disponible"""
        
        import random
        
        # Get lottery config for number ranges
        config = self.lottery_data_mcp.lottery_configs.get(lottery_id, {})
        number_count = config.get("number_count", 6)
        min_num, max_num = config.get("number_range", [1, 40])
        
        # Generate 3 random combinations (simple fallback)
        fallback_items = []
        for i in range(3):
            numbers = sorted(random.sample(range(min_num, max_num + 1), number_count))
            fallback_items.append({
                "numbers": numbers,
                "ens_score": random.uniform(0.3, 0.7),  # Random confidence
                "source": "fallback_random",
                "rank": i + 1
            })
        
        return {
            "game_name": lottery_id.replace('_', ' ').title(),
            "items": fallback_items,
            "based_on_result": lottery_result["numbers"],
            "generated_at": datetime.now().isoformat(),
            "execution_mode": "fallback",
            "warning": "Generated using fallback method - OMEGA API unavailable"
        }
    
    def schedule_lottery(self, lottery_id: str, user_prefs: Dict[str, Any], 
                        cron_expr: Optional[str] = None, timezone: str = "UTC") -> str:
        """Programar ejecución automática de lotería - ✅ Enhanced scheduling"""
        
        # Use default schedule if not provided
        if not cron_expr and lottery_id in self.default_schedules:
            default_config = self.default_schedules[lottery_id]
            cron_expr = default_config["cron"]
            timezone = default_config["timezone"]
        
        if not cron_expr:
            raise ValueError(f"No cron expression provided and no default for {lottery_id}")
        
        job_id = f"lottery_{lottery_id}_{uuid.uuid4().hex[:8]}"
        
        # Create wrapped task function
        async def wrapped_task():
            await self._run_wrapped_task(lottery_id, user_prefs, job_id)
        
        # Schedule job
        job = self.scheduler.add_job(
            wrapped_task,
            CronTrigger.from_crontab(cron_expr, timezone=timezone),
            id=job_id,
            replace_existing=False,
            max_instances=1  # Prevent overlapping executions
        )
        
        # Save job configuration
        job_config = {
            "job_id": job_id,
            "lottery_id": lottery_id,
            "cron_expr": cron_expr,
            "timezone": timezone,
            "user_prefs": user_prefs,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        self._save_job_config(job_id, job_config)
        
        logger.info(f"📅 Scheduled {lottery_id} with cron '{cron_expr}' (timezone: {timezone}) -> {job_id}")
        
        return job_id
    
    async def _run_wrapped_task(self, lottery_id: str, user_prefs: Dict[str, Any], job_id: str):
        """Wrapper para manejar errores en tareas programadas"""
        try:
            result = await self.run_lottery_cycle(lottery_id, user_prefs)
            
            if result.get("success"):
                logger.info(f"✅ Scheduled task completed: {job_id}")
            else:
                logger.warning(f"⚠️ Scheduled task finished with issues: {job_id} - {result.get('error', 'unknown')}")
                
        except Exception as e:
            logger.exception(f"❌ Scheduled task failed: {job_id} - {e}")
            
            # Try to send error notification if possible
            try:
                error_message = f"🚨 OMEGA Workflow Error\n\nJob: {job_id}\nLottery: {lottery_id}\nError: {str(e)}\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                await self.notification_mcp.send_notification(
                    message=error_message,
                    channels=user_prefs.get("error_notification_channels", ["email"]),
                    recipients=user_prefs.get("contact_info", {}),
                    priority="high"
                )
            except Exception as notify_error:
                logger.error(f"Failed to send error notification: {notify_error}")
    
    def schedule_all_default_lotteries(self, user_prefs: Dict[str, Any]) -> List[str]:
        """Programar todas las loterías con schedules por defecto"""
        job_ids = []
        
        for lottery_id in self.default_schedules.keys():
            try:
                job_id = self.schedule_lottery(lottery_id, user_prefs)
                job_ids.append(job_id)
            except Exception as e:
                logger.error(f"Failed to schedule {lottery_id}: {e}")
        
        logger.info(f"📅 Scheduled {len(job_ids)} default lotteries")
        return job_ids
    
    def unschedule_lottery(self, job_id: str) -> bool:
        """Cancelar programación de lotería"""
        try:
            self.scheduler.remove_job(job_id)
            
            # Update job config
            config_file = self.config_dir / f"{job_id}.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                config["status"] = "cancelled"
                config["cancelled_at"] = datetime.now().isoformat()
                
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
            
            logger.info(f"🗑️ Unscheduled job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unschedule {job_id}: {e}")
            return False
    
    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Obtener trabajos programados - ✅ Enhanced info"""
        jobs = []
        
        for job in self.scheduler.get_jobs():
            job_info = {
                "id": job.id,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
                "max_instances": job.max_instances,
                "pending": job.pending
            }
            
            # Try to load additional config
            config_file = self.config_dir / f"{job.id}.json"
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    job_info.update({
                        "lottery_id": config.get("lottery_id"),
                        "created_at": config.get("created_at"),
                        "status": config.get("status", "active")
                    })
                except:
                    pass
            
            jobs.append(job_info)
        
        return jobs
    
    def _save_job_config(self, job_id: str, config: Dict[str, Any]):
        """Guardar configuración de job"""
        try:
            config_file = self.config_dir / f"{job_id}.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save job config for {job_id}: {e}")
    
    def _log_workflow_execution(self, lottery_id: str, execution_id: str, success: bool, 
                               execution_time: float, metadata: Dict[str, Any]):
        """Log ejecución de workflow"""
        
        log_entry = {
            "execution_id": execution_id,
            "lottery_id": lottery_id,
            "success": success,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata
        }
        
        self.workflow_history.append(log_entry)
        
        # Mantener solo últimos 1000 registros
        if len(self.workflow_history) > 1000:
            self.workflow_history = self.workflow_history[-1000:]
    
    def get_workflow_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de workflows"""
        
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        last_week = now - timedelta(days=7)
        
        # Filter recent executions
        recent_24h = [
            entry for entry in self.workflow_history 
            if datetime.fromisoformat(entry["timestamp"]) >= last_24h
        ]
        
        recent_week = [
            entry for entry in self.workflow_history
            if datetime.fromisoformat(entry["timestamp"]) >= last_week
        ]
        
        # Calculate stats
        success_rate_24h = (
            len([e for e in recent_24h if e["success"]]) / len(recent_24h) * 100
            if recent_24h else 0
        )
        
        avg_execution_time = (
            sum(e["execution_time"] for e in recent_week) / len(recent_week)
            if recent_week else 0
        )
        
        return {
            "scheduled_jobs": len(self.scheduler.get_jobs()),
            "active_workflows": len(self.active_workflows),
            "processed_results": len(self.processed_results),
            "executions_last_24h": len(recent_24h),
            "executions_last_week": len(recent_week),
            "success_rate_24h": success_rate_24h,
            "avg_execution_time": avg_execution_time,
            "scheduler_running": self.scheduler_running,
            "supported_lotteries": list(self.default_schedules.keys())
        }
    
    async def run_manual_cycle(self, lottery_id: str, user_prefs: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar ciclo manual (para testing)"""
        logger.info(f"🔧 Manual cycle requested for {lottery_id}")
        return await self.run_lottery_cycle(lottery_id, user_prefs)
    
    def setup_monitoring_job(self, check_interval_minutes: int = 60) -> str:
        """Setup job de monitoreo del sistema"""
        
        async def monitoring_task():
            try:
                stats = self.get_workflow_stats()
                logger.info(f"📊 System monitoring: {stats}")
                
                # Alert if success rate is too low
                if stats["success_rate_24h"] < 80 and stats["executions_last_24h"] > 0:
                    logger.warning(f"⚠️ Low success rate detected: {stats['success_rate_24h']:.1f}%")
                
                # Alert if no executions in last 24h but jobs are scheduled
                if stats["scheduled_jobs"] > 0 and stats["executions_last_24h"] == 0:
                    logger.warning("⚠️ No executions in last 24h despite scheduled jobs")
                
            except Exception as e:
                logger.error(f"Monitoring task failed: {e}")
        
        job_id = "system_monitoring"
        
        self.scheduler.add_job(
            monitoring_task,
            IntervalTrigger(minutes=check_interval_minutes),
            id=job_id,
            replace_existing=True
        )
        
        logger.info(f"📊 System monitoring job scheduled every {check_interval_minutes} minutes")
        return job_id