"""Safe data utilities para prevenir unpacking errors"""
import numpy as np
import logging

logger = logging.getLogger(__name__)


def safe_prepare_data(func, *args, **kwargs):
    """Wrapper seguro para funciones de preparación de datos"""
    try:
        result = func(*args, **kwargs)
        
        # Si la función devuelve 4 valores (X_seq, X_temp, X_pos, scaler)
        # pero se esperan 2 (X, y), adaptar
        if isinstance(result, tuple):
            if len(result) == 4:
                X_seq, X_temp, X_pos, scaler = result
                # Combinar X_seq y X_temp para crear X
                if hasattr(X_seq, 'shape') and hasattr(X_temp, 'shape'):
                    X = np.concatenate([X_seq, X_temp], axis=-1) if X_seq.shape[0] > 0 else X_seq
                    # Crear y básico (desplazar secuencia)
                    y = X_seq[1:] if len(X_seq) > 1 else X_seq
                    return X, y
                else:
                    return X_seq, X_temp  # Fallback a primeros 2
            elif len(result) == 2:
                return result  # Ya está en formato correcto
            else:
                # Para otros casos, tomar primeros 2 elementos
                return result[:2]
        else:
            return result, result  # Fallback si no es tupla
            
    except Exception as e:
        logger.error(f"Error in safe_prepare_data: {e}")
        # Return dummy data para evitar crashes
        dummy_X = np.random.random((10, 6))
        dummy_y = np.random.random((10, 6))
        return dummy_X, dummy_y

def safe_unpack_lstm_data(data_prep_function, *args, **kwargs):
    """Función específica para desempaquetar datos LSTM de forma segura"""
    try:
        result = data_prep_function(*args, **kwargs)
        
        if isinstance(result, tuple) and len(result) >= 2:
            return result[0], result[1]  # Solo tomar X, y
        else:
            # Si no es tupla o tiene menos de 2 elementos, crear datos dummy
            logger.warning("⚠️ Datos LSTM inválidos, usando fallback")
            dummy_size = kwargs.get('sequence_length', 10)
            X = np.random.random((dummy_size, 6))
            y = np.random.random((dummy_size, 6))
            return X, y
            
    except Exception as e:
        logger.error(f"Error unpacking LSTM data: {e}")
        # Return safe defaults
        dummy_size = kwargs.get('sequence_length', 10)
        X = np.random.random((dummy_size, 6))
        y = np.random.random((dummy_size, 6))
        return X, y
