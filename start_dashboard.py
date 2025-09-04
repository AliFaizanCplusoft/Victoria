#!/usr/bin/env python3
"""
Simple HTTP server to serve the ML dashboard locally
This avoids CORS issues when loading CSV files
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

# Change to the directory containing the dashboard
os.chdir(Path(__file__).parent)

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def start_server():
    """Start the HTTP server and open the dashboard in browser"""
    
    # Check if dashboard file exists
    if not os.path.exists('ml_dashboard.html'):
        print("❌ Error: ml_dashboard.html not found!")
        print("Please run this script from the Victoria Project directory.")
        sys.exit(1)
    
    # Start server
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"🚀 Starting ML Dashboard server...")
        print(f"📊 Dashboard URL: http://localhost:{PORT}/ml_dashboard.html")
        print(f"📁 Serving files from: {os.getcwd()}")
        print(f"🔗 Opening dashboard in browser...")
        print(f"⚠️  Press Ctrl+C to stop the server")
        
        # Open dashboard in browser
        webbrowser.open(f'http://localhost:{PORT}/ml_dashboard.html')
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
            httpd.shutdown()

if __name__ == "__main__":
    start_server()