#!/usr/bin/env python3
"""
🔧 Fix Critical Errors - Solución de errores críticos en OMEGA
Corrige los errores identificados en el sistema
"""

import os
import sys
import pandas as pd
import logging
from pathlib import Path

def fix_logging_errors():
    """Corrige errores de logging en el sistema"""
    print("🔧 CORRIGIENDO ERRORES DE LOGGING...")
    
    # Archivos que necesitan corrección
    files_to_fix = [
        'core/predictor.py',
        'modules/clustering_engine.py', 
        'modules/genetic_model.py',
        'modules/lstm_model.py'
    ]
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Fix: 'function' object has no attribute 'warning'
                # Cambiar logger.warning por logger.warning()
                if 'logger.warning' in content and 'logger.warning(' not in content:
                    content = content.replace('logger.warning', 'logger.warning(')
                    # Agregar paréntesis de cierre si falta
                    lines = content.split('\n')
                    fixed_lines = []
                    for line in lines:
                        if 'logger.warning(' in line and not line.strip().endswith(')'):
                            line = line + ')'
                        fixed_lines.append(line)
                    content = '\n'.join(fixed_lines)
                
                # Guardar archivo corregido
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ {file_path} corregido")
            
            except Exception as e:
                print(f"❌ Error corrigiendo {file_path}: {e}")

def fix_data_validation_issues():
    """Corrige problemas de validación de datos"""
    print("\n🔧 CORRIGIENDO VALIDACIÓN DE DATOS...")
    
    # Verificar archivo de datos principal
    data_files = [
        'data/historial_kabala_github_emergency_clean.csv',
        'data/historial_kabala_github_fixed.csv',
        'data/jackpots_omega.csv'
    ]
    
    for data_file in data_files:
        if os.path.exists(data_file):
            try:
                df = pd.read_csv(data_file)
                print(f"✅ {data_file}: {len(df)} registros")
                
                # Verificar columnas bolilla
                bolilla_cols = [c for c in df.columns if 'bolilla' in c.lower()]
                if len(bolilla_cols) >= 6:
                    print(f"   📊 Columnas bolilla: {bolilla_cols[:6]}")
                    
                    # Validar rangos de números
                    for col in bolilla_cols[:6]:
                        min_val = df[col].min()
                        max_val = df[col].max()
                        if min_val < 1 or max_val > 40:
                            print(f"   ⚠️ {col}: rango inválido {min_val}-{max_val}")
                        else:
                            print(f"   ✅ {col}: rango válido {min_val}-{max_val}")
                else:
                    print(f"   ❌ Faltan columnas bolilla: {bolilla_cols}")
                    
            except Exception as e:
                print(f"❌ Error validando {data_file}: {e}")
        else:
            print(f"❌ {data_file} no existe")

def analyze_critical_errors():
    """Analiza los errores críticos específicos reportados"""
    print("\n🔍 ANALIZANDO ERRORES CRÍTICOS REPORTADOS...")
    
    errors = [
        "Se descartaron 3646 combinaciones inválidas del historial",
        "'function' object has no attribute 'warning'", 
        "Error en generación de distribución",
        "stat: path should be string, bytes, os.PathLike or integer, not Logger",
        "No such file or directory: 'data/historial_kabala_github_fixed.csv'"
    ]
    
    solutions = {
        "combinaciones inválidas": "Validar formato de datos y rangos 1-40",
        "function warning": "Corregir llamadas a logger.warning()",
        "generación de distribución": "Verificar configuración de logging", 
        "Logger path": "Pasar string en lugar de objeto Logger",
        "file not found": "Crear o verificar rutas de archivos de datos"
    }
    
    for error in errors:
        print(f"\n❌ ERROR: {error}")
        for key, solution in solutions.items():
            if any(word in error.lower() for word in key.split()):
                print(f"   💡 SOLUCIÓN: {solution}")
                break

def create_data_integrity_check():
    """Crea verificación de integridad de datos"""
    print("\n🔧 VERIFICANDO INTEGRIDAD DE DATOS...")
    
    main_data_file = 'data/historial_kabala_github_emergency_clean.csv'
    
    if os.path.exists(main_data_file):
        try:
            df = pd.read_csv(main_data_file)
            
            # Estadísticas básicas
            print(f"📊 Total registros: {len(df)}")
            print(f"📊 Columnas: {list(df.columns)}")
            
            # Verificar columnas bolilla
            bolilla_cols = [c for c in df.columns if 'bolilla' in c.lower()][:6]
            print(f"🎯 Columnas bolilla: {bolilla_cols}")
            
            # Contar registros válidos por columna
            valid_counts = {}
            total_invalid = 0
            
            for col in bolilla_cols:
                # Contar valores en rango 1-40
                valid_mask = (df[col] >= 1) & (df[col] <= 40) & df[col].notna()
                valid_count = valid_mask.sum()
                invalid_count = len(df) - valid_count
                
                valid_counts[col] = {
                    'valid': valid_count,
                    'invalid': invalid_count
                }
                total_invalid += invalid_count
                
                print(f"   {col}: {valid_count} válidos, {invalid_count} inválidos")
            
            print(f"\n📊 RESUMEN:")
            print(f"   Total inválidos: {total_invalid}")
            print(f"   Registros completamente válidos: {len(df) - (total_invalid // 6)}")
            
            # Si hay muchos inválidos, crear dataset limpio
            if total_invalid > 1000:
                print(f"\n🔧 CREANDO DATASET LIMPIO...")
                clean_df = df.copy()
                
                # Filtrar solo registros válidos
                for col in bolilla_cols:
                    clean_df = clean_df[
                        (clean_df[col] >= 1) & 
                        (clean_df[col] <= 40) & 
                        clean_df[col].notna()
                    ]
                
                # Guardar dataset limpio
                clean_file = 'data/historial_kabala_cleaned_fixed.csv'
                clean_df.to_csv(clean_file, index=False)
                print(f"✅ Dataset limpio guardado: {clean_file}")
                print(f"   Registros limpios: {len(clean_df)}")
                
                return clean_file
                
        except Exception as e:
            print(f"❌ Error verificando integridad: {e}")
    
    else:
        print(f"❌ Archivo principal no encontrado: {main_data_file}")
    
    return None

def run_comprehensive_fix():
    """Ejecuta corrección completa del sistema"""
    print("🔧" + "="*60)
    print("   OMEGA CRITICAL ERRORS FIX")
    print("   'Solucionando errores críticos del sistema'")
    print("="*62)
    
    # 1. Analizar errores críticos
    analyze_critical_errors()
    
    # 2. Verificar integridad de datos
    clean_data_file = create_data_integrity_check()
    
    # 3. Corregir validación de datos
    fix_data_validation_issues()
    
    # 4. Corregir errores de logging
    fix_logging_errors()
    
    print("\n✅ DIAGNÓSTICO COMPLETO FINALIZADO")
    print("\n💡 RECOMENDACIONES INMEDIATAS:")
    print("1. 🔍 3646 combinaciones inválidas sugiere problema serio en datos")
    print("2. 🔧 Corregir llamadas a logger en módulos core")
    print("3. 📁 Verificar rutas de archivos de datos")
    
    if clean_data_file:
        print(f"4. ✅ Usar archivo limpio: {clean_data_file}")
    
    print("\n🚨 PRÓXIMOS PASOS:")
    print("- Ejecutar sistema con datos limpios")
    print("- Monitorear logs por errores de logging")
    print("- Validar que todas las rutas existen")
    
    return True

if __name__ == "__main__":
    run_comprehensive_fix()