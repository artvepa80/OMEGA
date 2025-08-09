# OMEGA_PRO_AI-v10.1/utils/transformer_data_utils.py – Versión Ultra-Mejorada (OMEGA PRO AI v12.1)

import pandas as pd
import numpy as np
import torch
import re
from sklearn.preprocessing import StandardScaler

def prepare_advanced_transformer_data(df: pd.DataFrame, seq_length: int = 10, for_training: bool = False):
    """
    Prepara datos avanzados para el Transformer, con detección flexible de columnas y fixes de robustez.

    Args:
        df (pd.DataFrame): DataFrame con historial.
        seq_length (int): Longitud de secuencia.
        for_training (bool): Si es para entrenamiento (no usado actualmente).

    Returns:
        tuple: (X_seq, X_temp, X_pos, scaler)
    """
    # Columnas de bola: detecta 'n1'–'n6', 'Bolilla 1'–'Bolilla 6', o primeras 6 numéricas como fallback
    # Regex mejorado: case-insensitive, permite espacios o guiones bajos antes del dígito, y asegura fin de string
    columnas_bolillas = [c for c in df.columns if re.match(r'(?i)^(n[1-6]$|bolilla[_ \s]*\d+$)', c)]
    if len(columnas_bolillas) != 6:
        # Fallback: usar primeras 6 columnas numéricas si no coinciden
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if len(num_cols) >= 6:
            columnas_bolillas = num_cols[:6]
            print(f"⚠️ Columnas de bolillas no detectadas; usando fallback: {columnas_bolillas}")
        else:
            raise ValueError(f"❌ Se esperaban 6 columnas de números, encontradas: {columnas_bolillas}")
    columnas_bolillas.sort(key=lambda x: int(re.search(r'\d+', x).group()))

    # DETECCIÓN MEJORADA DE FECHA - COMIENZO DE MODIFICACIÓN
    # 1. Primero intentar por palabras clave
    col_fecha = next((c for c in df.columns if any(kw in c.lower() for kw in ['fecha', 'date', 'sorteo', 'draw'])), None)
    
    # 2. Si no se encuentra, intentar parsear columnas de tipo objeto
    if not col_fecha:
        for c in df.columns:
            if pd.api.types.is_object_dtype(df[c]) and len(df) > 0:
                try:
                    # Intentar parsear con formato estándar YYYY-MM-DD
                    pd.to_datetime(df[c], format='%Y-%m-%d')
                    col_fecha = c
                    print(f"✅ Detectada columna de fecha '{c}' por formato YYYY-MM-DD")
                    break
                except ValueError:
                    pass
    
    # 3. Si aún no se encuentra, lanzar error
    if not col_fecha:
        raise ValueError("❌ No se encontró columna de fecha.")
    
    # Renombrar y procesar columna de fecha
    df = df.rename(columns={col_fecha: 'fecha'})
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    df = df.dropna(subset=['fecha']).sort_values('fecha').copy()
    # DETECCIÓN MEJORADA DE FECHA - FIN DE MODIFICACIÓN
    
    # Chequeo post-dropna: Asegura suficientes filas después de eliminar NaT
    if len(df) < seq_length + 1:
        raise ValueError(f"❌ Sólo hay {len(df)} sorteos válidos después de parsing fechas, se necesitan al menos {seq_length + 1}.")

    # Agregar componentes temporales con normalización
    df['dia'] = df['fecha'].dt.day
    df['mes'] = df['fecha'].dt.month
    df['ano'] = df['fecha'].dt.year % 100  # Normaliza para evitar valores grandes

    X_seq, X_temp, X_pos = [], [], []
    for i in range(len(df) - seq_length):
        block = df.iloc[i: i + seq_length]
        X_seq.append(block[columnas_bolillas].values)
        X_temp.append(block[['dia', 'mes', 'ano']].values)
        X_pos.append(np.arange(seq_length))

    X_seq = torch.tensor(np.array(X_seq), dtype=torch.long)
    X_temp = torch.tensor(np.array(X_temp), dtype=torch.float)
    X_pos = torch.tensor(np.array(X_pos), dtype=torch.long)

    # Normalizar temp
    scaler = StandardScaler()
    tmp = scaler.fit_transform(X_temp.reshape(-1, 3))
    X_temp = torch.tensor(tmp.reshape(X_temp.shape), dtype=torch.float)

    return X_seq, X_temp, X_pos, scaler

def preparar_datos_transformer(ruta_csv: str, seq_length: int = 90):
    """
    Prepara datos desde CSV, con diagnóstico mejorado y parsing robusto.
    """
    df = pd.read_csv(ruta_csv)
    # Detección flexible de fecha
    col_fecha = next((c for c in df.columns if any(kw in c.lower() for kw in ['fecha', 'date', 'sorteo', 'draw'])), None)
    if col_fecha:
        df.rename(columns={col_fecha: 'fecha'}, inplace=True)
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce', dayfirst=False)  # Fix: False para Y-M-D estándar
    else:
        print("⚠️ No se encontró columna de fecha. Se usará un rango ficticio.")
        df['fecha'] = pd.date_range(start='2000-01-01', periods=len(df), freq='W')

    # Diagnóstico visual mejorado
    bol_cols = [c for c in df.columns if c.lower().startswith('n') or c.lower().startswith('bolilla') or c.lower().startswith('num')]
    print("🔍 Vista preliminar del DataFrame:")
    print(df[['fecha'] + bol_cols].head(5))
    print(f"✅ Sorteos válidos detectados: {len(df)} (antes de cleaning)")

    return prepare_advanced_transformer_data(df, seq_length=seq_length, for_training=False)