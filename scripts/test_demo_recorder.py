#!/usr/bin/env python3
"""
Test script for the 3-minute demo recorder

This script tests the recorder functionality without full video recording.
"""

import asyncio
import sys
from pathlib import Path

# Add the scripts directory to the path
sys.path.append(str(Path(__file__).parent))

from definitive_demo_recorder import ThreeMinuteDemoRecorder


async def test_recorder():
    """Test the recorder initialization and basic functionality"""
    
    print("🧪 Testing 3-Minute Demo Recorder")
    print("="*50)
    
    # Test initialization
    recorder = ThreeMinuteDemoRecorder(mode="screenshots")
    
    print(f"✅ Recorder initialized")
    print(f"   Session ID: {recorder.session_id}")
    print(f"   Mode: {recorder.mode}")
    print(f"   Base URL: {recorder.base_url}")
    
    # Test script timing
    print(f"\n📋 Script Timing Structure:")
    for scene, timing in recorder.script_timing.items():
        print(f"   {scene}: {timing['start']}s-{timing['end']}s ({timing['duration']}s)")
    
    # Test voiceover script
    print(f"\n🎙️  Voiceover Script Loaded:")
    for scene, script in recorder.voiceover_script.items():
        print(f"   {scene}: {len(script)} characters")
    
    # Verify total duration
    total_duration = sum(timing['duration'] for timing in recorder.script_timing.values())
    print(f"\n⏱️  Total Duration: {total_duration}s (Target: 180s)")
    
    if total_duration == 180:
        print("✅ Perfect timing alignment!")
    else:
        print(f"⚠️  Timing mismatch: {total_duration - 180}s difference")
    
    # Test directory creation
    print(f"\n📁 Output Directories:")
    for dir_name in ['screenshots_dir', 'videos_dir', 'metrics_dir']:
        dir_path = getattr(recorder, dir_name)
        exists = dir_path.exists()
        print(f"   {dir_name}: {dir_path} {'✅' if exists else '❌'}")
    
    print(f"\n🎉 Recorder test complete - Ready for demo recording!")


if __name__ == "__main__":
    asyncio.run(test_recorder())