#!/usr/bin/env python3
"""
🔧 OMEGA AI MCP Service Manager
Production service orchestration for OMEGA AI MCP integration
"""

import asyncio
import argparse
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from omega_mcp_integration import OMEGAMCPIntegration, initialize_mcp_integration, shutdown_mcp_integration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/omega_mcp_service.log')
    ]
)

logger = logging.getLogger(__name__)

class OMEGAMCPService:
    """Service manager for OMEGA AI MCP integration"""
    
    def __init__(self):
        self.integration = None
        self.is_running = False
        self.shutdown_event = asyncio.Event()
        self.service_config = {}
        
    async def start_service(self, config_path: Optional[str] = None, 
                           daemon_mode: bool = False) -> bool:
        """Start the MCP service"""
        try:
            logger.info("🚀 Starting OMEGA AI MCP Service...")
            
            # Initialize integration
            self.integration = OMEGAMCPIntegration(config_path)
            
            # Load service preferences
            user_prefs = self._load_user_preferences()
            
            # Initialize and start
            if not await self.integration.initialize():
                logger.error("❌ Failed to initialize MCP integration")
                return False
            
            if not await self.integration.start(user_prefs):
                logger.error("❌ Failed to start MCP services")
                return False
            
            self.is_running = True
            logger.info("✅ OMEGA AI MCP Service started successfully")
            
            if daemon_mode:
                await self._run_daemon()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start MCP service: {e}")
            return False
    
    async def stop_service(self):
        """Stop the MCP service gracefully"""
        if not self.is_running:
            return
        
        logger.info("🛑 Stopping OMEGA AI MCP Service...")
        self.is_running = False
        
        if self.integration:
            await self.integration.stop()
        
        self.shutdown_event.set()
        logger.info("✅ OMEGA AI MCP Service stopped")
    
    async def restart_service(self, config_path: Optional[str] = None):
        """Restart the MCP service"""
        logger.info("🔄 Restarting OMEGA AI MCP Service...")
        await self.stop_service()
        await asyncio.sleep(2)  # Brief pause
        return await self.start_service(config_path)
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status"""
        if self.integration:
            status = self.integration.get_status()
            status.update({
                "service_running": self.is_running,
                "service_uptime": self._get_uptime()
            })
            return status
        else:
            return {
                "service_running": False,
                "integration_active": False,
                "services_initialized": [],
                "error": "Integration not initialized"
            }
    
    def _load_user_preferences(self) -> Dict[str, Any]:
        """Load user preferences for MCP services"""
        prefs_file = Path("config/user_preferences.json")
        
        default_prefs = {
            "notification_channels": ["email"],
            "contact_info": {
                "email": os.getenv("TEST_EMAIL", "admin@localhost")
            },
            "prediction_count": 5,
            "include_analysis": True,
            "include_disclaimer": True,
            "risk_profile": "balanced",
            "summary_channels": ["email"],
            "error_notification_channels": ["email"],
            "lottery_preferences": {
                "kabala_pe": {
                    "enabled": True,
                    "notification_time": "23:30",
                    "timezone": "America/Lima"
                }
            }
        }
        
        if prefs_file.exists():
            try:
                with open(prefs_file, 'r') as f:
                    user_prefs = json.load(f)
                    # Merge with defaults
                    default_prefs.update(user_prefs)
                logger.info(f"✅ Loaded user preferences from {prefs_file}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load user preferences: {e}")
        else:
            # Create default preferences file
            try:
                with open(prefs_file, 'w') as f:
                    json.dump(default_prefs, f, indent=2)
                logger.info(f"📝 Created default user preferences at {prefs_file}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to create preferences file: {e}")
        
        return default_prefs
    
    def _get_uptime(self) -> str:
        """Get service uptime"""
        if hasattr(self, '_start_time'):
            uptime_seconds = time.time() - self._start_time
            hours, remainder = divmod(uptime_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        return "Unknown"
    
    async def _run_daemon(self):
        """Run service in daemon mode"""
        self._start_time = time.time()
        logger.info("🔄 Running in daemon mode. Press Ctrl+C to stop.")
        
        try:
            # Periodic status reporting
            async def status_reporter():
                while self.is_running:
                    try:
                        await asyncio.sleep(300)  # Every 5 minutes
                        status = self.get_service_status()
                        active_services = len(status.get('services_initialized', []))
                        uptime = status.get('service_uptime', 'Unknown')
                        logger.info(f"🔄 Service status: {active_services} services active, uptime: {uptime}")
                    except Exception as e:
                        logger.error(f"❌ Status reporter error: {e}")
            
            # Start background reporter
            reporter_task = asyncio.create_task(status_reporter())
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
            # Cancel reporter task
            reporter_task.cancel()
            try:
                await reporter_task
            except asyncio.CancelledError:
                pass
                
        except KeyboardInterrupt:
            logger.info("⌨️ Keyboard interrupt received")
        except Exception as e:
            logger.error(f"❌ Daemon error: {e}")
        finally:
            await self.stop_service()
    
    async def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        if not self.integration:
            return {"status": "error", "message": "Integration not initialized"}
        
        try:
            # Use the MCP manager for testing
            if hasattr(self.integration, 'mcp_manager') and self.integration.mcp_manager:
                test_results = await self.integration.mcp_manager.test_all_systems()
                
                all_healthy = all(result.get("success", False) for result in test_results.values())
                
                return {
                    "status": "healthy" if all_healthy else "unhealthy",
                    "timestamp": time.time(),
                    "tests": test_results,
                    "service_status": self.get_service_status()
                }
            else:
                return {
                    "status": "partial",
                    "message": "MCP manager not available",
                    "service_status": self.get_service_status()
                }
                
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return {
                "status": "error", 
                "error": str(e),
                "service_status": self.get_service_status()
            }

def setup_signal_handlers(service: OMEGAMCPService):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"🛑 Received signal {signum}")
        asyncio.create_task(service.stop_service())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main service entry point"""
    parser = argparse.ArgumentParser(description="OMEGA AI MCP Service Manager")
    parser.add_argument("action", choices=["start", "stop", "restart", "status", "health", "test"],
                       help="Service action to perform")
    parser.add_argument("--config", help="Path to MCP configuration file")
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode")
    parser.add_argument("--output", choices=["json", "text"], default="text", help="Output format")
    
    args = parser.parse_args()
    
    # Create service instance
    service = OMEGAMCPService()
    setup_signal_handlers(service)
    
    try:
        if args.action == "start":
            success = await service.start_service(args.config, args.daemon)
            if not success:
                sys.exit(1)
        
        elif args.action == "stop":
            await service.stop_service()
        
        elif args.action == "restart":
            success = await service.restart_service(args.config)
            if not success:
                sys.exit(1)
        
        elif args.action == "status":
            status = service.get_service_status()
            if args.output == "json":
                print(json.dumps(status, indent=2))
            else:
                print(f"Service Running: {status.get('service_running', False)}")
                print(f"Integration Active: {status.get('integration_active', False)}")
                print(f"Services: {', '.join(status.get('services_initialized', []))}")
                if 'service_uptime' in status:
                    print(f"Uptime: {status['service_uptime']}")
        
        elif args.action == "health":
            health = await service.run_health_check()
            if args.output == "json":
                print(json.dumps(health, indent=2))
            else:
                status = health.get('status', 'unknown')
                print(f"Health Status: {status.upper()}")
                if 'tests' in health:
                    for test_name, result in health['tests'].items():
                        status_icon = "✅" if result.get('success') else "❌"
                        print(f"  {status_icon} {test_name}: {'OK' if result.get('success') else result.get('error', 'Failed')}")
        
        elif args.action == "test":
            # Initialize temporarily for testing
            if not service.integration:
                service.integration = OMEGAMCPIntegration(args.config)
                await service.integration.initialize()
            
            health = await service.run_health_check()
            if args.output == "json":
                print(json.dumps(health, indent=2))
            else:
                print("🧪 Running MCP Integration Tests...")
                if 'tests' in health:
                    for test_name, result in health['tests'].items():
                        status = "✅ PASS" if result.get('success') else "❌ FAIL"
                        error = f" - {result.get('error', '')}" if not result.get('success') else ""
                        print(f"   {status} {test_name}{error}")
                else:
                    print(f"   Status: {health.get('status', 'unknown').upper()}")
                    if 'error' in health:
                        print(f"   Error: {health['error']}")
            
            await service.stop_service()
    
    except KeyboardInterrupt:
        logger.info("⌨️ Interrupted by user")
        await service.stop_service()
    except Exception as e:
        logger.error(f"❌ Service error: {e}")
        await service.stop_service()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())