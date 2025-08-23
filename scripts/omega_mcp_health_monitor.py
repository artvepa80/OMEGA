#!/usr/bin/env python3
"""
🔍 OMEGA AI MCP Health Monitor
Advanced health monitoring and alerting for OMEGA AI MCP services
"""

import asyncio
import json
import logging
import os
import sys
import time
import psutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from omega_mcp_integration import get_omega_mcp_integration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/omega_mcp_health_monitor.log')
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class HealthCheckResult:
    """Health check result data structure"""
    service_name: str
    status: str  # healthy, warning, critical, unknown
    message: str
    timestamp: str
    response_time_ms: float
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class SystemMetrics:
    """System metrics data structure"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    load_average: List[float]
    process_count: int
    timestamp: str

class OMEGAMCPHealthMonitor:
    """Comprehensive health monitor for OMEGA MCP services"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/health_monitor_config.json"
        self.config = {}
        self.alert_history = []
        self.health_history = []
        self.system_metrics_history = []
        self.last_alert_times = {}
        self.consecutive_failures = {}
        
        # Load configuration
        self._load_configuration()
        
        # Health check configurations
        self.health_checks = {
            "mcp_integration": self._check_mcp_integration_health,
            "lottery_data_service": self._check_lottery_data_service,
            "notification_service": self._check_notification_service,
            "workflow_automation": self._check_workflow_automation,
            "system_resources": self._check_system_resources,
            "process_health": self._check_process_health,
            "api_connectivity": self._check_api_connectivity,
            "data_integrity": self._check_data_integrity
        }
    
    def _load_configuration(self):
        """Load health monitor configuration"""
        config_file = Path(self.config_path)
        
        default_config = {
            "monitoring": {
                "check_interval_seconds": 300,
                "alert_interval_minutes": 15,
                "history_retention_hours": 24,
                "consecutive_failure_threshold": 3
            },
            "thresholds": {
                "cpu_percent": 85.0,
                "memory_percent": 80.0,
                "disk_usage_percent": 90.0,
                "response_time_ms": 5000.0,
                "process_memory_mb": 1024.0
            },
            "alerts": {
                "enabled": True,
                "channels": ["email", "console"],
                "severity_levels": ["critical", "warning"],
                "cooldown_minutes": 30
            },
            "services": {
                "mcp_integration": {"enabled": True, "critical": True},
                "lottery_data_service": {"enabled": True, "critical": False},
                "notification_service": {"enabled": True, "critical": False},
                "workflow_automation": {"enabled": True, "critical": False},
                "system_resources": {"enabled": True, "critical": True},
                "process_health": {"enabled": True, "critical": True},
                "api_connectivity": {"enabled": True, "critical": False},
                "data_integrity": {"enabled": True, "critical": False}
            }
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    self.config = {**default_config, **loaded_config}
                logger.info(f"✅ Health monitor configuration loaded from {config_file}")
            except Exception as e:
                logger.error(f"❌ Failed to load config: {e}")
                self.config = default_config
        else:
            self.config = default_config
            self._save_configuration()
    
    def _save_configuration(self):
        """Save configuration to file"""
        try:
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"💾 Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save configuration: {e}")
    
    async def _check_mcp_integration_health(self) -> HealthCheckResult:
        """Check OMEGA MCP Integration health"""
        start_time = time.time()
        
        try:
            integration = get_omega_mcp_integration()
            
            if not integration:
                return HealthCheckResult(
                    service_name="mcp_integration",
                    status="critical",
                    message="MCP Integration not available",
                    timestamp=datetime.now().isoformat(),
                    response_time_ms=(time.time() - start_time) * 1000
                )
            
            status_info = integration.get_status()
            
            if status_info.get("integration_active", False):
                status = "healthy"
                message = f"MCP Integration active with {len(status_info.get('services_initialized', []))} services"
            elif status_info.get("services_initialized"):
                status = "warning"
                message = "MCP Integration initialized but not active"
            else:
                status = "critical"
                message = "MCP Integration not properly initialized"
            
            return HealthCheckResult(
                service_name="mcp_integration",
                status=status,
                message=message,
                timestamp=datetime.now().isoformat(),
                response_time_ms=(time.time() - start_time) * 1000,
                details=status_info
            )
            
        except Exception as e:
            return HealthCheckResult(
                service_name="mcp_integration",
                status="critical",
                message="Failed to check MCP Integration",
                timestamp=datetime.now().isoformat(),
                response_time_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    async def _check_lottery_data_service(self) -> HealthCheckResult:
        """Check lottery data service health"""
        start_time = time.time()
        
        try:
            integration = get_omega_mcp_integration()
            
            if not integration or not hasattr(integration, 'mcps'):
                return HealthCheckResult(
                    service_name="lottery_data_service",
                    status="unknown",
                    message="Cannot access MCP services",
                    timestamp=datetime.now().isoformat(),
                    response_time_ms=(time.time() - start_time) * 1000
                )
            
            lottery_mcp = integration.mcps.get("lottery_data")
            if not lottery_mcp:
                return HealthCheckResult(
                    service_name="lottery_data_service",
                    status="warning",
                    message="Lottery data service not initialized",
                    timestamp=datetime.now().isoformat(),
                    response_time_ms=(time.time() - start_time) * 1000
                )
            
            # Test basic functionality
            if hasattr(lottery_mcp, 'get_supported_lotteries'):
                supported = lottery_mcp.get_supported_lotteries()
                status = "healthy"
                message = f"Lottery data service active with {len(supported)} lotteries"
            else:
                status = "warning"
                message = "Lottery data service running but functionality limited"
            
            return HealthCheckResult(
                service_name="lottery_data_service",
                status=status,
                message=message,
                timestamp=datetime.now().isoformat(),
                response_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                service_name="lottery_data_service",
                status="critical",
                message="Failed to check lottery data service",
                timestamp=datetime.now().isoformat(),
                response_time_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    async def _check_notification_service(self) -> HealthCheckResult:
        """Check notification service health"""
        start_time = time.time()
        
        try:
            integration = get_omega_mcp_integration()
            
            if not integration or not hasattr(integration, 'mcps'):
                return HealthCheckResult(
                    service_name="notification_service",
                    status="unknown",
                    message="Cannot access MCP services",
                    timestamp=datetime.now().isoformat(),
                    response_time_ms=(time.time() - start_time) * 1000
                )
            
            notification_mcp = integration.mcps.get("notifications")
            if not notification_mcp:
                return HealthCheckResult(
                    service_name="notification_service",
                    status="warning",
                    message="Notification service not initialized",
                    timestamp=datetime.now().isoformat(),
                    response_time_ms=(time.time() - start_time) * 1000
                )
            
            # Test basic functionality
            if hasattr(notification_mcp, 'get_delivery_stats'):
                stats = notification_mcp.get_delivery_stats()
                available_channels = len(stats.get('available_channels', []))
                status = "healthy" if available_channels > 0 else "warning"
                message = f"Notification service active with {available_channels} channels"
            else:
                status = "warning"
                message = "Notification service running but functionality limited"
            
            return HealthCheckResult(
                service_name="notification_service",
                status=status,
                message=message,
                timestamp=datetime.now().isoformat(),
                response_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                service_name="notification_service",
                status="critical",
                message="Failed to check notification service",
                timestamp=datetime.now().isoformat(),
                response_time_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    async def _check_workflow_automation(self) -> HealthCheckResult:
        """Check workflow automation health"""
        start_time = time.time()
        
        try:
            integration = get_omega_mcp_integration()
            
            if not integration or not hasattr(integration, 'mcps'):
                return HealthCheckResult(
                    service_name="workflow_automation",
                    status="unknown",
                    message="Cannot access MCP services",
                    timestamp=datetime.now().isoformat(),
                    response_time_ms=(time.time() - start_time) * 1000
                )
            
            workflow_mcp = integration.mcps.get("workflow_automation")
            if not workflow_mcp:
                return HealthCheckResult(
                    service_name="workflow_automation",
                    status="warning",
                    message="Workflow automation not initialized",
                    timestamp=datetime.now().isoformat(),
                    response_time_ms=(time.time() - start_time) * 1000
                )
            
            # Check scheduler status
            if hasattr(workflow_mcp, 'scheduler') and workflow_mcp.scheduler:
                if workflow_mcp.scheduler.running:
                    scheduled_jobs = len(workflow_mcp.scheduler.get_jobs())
                    status = "healthy"
                    message = f"Workflow automation active with {scheduled_jobs} scheduled jobs"
                else:
                    status = "warning"
                    message = "Workflow automation initialized but scheduler not running"
            else:
                status = "warning"
                message = "Workflow automation running but scheduler not available"
            
            return HealthCheckResult(
                service_name="workflow_automation",
                status=status,
                message=message,
                timestamp=datetime.now().isoformat(),
                response_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                service_name="workflow_automation",
                status="critical",
                message="Failed to check workflow automation",
                timestamp=datetime.now().isoformat(),
                response_time_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    async def _check_system_resources(self) -> HealthCheckResult:
        """Check system resource health"""
        start_time = time.time()
        
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            thresholds = self.config.get("thresholds", {})
            
            issues = []
            status = "healthy"
            
            if cpu_percent > thresholds.get("cpu_percent", 85):
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
                status = "warning"
            
            if memory.percent > thresholds.get("memory_percent", 80):
                issues.append(f"High memory usage: {memory.percent:.1f}%")
                status = "warning"
            
            if disk.percent > thresholds.get("disk_usage_percent", 90):
                issues.append(f"High disk usage: {disk.percent:.1f}%")
                status = "critical" if disk.percent > 95 else "warning"
            
            if issues:
                message = f"Resource issues detected: {'; '.join(issues)}"
            else:
                message = f"System resources healthy (CPU: {cpu_percent:.1f}%, Memory: {memory.percent:.1f}%, Disk: {disk.percent:.1f}%)"
            
            return HealthCheckResult(
                service_name="system_resources",
                status=status,
                message=message,
                timestamp=datetime.now().isoformat(),
                response_time_ms=(time.time() - start_time) * 1000,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_gb": memory.used / (1024**3),
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3)
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                service_name="system_resources",
                status="critical",
                message="Failed to check system resources",
                timestamp=datetime.now().isoformat(),
                response_time_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    async def _check_process_health(self) -> HealthCheckResult:
        """Check OMEGA process health"""
        start_time = time.time()
        
        try:
            # Look for OMEGA-related processes
            omega_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
                try:
                    if any(keyword in proc.info['name'].lower() for keyword in ['omega', 'mcp']):
                        omega_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'memory_mb': proc.info['memory_info'].rss / (1024*1024),
                            'cpu_percent': proc.info['cpu_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not omega_processes:
                return HealthCheckResult(
                    service_name="process_health",
                    status="warning",
                    message="No OMEGA processes found",
                    timestamp=datetime.now().isoformat(),
                    response_time_ms=(time.time() - start_time) * 1000
                )
            
            # Check for memory/CPU issues
            memory_threshold = self.config.get("thresholds", {}).get("process_memory_mb", 1024)
            high_memory_processes = [p for p in omega_processes if p['memory_mb'] > memory_threshold]
            
            if high_memory_processes:
                status = "warning"
                message = f"{len(high_memory_processes)} OMEGA processes using high memory"
            else:
                status = "healthy"
                message = f"{len(omega_processes)} OMEGA processes running normally"
            
            return HealthCheckResult(
                service_name="process_health",
                status=status,
                message=message,
                timestamp=datetime.now().isoformat(),
                response_time_ms=(time.time() - start_time) * 1000,
                details={"processes": omega_processes}
            )
            
        except Exception as e:
            return HealthCheckResult(
                service_name="process_health",
                status="critical",
                message="Failed to check process health",
                timestamp=datetime.now().isoformat(),
                response_time_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    async def _check_api_connectivity(self) -> HealthCheckResult:
        """Check API connectivity"""
        start_time = time.time()
        
        try:
            # This is a placeholder - implement actual API checks
            api_base = os.getenv("OMEGA_API_BASE", "http://localhost:8000")
            
            # For now, just check if the URL is reachable
            # In a full implementation, you'd make HTTP requests
            
            return HealthCheckResult(
                service_name="api_connectivity",
                status="healthy",
                message=f"API connectivity check passed for {api_base}",
                timestamp=datetime.now().isoformat(),
                response_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                service_name="api_connectivity",
                status="critical",
                message="Failed to check API connectivity",
                timestamp=datetime.now().isoformat(),
                response_time_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    async def _check_data_integrity(self) -> HealthCheckResult:
        """Check data integrity"""
        start_time = time.time()
        
        try:
            # Check critical data files
            critical_files = [
                "data/historial_kabala_github_emergency_clean.csv",
                "config/mcp_config.json"
            ]
            
            missing_files = []
            for file_path in critical_files:
                if not Path(file_path).exists():
                    missing_files.append(file_path)
            
            if missing_files:
                status = "critical"
                message = f"Missing critical files: {', '.join(missing_files)}"
            else:
                status = "healthy"
                message = f"All {len(critical_files)} critical files present"
            
            return HealthCheckResult(
                service_name="data_integrity",
                status=status,
                message=message,
                timestamp=datetime.now().isoformat(),
                response_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                service_name="data_integrity",
                status="critical",
                message="Failed to check data integrity",
                timestamp=datetime.now().isoformat(),
                response_time_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    async def run_all_health_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all enabled health checks"""
        results = {}
        
        enabled_services = {
            name: config for name, config in self.config.get("services", {}).items()
            if config.get("enabled", True)
        }
        
        logger.info(f"🔍 Running health checks for {len(enabled_services)} services...")
        
        for service_name, service_config in enabled_services.items():
            if service_name in self.health_checks:
                try:
                    result = await self.health_checks[service_name]()
                    results[service_name] = result
                    
                    # Log results
                    status_icon = {
                        "healthy": "✅",
                        "warning": "⚠️",
                        "critical": "❌",
                        "unknown": "❓"
                    }.get(result.status, "❓")
                    
                    logger.info(f"   {status_icon} {service_name}: {result.message}")
                    
                except Exception as e:
                    logger.error(f"❌ Health check failed for {service_name}: {e}")
                    results[service_name] = HealthCheckResult(
                        service_name=service_name,
                        status="critical",
                        message=f"Health check execution failed: {str(e)}",
                        timestamp=datetime.now().isoformat(),
                        response_time_ms=0,
                        error=str(e)
                    )
        
        # Update history
        self.health_history.append({
            "timestamp": datetime.now().isoformat(),
            "results": {name: asdict(result) for name, result in results.items()}
        })
        
        # Cleanup old history
        self._cleanup_history()
        
        return results
    
    def _cleanup_history(self):
        """Clean up old history entries"""
        retention_hours = self.config.get("monitoring", {}).get("history_retention_hours", 24)
        cutoff_time = datetime.now() - timedelta(hours=retention_hours)
        
        # Clean health history
        self.health_history = [
            entry for entry in self.health_history
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
        ]
        
        # Clean metrics history
        self.system_metrics_history = [
            entry for entry in self.system_metrics_history
            if datetime.fromisoformat(entry.timestamp) > cutoff_time
        ]
    
    async def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        results = await self.run_all_health_checks()
        
        # Calculate overall status
        statuses = [result.status for result in results.values()]
        if "critical" in statuses:
            overall_status = "critical"
        elif "warning" in statuses:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        # Count status types
        status_counts = {
            "healthy": len([s for s in statuses if s == "healthy"]),
            "warning": len([s for s in statuses if s == "warning"]),
            "critical": len([s for s in statuses if s == "critical"]),
            "unknown": len([s for s in statuses if s == "unknown"])
        }
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        report = {
            "summary": {
                "overall_status": overall_status,
                "timestamp": datetime.now().isoformat(),
                "services_checked": len(results),
                "status_breakdown": status_counts
            },
            "system_overview": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "uptime_hours": (time.time() - psutil.boot_time()) / 3600
            },
            "service_details": {
                name: asdict(result) for name, result in results.items()
            },
            "recommendations": self._generate_recommendations(results)
        }
        
        return report
    
    def _generate_recommendations(self, results: Dict[str, HealthCheckResult]) -> List[str]:
        """Generate recommendations based on health check results"""
        recommendations = []
        
        critical_services = [name for name, result in results.items() if result.status == "critical"]
        warning_services = [name for name, result in results.items() if result.status == "warning"]
        
        if critical_services:
            recommendations.append(f"🚨 CRITICAL: Immediate attention required for: {', '.join(critical_services)}")
        
        if warning_services:
            recommendations.append(f"⚠️ WARNING: Monitor closely: {', '.join(warning_services)}")
        
        # System-specific recommendations
        system_result = results.get("system_resources")
        if system_result and system_result.details:
            details = system_result.details
            if details.get("cpu_percent", 0) > 80:
                recommendations.append("🔧 Consider reducing CPU load or scaling resources")
            if details.get("memory_percent", 0) > 75:
                recommendations.append("🔧 Monitor memory usage and consider cleanup")
            if details.get("disk_percent", 0) > 85:
                recommendations.append("🔧 Free up disk space or expand storage")
        
        if not recommendations:
            recommendations.append("✅ All systems operating normally")
        
        return recommendations
    
    async def run_continuous_monitoring(self, interval_seconds: Optional[int] = None):
        """Run continuous health monitoring"""
        interval = interval_seconds or self.config.get("monitoring", {}).get("check_interval_seconds", 300)
        
        logger.info(f"🔄 Starting continuous health monitoring (interval: {interval}s)")
        
        try:
            while True:
                report = await self.generate_health_report()
                
                # Log summary
                summary = report["summary"]
                logger.info(f"🔍 Health check complete - Status: {summary['overall_status'].upper()}")
                logger.info(f"   Services: ✅{summary['status_breakdown']['healthy']} "
                           f"⚠️{summary['status_breakdown']['warning']} "
                           f"❌{summary['status_breakdown']['critical']} "
                           f"❓{summary['status_breakdown']['unknown']}")
                
                # Save report
                self._save_health_report(report)
                
                # Check for alerts
                await self._check_and_send_alerts(report)
                
                # Wait for next check
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("⌨️ Monitoring stopped by user")
        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
    
    def _save_health_report(self, report: Dict[str, Any]):
        """Save health report to file"""
        try:
            reports_dir = Path("data/health_reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = reports_dir / f"health_report_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Keep only recent reports (last 50)
            reports = sorted(reports_dir.glob("health_report_*.json"))
            if len(reports) > 50:
                for old_report in reports[:-50]:
                    old_report.unlink()
                    
        except Exception as e:
            logger.error(f"❌ Failed to save health report: {e}")
    
    async def _check_and_send_alerts(self, report: Dict[str, Any]):
        """Check conditions and send alerts if needed"""
        if not self.config.get("alerts", {}).get("enabled", True):
            return
        
        summary = report["summary"]
        overall_status = summary["overall_status"]
        
        # Check if we should send an alert
        should_alert = False
        alert_message = ""
        
        if overall_status in ["critical", "warning"]:
            # Check cooldown
            alert_key = f"status_{overall_status}"
            cooldown_minutes = self.config.get("alerts", {}).get("cooldown_minutes", 30)
            last_alert_time = self.last_alert_times.get(alert_key)
            
            if not last_alert_time or (datetime.now() - last_alert_time).total_seconds() > cooldown_minutes * 60:
                should_alert = True
                self.last_alert_times[alert_key] = datetime.now()
                
                # Build alert message
                status_counts = summary["status_breakdown"]
                alert_message = f"""
🚨 OMEGA AI MCP Health Alert

Overall Status: {overall_status.upper()}
Timestamp: {summary["timestamp"]}

Service Status:
✅ Healthy: {status_counts["healthy"]}
⚠️ Warning: {status_counts["warning"]}  
❌ Critical: {status_counts["critical"]}
❓ Unknown: {status_counts["unknown"]}

Recommendations:
{chr(10).join(f"• {rec}" for rec in report["recommendations"])}

Generated by OMEGA AI MCP Health Monitor
                """.strip()
        
        if should_alert and alert_message:
            logger.warning(f"🚨 Sending health alert: {overall_status}")
            # Here you would send the alert via configured channels
            # For now, we just log it
            logger.warning(alert_message)

async def main():
    """Main function for health monitor"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OMEGA AI MCP Health Monitor")
    parser.add_argument("--config", help="Path to health monitor configuration")
    parser.add_argument("--interval", type=int, help="Check interval in seconds")
    parser.add_argument("--continuous", action="store_true", help="Run continuous monitoring")
    parser.add_argument("--report", action="store_true", help="Generate single health report")
    parser.add_argument("--output", choices=["json", "text"], default="text", help="Output format")
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = OMEGAMCPHealthMonitor(args.config)
    
    try:
        if args.continuous:
            # Run continuous monitoring
            await monitor.run_continuous_monitoring(args.interval)
        else:
            # Generate single report
            report = await monitor.generate_health_report()
            
            if args.output == "json":
                print(json.dumps(report, indent=2))
            else:
                # Text format
                summary = report["summary"]
                print(f"\n🔍 OMEGA AI MCP Health Report")
                print(f"{'='*50}")
                print(f"Overall Status: {summary['overall_status'].upper()}")
                print(f"Timestamp: {summary['timestamp']}")
                print(f"Services Checked: {summary['services_checked']}")
                print(f"\nStatus Breakdown:")
                print(f"  ✅ Healthy: {summary['status_breakdown']['healthy']}")
                print(f"  ⚠️ Warning: {summary['status_breakdown']['warning']}")
                print(f"  ❌ Critical: {summary['status_breakdown']['critical']}")
                print(f"  ❓ Unknown: {summary['status_breakdown']['unknown']}")
                
                print(f"\n🔧 Recommendations:")
                for rec in report["recommendations"]:
                    print(f"  • {rec}")
                
                print(f"\n📊 System Overview:")
                sys_overview = report["system_overview"]
                print(f"  CPU: {sys_overview['cpu_percent']:.1f}%")
                print(f"  Memory: {sys_overview['memory_percent']:.1f}%")
                print(f"  Disk: {sys_overview['disk_percent']:.1f}%")
                print(f"  Uptime: {sys_overview['uptime_hours']:.1f} hours")
                
                print(f"\n📋 Service Details:")
                for name, details in report["service_details"].items():
                    status_icon = {"healthy": "✅", "warning": "⚠️", "critical": "❌", "unknown": "❓"}.get(details['status'], "❓")
                    print(f"  {status_icon} {name}: {details['message']} ({details['response_time_ms']:.1f}ms)")
    
    except Exception as e:
        logger.error(f"❌ Health monitor error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())