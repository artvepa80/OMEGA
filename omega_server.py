#!/usr/bin/env python3
"""
OMEGA PRO AI v10.1 - Railway Server
Simple HTTP server wrapper for Railway deployment
"""

import os
import sys
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import subprocess
import traceback

# Add OMEGA to Python path
sys.path.append('/app')

# Import OMEGA modules
try:
    from main import *  # Import main OMEGA functionality
    OMEGA_LOADED = True
except ImportError as e:
    print(f"⚠️  Error loading OMEGA: {e}")
    OMEGA_LOADED = False

# Server configuration
PORT = int(os.environ.get('PORT', 8000))
OMEGA_VERSION = os.environ.get('OMEGA_VERSION', 'v10.1')

class OmegaHandler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        """Custom logging"""
        print(f"🌐 {self.address_string()} - {format % args}")
    
    def do_GET(self):
        """Handle GET requests"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        try:
            if path == '/health':
                self.send_health_check()
            elif path == '/':
                self.send_home()
            elif path == '/status':
                self.send_status()
            elif path == '/predict':
                self.send_prediction()
            else:
                self.send_404()
        except Exception as e:
            self.send_error_response(str(e))
    
    def do_POST(self):
        """Handle POST requests"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        try:
            if path == '/predict':
                self.handle_prediction_post()
            else:
                self.send_404()
        except Exception as e:
            self.send_error_response(str(e))
    
    def send_health_check(self):
        """Health check endpoint"""
        health_data = {
            "status": "healthy",
            "omega_version": OMEGA_VERSION,
            "omega_loaded": OMEGA_LOADED,
            "timestamp": int(time.time()),
            "system": {
                "python_version": sys.version.split()[0],
                "working_directory": os.getcwd(),
                "omega_files": len([f for f in os.listdir('.') if f.endswith('.py')])
            }
        }
        
        # Test core imports
        try:
            import core.predictor
            health_data["core_predictor"] = "OK"
        except:
            health_data["core_predictor"] = "WARNING"
        
        try:
            import modules.lstm_model
            health_data["lstm_model"] = "OK"
        except:
            health_data["lstm_model"] = "WARNING"
        
        self.send_json_response(health_data)
    
    def send_home(self):
        """Home page"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OMEGA PRO AI {OMEGA_VERSION}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
                h1 {{ color: #333; }}
                .status {{ background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .endpoint {{ background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px; font-family: monospace; }}
                .footer {{ margin-top: 30px; text-align: center; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 OMEGA PRO AI {OMEGA_VERSION}</h1>
                <div class="status">
                    <strong>✅ Sistema funcionando correctamente</strong><br>
                    OMEGA Loaded: {"✅ YES" if OMEGA_LOADED else "⚠️ NO"}<br>
                    Python Files: {len([f for f in os.listdir('.') if f.endswith('.py')])}<br>
                    Port: {PORT}
                </div>
                
                <h2>🔗 API Endpoints:</h2>
                <div class="endpoint">GET /health - Health check</div>
                <div class="endpoint">GET /status - System status</div>
                <div class="endpoint">GET /predict - Quick prediction</div>
                <div class="endpoint">POST /predict - Advanced prediction</div>
                
                <h2>🧪 Quick Test:</h2>
                <p><a href="/health" target="_blank">🔍 Check Health</a></p>
                <p><a href="/status" target="_blank">📊 System Status</a></p>
                <p><a href="/predict" target="_blank">🎯 Quick Predict</a></p>
                
                <div class="footer">
                    <p>🚀 Deployed on Railway | 🧠 Powered by OMEGA AI</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_status(self):
        """System status"""
        status_data = {
            "omega_version": OMEGA_VERSION,
            "omega_loaded": OMEGA_LOADED,
            "system_info": {
                "python_version": sys.version,
                "working_directory": os.getcwd(),
                "python_path": sys.path[:3],
                "environment": dict(os.environ)
            },
            "files_info": {
                "total_python_files": len([f for f in os.listdir('.') if f.endswith('.py')]),
                "core_exists": os.path.exists('core'),
                "modules_exists": os.path.exists('modules'),
                "data_exists": os.path.exists('data'),
                "main_py_exists": os.path.exists('main.py')
            }
        }
        
        self.send_json_response(status_data)
    
    def send_prediction(self):
        """Simple prediction endpoint"""
        if not OMEGA_LOADED:
            self.send_json_response({
                "error": "OMEGA not loaded",
                "message": "System not ready for predictions"
            }, 503)
            return
        
        try:
            # Simple prediction using OMEGA
            result = {
                "prediction": "Demo prediction from OMEGA",
                "timestamp": int(time.time()),
                "version": OMEGA_VERSION,
                "status": "success",
                "message": "OMEGA AI is running on Railway!"
            }
            
            self.send_json_response(result)
            
        except Exception as e:
            self.send_json_response({
                "error": str(e),
                "traceback": traceback.format_exc()
            }, 500)
    
    def handle_prediction_post(self):
        """Handle POST prediction requests"""
        if not OMEGA_LOADED:
            self.send_json_response({
                "error": "OMEGA not loaded"
            }, 503)
            return
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Parse JSON data
            if content_length > 0:
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
            
            # Process prediction request
            result = {
                "prediction": f"Advanced prediction for: {data}",
                "timestamp": int(time.time()),
                "version": OMEGA_VERSION,
                "input_data": data,
                "status": "success"
            }
            
            self.send_json_response(result)
            
        except Exception as e:
            self.send_json_response({
                "error": str(e),
                "traceback": traceback.format_exc()
            }, 500)
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response"""
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))
    
    def send_404(self):
        """Send 404 response"""
        self.send_json_response({
            "error": "Not Found",
            "message": f"Path {self.path} not found",
            "available_endpoints": ["/", "/health", "/status", "/predict"]
        }, 404)
    
    def send_error_response(self, error_message):
        """Send error response"""
        self.send_json_response({
            "error": "Internal Server Error",
            "message": error_message,
            "traceback": traceback.format_exc()
        }, 500)

def main():
    """Start OMEGA server"""
    print(f"🚀 Starting OMEGA PRO AI {OMEGA_VERSION} Server")
    print(f"📁 Working Directory: {os.getcwd()}")
    print(f"🐍 Python Version: {sys.version.split()[0]}")
    print(f"🔧 OMEGA Loaded: {'✅ YES' if OMEGA_LOADED else '⚠️ NO'}")
    print(f"📊 Python Files: {len([f for f in os.listdir('.') if f.endswith('.py')])}")
    print(f"🌐 Starting server on port {PORT}")
    
    # Create HTTP server
    server = HTTPServer(('0.0.0.0', PORT), OmegaHandler)
    
    try:
        print(f"✅ OMEGA Server ready!")
        print(f"🔗 Health check: http://localhost:{PORT}/health")
        print(f"🏠 Home page: http://localhost:{PORT}/")
        print("=" * 50)
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down OMEGA server...")
        server.shutdown()
    except Exception as e:
        print(f"❌ Server error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()