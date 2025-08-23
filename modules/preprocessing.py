# preprocessing.py – Limpieza de datos para OMEGA PRO AI
import pandas as pd

def preprocess_data(file_path):
    """
    Carga y limpia el historial de sorteos para usar en los modelos de OMEGA PRO AI.
    Se enfoca exclusivamente en las columnas numéricas (bolillas).
    Asegura orden cronológico ascendente para análisis de series temporales.
    """
    try:
        # Cargar el DataFrame completo (incluyendo fecha)
        df = pd.read_csv(file_path)
        
        # Convertir columna de fecha a datetime
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        # Ordenar por fecha en orden ascendente
        df_sorted = df.sort_values('fecha', ascending=True).reset_index(drop=True)

        # Solo mantener columnas numéricas (asumiendo que bolillas son numéricas)
        df_numeric = df_sorted.select_dtypes(include='number')

        # Quitar filas incompletas o inválidas
        df_clean = df_numeric.dropna().astype(int)

        return df_clean

    except Exception as e:
        print(f"❌ Error al cargar o limpiar datos: {e}")
        return pd.DataFrame()

    # Seleccionar solo columnas numéricas (por si hay fecha u otras)
    numeric_df = df.select_dtypes(include='number')

    # Convertir cada fila a lista de enteros
    combinations = numeric_df.values.tolist()

    return combinations

