#!/usr/bin/env python3
"""
Quick Transparency Features Test

Tests the latest transparency improvements in the PowerDashboard component.
"""

import requests
import sys
from pathlib import Path

def test_dashboard_accessibility():
    """Test if dashboard is accessible."""
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        if response.status_code == 200:
            print("✅ Dashboard is accessible")
            return True
        else:
            print(f"❌ Dashboard returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dashboard not accessible: {e}")
        print("   Please start: cd dashboard && npm run dev")
        return False

def test_powerdashboard_component():
    """Test PowerDashboard component for transparency features."""
    component_path = Path("dashboard/src/components/PowerDashboard.tsx")
    
    if not component_path.exists():
        print(f"❌ PowerDashboard component not found: {component_path}")
        return False
    
    print("🔍 Checking PowerDashboard component for transparency features...")
    
    with open(component_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for mock labels
    mock_indicators = [
        "Incidents Resolved Today (mock)",
        "Average Resolution (mock)",
        "Zero-Touch Streak: 47 (mock)",
        "Multi-Agent Status (Mock)"
    ]
    
    found_indicators = []
    missing_indicators = []
    
    for indicator in mock_indicators:
        if indicator in content:
            found_indicators.append(indicator)
            print(f"   ✅ Found: {indicator}")
        else:
            missing_indicators.append(indicator)
            print(f"   ❌ Missing: {indicator}")
    
    if missing_indicators:
        print(f"❌ PowerDashboard transparency test FAILED")
        print(f"   Missing {len(missing_indicators)} mock labels")
        return False
    else:
        print(f"✅ PowerDashboard transparency test PASSED")
        print(f"   All {len(found_indicators)} mock labels found")
        return True

def test_transparency_validation_script():
    """Test if transparency validation script exists."""
    script_path = Path("hackathon/validate_transparency_improvements.py")
    
    if script_path.exists():
        print("✅ Transparency validation script exists")
        return True
    else:
        print("❌ Transparency validation script missing")
        return False

def main():
    """Run transparency features tests."""
    print("🔍 Testing Transparency Features")
    print("=" * 50)
    
    tests = [
        ("Dashboard Accessibility", test_dashboard_accessibility),
        ("PowerDashboard Component", test_powerdashboard_component),
        ("Validation Script", test_transparency_validation_script)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Testing {test_name}...")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TRANSPARENCY TESTS PASSED!")
        print("   System ready with transparency improvements")
        return True
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        print("   Review individual test results")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)