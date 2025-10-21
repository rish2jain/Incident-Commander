#!/usr/bin/env python3
"""
Test script for demo recorder
Validates setup and configuration without running full demo
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

import yaml


async def test_playwright_installation():
    """Test if Playwright is installed and browsers are available"""
    print("\n🧪 Testing Playwright Installation...")

    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright not installed")
        print("   Install with: pip install playwright")
        return False

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            await browser.close()
            print("✅ Playwright and Chromium browser installed")
            return True
    except Exception as e:
        print(f"❌ Playwright browser error: {e}")
        print("   Install browsers with: playwright install chromium")
        return False


def test_configuration():
    """Test if configuration file exists and is valid"""
    print("\n🧪 Testing Configuration...")

    config_path = Path(__file__).parent / "demo_recorder_config.yaml"

    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return False

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)

        required_keys = ['dashboard', 'video', 'screenshots', 'scenarios']
        for key in required_keys:
            if key not in config:
                print(f"❌ Missing configuration key: {key}")
                return False

        print("✅ Configuration file valid")
        return True

    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def test_output_directories():
    """Test if output directories can be created"""
    print("\n🧪 Testing Output Directories...")

    base_dir = Path("demo_recordings_test")

    try:
        # Create test directories
        for subdir in ["videos", "screenshots", "metrics"]:
            (base_dir / subdir).mkdir(parents=True, exist_ok=True)

        print("✅ Output directories created successfully")

        # Cleanup test directories
        import shutil
        shutil.rmtree(base_dir)

        return True

    except Exception as e:
        print(f"❌ Directory creation error: {e}")
        return False


async def test_dashboard_connection():
    """Test connection to dashboard"""
    print("\n🧪 Testing Dashboard Connection...")

    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    "http://localhost:3000",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        print("✅ Dashboard is running at http://localhost:3000")
                        return True
                    else:
                        print(f"⚠️ Dashboard returned status {response.status}")
                        return False
            except asyncio.TimeoutError:
                print("⚠️ Dashboard connection timeout")
                print("   Start dashboard with: cd dashboard && npm run dev")
                return False
            except Exception as e:
                print(f"⚠️ Dashboard not accessible: {e}")
                print("   Start dashboard with: cd dashboard && npm run dev")
                return False

    except ImportError:
        print("⚠️ aiohttp not installed (optional for testing)")
        print("   Install with: pip install aiohttp")
        return None


async def test_backend_connection():
    """Test connection to backend API"""
    print("\n🧪 Testing Backend Connection...")

    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    "http://localhost:8000/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        print("✅ Backend API is running at http://localhost:8000")
                        return True
                    else:
                        print(f"⚠️ Backend returned status {response.status}")
                        return False
            except asyncio.TimeoutError:
                print("⚠️ Backend connection timeout")
                print("   Start backend with: python -m uvicorn src.main:app --reload")
                return False
            except Exception as e:
                print(f"⚠️ Backend not accessible: {e}")
                print("   Start backend with: python -m uvicorn src.main:app --reload")
                return False

    except ImportError:
        print("⚠️ aiohttp not installed (optional for testing)")
        return None


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 DEMO RECORDER - VALIDATION TESTS")
    print("="*80)

    results = {
        "Playwright Installation": await test_playwright_installation(),
        "Configuration File": test_configuration(),
        "Output Directories": test_output_directories(),
        "Dashboard Connection": await test_dashboard_connection(),
        "Backend Connection": await test_backend_connection(),
    }

    # Print summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)

    passed = 0
    failed = 0
    warnings = 0

    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
            passed += 1
        elif result is False:
            status = "❌ FAIL"
            failed += 1
        else:
            status = "⚠️ SKIP"
            warnings += 1

        print(f"{status:10} {test_name}")

    print("\n" + "-"*80)
    print(f"Total: {passed} passed, {failed} failed, {warnings} skipped")
    print("="*80)

    # Overall status
    if failed == 0:
        print("\n✅ All critical tests passed! Ready to record demos.")
        print("\n🎬 Run demo with: ./run_demo_recording.sh")
    elif failed <= 2 and (
        results.get("Playwright Installation") and
        results.get("Configuration File")
    ):
        print("\n⚠️ Some tests failed, but core functionality is ready.")
        print("   Dashboard and Backend connections are optional for testing.")
        print("\n🎬 Start services and run: ./run_demo_recording.sh")
    else:
        print("\n❌ Critical tests failed. Please fix issues before recording.")
        print("\n📋 Next steps:")
        if not results.get("Playwright Installation"):
            print("   1. pip install playwright")
            print("   2. playwright install chromium")
        if not results.get("Configuration File"):
            print("   3. Check demo_recorder_config.yaml exists")

    print("")
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
