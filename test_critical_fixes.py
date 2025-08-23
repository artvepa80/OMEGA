#!/usr/bin/env python3
"""
Test script to verify critical fixes for OMEGA AI v10.1
Tests:
1. NumPy compatibility fix for np.bool deprecation
2. Performance report generation with fallbacks
"""

import sys
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_numpy_compatibility():
    """Test NumPy compatibility fix"""
    print("🔍 Testing NumPy compatibility fix...")
    
    try:
        # Import the compatibility module
        from utils.numpy_compat import patch_numpy_deprecated_aliases
        import numpy as np
        
        # Test that np.bool is available
        assert hasattr(np, 'bool'), "np.bool should be available after patch"
        
        # Test basic boolean operations
        test_bool = np.bool(True)
        assert test_bool == True, "np.bool should work correctly"
        
        print("✅ NumPy compatibility fix working correctly")
        return True
        
    except Exception as e:
        print(f"❌ NumPy compatibility fix failed: {e}")
        return False

def test_performance_reporter():
    """Test performance reporter with fallbacks"""
    print("🔍 Testing performance reporter with fallbacks...")
    
    try:
        from modules.performance_reporter import InteractivePerformanceReporter
        
        # Test with no performance monitor (should use fallbacks)
        reporter = InteractivePerformanceReporter(performance_monitor=None)
        
        # Try to generate dashboard (should use minimal report fallback)
        report_path, session_id = reporter.generate_interactive_dashboard()
        
        # Verify report was generated
        assert os.path.exists(report_path), f"Report should be generated at {report_path}"
        assert session_id is not None, "Session ID should be generated"
        
        print(f"✅ Performance reporter fallback working: {report_path}")
        return True
        
    except Exception as e:
        print(f"❌ Performance reporter test failed: {e}")
        return False

def test_utility_function():
    """Test the utility function with fallbacks"""
    print("🔍 Testing performance dashboard utility function...")
    
    try:
        from modules.performance_reporter import generate_performance_dashboard
        
        # This should work even without a performance monitor
        result_path = generate_performance_dashboard()
        
        assert result_path != "", "Should return a non-empty path"
        
        print(f"✅ Performance dashboard utility working: {result_path}")
        return True
        
    except Exception as e:
        print(f"❌ Performance dashboard utility test failed: {e}")
        return False

def main():
    """Run all critical fix tests"""
    print("🚀 OMEGA AI v10.1 - Critical Fixes Validation")
    print("=" * 50)
    
    test_results = []
    
    # Test 1: NumPy compatibility
    test_results.append(test_numpy_compatibility())
    
    # Test 2: Performance reporter fallbacks
    test_results.append(test_performance_reporter())
    
    # Test 3: Utility function
    test_results.append(test_utility_function())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    if passed_tests == total_tests:
        print(f"✅ All {total_tests} critical fixes are working correctly!")
        return 0
    else:
        print(f"❌ {total_tests - passed_tests}/{total_tests} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())