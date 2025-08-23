#!/usr/bin/env python3
"""
🚀 OMEGA Performance Testing Execution Script
Execute comprehensive performance testing suite with all validation requirements
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from performance_testing_framework import OmegaPerformanceTester, run_comprehensive_performance_tests
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def execute_performance_validation():
    """Execute the complete performance validation suite"""
    
    logger.info("🚀 OMEGA PRO AI - COMPREHENSIVE PERFORMANCE VALIDATION")
    logger.info("="*80)
    logger.info("Target: Validate scalability and achieve 100% system completion")
    logger.info("Expected Performance: 5000+ RPS, <2s response time, 99.9% uptime")
    logger.info("="*80)
    
    try:
        # Execute the full performance test suite
        results = await run_comprehensive_performance_tests()
        
        # Generate summary statistics
        performance_summary = generate_performance_summary(results)
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"performance_reports/detailed_results_{timestamp}.json"
        os.makedirs("performance_reports", exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'performance_summary': performance_summary,
                'detailed_results': results
            }, f, indent=2, default=str)
        
        logger.info(f"📊 Detailed results saved: {results_file}")
        
        # Print final validation results
        print_final_validation(performance_summary)
        
        return performance_summary
        
    except Exception as e:
        logger.error(f"❌ Performance testing failed: {e}")
        raise

def generate_performance_summary(results):
    """Generate performance summary from test results"""
    summary = {
        'timestamp': datetime.now().isoformat(),
        'overall_status': 'PASS',
        'tests_executed': len(results),
        'critical_metrics': {},
        'scalability_validation': {},
        'sla_compliance': {},
        'recommendations': []
    }
    
    # Analyze load test results
    load_tests = [r for r in results if 'rps_achieved' in str(r)]
    
    if load_tests:
        max_rps = max(r.get('rps_achieved', 0) for r in load_tests if isinstance(r, dict))
        avg_response_time = sum(r.get('avg_response_time', 0) for r in load_tests if isinstance(r, dict)) / len(load_tests)
        avg_error_rate = sum(r.get('error_rate', 0) for r in load_tests if isinstance(r, dict)) / len(load_tests)
        
        summary['critical_metrics'] = {
            'max_rps_achieved': max_rps,
            'avg_response_time': avg_response_time,
            'avg_error_rate': avg_error_rate,
            'rps_target_met': max_rps >= 5000,
            'response_time_acceptable': avg_response_time <= 2.0,
            'error_rate_acceptable': avg_error_rate <= 0.01
        }
    
    # Check SLA compliance
    sla_compliance = {
        'high_load_capability': summary['critical_metrics'].get('rps_target_met', False),
        'response_time_sla': summary['critical_metrics'].get('response_time_acceptable', False),
        'availability_sla': summary['critical_metrics'].get('error_rate_acceptable', False)
    }
    
    summary['sla_compliance'] = sla_compliance
    summary['sla_score'] = sum(sla_compliance.values()) / len(sla_compliance) * 100
    
    # Overall status determination
    if summary['sla_score'] >= 90:
        summary['overall_status'] = 'PASS'
        summary['system_grade'] = 'A+'
    elif summary['sla_score'] >= 80:
        summary['overall_status'] = 'PASS'
        summary['system_grade'] = 'A'
    elif summary['sla_score'] >= 70:
        summary['overall_status'] = 'CONDITIONAL_PASS'
        summary['system_grade'] = 'B+'
    else:
        summary['overall_status'] = 'FAIL'
        summary['system_grade'] = 'C'
    
    # Generate recommendations
    if not sla_compliance.get('high_load_capability', True):
        summary['recommendations'].append("Scale horizontally on Akash network to achieve 5000+ RPS target")
    
    if not sla_compliance.get('response_time_sla', True):
        summary['recommendations'].append("Optimize prediction algorithms and implement caching strategies")
    
    if not sla_compliance.get('availability_sla', True):
        summary['recommendations'].append("Implement additional circuit breaker patterns and error handling")
    
    return summary

def print_final_validation(summary):
    """Print final validation results"""
    
    print("\n" + "="*80)
    print("🏁 FINAL PERFORMANCE VALIDATION RESULTS")
    print("="*80)
    
    # Overall status
    status_emoji = "✅" if summary['overall_status'] == 'PASS' else "⚠️" if summary['overall_status'] == 'CONDITIONAL_PASS' else "❌"
    print(f"Overall Status: {status_emoji} {summary['overall_status']}")
    print(f"System Grade: {summary.get('system_grade', 'N/A')}")
    print(f"SLA Compliance Score: {summary.get('sla_score', 0):.1f}%")
    
    # Critical metrics
    print(f"\n📊 CRITICAL PERFORMANCE METRICS:")
    metrics = summary.get('critical_metrics', {})
    
    rps_status = "✅" if metrics.get('rps_target_met', False) else "❌"
    print(f"   {rps_status} Max RPS Achieved: {metrics.get('max_rps_achieved', 0):.0f} (Target: 5000+)")
    
    response_status = "✅" if metrics.get('response_time_acceptable', False) else "❌"
    print(f"   {response_status} Avg Response Time: {metrics.get('avg_response_time', 0):.3f}s (Target: <2s)")
    
    error_status = "✅" if metrics.get('error_rate_acceptable', False) else "❌"
    print(f"   {error_status} Error Rate: {metrics.get('avg_error_rate', 0):.3%} (Target: <1%)")
    
    # SLA compliance
    print(f"\n📋 SLA COMPLIANCE:")
    sla = summary.get('sla_compliance', {})
    for requirement, status in sla.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {requirement.replace('_', ' ').title()}")
    
    # Recommendations
    if summary.get('recommendations'):
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(summary['recommendations'], 1):
            print(f"   {i}. {rec}")
    
    # Final completion status
    print(f"\n🎯 SYSTEM COMPLETION STATUS:")
    if summary['overall_status'] == 'PASS' and summary.get('sla_score', 0) >= 95:
        print("   🌟 100% SYSTEM COMPLETION ACHIEVED")
        print("   🚀 OMEGA PRO AI ready for production deployment")
    elif summary['overall_status'] == 'PASS':
        print("   ✅ 95%+ SYSTEM COMPLETION ACHIEVED")
        print("   🔧 Minor optimizations recommended")
    else:
        print("   ⚠️ System completion requires additional optimization")
    
    print("="*80)

async def quick_smoke_test():
    """Run a quick smoke test to verify system basic functionality"""
    logger.info("🔍 Running quick smoke test...")
    
    async with OmegaPerformanceTester() as tester:
        # Quick health check
        health_result = await tester.single_request("/health")
        if health_result.status_code != 200:
            logger.error("❌ Health check failed")
            return False
        
        # Quick prediction test
        prediction_result = await tester.single_request("/predict", "POST", 
                                                       {"n_predictions": 1, "strategy": "balanced"})
        if prediction_result.status_code != 200:
            logger.error("❌ Prediction test failed")
            return False
        
        logger.info("✅ Smoke test passed")
        return True

if __name__ == "__main__":
    async def main():
        # First run smoke test
        if not await quick_smoke_test():
            logger.error("❌ Smoke test failed - system not ready for performance testing")
            sys.exit(1)
        
        # Run full performance validation
        try:
            summary = await execute_performance_validation()
            
            # Exit code based on results
            if summary['overall_status'] == 'PASS':
                sys.exit(0)
            elif summary['overall_status'] == 'CONDITIONAL_PASS':
                sys.exit(2)  # Warning exit code
            else:
                sys.exit(1)  # Failure exit code
                
        except Exception as e:
            logger.error(f"❌ Performance validation failed: {e}")
            sys.exit(1)
    
    # Run the main function
    asyncio.run(main())