#!/usr/bin/env python3
"""
🧪 OMEGA AI MCP Integration Test Runner
Comprehensive test suite runner for MCP services with detailed reporting
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class MCPIntegrationTestRunner:
    """Comprehensive test runner for MCP integration"""
    
    def __init__(self):
        self.test_results = []
        self.test_start_time = None
        self.test_suite_results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }
    
    def log_test_result(self, test_name: str, success: bool, message: str, duration: float = 0, error: str = None):
        """Log individual test result"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "duration_ms": duration * 1000,
            "timestamp": datetime.now().isoformat(),
            "error": error
        }
        
        self.test_results.append(result)
        
        if success:
            self.test_suite_results["passed"] += 1
            icon = "✅"
        else:
            self.test_suite_results["failed"] += 1
            icon = "❌"
            if error:
                self.test_suite_results["errors"].append(f"{test_name}: {error}")
        
        logger.info(f"{icon} {test_name}: {message} ({duration*1000:.1f}ms)")
    
    def skip_test(self, test_name: str, reason: str):
        """Skip a test with reason"""
        self.test_suite_results["skipped"] += 1
        logger.info(f"⏭️ {test_name}: SKIPPED - {reason}")
    
    async def test_mcp_availability(self) -> bool:
        """Test if MCP integration is available"""
        start_time = time.time()
        test_name = "MCP Integration Availability"
        
        try:
            from omega_mcp_integration import OMEGAMCPIntegration, get_omega_mcp_integration
            
            # Test basic import
            integration = get_omega_mcp_integration()
            
            self.log_test_result(
                test_name, 
                True, 
                "MCP integration modules loaded successfully",
                time.time() - start_time
            )
            return True
            
        except ImportError as e:
            self.log_test_result(
                test_name, 
                False, 
                "MCP integration not available", 
                time.time() - start_time,
                str(e)
            )
            return False
        except Exception as e:
            self.log_test_result(
                test_name, 
                False, 
                "Unexpected error testing MCP availability", 
                time.time() - start_time,
                str(e)
            )
            return False
    
    async def test_mcp_dependencies(self) -> bool:
        """Test MCP dependencies availability"""
        start_time = time.time()
        test_name = "MCP Dependencies Check"
        
        try:
            required_modules = [
                "apscheduler",
                "twilio", 
                "bs4",  # beautifulsoup4
                "yaml",  # pyyaml
                "aiofiles"
            ]
            
            missing_modules = []
            for module in required_modules:
                try:
                    __import__(module)
                except ImportError:
                    missing_modules.append(module)
            
            if missing_modules:
                self.log_test_result(
                    test_name,
                    False,
                    f"Missing required modules: {', '.join(missing_modules)}",
                    time.time() - start_time,
                    f"Install with: pip install {' '.join(missing_modules)}"
                )
                return False
            else:
                self.log_test_result(
                    test_name,
                    True,
                    f"All {len(required_modules)} required modules available",
                    time.time() - start_time
                )
                return True
                
        except Exception as e:
            self.log_test_result(
                test_name,
                False,
                "Error checking dependencies",
                time.time() - start_time,
                str(e)
            )
            return False
    
    async def test_mcp_configuration(self) -> bool:
        """Test MCP configuration loading and validation"""
        start_time = time.time()
        test_name = "MCP Configuration"
        
        try:
            from omega_mcp_integration import OMEGAMCPIntegration
            
            # Test default configuration
            integration = OMEGAMCPIntegration()
            config = integration.config
            
            # Validate required configuration keys
            required_keys = ["mcp_enabled", "services", "integration", "health_checks"]
            missing_keys = [key for key in required_keys if key not in config]
            
            if missing_keys:
                self.log_test_result(
                    test_name,
                    False,
                    f"Missing configuration keys: {missing_keys}",
                    time.time() - start_time
                )
                return False
            
            # Validate services configuration
            required_services = ["lottery_data", "notifications", "workflow_automation"]
            services = config.get("services", {})
            missing_services = [svc for svc in required_services if svc not in services]
            
            if missing_services:
                self.log_test_result(
                    test_name,
                    False,
                    f"Missing service configurations: {missing_services}",
                    time.time() - start_time
                )
                return False
            
            self.log_test_result(
                test_name,
                True,
                f"Configuration valid with {len(services)} services configured",
                time.time() - start_time
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                test_name,
                False,
                "Configuration test failed",
                time.time() - start_time,
                str(e)
            )
            return False
    
    async def test_mcp_initialization(self) -> Tuple[bool, Any]:
        """Test MCP integration initialization"""
        start_time = time.time()
        test_name = "MCP Integration Initialization"
        
        try:
            from omega_mcp_integration import OMEGAMCPIntegration
            
            integration = OMEGAMCPIntegration()
            
            # Test initialization (should work even without credentials)
            init_success = await integration.initialize()
            
            if init_success:
                self.log_test_result(
                    test_name,
                    True,
                    "MCP integration initialized successfully",
                    time.time() - start_time
                )
                return True, integration
            else:
                self.log_test_result(
                    test_name,
                    False,
                    "MCP integration initialization failed",
                    time.time() - start_time,
                    "Check logs for initialization errors"
                )
                return False, None
                
        except Exception as e:
            self.log_test_result(
                test_name,
                False,
                "MCP integration initialization error",
                time.time() - start_time,
                str(e)
            )
            return False, None
    
    async def test_mcp_status_reporting(self, integration) -> bool:
        """Test MCP status reporting functionality"""
        start_time = time.time()
        test_name = "MCP Status Reporting"
        
        try:
            if not integration:
                self.skip_test(test_name, "Integration not available")
                return False
            
            status = integration.get_status()
            
            # Validate status structure
            required_status_keys = ["integration_active", "services_initialized", "configuration", "timestamp"]
            missing_keys = [key for key in required_status_keys if key not in status]
            
            if missing_keys:
                self.log_test_result(
                    test_name,
                    False,
                    f"Status missing keys: {missing_keys}",
                    time.time() - start_time
                )
                return False
            
            services_count = len(status.get("services_initialized", []))
            
            self.log_test_result(
                test_name,
                True,
                f"Status reporting works, {services_count} services initialized",
                time.time() - start_time
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                test_name,
                False,
                "Status reporting test failed",
                time.time() - start_time,
                str(e)
            )
            return False
    
    async def test_mcp_service_health_checks(self, integration) -> bool:
        """Test MCP service health checks"""
        start_time = time.time()
        test_name = "MCP Service Health Checks"
        
        try:
            if not integration:
                self.skip_test(test_name, "Integration not available")
                return False
            
            # Test health monitoring
            from scripts.omega_mcp_health_monitor import OMEGAMCPHealthMonitor
            
            health_monitor = OMEGAMCPHealthMonitor()
            health_results = await health_monitor.run_all_health_checks()
            
            if health_results:
                healthy_services = sum(1 for result in health_results.values() if result.status == "healthy")
                total_services = len(health_results)
                
                self.log_test_result(
                    test_name,
                    True,
                    f"Health checks completed: {healthy_services}/{total_services} services healthy",
                    time.time() - start_time
                )
                return True
            else:
                self.log_test_result(
                    test_name,
                    False,
                    "No health check results returned",
                    time.time() - start_time
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                test_name,
                False,
                "Health checks test failed",
                time.time() - start_time,
                str(e)
            )
            return False
    
    async def test_mcp_service_scripts(self) -> bool:
        """Test MCP service management scripts"""
        start_time = time.time()
        test_name = "MCP Service Management Scripts"
        
        try:
            # Check if service scripts exist
            script_dir = Path(__file__).parent
            required_scripts = [
                "omega_mcp_service.py",
                "start_omega_mcp.sh",
                "stop_omega_mcp.sh",
                "restart_omega_mcp.sh"
            ]
            
            missing_scripts = []
            for script in required_scripts:
                script_path = script_dir / script
                if not script_path.exists():
                    missing_scripts.append(script)
            
            if missing_scripts:
                self.log_test_result(
                    test_name,
                    False,
                    f"Missing service scripts: {missing_scripts}",
                    time.time() - start_time
                )
                return False
            
            # Test if shell scripts are executable
            shell_scripts = [f for f in required_scripts if f.endswith('.sh')]
            non_executable = []
            for script in shell_scripts:
                script_path = script_dir / script
                if not os.access(script_path, os.X_OK):
                    non_executable.append(script)
            
            if non_executable:
                self.log_test_result(
                    test_name,
                    False,
                    f"Scripts not executable: {non_executable}",
                    time.time() - start_time,
                    "Run: chmod +x scripts/*.sh"
                )
                return False
            
            self.log_test_result(
                test_name,
                True,
                f"All {len(required_scripts)} service scripts available and properly configured",
                time.time() - start_time
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                test_name,
                False,
                "Service scripts test failed",
                time.time() - start_time,
                str(e)
            )
            return False
    
    async def test_mcp_configuration_files(self) -> bool:
        """Test MCP configuration files"""
        start_time = time.time()
        test_name = "MCP Configuration Files"
        
        try:
            project_root = Path(__file__).parent.parent
            config_files = [
                "config/mcp_config.json",
                "config/credentials.example.json",
                "config/user_preferences.example.json",
                ".env.mcp.template"
            ]
            
            issues = []
            for config_file in config_files:
                file_path = project_root / config_file
                if not file_path.exists():
                    issues.append(f"Missing: {config_file}")
                else:
                    try:
                        if config_file.endswith('.json'):
                            with open(file_path, 'r') as f:
                                json.load(f)
                    except json.JSONDecodeError as e:
                        issues.append(f"Invalid JSON in {config_file}: {e}")
            
            if issues:
                self.log_test_result(
                    test_name,
                    False,
                    f"Configuration file issues: {'; '.join(issues)}",
                    time.time() - start_time
                )
                return False
            
            self.log_test_result(
                test_name,
                True,
                f"All {len(config_files)} configuration files valid",
                time.time() - start_time
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                test_name,
                False,
                "Configuration files test failed",
                time.time() - start_time,
                str(e)
            )
            return False
    
    async def test_mcp_integration_with_main(self) -> bool:
        """Test MCP integration with main OMEGA system"""
        start_time = time.time()
        test_name = "MCP Integration with Main System"
        
        try:
            # Check if MCP integration is properly added to main.py
            main_file = Path(__file__).parent.parent / "main.py"
            
            if not main_file.exists():
                self.log_test_result(
                    test_name,
                    False,
                    "main.py not found",
                    time.time() - start_time
                )
                return False
            
            with open(main_file, 'r') as f:
                main_content = f.read()
            
            # Check for MCP imports
            mcp_imports = [
                "from omega_mcp_integration import",
                "MCP_INTEGRATION_AVAILABLE"
            ]
            
            missing_imports = []
            for import_line in mcp_imports:
                if import_line not in main_content:
                    missing_imports.append(import_line)
            
            if missing_imports:
                self.log_test_result(
                    test_name,
                    False,
                    f"Missing MCP imports in main.py: {missing_imports}",
                    time.time() - start_time
                )
                return False
            
            # Check for MCP arguments
            mcp_args = [
                "--enable-mcp",
                "--mcp-config",
                "--mcp-notify"
            ]
            
            missing_args = []
            for arg in mcp_args:
                if arg not in main_content:
                    missing_args.append(arg)
            
            if missing_args:
                self.log_test_result(
                    test_name,
                    False,
                    f"Missing MCP arguments in main.py: {missing_args}",
                    time.time() - start_time
                )
                return False
            
            self.log_test_result(
                test_name,
                True,
                "MCP integration properly integrated with main system",
                time.time() - start_time
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                test_name,
                False,
                "Main system integration test failed",
                time.time() - start_time,
                str(e)
            )
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all MCP integration tests"""
        self.test_start_time = time.time()
        
        logger.info("🧪 Starting OMEGA AI MCP Integration Test Suite...")
        logger.info("="*60)
        
        # Test 1: MCP Availability
        mcp_available = await self.test_mcp_availability()
        
        # Test 2: Dependencies
        deps_available = await self.test_mcp_dependencies()
        
        # Test 3: Configuration Files
        await self.test_mcp_configuration_files()
        
        # Test 4: Service Scripts
        await self.test_mcp_service_scripts()
        
        # Test 5: Main System Integration
        await self.test_mcp_integration_with_main()
        
        # Skip remaining tests if MCP not available or dependencies missing
        if not mcp_available or not deps_available:
            self.skip_test("MCP Configuration Test", "MCP or dependencies not available")
            self.skip_test("MCP Initialization Test", "MCP or dependencies not available")
            self.skip_test("MCP Status Reporting Test", "MCP or dependencies not available")
            self.skip_test("MCP Health Checks Test", "MCP or dependencies not available")
        else:
            # Test 6: Configuration
            await self.test_mcp_configuration()
            
            # Test 7: Initialization
            init_success, integration = await self.test_mcp_initialization()
            
            # Test 8: Status Reporting
            await self.test_mcp_status_reporting(integration)
            
            # Test 9: Health Checks
            await self.test_mcp_service_health_checks(integration)
        
        # Generate final report
        return self.generate_test_report()
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_duration = time.time() - self.test_start_time if self.test_start_time else 0
        
        # Calculate success rate
        total_tests = self.test_suite_results["passed"] + self.test_suite_results["failed"]
        success_rate = (self.test_suite_results["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": self.test_suite_results["passed"],
                "failed": self.test_suite_results["failed"],
                "skipped": self.test_suite_results["skipped"],
                "success_rate": success_rate,
                "total_duration_seconds": total_duration,
                "timestamp": datetime.now().isoformat()
            },
            "test_results": self.test_results,
            "errors": self.test_suite_results["errors"],
            "recommendations": self.generate_recommendations()
        }
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        failed_tests = [r for r in self.test_results if not r["success"]]
        
        if not failed_tests:
            recommendations.append("✅ All tests passed! MCP integration is ready for use.")
            recommendations.append("💡 You can now start MCP services with: scripts/start_omega_mcp.sh")
        else:
            recommendations.append("🔧 Address the following issues to complete MCP integration:")
            
            for test in failed_tests:
                if "dependencies" in test["test_name"].lower():
                    recommendations.append("📦 Install missing dependencies with: pip install -r requirements.txt")
                elif "configuration" in test["test_name"].lower():
                    recommendations.append("⚙️ Check and fix configuration files in config/ directory")
                elif "scripts" in test["test_name"].lower():
                    recommendations.append("🔐 Make scripts executable with: chmod +x scripts/*.sh")
                elif "credentials" in test["test_name"].lower():
                    recommendations.append("🔑 Set up credentials in config/credentials.json or environment variables")
        
        return recommendations
    
    def print_test_report(self, report: Dict[str, Any]):
        """Print formatted test report"""
        summary = report["summary"]
        
        print("\n" + "="*60)
        print("🧪 OMEGA AI MCP Integration Test Report")
        print("="*60)
        
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   ✅ Passed: {summary['passed']}")
        print(f"   ❌ Failed: {summary['failed']}")
        print(f"   ⏭️ Skipped: {summary['skipped']}")
        print(f"   📈 Success Rate: {summary['success_rate']:.1f}%")
        print(f"   ⏱️ Duration: {summary['total_duration_seconds']:.2f}s")
        
        if report["errors"]:
            print(f"\n❌ Errors:")
            for error in report["errors"]:
                print(f"   • {error}")
        
        print(f"\n💡 Recommendations:")
        for rec in report["recommendations"]:
            print(f"   {rec}")
        
        print(f"\n⏰ Report generated: {summary['timestamp']}")
        print("="*60)

async def main():
    """Main test runner function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OMEGA AI MCP Integration Test Runner")
    parser.add_argument("--output", choices=["json", "text"], default="text", help="Output format")
    parser.add_argument("--save-report", help="Save report to file")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run tests
    runner = MCPIntegrationTestRunner()
    report = await runner.run_all_tests()
    
    # Output report
    if args.output == "json":
        print(json.dumps(report, indent=2))
    else:
        runner.print_test_report(report)
    
    # Save report if requested
    if args.save_report:
        with open(args.save_report, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n💾 Report saved to: {args.save_report}")
    
    # Exit with appropriate code
    success = report["summary"]["failed"] == 0
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())