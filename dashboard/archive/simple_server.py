#!/usr/bin/env python3
"""
Simple HTTP Server for Dashboard
Minimal server that should work on all systems
"""

import http.server
import socketserver
import os
import webbrowser
import threading
import time

def start_server(port=8000):
    """Start a simple HTTP server."""
    
    class SimpleHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            print(f"📡 {format % args}")
    
    print(f"🚀 Starting Simple Dashboard Server")
    print(f"📁 Serving from: {os.getcwd()}")
    print(f"🌐 URL: http://localhost:{port}")
    
    try:
        with socketserver.TCPServer(("", port), SimpleHandler) as httpd:
            print(f"✅ Server running on port {port}")
            print(f"🎯 Dashboard ready at: http://localhost:{port}")
            print(f"⏹️  Press Ctrl+C to stop")
            
            # Open browser after 2 seconds
            def open_browser():
                time.sleep(2)
                try:
                    webbrowser.open(f'http://localhost:{port}')
                    print("🌐 Browser opened")
                except:
                    print("⚠️ Please open browser manually")
            
            threading.Thread(target=open_browser, daemon=True).start()
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\\n🛑 Server stopped")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is busy. Trying port {port + 1}...")
            start_server(port + 1)
        else:
            print(f"❌ Server error: {e}")

if __name__ == "__main__":
    start_server()