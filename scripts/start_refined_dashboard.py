#!/usr/bin/env python3
"""
Incident Commander - Refined Dashboard Startup Script

This script starts both the backend API server and the refined React dashboard.
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class DashboardManager:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.project_root = project_root
        self.dashboard_dir = self.project_root / "dashboard"
        
    def check_dependencies(self):
        """Check if required dependencies are available."""
        print("🔍 Checking dependencies...")
        
        # Check Python dependencies
        try:
            import fastapi
            import uvicorn
            print("✅ Python backend dependencies found")
        except ImportError as e:
            print(f"❌ Missing Python dependency: {e}")
            print("💡 Run: pip install -r requirements.txt")
            return False
        
        # Check Node.js
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"✅ Node.js found: {version}")
            else:
                print("❌ Node.js not found")
                return False
        except FileNotFoundError:
            print("❌ Node.js not installed")
            print("💡 Install Node.js 18+ from https://nodejs.org/")
            return False
        
        # Check if dashboard is built
        if not (self.dashboard_dir / "node_modules").exists():
            print("📦 Installing dashboard dependencies...")
            result = subprocess.run(
                ["npm", "install"], 
                cwd=self.dashboard_dir,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"❌ Failed to install dashboard dependencies: {result.stderr}")
                return False
            print("✅ Dashboard dependencies installed")
        
        return True
    
    def start_backend(self):
        """Start the FastAPI backend server."""
        print("🚀 Starting backend server...")
        
        # Change to project root directory
        os.chdir(self.project_root)
        
        # Start the backend server
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "src.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ]
        
        self.backend_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Monitor backend startup
        def monitor_backend():
            for line in iter(self.backend_process.stdout.readline, ''):
                if line:
                    print(f"[Backend] {line.rstrip()}")
                    if "Uvicorn running on" in line:
                        print("✅ Backend server started successfully")
        
        backend_thread = threading.Thread(target=monitor_backend, daemon=True)
        backend_thread.start()
        
        # Wait a moment for backend to start
        time.sleep(3)
        
        return self.backend_process.poll() is None
    
    def start_frontend(self):
        """Start the Next.js frontend dashboard."""
        print("🎨 Starting refined dashboard...")
        
        # Change to dashboard directory
        os.chdir(self.dashboard_dir)
        
        # Start the frontend server
        cmd = ["npm", "run", "dev"]
        
        self.frontend_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Monitor frontend startup
        def monitor_frontend():
            for line in iter(self.frontend_process.stdout.readline, ''):
                if line:
                    print(f"[Dashboard] {line.rstrip()}")
                    if "Ready" in line and "localhost:3000" in line:
                        print("✅ Refined dashboard started successfully")
        
        frontend_thread = threading.Thread(target=monitor_frontend, daemon=True)
        frontend_thread.start()
        
        return True
    
    def stop_services(self):
        """Stop both backend and frontend services."""
        print("\n🛑 Stopping services...")
        
        if self.backend_process:
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
                print("✅ Backend server stopped")
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                print("🔥 Backend server force killed")
        
        if self.frontend_process:
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
                print("✅ Dashboard stopped")
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
                print("🔥 Dashboard force killed")
    
    def run(self):
        """Main execution method."""
        print("🤖 Incident Commander - Refined Dashboard")
        print("=" * 50)
        
        # Check dependencies
        if not self.check_dependencies():
            sys.exit(1)
        
        # Setup signal handlers
        def signal_handler(signum, frame):
            self.stop_services()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Start backend
            if not self.start_backend():
                print("❌ Failed to start backend server")
                sys.exit(1)
            
            # Start frontend
            if not self.start_frontend():
                print("❌ Failed to start dashboard")
                sys.exit(1)
            
            print("\n🎉 Incident Commander is running!")
            print("=" * 50)
            print("🌐 Backend API:      http://localhost:8000")
            print("🎨 Refined Dashboard: http://localhost:3000")
            print("📚 API Documentation: http://localhost:8000/docs")
            print("🔌 WebSocket:        ws://localhost:8000/ws")
            print("\n💡 Press Ctrl+C to stop all services")
            print("=" * 50)
            
            # Keep the script running
            while True:
                time.sleep(1)
                
                # Check if processes are still running
                if self.backend_process and self.backend_process.poll() is not None:
                    print("❌ Backend process died unexpectedly")
                    break
                
                if self.frontend_process and self.frontend_process.poll() is not None:
                    print("❌ Frontend process died unexpectedly")
                    break
        
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        finally:
            self.stop_services()

def main():
    """Main entry point."""
    manager = DashboardManager()
    manager.run()

if __name__ == "__main__":
    main()