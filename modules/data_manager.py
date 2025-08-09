#!/usr/bin/env python3
"""
📊 OMEGA Data Manager - Gestor de Datos Mejorado
Maneja la lectura, validación y actualización del historial de sorteos
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import logging
import json
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

class OmegaDataManager:
    """Gestor robusto de datos históricos de sorteos"""
    
    def __init__(self, data_path: str = "data/historial_kabala_github_emergency_clean.csv"):
        self.data_path = data_path
        self.backup_dir = "data/backups"
        self.ensure_backup_dir()
        
        # Columnas esperadas del CSV
        self.expected_columns = [
            'fecha', 'Bolilla 1', 'Bolilla 2', 'Bolilla 3', 
            'Bolilla 4', 'Bolilla 5', 'Bolilla 6'
        ]
        
        # Mapping para normalizar nombres de columnas
        self.column_mapping = {
            'Bolilla 1': 'bolilla_1',
            'Bolilla 2': 'bolilla_2', 
            'Bolilla 3': 'bolilla_3',
            'Bolilla 4': 'bolilla_4',
            'Bolilla 5': 'bolilla_5',
            'Bolilla 6': 'bolilla_6'
        }
        
    def ensure_backup_dir(self):
        """Crea directorio de backups si no existe"""
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
        
    def create_backup(self) -> str:
        """Crea backup del archivo CSV actual"""
        if not os.path.exists(self.data_path):
            logger.warning(f"⚠️ Archivo no existe para backup: {self.data_path}")
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"historial_backup_{timestamp}.csv")
        
        try:
            shutil.copy2(self.data_path, backup_path)
            logger.info(f"✅ Backup creado: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"❌ Error creando backup: {e}")
            return None
    
    def load_historical_data(self) -> pd.DataFrame:
        """
        Carga datos históricos con validación robusta
        
        Returns:
            DataFrame limpio y validado
        """
        # Intentar múltiples rutas de archivo
        possible_paths = [
            self.data_path,
            "data/historial_kabala_github.csv",
            "data/historial_kabala_github_fixed.csv"
        ]
        
        df = None
        used_path = None
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    logger.info(f"📂 Intentando cargar: {path}")
                    df = pd.read_csv(path)
                    used_path = path
                    break
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando {path}: {e}")
                    continue
        
        if df is None:
            raise FileNotFoundError(f"No se pudo cargar ningún archivo de datos históricos")
        
        logger.info(f"✅ Datos cargados desde: {used_path}")
        logger.info(f"📊 Dimensiones: {df.shape}")
        logger.info(f"🏷️ Columnas: {list(df.columns)}")
        
        # Validar y limpiar datos
        df_clean = self.validate_and_clean_data(df)
        
        return df_clean
    
    def validate_and_clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Valida y limpia el DataFrame
        
        Args:
            df: DataFrame raw
            
        Returns:
            DataFrame limpio y validado
        """
        logger.info("🧹 Iniciando validación y limpieza de datos...")
        
        # 1. Normalizar nombres de columnas
        df = self.normalize_column_names(df)
        
        # 2. Validar columnas requeridas
        missing_cols = self.validate_required_columns(df)
        if missing_cols:
            logger.error(f"❌ Columnas faltantes: {missing_cols}")
            # Intentar mapear columnas alternativas
            df = self.attempt_column_mapping(df)
        
        # 3. Limpiar datos de bolillas
        df = self.clean_bolilla_data(df)
        
        # 4. Validar fechas
        df = self.validate_dates(df)
        
        # 5. Eliminar duplicados
        initial_rows = len(df)
        df = df.drop_duplicates()
        if len(df) < initial_rows:
            logger.info(f"🔄 Eliminados {initial_rows - len(df)} duplicados")
        
        # 6. Ordenar por fecha
        if 'fecha' in df.columns:
            df = df.sort_values('fecha')
            df = df.reset_index(drop=True)
        
        logger.info(f"✅ Datos limpiados: {len(df)} registros válidos")
        return df
    
    def normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza nombres de columnas"""
        # Aplicar mapping si es necesario
        df = df.rename(columns=self.column_mapping)
        
        # Limpiar espacios y caracteres especiales
        new_columns = {}
        for col in df.columns:
            clean_col = col.strip().lower().replace(' ', '_')
            if clean_col != col:
                new_columns[col] = clean_col
        
        if new_columns:
            df = df.rename(columns=new_columns)
            logger.info(f"🏷️ Columnas normalizadas: {new_columns}")
        
        return df
    
    def validate_required_columns(self, df: pd.DataFrame) -> List[str]:
        """Valida que existan las columnas requeridas"""
        required = ['fecha', 'bolilla_1', 'bolilla_2', 'bolilla_3', 'bolilla_4', 'bolilla_5', 'bolilla_6']
        missing = [col for col in required if col not in df.columns]
        return missing
    
    def attempt_column_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """Intenta mapear columnas alternativas"""
        logger.info("🔍 Intentando mapeo automático de columnas...")
        
        # Buscar columnas que contengan 'bolilla' o números
        bolilla_cols = [col for col in df.columns if 'bolilla' in col.lower()]
        
        if len(bolilla_cols) >= 6:
            # Mapear automáticamente
            mapping = {}
            for i, col in enumerate(sorted(bolilla_cols)[:6], 1):
                mapping[col] = f'bolilla_{i}'
            
            df = df.rename(columns=mapping)
            logger.info(f"✅ Mapeo automático exitoso: {mapping}")
        
        return df
    
    def clean_bolilla_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia datos de bolillas"""
        bolilla_cols = [f'bolilla_{i}' for i in range(1, 7)]
        
        for col in bolilla_cols:
            if col in df.columns:
                # Convertir a numérico, reemplazar NaN
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Validar rango 1-40
                df = df[(df[col] >= 1) & (df[col] <= 40)]
        
        # Eliminar filas con NaN en bolillas
        df = df.dropna(subset=bolilla_cols)
        
        # Convertir a int
        for col in bolilla_cols:
            if col in df.columns:
                df[col] = df[col].astype(int)
        
        return df
    
    def validate_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Valida y limpia fechas"""
        if 'fecha' not in df.columns:
            return df
            
        # Convertir a datetime
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        
        # Eliminar fechas inválidas
        df = df.dropna(subset=['fecha'])
        
        # Validar rango razonable (desde 1990)
        min_date = datetime(1990, 1, 1)
        max_date = datetime.now() + timedelta(days=30)  # Permitir fechas futuras cercanas
        
        df = df[(df['fecha'] >= min_date) & (df['fecha'] <= max_date)]
        
        return df
    
    def add_new_sorteo(self, fecha: str, numeros: List[int]) -> bool:
        """
        Añade un nuevo sorteo al archivo CSV
        
        Args:
            fecha: Fecha del sorteo (YYYY-MM-DD)
            numeros: Lista de 6 números del sorteo
            
        Returns:
            bool: True si se añadió exitosamente
        """
        logger.info(f"➕ Añadiendo nuevo sorteo: {fecha} - {numeros}")
        
        # Validar entrada
        if len(numeros) != 6:
            logger.error(f"❌ Debe proporcionar exactamente 6 números, recibidos: {len(numeros)}")
            return False
        
        if not all(1 <= n <= 40 for n in numeros):
            logger.error(f"❌ Números fuera del rango 1-40: {numeros}")
            return False
        
        # Validar fecha
        try:
            fecha_dt = pd.to_datetime(fecha)
        except:
            logger.error(f"❌ Fecha inválida: {fecha}")
            return False
        
        # Crear backup antes de modificar
        backup_path = self.create_backup()
        if not backup_path:
            logger.warning("⚠️ No se pudo crear backup, continuando...")
        
        try:
            # Cargar datos actuales
            df = self.load_historical_data()
            
            # Verificar si ya existe este sorteo
            if 'fecha' in df.columns:
                if any(df['fecha'] == fecha_dt):
                    logger.warning(f"⚠️ Sorteo para {fecha} ya existe, actualizando...")
                    df = df[df['fecha'] != fecha_dt]  # Remover existente
            
            # Crear nuevo registro
            new_row = {
                'fecha': fecha_dt,
                'bolilla_1': numeros[0],
                'bolilla_2': numeros[1],
                'bolilla_3': numeros[2],
                'bolilla_4': numeros[3],
                'bolilla_5': numeros[4],
                'bolilla_6': numeros[5]
            }
            
            # Calcular métricas adicionales si existen esas columnas
            if 'suma_total' in df.columns:
                new_row['suma_total'] = sum(numeros)
            if 'promedio' in df.columns:
                new_row['promedio'] = round(sum(numeros) / 6, 2)
            if 'rango' in df.columns:
                new_row['rango'] = max(numeros) - min(numeros)
            
            # Añadir a DataFrame
            new_df = pd.DataFrame([new_row])
            df = pd.concat([df, new_df], ignore_index=True)
            
            # Ordenar por fecha
            df = df.sort_values('fecha').reset_index(drop=True)
            
            # Guardar archivo actualizado
            df.to_csv(self.data_path, index=False)
            logger.info(f"✅ Sorteo añadido exitosamente al archivo {self.data_path}")
            
            # Actualizar último resultado oficial
            self.update_last_official_result(fecha, numeros)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error añadiendo sorteo: {e}")
            
            # Restaurar backup si existe
            if backup_path and os.path.exists(backup_path):
                try:
                    shutil.copy2(backup_path, self.data_path)
                    logger.info(f"🔄 Archivo restaurado desde backup")
                except:
                    logger.error(f"❌ No se pudo restaurar backup")
            
            return False
    
    def update_last_official_result(self, fecha: str, numeros: List[int]):
        """Actualiza el archivo de último resultado oficial"""
        result_data = {
            "fecha": fecha,
            "numeros": numeros,
            "fecha_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fuente": "data_manager_auto_update"
        }
        
        result_path = "data/ultimo_resultado_oficial.json"
        try:
            with open(result_path, 'w') as f:
                json.dump(result_data, f, indent=2)
            logger.info(f"✅ Último resultado oficial actualizado: {result_path}")
        except Exception as e:
            logger.error(f"❌ Error actualizando último resultado: {e}")
    
    def get_data_info(self) -> Dict:
        """Obtiene información del dataset actual"""
        try:
            df = self.load_historical_data()
            
            info = {
                "total_records": int(len(df)),
                "date_range": {
                    "from": str(df['fecha'].min()) if 'fecha' in df.columns else "N/A",
                    "to": str(df['fecha'].max()) if 'fecha' in df.columns else "N/A"
                },
                "columns": list(df.columns),
                "last_sorteo": {},
                "data_quality": {
                    "complete_records": int(len(df)),
                    "missing_data": int(df.isnull().sum().sum())
                }
            }
            
            # Información del último sorteo
            if len(df) > 0 and 'fecha' in df.columns:
                last_row = df.iloc[-1]
                bolilla_cols = [f'bolilla_{i}' for i in range(1, 7)]
                available_cols = [col for col in bolilla_cols if col in df.columns]
                
                if available_cols:
                    info["last_sorteo"] = {
                        "fecha": str(last_row['fecha']),
                        "numeros": [int(last_row[col]) for col in available_cols]
                    }
            
            return info
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo información: {e}")
            return {"error": str(e)}

def test_data_manager():
    """Función de prueba para el DataManager"""
    logger.info("🧪 Iniciando prueba del DataManager...")
    
    dm = OmegaDataManager()
    
    # Obtener información
    info = dm.get_data_info()
    logger.info(f"📊 Información del dataset: {json.dumps(info, indent=2)}")
    
    # Probar carga de datos
    try:
        df = dm.load_historical_data()
        logger.info(f"✅ Datos cargados exitosamente: {len(df)} registros")
        logger.info(f"🏷️ Columnas: {list(df.columns)}")
        
        # Mostrar últimos 3 registros
        if len(df) >= 3:
            logger.info("📋 Últimos 3 registros:")
            for _, row in df.tail(3).iterrows():
                bolillas = []
                for i in range(1, 7):
                    col = f'bolilla_{i}'
                    if col in row:
                        bolillas.append(str(int(row[col])))
                
                fecha = row.get('fecha', 'N/A')
                logger.info(f"   {fecha}: {' - '.join(bolillas)}")
        
    except Exception as e:
        logger.error(f"❌ Error en prueba: {e}")

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Ejecutar prueba
    test_data_manager()