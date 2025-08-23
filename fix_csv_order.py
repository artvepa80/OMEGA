#!/usr/bin/env python3
"""
Script para corregir el orden cronológico del CSV y hacerlo compatible con OMEGA PRO AI
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_csv_for_omega(input_file: str = 'data/historial_kabala_github.csv', 
                      output_file: str = None):
    """
    Corrige el CSV para compatibilidad total con OMEGA PRO AI
    
    Correcciones:
    1. Invierte el orden cronológico (antiguo → reciente)
    2. Valida integridad de datos
    3. Agrega columnas auxiliares útiles
    """
    
    if output_file is None:
        output_file = input_file.replace('.csv', '_fixed.csv')
    
    try:
        # Cargar CSV
        logger.info(f"📖 Cargando archivo: {input_file}")
        df = pd.read_csv(input_file, encoding='utf-8')
        
        initial_rows = len(df)
        logger.info(f"✅ Cargados {initial_rows} registros")
        
        # Verificar columnas
        expected_cols = ['fecha', 'Bolilla 1', 'Bolilla 2', 'Bolilla 3', 
                        'Bolilla 4', 'Bolilla 5', 'Bolilla 6']
        
        if list(df.columns) != expected_cols:
            logger.warning(f"⚠️ Orden de columnas diferente al esperado")
            logger.info(f"   Encontrado: {list(df.columns)}")
            logger.info(f"   Esperado: {expected_cols}")
        
        # CORRECCIÓN CRÍTICA: Invertir orden cronológico
        logger.info("🔄 Invirtiendo orden cronológico...")
        df = df.iloc[::-1].reset_index(drop=True)
        
        # Convertir fecha a datetime
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        
        # Eliminar filas con fechas inválidas
        df = df.dropna(subset=['fecha'])
        
        # Verificar orden cronológico
        if not df['fecha'].is_monotonic_increasing:
            logger.info("📅 Ordenando por fecha...")
            df = df.sort_values('fecha').reset_index(drop=True)
        
        # Validar integridad de números
        logger.info("🔍 Validando integridad de datos...")
        
        # Convertir a enteros
        for col in expected_cols[1:]:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
        
        # Eliminar filas con valores nulos
        before = len(df)
        df = df.dropna()
        if before > len(df):
            logger.info(f"   - Eliminadas {before - len(df)} filas con valores nulos")
        
        # Validar rango [1-40]
        for col in expected_cols[1:]:
            invalid = df[(df[col] < 1) | (df[col] > 40)]
            if len(invalid) > 0:
                logger.warning(f"   - {len(invalid)} filas con valores fuera de rango en {col}")
                df = df[(df[col] >= 1) & (df[col] <= 40)]
        
        # Agregar columnas auxiliares útiles
        logger.info("➕ Agregando columnas auxiliares...")
        
        # Día de la semana
        df['dia_semana'] = df['fecha'].dt.dayofweek
        
        # Mes
        df['mes'] = df['fecha'].dt.month
        
        # Año
        df['año'] = df['fecha'].dt.year
        
        # Suma total
        df['suma_total'] = df[expected_cols[1:]].sum(axis=1)
        
        # Promedio
        df['promedio'] = df[expected_cols[1:]].mean(axis=1).round(2)
        
        # Rango (max - min)
        df['rango'] = df[expected_cols[1:]].max(axis=1) - df[expected_cols[1:]].min(axis=1)
        
        # Cantidad de pares/impares
        def contar_pares(row):
            nums = [row[col] for col in expected_cols[1:]]
            return sum(1 for n in nums if n % 2 == 0)
        
        df['num_pares'] = df.apply(contar_pares, axis=1)
        df['num_impares'] = 6 - df['num_pares']
        
        # Números en rangos
        def contar_rango(row, min_val, max_val):
            nums = [row[col] for col in expected_cols[1:]]
            return sum(1 for n in nums if min_val <= n <= max_val)
        
        df['rango_1_13'] = df.apply(lambda x: contar_rango(x, 1, 13), axis=1)
        df['rango_14_27'] = df.apply(lambda x: contar_rango(x, 14, 27), axis=1)
        df['rango_28_40'] = df.apply(lambda x: contar_rango(x, 28, 40), axis=1)
        
        # Guardar archivo corregido
        logger.info(f"💾 Guardando archivo corregido: {output_file}")
        
        # Reordenar columnas para mejor legibilidad
        column_order = expected_cols + ['dia_semana', 'mes', 'año', 'suma_total', 
                                        'promedio', 'rango', 'num_pares', 'num_impares',
                                        'rango_1_13', 'rango_14_27', 'rango_28_40']
        df = df[column_order]
        
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        # Estadísticas finales
        logger.info("=" * 60)
        logger.info("📊 RESUMEN FINAL:")
        logger.info(f"   - Registros procesados: {len(df)}")
        logger.info(f"   - Rango de fechas: {df['fecha'].min().date()} a {df['fecha'].max().date()}")
        logger.info(f"   - Promedio histórico de suma: {df['suma_total'].mean():.1f}")
        logger.info(f"   - Promedio de pares por sorteo: {df['num_pares'].mean():.1f}")
        
        # Análisis del último sorteo para validación
        ultimo = df.iloc[-1]
        logger.info(f"\n🎯 Último sorteo en datos corregidos:")
        logger.info(f"   Fecha: {ultimo['fecha'].date()}")
        nums = [ultimo[f'Bolilla {i}'] for i in range(1, 7)]
        logger.info(f"   Números: {'-'.join(map(str, nums))}")
        logger.info(f"   Características: Pares={ultimo['num_pares']}, Suma={ultimo['suma_total']}, Rango={ultimo['rango']}")
        
        # Frecuencias actualizadas
        from collections import Counter
        all_nums = []
        for col in expected_cols[1:]:
            all_nums.extend(df[col].tolist())
        
        freq = Counter(all_nums)
        top_5 = freq.most_common(5)
        
        logger.info(f"\n🔥 Top 5 números más frecuentes:")
        for num, count in top_5:
            pct = (count / len(df)) * 100
            logger.info(f"   - Número {num}: {count} veces ({pct:.1f}%)")
        
        logger.info("=" * 60)
        logger.info(f"✅ Proceso completado exitosamente")
        logger.info(f"📁 Archivo guardado: {output_file}")
        
        return df
        
    except Exception as e:
        logger.error(f"❌ Error procesando archivo: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def create_training_dataset(csv_file: str, output_dir: str = 'data/processed/'):
    """
    Crea datasets específicos para cada modelo
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    df = pd.read_csv(csv_file)
    
    # Dataset para LSTM (secuencias)
    lstm_data = df[['fecha'] + [f'Bolilla {i}' for i in range(1, 7)]]
    lstm_data.to_csv(f'{output_dir}/lstm_data.csv', index=False)
    
    # Dataset para Transformer
    transformer_data = df.copy()
    transformer_data.to_csv(f'{output_dir}/transformer_data.csv', index=False)
    
    # Dataset para modelos estadísticos (con features)
    stats_data = df.copy()
    stats_data.to_csv(f'{output_dir}/statistical_data.csv', index=False)
    
    logger.info(f"✅ Datasets de entrenamiento creados en {output_dir}")


if __name__ == "__main__":
    import sys
    
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'data/historial_kabala_github.csv'
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Corregir CSV principal
    df_fixed = fix_csv_for_omega(input_file, output_file)
    
    # Crear datasets de entrenamiento
    if df_fixed is not None:
        output_path = output_file or input_file.replace('.csv', '_fixed.csv')
        create_training_dataset(output_path)
        
        print("\n✅ Todos los archivos están listos para OMEGA PRO AI")
        print("📁 Archivos generados:")
        print(f"   - {output_path}")
        print("   - data/processed/lstm_data.csv")
        print("   - data/processed/transformer_data.csv")
        print("   - data/processed/statistical_data.csv")