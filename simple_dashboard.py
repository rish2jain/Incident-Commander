#!/usr/bin/env python3
"""
Simple Dashboard Launcher - Direct File Opening Method
Alternative launcher that opens the standalone dashboard directly
"""

import os
import sys
import webbrowser
import time
import threading
from pathlib import Path

def main():
    print("🚀 AUTONOMOUS INCIDENT COMMANDER - SIMPLE DASHBOARD LAUNCHER")
    print("=" * 65)
    
    # Get dashboard directory
    dashboard_dir = Path(__file__).parent / "dashboard"
    
    if not dashboard_dir.exists():
        print("❌ Dashboard directory not found!")
        print(f"Expected: {dashboard_dir}")
        return
    
    # Check if standalone.html exists (preferred) or fall back to index.html
    standalone_file = dashboard_dir / "standalone.html"
    index_file = dashboard_dir / "index.html"
    
    if standalone_file.exists():
        dashboard_file = standalone_file
        print("✅ Using standalone dashboard (recommended)")
    elif index_file.exists():
        dashboard_file = index_file
        print("✅ Using standard dashboard")
    else:
        print(f"❌ Dashboard files not found in: {dashboard_dir}")
        return
    
    print(f"📁 Dashboard location: {dashboard_dir}")
    
    # Try to open the dashboard
    print("\n🎯 LAUNCHING DASHBOARD...")
    print("=" * 40)
    
    file_url = f"file://{dashboard_file.absolute()}"
    print(f"🌐 Dashboard URL: {file_url}")
    
    try:
        webbrowser.open(file_url)
        print("✅ Dashboard opened in browser!")
        
        print("\n🎮 DASHBOARD FEATURES:")
        print("   • Multi-Agent Swarm Visualization")
        print("   • Real-Time MTTR Counter")
        print("   • Interactive Scenario Triggers")
        print("   • Live Performance Metrics")
        print("   • Business Impact Calculator")
        
        print("\n🎯 DEMO INSTRUCTIONS:")
        print("   • Click agent nodes to see details")
        print("   • Use scenario buttons to trigger incidents")
        print("   • Watch real-time MTTR countdown")
        print("   • Monitor performance metrics")
        
        print("\n🏆 HACKATHON DEMO READY!")
        print("=" * 40)
        print("🎪 Perfect for judge demonstrations!")
        print("🎯 Click 'Database Cascade' to start a live demo")
        print("🤖 Watch the multi-agent swarm in action")
        print("⏱️  See sub-3-minute MTTR in real-time")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Could not open browser automatically: {e}")
        
        print("\n📋 MANUAL INSTRUCTIONS:")
        print("=" * 30)
        print(f"1. Open your web browser")
        print(f"2. Copy and paste this URL:")
        print(f"   {file_url}")
        print(f"3. Or navigate to the dashboard folder and double-click:")
        print(f"   {dashboard_file.name}")
        
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n" + "=" * 65)
        print("🎉 DASHBOARD LAUNCHED SUCCESSFULLY!")
        print("🏆 Ready to win the hackathon!")
    else:
        print("\n" + "=" * 65)
        print("⚠️  Manual launch required - see instructions above")
        print("🏆 Dashboard is ready once opened!")