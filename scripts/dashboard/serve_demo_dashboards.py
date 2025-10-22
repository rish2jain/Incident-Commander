#!/usr/bin/env python3
"""
Demo Dashboard Server

Serves the visual dashboards for hackathon demonstration.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path


class DemoDashboardServer:
    """Simple server for demo dashboards."""
    
    def __init__(self, port=8080):
        self.port = port
        self.dashboard_dir = Path(__file__).resolve().parent.parent.parent / "dashboard"
        
    def start_server(self):
        """Start the dashboard server."""
        if not self.dashboard_dir.exists():
            print("❌ Dashboard directory not found!")
            return False
            
        try:
            import functools
            handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(self.dashboard_dir))
            with socketserver.TCPServer(("", self.port), handler) as httpd:
                print(f"🚀 Demo Dashboard Server Started!")
                print(f"🏆 Comprehensive Dashboard: http://localhost:{self.port}/comprehensive_demo_dashboard.html")
                print(f"📊 Business Impact Dashboard: http://localhost:{self.port}/value_dashboard.html")
                print(f"🤖 Technical Dashboard: http://localhost:{self.port}/refined_dashboard.html")
                print(f"📋 All Files: http://localhost:{self.port}/")
                print(f"\n💡 Press Ctrl+C to stop the server")
                print(f"\n🎯 RECOMMENDED: Use Comprehensive Dashboard for maximum impact!")
                
                # Auto-open browser to comprehensive dashboard
                webbrowser.open(f"http://localhost:{self.port}/comprehensive_demo_dashboard.html")
                
                httpd.serve_forever()
                
        except KeyboardInterrupt:
            print("\n⏹️  Server stopped")
            return True
        except Exception as e:
            print(f"❌ Server error: {e}")
            return False


def main():
    """Main function."""
    print("🎬 HACKATHON DEMO DASHBOARD SERVER")
    print("=" * 50)
    
    server = DemoDashboardServer()
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()