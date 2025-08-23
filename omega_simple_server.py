#!/usr/bin/env python3
"""
OMEGA Web Interface - Simple HTTP Server
Sirve la interfaz web con CORS habilitado
"""

import http.server
import socketserver
import json
import urllib.request
import urllib.parse
from urllib.error import URLError
import webbrowser
import threading
import time

PORT = 8080
OMEGA_API = "https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win"
API_KEY = "ac.sk.production.a16cbf***c4cad7"

class OmegaHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.get_html_content().encode())
        elif self.path == '/api/predict':
            self.proxy_to_omega('predict', 'POST')
        elif self.path == '/api/health':
            self.proxy_to_omega('health', 'GET')
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/api/predict':
            self.proxy_to_omega('predict', 'POST')
        else:
            super().do_POST()
    
    def proxy_to_omega(self, endpoint, method):
        try:
            url = f"{OMEGA_API}/{endpoint}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {API_KEY}'
            }
            
            if method == 'POST':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                req = urllib.request.Request(url, data=post_data, headers=headers, method=method)
            else:
                req = urllib.request.Request(url, headers=headers, method=method)
            
            with urllib.request.urlopen(req) as response:
                data = response.read()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(data)
                
        except URLError as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = json.dumps({'error': str(e)})
            self.wfile.write(error_response.encode())
    
    def get_html_content(self):
        return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OMEGA PRO AI v10.1 - Cliente Web</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        .status {
            background: rgba(0, 255, 0, 0.2);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
        button {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 18px;
            border-radius: 25px;
            cursor: pointer;
            width: 100%;
            margin: 10px 0;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }
        button:disabled {
            background: #666;
            cursor: not-allowed;
            transform: none;
        }
        .loading {
            text-align: center;
            font-size: 18px;
            color: #ffd700;
        }
        .predictions {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }
        .prediction-item {
            background: rgba(255, 255, 255, 0.2);
            margin: 10px 0;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #ffd700;
        }
        .numbers {
            font-size: 24px;
            font-weight: bold;
            color: #ffd700;
            text-align: center;
            margin: 10px 0;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }
        .score {
            text-align: center;
            font-size: 14px;
            color: #a8e6cf;
        }
        .error {
            background: rgba(255, 0, 0, 0.3);
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            text-align: center;
        }
        .highlight {
            border-left: 4px solid #ffd700;
            background: rgba(255, 215, 0, 0.2);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌟 OMEGA PRO AI v10.1</h1>
        <div class="status">
            ✅ Ejecutándose en Akash Network - Red Descentralizada<br>
            🌐 Servidor Local Activo - Sin restricciones CORS
        </div>
        
        <button onclick="checkHealth()" id="healthBtn">🔍 Verificar Estado</button>
        <button onclick="generatePrediction()" id="predictBtn">🎲 Generar Predicción</button>
        <button onclick="openOriginalAPI()" id="apiBtn">🌐 Ver API Original</button>
        
        <div id="loading" class="loading" style="display: none;">
            ⏳ Consultando IA en Akash Network...
        </div>
        
        <div id="results"></div>
    </div>

    <script>
        function showLoading(show) {
            document.getElementById('loading').style.display = show ? 'block' : 'none';
            document.getElementById('predictBtn').disabled = show;
            document.getElementById('healthBtn').disabled = show;
        }

        function showResults(content) {
            document.getElementById('results').innerHTML = content;
        }

        async function checkHealth() {
            showLoading(true);
            try {
                const response = await fetch('/api/health');
                const data = await response.json();
                
                const content = `
                    <div class="predictions">
                        <h3>📊 Estado del Sistema OMEGA</h3>
                        <div class="prediction-item">
                            <strong>Estado:</strong> ${data.status} ✅<br>
                            <strong>Servicio:</strong> ${data.service}<br>
                            <strong>Plataforma:</strong> ${data.platform}<br>
                            <strong>Timestamp:</strong> ${new Date(data.timestamp).toLocaleString()}<br>
                            <strong>Uptime:</strong> ${data.uptime}
                        </div>
                    </div>
                `;
                showResults(content);
            } catch (error) {
                showResults(`<div class="error">❌ Error al verificar estado: ${error.message}</div>`);
            }
            showLoading(false);
        }

        async function generatePrediction() {
            showLoading(true);
            try {
                const response = await fetch('/api/predict', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ numbers: 6 })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    showResults(`<div class="error">❌ Error: ${data.error}</div>`);
                    showLoading(false);
                    return;
                }
                
                let content = `
                    <div class="predictions">
                        <h3>🎯 Predicciones OMEGA AI (${data.count} combinaciones)</h3>
                        <p><strong>Modelo:</strong> ${data.model} | <strong>Plataforma:</strong> ${data.platform}</p>
                        <p><strong>Precisión Base:</strong> ${data.accuracy_baseline}</p>
                `;
                
                // Ordenar por score (mayor a menor)
                const sortedPredictions = data.predictions.sort((a, b) => b.score - a.score);
                
                sortedPredictions.forEach((pred, index) => {
                    const isHighScore = pred.score > 0.65;
                    const star = isHighScore ? ' ⭐' : '';
                    const highlightClass = isHighScore ? 'highlight' : '';
                    const rank = index === 0 ? ' 🏆' : index === 1 ? ' 🥈' : index === 2 ? ' 🥉' : '';
                    
                    content += `
                        <div class="prediction-item ${highlightClass}">
                            <div><strong>Predicción ${index + 1}${star}${rank}</strong></div>
                            <div class="numbers">[${pred.combination.join(' - ')}]</div>
                            <div class="score">
                                Score: ${pred.score.toFixed(3)} | SVI: ${pred.svi.toFixed(3)}<br>
                                Fuente: ${pred.source} | ${new Date(pred.timestamp).toLocaleTimeString()}
                            </div>
                        </div>
                    `;
                });
                
                // Agregar estadísticas
                const avgScore = (sortedPredictions.reduce((sum, p) => sum + p.score, 0) / sortedPredictions.length).toFixed(3);
                const bestScore = sortedPredictions[0].score.toFixed(3);
                
                content += `
                    <div class="prediction-item" style="background: rgba(0, 255, 0, 0.2); text-align: center;">
                        <strong>📈 Estadísticas:</strong><br>
                        Mejor Score: ${bestScore} | Promedio: ${avgScore}<br>
                        Generado: ${new Date().toLocaleString()}
                    </div>
                </div>`;
                
                showResults(content);
                
            } catch (error) {
                showResults(`<div class="error">❌ Error al generar predicción: ${error.message}</div>`);
            }
            showLoading(false);
        }

        function openOriginalAPI() {
            window.open('https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win', '_blank');
        }

        // Auto-verificar estado al cargar
        window.onload = function() {
            console.log('🚀 OMEGA Web Interface cargada');
            console.log('🌐 Conectando con Akash Network...');
            checkHealth();
        };
    </script>
</body>
</html>'''

def start_server():
    """Iniciar el servidor web"""
    with socketserver.TCPServer(("", PORT), OmegaHandler) as httpd:
        print(f"🚀 OMEGA Web Server iniciado en http://localhost:{PORT}")
        print(f"🌐 Sirviendo interfaz OMEGA con proxy a Akash")
        print(f"📡 API: {OMEGA_API}")
        print(f"🔑 API Key: {API_KEY[:20]}...")
        print(f"⏹️  Presiona Ctrl+C para detener")
        
        # Abrir navegador automáticamente
        def open_browser():
            time.sleep(2)  # Esperar que el servidor se inicie
            webbrowser.open(f"http://localhost:{PORT}")
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Servidor OMEGA detenido")

if __name__ == "__main__":
    start_server()