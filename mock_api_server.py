#!/usr/bin/env python3
"""
Mock API Server for Integration Testing
Provides health endpoints and basic API functionality for testing
"""

from flask import Flask, jsonify, request
import time
import threading
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock server start time
start_time = time.time()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    uptime = time.time() - start_time
    return jsonify({
        'status': 'healthy',
        'uptime': round(uptime, 2),
        'service': 'omega-api-mock',
        'version': '1.0.0',
        'timestamp': time.time()
    })

@app.route('/api/v1/health', methods=['GET'])
def api_health():
    """API health check endpoint"""
    return jsonify({
        'api_status': 'operational',
        'endpoints_available': ['/health', '/api/v1/health', '/api/v1/predict'],
        'last_check': time.time()
    })

@app.route('/api/v1/predict', methods=['POST'])
def predict():
    """Mock prediction endpoint"""
    return jsonify({
        'prediction': 'mock_response',
        'confidence': 0.85,
        'timestamp': time.time(),
        'status': 'success'
    })

@app.route('/ssl/cert.pem', methods=['GET'])
def get_certificate():
    """Serve SSL certificate for testing"""
    try:
        with open('ssl/cert.pem', 'r') as f:
            cert_content = f.read()
        return cert_content, 200, {'Content-Type': 'text/plain'}
    except FileNotFoundError:
        return jsonify({'error': 'Certificate not found'}), 404

@app.route('/ssl/bundle.pem', methods=['GET']) 
def get_certificate_bundle():
    """Serve SSL certificate bundle for testing"""
    try:
        with open('ssl/bundle.pem', 'r') as f:
            bundle_content = f.read()
        return bundle_content, 200, {'Content-Type': 'text/plain'}
    except FileNotFoundError:
        return jsonify({'error': 'Certificate bundle not found'}), 404

@app.after_request
def after_request(response):
    """Add security headers"""
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Server'] = 'Omega-Mock-API/1.0'
    return response

if __name__ == '__main__':
    print("🚀 Starting Mock API Server for Integration Testing")
    print("Available endpoints:")
    print("  - GET  /health")
    print("  - GET  /api/v1/health") 
    print("  - POST /api/v1/predict")
    print("  - GET  /ssl/cert.pem")
    print("  - GET  /ssl/bundle.pem")
    print("\nServer starting on http://localhost:8001")
    
    app.run(host='0.0.0.0', port=8001, debug=False)