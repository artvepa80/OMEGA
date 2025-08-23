#!/usr/bin/env python3
"""
LIMPIADOR DE DATOS DE EMERGENCIA PARA OMEGA PRO AI
Limpia y valida el historial antes de la ejecución principal
"""

import pandas as pd
import numpy as np
from pathlib import Path

def emergency_clean_data():
    """Limpieza de emergencia del dataset histórico"""
    
    data_file = Path("data/historial_kabala_github_fixed.csv")
    
    if not data_file.exists():
        print("❌ No se encuentra el archivo de datos")
        return False
    
    try:
        # Cargar datos raw
        df = pd.read_csv(data_file)
        print(f"📊 Cargando {len(df)} registros...")
        
        # Identificar columnas de bolillas
        bolilla_cols = [col for col in df.columns if 'bolilla' in col.lower()]
        
        if len(bolilla_cols) < 6:
            # Buscar columnas numéricas
            numeric_cols = []
            for col in df.columns:
                try:
                    sample = pd.to_numeric(df[col].dropna().head(100), errors='coerce')
                    if not sample.isna().all() and sample.min() >= 1 and sample.max() <= 40:
                        numeric_cols.append(col)
                except:
                    continue
            bolilla_cols = numeric_cols[:6]
        
        if len(bolilla_cols) < 6:
            print("❌ No se encontraron suficientes columnas de bolillas")
            return False
        
        # Tomar solo las columnas de bolillas
        df_clean = df[bolilla_cols[:6]].copy()
        
        # Limpiar cada columna
        for col in df_clean.columns:
            # Convertir a string y limpiar
            df_clean[col] = df_clean[col].astype(str).str.strip()
            # Remover caracteres no numéricos
            df_clean[col] = df_clean[col].str.replace(r'[^0-9]', '', regex=True)
            # Convertir a numérico
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        # Rellenar NaN con valores válidos
        for col in df_clean.columns:
            median_val = df_clean[col].median()
            if pd.isna(median_val):
                median_val = 20  # Valor por defecto
            df_clean[col] = df_clean[col].fillna(median_val)
        
        # Clip a rango válido
        df_clean = df_clean.clip(lower=1, upper=40)
        
        # Convertir a enteros
        df_clean = df_clean.round().astype(int)
        
        # Renombrar columnas
        df_clean.columns = [f'bolilla_{i}' for i in range(1, len(df_clean.columns) + 1)]
        
        # Guardar datos limpios
        backup_file = data_file.parent / "historial_kabala_github_emergency_clean.csv"
        df_clean.to_csv(backup_file, index=False)
        
        # Reemplazar archivo original
        df_clean.to_csv(data_file, index=False)
        
        print(f"✅ Datos limpiados exitosamente: {len(df_clean)} registros válidos")
        print(f"💾 Backup guardado en: {backup_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en limpieza de emergencia: {e}")
        return False

if __name__ == '__main__':
    emergency_clean_data()
