#!/usr/bin/env python3
"""
🔗 OMEGA AI MCP Integration Layer
Production-ready integration of MCP services with main OMEGA AI system
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import importlib
import signal
import traceback
from datetime import datetime

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/omega_mcp_integration.log')
    ]
)

logger = logging.getLogger(__name__)

class OMEGAMCPIntegration:
    """Main integration layer for OMEGA AI with MCPs"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/mcp_config.json"
        self.config = {}
        self.mcps = {}
        self.mcp_manager = None
        self.is_running = False
        self.startup_tasks = []
        self.shutdown_tasks = []
        
        # Create required directories
        self._create_directories()
        
        # Load configuration
        self._load_configuration()
        
        # Initialize signal handlers
        self._setup_signal_handlers()
    
    def _create_directories(self):
        """Create necessary directories for MCP operations"""
        dirs = [
            'logs',
            'data/lottery_ingestion',
            'data/mcp_cache',
            'config',
            'mcps'
        ]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def _load_configuration(self):
        """Load MCP configuration from file or create default"""
        config_file = Path(self.config_path)
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"✅ Loaded MCP configuration from {config_file}")
            except Exception as e:
                logger.error(f"❌ Failed to load MCP config: {e}")
                self.config = self._get_default_config()
        else:
            logger.info("📝 Creating default MCP configuration")
            self.config = self._get_default_config()
            self._save_configuration()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default MCP configuration"""
        return {
            "mcp_enabled": True,
            "auto_start": False,  # Requires explicit activation
            "services": {
                "lottery_data": {
                    "enabled": True,
                    "data_dir": "data/lottery_ingestion",
                    "cache_enabled": True,
                    "timeout_seconds": 30
                },
                "notifications": {
                    "enabled": True,
                    "channels": {
                        "console": True,
                        "email": False,
                        "whatsapp": False,
                        "telegram": False,
                        "discord": False
                    },
                    "rate_limiting": {
                        "max_per_minute": 10,
                        "max_per_hour": 100
                    }
                },
                "workflow_automation": {
                    "enabled": True,
                    "scheduler_timezone": "America/Lima",
                    "default_lotteries": ["kabala_pe"],
                    "monitoring_interval": 60
                }
            },
            "integration": {
                "omega_api_base": "http://localhost:8000",
                "prediction_integration": True,
                "result_caching": True,
                "error_notifications": True
            },
            "health_checks": {
                "enabled": True,
                "interval_seconds": 300,
                "alert_on_failure": True
            }
        }
    
    def _save_configuration(self):
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"💾 Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save configuration: {e}")
    
    def _setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers"""
        def signal_handler(signum, frame):
            logger.info(f"🛑 Received signal {signum}, shutting down...")
            if self.is_running:
                asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize(self, credentials: Optional[Dict[str, str]] = None) -> bool:
        """Initialize MCP services"""
        if not self.config.get("mcp_enabled", True):
            logger.info("📴 MCP services disabled in configuration")
            return False
        
        try:
            logger.info("🚀 Initializing OMEGA MCP Integration...")
            
            # Load credentials
            if not credentials:
                credentials = self._load_credentials()
            
            # Import and initialize MCP modules
            await self._initialize_mcps(credentials)
            
            # Setup health monitoring if enabled
            if self.config.get("health_checks", {}).get("enabled", True):
                await self._setup_health_monitoring()
            
            logger.info("✅ OMEGA MCP Integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize MCP integration: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def _load_credentials(self) -> Dict[str, str]:
        """Load credentials from various sources"""
        credentials = {}
        
        # 1. Try environment variables first
        env_mapping = {
            "twilio_account_sid": "TWILIO_ACCOUNT_SID",
            "twilio_auth_token": "TWILIO_AUTH_TOKEN", 
            "twilio_whatsapp_from": "TWILIO_WHATSAPP_FROM",
            "telegram_bot_token": "TELEGRAM_BOT_TOKEN",
            "discord_webhook_url": "DISCORD_WEBHOOK_URL",
            "smtp_host": "SMTP_HOST",
            "smtp_user": "SMTP_USER",
            "smtp_password": "SMTP_PASSWORD",
            "smtp_port": "SMTP_PORT",
            "omega_api_key": "OMEGA_API_KEY"
        }
        
        for key, env_var in env_mapping.items():
            value = os.getenv(env_var)
            if value:
                credentials[key] = value
        
        # 2. Try credentials file
        creds_file = Path("config/credentials.json")
        if creds_file.exists():
            try:
                with open(creds_file, 'r') as f:
                    file_creds = json.load(f)
                    # Environment variables take precedence
                    for key, value in file_creds.items():
                        if key not in credentials:
                            credentials[key] = value
            except Exception as e:
                logger.warning(f"⚠️ Failed to load credentials file: {e}")
        
        # 3. Try .env file
        env_file = Path(".env")
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_key = key.strip()
                            env_value = value.strip().strip('"\'')
                            # Convert to our internal format
                            for cred_key, env_var in env_mapping.items():
                                if env_key == env_var and cred_key not in credentials:
                                    credentials[cred_key] = env_value
            except Exception as e:
                logger.warning(f"⚠️ Failed to load .env file: {e}")
        
        logger.info(f"🔑 Loaded {len(credentials)} credential entries")
        return credentials
    
    async def _initialize_mcps(self, credentials: Dict[str, str]):
        """Initialize MCP services"""
        try:
            # Import MCP modules
            sys.path.append(str(Path(__file__).parent))
            
            from mcps.lottery_data_mcp import ProductionLotteryDataMCP
            from mcps.notification_mcp import ProductionNotificationMCP  
            from mcps.workflow_automation_mcp import ProductionWorkflowAutomationMCP
            
            # Initialize Lottery Data MCP
            if self.config["services"]["lottery_data"]["enabled"]:
                self.mcps["lottery_data"] = ProductionLotteryDataMCP(
                    data_dir=self.config["services"]["lottery_data"]["data_dir"]
                )
                logger.info("✅ Lottery Data MCP initialized")
            
            # Initialize Notification MCP
            if self.config["services"]["notifications"]["enabled"]:
                self.mcps["notifications"] = ProductionNotificationMCP(credentials)
                logger.info("✅ Notification MCP initialized")
            
            # Initialize Workflow Automation MCP
            if self.config["services"]["workflow_automation"]["enabled"]:
                self.mcps["workflow_automation"] = ProductionWorkflowAutomationMCP(
                    omega_api_base=self.config["integration"]["omega_api_base"],
                    lottery_data_mcp=self.mcps.get("lottery_data"),
                    notification_mcp=self.mcps.get("notifications")
                )
                logger.info("✅ Workflow Automation MCP initialized")
            
            # Import and initialize MCP Manager
            from scripts.run_mcps import MCPManager
            self.mcp_manager = MCPManager(credentials)
            
        except ImportError as e:
            logger.error(f"❌ Failed to import MCP modules: {e}")
            logger.error("Please ensure MCP dependencies are installed: pip install -r requirements.txt")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to initialize MCPs: {e}")
            raise
    
    async def _setup_health_monitoring(self):
        """Setup health monitoring for MCP services"""
        async def health_check():
            """Perform health checks on all MCP services"""
            try:
                health_status = {}
                
                for service_name, mcp in self.mcps.items():
                    try:
                        if hasattr(mcp, 'health_check'):
                            health_status[service_name] = await mcp.health_check()
                        else:
                            # Basic availability check
                            health_status[service_name] = {"status": "healthy", "timestamp": datetime.now().isoformat()}
                    except Exception as e:
                        health_status[service_name] = {"status": "unhealthy", "error": str(e), "timestamp": datetime.now().isoformat()}
                
                # Log overall health
                healthy_services = sum(1 for status in health_status.values() if status.get("status") == "healthy")
                total_services = len(health_status)
                
                if healthy_services == total_services:
                    logger.debug(f"💚 All {total_services} MCP services healthy")
                else:
                    logger.warning(f"⚠️ {healthy_services}/{total_services} MCP services healthy")
                    
                    # Send alert if configured
                    if self.config.get("health_checks", {}).get("alert_on_failure", True):
                        await self._send_health_alert(health_status)
                
                return health_status
                
            except Exception as e:
                logger.error(f"❌ Health check failed: {e}")
                return {}
        
        # Schedule regular health checks
        interval = self.config.get("health_checks", {}).get("interval_seconds", 300)
        self.startup_tasks.append(self._schedule_periodic_task(health_check, interval))
    
    async def _send_health_alert(self, health_status: Dict[str, Any]):
        """Send health alert notification"""
        if "notifications" in self.mcps:
            try:
                unhealthy_services = [name for name, status in health_status.items() if status.get("status") != "healthy"]
                
                message = f"🚨 OMEGA MCP Health Alert\n\nUnhealthy services: {', '.join(unhealthy_services)}\nTime: {datetime.now().isoformat()}"
                
                await self.mcps["notifications"].send_notification(
                    message=message,
                    channels=["email", "whatsapp"],  # Use configured channels
                    priority="high"
                )
            except Exception as e:
                logger.error(f"❌ Failed to send health alert: {e}")
    
    async def _schedule_periodic_task(self, task_func, interval_seconds: int):
        """Schedule a periodic task"""
        while self.is_running:
            try:
                await task_func()
            except Exception as e:
                logger.error(f"❌ Periodic task failed: {e}")
            
            await asyncio.sleep(interval_seconds)
    
    async def start(self, user_preferences: Optional[Dict[str, Any]] = None) -> bool:
        """Start MCP services"""
        if not self.mcps:
            logger.error("❌ MCPs not initialized. Call initialize() first.")
            return False
        
        if self.is_running:
            logger.warning("⚠️ MCP services already running")
            return True
        
        try:
            logger.info("🚀 Starting OMEGA MCP services...")
            self.is_running = True
            
            # Start workflow automation if available
            if "workflow_automation" in self.mcps:
                self.mcps["workflow_automation"].start()
                
                # Deploy production workflows if user preferences provided
                if user_preferences:
                    await self.mcp_manager.deploy_production_workflows(user_preferences)
            
            # Start background tasks
            for task in self.startup_tasks:
                asyncio.create_task(task)
            
            logger.info("✅ OMEGA MCP services started successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start MCP services: {e}")
            self.is_running = False
            return False
    
    async def stop(self):
        """Stop MCP services gracefully"""
        if not self.is_running:
            return
        
        logger.info("🛑 Stopping OMEGA MCP services...")
        self.is_running = False
        
        try:
            # Stop workflow automation
            if "workflow_automation" in self.mcps:
                self.mcps["workflow_automation"].shutdown()
            
            # Run shutdown tasks
            for task in self.shutdown_tasks:
                try:
                    await task
                except Exception as e:
                    logger.error(f"❌ Shutdown task failed: {e}")
            
            logger.info("✅ OMEGA MCP services stopped")
            
        except Exception as e:
            logger.error(f"❌ Error during MCP shutdown: {e}")
    
    async def shutdown(self):
        """Complete shutdown of the integration"""
        await self.stop()
        logger.info("👋 OMEGA MCP Integration shutdown complete")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of MCP services"""
        return {
            "integration_active": self.is_running,
            "services_initialized": list(self.mcps.keys()),
            "configuration": {
                "mcp_enabled": self.config.get("mcp_enabled", False),
                "auto_start": self.config.get("auto_start", False),
                "services_count": len([s for s in self.config.get("services", {}).values() if s.get("enabled", False)])
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def is_mcp_enabled(self) -> bool:
        """Check if MCP services are enabled"""
        return self.config.get("mcp_enabled", False) and bool(self.mcps)
    
    async def predict_with_mcp(self, lottery_type: str = "kabala_pe", **kwargs) -> Dict[str, Any]:
        """Make predictions using MCP integration"""
        if not self.is_running or "workflow_automation" not in self.mcps:
            raise RuntimeError("MCP services not available for predictions")
        
        try:
            # Use workflow automation to generate predictions
            test_prefs = {
                "prediction_count": kwargs.get("count", 3),
                "include_analysis": kwargs.get("analysis", True),
                "include_disclaimer": kwargs.get("disclaimer", True),
                "notification_channels": []  # Don't send notifications for API calls
            }
            
            result = await self.mcps["workflow_automation"].run_manual_cycle(lottery_type, test_prefs)
            return result
            
        except Exception as e:
            logger.error(f"❌ MCP prediction failed: {e}")
            raise

# Global integration instance
_omega_mcp = None

def get_omega_mcp_integration() -> OMEGAMCPIntegration:
    """Get global MCP integration instance"""
    global _omega_mcp
    if _omega_mcp is None:
        _omega_mcp = OMEGAMCPIntegration()
    return _omega_mcp

async def initialize_mcp_integration(credentials: Optional[Dict[str, str]] = None, 
                                   user_preferences: Optional[Dict[str, Any]] = None) -> bool:
    """Initialize and optionally start MCP integration"""
    integration = get_omega_mcp_integration()
    
    # Initialize
    if not await integration.initialize(credentials):
        return False
    
    # Auto-start if configured
    if integration.config.get("auto_start", False) or user_preferences:
        return await integration.start(user_preferences)
    
    return True

async def shutdown_mcp_integration():
    """Shutdown MCP integration"""
    global _omega_mcp
    if _omega_mcp:
        await _omega_mcp.shutdown()
        _omega_mcp = None

if __name__ == "__main__":
    """CLI interface for MCP integration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OMEGA AI MCP Integration")
    parser.add_argument("--action", choices=["start", "stop", "status", "test"], 
                       default="start", help="Action to perform")
    parser.add_argument("--config", help="Path to MCP configuration file")
    parser.add_argument("--auto-start", action="store_true", help="Auto-start services after initialization")
    
    args = parser.parse_args()
    
    async def main():
        integration = OMEGAMCPIntegration(args.config)
        
        if args.action == "status":
            status = integration.get_status()
            print(json.dumps(status, indent=2))
            return
        
        # Initialize
        if not await integration.initialize():
            print("❌ Failed to initialize MCP integration")
            return
        
        if args.action == "start" or args.auto_start:
            # Start services
            success = await integration.start()
            if success:
                print("✅ MCP services started. Press Ctrl+C to stop.")
                try:
                    while True:
                        await asyncio.sleep(60)
                        status = integration.get_status()
                        print(f"🔄 Status: {status['services_initialized']} services running")
                except KeyboardInterrupt:
                    print("\n🛑 Stopping services...")
            else:
                print("❌ Failed to start MCP services")
        
        elif args.action == "test":
            # Run tests
            if integration.mcp_manager:
                test_results = await integration.mcp_manager.test_all_systems()
                print("📊 Test Results:")
                for system, result in test_results.items():
                    status = "✅" if result.get("success") else "❌"
                    print(f"   {status} {system}: {'OK' if result.get('success') else result.get('error', 'Failed')}")
            else:
                print("❌ MCP manager not available for testing")
        
        await integration.shutdown()
    
    asyncio.run(main())