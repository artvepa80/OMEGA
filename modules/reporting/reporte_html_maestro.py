# OMEGA_PRO_AI_v10.1/modules/reporting/reporte_html_maestro.py

import os
import json
from datetime import datetime

# Plantilla HTML con gráficos interactivos
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Combinación Maestra OMEGA PRO</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        :root {{
            --color-ok: #4CAF50;
            --color-warning: #FFC107;
            --color-danger: #F44336;
        }}
        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ 
            background: linear-gradient(135deg, #1a237e, #283593);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .combination {{
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 30px 0;
        }}
        .number {{
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: bold;
            background: #3f51b5;
            color: white;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            position: relative;
        }}
        .number.star::after {{
            content: '🌟';
            position: absolute;
            top: -20px;
            font-size: 24px;
        }}
        .number:hover {{
            transform: scale(1.1);
            box-shadow: 0 6px 12px rgba(0,0,0,0.3);
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .risk-indicator {{
            font-size: 24px;
            font-weight: bold;
            margin-top: 10px;
        }}
        .risk-low {{ color: var(--color-ok); }}
        .risk-moderate {{ color: var(--color-warning); }}
        .risk-high {{ color: var(--color-danger); }}
        .chart-container {{ 
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .footer {{ 
            text-align: center; 
            margin-top: 30px;
            color: #757575;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ Combinación Maestra OMEGA PRO</h1>
            <p>Generada el {fecha}</p>
        </div>
        
        <div class="combination">
            <!-- Números generados dinámicamente -->
            {numeros_html}
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <h3>Puntuación Estructural</h3>
                <div class="score-value">{score}</div>
                <div class="score-bar">
                    <div style="width: {score_percent}%; height: 10px; background: #3f51b5;"></div>
                </div>
            </div>
            
            <div class="metric-card">
                <h3>Viabilidad de Inversión (SVI)</h3>
                <div class="svi-value">{svi}</div>
                <div class="svi-bar">
                    <div style="width: {svi_percent}%; height: 10px; background: #4CAF50;"></div>
                </div>
            </div>
            
            <div class="metric-card">
                <h3>Perfil de Premio</h3>
                <div class="profile-value">{perfil}</div>
                <div class="profile-desc">{perfil_desc}</div>
            </div>
            
            <div class="metric-card">
                <h3>Nivel de Riesgo</h3>
                <div class="risk-indicator risk-{riesgo_class}">{alerta}</div>
                <p>{recomendacion}</p>
            </div>
        </div>
        
        <div class="chart-container">
            <div id="radarChart" style="height: 400px;"></div>
        </div>
        
        <div class="chart-container">
            <div id="decadesChart" style="height: 300px;"></div>
        </div>
        
        <div class="footer">
            <p>Sistema OMEGA PRO AI • Generado {timestamp}</p>
        </div>
    </div>
    
    <script>
        // Datos para gráficos
        const radarData = {{
            labels: ['Balance Numérico', 'Distribución', 'Patrones', 'Rareza', 'Historial'],
            values: {radar_values}
        }};
        
        const decadesData = {{
            labels: {decades_labels},
            values: {decades_values}
        }};
        
        // Gráfico Radar
        Plotly.newPlot('radarChart', [{{
            type: 'scatterpolar',
            r: radarData.values,
            theta: radarData.labels,
            fill: 'toself',
            fillcolor: 'rgba(63, 81, 181, 0.5)',
            line: {{ color: 'rgb(63, 81, 181)' }}
        }}], {{
            polar: {{ radialaxis: {{ visible: true, range: [0, 10] }} }},
            showlegend: false
        }});
        
        // Gráfico de Décadas
        Plotly.newPlot('decadesChart', [{{
            type: 'bar',
            x: decadesData.labels,
            y: decadesData.values,
            marker: {{ 
                color: decadesData.values.map(v => 
                    v > 2 ? 'rgba(244, 67, 54, 0.7)' : 
                    v < 2 ? 'rgba(76, 175, 80, 0.7)' : 
                    'rgba(255, 193, 7, 0.7)'
                )
            }}
        }}], {{
            title: 'Distribución por Décadas',
            xaxis: {{ title: 'Década' }},
            yaxis: {{ title: 'Cantidad de Números' }}
        }});
    </script>
</body>
</html>
"""

def generar_reporte_html(metadata: dict, ruta_salida: str = "outputs/reporte_maestro.html"):
    """Genera reporte HTML interactivo con gráficos y análisis visual"""
    # Determinar estrellas (números con mejor score histórico)
    top_nums = sorted(
        metadata["proceso_generacion"]["frecuencias_ponderadas"], 
        key=lambda x: x[1], 
        reverse=True
    )[:2]
    estrellas = [num for num, _ in top_nums]
    
    # Construir HTML de números con estrellas
    numeros_html = ""
    for num in metadata["combinacion_maestra"]:
        star_class = "star" if num in estrellas else ""
        numeros_html += f'<div class="number {star_class}">{num}</div>'
    
    # Descripción de perfiles
    perfiles_desc = {
        "A": "Alta probabilidad de premios menores",
        "B": "Balanceado - Óptimo para jackpot",
        "C": "Alto riesgo - Solo para jackpot"
    }
    
    # Preparar datos para gráfico radar (datos de ejemplo)
    radar_values = [
        min(9.2, metadata["score"] * 1.8),  # Balance
        8.5,  # Distribución
        7.8,  # Patrones
        6.3,  # Rareza
        min(9.0, metadata["svi"] * 10)   # Historial
    ]
    
    # Distribución por décadas
    decadas = [n // 10 * 10 for n in metadata["combinacion_maestra"]]
    decade_counts = Counter(decadas)
    decades_labels = sorted(decade_counts.keys())
    decades_values = [decade_counts[d] for d in decades_labels]
    
    # Rellenar plantilla
    html_final = HTML_TEMPLATE.format(
        fecha=datetime.now().strftime("%d/%m/%Y %H:%M"),
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        numeros_html=numeros_html,
        score=f"{metadata['score']:.2f}",
        score_percent=min(100, metadata["score"] * 20),
        svi=f"{metadata['svi']:.3f}",
        svi_percent=metadata["svi"] * 100,
        perfil=metadata["perfil"],
        perfil_desc=perfiles_desc.get(metadata["perfil"], ""),
        alerta=metadata["riesgo"]["alerta"],
        recomendacion=metadata["riesgo"]["recomendacion"],
        riesgo_class=metadata["riesgo"]["nivel_riesgo"],
        radar_values=radar_values,
        decades_labels=decades_labels,
        decades_values=decades_values
    )
    
    # Guardar archivo
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    with open(ruta_salida, "w") as f:
        f.write(html_final)
    
    return ruta_salida