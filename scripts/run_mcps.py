#!/usr/bin/env python3
"""
🔗 OMEGA MCPs Integration Script
Production deployment and testing of all MCPs
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from mcps.lottery_data_mcp import ProductionLotteryDataMCP
from mcps.notification_mcp import ProductionNotificationMCP  
from mcps.workflow_automation_mcp import ProductionWorkflowAutomationMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/mcp_operations.log')
    ]
)

logger = logging.getLogger(__name__)

class MCPManager:
    """Manager para coordinar todos los MCPs"""
    
    def __init__(self, credentials: Dict[str, str]):
        self.credentials = credentials
        
        # Initialize MCPs
        self.lottery_mcp = ProductionLotteryDataMCP(data_dir="data/lottery_ingestion")
        self.notification_mcp = ProductionNotificationMCP(credentials)
        self.workflow_mcp = ProductionWorkflowAutomationMCP(
            omega_api_base=os.getenv("OMEGA_API_BASE", "http://localhost:8000"),
            lottery_data_mcp=self.lottery_mcp,
            notification_mcp=self.notification_mcp
        )
        
        logger.info("🚀 MCP Manager initialized")
    
    async def test_all_systems(self) -> Dict[str, Any]:
        """Test completo de todos los sistemas"""
        
        results = {}
        
        # 1. Test Lottery Data MCP
        logger.info("🎰 Testing Lottery Data MCP...")
        try:
            # Test fetch de cada lotería
            lottery_results = await self.lottery_mcp.bulk_fetch_all_lotteries()
            
            results["lottery_data"] = {
                "success": True,
                "supported_lotteries": self.lottery_mcp.get_supported_lotteries(),
                "fetch_results": lottery_results,
                "cache_stats": self.lottery_mcp.get_cache_stats()
            }
            
        except Exception as e:
            results["lottery_data"] = {"success": False, "error": str(e)}
        
        # 2. Test Notification MCP
        logger.info("📨 Testing Notification MCP...")
        try:
            # Test channels
            channel_test = await self.notification_mcp.test_channels()
            delivery_stats = self.notification_mcp.get_delivery_stats()
            
            results["notifications"] = {
                "success": True,
                "channel_tests": channel_test,
                "delivery_stats": delivery_stats
            }
            
        except Exception as e:
            results["notifications"] = {"success": False, "error": str(e)}
        
        # 3. Test Workflow Automation MCP
        logger.info("🤖 Testing Workflow Automation MCP...")
        try:
            # Start scheduler
            self.workflow_mcp.start()
            
            # Test manual cycle
            test_prefs = {
                "notification_channels": ["whatsapp"],
                "contact_info": {"whatsapp": self.credentials.get("test_whatsapp")},
                "prediction_count": 3,
                "include_analysis": True
            }
            
            # Test with Kabala (most reliable)
            manual_result = await self.workflow_mcp.run_manual_cycle("kabala_pe", test_prefs)
            
            # Get workflow stats
            workflow_stats = self.workflow_mcp.get_workflow_stats()
            
            results["workflow_automation"] = {
                "success": True,
                "manual_test": manual_result,
                "stats": workflow_stats,
                "scheduled_jobs": self.workflow_mcp.get_scheduled_jobs()
            }
            
        except Exception as e:
            results["workflow_automation"] = {"success": False, "error": str(e)}
        
        return results
    
    async def deploy_production_workflows(self, user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Desplegar workflows de producción"""
        
        logger.info("🚀 Deploying production workflows...")
        
        # Start scheduler
        self.workflow_mcp.start()
        
        # Schedule default lotteries
        job_ids = self.workflow_mcp.schedule_all_default_lotteries(user_preferences)
        
        # Setup monitoring
        monitoring_job = self.workflow_mcp.setup_monitoring_job(check_interval_minutes=60)
        
        # Schedule summary report (daily)
        summary_job_id = await self._schedule_daily_summary(user_preferences)
        
        deployment_info = {
            "scheduler_started": True,
            "lottery_jobs": job_ids,
            "monitoring_job": monitoring_job,
            "summary_job": summary_job_id,
            "total_jobs": len(job_ids) + 2,  # +monitoring +summary
            "deployment_time": asyncio.get_event_loop().time()
        }
        
        logger.info(f"✅ Production deployment completed: {len(job_ids)} lottery jobs + 2 system jobs")
        
        return deployment_info
    
    async def _schedule_daily_summary(self, user_prefs: Dict[str, Any]) -> str:
        """Schedule daily summary report"""
        
        async def daily_summary_task():
            try:
                # Collect stats from all MCPs
                lottery_stats = self.lottery_mcp.get_cache_stats()
                notification_stats = self.notification_mcp.get_delivery_stats()
                workflow_stats = self.workflow_mcp.get_workflow_stats()
                
                # Format summary message
                message = f"""📊 OMEGA AI Daily Summary
                
🎰 Lottery Data:
   - Supported: {len(lottery_stats['supported_lotteries'])} lotteries
   - Cache entries: {lottery_stats['cache_entries']}
   
📨 Notifications:
   - Channels: {len(notification_stats['available_channels'])}
   - Failed deliveries: {notification_stats['failed_deliveries_count']}
   
🤖 Workflows:
   - Scheduled jobs: {workflow_stats['scheduled_jobs']}
   - Success rate (24h): {workflow_stats['success_rate_24h']:.1f}%
   - Executions (24h): {workflow_stats['executions_last_24h']}
   
Generated: {asyncio.get_event_loop().time()}"""
                
                # Send summary
                await self.notification_mcp.send_notification(
                    message=message,
                    channels=user_prefs.get("summary_channels", ["email"]),
                    recipients=user_prefs.get("contact_info", {}),
                    priority="normal"
                )
                
                logger.info("📊 Daily summary sent")
                
            except Exception as e:
                logger.error(f"Daily summary task failed: {e}")
        
        # Schedule for 9 AM daily
        job_id = "daily_summary"
        
        self.workflow_mcp.scheduler.add_job(
            daily_summary_task,
            trigger="cron",
            hour=9,
            minute=0,
            id=job_id,
            replace_existing=True
        )
        
        return job_id
    
    def shutdown(self):
        """Shutdown graceful de todos los MCPs"""
        logger.info("🛑 Shutting down MCPs...")
        
        try:
            self.workflow_mcp.shutdown()
            logger.info("✅ All MCPs shut down gracefully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

def load_credentials() -> Dict[str, str]:
    """Cargar credenciales desde archivo o variables de entorno"""
    
    credentials = {}
    
    # Try to load from credentials.json
    creds_file = Path("config/credentials.json")
    if creds_file.exists():
        with open(creds_file) as f:
            credentials.update(json.load(f))
    
    # Override with environment variables
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
        "test_whatsapp": "TEST_WHATSAPP",
        "test_telegram_chat_id": "TEST_TELEGRAM_CHAT_ID",
        "test_email": "TEST_EMAIL"
    }
    
    for key, env_var in env_mapping.items():
        if os.getenv(env_var):
            credentials[key] = os.getenv(env_var)
    
    return credentials

async def main():
    """Función principal"""
    
    print("🚀 OMEGA MCPs Integration Starting...")
    
    # Load credentials
    credentials = load_credentials()
    
    if not credentials:
        print("❌ No credentials found. Please set environment variables or create config/credentials.json")
        return
    
    print(f"✅ Loaded {len(credentials)} credential entries")
    
    # Initialize MCP Manager
    manager = MCPManager(credentials)
    
    try:
        # Run tests
        print("\n🧪 Running system tests...")
        test_results = await manager.test_all_systems()
        
        print("\n📊 Test Results:")
        for system, result in test_results.items():
            status = "✅" if result.get("success") else "❌"
            print(f"   {status} {system}: {'OK' if result.get('success') else result.get('error', 'Failed')}")
        
        # Deploy production workflows if tests passed
        all_passed = all(result.get("success", False) for result in test_results.values())
        
        if all_passed:
            print("\n🚀 All tests passed! Deploying production workflows...")
            
            # Production user preferences
            user_prefs = {
                "notification_channels": ["whatsapp", "telegram"],
                "contact_info": {
                    "whatsapp": credentials.get("test_whatsapp"),
                    "telegram": credentials.get("test_telegram_chat_id"),
                    "email": credentials.get("test_email")
                },
                "prediction_count": 5,
                "include_analysis": True,
                "include_disclaimer": True,
                "risk_profile": "balanced",
                "summary_channels": ["email"],
                "error_notification_channels": ["whatsapp", "email"]
            }
            
            deployment_result = await manager.deploy_production_workflows(user_prefs)
            
            print(f"\n✅ Production deployment completed!")
            print(f"   📅 Scheduled {deployment_result['total_jobs']} jobs")
            print(f"   🎰 Lottery jobs: {len(deployment_result['lottery_jobs'])}")
            print(f"   📊 Monitoring: Active")
            
            # Show scheduled jobs
            scheduled_jobs = manager.workflow_mcp.get_scheduled_jobs()
            print(f"\n📅 Scheduled Jobs:")
            for job in scheduled_jobs:
                next_run = job.get('next_run', 'Not scheduled')
                lottery = job.get('lottery_id', 'System job')
                print(f"   • {job['id'][:12]}... [{lottery}] -> Next: {next_run}")
            
            print(f"\n🎯 MCPs are now running autonomously!")
            print(f"   📱 You'll receive notifications according to lottery schedules")
            print(f"   📊 Daily summaries at 9 AM")
            print(f"   🔍 Monitor logs: data/mcp_operations.log")
            
            # Keep running
            print(f"\n⏸️  Press Ctrl+C to stop...")
            
            try:
                while True:
                    await asyncio.sleep(300)  # Check every 5 minutes
                    
                    # Print status update
                    stats = manager.workflow_mcp.get_workflow_stats()
                    print(f"🔄 Status: {stats['scheduled_jobs']} jobs, {stats['executions_last_24h']} executions (24h), {stats['success_rate_24h']:.1f}% success")
                    
            except KeyboardInterrupt:
                print(f"\n🛑 Stopping MCPs...")
                
        else:
            print(f"\n❌ Some tests failed. Please check configuration and try again.")
            
            # Show specific errors
            for system, result in test_results.items():
                if not result.get("success"):
                    print(f"   {system}: {result.get('error', 'Unknown error')}")
    
    finally:
        manager.shutdown()
        print(f"👋 MCPs stopped. Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())