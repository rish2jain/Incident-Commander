#!/usr/bin/env python3
"""
Test script for the Comprehensive Demo Recorder
Validates functionality and provides usage examples
"""

import asyncio
import sys
from pathlib import Path

# Add the scripts directory to the path
sys.path.append(str(Path(__file__).parent))

from comprehensive_demo_recorder import ComprehensiveDemoRecorder


async def test_dashboard_availability():
    """Test if the dashboard is available"""
    print("🧪 Testing Dashboard Availability")
    print("=" * 50)
    
    recorder = ComprehensiveDemoRecorder()
    is_available = await recorder.check_dashboard_availability()
    
    if is_available:
        print("✅ Dashboard is available and ready for recording")
        return True
    else:
        print("❌ Dashboard is not available")
        print("💡 Start the dashboard with: cd dashboard && npm run dev")
        return False


async def test_directory_creation():
    """Test if output directories are created properly"""
    print("\n🧪 Testing Directory Creation")
    print("=" * 50)
    
    recorder = ComprehensiveDemoRecorder()
    
    # Check if directories exist
    directories = [
        recorder.output_dir,
        recorder.screenshots_dir,
        recorder.videos_dir,
        recorder.metrics_dir
    ]
    
    all_exist = True
    for directory in directories:
        if directory.exists():
            print(f"✅ {directory} exists")
        else:
            print(f"❌ {directory} does not exist")
            all_exist = False
    
    return all_exist


async def test_feature_list():
    """Test if the feature list is comprehensive"""
    print("\n🧪 Testing Feature List")
    print("=" * 50)
    
    recorder = ComprehensiveDemoRecorder()
    
    expected_features = [
        "Next.js",
        "TypeScript", 
        "WebSocket",
        "AWS AI",
        "Byzantine",
        "Multi-agent",
        "validation",
        "incident management"
    ]
    
    feature_text = " ".join(recorder.current_features).lower()
    
    missing_features = []
    for feature in expected_features:
        if feature.lower() not in feature_text:
            missing_features.append(feature)
    
    if not missing_features:
        print("✅ All expected features are mentioned")
        print(f"📊 Total features listed: {len(recorder.current_features)}")
        return True
    else:
        print(f"❌ Missing features: {missing_features}")
        return False


async def run_quick_demo_test():
    """Run a quick demo test (without full recording)"""
    print("\n🧪 Running Quick Demo Test")
    print("=" * 50)
    
    # Only test if dashboard is available
    recorder = ComprehensiveDemoRecorder()
    
    if not await recorder.check_dashboard_availability():
        print("⚠️  Skipping demo test - dashboard not available")
        return False
    
    try:
        # Test screenshot capture functionality
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            page = await context.new_page()
            
            # Navigate to dashboard
            await page.goto(f"{recorder.base_url}/")
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Test screenshot capture
            await recorder.capture_screenshot(
                page, 
                "test_screenshot", 
                "Test screenshot for validation"
            )
            
            await context.close()
            await browser.close()
            
        print("✅ Quick demo test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Quick demo test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🎬 COMPREHENSIVE DEMO RECORDER - TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Directory Creation", test_directory_creation),
        ("Feature List", test_feature_list),
        ("Dashboard Availability", test_dashboard_availability),
        ("Quick Demo Test", run_quick_demo_test)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Demo recorder is ready to use.")
        print("\n🚀 To run the full demo recording:")
        print("   python scripts/comprehensive_demo_recorder.py")
    else:
        print("⚠️  Some tests failed. Please address the issues before recording.")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())