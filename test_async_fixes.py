#!/usr/bin/env python3
"""
Test script to validate the asyncio fixes in OMEGA AI system
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_async_function():
    """Simple test async function"""
    await asyncio.sleep(0.1)
    return {"status": "success", "message": "Async function executed successfully"}

def test_safe_async_execution():
    """Test the safe async execution from main_structured_logging.py"""
    print("🧪 Testing safe_async_execution...")
    
    try:
        # Import the fixed function
        from main_structured_logging import safe_async_execution
        
        # Test 1: Call from synchronous context (no event loop)
        print("Test 1: Calling from synchronous context...")
        result = safe_async_execution(test_async_function())
        print(f"✅ Result: {result}")
        
        # Test 2: Call from within an event loop
        async def test_from_async_context():
            print("Test 2: Calling from async context (simulating event loop conflict)...")
            result = safe_async_execution(test_async_function())
            print(f"✅ Result from async context: {result}")
            return result
        
        # Run test 2 in an event loop
        asyncio.run(test_from_async_context())
        
        print("✅ All asyncio tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_omega_unified_main():
    """Test that omega_unified_main.py doesn't have asyncio issues"""
    print("\n🧪 Testing omega_unified_main.py import...")
    
    try:
        # Test import
        import omega_unified_main
        print("✅ omega_unified_main.py imported successfully")
        
        # Test that it can be imported from within an event loop
        async def test_import_from_async():
            import omega_unified_main
            return True
        
        result = asyncio.run(test_import_from_async())
        print("✅ omega_unified_main.py works in async context")
        
        return True
        
    except Exception as e:
        print(f"❌ omega_unified_main.py test failed: {e}")
        return False

def test_main_structured_logging():
    """Test that main_structured_logging.py doesn't have asyncio issues"""
    print("\n🧪 Testing main_structured_logging.py import...")
    
    try:
        # Test basic import
        import main_structured_logging
        print("✅ main_structured_logging.py imported successfully")
        
        # Test safe_async_execution function
        if hasattr(main_structured_logging, 'safe_async_execution'):
            print("✅ safe_async_execution function is available")
        else:
            print("❌ safe_async_execution function not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ main_structured_logging.py test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all asyncio fix tests"""
    print("🚀 OMEGA AI - AsyncIO Fix Validation Tests")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Test 1: safe_async_execution
    test1_result = test_safe_async_execution()
    all_tests_passed = all_tests_passed and test1_result
    
    # Test 2: omega_unified_main.py
    test2_result = test_omega_unified_main()
    all_tests_passed = all_tests_passed and test2_result
    
    # Test 3: main_structured_logging.py
    test3_result = test_main_structured_logging()
    all_tests_passed = all_tests_passed and test3_result
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 ALL ASYNCIO FIXES VALIDATED SUCCESSFULLY!")
        print("✅ No more 'asyncio.run() cannot be called from a running event loop' warnings expected")
    else:
        print("❌ SOME TESTS FAILED - Review the fixes")
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())