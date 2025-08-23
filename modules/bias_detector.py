#!/usr/bin/env python3
"""
🔍 OMEGA Bias Detector - Detecta y corrige sesgos sistemáticos en modelos ML
Previene omisión sistemática de números específicos
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Set, Tuple, Any
import logging
from collections import Counter, defaultdict
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class OmegaBiasDetector:
    """Sistema de detección y corrección de sesgos en modelos OMEGA"""
    
    def __init__(self):
        self.bias_thresholds = {
            'range_imbalance': 0.3,     # 30% max diferencia entre rangos
            'number_frequency': 0.15,   # 15% max diferencia en frecuencia
            'systematic_omission': 5,   # Max 5 números completamente omitidos
            'min_coverage': 0.80        # Min 80% cobertura del espacio numérico
        }
        
        self.number_ranges = {
            'bajo': (1, 13),      # 13 números
            'medio': (14, 27),    # 14 números  
            'alto': (28, 40)      # 13 números
        }
        
    def detect_biases(self, predictions: List[Dict]) -> Dict:
        """
        Detecta sesgos sistemáticos en predicciones
        
        Args:
            predictions: Lista de predicciones OMEGA
            
        Returns:
            Dict con análisis detallado de sesgos detectados
        """
        logger.info("🔍 Iniciando detección de sesgos sistemáticos...")
        
        # Extraer números de todas las predicciones
        all_numbers = self._extract_numbers(predictions)
        
        if not all_numbers:
            return {"error": "No se encontraron números en las predicciones"}
        
        # Análisis de sesgos
        bias_analysis = {
            'total_predictions': len(predictions),
            'total_numbers': len(all_numbers),
            'unique_numbers': len(set(all_numbers)),
            'coverage_percentage': len(set(all_numbers)) / 40 * 100,
            'biases_detected': []
        }
        
        # 1. Detectar sesgo de rango
        range_bias = self._detect_range_bias(all_numbers)
        if range_bias['has_bias']:
            bias_analysis['biases_detected'].append(range_bias)
        
        # 2. Detectar sesgo de frecuencia
        frequency_bias = self._detect_frequency_bias(all_numbers)
        if frequency_bias['has_bias']:
            bias_analysis['biases_detected'].append(frequency_bias)
        
        # 3. Detectar omisión sistemática
        omission_bias = self._detect_systematic_omission(all_numbers)
        if omission_bias['has_bias']:
            bias_analysis['biases_detected'].append(omission_bias)
        
        # 4. Detectar patrones de distribución
        distribution_bias = self._detect_distribution_bias(all_numbers)
        if distribution_bias['has_bias']:
            bias_analysis['biases_detected'].append(distribution_bias)
        
        # 5. Detectar sesgos por fuente de modelo
        model_bias = self._detect_model_source_bias(predictions)
        if model_bias['has_bias']:
            bias_analysis['biases_detected'].append(model_bias)
        
        # Calcular severidad general
        bias_analysis['bias_severity'] = self._calculate_bias_severity(bias_analysis['biases_detected'])
        bias_analysis['needs_correction'] = len(bias_analysis['biases_detected']) > 0
        
        logger.info(f"🔍 Sesgos detectados: {len(bias_analysis['biases_detected'])}")
        if bias_analysis['biases_detected']:
            for bias in bias_analysis['biases_detected']:
                logger.warning(f"⚠️ Sesgo {bias['type']}: {bias['description']}")
        
        return bias_analysis
    
    def correct_biases(self, predictions: List[Dict], bias_analysis: Dict) -> List[Dict]:
        """
        Corrige sesgos detectados en predicciones
        
        Args:
            predictions: Predicciones originales
            bias_analysis: Análisis de sesgos de detect_biases()
            
        Returns:
            Predicciones corregidas
        """
        if not bias_analysis.get('needs_correction', False):
            logger.info("✅ No se detectaron sesgos que requieran corrección")
            return predictions
        
        logger.info("🔧 Iniciando corrección de sesgos...")
        corrected_predictions = predictions.copy()
        
        for bias in bias_analysis['biases_detected']:
            bias_type = bias['type']
            
            try:
                if bias_type == 'range_imbalance':
                    corrected_predictions = self._correct_range_bias(corrected_predictions, bias)
                elif bias_type == 'frequency_imbalance':
                    corrected_predictions = self._correct_frequency_bias(corrected_predictions, bias)
                elif bias_type == 'systematic_omission':
                    corrected_predictions = self._correct_omission_bias(corrected_predictions, bias)
                elif bias_type == 'distribution_skew':
                    corrected_predictions = self._correct_distribution_bias(corrected_predictions, bias)
                elif bias_type == 'model_source_bias':
                    corrected_predictions = self._correct_model_bias(corrected_predictions, bias)
                    
                logger.info(f"✅ Sesgo {bias_type} corregido")
                
            except Exception as e:
                logger.error(f"🚨 Error corrigiendo sesgo {bias_type}: {e}")
        
        logger.info("🔧 Corrección de sesgos completada")
        return corrected_predictions
    
    def _extract_numbers(self, predictions: List[Dict]) -> List[int]:
        """Extrae todos los números de las predicciones"""
        numbers = []
        for pred in predictions:
            combination = pred.get('combination', [])
            if isinstance(combination, list):
                numbers.extend([n for n in combination if isinstance(n, int) and 1 <= n <= 40])
        return numbers
    
    def _detect_range_bias(self, all_numbers: List[int]) -> Dict:
        """Detecta sesgo hacia rangos específicos"""
        range_counts = {}
        total_numbers = len(all_numbers)
        
        for range_name, (start, end) in self.number_ranges.items():
            range_numbers = [n for n in all_numbers if start <= n <= end]
            range_counts[range_name] = {
                'count': len(range_numbers),
                'percentage': len(range_numbers) / total_numbers if total_numbers > 0 else 0,
                'expected_percentage': (end - start + 1) / 40  # Porcentaje esperado
            }
        
        # Calcular desviaciones
        max_deviation = 0
        worst_range = None
        
        for range_name, stats in range_counts.items():
            deviation = abs(stats['percentage'] - stats['expected_percentage'])
            if deviation > max_deviation:
                max_deviation = deviation
                worst_range = range_name
        
        has_bias = max_deviation > self.bias_thresholds['range_imbalance']
        
        return {
            'type': 'range_imbalance',
            'has_bias': has_bias,
            'severity': 'high' if max_deviation > 0.5 else 'medium' if max_deviation > 0.3 else 'low',
            'description': f"Desbalance en rango {worst_range}: {max_deviation:.1%} desviación",
            'range_stats': range_counts,
            'max_deviation': max_deviation,
            'affected_range': worst_range
        }
    
    def _detect_frequency_bias(self, all_numbers: List[int]) -> Dict:
        """Detecta sesgo en frecuencia de números específicos"""
        number_freq = Counter(all_numbers)
        frequencies = list(number_freq.values())
        
        if not frequencies:
            return {'type': 'frequency_imbalance', 'has_bias': False}
        
        expected_freq = len(all_numbers) / 40  # Frecuencia esperada
        
        # Calcular coeficiente de variación
        freq_std = np.std(frequencies)
        freq_mean = np.mean(frequencies)
        cv = freq_std / freq_mean if freq_mean > 0 else 0
        
        # Identificar números con frecuencia anómala
        over_represented = [(num, freq) for num, freq in number_freq.items() 
                          if freq > expected_freq * (1 + self.bias_thresholds['number_frequency'])]
        under_represented = [(num, freq) for num, freq in number_freq.items() 
                           if freq < expected_freq * (1 - self.bias_thresholds['number_frequency'])]
        
        has_bias = cv > self.bias_thresholds['number_frequency'] or len(over_represented) > 5 or len(under_represented) > 5
        
        return {
            'type': 'frequency_imbalance',
            'has_bias': has_bias,
            'severity': 'high' if cv > 0.3 else 'medium' if cv > 0.2 else 'low',
            'description': f"Desbalance de frecuencia: CV={cv:.2f}",
            'coefficient_variation': cv,
            'expected_frequency': expected_freq,
            'over_represented': over_represented[:10],  # Top 10
            'under_represented': under_represented[:10],
            'frequency_distribution': dict(number_freq)
        }
    
    def _detect_systematic_omission(self, all_numbers: List[int]) -> Dict:
        """Detecta números sistemáticamente omitidos"""
        present_numbers = set(all_numbers)
        all_possible = set(range(1, 41))
        omitted_numbers = list(all_possible - present_numbers)
        
        has_bias = len(omitted_numbers) > self.bias_thresholds['systematic_omission']
        coverage = len(present_numbers) / 40
        
        return {
            'type': 'systematic_omission',
            'has_bias': has_bias,
            'severity': 'high' if len(omitted_numbers) > 10 else 'medium' if len(omitted_numbers) > 5 else 'low',
            'description': f"{len(omitted_numbers)} números completamente omitidos",
            'omitted_numbers': sorted(omitted_numbers),
            'coverage_percentage': coverage * 100,
            'omitted_count': len(omitted_numbers)
        }
    
    def _detect_distribution_bias(self, all_numbers: List[int]) -> Dict:
        """Detecta sesgos en la distribución estadística"""
        if len(set(all_numbers)) < 10:  # Muy pocos números únicos para análisis
            return {'type': 'distribution_skew', 'has_bias': False}
        
        # Test de normalidad (debería ser aproximadamente uniforme)
        hist, _ = np.histogram(all_numbers, bins=20, range=(1, 40))
        
        # Calcular skewness y kurtosis
        try:
            skewness = stats.skew(all_numbers)
            kurtosis = stats.kurtosis(all_numbers)
            
            # Test de uniformidad (Chi-cuadrado)
            expected_uniform = len(all_numbers) / 40
            observed_freq = Counter(all_numbers)
            chi2_stat = sum((freq - expected_uniform) ** 2 / expected_uniform 
                          for freq in observed_freq.values())
            
            # Sesgos significativos
            has_skew_bias = abs(skewness) > 0.5
            has_kurtosis_bias = abs(kurtosis) > 1.0
            has_uniformity_bias = chi2_stat > 50  # Threshold arbitrario
            
            has_bias = has_skew_bias or has_kurtosis_bias or has_uniformity_bias
            
            return {
                'type': 'distribution_skew',
                'has_bias': has_bias,
                'severity': 'high' if abs(skewness) > 1.0 or abs(kurtosis) > 2.0 else 'medium',
                'description': f"Distribución sesgada: skew={skewness:.2f}, kurt={kurtosis:.2f}",
                'skewness': skewness,
                'kurtosis': kurtosis,
                'chi2_statistic': chi2_stat,
                'distribution_type': 'right_skewed' if skewness > 0.5 else 'left_skewed' if skewness < -0.5 else 'symmetric'
            }
            
        except Exception as e:
            logger.debug(f"Error en análisis de distribución: {e}")
            return {'type': 'distribution_skew', 'has_bias': False}
    
    def _detect_model_source_bias(self, predictions: List[Dict]) -> Dict:
        """Detecta sesgos por fuente de modelo"""
        source_numbers = defaultdict(list)
        
        for pred in predictions:
            source = pred.get('source', 'unknown')
            combination = pred.get('combination', [])
            if combination:
                source_numbers[source].extend(combination)
        
        if len(source_numbers) <= 1:
            return {'type': 'model_source_bias', 'has_bias': False}
        
        # Analizar diversidad por fuente
        source_analysis = {}
        for source, numbers in source_numbers.items():
            unique_numbers = len(set(numbers))
            coverage = unique_numbers / 40
            source_analysis[source] = {
                'total_numbers': len(numbers),
                'unique_numbers': unique_numbers,
                'coverage': coverage,
                'avg_numbers_per_pred': len(numbers) / len([p for p in predictions if p.get('source') == source])
            }
        
        # Detectar fuentes con baja diversidad
        low_diversity_sources = [source for source, stats in source_analysis.items() 
                               if stats['coverage'] < 0.5]
        
        has_bias = len(low_diversity_sources) > 0
        
        return {
            'type': 'model_source_bias',
            'has_bias': has_bias,
            'severity': 'medium' if len(low_diversity_sources) <= 2 else 'high',
            'description': f"{len(low_diversity_sources)} modelos con baja diversidad",
            'source_analysis': source_analysis,
            'low_diversity_sources': low_diversity_sources
        }
    
    def _calculate_bias_severity(self, biases: List[Dict]) -> str:
        """Calcula severidad general de sesgos"""
        if not biases:
            return 'none'
        
        high_severity = sum(1 for bias in biases if bias.get('severity') == 'high')
        medium_severity = sum(1 for bias in biases if bias.get('severity') == 'medium')
        
        if high_severity > 0:
            return 'high'
        elif medium_severity > 1:
            return 'high'
        elif medium_severity > 0:
            return 'medium'
        else:
            return 'low'
    
    def _correct_range_bias(self, predictions: List[Dict], bias_info: Dict) -> List[Dict]:
        """Corrige sesgo de rango rebalanceando predicciones"""
        affected_range = bias_info.get('affected_range')
        if not affected_range:
            return predictions
        
        # Reemplazar algunos números del rango sobrerepresentado
        corrected = []
        for pred in predictions:
            combination = pred.get('combination', [])
            if not combination:
                corrected.append(pred)
                continue
            
            new_combination = list(combination)
            range_start, range_end = self.number_ranges[affected_range]
            
            # Reemplazar hasta 2 números del rango problemático
            replacements = 0
            for i, num in enumerate(combination):
                if replacements < 2 and range_start <= num <= range_end and np.random.random() < 0.2:
                    # Seleccionar rango alternativo
                    alt_ranges = [r for r in self.number_ranges.keys() if r != affected_range]
                    alt_range = np.random.choice(alt_ranges)
                    alt_start, alt_end = self.number_ranges[alt_range]
                    
                    # Generar número de reemplazo
                    replacement = np.random.randint(alt_start, alt_end + 1)
                    if replacement not in new_combination:
                        new_combination[i] = replacement
                        replacements += 1
            
            corrected_pred = pred.copy()
            corrected_pred['combination'] = sorted(new_combination)
            corrected_pred['bias_corrected'] = replacements > 0
            corrected.append(corrected_pred)
        
        return corrected
    
    def _correct_frequency_bias(self, predictions: List[Dict], bias_info: Dict) -> List[Dict]:
        """Corrige sesgo de frecuencia diversificando números"""
        over_represented = [num for num, _ in bias_info.get('over_represented', [])]
        
        if not over_represented:
            return predictions
        
        corrected = []
        for pred in predictions:
            combination = pred.get('combination', [])
            if not combination:
                corrected.append(pred)
                continue
            
            new_combination = list(combination)
            
            # Reemplazar números sobrerepresentados con probabilidad
            for i, num in enumerate(combination):
                if num in over_represented and np.random.random() < 0.15:
                    # Generar número alternativo
                    available = list(set(range(1, 41)) - set(new_combination))
                    if available:
                        replacement = np.random.choice(available)
                        new_combination[i] = replacement
            
            corrected_pred = pred.copy()
            corrected_pred['combination'] = sorted(new_combination)
            corrected.append(corrected_pred)
        
        return corrected
    
    def _correct_omission_bias(self, predictions: List[Dict], bias_info: Dict) -> List[Dict]:
        """Corrige sesgo de omisión agregando números faltantes"""
        omitted_numbers = bias_info.get('omitted_numbers', [])
        
        if not omitted_numbers:
            return predictions
        
        # Agregar números omitidos a algunas predicciones existentes
        corrected = list(predictions)
        
        # Calcular cuántas predicciones modificar
        num_to_modify = min(len(omitted_numbers), len(predictions) // 5)  # Max 20%
        
        indices_to_modify = np.random.choice(len(predictions), num_to_modify, replace=False)
        
        for i, idx in enumerate(indices_to_modify):
            if i < len(omitted_numbers):
                pred = corrected[idx]
                combination = pred.get('combination', [])
                if combination and len(combination) > 0:
                    new_combination = list(combination)
                    # Reemplazar un número aleatorio con uno omitido
                    replace_idx = np.random.randint(len(new_combination))
                    new_combination[replace_idx] = omitted_numbers[i]
                    
                    corrected_pred = pred.copy()
                    corrected_pred['combination'] = sorted(new_combination)
                    corrected_pred['omission_corrected'] = True
                    corrected[idx] = corrected_pred
        
        return corrected
    
    def _correct_distribution_bias(self, predictions: List[Dict], bias_info: Dict) -> List[Dict]:
        """Corrige sesgo de distribución normalizando"""
        # Para sesgos de distribución, aplicamos randomización suave
        corrected = []
        
        for pred in predictions:
            combination = pred.get('combination', [])
            if not combination:
                corrected.append(pred)
                continue
            
            new_combination = list(combination)
            
            # Aplicar pequeña perturbación aleatoria (10% de las predicciones)
            if np.random.random() < 0.1:
                # Reemplazar un número con uno aleatorio bien distribuido
                replace_idx = np.random.randint(len(new_combination))
                replacement = np.random.randint(1, 41)
                
                attempts = 0
                while replacement in new_combination and attempts < 10:
                    replacement = np.random.randint(1, 41)
                    attempts += 1
                
                if replacement not in new_combination:
                    new_combination[replace_idx] = replacement
            
            corrected_pred = pred.copy()
            corrected_pred['combination'] = sorted(new_combination)
            corrected.append(corrected_pred)
        
        return corrected
    
    def _correct_model_bias(self, predictions: List[Dict], bias_info: Dict) -> List[Dict]:
        """Corrige sesgos específicos de modelos"""
        low_diversity_sources = bias_info.get('low_diversity_sources', [])
        
        if not low_diversity_sources:
            return predictions
        
        corrected = []
        
        for pred in predictions:
            source = pred.get('source', 'unknown')
            combination = pred.get('combination', [])
            
            if source in low_diversity_sources and combination:
                # Aplicar diversificación agresiva
                new_combination = list(combination)
                
                # Reemplazar hasta 3 números para aumentar diversidad
                replacements = min(3, len(combination))
                indices_to_replace = np.random.choice(len(combination), replacements, replace=False)
                
                for idx in indices_to_replace:
                    replacement = np.random.randint(1, 41)
                    attempts = 0
                    while replacement in new_combination and attempts < 10:
                        replacement = np.random.randint(1, 41)
                        attempts += 1
                    
                    if replacement not in new_combination:
                        new_combination[idx] = replacement
                
                corrected_pred = pred.copy()
                corrected_pred['combination'] = sorted(new_combination)
                corrected_pred['model_bias_corrected'] = True
                corrected.append(corrected_pred)
            else:
                corrected.append(pred)
        
        return corrected

# Funciones de conveniencia
def detect_prediction_biases(predictions: List[Dict]) -> Dict:
    """Función de conveniencia para detectar sesgos"""
    detector = OmegaBiasDetector()
    return detector.detect_biases(predictions)

def correct_prediction_biases(predictions: List[Dict], bias_analysis: Dict = None) -> List[Dict]:
    """Función de conveniencia para corregir sesgos"""
    detector = OmegaBiasDetector()
    
    if bias_analysis is None:
        bias_analysis = detector.detect_biases(predictions)
    
    return detector.correct_biases(predictions, bias_analysis)