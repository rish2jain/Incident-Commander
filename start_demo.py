#!/usr/bin/env python3
"""
Demo startup script for Incident Commander WebSocket integration.

Starts the FastAPI server and opens the live dashboard for testing.
"""

import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


API_BASE = os.environ.get("HACKATHON_API_URL", "http://localhost:8000")
DASHBOARD_PORT = int(os.environ.get("HACKATHON_DASHBOARD_PORT", "3000"))
DASHBOARD_BASE = os.environ.get(
    "HACKATHON_DASHBOARD_BASE",
    f"http://localhost:{DASHBOARD_PORT}"
)
DASHBOARD_PAGE = os.environ.get(
    "HACKATHON_DASHBOARD_URL",
    f"{DASHBOARD_BASE}/comprehensive_demo_dashboard.html"
)
WEBSOCKET_URL = os.environ.get(
    "HACKATHON_WEBSOCKET_URL",
    API_BASE.replace("http", "ws") + "/dashboard/ws"
)


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
        sys.executable, "-m", "http.server", str(DASHBOARD_PORT)
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
        
        if wait_for_server(f"{API_BASE.rstrip('/')}/health"):
            print(f"✅ FastAPI server ready at {API_BASE}")
        else:
            print("❌ FastAPI server failed to start")
            return
        
        if wait_for_server(DASHBOARD_BASE):
            print(f"✅ Dashboard server ready at {DASHBOARD_BASE}")
        else:
            print("❌ Dashboard server failed to start")
            return
        
        # Open dashboard in browser
        print(f"🌐 Opening dashboard: {DASHBOARD_PAGE}")
        webbrowser.open(DASHBOARD_PAGE)
        
        print("\n" + "=" * 50)
        print("🎉 Demo environment ready!")
        print(f"📊 Dashboard: {DASHBOARD_PAGE}")
        print(f"🔌 API: {API_BASE}")
        print(f"📡 WebSocket: {WEBSOCKET_URL}")
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
