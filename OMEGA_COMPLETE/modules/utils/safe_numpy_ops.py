"""Safe NumPy operations para prevenir boolean errors"""
import numpy as np
import logging

logger = logging.getLogger(__name__)


def safe_boolean_operation(arr1, arr2, operation='subtract'):
    """
    Operaciones seguras para arrays booleanos de NumPy
    """
    import numpy as np
    
    try:
        if operation == 'subtract':
            # En lugar de arr1 - arr2 (no soportado), usar XOR lógico
            return np.logical_xor(arr1, arr2).astype(int)
        elif operation == 'add':
            return np.logical_or(arr1, arr2).astype(int) 
        elif operation == 'multiply':
            return np.logical_and(arr1, arr2).astype(int)
        else:
            # Convertir a enteros para operaciones aritméticas
            return np.array(arr1, dtype=int) - np.array(arr2, dtype=int)
            
    except Exception as e:
        logger.error(f"Error in boolean operation: {e}")
        # Fallback: convertir a enteros
        return np.array(arr1, dtype=int) - np.array(arr2, dtype=int)

def fix_threshold_adjustments(scores, thresholds, method='safe'):
    """
    Fix para threshold adjustments que causan boolean subtract errors
    """
    import numpy as np
    
    try:
        scores = np.array(scores)
        thresholds = np.array(thresholds)
        
        if method == 'safe':
            # Método seguro: usar comparaciones en lugar de substracciones
            above_threshold = scores > thresholds
            below_threshold = scores < thresholds
            
            # Ajustes basados en comparaciones
            adjusted_scores = scores.copy()
            adjusted_scores[above_threshold] *= 1.1  # Boost scores above threshold
            adjusted_scores[below_threshold] *= 0.9  # Reduce scores below threshold
            
            return adjusted_scores
        else:
            # Método legacy con fix
            diff = safe_boolean_operation(scores > thresholds, scores < thresholds, 'subtract')
            return scores + (diff * 0.1)
            
    except Exception as e:
        logger.error(f"Error in threshold adjustments: {e}")
        return scores  # Return original scores as fallback

def safe_array_subtract(arr1, arr2):
    """Substracción segura de arrays que pueden ser booleanos"""
    import numpy as np
    
    try:
        # Verificar si son arrays booleanos
        if arr1.dtype == bool or arr2.dtype == bool:
            # Convertir a enteros para permitir substracción
            arr1_int = np.array(arr1, dtype=int)
            arr2_int = np.array(arr2, dtype=int)
            return arr1_int - arr2_int
        else:
            # Substracción normal
            return arr1 - arr2
            
    except Exception as e:
        logger.error(f"Error in array subtraction: {e}")
        # Fallback: retornar arr1
        return np.array(arr1, dtype=float)
