#!/usr/bin/env python3
"""
Simple HTTP server for the Autonomous Incident Commander Dashboard
Serves the interactive dashboard for hackathon demonstration
"""

import http.server
import socketserver
import os
import sys
import webbrowser
import threading
import time
from pathlib import Path

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for dashboard files with proper MIME types."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)
    
    def end_headers(self):
        # Add CORS headers for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight requests."""
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        """Custom log format."""
        print(f"🌐 Dashboard: {format % args}")

def start_dashboard_server(port=3000):
    """Start the dashboard server."""
    
    # Change to dashboard directory
    dashboard_dir = Path(__file__).parent
    os.chdir(dashboard_dir)
    
    print(f"🚀 Starting Autonomous Incident Commander Dashboard")
    print(f"📁 Serving from: {dashboard_dir}")
    print(f"🌐 Dashboard URL: http://localhost:{port}")
    print(f"📊 Open your browser to view the interactive demo")
    print("=" * 60)
    
    def open_browser():
        """Open browser after server starts."""
        time.sleep(2)
        try:
            webbrowser.open(f'http://localhost:{port}')
            print("🌐 Browser opened to dashboard")
        except Exception as e:
            print(f"⚠️  Could not open browser automatically: {e}")
            print(f"🔗 Please open http://localhost:{port} manually")
    
    # Start browser opener in background
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    try:
        with socketserver.TCPServer(("", port), DashboardHandler) as httpd:
            print(f"✅ Dashboard server running on port {port}")
            print(f"🎯 Ready for hackathon demonstration!")
            print("\\n🔧 Controls:")
            print("   • Click agent nodes to see details")
            print("   • Use scenario buttons to trigger incidents")
            print("   • Watch real-time MTTR countdown")
            print("   • Monitor agent swarm intelligence")
            print("\\n⏹️  Press Ctrl+C to stop the server")
            print("=" * 60)
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\\n🛑 Dashboard server stopped")
        print("👋 Thanks for using Autonomous Incident Commander!")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use")
            print(f"💡 Try a different port: python server.py --port 3001")
        else:
            print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Autonomous Incident Commander Dashboard Server')
    parser.add_argument('--port', type=int, default=3000, help='Port to serve dashboard (default: 3000)')
    
    args = parser.parse_args()
    
    start_dashboard_server(args.port)