"""Safe casting utilities para prevenir type errors"""
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def safe_cast_to_int(value, default=0):
    """Conversión segura a entero"""
    import numpy as np
    import pandas as pd
    
    try:
        # Si es array de NumPy
        if isinstance(value, np.ndarray):
            if value.dtype == 'O':  # Object dtype
                # Intentar convertir elemento por elemento
                result = []
                for item in value.flat:
                    result.append(safe_cast_single_to_int(item, default))
                return np.array(result, dtype=int).reshape(value.shape)
            else:
                return value.astype(int)
        
        # Si es pandas Series
        elif isinstance(value, pd.Series):
            return value.apply(lambda x: safe_cast_single_to_int(x, default))
        
        # Si es valor único
        else:
            return safe_cast_single_to_int(value, default)
            
    except Exception as e:
        logger.error(f"Error in safe_cast_to_int: {e}")
        if hasattr(value, '__len__') and len(value) > 0:
            return np.full(len(value), default, dtype=int)
        else:
            return default

def safe_cast_single_to_int(value, default=0):
    """Conversión segura de un valor único a entero"""
    try:
        if value is None or value == '':
            return default
        elif isinstance(value, str):
            # Limpiar string y extraer números
            cleaned = ''.join(c for c in value if c.isdigit() or c == '-')
            return int(cleaned) if cleaned else default
        elif isinstance(value, (int, np.integer)):
            return int(value)
        elif isinstance(value, (float, np.floating)):
            return int(value) if not np.isnan(value) else default
        else:
            # Intentar conversión directa
            return int(value)
    except (ValueError, TypeError, OverflowError):
        return default

def safe_array_operations(arr, operation='mean', axis=None):
    """Operaciones seguras en arrays con tipos mixtos"""
    import numpy as np
    
    try:
        # Convertir a array si no lo es
        if not isinstance(arr, np.ndarray):
            arr = np.array(arr)
        
        # Si es object dtype, intentar limpiar
        if arr.dtype == 'O':
            cleaned_arr = np.array([safe_cast_single_to_int(x, 0) for x in arr.flat])
            if arr.ndim > 1:
                cleaned_arr = cleaned_arr.reshape(arr.shape)
            arr = cleaned_arr
        
        # Realizar operación
        if operation == 'mean':
            return np.mean(arr, axis=axis)
        elif operation == 'sum':
            return np.sum(arr, axis=axis)
        elif operation == 'std':
            return np.std(arr, axis=axis)
        elif operation == 'max':
            return np.max(arr, axis=axis)
        elif operation == 'min':
            return np.min(arr, axis=axis)
        else:
            return arr
            
    except Exception as e:
        logger.error(f"Error in safe_array_operations: {e}")
        # Return safe default
        if axis is None:
            return 0.0
        else:
            shape = list(arr.shape)
            shape.pop(axis)
            return np.zeros(shape)

def clean_dataframe_dtypes(df):
    """Limpia tipos de datos problemáticos en DataFrame"""
    import pandas as pd
    import numpy as np
    
    df_clean = df.copy()
    
    for col in df_clean.columns:
        try:
            if df_clean[col].dtype == 'O':  # Object dtype
                # Intentar conversión inteligente
                sample_values = df_clean[col].dropna().head(10)
                
                if len(sample_values) > 0:
                    first_val = sample_values.iloc[0]
                    
                    # Si parece numérico, convertir a numérico
                    if isinstance(first_val, (int, float)) or str(first_val).replace('.', '').replace('-', '').isdigit():
                        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
                    
                    # Si parece fecha, convertir a datetime
                    elif any(char in str(first_val) for char in ['-', '/', ':']):
                        try:
                            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
                        except:
                            pass  # Mantener como object si no se puede convertir
                            
        except Exception as e:
            logger.warning(f"No se pudo limpiar columna {col}: {e}")
            continue
    
    return df_clean
