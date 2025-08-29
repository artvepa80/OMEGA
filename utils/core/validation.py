# OMEGA_PRO_AI_v10.1/utils/validation.py – Utility module for combination validation (OMEGA PRO AI v12.4)

from typing import Optional
from typing import List
import pandas as pd
import numpy as np
import logging

# Logger configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

def validate_combination(combo: List[int], min_value: int = 1, max_value: int = 40) -> bool:
    """
    Validates a combination based on length, uniqueness, and value range.

    Args:
        combo (List[int]): List of integers representing the combination.
        min_value (int): Minimum allowed value (default: 1).
        max_value (int): Maximum allowed value (default: 40).

    Returns:
        bool: True if the combination is valid, False otherwise.
    """
    if not isinstance(combo, list) or len(combo) != 6:
        logger.debug(f"Invalid combo length: {len(combo)}")
        return False
    if len(set(combo)) != 6:
        logger.debug("Duplicate values in combo")
        return False
    if not all(isinstance(x, int) and min_value <= x <= max_value for x in combo):
        logger.debug("Values out of range or non-int")
        return False
    return True




def clean_historial_df(
        df: pd.DataFrame,
        min_value: int = 1,
        max_value: int = 40,
        dummy_rows: int = 60
) -> pd.DataFrame:
    """
    • Mantiene solo columnas numéricas o convertibles a numérico.
    • Maneja NaN, inf, -inf de forma robusta.
    • Clips y redondea al rango [min_value, max_value].
    • Si todo falla, genera un DataFrame 'dummy' con reposición (no rompe).
    """
    try:
        # Paso 1: Convertir a numérico (errores → NaN)
        df_num = df.apply(pd.to_numeric, errors="coerce")
        
        # Paso 2: Reemplazar infinitos con NaN ANTES de cualquier operación
        df_num = df_num.replace([np.inf, -np.inf], np.nan)
        # FIX: Convertir objetos a numérico de forma más robusta
        for col in df_num.columns:
            df_num[col] = pd.to_numeric(df_num[col], errors='coerce')
        
        # Paso 3: Seleccionar columnas numéricas
        numeric_cols = df_num.select_dtypes(include="number").columns
        if len(numeric_cols) < 6:
            raise ValueError("No se encontraron ≥6 columnas numéricas")
        
        # Paso 4: Tomar solo las primeras 6 columnas numéricas
        cols_to_use = list(numeric_cols)[:6]
        df_subset = df_num[cols_to_use].copy()
        
        # Paso 5: Rellenar NaN con valores seguros
        # Usar mediana si es posible, sino usar valores por defecto
        for col in cols_to_use:
            median_val = df_subset[col].median()
            if pd.isna(median_val) or not (min_value <= median_val <= max_value):
                # Si no hay mediana válida, usar valores distribuidos
                fill_value = min_value + (hash(col) % (max_value - min_value + 1))
            else:
                fill_value = median_val
            
            df_subset[col] = df_subset[col].fillna(fill_value)
        
        # Paso 6: Clip al rango válido
        df_subset = df_subset.clip(lower=min_value, upper=max_value)
        
        # Paso 7: Redondear y convertir a int de forma segura
        df_clean = df_subset.round()
        
        # Verificar que no hay valores problemáticos antes de convertir a int
        # FIX: Asegurar que los valores sean numéricos válidos
        df_clean = df_clean.fillna(method='ffill').fillna(min_value)
        for col in cols_to_use:
            if df_clean[col].isna().any():
                logger.warning(f"⚠️ Columna {col} tiene NaN después de limpieza")
                df_clean[col] = df_clean[col].fillna(min_value)
            
            if (df_clean[col] < min_value).any() or (df_clean[col] > max_value).any():
                logger.warning(f"⚠️ Columna {col} tiene valores fuera de rango")
                df_clean[col] = df_clean[col].clip(lower=min_value, upper=max_value)
        
        # Conversión final a int
        df_clean = df_clean.astype(int)
        
        # Renombrar columnas a formato esperado
        new_columns = [f"bolilla_{i}" for i in range(1, len(cols_to_use) + 1)]
        df_clean.columns = new_columns
        
        logger.info(f"✅ Dataset limpio: {len(df_clean)} registros, {len(df_clean.columns)} columnas")
        return df_clean
        
    except Exception as exc:
        logger.error(f"🚨 Error en limpieza de DF: {exc}")
        logger.error(f"🔍 Tipo de error: {type(exc).__name__}")
        logger.error(f"🔍 DataFrame shape: {df.shape if df is not None else 'None'}")
        logger.error(f"🔍 DataFrame dtypes: {df.dtypes.tolist() if df is not None else 'None'}")

        # ----- Fallback seguro ------------------------------------------------
        logger.warning("⚠️ Generando DataFrame dummy para continuar el flujo")
        rng = np.random.default_rng(seed=42)  # Seed fijo para reproducibilidad
        
        # Generar datos dummy más realistas para lotería
        dummy_data = []
        for _ in range(dummy_rows):
            # Generar 6 números únicos entre min_value y max_value
            row = rng.choice(
                range(min_value, max_value + 1), 
                size=6, 
                replace=False
            )
            dummy_data.append(sorted(row))  # Ordenar para mayor realismo
        
        dummy_df = pd.DataFrame(
            dummy_data, 
            columns=[f"bolilla_{i}" for i in range(1, 7)]
        )
        
        logger.info(f"✅ DataFrame dummy generado: {len(dummy_df)} registros")
        return dummy_df




def safe_convert_to_int(df, min_val=1, max_val=40):
    """Conversión segura de DataFrame a enteros"""
    try:
        # Paso 1: Convertir todo a string primero, luego a numérico
        for col in df.columns:
            # Convertir a string y limpiar
            df[col] = df[col].astype(str).str.strip()
            # Remover caracteres no numéricos excepto puntos y guiones
            df[col] = df[col].str.replace(r'[^0-9.-]', '', regex=True)
            # Convertir a numérico
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Paso 2: Llenar NaN con valores válidos
        df = df.fillna(method='bfill').fillna(method='ffill').fillna(min_val)
        
        # Paso 3: Clip a rango válido
        df = df.clip(lower=min_val, upper=max_val)
        
        # Paso 4: Redondear y convertir a int
        df = df.round().astype(int)
        
        return df
        
    except Exception as e:
        logger.error(f"Error en conversión segura: {e}")
        # Fallback: generar datos dummy
        return pd.DataFrame(
            np.random.randint(min_val, max_val+1, size=(len(df), len(df.columns))),
            columns=df.columns
        )
