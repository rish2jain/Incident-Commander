#!/usr/bin/env python3
"""
Dashboard Test Script
Quick verification that all dashboard components are working
"""

import os
from pathlib import Path

def test_dashboard_files():
    """Test that all required dashboard files exist and are valid."""
    
    print("🧪 TESTING DASHBOARD COMPONENTS")
    print("=" * 50)
    
    dashboard_dir = Path(__file__).parent / "dashboard"
    
    # Check dashboard directory
    if not dashboard_dir.exists():
        print("❌ Dashboard directory not found!")
        return False
    
    print("✅ Dashboard directory found")
    
    # Required files
    required_files = {
        "standalone.html": "Self-contained dashboard (recommended)",
        "index.html": "Standard dashboard",
        "dashboard.js": "JavaScript functionality",
        "server.py": "Python web server",
        "simple_server.py": "Backup simple server"
    }
    
    found_files = []
    missing_files = []
    
    for filename, description in required_files.items():
        filepath = dashboard_dir / filename
        if filepath.exists():
            found_files.append((filename, description))
            print(f"✅ {filename} - {description}")
        else:
            missing_files.append((filename, description))
            print(f"❌ {filename} - {description}")
    
    # Check file contents
    print(f"\n📊 DASHBOARD FILE ANALYSIS:")
    print("=" * 30)
    
    # Check standalone.html
    standalone_file = dashboard_dir / "standalone.html"
    if standalone_file.exists():
        content = standalone_file.read_text()
        if "</html>" in content and "script>" in content and len(content) > 30000:
            print("✅ standalone.html - Complete self-contained dashboard")
        else:
            print("⚠️ standalone.html - File seems incomplete")
    
    # Check index.html
    index_file = dashboard_dir / "index.html"
    if index_file.exists():
        content = index_file.read_text()
        if "dashboard.js" in content:
            print("✅ index.html - Links to external JavaScript")
        else:
            print("⚠️ index.html - Missing JavaScript reference")
    
    # Summary
    print(f"\n📋 TEST SUMMARY:")
    print("=" * 20)
    print(f"✅ Files found: {len(found_files)}")
    print(f"❌ Files missing: {len(missing_files)}")
    
    if len(found_files) >= 2:  # At least standalone.html or index.html + dashboard.js
        print("\n🎉 DASHBOARD IS READY!")
        print("🚀 Use: python simple_dashboard.py")
        return True
    else:
        print("\n⚠️ DASHBOARD NEEDS ATTENTION")
        print("🔧 Some required files are missing")
        return False

def show_launch_options():
    """Show different ways to launch the dashboard."""
    
    print(f"\n🚀 DASHBOARD LAUNCH OPTIONS:")
    print("=" * 35)
    
    print("1️⃣ RECOMMENDED: Simple Launcher")
    print("   python simple_dashboard.py")
    print("   → Opens standalone dashboard directly")
    
    print("\n2️⃣ ALTERNATIVE: Direct File Opening")
    print("   → Navigate to dashboard/ folder")
    print("   → Double-click standalone.html")
    
    print("\n3️⃣ SERVER METHOD: HTTP Server")
    print("   cd dashboard")
    print("   python simple_server.py")
    print("   → Opens at http://localhost:8000")
    
    print("\n4️⃣ PYTHON BUILT-IN: Simple Server")
    print("   cd dashboard")
    print("   python -m http.server 8000")
    print("   → Opens at http://localhost:8000")

def main():
    """Run dashboard tests and show launch options."""
    
    # Test dashboard files
    dashboard_ready = test_dashboard_files()
    
    # Show launch options
    show_launch_options()
    
    # Final status
    print(f"\n" + "=" * 50)
    if dashboard_ready:
        print("🏆 DASHBOARD TEST PASSED!")
        print("🎯 Ready for hackathon demonstration!")
        print("🚀 Launch with: python simple_dashboard.py")
    else:
        print("⚠️ DASHBOARD TEST FAILED!")
        print("🔧 Check missing files and try again")
    
    return dashboard_ready

if __name__ == "__main__":
    main()