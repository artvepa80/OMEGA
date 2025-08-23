#!/usr/bin/env python3
"""
📊 HTML REPORTER V3 - Fase 3 del Sistema Agéntico
Sistema avanzado de reportes HTML para explicabilidad completa
Genera reportes interactivos con visualizaciones y análisis detallados
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

def generate_advanced_report(
    title: str,
    agent_data: Dict[str, Any],
    reflection_data: Optional[Dict[str, Any]] = None,
    out_path: str = "outputs/reporte_agente_avanzado.html"
) -> str:
    """Genera reporte HTML avanzado con explicabilidad completa"""
    
    html_parts = []
    
    # Header con CSS avanzado
    html_parts.append(_generate_html_header(title))
    
    # Navegación
    html_parts.append(_generate_navigation())
    
    # Resumen ejecutivo
    html_parts.append(_generate_executive_summary(agent_data))
    
    # Análisis de decisiones
    if reflection_data:
        html_parts.append(_generate_decision_analysis(reflection_data))
    
    # Performance dashboard
    html_parts.append(_generate_performance_dashboard(agent_data))
    
    # Recomendaciones
    if reflection_data and "recommendations" in reflection_data:
        html_parts.append(_generate_recommendations_section(reflection_data["recommendations"]))
    
    # Timeline de actividad
    html_parts.append(_generate_timeline(agent_data))
    
    # Footer
    html_parts.append(_generate_html_footer())
    
    # Combinar y guardar
    full_html = "\n".join(html_parts)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(full_html, encoding="utf-8")
    
    return out_path

def _generate_html_header(title: str) -> str:
    """Genera header HTML con CSS avanzado"""
    
    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; padding: 30px; background: linear-gradient(45deg, #FF6B6B, #4ECDC4); color: white; border-radius: 12px; margin-bottom: 30px; }}
        .header h1 {{ font-size: 2.5em; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
        .section {{ margin-bottom: 30px; padding: 25px; background: #f8f9fa; border-radius: 12px; border-left: 5px solid #007bff; }}
        .section h2 {{ color: #007bff; margin-bottom: 20px; font-size: 1.8em; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }}
        .metric-card {{ background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .metric-value {{ font-size: 2.5em; font-weight: bold; color: #28a745; margin-bottom: 5px; }}
        .metric-label {{ color: #666; font-size: 0.9em; }}
        .alert {{ padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        .alert-success {{ background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }}
        .alert-info {{ background: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; }}
        .table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        .table th, .table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        .table th {{ background: #007bff; color: white; }}
        .insight {{ background: white; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #17a2b8; }}
        .recommendation {{ background: white; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #ffc107; }}
        .priority-high {{ border-left-color: #dc3545 !important; }}
        .timeline {{ position: relative; padding-left: 30px; }}
        .timeline-item {{ position: relative; padding-bottom: 20px; }}
        .nav {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 30px; }}
        .nav a {{ display: inline-block; padding: 10px 20px; margin: 5px; background: #007bff; color: white; text-decoration: none; border-radius: 6px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>Reporte Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        </div>
"""

def _generate_navigation() -> str:
    """Genera navegación interna"""
    return """
        <div class="nav">
            <a href="#resumen">📊 Resumen</a>
            <a href="#decisiones">🧠 Decisiones</a>
            <a href="#performance">📈 Performance</a>
            <a href="#recomendaciones">💡 Recomendaciones</a>
            <a href="#timeline">⏱️ Timeline</a>
        </div>
"""

def _generate_executive_summary(agent_data: Dict[str, Any]) -> str:
    """Genera resumen ejecutivo"""
    
    total_cycles = len(agent_data.get("cycle_results", []))
    
    if agent_data.get("cycle_results"):
        latest_cycle = agent_data["cycle_results"][-1]
        latest_reward = latest_cycle.get("best_reward", 0)
        avg_quality = np.mean([c.get("quality_rate", 0) for c in agent_data["cycle_results"]])
    else:
        latest_reward = 0
        avg_quality = 0
    
    return f"""
        <section id="resumen" class="section">
            <h2>📊 Resumen Ejecutivo</h2>
            
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{total_cycles}</div>
                    <div class="metric-label">Ciclos Ejecutados</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{latest_reward:.3f}</div>
                    <div class="metric-label">Último Reward</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{avg_quality:.1%}</div>
                    <div class="metric-label">Calidad Promedio</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">V3.0</div>
                    <div class="metric-label">Versión Agente</div>
                </div>
            </div>
            
            <div class="alert alert-success">
                <strong>✅ Estado del Sistema:</strong> Agente funcionando con capacidades avanzadas de auto-reflexión y optimización.
            </div>
            
            <div class="alert alert-info">
                <strong>🔍 Capacidades Activas:</strong> Self-Reflection, Bayesian Optimization, Active Learning, Drift Detection
            </div>
        </section>
"""

def _generate_decision_analysis(reflection_data: Dict[str, Any]) -> str:
    """Genera análisis de decisiones"""
    
    decision_analysis = reflection_data.get("decision_analysis", {})
    insights = decision_analysis.get("insights", [])
    
    html = f"""
        <section id="decisiones" class="section">
            <h2>🧠 Análisis de Decisiones</h2>
            
            <h3>💡 Insights Clave</h3>
    """
    
    if insights:
        for insight in insights:
            html += f'<div class="insight">{insight}</div>'
    else:
        html += '<div class="insight">No hay insights disponibles en este momento</div>'
    
    html += "</section>"
    
    return html

def _generate_performance_dashboard(agent_data: Dict[str, Any]) -> str:
    """Genera dashboard de performance"""
    
    cycle_results = agent_data.get("cycle_results", [])
    
    if not cycle_results:
        return '<section id="performance" class="section"><h2>📈 Performance Dashboard</h2><p>No hay datos disponibles</p></section>'
    
    rewards = [c.get("best_reward", 0) for c in cycle_results]
    best_reward = max(rewards)
    avg_reward = np.mean(rewards)
    
    html = f"""
        <section id="performance" class="section">
            <h2>📈 Performance Dashboard</h2>
            
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{avg_reward:.3f}</div>
                    <div class="metric-label">Reward Promedio</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{best_reward:.3f}</div>
                    <div class="metric-label">Mejor Reward</div>
                </div>
            </div>
            
            <h3>📈 Últimos Ciclos</h3>
            <table class="table">
                <tr><th>Ciclo</th><th>Best Reward</th><th>Quality Rate</th><th>Estado</th></tr>
"""
    
    for cycle in cycle_results[-5:]:
        cycle_num = cycle.get("cycle", "N/A")
        reward = cycle.get("best_reward", 0)
        quality = cycle.get("quality_rate", 0)
        status = "✅ Excelente" if reward > 0.8 else "🔄 Bueno" if reward > 0.6 else "⚠️ Mejorable"
        
        html += f"""
                <tr>
                    <td>#{cycle_num}</td>
                    <td>{reward:.3f}</td>
                    <td>{quality:.1%}</td>
                    <td>{status}</td>
                </tr>
        """
    
    html += """
            </table>
        </section>
"""
    
    return html

def _generate_recommendations_section(recommendations: List[Dict[str, Any]]) -> str:
    """Genera sección de recomendaciones"""
    
    html = """
        <section id="recomendaciones" class="section">
            <h2>💡 Recomendaciones del Sistema</h2>
            
            <p>Recomendaciones generadas automáticamente basadas en análisis de performance:</p>
"""
    
    for i, rec in enumerate(recommendations[:5]):
        priority = rec.get("priority", "medium")
        priority_class = f"priority-{priority}"
        
        html += f"""
            <div class="recommendation {priority_class}">
                <h4>📌 Recomendación #{i+1} - Prioridad: {priority.upper()}</h4>
                <p><strong>Acción:</strong> {rec.get('action', 'N/A')}</p>
                <p><strong>Justificación:</strong> {rec.get('rationale', 'N/A')}</p>
                <p><strong>Implementación:</strong> {rec.get('implementation', 'N/A')}</p>
            </div>
        """
    
    html += "</section>"
    return html

def _generate_timeline(agent_data: Dict[str, Any]) -> str:
    """Genera timeline de actividad"""
    
    cycle_results = agent_data.get("cycle_results", [])
    
    html = """
        <section id="timeline" class="section">
            <h2>⏱️ Timeline de Actividad</h2>
            
            <div class="timeline">
"""
    
    for cycle in cycle_results[-8:]:
        cycle_num = cycle.get("cycle", "N/A")
        reward = cycle.get("best_reward", 0)
        mode = cycle.get("planner_mode", "unknown")
        
        html += f"""
                <div class="timeline-item">
                    <div>Ciclo #{cycle_num} - Reward: {reward:.3f} - Modo: {mode}</div>
                </div>
        """
    
    html += """
            </div>
        </section>
"""
    
    return html

def _generate_html_footer() -> str:
    """Genera footer HTML"""
    
    return """
        <div style="text-align: center; padding: 30px; color: #666; border-top: 1px solid #dee2e6; margin-top: 40px;">
            <p>🤖 OMEGA PRO AI V3.0 - Sistema Agéntico Avanzado</p>
            <p>Reporte generado automáticamente por Self-Reflection Engine</p>
        </div>
    </div>
</body>
</html>
"""
