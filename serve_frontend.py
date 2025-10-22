#!/usr/bin/env python3
"""
Simple HTTP server to serve the frontend files.
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = 3000
FRONTEND_DIR = Path(__file__).parent / "frontend"

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    if not FRONTEND_DIR.exists():
        print(f"❌ Frontend directory not found: {FRONTEND_DIR}")
        return
    
    print(f"🌐 Starting frontend server...")
    print(f"📁 Serving files from: {FRONTEND_DIR}")
    print(f"🔗 Frontend URL: http://localhost:{PORT}")
    print(f"🚀 Make sure the API server is running on port 8000")
    print(f"⏹️  Press Ctrl+C to stop the server")
    
    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            # Open browser automatically
            webbrowser.open(f'http://localhost:{PORT}')
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Frontend server stopped")

if __name__ == "__main__":
    main()