#!/usr/bin/env python3
"""
🚀 Railway Startup Script for OMEGA
Handles port configuration correctly
"""

import os
import subprocess
import sys

def start_server():
    """Start the server with proper port handling"""
    
    # Get port from environment or use default
    port = os.environ.get('PORT', '8000')
    
    print(f"🚀 Starting OMEGA server on port {port}")
    
    # Check if we have a main.py with FastAPI app
    if os.path.exists('main.py'):
        # Start with uvicorn
        cmd = [
            'uvicorn', 
            'main:app',
            '--host', '0.0.0.0',
            '--port', port
        ]
    else:
        print("❌ main.py not found!")
        sys.exit(1)
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("🛑 Server stopped by user")

if __name__ == "__main__":
    start_server()