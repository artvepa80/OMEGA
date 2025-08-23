#!/usr/bin/env python3
"""
📊 Actualizador de Sorteos OMEGA PRO AI
Script para añadir nuevos sorteos oficiales al sistema
"""

import argparse
import logging
import sys
from modules.data_manager import OmegaDataManager
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description="Actualizar historial con nuevo sorteo oficial",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python3 update_sorteo.py --fecha 2025-08-07 --numeros 29,22,7,37,23,33
  python3 update_sorteo.py --fecha 2025-08-09 --numeros "1 15 23 31 35 40"
  python3 update_sorteo.py --info  # Mostrar información del dataset
        """
    )
    
    parser.add_argument(
        "--fecha", 
        type=str, 
        help="Fecha del sorteo (formato: YYYY-MM-DD)"
    )
    
    parser.add_argument(
        "--numeros", 
        type=str, 
        help="Números del sorteo (formato: '1,2,3,4,5,6' o '1 2 3 4 5 6')"
    )
    
    parser.add_argument(
        "--info", 
        action="store_true", 
        help="Mostrar información del dataset actual"
    )
    
    parser.add_argument(
        "--backup", 
        action="store_true", 
        help="Crear backup antes de modificar"
    )
    
    args = parser.parse_args()
    
    # Crear instancia del data manager
    dm = OmegaDataManager()
    
    # Mostrar información si se solicita
    if args.info:
        logger.info("📊 Obteniendo información del dataset...")
        info = dm.get_data_info()
        
        print("\n" + "="*60)
        print("📊 INFORMACIÓN DEL DATASET OMEGA PRO AI")
        print("="*60)
        print(f"📈 Total de registros: {info['total_records']}")
        print(f"📅 Rango de fechas: {info['date_range']['from']} → {info['date_range']['to']}")
        print(f"🗂️ Columnas disponibles: {len(info['columns'])}")
        
        if info.get('last_sorteo'):
            last = info['last_sorteo']
            print(f"\n🎯 ÚLTIMO SORTEO REGISTRADO:")
            print(f"   📅 Fecha: {last['fecha']}")
            print(f"   🎲 Números: {' - '.join(map(str, last['numeros']))}")
        
        print(f"\n✅ Calidad de datos:")
        print(f"   • Registros completos: {info['data_quality']['complete_records']}")
        print(f"   • Datos faltantes: {info['data_quality']['missing_data']}")
        
        print("="*60)
        return
    
    # Validar argumentos requeridos
    if not args.fecha or not args.numeros:
        print("❌ Error: Se requieren --fecha y --numeros")
        print("💡 Uso: python3 update_sorteo.py --fecha 2025-08-09 --numeros '1,2,3,4,5,6'")
        print("💡 Para más información: python3 update_sorteo.py --help")
        sys.exit(1)
    
    # Parsear números
    try:
        # Permitir tanto comas como espacios como separadores
        numeros_str = args.numeros.replace(',', ' ').split()
        numeros = [int(n) for n in numeros_str]
        
        if len(numeros) != 6:
            raise ValueError(f"Se requieren exactamente 6 números, proporcionados: {len(numeros)}")
        
        if not all(1 <= n <= 40 for n in numeros):
            raise ValueError(f"Todos los números deben estar entre 1 y 40")
        
    except ValueError as e:
        print(f"❌ Error en números: {e}")
        print("💡 Formato correcto: --numeros '1,2,3,4,5,6' o --numeros '1 2 3 4 5 6'")
        sys.exit(1)
    
    # Validar fecha
    try:
        fecha_dt = datetime.strptime(args.fecha, '%Y-%m-%d')
    except ValueError:
        print(f"❌ Error en fecha: formato debe ser YYYY-MM-DD")
        print(f"💡 Ejemplo: --fecha 2025-08-09")
        sys.exit(1)
    
    # Crear backup si se solicita
    if args.backup:
        logger.info("💾 Creando backup...")
        backup_path = dm.create_backup()
        if backup_path:
            print(f"✅ Backup creado: {backup_path}")
        else:
            print("⚠️ No se pudo crear backup")
    
    # Mostrar resumen antes de proceder
    print("\n" + "="*50)
    print("📊 RESUMEN DEL SORTEO A AÑADIR")
    print("="*50)
    print(f"📅 Fecha: {args.fecha}")
    print(f"🎲 Números: {' - '.join(map(str, numeros))}")
    print(f"📊 Suma: {sum(numeros)}")
    print(f"📈 Promedio: {sum(numeros)/6:.2f}")
    print(f"📏 Rango: {max(numeros) - min(numeros)}")
    print("="*50)
    
    # Confirmar acción
    respuesta = input("¿Continuar con la actualización? (s/N): ").lower().strip()
    if respuesta not in ['s', 'sí', 'si', 'y', 'yes']:
        print("❌ Operación cancelada por el usuario")
        return
    
    # Añadir sorteo
    logger.info(f"➕ Añadiendo sorteo: {args.fecha} - {numeros}")
    
    try:
        result = dm.add_new_sorteo(args.fecha, numeros)
        
        if result:
            print("\n✅ ¡SORTEO AÑADIDO EXITOSAMENTE!")
            
            # Mostrar información actualizada
            info = dm.get_data_info()
            print(f"📊 Total de registros ahora: {info['total_records']}")
            
            if info.get('last_sorteo'):
                last = info['last_sorteo']
                print(f"🎯 Último sorteo registrado:")
                print(f"   📅 {last['fecha']}")
                print(f"   🎲 {' - '.join(map(str, last['numeros']))}")
            
            print(f"\n💾 Archivos actualizados:")
            print(f"   • Historial CSV: data/historial_kabala_github_emergency_clean.csv")
            print(f"   • Último resultado: data/ultimo_resultado_oficial.json")
            
            print(f"\n🚀 El sistema OMEGA PRO AI ya puede usar estos datos para nuevas predicciones!")
            
        else:
            print("❌ Error añadiendo sorteo. Revisar logs para más detalles.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()