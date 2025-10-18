#!/usr/bin/env python3
"""
Demo startup script for Incident Commander WebSocket integration.

Starts the FastAPI server and opens the live dashboard for testing.
"""

import asyncio
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


def start_fastapi_server():
    """Start the FastAPI server."""
    print("🚀 Starting FastAPI server...")
    
    # Start uvicorn server
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "src.main:app", 
        "--reload", 
        "--port", "8000",
        "--host", "0.0.0.0"
    ])
    
    return process


def start_dashboard_server():
    """Start a simple HTTP server for the dashboard."""
    print("🌐 Starting dashboard server...")
    
    dashboard_dir = Path("dashboard")
    
    # Start simple HTTP server for dashboard
    process = subprocess.Popen([
        sys.executable, "-m", "http.server", "3000"
    ], cwd=dashboard_dir)
    
    return process


def wait_for_server(url, timeout=30):
    """Wait for server to be ready."""
    import requests
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False


def main():
    """Start demo environment."""
    print("🎭 Starting Incident Commander Demo Environment")
    print("=" * 50)
    
    # Start FastAPI server
    api_process = start_fastapi_server()
    
    # Start dashboard server  
    dashboard_process = start_dashboard_server()
    
    try:
        # Wait for servers to start
        print("⏳ Waiting for servers to start...")
        
        if wait_for_server("http://localhost:8000/health"):
            print("✅ FastAPI server ready at http://localhost:8000")
        else:
            print("❌ FastAPI server failed to start")
            return
        
        if wait_for_server("http://localhost:3000"):
            print("✅ Dashboard server ready at http://localhost:3000")
        else:
            print("❌ Dashboard server failed to start")
            return
        
        # Open dashboard in browser
        dashboard_url = "http://localhost:3000/live_dashboard.html"
        print(f"🌐 Opening dashboard: {dashboard_url}")
        webbrowser.open(dashboard_url)
        
        print("\n" + "=" * 50)
        print("🎉 Demo environment ready!")
        print("📊 Dashboard: http://localhost:3000/live_dashboard.html")
        print("🔌 API: http://localhost:8000")
        print("📡 WebSocket: ws://localhost:8000/ws")
        print("\n💡 Try triggering a demo scenario from the dashboard!")
        print("Press Ctrl+C to stop...")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping demo environment...")
        
    finally:
        # Clean up processes
        api_process.terminate()
        dashboard_process.terminate()
        
        try:
            api_process.wait(timeout=5)
            dashboard_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            api_process.kill()
            dashboard_process.kill()
        
        print("✅ Demo environment stopped")


if __name__ == "__main__":
    main()