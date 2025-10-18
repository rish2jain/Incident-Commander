#!/usr/bin/env python3
"""
Autonomous Incident Commander - Live Demo Launcher
Starts backend and opens live dashboard for real agent demonstration
"""

import os
import sys
import time
import subprocess
import webbrowser
import threading
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = ['fastapi', 'uvicorn', 'websockets']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   • {package}")
        print("\n💡 Install with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def start_backend():
    """Start the FastAPI backend server."""
    print("🚀 Starting Autonomous Incident Commander Backend...")
    
    try:
        # Start backend server
        process = subprocess.Popen([
            sys.executable, "dashboard_backend.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Backend server started successfully")
            return process
        else:
            stdout, stderr = process.communicate()
            print("❌ Backend server failed to start")
            if stdout:
                print("Output:", stdout)
            if stderr:
                print("Error:", stderr)
            return None
            
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def open_dashboard():
    """Open the live dashboard in browser."""
    time.sleep(2)  # Wait for backend to be ready
    
    dashboard_url = "http://localhost:8000/dashboard/live_dashboard.html"
    
    try:
        webbrowser.open(dashboard_url)
        print(f"🌐 Dashboard opened: {dashboard_url}")
    except Exception as e:
        print(f"⚠️ Could not open browser automatically: {e}")
        print(f"🔗 Please open manually: {dashboard_url}")

def main():
    """Main demo launcher."""
    print("🎯 AUTONOMOUS INCIDENT COMMANDER - LIVE DEMO")
    print("=" * 60)
    print("🤖 Real Backend Integration with Agent Workflows")
    print("📊 Live Dashboard with WebSocket Updates")
    print("🎮 Interactive Incident Scenarios")
    print("=" * 60)
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        print("\\n❌ Please install missing dependencies and try again")
        return False
    
    print("✅ All dependencies found")
    
    # Check if backend file exists
    backend_file = Path("dashboard_backend.py")
    if not backend_file.exists():
        print("❌ Backend file not found: dashboard_backend.py")
        return False
    
    # Check if dashboard file exists
    dashboard_file = Path("dashboard/live_dashboard.html")
    if not dashboard_file.exists():
        print("❌ Dashboard file not found: dashboard/live_dashboard.html")
        return False
    
    print("✅ All required files found")
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        return False
    
    # Open dashboard in browser
    browser_thread = threading.Thread(target=open_dashboard, daemon=True)
    browser_thread.start()
    
    print("\\n🎉 LIVE DEMO READY!")
    print("=" * 40)
    print("🌐 Dashboard: http://localhost:8000/dashboard/live_dashboard.html")
    print("📡 API Docs: http://localhost:8000/docs")
    print("🔌 WebSocket: ws://localhost:8000/ws")
    print()
    print("🎮 DEMO FEATURES:")
    print("   • Real agent workflows and decision-making")
    print("   • Live WebSocket updates from backend")
    print("   • Actual incident processing logic")
    print("   • Real performance metrics calculation")
    print("   • Live agent activity feed")
    print("   • Interactive scenario triggers")
    print()
    print("🎯 HACKATHON DEMO SCRIPT:")
    print("   1. Show live agent activity feed")
    print("   2. Click 'Database Cascade' scenario")
    print("   3. Watch real agent workflows execute")
    print("   4. Show actual decision-making processes")
    print("   5. Demonstrate real performance metrics")
    print()
    print("⏹️  Press Ctrl+C to stop the demo")
    print("=" * 60)
    
    try:
        # Keep the main process running
        while True:
            time.sleep(1)
            
            # Check if backend is still running
            if backend_process.poll() is not None:
                print("\\n❌ Backend process stopped unexpectedly")
                break
                
    except KeyboardInterrupt:
        print("\\n🛑 Stopping live demo...")
        
        # Terminate backend process
        if backend_process:
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend_process.kill()
        
        print("✅ Demo stopped successfully")
        print("🏆 Ready for hackathon submission!")
    
    return True

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\\n❌ Demo failed to start")
        print("💡 Try running components manually:")
        print("   1. python dashboard_backend.py")
        print("   2. Open http://localhost:8000/dashboard/live_dashboard.html")
        sys.exit(1)
    else:
        print("\\n🎉 Demo completed successfully!")
        sys.exit(0)