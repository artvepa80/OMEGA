#!/usr/bin/env python3
"""
OMEGA PRO AI v10.1 - Comprehensive Test Runner
Automated test execution with reporting and CI/CD integration
"""

import os
import sys
import argparse
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


class OMEGATestRunner:
    """Comprehensive test runner for OMEGA PRO AI"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_dir = self.project_root / "tests"
        self.reports_dir = self.project_root / "test_reports"
        self.coverage_dir = self.project_root / "htmlcov"
        
        # Create necessary directories
        self.reports_dir.mkdir(exist_ok=True)
        self.coverage_dir.mkdir(exist_ok=True)
    
    def run_command(self, command, capture_output=True):
        """Run shell command and return result"""
        print(f"🔄 Running: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=capture_output,
                text=True,
                cwd=self.project_root
            )
            return result
        except Exception as e:
            print(f"❌ Error running command: {e}")
            return None
    
    def setup_environment(self):
        """Setup test environment"""
        print("🛠️ Setting up test environment...")
        
        # Create necessary directories
        directories = [
            "data", "logs", "models", "temp", "outputs", "results",
            "tests/unit", "tests/integration", "tests/performance", "tests/security"
        ]
        
        for directory in directories:
            (self.project_root / directory).mkdir(parents=True, exist_ok=True)
        
        # Set environment variables for testing
        os.environ.update({
            'TESTING': 'true',
            'LOG_LEVEL': 'WARNING',
            'OMEGA_ENV': 'testing'
        })
        
        print("✅ Test environment setup complete")
    
    def run_unit_tests(self, python_versions=None):
        """Run unit tests"""
        print("\n🧪 Running Unit Tests...")
        
        if python_versions is None:
            python_versions = ['python']
        
        results = {}
        
        for python_version in python_versions:
            print(f"\n📋 Testing with {python_version}...")
            
            command = f"""
            {python_version} -m pytest tests/unit/ -v \
                --cov=core \
                --cov=modules \
                --cov-report=xml:coverage-unit.xml \
                --cov-report=html:htmlcov-unit \
                --cov-report=term-missing \
                --junit-xml=test-results-unit.xml \
                -m "unit and not slow"
            """
            
            result = self.run_command(command.strip())
            results[f'unit-{python_version}'] = {
                'returncode': result.returncode if result else 1,
                'stdout': result.stdout if result else '',
                'stderr': result.stderr if result else ''
            }
            
            if result and result.returncode == 0:
                print(f"✅ Unit tests passed for {python_version}")
            else:
                print(f"❌ Unit tests failed for {python_version}")
        
        return results
    
    def run_integration_tests(self):
        """Run integration tests"""
        print("\n🔗 Running Integration Tests...")
        
        # Set integration test environment
        os.environ['RUN_INTEGRATION_TESTS'] = 'true'
        
        command = """
        python -m pytest tests/integration/ -v \
            --cov=core \
            --cov=modules \
            --cov=api \
            --cov-report=xml:coverage-integration.xml \
            --junit-xml=test-results-integration.xml \
            -m "integration and not slow"
        """
        
        result = self.run_command(command.strip())
        
        if result and result.returncode == 0:
            print("✅ Integration tests passed")
        else:
            print("❌ Integration tests failed")
        
        return {
            'integration': {
                'returncode': result.returncode if result else 1,
                'stdout': result.stdout if result else '',
                'stderr': result.stderr if result else ''
            }
        }
    
    def run_performance_tests(self, skip_slow=True):
        """Run performance tests"""
        print("\n🚀 Running Performance Tests...")
        
        # Set performance test environment
        if skip_slow:
            os.environ['SKIP_SLOW_TESTS'] = 'false'
        else:
            os.environ['SKIP_SLOW_TESTS'] = 'true'
        
        command = """
        python -m pytest tests/performance/ -v \
            --benchmark-only \
            --benchmark-json=benchmark_results.json \
            --junit-xml=test-results-performance.xml \
            -m "performance"
        """
        
        result = self.run_command(command.strip())
        
        if result and result.returncode == 0:
            print("✅ Performance tests passed")
            self.generate_performance_report()
        else:
            print("❌ Performance tests failed")
        
        return {
            'performance': {
                'returncode': result.returncode if result else 1,
                'stdout': result.stdout if result else '',
                'stderr': result.stderr if result else ''
            }
        }
    
    def run_security_tests(self):
        """Run security tests"""
        print("\n🔒 Running Security Tests...")
        
        # Run bandit security analysis
        print("🔍 Running Bandit security analysis...")
        bandit_result = self.run_command(
            "bandit -r core/ modules/ api/ -f json -o bandit-report.json"
        )
        
        # Run safety check for dependencies
        print("🛡️ Checking for known vulnerabilities...")
        safety_result = self.run_command(
            "safety check --json --output safety-report.json"
        )
        
        # Run security tests
        command = """
        python -m pytest tests/security/ -v \
            --junit-xml=test-results-security.xml \
            -m "security"
        """
        
        result = self.run_command(command.strip())
        
        if result and result.returncode == 0:
            print("✅ Security tests passed")
        else:
            print("❌ Security tests failed")
        
        return {
            'security': {
                'returncode': result.returncode if result else 1,
                'stdout': result.stdout if result else '',
                'stderr': result.stderr if result else '',
                'bandit': bandit_result.returncode if bandit_result else 1,
                'safety': safety_result.returncode if safety_result else 1
            }
        }
    
    def run_code_quality_checks(self):
        """Run code quality checks"""
        print("\n📝 Running Code Quality Checks...")
        
        checks = {
            'black': "black --check --diff core/ modules/ api/ tests/",
            'isort': "isort --check-only --diff core/ modules/ api/ tests/",
            'flake8': "flake8 core/ modules/ api/ --max-line-length=100 --extend-ignore=E203,W503",
            'mypy': "mypy core/ modules/ api/ --ignore-missing-imports --no-strict-optional"
        }
        
        results = {}
        
        for check_name, command in checks.items():
            print(f"🔍 Running {check_name}...")
            result = self.run_command(command)
            
            results[check_name] = {
                'returncode': result.returncode if result else 1,
                'stdout': result.stdout if result else '',
                'stderr': result.stderr if result else ''
            }
            
            if result and result.returncode == 0:
                print(f"✅ {check_name} passed")
            else:
                print(f"❌ {check_name} failed")
        
        return results
    
    def generate_performance_report(self):
        """Generate performance test report"""
        benchmark_file = self.project_root / "benchmark_results.json"
        
        if not benchmark_file.exists():
            return
        
        try:
            with open(benchmark_file, 'r') as f:
                data = json.load(f)
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_benchmarks': len(data.get('benchmarks', [])),
                    'fastest_test': None,
                    'slowest_test': None,
                    'average_time': 0
                },
                'benchmarks': []
            }
            
            benchmarks = data.get('benchmarks', [])
            if benchmarks:
                times = []
                for benchmark in benchmarks:
                    stats = benchmark.get('stats', {})
                    mean_time = stats.get('mean', 0)
                    times.append(mean_time)
                    
                    report['benchmarks'].append({
                        'name': benchmark.get('name', 'Unknown'),
                        'mean_time': mean_time,
                        'stddev': stats.get('stddev', 0),
                        'min_time': stats.get('min', 0),
                        'max_time': stats.get('max', 0)
                    })
                
                if times:
                    report['summary']['average_time'] = sum(times) / len(times)
                    report['summary']['fastest_test'] = min(report['benchmarks'], 
                                                          key=lambda x: x['mean_time'])
                    report['summary']['slowest_test'] = max(report['benchmarks'], 
                                                          key=lambda x: x['mean_time'])
            
            # Save performance report
            with open(self.reports_dir / 'performance_report.json', 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"📊 Performance report generated: {report['summary']}")
            
        except Exception as e:
            print(f"❌ Error generating performance report: {e}")
    
    def generate_comprehensive_report(self, results):
        """Generate comprehensive test report"""
        print("\n📊 Generating Comprehensive Test Report...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_passed': 0,
                'total_failed': 0,
                'total_skipped': 0
            },
            'results': results,
            'coverage': self.get_coverage_info(),
            'environment': {
                'python_version': sys.version,
                'platform': sys.platform,
                'working_directory': str(self.project_root)
            }
        }
        
        # Calculate summary statistics
        for test_type, test_results in results.items():
            if isinstance(test_results, dict) and 'returncode' in test_results:
                if test_results['returncode'] == 0:
                    report['summary']['total_passed'] += 1
                else:
                    report['summary']['total_failed'] += 1
        
        # Save comprehensive report
        report_file = self.reports_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate HTML report
        self.generate_html_report(report)
        
        print(f"✅ Comprehensive report saved: {report_file}")
        return report
    
    def get_coverage_info(self):
        """Get coverage information"""
        coverage_file = self.project_root / "coverage.xml"
        
        if not coverage_file.exists():
            return None
        
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(coverage_file)
            root = tree.getroot()
            
            coverage_info = {
                'line_rate': float(root.get('line-rate', 0)),
                'branch_rate': float(root.get('branch-rate', 0)),
                'lines_covered': int(root.get('lines-covered', 0)),
                'lines_valid': int(root.get('lines-valid', 0))
            }
            
            return coverage_info
        except Exception as e:
            print(f"⚠️ Could not parse coverage info: {e}")
            return None
    
    def generate_html_report(self, report):
        """Generate HTML test report"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>OMEGA PRO AI Test Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f4f4f4; padding: 20px; border-radius: 5px; }
                .summary { display: flex; gap: 20px; margin: 20px 0; }
                .metric { background-color: #e9e9e9; padding: 15px; border-radius: 5px; text-align: center; }
                .passed { color: green; }
                .failed { color: red; }
                .section { margin: 20px 0; }
                .test-result { margin: 10px 0; padding: 10px; border-left: 4px solid #ddd; }
                .test-passed { border-left-color: green; }
                .test-failed { border-left-color: red; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>OMEGA PRO AI Test Report</h1>
                <p>Generated: {timestamp}</p>
            </div>
            
            <div class="summary">
                <div class="metric">
                    <h3>Tests Passed</h3>
                    <div class="passed">{total_passed}</div>
                </div>
                <div class="metric">
                    <h3>Tests Failed</h3>
                    <div class="failed">{total_failed}</div>
                </div>
                <div class="metric">
                    <h3>Coverage</h3>
                    <div>{coverage}%</div>
                </div>
            </div>
            
            <div class="section">
                <h2>Test Results</h2>
                {test_results}
            </div>
        </body>
        </html>
        """
        
        # Format test results
        test_results_html = ""
        for test_type, result in report['results'].items():
            if isinstance(result, dict) and 'returncode' in result:
                status = "passed" if result['returncode'] == 0 else "failed"
                test_results_html += f"""
                <div class="test-result test-{status}">
                    <h3>{test_type.replace('_', ' ').title()}</h3>
                    <p>Status: <span class="{status}">{status.upper()}</span></p>
                </div>
                """
        
        # Get coverage percentage
        coverage_pct = "N/A"
        if report['coverage']:
            coverage_pct = f"{report['coverage']['line_rate'] * 100:.1f}"
        
        # Generate HTML
        html_content = html_template.format(
            timestamp=report['timestamp'],
            total_passed=report['summary']['total_passed'],
            total_failed=report['summary']['total_failed'],
            coverage=coverage_pct,
            test_results=test_results_html
        )
        
        # Save HTML report
        html_file = self.reports_dir / "test_report.html"
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        print(f"📄 HTML report generated: {html_file}")
    
    def run_all_tests(self, options=None):
        """Run all tests"""
        if options is None:
            options = {}
        
        print("🚀 Starting Comprehensive Test Suite for OMEGA PRO AI v10.1")
        print("=" * 60)
        
        start_time = time.time()
        
        # Setup environment
        self.setup_environment()
        
        # Run all test suites
        all_results = {}
        
        if options.get('unit', True):
            all_results.update(self.run_unit_tests())
        
        if options.get('integration', True):
            all_results.update(self.run_integration_tests())
        
        if options.get('performance', True):
            all_results.update(self.run_performance_tests(skip_slow=options.get('skip_slow', True)))
        
        if options.get('security', True):
            all_results.update(self.run_security_tests())
        
        if options.get('quality', True):
            all_results.update(self.run_code_quality_checks())
        
        # Generate comprehensive report
        report = self.generate_comprehensive_report(all_results)
        
        # Print summary
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("🎯 Test Suite Complete!")
        print(f"⏱️  Total Duration: {duration:.2f} seconds")
        print(f"✅ Tests Passed: {report['summary']['total_passed']}")
        print(f"❌ Tests Failed: {report['summary']['total_failed']}")
        print(f"📊 Reports saved in: {self.reports_dir}")
        
        return all_results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="OMEGA PRO AI Comprehensive Test Runner"
    )
    
    parser.add_argument(
        '--unit', action='store_true',
        help='Run unit tests'
    )
    parser.add_argument(
        '--integration', action='store_true', 
        help='Run integration tests'
    )
    parser.add_argument(
        '--performance', action='store_true',
        help='Run performance tests'
    )
    parser.add_argument(
        '--security', action='store_true',
        help='Run security tests'
    )
    parser.add_argument(
        '--quality', action='store_true',
        help='Run code quality checks'
    )
    parser.add_argument(
        '--all', action='store_true',
        help='Run all tests'
    )
    parser.add_argument(
        '--skip-slow', action='store_true',
        help='Skip slow running tests'
    )
    
    args = parser.parse_args()
    
    # If no specific tests selected, run all
    if not any([args.unit, args.integration, args.performance, args.security, args.quality]):
        args.all = True
    
    options = {
        'unit': args.unit or args.all,
        'integration': args.integration or args.all,
        'performance': args.performance or args.all,
        'security': args.security or args.all,
        'quality': args.quality or args.all,
        'skip_slow': args.skip_slow
    }
    
    runner = OMEGATestRunner()
    results = runner.run_all_tests(options)
    
    # Exit with error code if any tests failed
    failed_tests = sum(1 for result in results.values() 
                      if isinstance(result, dict) and result.get('returncode', 0) != 0)
    
    sys.exit(1 if failed_tests > 0 else 0)


if __name__ == '__main__':
    main()