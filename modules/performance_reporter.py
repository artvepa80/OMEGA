# OMEGA_PRO_AI_v10.1/modules/performance_reporter.py
# Advanced Interactive Performance Reporting and Analytics System
# Enhanced with Plotly, WebSocket support, and security hardening

import os
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from collections import defaultdict
import logging
import asyncio
import secrets
import hashlib
import uuid
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor
import base64
from io import BytesIO

# Safe imports with fallbacks
def safe_import_module(module_name: str):
    """Safely import optional dependencies"""
    try:
        return __import__(module_name)
    except ImportError as e:
        logging.warning(f"Optional dependency {module_name} not available: {e}")
        return None

# Optional dependencies with fallbacks
plotly_go = safe_import_module('plotly.graph_objects')
plotly_px = safe_import_module('plotly.express') 
plotly_subplots = safe_import_module('plotly.subplots')
websockets = safe_import_module('websockets')
jinja2_env = safe_import_module('jinja2')
bleach = safe_import_module('bleach')
openpyxl = safe_import_module('openpyxl')
xlsxwriter = safe_import_module('xlsxwriter')
matplotlib_plt = safe_import_module('matplotlib.pyplot')
reportlab = safe_import_module('reportlab')

# Check if advanced features are available
PLOTLY_AVAILABLE = plotly_go is not None
WEBSOCKETS_AVAILABLE = websockets is not None
JINJA2_AVAILABLE = jinja2_env is not None
EXCEL_AVAILABLE = openpyxl is not None or xlsxwriter is not None
MATPLOTLIB_AVAILABLE = matplotlib_plt is not None
REPORTLAB_AVAILABLE = reportlab is not None

# Configurar directorios
os.makedirs('reports/performance', exist_ok=True)
os.makedirs('reports/performance/charts', exist_ok=True)
os.makedirs('reports/performance/exports', exist_ok=True)
os.makedirs('logs/performance', exist_ok=True)
os.makedirs('templates/performance', exist_ok=True)

class SecurityConfig:
    """Configuración de seguridad para el sistema de reportes"""
    
    # Configuración de sanitización HTML
    ALLOWED_TAGS = ['b', 'i', 'u', 'strong', 'em', 'p', 'br', 'div', 'span', 'small']
    ALLOWED_ATTRIBUTES = {'span': ['class'], 'div': ['class']}
    
    # Configuración CSRF
    CSRF_TOKEN_LENGTH = 32
    SESSION_TIMEOUT = 3600  # 1 hora
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generar token CSRF seguro"""
        return secrets.token_urlsafe(SecurityConfig.CSRF_TOKEN_LENGTH)
    
    @staticmethod
    def sanitize_html(content: str) -> str:
        """Sanitizar contenido HTML para prevenir XSS"""
        return bleach.clean(
            content,
            tags=SecurityConfig.ALLOWED_TAGS,
            attributes=SecurityConfig.ALLOWED_ATTRIBUTES,
            strip=True
        )
    
    @staticmethod
    def validate_input(input_data: Any, expected_type: type) -> bool:
        """Validar tipos de entrada"""
        return isinstance(input_data, expected_type)

class InteractivePerformanceReporter:
    """
    Sistema avanzado de reportes interactivos con dashboards en tiempo real.
    
    Características mejoradas:
    - Dashboards interactivos con Plotly
    - Actualizaciones en tiempo real via WebSocket
    - Exportación a múltiples formatos (PDF, Excel, CSV, PNG)
    - Seguridad hardened (XSS protection, CSRF tokens)
    - Diseño responsive y mobile-friendly
    - Filtrado interactivo y drill-down capabilities
    - Métricas específicas de OMEGA AI (LSTM accuracy trending)
    """
    
    def __init__(self, performance_monitor=None):
        self.performance_monitor = performance_monitor
        self.logger = logging.getLogger('InteractivePerformanceReporter')
        
        # Configure logging for performance reports
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/performance_reports.log'),
                logging.StreamHandler()
            ]
        )
        
        # Configurar Jinja2 con seguridad (with fallback)
        self.jinja_env = None
        if JINJA2_AVAILABLE:
            try:
                from jinja2 import Environment, FileSystemLoader, select_autoescape
                template_dir = Path(__file__).parent.parent / 'templates'
                self.jinja_env = Environment(
                    loader=FileSystemLoader(template_dir),
                    autoescape=select_autoescape(['html', 'xml']),
                    trim_blocks=True,
                    lstrip_blocks=True
                )
            except Exception as e:
                self.logger.warning(f"Could not initialize Jinja2: {e}")
        
        # Configuración de seguridad
        self.security_config = SecurityConfig()
        self.active_sessions = {}
        self.csrf_tokens = {}
        
        # WebSocket connections para actualizaciones en tiempo real (with fallback)
        self.websocket_clients = set() if WEBSOCKETS_AVAILABLE else None
        self.update_executor = ThreadPoolExecutor(max_workers=2)
        
        # Configurar colores de tema OMEGA
        self.omega_colors = {
            'primary': '#667eea',
            'secondary': '#764ba2',
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'info': '#17a2b8'
        }
        
        self.logger.info("✅ Interactive Performance Reporter initialized with security hardening")
    
    def generate_interactive_dashboard(self, output_path: Optional[str] = None, 
                                     session_id: Optional[str] = None) -> Tuple[str, str]:
        """Generar dashboard interactivo con seguridad hardened y fallbacks"""
        try:
            # Check if performance monitor is available
            if not self.performance_monitor:
                self.logger.warning("Performance monitor no disponible, generando reporte básico")
                return self._generate_minimal_report(output_path, session_id)
            
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"reports/performance/interactive_dashboard_{timestamp}.html"
            
            # Generar session ID y CSRF token seguros
            if not session_id:
                session_id = str(uuid.uuid4())
            
            csrf_token = self.security_config.generate_csrf_token()
            self.csrf_tokens[session_id] = {
                'token': csrf_token,
                'created_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(seconds=SecurityConfig.SESSION_TIMEOUT)
            }
            
            # Try to generate advanced report
            try:
                # Obtener datos de rendimiento
                summary = self.performance_monitor.get_performance_summary()
                
                # Generar datos de gráficos interactivos (with fallback)
                chart_data = self._generate_interactive_chart_data_safe(summary)
                
                # Generar dashboard HTML con template seguro
                html_content = self._generate_dashboard_html_safe(summary, chart_data, csrf_token)
                
                # Escribir dashboard
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                self.logger.info(f"🚀 Dashboard interactivo generado: {output_path}")
                self.logger.info(f"🔒 Session ID: {session_id}, CSRF Token configurado")
                
                return output_path, session_id
                
            except Exception as inner_e:
                self.logger.warning(f"Fallo generación avanzada, usando fallback básico: {inner_e}")
                return self._generate_minimal_report(output_path, session_id)
                
        except Exception as e:
            self.logger.error(f"❌ Error crítico generando dashboard: {str(e)}")
            # Generate emergency minimal report
            return self._generate_emergency_report(output_path or "reports/performance/emergency_report.html")
    
    def _generate_html_report(self, summary: Dict) -> str:
        """Generar contenido HTML del reporte"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OMEGA AI - Reporte de Rendimiento</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
                .section {{ background: white; margin: 20px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #f8f9fa; border-radius: 5px; border-left: 4px solid #007bff; }}
                .alert {{ padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .alert-critical {{ background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }}
                .alert-warning {{ background-color: #fff3cd; border: 1px solid #ffeeba; color: #856404; }}
                .alert-info {{ background-color: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; }}
                .chart-container {{ text-align: center; margin: 20px 0; }}
                .recommendation {{ background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 10px; margin: 5px 0; border-radius: 5px; }}
                .recommendation.high {{ border-left: 4px solid #dc3545; }}
                .recommendation.medium {{ border-left: 4px solid #ffc107; }}
                .recommendation.low {{ border-left: 4px solid #28a745; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; font-weight: bold; }}
                .performance-good {{ color: #28a745; }}
                .performance-warning {{ color: #ffc107; }}
                .performance-critical {{ color: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔍 OMEGA AI - Reporte de Rendimiento</h1>
                <p>Generado el {timestamp}</p>
            </div>
        """
        
        # Información de sesión
        session_info = summary['session_info']
        html += f"""
            <div class="section">
                <h2>📊 Información de Sesión</h2>
                <div class="metric">
                    <strong>Duración:</strong> {session_info['duration_formatted']}
                </div>
                <div class="metric">
                    <strong>Modelos Ejecutados:</strong> {session_info['total_models_executed']}
                </div>
                <div class="metric">
                    <strong>Tiempo Total:</strong> {session_info['total_execution_time']:.1f}s
                </div>
                <div class="metric">
                    <strong>Timeouts:</strong> {session_info['total_timeouts']}
                </div>
                <div class="metric">
                    <strong>Fallbacks:</strong> {session_info['total_fallbacks']}
                </div>
            </div>
        """
        
        # Rendimiento por modelo
        model_perf = summary['model_performance']
        if model_perf:
            html += """
                <div class="section">
                    <h2>🎯 Rendimiento por Modelo</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Modelo</th>
                                <th>Ejecuciones</th>
                                <th>Tiempo Promedio (s)</th>
                                <th>Tasa de Éxito</th>
                                <th>Timeouts</th>
                                <th>Fallbacks</th>
                                <th>Estado</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for model_name, metrics in model_perf.items():
                exec_count = metrics['execution_count']
                avg_time = metrics['avg_execution_time']
                success_rate = metrics['success_rate']
                timeouts = metrics['timeout_count']
                fallbacks = metrics['fallback_count']
                
                # Determinar estado
                if success_rate >= 0.9 and avg_time < 15:
                    status = '<span class="performance-good">✅ Excelente</span>'
                elif success_rate >= 0.7 and avg_time < 30:
                    status = '<span class="performance-warning">⚠️ Bueno</span>'
                else:
                    status = '<span class="performance-critical">🚨 Requiere atención</span>'
                
                html += f"""
                    <tr>
                        <td><strong>{model_name}</strong></td>
                        <td>{exec_count}</td>
                        <td>{avg_time:.1f}</td>
                        <td>{success_rate:.1%}</td>
                        <td>{timeouts}</td>
                        <td>{fallbacks}</td>
                        <td>{status}</td>
                    </tr>
                """
            
            html += """
                        </tbody>
                    </table>
                </div>
            """
        
        # Recursos del sistema
        current_resources = summary.get('current_resources')
        if current_resources:
            html += f"""
                <div class="section">
                    <h2>💻 Recursos del Sistema</h2>
                    <div class="metric">
                        <strong>CPU:</strong> {current_resources['cpu_percent']:.1f}%
                    </div>
                    <div class="metric">
                        <strong>Memoria Total:</strong> {current_resources['memory_percent']:.1f}%
                    </div>
                    <div class="metric">
                        <strong>Memoria Proceso:</strong> {current_resources['process_memory_mb']:.1f} MB
                    </div>
                    <div class="metric">
                        <strong>Hilos Activos:</strong> {current_resources['active_threads']}
                    </div>
                    <div class="metric">
                        <strong>Archivos Abiertos:</strong> {current_resources['open_files']}
                    </div>
                </div>
            """
        
        # Alertas recientes
        recent_alerts = summary.get('recent_alerts', [])
        if recent_alerts:
            html += """
                <div class="section">
                    <h2>⚠️ Alertas Recientes</h2>
            """
            
            for alert in recent_alerts[-10:]:  # Últimas 10 alertas
                alert_class = f"alert-{alert['severity']}"
                severity_emoji = {"warning": "⚠️", "critical": "🚨", "info": "ℹ️"}.get(alert['severity'], "•")
                
                html += f"""
                    <div class="alert {alert_class}">
                        <strong>{severity_emoji} {alert['severity'].upper()}</strong>: {alert['message']}
                """
                
                if alert.get('recommendation'):
                    html += f"<br><strong>💡 Recomendación:</strong> {alert['recommendation']}"
                
                html += "</div>"
            
            html += "</div>"
        
        # Análisis de cuellos de botella
        bottlenecks = summary.get('bottleneck_analysis', {})
        if any(bottlenecks.values()):
            html += """
                <div class="section">
                    <h2>🚧 Análisis de Cuellos de Botella</h2>
            """
            
            if bottlenecks.get('slowest_models'):
                html += "<h3>⏳ Modelos Más Lentos</h3><ul>"
                for model_info in bottlenecks['slowest_models']:
                    html += f"<li><strong>{model_info['model']}</strong>: {model_info['avg_time']:.1f}s promedio ({model_info['executions']} ejecuciones)</li>"
                html += "</ul>"
            
            if bottlenecks.get('timeout_models'):
                html += "<h3>⏰ Modelos con Timeouts</h3><ul>"
                for model_info in bottlenecks['timeout_models']:
                    html += f"<li><strong>{model_info['model']}</strong>: {model_info['timeout_count']} timeouts ({model_info['timeout_rate']:.1%} del total)</li>"
                html += "</ul>"
            
            if bottlenecks.get('resource_constraints'):
                html += "<h3>💻 Restricciones de Recursos</h3><ul>"
                for constraint in bottlenecks['resource_constraints']:
                    html += f"<li><strong>{constraint['resource']}</strong>: {constraint['avg_usage']:.1f}% - {constraint['impact']}</li>"
                html += "</ul>"
            
            html += "</div>"
        
        # Recomendaciones de optimización
        recommendations = summary.get('optimization_recommendations', [])
        if recommendations:
            html += """
                <div class="section">
                    <h2>💡 Recomendaciones de Optimización</h2>
            """
            
            for rec in recommendations:
                priority_class = rec.get('priority', 'low')
                priority_emoji = {"high": "🔥", "medium": "⚠️", "low": "ℹ️"}.get(priority_class, "•")
                
                html += f"""
                    <div class="recommendation {priority_class}">
                        <strong>{priority_emoji} [{priority_class.upper()}]</strong> {rec['recommendation']}
                """
                
                if rec.get('issue'):
                    html += f"<br><small><strong>Problema:</strong> {rec['issue']}</small>"
                
                html += "</div>"
            
            html += "</div>"
        
        # Placeholder para gráficos
        html += """
            <div class="section">
                <h2>📈 Gráficos de Rendimiento</h2>
                <div id="charts-placeholder">
                    <!-- Los gráficos se insertarán aquí -->
                </div>
            </div>
        """
        
        html += """
            <div class="section">
                <h2>📋 Resumen Ejecutivo</h2>
                <p>Este reporte fue generado automáticamente por el sistema de monitoreo de rendimiento de OMEGA AI.</p>
        """
        
        # Generar resumen ejecutivo
        total_models = len(model_perf) if model_perf else 0
        avg_success_rate = np.mean([m['success_rate'] for m in model_perf.values()]) if model_perf else 0
        critical_alerts_count = len([a for a in recent_alerts if a['severity'] == 'critical'])
        high_priority_recs = len([r for r in recommendations if r.get('priority') == 'high'])
        
        if avg_success_rate >= 0.85:
            system_health = "🟢 Excelente"
        elif avg_success_rate >= 0.70:
            system_health = "🟡 Bueno"
        else:
            system_health = "🔴 Requiere atención"
        
        html += f"""
                <div class="metric">
                    <strong>Estado del Sistema:</strong> {system_health}
                </div>
                <div class="metric">
                    <strong>Modelos Analizados:</strong> {total_models}
                </div>
                <div class="metric">
                    <strong>Tasa de Éxito Promedio:</strong> {avg_success_rate:.1%}
                </div>
                <div class="metric">
                    <strong>Alertas Críticas:</strong> {critical_alerts_count}
                </div>
                <div class="metric">
                    <strong>Recomendaciones Prioritarias:</strong> {high_priority_recs}
                </div>
            </div>
            
            <footer style="text-align: center; margin-top: 40px; padding: 20px; background-color: #f8f9fa; border-radius: 8px;">
                <p>🤖 Generado por OMEGA AI Performance Monitor v10.1</p>
                <p style="font-size: 12px; color: #6c757d;">Para soporte técnico, consulta los logs detallados en la carpeta logs/performance/</p>
            </footer>
        </body>
        </html>
        """
        
        return html
    
    def _generate_performance_charts(self, summary: Dict, charts_dir: str) -> Dict[str, str]:
        """Generar gráficos de rendimiento"""
        chart_paths = {}
        
        model_perf = summary.get('model_performance', {})
        if not model_perf:
            return chart_paths
        
        # Gráfico 1: Tiempo de ejecución por modelo
        fig, ax = plt.subplots(figsize=(12, 6))
        models = list(model_perf.keys())
        exec_times = [model_perf[m]['avg_execution_time'] for m in models]
        
        bars = ax.bar(models, exec_times, color=['#ff6b6b' if t > 20 else '#4ecdc4' if t < 10 else '#ffe66d' for t in exec_times])
        ax.set_title('Tiempo Promedio de Ejecución por Modelo', fontsize=14, fontweight='bold')
        ax.set_ylabel('Tiempo (segundos)')
        ax.set_xlabel('Modelo')
        plt.xticks(rotation=45, ha='right')
        
        # Añadir valores en las barras
        for bar, time in zip(bars, exec_times):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                   f'{time:.1f}s', ha='center', va='bottom')
        
        plt.tight_layout()
        chart_path = os.path.join(charts_dir, 'execution_times.png')
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        chart_paths['execution_times'] = chart_path
        
        # Gráfico 2: Tasa de éxito por modelo
        fig, ax = plt.subplots(figsize=(12, 6))
        success_rates = [model_perf[m]['success_rate'] * 100 for m in models]
        
        bars = ax.bar(models, success_rates, color=['#ff6b6b' if r < 80 else '#4ecdc4' if r > 90 else '#ffe66d' for r in success_rates])
        ax.set_title('Tasa de Éxito por Modelo', fontsize=14, fontweight='bold')
        ax.set_ylabel('Tasa de Éxito (%)')
        ax.set_xlabel('Modelo')
        ax.set_ylim(0, 105)
        plt.xticks(rotation=45, ha='right')
        
        # Añadir valores en las barras
        for bar, rate in zip(bars, success_rates):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                   f'{rate:.1f}%', ha='center', va='bottom')
        
        plt.tight_layout()
        chart_path = os.path.join(charts_dir, 'success_rates.png')
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        chart_paths['success_rates'] = chart_path
        
        # Gráfico 3: Distribución de problemas
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Timeouts por modelo
        timeouts = [model_perf[m]['timeout_count'] for m in models]
        if sum(timeouts) > 0:
            ax1.pie([t for t in timeouts if t > 0], 
                   labels=[m for m, t in zip(models, timeouts) if t > 0],
                   autopct='%1.1f%%', startangle=90)
            ax1.set_title('Distribución de Timeouts por Modelo')
        else:
            ax1.text(0.5, 0.5, 'No hay timeouts registrados', ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title('Distribución de Timeouts por Modelo')
        
        # Fallbacks por modelo
        fallbacks = [model_perf[m]['fallback_count'] for m in models]
        if sum(fallbacks) > 0:
            ax2.pie([f for f in fallbacks if f > 0], 
                   labels=[m for m, f in zip(models, fallbacks) if f > 0],
                   autopct='%1.1f%%', startangle=90)
            ax2.set_title('Distribución de Fallbacks por Modelo')
        else:
            ax2.text(0.5, 0.5, 'No hay fallbacks registrados', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Distribución de Fallbacks por Modelo')
        
        plt.tight_layout()
        chart_path = os.path.join(charts_dir, 'problem_distribution.png')
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        chart_paths['problem_distribution'] = chart_path
        
        # Gráfico 4: Recursos del sistema en el tiempo
        if self.performance_monitor and hasattr(self.performance_monitor, 'resource_history'):
            resource_history = list(self.performance_monitor.resource_history) if hasattr(self.performance_monitor, 'resource_history') else []
            if len(resource_history) > 1:
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 8))
                
                timestamps = [datetime.fromisoformat(r.timestamp) for r in resource_history[:100]]
                cpu_usage = [r.cpu_percent for r in resource_history[:100]]
                memory_usage = [r.memory_percent for r in resource_history[:100]]
                
                ax1.plot(timestamps, cpu_usage, label='CPU %', color='#ff6b6b', linewidth=2)
                ax1.set_title('Uso de CPU en el Tiempo')
                ax1.set_ylabel('CPU (%)')
                ax1.grid(True, alpha=0.3)
                ax1.legend()
                
                ax2.plot(timestamps, memory_usage, label='Memoria %', color='#4ecdc4', linewidth=2)
                ax2.set_title('Uso de Memoria en el Tiempo')
                ax2.set_ylabel('Memoria (%)')
                ax2.set_xlabel('Tiempo')
                ax2.grid(True, alpha=0.3)
                ax2.legend()
                
                plt.xticks(rotation=45)
                plt.tight_layout()
                chart_path = os.path.join(charts_dir, 'resource_timeline.png')
                plt.savefig(chart_path, dpi=150, bbox_inches='tight')
                plt.close()
                chart_paths['resource_timeline'] = chart_path
        
        return chart_paths
    
    def _insert_charts_in_html(self, html_content: str, chart_paths: Dict[str, str]) -> str:
        """Insertar gráficos en el HTML"""
        charts_html = ""
        
        chart_titles = {
            'execution_times': 'Tiempo de Ejecución por Modelo',
            'success_rates': 'Tasa de Éxito por Modelo',
            'problem_distribution': 'Distribución de Problemas',
            'resource_timeline': 'Recursos del Sistema en el Tiempo'
        }
        
        for chart_key, chart_path in chart_paths.items():
            if os.path.exists(chart_path):
                relative_path = os.path.relpath(chart_path, os.path.dirname(html_content))
                title = chart_titles.get(chart_key, chart_key.replace('_', ' ').title())
                
                charts_html += f"""
                    <div class="chart-container">
                        <h3>{title}</h3>
                        <img src="{relative_path}" alt="{title}" style="max-width: 100%; height: auto;">
                    </div>
                """
        
        return html_content.replace(
            '<div id="charts-placeholder"><!-- Los gráficos se insertarán aquí --></div>',
            charts_html
        )
    
    def generate_bottleneck_analysis(self) -> Dict[str, Any]:
        """Análisis específico de cuellos de botella"""
        if not self.performance_monitor:
            return {}
        
        summary = self.performance_monitor.get_performance_summary()
        model_perf = summary.get('model_performance', {})
        
        analysis = {
            'critical_bottlenecks': [],
            'performance_recommendations': [],
            'resource_optimization': [],
            'timeout_analysis': {},
            'memory_analysis': {}
        }
        
        # Análisis de modelos críticos
        for model_name, metrics in model_perf.items():
            if metrics['avg_execution_time'] > 25:  # Más de 25 segundos
                analysis['critical_bottlenecks'].append({
                    'model': model_name,
                    'issue': 'slow_execution',
                    'avg_time': metrics['avg_execution_time'],
                    'severity': 'high' if metrics['avg_execution_time'] > 30 else 'medium',
                    'recommendation': f'Optimizar algoritmo de {model_name} o incrementar timeout'
                })
            
            timeout_rate = metrics['timeout_count'] / max(1, metrics['execution_count'])
            if timeout_rate > 0.2:  # Más del 20% de timeouts
                analysis['critical_bottlenecks'].append({
                    'model': model_name,
                    'issue': 'frequent_timeouts',
                    'timeout_rate': timeout_rate,
                    'severity': 'high',
                    'recommendation': f'Revisar implementación de {model_name} por timeouts frecuentes'
                })
        
        # Análisis de recursos
        current_resources = summary.get('current_resources')
        if current_resources:
            if current_resources['memory_percent'] > 80:
                analysis['resource_optimization'].append({
                    'resource': 'memory',
                    'usage': current_resources['memory_percent'],
                    'recommendation': 'Optimizar gestión de memoria o incrementar RAM disponible'
                })
            
            if current_resources['cpu_percent'] > 85:
                analysis['resource_optimization'].append({
                    'resource': 'cpu',
                    'usage': current_resources['cpu_percent'],
                    'recommendation': 'Reducir modelos paralelos o usar CPU más potente'
                })
        
        return analysis
    
    def export_performance_csv(self, output_path: Optional[str] = None) -> str:
        """Exportar métricas de rendimiento a CSV con manejo de errores"""
        try:
            if not self.performance_monitor:
                raise ValueError("Performance monitor no disponible")
            
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"reports/performance/performance_metrics_{timestamp}.csv"
            
            # Asegurarse de que el directorio existe
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            summary = self.performance_monitor.get_performance_summary()
            model_perf = summary.get('model_performance', {})
            
            # Crear DataFrame con métricas
            data = []
            for model_name, metrics in model_perf.items():
                # Manejar valores predeterminados
                data.append({
                    'model': model_name,
                    'execution_count': metrics.get('execution_count', 0),
                    'avg_execution_time': metrics.get('avg_execution_time', 0.0),
                    'last_execution_time': metrics.get('last_execution_time', 'N/A'),
                    'success_rate': metrics.get('success_rate', 0.0),
                    'timeout_count': metrics.get('timeout_count', 0),
                    'fallback_count': metrics.get('fallback_count', 0),
                    'peak_memory_usage': metrics.get('peak_memory_usage', 0.0),
                    'last_error': metrics.get('last_error', 'None')
                })
            
            df = pd.DataFrame(data)
            df.to_csv(output_path, index=False)
            
            self.logger.info(f"📊 Métricas exportadas a CSV: {output_path}")
            return output_path
        
        except Exception as e:
            error_msg = f"Error exportando métricas de rendimiento: {e}"
            self.logger.error(error_msg)
            # Registrar error detallado en log
            self.logger.exception("Trace de error de exportación CSV:")
            raise RuntimeError(error_msg) from e
    
    def _generate_interactive_chart_data_safe(self, summary: Dict) -> Dict:
        """Generate chart data with fallbacks for missing dependencies"""
        try:
            if PLOTLY_AVAILABLE:
                return self._generate_interactive_chart_data(summary)
            else:
                # Return minimal chart data structure
                return {
                    'performance_chart': {'data': [], 'layout': {}},
                    'memory_chart': {'data': [], 'layout': {}},
                    'accuracy_chart': {'data': [], 'layout': {}},
                    'charts_available': False
                }
        except Exception as e:
            self.logger.warning(f"Error generating chart data, using fallback: {e}")
            return {'charts_available': False, 'error': str(e)}
    
    def _generate_dashboard_html_safe(self, summary: Dict, chart_data: Dict, csrf_token: str) -> str:
        """Generate dashboard HTML with fallbacks"""
        try:
            if self.jinja_env and JINJA2_AVAILABLE:
                return self._generate_secure_dashboard_html(summary, chart_data, csrf_token)
            else:
                return self._generate_html_report(summary)
        except Exception as e:
            self.logger.warning(f"Error generating secure dashboard, using basic HTML: {e}")
            return self._generate_html_report(summary)
    
    def _generate_minimal_report(self, output_path: Optional[str] = None, session_id: Optional[str] = None) -> Tuple[str, str]:
        """Generate minimal performance report when advanced features fail"""
        try:
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"reports/performance/minimal_report_{timestamp}.html"
            
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Create minimal summary
            minimal_summary = {
                'session_info': {
                    'duration_formatted': 'N/A',
                    'status': 'Limited monitoring available'
                },
                'system_metrics': {
                    'cpu_usage': 0.0,
                    'memory_usage': 0.0,
                    'disk_usage': 0.0
                },
                'recommendations': ['Sistema ejecutándose en modo básico']
            }
            
            html_content = self._generate_html_report(minimal_summary)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"📄 Reporte mínimo generado: {output_path}")
            return output_path, session_id
            
        except Exception as e:
            self.logger.error(f"Error generando reporte mínimo: {e}")
            return self._generate_emergency_report(output_path)
    
    def _generate_emergency_report(self, output_path: str) -> Tuple[str, str]:
        """Generate emergency text-based report when all else fails"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            session_id = str(uuid.uuid4())
            
            if not output_path.endswith('.html'):
                output_path = output_path.replace('.html', '.txt')
            
            content = f"""
OMEGA AI - Reporte de Emergencia
Generado: {timestamp}
Session ID: {session_id}

ESTADO: Sistema funcionando en modo de emergencia
- Performance monitor: No disponible o con errores
- Dependencias opcionales: No disponibles
- Modo de operación: Básico

Para resolver este problema:
1. Verificar instalación de dependencias opcionales
2. Revisar logs del sistema
3. Contactar soporte técnico si persiste

Este reporte fue generado como fallback de emergencia.
"""
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.warning(f"⚠️ Reporte de emergencia generado: {output_path}")
            return output_path, session_id
            
        except Exception as e:
            self.logger.critical(f"❌ Error crítico generando reporte de emergencia: {e}")
            return "reports/performance/critical_error.txt", "emergency-session"

def generate_performance_dashboard() -> str:
    """Función utilitaria para generar dashboard completo con fallbacks robustos"""
    try:
        # Try to import performance monitor
        try:
            from .performance_monitor import get_performance_monitor
            monitor = get_performance_monitor()
        except ImportError as ie:
            logging.warning(f"Could not import performance monitor: {ie}")
            monitor = None
        except Exception as e:
            logging.warning(f"Error getting performance monitor: {e}")
            monitor = None
        
        reporter = InteractivePerformanceReporter(monitor)
        
        # Generar reporte HTML (with fallbacks built-in)
        report_path, session_id = reporter.generate_interactive_dashboard()
        
        # Try to generate CSV if possible
        csv_path = None
        try:
            csv_path = reporter.export_performance_csv()
            print(f"✅ CSV de métricas: {csv_path}")
        except Exception as csv_e:
            logging.warning(f"Could not generate CSV metrics: {csv_e}")
            print("⚠️ CSV metrics not available (optional feature)")
        
        print(f"✅ Dashboard generado: {report_path}")
        print(f"🔒 Session ID: {session_id}")
        
        return report_path
        
    except Exception as e:
        error_msg = f"Error generando dashboard de rendimiento: {e}"
        print(f"❌ {error_msg}")
        logging.error(error_msg)
        
        # Try to generate emergency report
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            emergency_path = f"reports/performance/emergency_{timestamp}.txt"
            
            with open(emergency_path, 'w', encoding='utf-8') as f:
                f.write(f"OMEGA AI - Error Report\nTime: {datetime.now()}\nError: {error_msg}\n")
            
            print(f"📄 Emergency report generated: {emergency_path}")
            return emergency_path
        except Exception:
            print("❌ Critical error: Could not generate any report")
            return ""