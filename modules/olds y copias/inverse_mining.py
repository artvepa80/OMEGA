# modules/inverse_mining_engine.py – Módulo unificado para minería inversa (OMEGA PRO AI v10.10)

import argparse
import csv
import json
import os
import sys
import pandas as pd
from datetime import datetime
from modules.filters.ghost_rng_observer import simulate_ghost_rng
from modules.filters.rules_filter import FiltroEstrategico
from utils.validation import validate_combination  # Updated import to avoid circular dependency
from utils.logger import log_info, log_error

# Parámetros globales
MAX_RESULTS = 120
BOOST_FOCUS_MULTIPLIER = 2.0
PENALTY_WEIGHT = 0.15
DEFAULT_COUNT = 20

def validar_entrada(seed, boost, penalize, focus_positions):
    """Valida y normaliza los parámetros de entrada"""
    if not validate_combination(seed):
        log_error(f"🚨 Invalid seed: {seed}. Must be 6 unique integers between 1-40")
        raise ValueError("La semilla debe contener 6 números únicos entre 1 y 40")

    boost = boost[:5] if len(boost) > 5 else boost
    penalize = penalize[:10] if len(penalize) > 10 else penalize

    valid_positions = {"B1", "B2", "B3", "B4", "B5", "B6"}
    posiciones_validas = []
    for pos in focus_positions:
        if pos.upper() in valid_positions:
            posiciones_validas.append(pos.upper())
        else:
            log_info(f"⚠️ Invalid position ignored: {pos}")

    return boost, penalize, list(set(posiciones_validas))

def calcular_ajuste_posicional(combo, boost, penalize, focus_positions):
    """Calcula ajustes de puntuación basados en posiciones estratégicas"""
    ajuste = 0.0
    for idx, num in enumerate(combo):
        pos = f"B{idx+1}"
        factor_pos = BOOST_FOCUS_MULTIPLIER if pos in focus_positions else 1.0
        
        if num in boost:
            ajuste += 0.07 * factor_pos
            
        if num in penalize:
            ajuste -= PENALTY_WEIGHT * (1.5 if pos in focus_positions else 1.0)
    
    return ajuste

def transformar_a_formato(combinaciones, source="apriori"):  # Changed source to match consensus_engine.py
    return [
        {
            "combination": list(c),
            "score": round(score, 4),
            "source": source,
            "timestamp": datetime.now().isoformat()
        }
        for c, seed in combinaciones
    ]

def aplicar_mineria_inversa(historial_df: pd.DataFrame, seed, boost, penalize, focus_positions, cantidad, perfil_svi):
    """Algoritmo principal de minería inversa"""
    try:
        seed_value = sum(seed) + sum(boost) - sum(penalize)
        simuladas = simulate_ghost_rng(
            historial_csv_path="data/historial_kabala_github.csv",
            perfil_svi=perfil_svi,
            max_seeds=200,
            training_mode=False
        )

        filtro = FiltroEstrategico()
        filtro.cargar_historial(historial_df.values.tolist())

        # Map perfil_svi to rules_filter.py profiles
        perfil_svi_map = {
            "default": "moderado",
            "conservative": "conservador",
            "aggressive": "agresivo"
        }
        perfil_filtro = perfil_svi_map.get(perfil_svi, "moderado")
        
        # Profile-specific thresholds
        umbral_map = {
            "moderado": 0.85,
            "conservador": 0.9,
            "agresivo": 0.75
        }
        umbral = umbral_map.get(perfil_filtro, 0.85)

        resultados = []
        for sim in simuladas:
            combo = sim.get("draw", [])
            if not validate_combination(combo):
                log_info(f"⚠️ Invalid combination skipped: {combo}")
                continue

            score_base, razones = filtro.aplicar_filtros(combo, return_score=True, perfil_svi=perfil_filtro)
            ajuste = calcular_ajuste_posicional(combo, boost, penalize, focus_positions)
            penalizacion_extra = sum(1 for n in combo if n in penalize) * 0.03
            score_final = max(0.01, min(0.99, score_base + ajuste - penalizacion_extra))

            if score_final >= umbral:
                resultados.append((combo, score_final))
            else:
                log_info(f"🧹 Rejected combination: {combo}, Score: {score_final:.4f}, Reasons: {razones}")

        resultados.sort(key=lambda x: x[1], reverse=True)
        return resultados[:min(cantidad, MAX_RESULTS)]

    except Exception as e:
        log_error(f"🚨 Error in aplicar_mineria_inversa: {str(e)}")
        return []

def ejecutar_minado_inverso(historial_df: pd.DataFrame, seed, boost=[], penalize=[], focus_positions=[], count=DEFAULT_COUNT, mostrar=False, perfil_svi="default"):
    """
    Función principal para uso interno desde otros módulos
    
    Args:
        historial_df (pd.DataFrame): Historical lottery data
        seed (list): Semilla base de 6 números
        boost (list): Números a reforzar
        penalize (list): Números a penalizar
        focus_positions (list): Posiciones estratégicas (ej. ['B1', 'B3'])
        count (int): Cantidad de resultados a generar
        mostrar (bool): Mostrar resultados en consola
        perfil_svi (str): SVI profile ('default', 'conservative', 'aggressive')
    
    Returns:
        list: Resultados formateados
    """
    try:
        log_info(f"🚀 Starting ejecutar_minado_inverso with perfil_svi: {perfil_svi}")
        boost, penalize, focus_positions = validar_entrada(seed, boost, penalize, focus_positions)
        resultados = aplicar_mineria_inversa(historial_df, seed, boost, penalize, focus_positions, count, perfil_svi)
        formateados = transformar_a_formato(resultados)
        
        if not formateados:
            log_error("🚨 No valid combinations generated, returning fallback")
            return [{"combination": [1, 2, 3, 4, 5, 6], "score": 0.5, "source": "apriori", "timestamp": datetime.now().isoformat()}]

        if mostrar:
            log_info("\n🎯 Resultados de Minería Inversa:")
            log_info(f"📌 Seed: {seed} | Boost: {boost} | Penalize: {penalize} | Posiciones: {focus_positions}")
            log_info(f"📊 Combinaciones generadas: {len(formateados)}")
            if formateados:
                log_info(f"💎 Mejor score: {formateados[0]['score']:.4f}")
                log_info("🏆 Top Combinaciones:")
                for i, r in enumerate(formateados[:min(10, len(formateados))]):
                    log_info(f"#{i+1}: {r['combination']} | Score: {r['score']:.4f}")

        return formateados

    except Exception as e:
        log_error(f"❌ Error en minería inversa: {str(e)}")
        return [{"combination": [1, 2, 3, 4, 5, 6], "score": 0.5, "source": "apriori", "timestamp": datetime.now().isoformat()}]

def exportar_resultados(combinaciones, path):
    """Exporta resultados a CSV o JSON"""
    if not combinaciones:
        log_error("⚠️ No hay resultados para exportar")
        return

    os.makedirs(os.path.dirname(path), exist_ok=True)
    ext = os.path.splitext(path)[1].lower()
    
    try:
        if ext == '.json':
            with open(path, 'w') as f:
                json.dump({
                    "system": "OMEGA PRO AI",
                    "version": "10.10",
                    "module": "Inverse Mining Engine",
                    "results": combinaciones,
                    "generated": datetime.now().isoformat()
                }, f, indent=2)
        else:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["# SISTEMA OMEGA PRO AI - MINERÍA INVERSA v10.10"])
                writer.writerow(["# Generado:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                writer.writerow(["Combinación", "Score", "Fuente", "Timestamp"])
                for item in combinaciones:
                    writer.writerow([
                        item["combination"], 
                        item["score"], 
                        item["source"],
                        item["timestamp"]
                    ])
        log_info(f"✅ Resultados exportados: {path} ({len(combinaciones)} combinaciones)")
    except Exception as e:
        log_error(f"❌ Error exportando resultados: {str(e)}")

def mostrar_resumen(resultados, boost, penalize, focus_positions):
    """Muestra resumen detallado de resultados"""
    if not resultados:
        log_info("\n⚠️ No se generaron combinaciones válidas")
        return

    log_info("\n" + "="*60)
    log_info(f"🔥 Resumen de Minería Inversa")
    log_info(f"📊 Combinaciones generadas: {len(resultados)}")
    log_info(f"💎 Mejor score: {resultados[0]['score']:.4f}")
    log_info(f"⚙️ Parámetros aplicados:")
    log_info(f"   - Boost: {boost or 'Ninguno'}")
    log_info(f"   - Penalize: {penalize or 'Ninguno'}")
    log_info(f"   - Posiciones estratégicas: {focus_positions or 'Ninguna'}")
    log_info("="*60)
    
    log_info("\n🏆 Top 10 Combinaciones:")
    for i, item in enumerate(resultados[:10]):
        log_info(f"#{i+1}: {item['combination']} \tScore: {item['score']:.4f}")
    log_info("="*60)

def parse_args():
    """Configuración de CLI para ejecución independiente"""
    parser = argparse.ArgumentParser(
        description="🧠 Módulo Avanzado de Minería Inversa – OMEGA PRO AI v10.10",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--seed', nargs=6, type=int, required=True, 
                        help='Combinación semilla base (6 números únicos)')
    parser.add_argument('--boost', nargs='*', type=int, default=[], 
                        help='Números a reforzar (máx. 5)')
    parser.add_argument('--penalize', nargs='*', type=int, default=[], 
                        help='Números a penalizar (máx. 10)')
    parser.add_argument('--focus-positions', nargs='*', type=str, default=[], 
                        help='Posiciones estratégicas a enfatizar (ej. B1 B3)')
    parser.add_argument('--output', type=str, default='results/inversion_output.csv', 
                        help='Archivo de salida CSV/JSON')
    parser.add_argument('--count', type=int, default=MAX_RESULTS, 
                        help=f'Número de resultados a generar (max {MAX_RESULTS})')
    parser.add_argument('--silent', action='store_true', 
                        help='Modo silencioso (sin salida en consola)')
    parser.add_argument('--perfil-svi', type=str, default='default', 
                        choices=['default', 'conservative', 'aggressive'],
                        help='Perfil SVI para filtrado')
    parser.add_argument('--historial-csv', type=str, default='data/historial_kabala_github.csv', 
                        help='Ruta al archivo CSV de datos históricos')
    return parser.parse_args()

def main():
    """Punto de entrada para ejecución CLI"""
    args = parse_args()
    
    if not args.silent:
        log_info("\n" + "🚀"*30)
        log_info("🔍 EJECUTANDO MINERÍA INVERSA AVANZADA - OMEGA PRO AI v10.10")
        log_info("🚀"*30)
    
    try:
        # Load historical data
        expected_cols = [f'Bolilla {i}' for i in range(1, 7)]
        historial_df = pd.read_csv(args.historial_csv, usecols=expected_cols)
        historial_df = historial_df.dropna().astype(int)
        if not all(historial_df[col].between(1, 40).all() for col in expected_cols):
            log_error("🚨 Invalid historical data: numbers outside range [1, 40]")
            sys.exit(1)

        boost, penalize, focus_positions = validar_entrada(
            args.seed, 
            args.boost, 
            args.penalize, 
            args.focus_positions
        )
        
        resultados = ejecutar_minado_inverso(
            historial_df=historial_df,
            seed=args.seed,
            boost=boost,
            penalize=penalize,
            focus_positions=focus_positions,
            count=args.count,
            mostrar=not args.silent,
            perfil_svi=args.perfil_svi
        )
        
        if resultados:
            exportar_resultados(resultados, args.output)
            if not args.silent:
                mostrar_resumen(resultados, boost, penalize, focus_positions)
        elif not args.silent:
            log_info("\n⚠️ No se generaron combinaciones válidas")
    
    except Exception as e:
        log_error(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()