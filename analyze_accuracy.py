#!/usr/bin/env python3
# Análisis de precisión OMEGA vs resultado real 5/08/2025

import json
from pathlib import Path

def analyze_accuracy():
    """Analiza la precisión de las predicciones vs resultado real"""
    
    # Resultado real del 5/08/2025
    resultado_real = [14, 39, 34, 40, 31, 29]
    resultado_real_set = set(resultado_real)
    
    print("🎯 ANÁLISIS DE PRECISIÓN OMEGA PRO AI ULTIMATE")
    print("=" * 60)
    print(f"🎲 Resultado real 5/08/2025: {' - '.join(f'{n:02d}' for n in sorted(resultado_real))}")
    print("=" * 60)
    
    # Cargar resultados de OMEGA Ultimate
    results_dir = Path("results/ultimate")
    if not results_dir.exists():
        print("❌ No se encontraron resultados de OMEGA Ultimate")
        return
    
    # Buscar el archivo JSON más reciente
    json_files = list(results_dir.glob("omega_ultimate_summary_*.json"))
    if not json_files:
        print("❌ No se encontraron archivos de resultados")
        return
    
    latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
    
    try:
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        predictions = data.get('final_combinations', [])
        
        print(f"\n📊 ANALIZANDO {len(predictions)} PREDICCIONES:")
        print("-" * 60)
        
        best_matches = []
        
        for i, pred in enumerate(predictions):
            combo = pred['combination']
            combo_set = set(combo)
            
            # Calcular aciertos
            aciertos = len(resultado_real_set.intersection(combo_set))
            precision = (aciertos / 6) * 100
            
            # Análisis posicional
            aciertos_posicion = sum(1 for j, num in enumerate(sorted(combo)) 
                                  if j < len(sorted(resultado_real)) and num == sorted(resultado_real)[j])
            
            source_emoji = {
                '200_analyzer': '📊',
                'neural_enhanced': '🧠',
                'main_system': '🚀',
                'maestra': '👑',
                'fallback': '🔄'
            }.get(pred['source'], '🎲')
            
            combo_str = ' - '.join(f'{int(n):02d}' for n in sorted(combo))
            
            print(f"{i+1:2d}. {source_emoji} {combo_str} | "
                  f"Aciertos: {aciertos}/6 ({precision:4.1f}%) | "
                  f"Fuente: {pred['source']}")
            
            if aciertos > 0:
                numeros_acertados = sorted(resultado_real_set.intersection(combo_set))
                print(f"    ✅ Números acertados: {' - '.join(f'{int(n):02d}' for n in numeros_acertados)}")
            
            best_matches.append({
                'ranking': i + 1,
                'combination': combo,
                'aciertos': aciertos,
                'precision': precision,
                'source': pred['source'],
                'score': pred.get('score', 0)
            })
        
        # Encontrar mejor predicción
        best_prediction = max(best_matches, key=lambda x: x['aciertos'])
        
        print("\n" + "=" * 60)
        print("🏆 MEJOR PREDICCIÓN:")
        print("=" * 60)
        
        if best_prediction['aciertos'] > 0:
            combo_str = ' - '.join(f'{int(n):02d}' for n in sorted(best_prediction['combination']))
            print(f"🎯 Ranking #{best_prediction['ranking']}: {combo_str}")
            print(f"✅ Aciertos: {best_prediction['aciertos']}/6 ({best_prediction['precision']:.1f}%)")
            print(f"🔧 Fuente: {best_prediction['source']}")
            print(f"📊 Score original: {float(best_prediction['score']):.3f}")
            
            # Análisis específico de aciertos
            combo_set = set(best_prediction['combination'])
            aciertos_detalle = sorted(resultado_real_set.intersection(combo_set))
            print(f"🎲 Números acertados: {' - '.join(f'{int(n):02d}' for n in aciertos_detalle)}")
            
        else:
            print("❌ Ninguna predicción tuvo aciertos directos")
        
        # Estadísticas generales
        total_aciertos = sum(match['aciertos'] for match in best_matches)
        promedio_aciertos = total_aciertos / len(best_matches) if best_matches else 0
        
        print("\n" + "=" * 60)
        print("📈 ESTADÍSTICAS GENERALES:")
        print("=" * 60)
        print(f"🎯 Total de aciertos: {total_aciertos}")
        print(f"📊 Promedio por predicción: {promedio_aciertos:.2f}")
        print(f"🏆 Mejor resultado: {best_prediction['aciertos']}/6 aciertos")
        
        # Análisis por fuente
        sources_stats = {}
        for match in best_matches:
            source = match['source']
            if source not in sources_stats:
                sources_stats[source] = {'total_aciertos': 0, 'count': 0}
            sources_stats[source]['total_aciertos'] += match['aciertos']
            sources_stats[source]['count'] += 1
        
        print(f"\n📊 RENDIMIENTO POR FUENTE:")
        for source, stats in sources_stats.items():
            avg = stats['total_aciertos'] / stats['count']
            source_emoji = {
                '200_analyzer': '📊',
                'neural_enhanced': '🧠',
                'main_system': '🚀',
                'maestra': '👑',
                'fallback': '🔄'
            }.get(source, '🎲')
            print(f"{source_emoji} {source}: {avg:.2f} aciertos promedio ({stats['count']} predicciones)")
        
        # Análisis de números más predichos vs reales
        all_predicted_numbers = []
        for match in best_matches:
            all_predicted_numbers.extend(match['combination'])
        
        from collections import Counter
        predicted_freq = Counter(all_predicted_numbers)
        
        print(f"\n🔥 NÚMEROS MÁS PREDICHOS vs RESULTADO REAL:")
        print("-" * 40)
        top_predicted = predicted_freq.most_common(10)
        
        for num, freq in top_predicted:
            status = "✅ ACERTÓ" if int(num) in resultado_real else "❌"
            print(f"{int(num):2d}: predicho {freq} veces {status}")
        
        print("\n" + "=" * 60)
        print("🎯 CONCLUSIONES:")
        print("=" * 60)
        
        if best_prediction['aciertos'] >= 3:
            print("🎉 ¡EXCELENTE! Logramos 3+ aciertos - resultado muy positivo")
        elif best_prediction['aciertos'] >= 2:
            print("👍 BUENO: 2 aciertos - rendimiento decente")
        elif best_prediction['aciertos'] >= 1:
            print("📈 MODERADO: 1 acierto - hay potencial de mejora")
        else:
            print("🔧 OPORTUNIDAD: Sin aciertos directos - revisar estrategias")
        
        return best_matches
        
    except Exception as e:
        print(f"❌ Error analizando resultados: {e}")
        return []

if __name__ == '__main__':
    analyze_accuracy()
