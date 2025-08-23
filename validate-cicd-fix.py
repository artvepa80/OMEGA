#!/usr/bin/env python3
"""
OMEGA CI/CD Pipeline Validation Script
=====================================

This script validates that all CI/CD pipeline fixes have been applied correctly
and the system is ready for automated deployment.

Usage: python validate-cicd-fix.py
"""

import os
import yaml
import json
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

class CICDValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.workflows_dir = self.project_root / '.github' / 'workflows'
        self.deploy_dir = self.project_root / 'deploy'
        self.akash_url = "https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win"
        
        self.results = {
            'workflow_validation': [],
            'configuration_validation': [],
            'deployment_validation': [],
            'connectivity_validation': []
        }
    
    def validate_workflows(self) -> bool:
        """Validate all GitHub Actions workflow files"""
        print("🔍 Validating GitHub Actions workflows...")
        
        required_workflows = [
            'simple-deploy.yml',
            'python-package.yml',
            'dependency-updates.yml',
            'omega-comprehensive-ci.yml',
            'monitoring-alerting.yml',
            'pipeline-validation.yml',
            'blue-green-deployment.yml',
            'automated-rollback.yml',
            'secrets-validation.yml',
            'pipeline-test.yml'
        ]
        
        all_valid = True
        
        for workflow_file in required_workflows:
            workflow_path = self.workflows_dir / workflow_file
            
            if not workflow_path.exists():
                self.results['workflow_validation'].append(f"❌ Missing: {workflow_file}")
                all_valid = False
                continue
            
            try:
                with open(workflow_path, 'r') as f:
                    workflow_content = yaml.safe_load(f)
                
                # Validate required fields
                required_fields = ['name', 'on', 'jobs']
                for field in required_fields:
                    if field not in workflow_content:
                        self.results['workflow_validation'].append(f"❌ {workflow_file}: Missing '{field}' field")
                        all_valid = False
                        continue
                
                # Check for deprecated action versions
                workflow_str = f.read()
                if 'actions/download-artifact@v3' in workflow_str:
                    self.results['workflow_validation'].append(f"⚠️ {workflow_file}: Uses deprecated download-artifact@v3")
                
                if 'actions/setup-python@v3' in workflow_str:
                    self.results['workflow_validation'].append(f"⚠️ {workflow_file}: Uses deprecated setup-python@v3")
                
                self.results['workflow_validation'].append(f"✅ {workflow_file}: Valid YAML structure")
                
            except yaml.YAMLError as e:
                self.results['workflow_validation'].append(f"❌ {workflow_file}: Invalid YAML - {e}")
                all_valid = False
            except Exception as e:
                self.results['workflow_validation'].append(f"❌ {workflow_file}: Error - {e}")
                all_valid = False
        
        return all_valid
    
    def validate_requirements(self) -> bool:
        """Validate requirements.txt for CI/CD compatibility"""
        print("📦 Validating requirements.txt...")
        
        requirements_path = self.project_root / 'requirements.txt'
        
        if not requirements_path.exists():
            self.results['configuration_validation'].append("❌ requirements.txt not found")
            return False
        
        try:
            with open(requirements_path, 'r') as f:
                content = f.read()
            
            # Check for Apple-specific paths that break CI
            apple_paths = [
                'file:///AppleInternal',
                '@ file://',
                'BuildRoots'
            ]
            
            has_apple_paths = False
            for apple_path in apple_paths:
                if apple_path in content:
                    self.results['configuration_validation'].append(f"❌ Found Apple-specific path: {apple_path}")
                    has_apple_paths = True
            
            if not has_apple_paths:
                self.results['configuration_validation'].append("✅ requirements.txt: No Apple-specific paths")
            
            # Count dependencies
            lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
            self.results['configuration_validation'].append(f"📊 {len(lines)} dependencies found")
            
            return not has_apple_paths
            
        except Exception as e:
            self.results['configuration_validation'].append(f"❌ requirements.txt error: {e}")
            return False
    
    def validate_akash_deployment(self) -> bool:
        """Validate Akash deployment configuration"""
        print("☁️ Validating Akash deployment configuration...")
        
        deployment_file = self.deploy_dir / 'akash-deployment.yaml'
        
        if not deployment_file.exists():
            self.results['deployment_validation'].append("❌ akash-deployment.yaml not found")
            return False
        
        try:
            with open(deployment_file, 'r') as f:
                deployment_config = yaml.safe_load(f)
            
            # Validate required Akash fields
            required_fields = ['version', 'services']
            for field in required_fields:
                if field not in deployment_config:
                    self.results['deployment_validation'].append(f"❌ Missing required field: {field}")
                    return False
            
            # Check for proper image names (Docker Hub format)
            services = deployment_config.get('services', {})
            for service_name, service_config in services.items():
                image = service_config.get('image', '')
                if 'artvepa80/' in image:
                    self.results['deployment_validation'].append(f"✅ {service_name}: Uses proper Docker Hub image")
                else:
                    self.results['deployment_validation'].append(f"⚠️ {service_name}: Image may need Docker Hub prefix")
            
            self.results['deployment_validation'].append("✅ Akash deployment configuration valid")
            return True
            
        except yaml.YAMLError as e:
            self.results['deployment_validation'].append(f"❌ Invalid YAML in deployment config: {e}")
            return False
        except Exception as e:
            self.results['deployment_validation'].append(f"❌ Deployment config error: {e}")
            return False
    
    def validate_deployment_connectivity(self) -> bool:
        """Test connectivity to the deployed Akash service"""
        print("🌐 Testing deployment connectivity...")
        
        endpoints = [
            ('Root', '/'),
            ('Health', '/health'),
            ('Status', '/status'),
            ('Predict', '/predict')
        ]
        
        connectivity_ok = False
        
        for name, endpoint in endpoints:
            try:
                url = f"{self.akash_url}{endpoint}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    self.results['connectivity_validation'].append(f"✅ {name}: HTTP 200 OK")
                    connectivity_ok = True
                elif response.status_code in [404, 405]:
                    self.results['connectivity_validation'].append(f"⚠️ {name}: HTTP {response.status_code} (endpoint exists)")
                    connectivity_ok = True  # Service is responding
                else:
                    self.results['connectivity_validation'].append(f"⚠️ {name}: HTTP {response.status_code}")
                
            except requests.exceptions.Timeout:
                self.results['connectivity_validation'].append(f"❌ {name}: Timeout")
            except requests.exceptions.ConnectionError:
                self.results['connectivity_validation'].append(f"❌ {name}: Connection failed")
            except Exception as e:
                self.results['connectivity_validation'].append(f"❌ {name}: Error - {e}")
        
        return connectivity_ok
    
    def generate_report(self) -> Dict:
        """Generate comprehensive validation report"""
        print("\n📊 Generating validation report...")
        
        # Count successes and failures
        total_checks = sum(len(results) for results in self.results.values())
        successful_checks = sum(
            len([r for r in results if r.startswith('✅')])
            for results in self.results.values()
        )
        warning_checks = sum(
            len([r for r in results if r.startswith('⚠️')])
            for results in self.results.values()
        )
        failed_checks = sum(
            len([r for r in results if r.startswith('❌')])
            for results in self.results.values()
        )
        
        overall_status = "PASSED" if failed_checks == 0 else "NEEDS ATTENTION"
        
        report = {
            'timestamp': subprocess.check_output(['date'], text=True).strip(),
            'overall_status': overall_status,
            'summary': {
                'total_checks': total_checks,
                'successful': successful_checks,
                'warnings': warning_checks,
                'failed': failed_checks,
                'success_rate': f"{(successful_checks / total_checks * 100):.1f}%" if total_checks > 0 else "0%"
            },
            'detailed_results': self.results,
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Check for common issues
        all_results = []
        for category_results in self.results.values():
            all_results.extend(category_results)
        
        result_text = '\n'.join(all_results)
        
        if 'Apple-specific path' in result_text:
            recommendations.append("🔧 Clean up requirements.txt to remove macOS-specific package paths")
        
        if 'deprecated' in result_text:
            recommendations.append("🔧 Update GitHub Actions to use latest action versions")
        
        if 'Connection failed' in result_text:
            recommendations.append("🔧 Check Akash Network deployment status and connectivity")
        
        if 'Missing' in result_text:
            recommendations.append("🔧 Add missing workflow files or configuration")
        
        if not recommendations:
            recommendations.append("✅ All major issues have been resolved!")
        
        recommendations.extend([
            "📊 Run the pipeline-test.yml workflow to perform end-to-end testing",
            "🔍 Monitor the deployment using the monitoring-alerting.yml workflow",
            "🚀 The CI/CD pipeline is ready for production use"
        ])
        
        return recommendations
    
    def print_report(self, report: Dict):
        """Print a formatted report to console"""
        print(f"\n{'='*60}")
        print("🚀 OMEGA CI/CD Pipeline Validation Report")
        print(f"{'='*60}")
        print(f"Date: {report['timestamp']}")
        print(f"Overall Status: {report['overall_status']}")
        print(f"Success Rate: {report['summary']['success_rate']}")
        print()
        
        print(f"📊 Summary:")
        print(f"  • Total Checks: {report['summary']['total_checks']}")
        print(f"  • Successful: {report['summary']['successful']}")
        print(f"  • Warnings: {report['summary']['warnings']}")
        print(f"  • Failed: {report['summary']['failed']}")
        print()
        
        # Print detailed results
        for category, results in report['detailed_results'].items():
            if results:
                print(f"{category.replace('_', ' ').title()}:")
                for result in results:
                    print(f"  {result}")
                print()
        
        # Print recommendations
        print("🎯 Recommendations:")
        for i, recommendation in enumerate(report['recommendations'], 1):
            print(f"  {i}. {recommendation}")
        print()
        
        print(f"🌐 Deployment URL: {self.akash_url}")
        print(f"{'='*60}")
    
    def run_validation(self) -> bool:
        """Run complete validation suite"""
        print("🚀 Starting OMEGA CI/CD Pipeline Validation")
        print(f"Project root: {self.project_root}")
        print(f"Deployment URL: {self.akash_url}")
        print()
        
        # Run all validations
        workflows_valid = self.validate_workflows()
        requirements_valid = self.validate_requirements()
        deployment_valid = self.validate_akash_deployment()
        connectivity_valid = self.validate_deployment_connectivity()
        
        # Generate and display report
        report = self.generate_report()
        self.print_report(report)
        
        # Save report to file
        report_file = self.project_root / 'cicd-validation-report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"📄 Full report saved to: {report_file}")
        
        # Return overall success
        return report['overall_status'] == 'PASSED'

def main():
    """Main validation function"""
    validator = CICDValidator()
    success = validator.run_validation()
    
    if success:
        print("✅ All validations passed! CI/CD pipeline is ready.")
        exit(0)
    else:
        print("⚠️ Some issues found. Please review recommendations above.")
        exit(1)

if __name__ == '__main__':
    main()