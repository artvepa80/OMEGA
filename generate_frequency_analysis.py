#!/usr/bin/env python3
"""
Generador de Análisis de Frecuencias y HTML Preview
Para las 8 series OMEGA del día
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from collections import Counter
import os

def load_series_data():
    """Carga las 8 series corregidas"""
    csv_path = "outputs/omega_8_series_corregidas_20250807.csv"
    if not os.path.exists(csv_path):
        # Fallback a datos manuales
        data = [
            [14,16,22,34,35,39],  # Agéntico Neural Enhanced
            [13,15,24,28,32,36],  # Híbrido Neural Enhanced
            [2,3,7,12,23,38],     # Agéntico Meta Learning
            [7,10,11,14,16,31],   # Agéntico Multi-Objective
            [1,7,15,28,30,36],    # Híbrido Fusión
            [2,8,11,31,34,39],    # Híbrido Meta Learning
            [7,27,30,32,36,40],   # Pipeline Maestra
            [6,10,13,34,35,36]    # Pipeline Fallback
        ]
        sources = ["Agéntico V4.0", "Híbrido", "Agéntico V4.0", "Agéntico V4.0", 
                  "Híbrido", "Híbrido", "Pipeline", "Pipeline"]
        scores = [0.860, 0.799, 0.795, 0.755, 0.712, 0.764, 0.500, 0.600]
        
        # Crear DataFrame artificial
        rows = []
        for i, (combo, source, score) in enumerate(zip(data, sources, scores)):
            rows.append({
                'Num1': combo[0], 'Num2': combo[1], 'Num3': combo[2],
                'Num4': combo[3], 'Num5': combo[4], 'Num6': combo[5],
                'Fuente': source, 'Composite': score
            })
        df = pd.DataFrame(rows)
    else:
        df = pd.read_csv(csv_path)
    
    return df

def analyze_frequencies(df):
    """Analiza frecuencias de números 1-40"""
    all_numbers = []
    
    # Extraer todos los números de las combinaciones
    for col in ['Num1', 'Num2', 'Num3', 'Num4', 'Num5', 'Num6']:
        all_numbers.extend(df[col].tolist())
    
    # Contar frecuencias
    freq_counter = Counter(all_numbers)
    
    # Crear array completo 1-40
    frequencies = []
    numbers = list(range(1, 41))
    
    for num in numbers:
        frequencies.append(freq_counter.get(num, 0))
    
    return numbers, frequencies, freq_counter

def create_frequency_chart(numbers, frequencies):
    """Crea gráfico de frecuencias"""
    plt.figure(figsize=(15, 8))
    
    # Crear colores basados en frecuencia
    colors = []
    for freq in frequencies:
        if freq >= 3:
            colors.append('#FF4444')  # Rojo para muy frecuentes
        elif freq >= 2:
            colors.append('#FF8844')  # Naranja para frecuentes
        elif freq == 1:
            colors.append('#4488FF')  # Azul para moderado
        else:
            colors.append('#CCCCCC')  # Gris para no usados
    
    # Crear barras
    bars = plt.bar(numbers, frequencies, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
    
    # Personalizar
    plt.title('📊 Análisis de Frecuencias - 8 Series OMEGA (1-40)', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Números de Lotería', fontsize=12)
    plt.ylabel('Frecuencia de Aparición', fontsize=12)
    plt.grid(True, alpha=0.3, axis='y')
    
    # Configurar ejes
    plt.xticks(range(1, 41, 2))  # Mostrar números impares para mejor legibilidad
    plt.xlim(0.5, 40.5)
    
    # Añadir etiquetas de frecuencia en barras altas
    for bar, freq in zip(bars, frequencies):
        if freq > 0:
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, 
                    str(freq), ha='center', va='bottom', fontweight='bold')
    
    # Leyenda
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#FF4444', label='Muy Frecuente (3+)'),
        Patch(facecolor='#FF8844', label='Frecuente (2)'),
        Patch(facecolor='#4488FF', label='Moderado (1)'),
        Patch(facecolor='#CCCCCC', label='No Usado (0)')
    ]
    plt.legend(handles=legend_elements, loc='upper right')
    
    # Estadísticas en el gráfico
    total_numbers = sum(frequencies)
    unique_numbers = sum(1 for f in frequencies if f > 0)
    max_freq = max(frequencies)
    
    stats_text = f'Total: {total_numbers} números\nÚnicos: {unique_numbers}/40\nMáx freq: {max_freq}'
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    
    # Guardar
    chart_path = "outputs/omega_frequency_analysis_20250807.png"
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    print(f"📊 Gráfico guardado: {chart_path}")
    
    return chart_path

def generate_html_preview(df, freq_counter, chart_path):
    """Genera HTML preview completo"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Calcular estadísticas
    total_series = len(df)
    avg_composite = df['Composite'].mean()
    source_counts = df['Fuente'].value_counts()
    
    # Top números más frecuentes
    top_numbers = sorted(freq_counter.items(), key=lambda x: x[1], reverse=True)[:10]
    
    html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 OMEGA - 8 Series para Hoy</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #FF6B6B;
        }}
        .series-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            padding: 30px;
        }}
        .series-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-left: 5px solid #4ECDC4;
        }}
        .series-numbers {{
            display: flex;
            gap: 10px;
            margin: 15px 0;
            flex-wrap: wrap;
        }}
        .number {{
            background: #4ECDC4;
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 16px;
        }}
        .source-tag {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 10px;
        }}
        .source-agentico {{ background: #FF6B6B; color: white; }}
        .source-hibrido {{ background: #4ECDC4; color: white; }}
        .source-pipeline {{ background: #45B7D1; color: white; }}
        .frequency-chart {{
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
        }}
        .frequency-chart img {{
            max-width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .top-numbers {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
            margin: 20px 0;
        }}
        .top-number {{
            background: #FF6B6B;
            color: white;
            padding: 10px 15px;
            border-radius: 20px;
            font-weight: bold;
        }}
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #4ECDC4;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 OMEGA PRO AI</h1>
            <h2>8 Series Optimizadas para Hoy</h2>
            <p>Generado: {timestamp}</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{total_series}</div>
                <div>Series Generadas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{avg_composite:.3f}</div>
                <div>Score Promedio</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{source_counts.get('Agéntico V4.0', 0)}</div>
                <div>Series Agénticas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{source_counts.get('Híbrido', 0)}</div>
                <div>Series Híbridas</div>
            </div>
        </div>

        <div class="series-grid">
"""

    # Agregar cada serie
    for i, row in df.iterrows():
        numbers = [row['Num1'], row['Num2'], row['Num3'], row['Num4'], row['Num5'], row['Num6']]
        
        source_class = "source-agentico" if "Agéntico" in row['Fuente'] else \
                      "source-hibrido" if "Híbrido" in row['Fuente'] else "source-pipeline"
        
        html_content += f"""
            <div class="series-card">
                <h3>Serie #{i+1}</h3>
                <span class="source-tag {source_class}">{row['Fuente']}</span>
                <div class="series-numbers">
"""
        for num in numbers:
            html_content += f'<div class="number">{num:02d}</div>'
        
        html_content += f"""
                </div>
                <p><strong>Score Composite:</strong> {row['Composite']:.3f}</p>
                <p><strong>Modelo:</strong> {row.get('Modelo', 'N/A')}</p>
            </div>
"""

    html_content += f"""
        </div>

        <div class="frequency-chart">
            <h2>📊 Análisis de Frecuencias (1-40)</h2>
            <img src="{os.path.basename(chart_path)}" alt="Gráfico de Frecuencias">
            
            <h3>🔥 Top 10 Números Más Frecuentes</h3>
            <div class="top-numbers">
"""

    # Agregar top números
    for num, freq in top_numbers:
        html_content += f'<div class="top-number">{num:02d} ({freq}x)</div>'

    html_content += f"""
            </div>
        </div>

        <div style="padding: 30px;">
            <h2>📋 Tabla Detallada</h2>
            <table>
                <tr>
                    <th>Serie</th>
                    <th>Números</th>
                    <th>Fuente</th>
                    <th>Score</th>
                    <th>Modelo</th>
                </tr>
"""

    # Tabla detallada
    for i, row in df.iterrows():
        numbers_str = f"{row['Num1']:02d}-{row['Num2']:02d}-{row['Num3']:02d}-{row['Num4']:02d}-{row['Num5']:02d}-{row['Num6']:02d}"
        html_content += f"""
                <tr>
                    <td>#{i+1}</td>
                    <td>{numbers_str}</td>
                    <td>{row['Fuente']}</td>
                    <td>{row['Composite']:.3f}</td>
                    <td>{row.get('Modelo', 'N/A')}</td>
                </tr>
"""

    html_content += """
            </table>
        </div>

        <div class="footer">
            <p>🚀 OMEGA PRO AI v10.1 - Sistema Híbrido Avanzado</p>
            <p>Análisis basado en Pipeline v10.1 + Agéntico V4.0 + Machine Learning</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Guardar HTML
    html_path = "outputs/omega_preview_20250807.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"📄 HTML preview guardado: {html_path}")
    return html_path

def main():
    """Función principal"""
    print("🎯 Generando análisis de frecuencias y HTML preview...")
    
    # Cargar datos
    df = load_series_data()
    print(f"✅ Cargadas {len(df)} series")
    
    # Analizar frecuencias
    numbers, frequencies, freq_counter = analyze_frequencies(df)
    print(f"📊 Analizadas frecuencias de {len(numbers)} números")
    
    # Crear gráfico
    chart_path = create_frequency_chart(numbers, frequencies)
    
    # Generar HTML
    html_path = generate_html_preview(df, freq_counter, chart_path)
    
    # Estadísticas finales
    total_used = sum(1 for f in frequencies if f > 0)
    most_frequent = max(freq_counter.items(), key=lambda x: x[1])
    
    print(f"\n📈 ESTADÍSTICAS FINALES:")
    print(f"   🎯 Números únicos usados: {total_used}/40")
    print(f"   🔥 Número más frecuente: {most_frequent[0]} ({most_frequent[1]} veces)")
    print(f"   📊 Distribución por fuente:")
    for source, count in df['Fuente'].value_counts().items():
        print(f"      • {source}: {count} series")
    
    print(f"\n✅ Archivos generados:")
    print(f"   📊 {chart_path}")
    print(f"   📄 {html_path}")

if __name__ == "__main__":
    main()
