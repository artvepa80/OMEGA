#!/usr/bin/env python3
"""
Test script for OMEGA integration
Verify that the real OMEGA models are working correctly with the FastAPI system
"""

import asyncio
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.omega_flow_integrated import OmegaFlowIntegrated

async def test_omega_integration():
    """Test the OMEGA integration"""
    print("🚀 Testing OMEGA Integration...")
    
    try:
        # Create mock redis client for testing
        class MockRedis:
            async def ping(self):
                return "PONG"
            
            async def setex(self, key, timeout, value):
                print(f"📝 Cache: {key}")
                return True
        
        mock_redis = MockRedis()
        
        # Initialize OMEGA flow
        omega_flow = OmegaFlowIntegrated(mock_redis)
        print("✅ OMEGA Flow created")
        
        # Initialize the system
        await omega_flow.initialize()
        print("✅ OMEGA Flow initialized")
        
        # Test prediction generation
        print("🎲 Generating statistical analysis...")
        
        result = await omega_flow.generate_series(
            lottery_type="kabala",
            series_count=3,
            filters={"exclude_numbers": [13]},
            user_preferences={"mode": "balanced"}
        )
        
        print(f"✅ Generated {len(result.series)} statistical predictions")
        
        # Display results
        print("\n📊 Statistical Analysis Results:")
        print(f"Analysis Type: Statistical Pattern Recognition")
        
        for i, series in enumerate(result.series[:3], 1):
            print(f"\nSeries {i}: {series.numbers}")
            print(f"  📈 Confidence: {series.confidence:.3f}")
            print(f"  🔍 Pattern Score: {series.pattern_score:.3f}")
            print(f"  📊 SVI Score: {series.svi_score:.3f}")
            print(f"  🤖 Source: {series.source}")
        
        print(f"\n📋 Analysis Summary:")
        analysis = result.analysis
        if "prediction_quality" in analysis:
            pq = analysis["prediction_quality"]
            print(f"  Average Confidence: {pq.get('avg_confidence', 0):.3f}")
            print(f"  Pattern Consistency: {pq.get('pattern_consistency', 0):.3f}")
        
        print(f"\n💡 Statistical Recommendations:")
        for rec in result.recommendations[:5]:
            print(f"  • {rec}")
        
        print(f"\n⚠️  Disclaimer Preview:")
        disclaimer_lines = result.disclaimer.strip().split('\n')
        for line in disclaimer_lines[:3]:
            if line.strip():
                print(f"  {line.strip()}")
        print("  [... full disclaimer included in API response]")
        
        print(f"\n✅ OMEGA Integration Test: SUCCESS")
        print(f"🎯 Real OMEGA prediction models are now integrated with FastAPI!")
        
        return True
        
    except Exception as e:
        print(f"❌ OMEGA Integration Test: FAILED")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 OMEGA Integration Test Suite")
    print("=" * 50)
    
    success = asyncio.run(test_omega_integration())
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! OMEGA is ready to serve statistical analysis.")
    else:
        print("🚨 Tests failed. Check the errors above.")
    
    sys.exit(0 if success else 1)