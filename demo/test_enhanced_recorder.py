#!/usr/bin/env python3
"""
Test script for the enhanced demo recorder.
Validates configuration and system readiness.
"""

import asyncio
import sys
from pathlib import Path

# Import the enhanced recorder
from record_demo import EnhancedDemoRecorder, DEMO_SCENARIOS, BUSINESS_METRICS, AWS_AI_SERVICES

async def test_recorder_setup():
    """Test the enhanced recorder setup."""
    print("🧪 Testing Enhanced Demo Recorder Setup")
    print("=" * 50)
    
    recorder = EnhancedDemoRecorder()
    
    # Test directory creation
    assert recorder.output_dir.exists(), "Output directory not created"
    assert recorder.videos_dir.exists(), "Videos directory not created"
    assert recorder.screenshots_dir.exists(), "Screenshots directory not created"
    assert recorder.metrics_dir.exists(), "Metrics directory not created"
    
    print("✅ Directory structure created successfully")
    
    # Test configuration
    assert len(DEMO_SCENARIOS) == 5, f"Expected 5 scenarios, got {len(DEMO_SCENARIOS)}"
    assert len(AWS_AI_SERVICES) == 8, f"Expected 8 AWS services, got {len(AWS_AI_SERVICES)}"
    assert 'annual_savings' in BUSINESS_METRICS, "Business metrics missing annual_savings"
    
    print("✅ Configuration validation passed")
    
    # Test scenario structure
    for scenario in DEMO_SCENARIOS:
        required_keys = ['name', 'url', 'duration', 'description', 'business_focus', 'actions', 'key_points']
        for key in required_keys:
            assert key in scenario, f"Scenario {scenario.get('name', 'unknown')} missing key: {key}"
    
    print("✅ Scenario structure validation passed")
    
    print("\n🎉 All tests passed! Enhanced recorder is ready for use.")
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_recorder_setup())
        if result:
            print("\n✅ Enhanced Demo Recorder is ready for hackathon submission!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)