#!/usr/bin/env python3
"""
Helper para operaciones de scoring seguras sin objetos no-pickle
"""
import numpy as np
from typing import List, Dict, Any

def score_single_safe(combo_data, training_data_safe, params_safe):
    """
    Función top-level sin referencias a logger/locks para pickle.
    Solo usa tipos serializables: dict, list, np.ndarray
    """
    try:
        if isinstance(combo_data, dict):
            combo = combo_data.get('combination', combo_data.get('combo', []))
        else:
            combo = combo_data
        
        # Cálculo de score básico usando solo datos serializables
        if not combo or len(combo) != 6:
            return 20.0  # Score neutro
        
        # Score básico basado en suma y distribución
        suma = sum(combo)
        score = 20.0
        
        # Ajustes simples sin objetos complejos
        if 120 <= suma <= 180:
            score += 5.0
        
        # Diversidad de décadas
        decades = {n // 10 for n in combo}
        if len(decades) >= 3:
            score += 3.0
        
        # Patrón par/impar
        pares = sum(1 for n in combo if n % 2 == 0)
        if 2 <= pares <= 4:
            score += 2.0
            
        return float(score)
        
    except Exception:
        return 26.0  # Score neutro como fallback

def parallel_score_safe(combinations, training_data, n_jobs=4):
    """
    Función de scoring paralelo segura usando threading como fallback
    """
    try:
        from joblib import Parallel, delayed, parallel_backend
        
        # Convertir training_data a formato serializable
        if hasattr(training_data, 'values'):
            training_safe = training_data.values.tolist()
        elif isinstance(training_data, np.ndarray):
            training_safe = training_data.tolist()
        else:
            training_safe = list(training_data)
        
        params_safe = {'trend_factor': 1.0, 'vol_factor': 1.0}
        
        # Intentar loky primero, luego threading
        try:
            with parallel_backend("loky"):
                results = Parallel(n_jobs=n_jobs)(
                    delayed(score_single_safe)(combo, training_safe, params_safe)
                    for combo in combinations
                )
                return results
        except Exception:
            # Fallback a threading si loky falla
            with parallel_backend("threading"):
                results = Parallel(n_jobs=min(4, n_jobs))(
                    delayed(score_single_safe)(combo, training_safe, params_safe)
                    for combo in combinations
                )
                return results
                
    except Exception:
        # Fallback secuencial final
        return [
            score_single_safe(combo, [], {})
            for combo in combinations
        ]
