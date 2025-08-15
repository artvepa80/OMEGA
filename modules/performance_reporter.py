# OMEGA_PRO_AI_v10.1/modules/performance_reporter.py
# Advanced Performance Reporting and Analytics System

import os
import json
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import logging

# Configurar directorios
os.makedirs('reports/performance', exist_ok=True)
os.makedirs('reports/performance/charts', exist_ok=True)

class PerformanceReporter:
    """
    Sistema avanzado de reportes y análisis de rendimiento.
    
    Genera reportes detallados, gráficos y análisis de tendencias
    para identificar cuellos de botella y oportunidades de optimización.
    """
    
    def __init__(self, performance_monitor=None):
        self.performance_monitor = performance_monitor
        self.logger = logging.getLogger('PerformanceReporter')
        
        # Configurar estilo de gráficos
        plt.style.use('default')
        sns.set_palette("husl")
    
    def generate_comprehensive_report(self, output_path: Optional[str] = None) -> str:
        """Generar reporte completo de rendimiento"""
        if not self.performance_monitor:
            raise ValueError("Performance monitor no disponible")
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"reports/performance/comprehensive_report_{timestamp}.html"
        
        summary = self.performance_monitor.get_performance_summary()
        
        # Generar HTML del reporte
        html_content = self._generate_html_report(summary)
        
        # Generar gráficos
        charts_dir = os.path.join(os.path.dirname(output_path), 'charts')
        os.makedirs(charts_dir, exist_ok=True)
        
        chart_paths = self._generate_performance_charts(summary, charts_dir)
        
        # Insertar gráficos en HTML
        html_content = self._insert_charts_in_html(html_content, chart_paths)
        
        # Escribir reporte
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"📊 Reporte completo generado: {output_path}")
        return output_path
    
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
            resource_history = list(self.performance_monitor.resource_history)
            if len(resource_history) > 1:
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 8))
                
                timestamps = [datetime.fromisoformat(r.timestamp) for r in resource_history]
                cpu_usage = [r.cpu_percent for r in resource_history]
                memory_usage = [r.memory_percent for r in resource_history]
                
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
        """Exportar métricas de rendimiento a CSV"""
        if not self.performance_monitor:
            raise ValueError("Performance monitor no disponible")
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"reports/performance/performance_metrics_{timestamp}.csv"
        
        summary = self.performance_monitor.get_performance_summary()
        model_perf = summary.get('model_performance', {})
        
        # Crear DataFrame con métricas
        data = []
        for model_name, metrics in model_perf.items():
            data.append({
                'model': model_name,
                'execution_count': metrics['execution_count'],
                'avg_execution_time': metrics['avg_execution_time'],
                'last_execution_time': metrics['last_execution_time'],
                'success_rate': metrics['success_rate'],
                'timeout_count': metrics['timeout_count'],
                'fallback_count': metrics['fallback_count'],
                'peak_memory_usage': metrics['peak_memory_usage'],
                'last_error': metrics['last_error'] or 'None'
            })
        
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        
        self.logger.info(f"📊 Métricas exportadas a CSV: {output_path}")
        return output_path

def generate_performance_dashboard() -> str:
    """Función utilitaria para generar dashboard completo"""
    try:
        from modules.performance_monitor import get_performance_monitor
        
        monitor = get_performance_monitor()
        reporter = PerformanceReporter(monitor)
        
        # Generar reporte completo
        report_path = reporter.generate_comprehensive_report()
        
        # Generar CSV de métricas
        csv_path = reporter.export_performance_csv()
        
        print(f"✅ Dashboard generado: {report_path}")
        print(f"✅ CSV exportado: {csv_path}")
        
        return report_path
        
    except Exception as e:
        print(f"❌ Error generando dashboard: {e}")
        return ""