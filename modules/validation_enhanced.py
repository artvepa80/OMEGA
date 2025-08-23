#!/usr/bin/env python3
"""
Módulo de Validación Mejorado para OMEGA PRO AI
Implementa validaciones robustas basadas en el análisis técnico realizado
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional, Union
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Excepción personalizada para errores de validación"""
    pass

class OmegaValidator:
    """Clase principal para validaciones robustas de OMEGA PRO AI"""
    
    @staticmethod
    def validate_combination(combination: Any, 
                           min_length: int = 6, 
                           max_length: int = 6,
                           min_value: int = 1,
                           max_value: int = 40) -> List[int]:
        """
        Valida una combinación de números de lotería
        
        Args:
            combination: Combinación a validar
            min_length: Longitud mínima (default: 6)
            max_length: Longitud máxima (default: 6)
            min_value: Valor mínimo por número (default: 1)
            max_value: Valor máximo por número (default: 40)
            
        Returns:
            List[int]: Combinación validada y normalizada
            
        Raises:
            ValidationError: Si la combinación no es válida
        """
        # Verificar que no sea None
        if combination is None:
            raise ValidationError("La combinación no puede ser None")
        
        # Convertir a lista si es necesario
        if isinstance(combination, (np.ndarray, tuple)):
            combination = list(combination)
        elif not isinstance(combination, list):
            raise ValidationError(f"Tipo de combinación no válido: {type(combination)}. Esperado: list, np.ndarray o tuple")
        
        # Verificar longitud
        if len(combination) < min_length or len(combination) > max_length:
            raise ValidationError(f"Longitud de combinación inválida: {len(combination)}. Esperado: {min_length}-{max_length}")
        
        # Convertir y validar números
        validated_combo = []
        for i, num in enumerate(combination):
            try:
                # Convertir a int (maneja np.int64, float, etc.)
                if isinstance(num, (np.integer, np.floating)):
                    num = int(num)
                elif isinstance(num, float):
                    num = int(round(num))
                elif not isinstance(num, int):
                    num = int(num)
                
                # Verificar rango
                if num < min_value or num > max_value:
                    raise ValidationError(f"Número {num} en posición {i} fuera de rango [{min_value}, {max_value}]")
                
                validated_combo.append(num)
                
            except (ValueError, TypeError) as e:
                raise ValidationError(f"Error convirtiendo número en posición {i}: {num} -> {e}")
        
        # Verificar duplicados
        if len(set(validated_combo)) != len(validated_combo):
            duplicates = [x for x in set(validated_combo) if validated_combo.count(x) > 1]
            raise ValidationError(f"Números duplicados encontrados: {duplicates}")
        
        return validated_combo
    
    @staticmethod
    def validate_combinations_batch(combinations: List[Any],
                                  allow_failures: bool = True,
                                  max_failure_rate: float = 0.1) -> Tuple[List[List[int]], List[str]]:
        """
        Valida un lote de combinaciones
        
        Args:
            combinations: Lista de combinaciones a validar
            allow_failures: Si permitir fallas individuales
            max_failure_rate: Tasa máxima de fallas permitida (0.0-1.0)
            
        Returns:
            Tuple[List[List[int]], List[str]]: (combinaciones_válidas, errores)
        """
        if not combinations:
            raise ValidationError("Lista de combinaciones vacía")
        
        valid_combinations = []
        errors = []
        
        for i, combo in enumerate(combinations):
            try:
                validated = OmegaValidator.validate_combination(combo)
                valid_combinations.append(validated)
            except ValidationError as e:
                error_msg = f"Combinación {i}: {e}"
                errors.append(error_msg)
                
                if not allow_failures:
                    raise ValidationError(f"Validación falló en combinación {i}: {e}")
        
        # Verificar tasa de fallas
        failure_rate = len(errors) / len(combinations)
        if failure_rate > max_failure_rate:
            raise ValidationError(f"Tasa de fallas demasiado alta: {failure_rate:.2%} > {max_failure_rate:.2%}")
        
        return valid_combinations, errors
    
    @staticmethod
    def validate_historical_data(data: Union[pd.DataFrame, np.ndarray, List[List[int]]],
                                min_rows: int = 10,
                                required_columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Valida datos históricos de sorteos
        
        Args:
            data: Datos históricos
            min_rows: Número mínimo de filas requeridas
            required_columns: Columnas requeridas (opcional)
            
        Returns:
            pd.DataFrame: Datos validados y normalizados
        """
        if data is None:
            raise ValidationError("Datos históricos no pueden ser None")
        
        # Convertir a DataFrame si es necesario
        if isinstance(data, np.ndarray):
            if data.ndim != 2:
                raise ValidationError(f"Array debe ser 2D, recibido: {data.ndim}D")
            if data.shape[1] < 6:
                raise ValidationError(f"Array debe tener al menos 6 columnas, recibido: {data.shape[1]}")
            
            column_names = [f'n{i+1}' for i in range(data.shape[1])]
            data = pd.DataFrame(data, columns=column_names)
            
        elif isinstance(data, list):
            if not data:
                raise ValidationError("Lista de datos históricos vacía")
            
            # Validar cada fila
            for i, row in enumerate(data):
                if not isinstance(row, (list, tuple, np.ndarray)):
                    raise ValidationError(f"Fila {i} debe ser lista/tuple/array, recibido: {type(row)}")
                if len(row) < 6:
                    raise ValidationError(f"Fila {i} debe tener al menos 6 elementos, recibido: {len(row)}")
            
            data = pd.DataFrame(data)
            
        elif not isinstance(data, pd.DataFrame):
            raise ValidationError(f"Tipo de datos no soportado: {type(data)}")
        
        # Verificar DataFrame resultante
        if data.empty:
            raise ValidationError("DataFrame resultante está vacío")
        
        if len(data) < min_rows:
            raise ValidationError(f"Insuficientes filas de datos: {len(data)} < {min_rows}")
        
        # Verificar columnas requeridas
        if required_columns:
            missing_cols = set(required_columns) - set(data.columns)
            if missing_cols:
                raise ValidationError(f"Columnas faltantes: {missing_cols}")
        
        # Validar datos numéricos
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 6:
            raise ValidationError(f"Insuficientes columnas numéricas: {len(numeric_cols)} < 6")
        
        # Verificar valores válidos en las primeras 6 columnas numéricas
        main_cols = numeric_cols[:6]
        for col in main_cols:
            invalid_values = data[col][(data[col] < 1) | (data[col] > 40)]
            if not invalid_values.empty:
                raise ValidationError(f"Valores inválidos en columna {col}: {invalid_values.tolist()}")
        
        return data
    
    @staticmethod
    def validate_model_weights(weights: Dict[str, float],
                              expected_models: Optional[List[str]] = None,
                              normalize: bool = True) -> Dict[str, float]:
        """
        Valida pesos de modelos
        
        Args:
            weights: Diccionario de pesos por modelo
            expected_models: Modelos esperados (opcional)
            normalize: Si normalizar pesos a suma 1.0
            
        Returns:
            Dict[str, float]: Pesos validados
        """
        if not isinstance(weights, dict):
            raise ValidationError(f"Pesos deben ser diccionario, recibido: {type(weights)}")
        
        if not weights:
            raise ValidationError("Diccionario de pesos vacío")
        
        # Validar valores
        for model, weight in weights.items():
            if not isinstance(model, str):
                raise ValidationError(f"Nombre de modelo debe ser string: {model}")
            
            if not isinstance(weight, (int, float, np.number)):
                raise ValidationError(f"Peso debe ser numérico para modelo {model}: {weight}")
            
            weight = float(weight)
            if weight < 0:
                raise ValidationError(f"Peso negativo para modelo {model}: {weight}")
            
            weights[model] = weight
        
        # Verificar modelos esperados
        if expected_models:
            missing_models = set(expected_models) - set(weights.keys())
            if missing_models:
                logger.warning(f"Modelos faltantes en pesos: {missing_models}")
        
        # Normalizar si se solicita
        if normalize:
            total = sum(weights.values())
            if total == 0:
                raise ValidationError("Suma total de pesos es cero")
            
            weights = {model: weight/total for model, weight in weights.items()}
        
        return weights
    
    @staticmethod
    def validate_sorteo_result(resultado: List[int]) -> List[int]:
        """
        Valida resultado oficial de sorteo
        
        Args:
            resultado: Resultado del sorteo
            
        Returns:
            List[int]: Resultado validado
        """
        return OmegaValidator.validate_combination(
            resultado, 
            min_length=6, 
            max_length=6,
            min_value=1,
            max_value=40
        )
    
    @staticmethod
    def validate_metrics(metrics: Dict[str, Any],
                        required_metrics: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Valida métricas de rendimiento
        
        Args:
            metrics: Diccionario de métricas
            required_metrics: Métricas requeridas (opcional)
            
        Returns:
            Dict[str, float]: Métricas validadas
        """
        if not isinstance(metrics, dict):
            raise ValidationError(f"Métricas deben ser diccionario, recibido: {type(metrics)}")
        
        validated_metrics = {}
        
        for metric_name, value in metrics.items():
            if not isinstance(metric_name, str):
                raise ValidationError(f"Nombre de métrica debe ser string: {metric_name}")
            
            try:
                value = float(value)
                if np.isnan(value) or np.isinf(value):
                    raise ValidationError(f"Valor inválido para métrica {metric_name}: {value}")
                
                validated_metrics[metric_name] = value
                
            except (ValueError, TypeError):
                raise ValidationError(f"Error convirtiendo métrica {metric_name}: {value}")
        
        # Verificar métricas requeridas
        if required_metrics:
            missing_metrics = set(required_metrics) - set(validated_metrics.keys())
            if missing_metrics:
                raise ValidationError(f"Métricas faltantes: {missing_metrics}")
        
        return validated_metrics

# Funciones de conveniencia
def safe_validate_combination(combination: Any) -> Optional[List[int]]:
    """Versión segura que retorna None en lugar de excepción"""
    try:
        return OmegaValidator.validate_combination(combination)
    except ValidationError:
        return None

def validate_and_log_combinations(combinations: List[Any], 
                                 logger: logging.Logger) -> List[List[int]]:
    """Valida combinaciones y registra errores en log"""
    try:
        valid_combos, errors = OmegaValidator.validate_combinations_batch(combinations)
        
        if errors:
            logger.warning(f"Se encontraron {len(errors)} errores de validación:")
            for error in errors[:5]:  # Mostrar solo primeros 5
                logger.warning(f"  - {error}")
            if len(errors) > 5:
                logger.warning(f"  ... y {len(errors) - 5} errores más")
        
        logger.info(f"✅ Validadas {len(valid_combos)}/{len(combinations)} combinaciones")
        return valid_combos
        
    except ValidationError as e:
        logger.error(f"❌ Error crítico en validación: {e}")
        return []
