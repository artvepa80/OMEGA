# lstm_v2.py – LSTM profundo v10.4 mejorado con compensación, ruido Levy, filtros estratégicos y muestreo probabilístico – Versión 11.0 Optimizada

import numpy as np
import pandas as pd
import random
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization, Input, TimeDistributed
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam
from scipy.stats import levy_stable
from modules.filters.rules_filter import FiltroEstrategico
from modules.score_dynamics import score_combinations
import logging
import os
from scipy.spatial.distance import hamming
from typing import List, Dict, Set, Tuple, Optional
from .lstm_model import generar_combinaciones_lstm
from utils import wrap_logger, fallback_combinations

def generar_combinaciones_lstm_v2(
    data: pd.DataFrame,
    historial_set: Set[Tuple[int,...]],
    cantidad: int,
    logger: Optional[logging.Logger] = None,
    config: dict = None
) -> List[Dict]:
    """
    Wrapper v2 para el generador LSTM con manejo de errores y configuración extendida.
    Utiliza la implementación base de LSTM y añade pasos adicionales de procesamiento.
    """
    log = wrap_logger(logger)
    
    # Configuración predeterminada
    default_config = {
        'version': 'v11.0',
        'fuerza_baja': 0.3,
        'posicional': False,
        'perfil_svi': 'moderado'
    }
    
    # Combinar configuración predeterminada con parámetros personalizados
    final_config = {**default_config, **(config or {})}
    
    # Log de configuración
    log(f"[LSTM v2] Configuración: {final_config}", "debug")
    
    try:
        # Llamar al generador base de LSTM
        resultados = generar_combinaciones_lstm(
            data=data,
            historial_set=historial_set,
            cantidad=cantidad,
            logger=logger,
            config=final_config
        )
        
        # Paso adicional: Aplicar filtro estratégico si está disponible
        if 'filtro_estrategico' in final_config:
            log("[LSTM v2] 🔍 Aplicando filtro estratégico adicional")
            filtro = FiltroEstrategico()
            filtro.cargar_historial(list(historial_set))
            
            resultados_filtrados = []
            for resultado in resultados:
                combo = resultado['combination']
                valido, score, razones = filtro.aplicar_filtros(combo, return_score=True, return_reasons=True)
                if valido:
                    resultado['score'] = max(0.5, resultado['score'] * score)
                    resultado['metrics']['filtro_score'] = score
                    resultados_filtrados.append(resultado)
                else:
                    log(f"[LSTM v2] ❌ Filtrada: {combo} | Razones: {razones}")
            
            # Si filtramos demasiados, completar con fallback
            if len(resultados_filtrados) < cantidad:
                faltantes = cantidad - len(resultados_filtrados)
                log(f"[LSTM v2] ⚠️ {faltantes} combos filtrados, agregando fallbacks")
                resultados_filtrados.extend(fallback_combinations(historial_set, faltantes))
            
            return resultados_filtrados
        
        return resultados
    
    except (ValueError, TypeError) as ve:
        log(f"[LSTM v2] ⚠️ Error de datos: {ve}", "error")
    except Exception as e:
        log(f"[LSTM v2] ⚠️ Error inesperado: {e}", "error")
    
    # Fallback en caso de cualquier error
    log("[LSTM v2] ⚠️ Devolviendo combinaciones de respaldo")
    return fallback_combinations(historial_set, cantidad)