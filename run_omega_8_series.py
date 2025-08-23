#!/usr/bin/env python3
"""
🎯 OMEGA PRO AI v10.1 - Ejecutor para 8 Series
Script optimizado para generar exactamente 8 series con todos los modelos activos
"""

import os
import sys
from datetime import datetime

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

def ejecutar_omega_8_series():
    """
    Ejecuta OMEGA PRO AI con configuración optimizada para 8 series
    """
    print("🚀 OMEGA PRO AI v10.1 - Generador de 8 Series")
    print("=" * 60)
    print("🔥 TODOS LOS MODELOS ACTIVADOS PARA MÁXIMA PRECISIÓN")
    print("🎯 Generando exactamente 8 series finales")
    print("=" * 60)
    print(f"📅 Fecha de ejecución: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    try:
        # Ejecutar main con configuración optimizada para 8 series
        resultado = main(
            data_path="data/historial_kabala_github.csv",
            svi_profile="default",
            top_n=8,  # Exactamente 8 series
            enable_models=["all"],  # Todos los modelos activos
            export_formats=["csv", "json"],
            viabilidad_config="config/viabilidad.json",
            retrain=False,  # Optimizado para velocidad
            evaluate=False,  # Optimizado para velocidad
            backtest=False,  # Optimizado para velocidad
            disable_multiprocessing=False,
            dry_run=False
        )
        
        print("\n" + "🎉" * 20)
        print("✅ EJECUCIÓN COMPLETADA EXITOSAMENTE")
        print(f"📊 Generadas {len(resultado)} series finales")
        print("🎉" * 20)
        
        return resultado
        
    except Exception as e:
        print(f"\n❌ ERROR EN LA EJECUCIÓN: {e}")
        print("📝 Revisa los logs para más detalles")
        return []

if __name__ == "__main__":
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("data/historial_kabala_github.csv"):
        print("❌ ERROR: No se encontró el archivo de datos históricos")
        print("📁 Asegúrate de ejecutar desde el directorio raíz del proyecto")
        sys.exit(1)
    
    if not os.path.exists("config/viabilidad.json"):
        print("❌ ERROR: No se encontró el archivo de configuración")
        print("📁 Asegúrate de que existe config/viabilidad.json")
        sys.exit(1)
    
    # Ejecutar el sistema
    series_generadas = ejecutar_omega_8_series()
    
    if series_generadas:
        print(f"\n🎯 SISTEMA COMPLETADO: {len(series_generadas)} series listas para usar")
    else:
        print("\n⚠️ No se generaron series. Revisa los logs.")
        sys.exit(1)