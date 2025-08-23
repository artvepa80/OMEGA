#!/usr/bin/env python3
"""
OMEGA AI Deployment Safety Automation
Deployment Engineer Implementation for Safe /results/ Integration

This script provides automated safety measures for integrating /results/ folder
components without breaking the existing production system.
"""

import os
import sys
import json
import shutil
import subprocess
import time
import requests
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/deployment_safety.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SafetyCheckResult:
    """Results from a safety check"""
    check_name: str
    status: str  # 'pass', 'fail', 'warning'
    message: str
    details: Dict[str, Any]
    timestamp: str

@dataclass
class DeploymentSnapshot:
    """Snapshot of system state before deployment"""
    timestamp: str
    git_commit: str
    file_checksums: Dict[str, str]
    environment_vars: Dict[str, str]
    running_processes: List[str]
    api_health: Dict[str, Any]
    resource_usage: Dict[str, float]

class DeploymentSafetyManager:
    """Comprehensive deployment safety management"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.results_path = self.project_root / "results"
        self.backup_path = self.project_root / "deployment_backups"
        self.logs_path = self.project_root / "logs"
        
        # Ensure directories exist
        self.logs_path.mkdir(exist_ok=True)
        self.backup_path.mkdir(exist_ok=True)
        
        # Critical files to monitor
        self.critical_files = [
            "main.py",
            "api_simple.py", 
            "core/consensus_engine.py",
            "core/predictor.py",
            "deploy/production-akash-secure.yaml",
            "requirements.txt"
        ]
        
        # Dangerous patterns in /results/ files
        self.dangerous_patterns = [
            "from main import",
            "import main",
            "os.system(",
            "subprocess.call(",
            "exec(",
            "eval("
        ]
        
        # Production API endpoints to protect
        self.production_endpoints = [
            "/health",
            "/predict", 
            "/status",
            "/"
        ]
        
        logger.info("🛡️ Deployment Safety Manager initialized")
    
    def create_system_snapshot(self) -> DeploymentSnapshot:
        """Create complete system snapshot for rollback capability"""
        logger.info("📸 Creating system snapshot...")
        
        # Get git commit
        try:
            git_commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], 
                text=True
            ).strip()
        except subprocess.CalledProcessError:
            git_commit = "unknown"
        
        # Calculate file checksums
        file_checksums = {}
        for file_path in self.critical_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                with open(full_path, 'rb') as f:
                    content = f.read()
                    file_checksums[file_path] = hashlib.sha256(content).hexdigest()
        
        # Environment variables
        env_vars = {k: v for k, v in os.environ.items() 
                   if k.startswith(('OMEGA_', 'PORT', 'ENVIRONMENT'))}
        
        # Running processes
        try:
            ps_output = subprocess.check_output(
                ["ps", "aux"], text=True
            )
            processes = [line for line in ps_output.split('\n') 
                        if 'python' in line or 'omega' in line]
        except subprocess.CalledProcessError:
            processes = []
        
        # API health
        api_health = self._check_api_health()
        
        # Resource usage
        resource_usage = self._get_resource_usage()
        
        snapshot = DeploymentSnapshot(
            timestamp=datetime.now().isoformat(),
            git_commit=git_commit,
            file_checksums=file_checksums,
            environment_vars=env_vars,
            running_processes=processes,
            api_health=api_health,
            resource_usage=resource_usage
        )
        
        # Save snapshot
        snapshot_file = self.backup_path / f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(snapshot_file, 'w') as f:
            json.dump(asdict(snapshot), f, indent=2)
        
        logger.info(f"✅ System snapshot saved to {snapshot_file}")
        return snapshot
    
    def analyze_results_conflicts(self) -> List[SafetyCheckResult]:
        """Analyze /results/ folder for potential conflicts"""
        logger.info("🔍 Analyzing /results/ folder for conflicts...")
        
        results = []
        
        if not self.results_path.exists():
            results.append(SafetyCheckResult(
                check_name="results_folder_existence",
                status="pass",
                message="/results/ folder does not exist - no conflicts",
                details={},
                timestamp=datetime.now().isoformat()
            ))
            return results
        
        # Check for dangerous imports
        dangerous_imports = self._check_dangerous_imports()
        if dangerous_imports:
            results.append(SafetyCheckResult(
                check_name="dangerous_imports",
                status="fail",
                message=f"Found {len(dangerous_imports)} dangerous import patterns",
                details={"dangerous_imports": dangerous_imports},
                timestamp=datetime.now().isoformat()
            ))
        
        # Check for API endpoint conflicts  
        api_conflicts = self._check_api_conflicts()
        if api_conflicts:
            results.append(SafetyCheckResult(
                check_name="api_conflicts",
                status="fail", 
                message=f"Found {len(api_conflicts)} API endpoint conflicts",
                details={"conflicts": api_conflicts},
                timestamp=datetime.now().isoformat()
            ))
        
        # Check for environment variable conflicts
        env_conflicts = self._check_environment_conflicts()
        if env_conflicts:
            results.append(SafetyCheckResult(
                check_name="environment_conflicts",
                status="warning",
                message=f"Found {len(env_conflicts)} environment variable conflicts", 
                details={"conflicts": env_conflicts},
                timestamp=datetime.now().isoformat()
            ))
        
        # Check for port conflicts
        port_conflicts = self._check_port_conflicts()
        if port_conflicts:
            results.append(SafetyCheckResult(
                check_name="port_conflicts",
                status="fail",
                message="Multiple services trying to use same ports",
                details={"conflicts": port_conflicts},
                timestamp=datetime.now().isoformat()
            ))
        
        # Check resource requirements
        resource_check = self._check_resource_requirements()
        results.append(resource_check)
        
        if not any(r.status == "fail" for r in results):
            results.append(SafetyCheckResult(
                check_name="overall_assessment",
                status="pass" if not any(r.status == "warning" for r in results) else "warning",
                message="No critical conflicts detected" if not any(r.status == "warning" for r in results) else "Some warnings found",
                details={"total_checks": len(results)},
                timestamp=datetime.now().isoformat()
            ))
        
        return results
    
    def _check_dangerous_imports(self) -> List[Dict[str, str]]:
        """Check for dangerous import patterns in /results/ files"""
        dangerous_imports = []
        
        for py_file in self.results_path.glob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for line_num, line in enumerate(content.split('\n'), 1):
                    for pattern in self.dangerous_patterns:
                        if pattern in line:
                            dangerous_imports.append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "line": line_num,
                                "pattern": pattern,
                                "code": line.strip()
                            })
            except Exception as e:
                logger.warning(f"Could not read {py_file}: {e}")
        
        return dangerous_imports
    
    def _check_api_conflicts(self) -> List[Dict[str, str]]:
        """Check for API endpoint conflicts"""
        conflicts = []
        
        # Find all FastAPI files
        api_files = []
        
        # Existing API files
        for pattern in ["api*.py", "main.py"]:
            api_files.extend(self.project_root.glob(pattern))
        
        # Results API files
        if self.results_path.exists():
            api_files.extend(self.results_path.glob("api*.py"))
        
        # Analyze endpoints in each file
        all_endpoints = {}
        for api_file in api_files:
            try:
                endpoints = self._extract_api_endpoints(api_file)
                for endpoint in endpoints:
                    if endpoint in all_endpoints:
                        conflicts.append({
                            "endpoint": endpoint,
                            "file1": all_endpoints[endpoint],
                            "file2": str(api_file.relative_to(self.project_root))
                        })
                    else:
                        all_endpoints[endpoint] = str(api_file.relative_to(self.project_root))
            except Exception as e:
                logger.warning(f"Could not analyze {api_file}: {e}")
        
        return conflicts
    
    def _extract_api_endpoints(self, file_path: Path) -> List[str]:
        """Extract API endpoints from a Python file"""
        endpoints = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for FastAPI route decorators
            import re
            patterns = [
                r'@app\.get\(["\']([^"\']+)["\']',
                r'@app\.post\(["\']([^"\']+)["\']',
                r'@app\.put\(["\']([^"\']+)["\']',
                r'@app\.delete\(["\']([^"\']+)["\']'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                endpoints.extend(matches)
                
        except Exception as e:
            logger.warning(f"Error extracting endpoints from {file_path}: {e}")
        
        return endpoints
    
    def _check_environment_conflicts(self) -> List[Dict[str, str]]:
        """Check for environment variable conflicts"""
        conflicts = []
        
        # Current environment variables used by the system
        current_env_vars = {
            'OMEGA_ENV', 'OMEGA_VERSION', 'PERFORMANCE_MODE',
            'PORT', 'PYTHONPATH', 'WORKERS', 'ENVIRONMENT'
        }
        
        # Check /results/ files for environment variable usage
        if self.results_path.exists():
            for py_file in self.results_path.glob("*.py"):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    import re
                    env_pattern = r'os\.getenv\(["\']([^"\']+)["\']'
                    env_vars_used = re.findall(env_pattern, content)
                    
                    for var in env_vars_used:
                        if var in current_env_vars:
                            conflicts.append({
                                "variable": var,
                                "file": str(py_file.relative_to(self.project_root)),
                                "type": "potential_override"
                            })
                            
                except Exception as e:
                    logger.warning(f"Could not check env vars in {py_file}: {e}")
        
        return conflicts
    
    def _check_port_conflicts(self) -> List[Dict[str, Any]]:
        """Check for port conflicts"""
        conflicts = []
        
        # Default port is 8000 for most services
        port_usage = {}
        
        # Check current system
        current_port = os.getenv("PORT", "8000")
        port_usage["current_system"] = current_port
        
        # Check /results/ files
        if self.results_path.exists():
            for py_file in self.results_path.glob("*.py"):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    import re
                    port_patterns = [
                        r'port\s*=\s*(\d+)',
                        r'PORT.*?(\d+)',
                        r'getenv\(["\']PORT["\'],\s*["\']?(\d+)["\']?\)'
                    ]
                    
                    for pattern in port_patterns:
                        matches = re.findall(pattern, content)
                        for port in matches:
                            if port in port_usage.values():
                                conflicts.append({
                                    "port": port,
                                    "file1": [k for k, v in port_usage.items() if v == port][0],
                                    "file2": str(py_file.relative_to(self.project_root))
                                })
                            port_usage[str(py_file.relative_to(self.project_root))] = port
                            
                except Exception as e:
                    logger.warning(f"Could not check ports in {py_file}: {e}")
        
        return conflicts
    
    def _check_resource_requirements(self) -> SafetyCheckResult:
        """Check if system can handle additional resource requirements"""
        try:
            import psutil
            
            # Current resource usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            
            # Estimated additional requirements from /results/ integration
            estimated_memory_increase = 200  # MB
            estimated_cpu_increase = 10  # percent
            
            projected_memory = memory_info.percent + (estimated_memory_increase / (memory_info.total / 1024**3)) * 100
            projected_cpu = cpu_percent + estimated_cpu_increase
            
            details = {
                "current_memory_percent": memory_info.percent,
                "current_cpu_percent": cpu_percent,
                "projected_memory_percent": projected_memory,
                "projected_cpu_percent": projected_cpu,
                "disk_usage_percent": disk_info.percent
            }
            
            if projected_memory > 85 or projected_cpu > 85:
                return SafetyCheckResult(
                    check_name="resource_requirements",
                    status="fail",
                    message="Insufficient resources for safe integration",
                    details=details,
                    timestamp=datetime.now().isoformat()
                )
            elif projected_memory > 70 or projected_cpu > 70:
                return SafetyCheckResult(
                    check_name="resource_requirements", 
                    status="warning",
                    message="Resource usage will be high after integration",
                    details=details,
                    timestamp=datetime.now().isoformat()
                )
            else:
                return SafetyCheckResult(
                    check_name="resource_requirements",
                    status="pass",
                    message="Sufficient resources available for integration",
                    details=details,
                    timestamp=datetime.now().isoformat()
                )
                
        except ImportError:
            return SafetyCheckResult(
                check_name="resource_requirements",
                status="warning",
                message="psutil not available - cannot check resource usage",
                details={},
                timestamp=datetime.now().isoformat()
            )
    
    def _check_api_health(self) -> Dict[str, Any]:
        """Check current API health"""
        health_status = {}
        
        # Try to connect to current API
        try:
            port = os.getenv("PORT", "8000")
            url = f"http://localhost:{port}/health"
            
            response = requests.get(url, timeout=5)
            health_status = {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "content": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200]
            }
        except Exception as e:
            health_status = {
                "status": "unreachable", 
                "error": str(e)
            }
        
        return health_status
    
    def _get_resource_usage(self) -> Dict[str, float]:
        """Get current resource usage"""
        try:
            import psutil
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
        except ImportError:
            return {"error": "psutil not available"}
    
    def isolate_results_folder(self) -> bool:
        """Safely isolate /results/ folder to prevent conflicts"""
        logger.info("🚧 Isolating /results/ folder...")
        
        if not self.results_path.exists():
            logger.info("✅ /results/ folder does not exist - no isolation needed")
            return True
        
        # Create isolation directory
        isolation_path = self.project_root / "integration_sandbox"
        isolation_path.mkdir(exist_ok=True)
        
        # Move /results/ contents to sandbox
        try:
            for item in self.results_path.iterdir():
                destination = isolation_path / item.name
                if item.is_dir():
                    shutil.copytree(item, destination, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, destination)
                logger.info(f"📦 Moved {item.name} to sandbox")
            
            # Create marker file
            marker_file = isolation_path / "ISOLATION_MARKER.txt"
            with open(marker_file, 'w') as f:
                f.write(f"Integration sandbox created on {datetime.now().isoformat()}\n")
                f.write("Original /results/ folder contents isolated for safe integration\n")
            
            logger.info(f"✅ /results/ folder isolated to {isolation_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to isolate /results/ folder: {e}")
            return False
    
    def create_integration_branch(self) -> bool:
        """Create safe integration branch"""
        logger.info("🌿 Creating integration branch...")
        
        try:
            # Check if we're in a git repository
            subprocess.check_output(["git", "status"], stderr=subprocess.DEVNULL)
            
            # Create and checkout integration branch
            branch_name = f"feature/results-integration-{datetime.now().strftime('%Y%m%d')}"
            subprocess.run(["git", "checkout", "-b", branch_name], check=True)
            
            # Add isolation marker
            subprocess.run(["git", "add", "integration_sandbox/"], check=True) 
            subprocess.run([
                "git", "commit", "-m", 
                "🚧 Isolate /results/ folder for safe integration"
            ], check=True)
            
            logger.info(f"✅ Created integration branch: {branch_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to create integration branch: {e}")
            return False
    
    def validate_production_stability(self) -> bool:
        """Validate that production system remains stable"""
        logger.info("🏥 Validating production stability...")
        
        checks = [
            self._validate_api_endpoints(),
            self._validate_file_integrity(),
            self._validate_environment_variables(),
            self._validate_process_health()
        ]
        
        all_passed = all(checks)
        
        if all_passed:
            logger.info("✅ Production system validation passed")
        else:
            logger.error("❌ Production system validation failed")
        
        return all_passed
    
    def _validate_api_endpoints(self) -> bool:
        """Validate all production API endpoints are working"""
        try:
            port = os.getenv("PORT", "8000")
            base_url = f"http://localhost:{port}"
            
            for endpoint in self.production_endpoints:
                url = f"{base_url}{endpoint}"
                response = requests.get(url, timeout=10)
                
                if response.status_code not in [200, 404]:  # 404 is acceptable for some endpoints
                    logger.error(f"❌ Endpoint {endpoint} returned {response.status_code}")
                    return False
                    
                logger.info(f"✅ Endpoint {endpoint} responding correctly")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ API endpoint validation failed: {e}")
            return False
    
    def _validate_file_integrity(self) -> bool:
        """Validate critical files haven't been corrupted"""
        try:
            for file_path in self.critical_files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    # Basic syntax check for Python files
                    if file_path.endswith('.py'):
                        with open(full_path, 'r') as f:
                            content = f.read()
                        compile(content, str(full_path), 'exec')
                    
                    logger.info(f"✅ File {file_path} integrity validated")
                else:
                    logger.warning(f"⚠️ Critical file {file_path} not found")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ File integrity validation failed: {e}")
            return False
    
    def _validate_environment_variables(self) -> bool:
        """Validate environment variables are set correctly"""
        required_vars = ["OMEGA_ENV", "OMEGA_VERSION"]
        
        for var in required_vars:
            if not os.getenv(var):
                logger.error(f"❌ Required environment variable {var} not set")
                return False
            logger.info(f"✅ Environment variable {var} validated")
        
        return True
    
    def _validate_process_health(self) -> bool:
        """Validate system processes are healthy"""
        try:
            # Check if main processes are running
            ps_output = subprocess.check_output(["ps", "aux"], text=True)
            
            # Look for python processes
            python_processes = [line for line in ps_output.split('\n') if 'python' in line.lower()]
            
            if not python_processes:
                logger.warning("⚠️ No Python processes detected")
                return False
            
            logger.info(f"✅ Found {len(python_processes)} Python processes")
            return True
            
        except Exception as e:
            logger.error(f"❌ Process health validation failed: {e}")
            return False
    
    def generate_safety_report(self, snapshot: DeploymentSnapshot, 
                              conflict_results: List[SafetyCheckResult]) -> Dict[str, Any]:
        """Generate comprehensive safety report"""
        logger.info("📊 Generating safety report...")
        
        # Count results by status
        status_counts = {"pass": 0, "warning": 0, "fail": 0}
        for result in conflict_results:
            status_counts[result.status] += 1
        
        # Determine overall risk level
        if status_counts["fail"] > 0:
            risk_level = "CRITICAL"
        elif status_counts["warning"] > 0:
            risk_level = "HIGH" 
        else:
            risk_level = "LOW"
        
        # Create recommendations
        recommendations = []
        if status_counts["fail"] > 0:
            recommendations.append("🚨 DO NOT PROCEED with integration until critical issues are resolved")
            recommendations.append("🔧 Fix all failing safety checks before continuing")
        if status_counts["warning"] > 0:
            recommendations.append("⚠️ Address warnings before production deployment")
        
        recommendations.extend([
            "📋 Create integration branch for safe testing",
            "🧪 Set up parallel testing environment", 
            "📊 Implement comprehensive monitoring",
            "🔄 Prepare automated rollback procedures"
        ])
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "risk_level": risk_level,
            "system_snapshot": asdict(snapshot),
            "safety_checks": {
                "total": len(conflict_results),
                "passed": status_counts["pass"],
                "warnings": status_counts["warning"], 
                "failures": status_counts["fail"],
                "details": [asdict(result) for result in conflict_results]
            },
            "recommendations": recommendations,
            "next_steps": [
                "1. Review all failed safety checks",
                "2. Implement fixes for critical issues", 
                "3. Create isolated integration environment",
                "4. Perform gradual, monitored integration",
                "5. Maintain rollback capability at all times"
            ]
        }
        
        # Save report
        report_file = self.logs_path / f"safety_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Safety report saved to {report_file}")
        return report
    
    def run_complete_safety_assessment(self) -> Dict[str, Any]:
        """Run complete safety assessment"""
        logger.info("🛡️ Starting complete safety assessment...")
        
        print("🚀 OMEGA AI Deployment Safety Assessment")
        print("=" * 60)
        
        # Step 1: Create system snapshot
        print("📸 Creating system snapshot...")
        snapshot = self.create_system_snapshot()
        
        # Step 2: Analyze conflicts
        print("🔍 Analyzing potential conflicts...")
        conflict_results = self.analyze_results_conflicts()
        
        # Step 3: Isolate /results/ folder
        print("🚧 Isolating /results/ folder...")
        isolation_success = self.isolate_results_folder()
        
        # Step 4: Validate production stability
        print("🏥 Validating production stability...")
        stability_ok = self.validate_production_stability()
        
        # Step 5: Create integration branch
        print("🌿 Creating integration branch...")
        branch_created = self.create_integration_branch()
        
        # Step 6: Generate report
        print("📊 Generating safety report...")
        report = self.generate_safety_report(snapshot, conflict_results)
        
        # Add assessment results to report
        report["assessment_results"] = {
            "isolation_successful": isolation_success,
            "stability_validated": stability_ok,
            "branch_created": branch_created
        }
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 SAFETY ASSESSMENT SUMMARY")
        print("=" * 60)
        print(f"Risk Level: {report['risk_level']}")
        print(f"Safety Checks: {report['safety_checks']['passed']} passed, "
              f"{report['safety_checks']['warnings']} warnings, "
              f"{report['safety_checks']['failures']} failures")
        print(f"Isolation: {'✅ SUCCESS' if isolation_success else '❌ FAILED'}")
        print(f"Stability: {'✅ VALIDATED' if stability_ok else '❌ ISSUES'}")
        print(f"Branch: {'✅ CREATED' if branch_created else '❌ FAILED'}")
        
        print("\n📋 RECOMMENDATIONS:")
        for rec in report["recommendations"]:
            print(f"   {rec}")
        
        return report

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="OMEGA AI Deployment Safety Automation")
    parser.add_argument("--assessment", action="store_true", help="Run complete safety assessment")
    parser.add_argument("--isolate", action="store_true", help="Isolate /results/ folder only")
    parser.add_argument("--validate", action="store_true", help="Validate production stability only")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    
    args = parser.parse_args()
    
    # Initialize safety manager
    safety_manager = DeploymentSafetyManager(args.project_root)
    
    if args.assessment:
        # Run complete assessment
        report = safety_manager.run_complete_safety_assessment()
        sys.exit(0 if report["risk_level"] == "LOW" else 1)
    
    elif args.isolate:
        # Isolate /results/ folder only
        success = safety_manager.isolate_results_folder()
        sys.exit(0 if success else 1)
        
    elif args.validate:
        # Validate production stability only
        stability = safety_manager.validate_production_stability()
        sys.exit(0 if stability else 1)
        
    else:
        # Default: run complete assessment
        report = safety_manager.run_complete_safety_assessment()
        sys.exit(0 if report["risk_level"] == "LOW" else 1)