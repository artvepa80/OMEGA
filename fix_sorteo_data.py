#!/usr/bin/env python3
"""
Script para corregir el dataset:
- Eliminar sorteo incorrecto del 16-08-2025
- Agregar sorteo correcto del 12-08-2025: 11-29-24-23-28-39
"""

import pandas as pd
import logging
from datetime import datetime
from modules.data_manager import OmegaDataManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_sorteo_data():
    """Corrige los datos del sorteo"""
    
    try:
        # Crear instancia del data manager
        dm = OmegaDataManager()
        
        print("🔍 Estado actual del dataset:")
        info = dm.get_data_info()
        print(f"   Total registros: {info['total_records']}")
        if info.get('last_sorteo'):
            last = info['last_sorteo']
            print(f"   Último sorteo: {last['fecha']} - {' - '.join(map(str, last['numeros']))}")
        
        # Leer el CSV directamente para manipular
        csv_path = "data/historial_kabala_github_emergency_clean.csv"
        df = pd.read_csv(csv_path)
        
        print(f"\n📊 Dataset cargado: {len(df)} registros")
        
        # 1. ELIMINAR sorteo incorrecto del 16-08-2025
        print("\n🗑️ Eliminando sorteo incorrecto del 2025-08-16...")
        before_count = len(df)
        
        # Filtrar para eliminar 2025-08-16
        df = df[df['fecha'] != '2025-08-16']
        
        after_count = len(df)
        removed_count = before_count - after_count
        
        if removed_count > 0:
            print(f"✅ Eliminado {removed_count} registro(s) del 2025-08-16")
        else:
            print("ℹ️ No se encontró sorteo del 2025-08-16 para eliminar")
        
        # 2. VERIFICAR si ya existe el sorteo del 12-08-2025
        existing_12_08 = df[df['fecha'] == '2025-08-12']
        if len(existing_12_08) > 0:
            print(f"⚠️ Ya existe sorteo del 2025-08-12:")
            for idx, row in existing_12_08.iterrows():
                nums = [row['bolilla_1'], row['bolilla_2'], row['bolilla_3'], 
                       row['bolilla_4'], row['bolilla_5'], row['bolilla_6']]
                print(f"   Existente: {' - '.join(map(str, nums))}")
            
            # Eliminar el existente para agregar el correcto
            df = df[df['fecha'] != '2025-08-12']
            print("🗑️ Eliminando sorteo existente del 2025-08-12 para corregir")
        
        # 3. AGREGAR sorteo correcto del 12-08-2025
        print("\n➕ Agregando sorteo correcto del 2025-08-12: 11-29-24-23-28-39")
        
        # Crear nuevo registro
        nuevo_sorteo = {
            'fecha': '2025-08-12',
            'bolilla_1': 11,
            'bolilla_2': 29,
            'bolilla_3': 24,
            'bolilla_4': 23,
            'bolilla_5': 28,
            'bolilla_6': 39
        }
        
        # Agregar columnas faltantes con valores por defecto
        for col in df.columns:
            if col not in nuevo_sorteo:
                if 'bolilla' not in col and col != 'fecha':
                    nuevo_sorteo[col] = None
        
        # Crear DataFrame del nuevo sorteo y concatenar
        nuevo_df = pd.DataFrame([nuevo_sorteo])
        df = pd.concat([df, nuevo_df], ignore_index=True)
        
        # 4. ORDENAR por fecha para mantener cronología
        df['fecha'] = pd.to_datetime(df['fecha'])
        df = df.sort_values('fecha').reset_index(drop=True)
        
        # Convertir fecha de vuelta a string
        df['fecha'] = df['fecha'].dt.strftime('%Y-%m-%d')
        
        # 5. GUARDAR dataset corregido
        print(f"\n💾 Guardando dataset corregido...")
        df.to_csv(csv_path, index=False)
        
        print(f"✅ Dataset corregido guardado: {len(df)} registros")
        
        # 6. ACTUALIZAR ultimo_resultado_oficial.json
        print("\n📄 Actualizando ultimo_resultado_oficial.json...")
        
        ultimo_resultado = {
            "fecha": "2025-08-12",
            "numeros": [11, 29, 24, 23, 28, 39],
            "fecha_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fuente": "manual_correction"
        }
        
        import json
        with open("data/ultimo_resultado_oficial.json", "w") as f:
            json.dump(ultimo_resultado, f, indent=2)
        
        print("✅ ultimo_resultado_oficial.json actualizado")
        
        # 7. VERIFICAR corrección
        print("\n🔍 Verificando corrección...")
        info_final = dm.get_data_info()
        print(f"   Total registros final: {info_final['total_records']}")
        if info_final.get('last_sorteo'):
            last_final = info_final['last_sorteo']
            print(f"   Último sorteo corregido: {last_final['fecha']} - {' - '.join(map(str, last_final['numeros']))}")
        
        print("\n🎉 CORRECCIÓN COMPLETADA EXITOSAMENTE!")
        print("="*60)
        print("✅ Eliminado: Sorteo incorrecto del 2025-08-16")
        print("✅ Agregado: Sorteo correcto del 2025-08-12: 11-29-24-23-28-39")
        print("✅ Dataset ordenado cronológicamente")
        print("✅ Archivo ultimo_resultado_oficial.json actualizado")
        print("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error corrigiendo datos: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_sorteo_data()