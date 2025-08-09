# modules/inverse_mining_engine.py – Módulo avanzado de minería inversa (OMEGA PRO AI v10.16)

import argparse
import csv
import json
import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from modules.filters.ghost_rng_generative import simulate_ghost_rng
from modules.filters.rules_filter import FiltroEstrategico
from utils.validation import validate_combination
import tempfile

# Parámetros globales optimizados
MAX_RESULTS = 150
BOOST_FOCUS_MULTIPLIER = 2.2
PENALTY_WEIGHT = 0.12
DEFAULT_COUNT = 25
MIN_SCORE_LIMIT = 0.15

# Configuración avanzada de logging
default_logger = logging.getLogger("InverseMiningPro")
default_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(module)s] %(message)s")
handler.setFormatter(formatter)
default_logger.addHandler(handler)

def validar_entrada(seed, boost, penalize, focus_positions, logger=default_logger):
    """Valida y normaliza los parámetros de entrada con mayor robustez"""
    if not validate_combination(seed):
        logger.error(f"🚨 Semilla inválida: {seed}. Debe contener 6 números únicos entre 1-40")
        raise ValueError("Semilla inválida: debe contener 6 números únicos entre 1 y 40")

    # Limitar y eliminar duplicados
    boost = list(set(boost))[:5]
    penalize = list(set(penalize))[:10]

    # Validación avanzada de posiciones
    valid_positions = {"B1", "B2", "B3", "B4", "B5", "B6"}
    posiciones_validas = []
    for pos in focus_positions:
        clean_pos = pos.strip().upper()
        if clean_pos in valid_positions:
            if clean_pos not in posiciones_validas:
                posiciones_validas.append(clean_pos)
        else:
            logger.warning(f"⚠️ Posición inválida ignorada: {pos}")

    return boost, penalize, posiciones_validas

def calcular_ajuste_posicional(combo, boost, penalize, focus_positions):
    """Cálculo optimizado de ajustes de puntuación con factores posicionales"""
    ajuste = 0.0
    for idx, num in enumerate(combo):
        pos = f"B{idx+1}"
        factor_pos = BOOST_FOCUS_MULTIPLIER if pos in focus_positions else 1.0
        
        if num in boost:
            ajuste += 0.07 * factor_pos
            
        if num in penalize:
            # Penalización reducida en posiciones estratégicas
            penalty_factor = 1.2 if pos in focus_positions else 1.0
            ajuste -= PENALTY_WEIGHT * penalty_factor
    
    return np.clip(ajuste, -0.5, 0.5)  # Clip para estabilidad

def transformar_a_formato(resultados, source="inverse_mining"):
    """Formateo optimizado de resultados"""
    return [
        {
            "combination": list(combo),
            "score": round(score, 4),
            "source": source,
            "timestamp": datetime.now().isoformat()
        }
        for combo, score in resultados
    ]

def aplicar_mineria_inversa(historial_df: pd.DataFrame, seed, boost, penalize, focus_positions, cantidad, perfil_svi, logger=default_logger):
    """Algoritmo principal mejorado de minería inversa"""
    try:
        # Eliminar duplicados en datos históricos
        historial_df = historial_df.drop_duplicates()
        
        # Crear temp CSV for simulate_ghost_rng (since it expects path)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as temp_file:
            historial_df.to_csv(temp_file.name, index=False)
            temp_path = temp_file.name
        
        # Generar combinaciones simuladas usando temp path
        simuladas = simulate_ghost_rng(
            historial_csv_path=temp_path,
            perfil_svi=perfil_svi,
            max_seeds=250,
            training_mode=False
        )
        
        os.unlink(temp_path)  # Clean temp
        
        # Manejo de errores en generación de simulaciones
        if simuladas is None:
            logger.error("❌ Fallo crítico en ghost_rng: No se generaron simulaciones")
            return []

        # Configuración de filtro estratégico
        filtro = FiltroEstrategico()
        filtro.cargar_historial(historial_df.values.tolist())

        # Mapeo optimizado de perfiles
        perfil_map = {
            "default": "moderado",
            "conservative": "conservador",
            "aggressive": "agresivo"
        }
        perfil_filtro = perfil_map.get(perfil_svi, "moderado")
        
        # Umbrales dinámicos basados en distribución histórica
        umbrales = {
            "moderado": 0.68,
            "conservador": 0.78,
            "agresivo": 0.58
        }
        umbral = umbrales.get(perfil_filtro, 0.65)

        # Análisis estadístico para ajuste dinámico
        all_numbers = historial_df.values.flatten()
        num_freq = pd.Series(all_numbers).value_counts(normalize=True)
        avg_freq = num_freq.mean()

        resultados = []
        for sim in simuladas:
            combo = sim.get("draw", [])
            if not validate_combination(combo):
                logger.debug(f"Combinación inválida descartada: {combo}")
                continue

            # Aplicar filtros con perfil
            resultado_filtro = filtro.aplicar_filtros(
                combo,
                return_score=True,
                return_reasons=True,
                perfil_svi=perfil_filtro
            )
            
            # Manejar diferentes valores de retorno
            if len(resultado_filtro) == 3:
                aprobado, score_base, razones = resultado_filtro
            elif len(resultado_filtro) == 2:
                score_base, razones = resultado_filtro
                aprobado = True
            else:
                logger.warning(f"⚠️ Resultado inesperado de filtros: {resultado_filtro}")
                score_base, razones = 0.0, ["Error interno"]
                aprobado = False
            
            # Ajustes posicionales
            ajuste = calcular_ajuste_posicional(combo, boost, penalize, focus_positions)
            
            # Penalización basada en frecuencia
            penalizacion_freq = sum(0.02 * (1 - num_freq.get(n, avg_freq)) for n in combo if n in penalize)
            score_final = max(MIN_SCORE_LIMIT, min(0.99, score_base + ajuste - penalizacion_freq))

            # Evaluación basada en umbral dinámico
            if score_final >= umbral:
                resultados.append((combo, score_final))
            else:
                logger.debug(f"Combinación descartada: {combo}, Score: {score_final:.4f}, Razones: {razones}")

        # Ordenar y limitar resultados
        resultados.sort(key=lambda x: x[1], reverse=True)
        return resultados[:min(cantidad, MAX_RESULTS)]

    except Exception as e:
        logger.exception(f"🚨 Error crítico en minería inversa: {str(e)}")
        return []

def ejecutar_minado_inverso(historial_df: pd.DataFrame, seed, boost=[], penalize=[], focus_positions=[], count=DEFAULT_COUNT, mostrar=False, perfil_svi="default", logger=default_logger):
    """
    Función principal optimizada para integración
    
    Args:
        historial_df (pd.DataFrame): Datos históricos optimizados
        seed (list): Semilla base de 6 números
        boost (list): Números a reforzar
        penalize (list): Números a penalizar
        focus_positions (list): Posiciones estratégicas (ej. ['B1', 'B3'])
        count (int): Cantidad de resultados a generar
        mostrar (bool): Mostrar resultados en consola
        perfil_svi (str): Perfil SVI ('default', 'conservative', 'aggressive')
        logger (logging.Logger): Instancia de logger
    
    Returns:
        list: Resultados formateados
    """
    try:
        logger.info(f"🚀 Iniciando minería inversa con perfil: {perfil_svi}")
        boost, penalize, focus_positions = validar_entrada(seed, boost, penalize, focus_positions, logger)
        
        # Preprocesamiento de datos
        historial_df = historial_df.dropna().astype(int)
        
        resultados = aplicar_mineria_inversa(
            historial_df, seed, boost, penalize,
            focus_positions, count, perfil_svi, logger
        )
        
        formateados = transformar_a_formato(resultados)
        
        if not formateados:
            logger.warning("⚠️ No se generaron combinaciones válidas, usando respaldo")
            return [{
                "combination": [1, 2, 3, 4, 5, 6],
                "score": 0.5,
                "source": "inverse_mining",
                "timestamp": datetime.now().isoformat()
            }]

        if mostrar:
            logger.info("\n🎯 RESULTADOS DE MINERÍA INVERSA:")
            logger.info(f"📌 Semilla: {seed} | Boost: {boost} | Penalizar: {penalize} | Posiciones: {focus_positions}")
            logger.info(f"📊 Combinaciones generadas: {len(formateados)}")
            if formateados:
                logger.info(f"💎 Mejor score: {formateados[0]['score']:.4f}")
                logger.info("🏆 Combinaciones principales:")
                for i, item in enumerate(formateados[:min(10, len(formateados))]):
                    logger.info(f"#{i+1}: {item['combination']} | Score: {item['score']:.4f}")

        return formateados

    except Exception as e:
        logger.exception(f"❌ Error crítico en ejecución: {str(e)}")
        return [{
            "combination": [1, 2, 3, 4, 5, 6],
            "score": 0.5,
            "source": "inverse_mining",
            "timestamp": datetime.now().isoformat()
        }]

def exportar_resultados(combinaciones, path, logger=default_logger):
    """Exportación mejorada a múltiples formatos"""
    if not combinaciones:
        logger.warning("⚠️ Sin resultados para exportar")
        return

    os.makedirs(os.path.dirname(path), exist_ok=True)
    ext = os.path.splitext(path)[1].lower()
    
    try:
        if ext == '.json':
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({
                    "system": "OMEGA PRO AI",
                    "version": "10.16",
                    "module": "Inverse Mining Engine",
                    "profile": "advanced",
                    "results": combinaciones,
                    "generated": datetime.now().isoformat(),
                    "count": len(combinaciones)
                }, f, indent=2, ensure_ascii=False)
                
        elif ext == '.parquet':
            df = pd.DataFrame(combinaciones)
            df.to_parquet(path, index=False)
            
        else: # CSV por defecto
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(["# SISTEMA OMEGA PRO AI - MINERÍA INVERSA v10.16"])
                writer.writerow(["# Generado:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                writer.writerow(["Combinación", "Score", "Fuente", "Timestamp"])
                for item in combinaciones:
                    writer.writerow([
                        ','.join(map(str, item["combination"])),
                        item["score"],
                        item["source"],
                        item["timestamp"]
                    ])
        logger.info(f"✅ Resultados exportados: {path} ({len(combinaciones)} combinaciones)")
        
    except Exception as e:
        logger.error(f"❌ Error en exportación: {str(e)}")
        # Fallback a CSV simple
        backup_path = os.path.join(os.path.dirname(path), "backup_results.csv")
        with open(backup_path, 'w') as f:
            f.write("Combinacion\n")
            for item in combinaciones:
                f.write(','.join(map(str, item["combination"])) + '\n')
        logger.info(f"⚠️ Exportación de respaldo en: {backup_path}")

def mostrar_resumen(resultados, boost, penalize, focus_positions, logger=default_logger):
    """Resumen analítico mejorado"""
    if not resultados:
        logger.info("\n⚠️ No se generaron combinaciones válidas")
        return

    # Análisis estadístico
    scores = [r['score'] for r in resultados]
    mean_score = np.mean(scores)
    top_comb = resultados[0]['combination']
    
    logger.info("\n" + "="*70)
    logger.info(f"🔥 RESUMEN ANALÍTICO - MINERÍA INVERSA")
    logger.info(f"📊 Combinaciones generadas: {len(resultados)}")
    logger.info(f"📈 Score promedio: {mean_score:.4f}")
    logger.info(f"💎 Mejor score: {resultados[0]['score']:.4f}")
    logger.info(f"🏆 Combinación top: {top_comb}")
    logger.info(f"⚙️ Parámetros estratégicos:")
    logger.info(f" - Boost: {boost or 'Ninguno'}")
    logger.info(f" - Penalizar: {penalize or 'Ninguno'}")
    logger.info(f" - Posiciones clave: {focus_positions or 'Ninguna'}")
    logger.info("="*70)
    
    logger.info("\n🔝 TOP 10 COMBINACIONES:")
    for i, item in enumerate(resultados[:10]):
        logger.info(f"#{i+1}: {item['combination']} \tScore: {item['score']:.4f}")
    
    logger.info("="*70)

def parse_args():
    """Interfaz CLI mejorada"""
    parser = argparse.ArgumentParser(
        description="🧠 MÓDULO AVANZADO DE MINERÍA INVERSA - OMEGA PRO AI v10.16",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--seed', nargs=6, type=int, required=True,
                        help='Combinación semilla base (6 números únicos)')
    parser.add_argument('--boost', nargs='*', type=int, default=[],
                        help='Números a reforzar (máx. 5)')
    parser.add_argument('--penalize', nargs='*', type=int, default=[],
                        help='Números a penalizar (máx. 10)')
    parser.add_argument('--focus-positions', nargs='*', type=str, default=[],
                        help='Posiciones estratégicas (ej. B1 B3)')
    parser.add_argument('--output', type=str, default='results/inversion_output.csv',
                        help='Archivo de salida (CSV, JSON, Parquet)')
    parser.add_argument('--count', type=int, default=MAX_RESULTS,
                        help=f'Resultados a generar (max {MAX_RESULTS})')
    parser.add_argument('--silent', action='store_true',
                        help='Modo silencioso (sin salida en consola)')
    parser.add_argument('--perfil-svi', type=str, default='default',
                        choices=['default', 'conservative', 'aggressive'],
                        help='Perfil de riesgo SVI')
    parser.add_argument('--historial-csv', type=str, default='data/historial_kabala_github.csv',
                        help='Ruta a datos históricos')
    parser.add_argument('--verbose', action='store_true',
                        help='Modo detallado (debug logging)')
    return parser.parse_args()

def main():
    """Punto de entrada optimizado para CLI"""
    args = parse_args()
    
    # Configuración avanzada de logger
    logger = logging.getLogger("InverseMiningCLI")
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logging.basicConfig(level=logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(module)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    if not args.silent:
        logger.info("\n" + "🚀"*40)
        logger.info("🔍 EJECUTANDO MINERÍA INVERSA AVANZADA - OMEGA PRO AI v10.16")
        logger.info("🚀"*40)
    
    try:
        # Carga optimizada de datos históricos
        expected_cols = [f'Bolilla {i}' for i in range(1, 7)]
        logger.info(f"📂 Cargando datos históricos desde: {args.historial_csv}")
        
        # Lectura con manejo de errores
        try:
            historial_df = pd.read_csv(
                args.historial_csv,
                usecols=expected_cols,
                dtype={col: 'Int8' for col in expected_cols}
            )
        except Exception as e:
            logger.error(f"❌ Error al cargar CSV histórico: {str(e)}")
            # Fallback a datos dummy si falla
            dummy_data = np.random.randint(1, 41, size=(100, 6))
            historial_df = pd.DataFrame(dummy_data, columns=expected_cols)
            logger.warning("⚠️ Usando datos dummy como fallback")

        
        # Validación avanzada de datos
        if historial_df.empty:
            logger.error("🚨 El archivo histórico está vacío")
            sys.exit(1)
            
        if historial_df.isna().any().any():
            logger.warning("⚠️ Datos históricos contienen valores nulos, limpiando...")
            historial_df = historial_df.dropna()
        
        # Validación de estructura de columnas
        if not all(col in historial_df.columns for col in expected_cols):
            missing = [col for col in expected_cols if col not in historial_df.columns]
            logger.error(f"🚨 Columnas faltantes en histórico: {missing}")
            sys.exit(1)
            
        # Validación de rango numérico
        for col in expected_cols:
            if not historial_df[col].between(1, 40).all():
                invalid_count = historial_df[~historial_df[col].between(1, 40)][col].count()
                logger.error(f"🚨 Columna '{col}' tiene {invalid_count} valores fuera de rango [1, 40]")
                sys.exit(1)

        # Procesamiento principal
        boost, penalize, focus_positions = validar_entrada(
            args.seed,
            args.boost,
            args.penalize,
            args.focus_positions,
            logger
        )
        
        resultados = ejecutar_minado_inverso(
            historial_df=historial_df,
            seed=args.seed,
            boost=boost,
            penalize=penalize,
            focus_positions=focus_positions,
            count=args.count,
            mostrar=not args.silent,
            perfil_svi=args.perfil_svi,
            logger=logger
        )
        
        # Exportación y visualización
        if resultados:
            exportar_resultados(resultados, args.output, logger)
            if not args.silent:
                mostrar_resumen(resultados, boost, penalize, focus_positions, logger)
        elif not args.silent:
            logger.info("\n⚠️ No se generaron combinaciones válidas")
    
    except Exception as e:
        logger.exception(f"❌ ERROR CRÍTICO: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()