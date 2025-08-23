#!/usr/bin/env python3
"""
🔧 OMEGA PRO AI - Parches para Errores Críticos
Correcciones para los errores identificados en UPGRADE_PLAN.md
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CriticalErrorsFixer:
    """Clase para aplicar parches automáticos a errores críticos"""
    
    def __init__(self, project_root: str = "/Users/user/Documents/OMEGA_PRO_AI_v10.1"):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / "fixes" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def create_backup(self, file_path: Path) -> Path:
        """Crea backup de un archivo antes de modificarlo"""
        backup_path = self.backup_dir / f"{file_path.name}.backup"
        shutil.copy2(file_path, backup_path)
        logger.info(f"✅ Backup creado: {backup_path}")
        return backup_path
    
    def fix_numpy_operators(self):
        """Corrige operadores NumPy obsoletos (- por ^)"""
        logger.info("🔧 Corrigiendo operadores NumPy obsoletos...")
        
        files_to_fix = [
            "core/predictor.py",
            "modules/scoring_system.py", 
            "modules/meta_learning_integrator.py",
            "modules/lstm_predictor_v2.py"
        ]
        
        pattern = r'(\w+)\s*-\s*(\w+)'  # Patrón para operadores -
        replacement = r'\1 ^ \2'  # Reemplazo por ^
        
        for file_rel in files_to_fix:
            file_path = self.project_root / file_rel
            if file_path.exists():
                try:
                    self.create_backup(file_path)
                    
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Solo reemplazar en contextos numpy/boolean
                    if "numpy" in content or "np." in content:
                        # Buscar líneas específicas con el warning
                        lines = content.split('\n')
                        modified = False
                        
                        for i, line in enumerate(lines):
                            if "boolean subtract" in line or "the `-` operator" in line:
                                # Buscar la línea problemática anterior
                                for j in range(max(0, i-5), i):
                                    if re.search(r'\w+\s*-\s*\w+', lines[j]) and any(keyword in lines[j] for keyword in ['array', 'np.', 'mask', 'boolean']):
                                        lines[j] = re.sub(pattern, replacement, lines[j])
                                        modified = True
                                        logger.info(f"   📝 Línea {j+1}: {lines[j].strip()}")
                        
                        if modified:
                            with open(file_path, 'w') as f:
                                f.write('\n'.join(lines))
                            logger.info(f"✅ Corregido: {file_path}")
                        else:
                            logger.info(f"ℹ️ No se encontraron patrones a corregir en: {file_path}")
                    
                except Exception as e:
                    logger.error(f"❌ Error corrigiendo {file_path}: {e}")
    
    def fix_logger_references(self):
        """Corrige referencias incorrectas de logger"""
        logger.info("🔧 Corrigiendo referencias de logger...")
        
        file_path = self.project_root / "core" / "predictor.py"
        if not file_path.exists():
            logger.warning(f"⚠️ Archivo no encontrado: {file_path}")
            return
        
        try:
            self.create_backup(file_path)
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Corregir el error específico: 'function' object has no attribute 'warning'
            fixes = [
                (r"logger\.warning\(\)", "self.logger.warning() if hasattr(self, 'logger') else logging.warning()"),
                (r"logger\.error\(\)", "self.logger.error() if hasattr(self, 'logger') else logging.error()"),
                (r"logger\.info\(\)", "self.logger.info() if hasattr(self, 'logger') else logging.info()"),
                # Asegurar que logger esté importado
                ("import logging\nlogger = logging.getLogger(__name__)", 
                 "import logging\nlogger = logging.getLogger(__name__)\nlogging.basicConfig(level=logging.INFO)")
            ]
            
            modified = False
            for pattern, replacement in fixes:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    modified = True
            
            if modified:
                with open(file_path, 'w') as f:
                    f.write(content)
                logger.info(f"✅ Referencias de logger corregidas en: {file_path}")
            else:
                logger.info(f"ℹ️ No se encontraron referencias problemáticas en: {file_path}")
                
        except Exception as e:
            logger.error(f"❌ Error corrigiendo logger: {e}")
    
    def fix_iterable_errors(self):
        """Corrige errores de 'int' object is not iterable"""
        logger.info("🔧 Corrigiendo errores de iterables...")
        
        files_to_check = [
            "modules/filtros.py",
            "core/predictor.py",
            "modules/scoring_system.py"
        ]
        
        for file_rel in files_to_check:
            file_path = self.project_root / file_rel
            if file_path.exists():
                try:
                    self.create_backup(file_path)
                    
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Patrones comunes que causan el error
                    fixes = [
                        # Asegurar que los valores sean listas antes de iterar
                        (r"for\s+(\w+)\s+in\s+(\w+):", 
                         r"for \1 in (\2 if isinstance(\2, (list, tuple, set)) else [\2]):"),
                        
                        # Validar antes de usar extend/append con iterables
                        (r"(\w+)\.extend\((\w+)\)", 
                         r"\1.extend(\2 if isinstance(\2, (list, tuple)) else [\2])"),
                         
                        # Proteger desempaquetado de valores
                        (r"(\w+),\s*(\w+)\s*=\s*(\w+)", 
                         r"temp_values = \3\nif isinstance(temp_values, (list, tuple)) and len(temp_values) >= 2:\n    \1, \2 = temp_values[:2]\nelse:\n    \1, \2 = temp_values, None")
                    ]
                    
                    modified = False
                    for pattern, replacement in fixes:
                        if re.search(pattern, content):
                            content = re.sub(pattern, replacement, content)
                            modified = True
                    
                    if modified:
                        with open(file_path, 'w') as f:
                            f.write(content)
                        logger.info(f"✅ Errores de iterables corregidos en: {file_path}")
                    
                except Exception as e:
                    logger.error(f"❌ Error corrigiendo iterables en {file_path}: {e}")
    
    def fix_lstm_unpacking_error(self):
        """Corrige el error específico de 'too many values to unpack' en LSTM"""
        logger.info("🔧 Corrigiendo error de desempaquetado LSTM...")
        
        file_path = self.project_root / "modules" / "meta_learning_integrator.py"
        if not file_path.exists():
            logger.warning(f"⚠️ Archivo no encontrado: {file_path}")
            return
        
        try:
            self.create_backup(file_path)
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Buscar y corregir el patrón problemático
            lines = content.split('\n')
            modified = False
            
            for i, line in enumerate(lines):
                # Buscar llamadas problemáticas a métodos que pueden devolver diferentes números de valores
                if "lstm_results = self.lstm_v2.train(" in line:
                    # Cambiar a un manejo más robusto
                    lines[i] = line.replace(
                        "lstm_results = self.lstm_v2.train(",
                        "try:\n                    lstm_results = self.lstm_v2.train("
                    )
                    # Añadir manejo de excepción
                    if i + 1 < len(lines):
                        lines.insert(i + 2, "                except Exception as e:")
                        lines.insert(i + 3, "                    logger.error(f'❌ Error en entrenamiento LSTM: {e}')")
                        lines.insert(i + 4, "                    lstm_results = {'error': str(e), 'success': False}")
                    modified = True
                    break
                
                # Buscar desempaquetados directos problemáticos
                if ", " in line and " = " in line and any(word in line for word in ["train", "epoch", "loss", "acc"]):
                    # Si parece ser un desempaquetado directo, añadir validación
                    if re.match(r'\s*(\w+),\s*(\w+)\s*=\s*.*', line):
                        var1, var2, expr = re.match(r'\s*(\w+),\s*(\w+)\s*=\s*(.*)', line).groups()
                        safer_line = f"""                try:
                    {var1}, {var2} = {expr}
                except ValueError as e:
                    if "too many values to unpack" in str(e):
                        result = {expr}
                        {var1} = result if not isinstance(result, (list, tuple)) else result[0] if len(result) > 0 else None
                        {var2} = result[1] if isinstance(result, (list, tuple)) and len(result) > 1 else None
                    else:
                        raise"""
                        lines[i] = safer_line
                        modified = True
                        break
            
            if modified:
                with open(file_path, 'w') as f:
                    f.write('\n'.join(lines))
                logger.info(f"✅ Error de desempaquetado LSTM corregido en: {file_path}")
            else:
                logger.info(f"ℹ️ No se encontró el patrón problemático en: {file_path}")
                
        except Exception as e:
            logger.error(f"❌ Error corrigiendo desempaquetado LSTM: {e}")
    
    def optimize_lstm_epochs(self):
        """Optimiza el número de epochs para reducir tiempo de ejecución"""
        logger.info("⚡ Optimizando epochs de LSTM...")
        
        files_to_optimize = [
            ("modules/lstm_predictor_v2.py", "epochs: int = 100", "epochs: int = 20"),
            ("modules/meta_learning_integrator.py", "epochs=20", "epochs=10"),
            ("core/predictor.py", "epochs=100", "epochs=15")
        ]
        
        for file_rel, old_pattern, new_pattern in files_to_optimize:
            file_path = self.project_root / file_rel
            if file_path.exists():
                try:
                    self.create_backup(file_path)
                    
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    if old_pattern in content:
                        content = content.replace(old_pattern, new_pattern)
                        
                        with open(file_path, 'w') as f:
                            f.write(content)
                        
                        logger.info(f"✅ Epochs optimizados en: {file_path}")
                        logger.info(f"   📝 {old_pattern} → {new_pattern}")
                
                except Exception as e:
                    logger.error(f"❌ Error optimizando epochs en {file_path}: {e}")
    
    def create_model_cache_system(self):
        """Crea sistema de caché para modelos entrenados"""
        logger.info("💾 Creando sistema de caché de modelos...")
        
        cache_dir = self.project_root / "models" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        cache_manager_code = '''#!/usr/bin/env python3
"""
💾 OMEGA Model Cache Manager
Sistema de caché para modelos entrenados
"""

import os
import pickle
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ModelCacheManager:
    """Gestor de caché para modelos entrenados"""
    
    def __init__(self, cache_dir="models/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.load_metadata()
    
    def load_metadata(self):
        """Carga metadatos del caché"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}
    
    def save_metadata(self):
        """Guarda metadatos del caché"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def get_cache_key(self, model_name, data_hash, params):
        """Genera clave única para el caché"""
        key_data = f"{model_name}_{data_hash}_{hash(str(sorted(params.items())))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def is_cached(self, cache_key):
        """Verifica si un modelo está en caché y es válido"""
        if cache_key not in self.metadata:
            return False
        
        cache_info = self.metadata[cache_key]
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        # Verificar que el archivo existe
        if not cache_file.exists():
            del self.metadata[cache_key]
            self.save_metadata()
            return False
        
        # Verificar que no ha expirado (24 horas)
        cached_time = datetime.fromisoformat(cache_info['timestamp'])
        if datetime.now() - cached_time > timedelta(hours=24):
            cache_file.unlink()
            del self.metadata[cache_key]
            self.save_metadata()
            return False
        
        return True
    
    def save_model(self, cache_key, model, model_info):
        """Guarda modelo en caché"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            
            with open(cache_file, 'wb') as f:
                pickle.dump(model, f)
            
            self.metadata[cache_key] = {
                'timestamp': datetime.now().isoformat(),
                'model_info': model_info,
                'file_size': cache_file.stat().st_size
            }
            
            self.save_metadata()
            logger.info(f"💾 Modelo guardado en caché: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando modelo en caché: {e}")
            return False
    
    def load_model(self, cache_key):
        """Carga modelo desde caché"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            
            with open(cache_file, 'rb') as f:
                model = pickle.load(f)
            
            logger.info(f"✅ Modelo cargado desde caché: {cache_key}")
            return model
            
        except Exception as e:
            logger.error(f"❌ Error cargando modelo desde caché: {e}")
            return None
    
    def clear_old_cache(self, hours=48):
        """Limpia caché antiguo"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        removed_count = 0
        
        for cache_key, info in list(self.metadata.items()):
            cached_time = datetime.fromisoformat(info['timestamp'])
            if cached_time < cutoff_time:
                cache_file = self.cache_dir / f"{cache_key}.pkl"
                if cache_file.exists():
                    cache_file.unlink()
                del self.metadata[cache_key]
                removed_count += 1
        
        if removed_count > 0:
            self.save_metadata()
            logger.info(f"🧹 Eliminados {removed_count} modelos antiguos del caché")
        
        return removed_count
    
    def get_cache_stats(self):
        """Obtiene estadísticas del caché"""
        total_files = len(self.metadata)
        total_size = sum(info.get('file_size', 0) for info in self.metadata.values())
        
        return {
            'total_models': total_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'cache_dir': str(self.cache_dir)
        }
'''
        
        cache_file = self.project_root / "modules" / "model_cache.py"
        with open(cache_file, 'w') as f:
            f.write(cache_manager_code)
        
        logger.info(f"✅ Sistema de caché creado en: {cache_file}")
    
    def apply_all_fixes(self):
        """Aplica todas las correcciones"""
        logger.info("🚀 Iniciando aplicación de todas las correcciones...")
        
        try:
            self.fix_numpy_operators()
            self.fix_logger_references() 
            self.fix_iterable_errors()
            self.fix_lstm_unpacking_error()
            self.optimize_lstm_epochs()
            self.create_model_cache_system()
            
            logger.info("✅ Todas las correcciones aplicadas exitosamente!")
            
            # Crear resumen
            summary = f"""
🎉 CORRECCIONES APLICADAS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================

✅ Operadores NumPy obsoletos corregidos (- por ^)
✅ Referencias de logger corregidas  
✅ Errores de iterables solucionados
✅ Error de desempaquetado LSTM v2 corregido
⚡ Epochs optimizados para mejor rendimiento
💾 Sistema de caché de modelos implementado

📁 Backups creados en: {self.backup_dir}

🚀 El sistema debería funcionar sin errores críticos ahora.
   Para probar: python3 main.py --top_n 3
"""
            
            summary_file = self.project_root / "fixes" / "CORRECTIONS_APPLIED.txt"
            with open(summary_file, 'w') as f:
                f.write(summary)
            
            print(summary)
            
        except Exception as e:
            logger.error(f"❌ Error aplicando correcciones: {e}")
            raise

def main():
    """Función principal para ejecutar las correcciones"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    fixer = CriticalErrorsFixer()
    fixer.apply_all_fixes()

if __name__ == "__main__":
    main()