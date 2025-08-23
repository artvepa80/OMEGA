#!/usr/bin/env python3
"""
Script para aplicar correcciones a OMEGA PRO AI v10.1
Ya tenemos el CSV corregido, solo falta actualizar el código
"""

import os
import re
from datetime import datetime

def backup_file(filepath):
    """Crear backup del archivo original"""
    if os.path.exists(filepath):
        backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(filepath, 'r') as f:
            content = f.read()
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"✅ Backup creado: {backup_path}")
        return True
    return False

def fix_main_py():
    """Actualizar main.py para usar el CSV corregido"""
    filepath = "main.py"
    if not os.path.exists(filepath):
        print(f"❌ {filepath} no encontrado")
        return False
    
    backup_file(filepath)
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Contador de cambios
    changes = 0
    
    # Reemplazar en la función main
    new_content = content.replace(
        'data_path="data/historial_kabala_github.csv"',
        'data_path="data/historial_kabala_github_fixed.csv"'
    )
    if new_content != content:
        changes += 1
        content = new_content
    
    # Reemplazar en argparse
    new_content = content.replace(
        'default="data/historial_kabala_github.csv"',
        'default="data/historial_kabala_github_fixed.csv"'
    )
    if new_content != content:
        changes += 1
        content = new_content
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✅ main.py actualizado ({changes} cambios)")
    return True

def fix_consensus_engine():
    """Arreglar GeneticConfig en consensus_engine.py"""
    filepath = "core/consensus_engine.py"
    if not os.path.exists(filepath):
        print(f"❌ {filepath} no encontrado")
        return False
    
    backup_file(filepath)
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Reemplazar GeneticConfig con parámetros incorrectos
    pattern = r'cfg = GeneticConfig\(poblacion_inicial=\d+, generaciones=\d+\)'
    replacement = 'cfg = GeneticConfig()  # Fixed: usando defaults'
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"✅ consensus_engine.py corregido")
    else:
        print(f"ℹ️ consensus_engine.py ya estaba correcto o no se encontró el patrón")
    
    return True

def fix_predictor_py():
    """Actualizar predictor.py para usar el CSV corregido"""
    filepath = "core/predictor.py"
    if not os.path.exists(filepath):
        print(f"❌ {filepath} no encontrado")
        return False
    
    backup_file(filepath)
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Reemplazar en DEFAULT_DATA_PATHS
    content = content.replace(
        '"data/historial_kabala_github.csv"',
        '"data/historial_kabala_github_fixed.csv"'
    )
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✅ predictor.py actualizado")
    return True

def fix_jackpot_profiler():
    """Agregar método faltante predecir_perfil"""
    filepath = "modules/profiling/jackpot_profiler.py"
    if not os.path.exists(filepath):
        print(f"❌ {filepath} no encontrado")
        return False
    
    backup_file(filepath)
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Verificar si ya existe el método
    if "def predecir_perfil" in content:
        print("ℹ️ predecir_perfil ya existe en jackpot_profiler.py")
        return True
    
    # Buscar donde insertar (después de predecir_probabilidades)
    lines = content.split('\n')
    insert_index = -1
    
    for i, line in enumerate(lines):
        if "def predecir_probabilidades" in line:
            # Buscar el final de este método
            indent = len(line) - len(line.lstrip())
            for j in range(i+1, len(lines)):
                # Cuando encontramos algo con la misma indentación, insertamos antes
                if lines[j].strip() and not lines[j].startswith(' ' * (indent + 4)):
                    if lines[j].startswith(' ' * indent) or not lines[j].startswith(' '):
                        insert_index = j
                        break
    
    if insert_index > 0:
        # Insertar el nuevo método
        new_method = '''
    def predecir_perfil(self, combinacion: List[int]) -> Dict[str, Any]:
        """
        Alias para mantener compatibilidad con el código que espera 'predecir_perfil'.
        """
        return self.predecir_probabilidades(combinacion)
'''
        lines.insert(insert_index, new_method)
        
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"✅ Método predecir_perfil agregado a jackpot_profiler.py")
    else:
        print(f"⚠️ No se pudo encontrar dónde insertar el método")
    
    return True

def main():
    print("=" * 60)
    print("🔧 APLICANDO CORRECCIONES A OMEGA PRO AI v10.1")
    print("=" * 60)
    
    # Verificar que existe el CSV corregido
    if not os.path.exists("data/historial_kabala_github_fixed.csv"):
        print("❌ No se encuentra el CSV corregido")
        print("   Ejecuta primero: python fix_csv_order.py data/historial_kabala_github.csv")
        return
    
    print("✅ CSV corregido encontrado\n")
    
    # Aplicar correcciones
    fixes = [
        ("main.py", fix_main_py),
        ("consensus_engine.py", fix_consensus_engine),
        ("predictor.py", fix_predictor_py),
        ("jackpot_profiler.py", fix_jackpot_profiler)
    ]
    
    success = 0
    for name, func in fixes:
        print(f"\n📝 Procesando {name}...")
        try:
            if func():
                success += 1
        except Exception as e:
            print(f"❌ Error procesando {name}: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ Correcciones aplicadas: {success}/{len(fixes)}")
    
    if success == len(fixes):
        print("\n🎉 ¡Todas las correcciones aplicadas exitosamente!")
        print("\n📋 Ahora puedes ejecutar:")
        print("   python main.py --top_n 10")
    else:
        print("\n⚠️ Algunas correcciones fallaron")

if __name__ == "__main__":
    main()
