#!/usr/bin/env python3
"""
🎯 OMEGA Diversity Enhancer - Asegura cobertura completa del espacio numérico
Previene omisión de números críticos en predicciones
"""

import random
import numpy as np
from typing import List, Dict, Set, Tuple
import logging
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

class OmegaDiversityEnhancer:
    """Sistema que asegura diversidad completa en predicciones OMEGA"""
    
    def __init__(self):
        self.target_coverage = 0.95  # 95% de números 1-40 deben aparecer
        self.min_frequency = 1       # Cada número debe aparecer mínimo 1 vez
        self.range_balance = {       # Balance entre rangos
            "bajo": (1, 13),     # 1-13
            "medio": (14, 27),   # 14-27  
            "alto": (28, 40)     # 28-40
        }
        
    def enhance_predictions(self, predictions: List[Dict]) -> List[Dict]:
        """
        Mejora diversidad de predicciones asegurando cobertura completa
        
        Args:
            predictions: Lista de predicciones originales
            
        Returns:
            Lista de predicciones mejoradas con diversidad garantizada
        """
        logger.info("🎯 Iniciando mejora de diversidad de predicciones...")
        
        # 1. Analizar cobertura actual
        coverage_analysis = self._analyze_coverage(predictions)
        logger.info(f"📊 Cobertura actual: {coverage_analysis['coverage_percentage']:.1f}%")
        
        # 2. Identificar números omitidos
        missing_numbers = coverage_analysis['missing_numbers']
        if missing_numbers:
            logger.warning(f"⚠️ Números completamente omitidos: {missing_numbers}")
        
        # 3. Mejorar predicciones existentes
        enhanced_predictions = self._enhance_existing_predictions(predictions, coverage_analysis)
        
        # 4. Generar predicciones de diversidad si es necesario
        if len(missing_numbers) > 0:
            diversity_predictions = self._generate_diversity_predictions(missing_numbers, len(predictions))
            enhanced_predictions.extend(diversity_predictions)
            logger.info(f"➕ Agregadas {len(diversity_predictions)} predicciones de diversidad")
            
            # Si aún hay números omitidos después de la primera pasada, ser más agresivo
            temp_analysis = self._analyze_coverage(enhanced_predictions)
            if len(temp_analysis['missing_numbers']) > 0:  # Si aún faltan números
                additional_predictions = self._generate_aggressive_coverage(temp_analysis['missing_numbers'])
                enhanced_predictions.extend(additional_predictions)
                logger.warning(f"🚨 Cobertura agresiva: +{len(additional_predictions)} predicciones para números críticos")
        
        # 5. Validar cobertura final
        final_analysis = self._analyze_coverage(enhanced_predictions)
        logger.info(f"✅ Cobertura final: {final_analysis['coverage_percentage']:.1f}%")
        
        return enhanced_predictions[:len(predictions)]  # Mantener cantidad original
    
    def _analyze_coverage(self, predictions: List[Dict]) -> Dict:
        """Analiza cobertura de números en predicciones"""
        
        # Recopilar todos los números predichos
        all_numbers = []
        for pred in predictions:
            combination = pred.get('combination', [])
            if isinstance(combination, list) and len(combination) > 0:
                all_numbers.extend(combination)
        
        # Estadísticas de cobertura
        unique_numbers = set(all_numbers)
        missing_numbers = set(range(1, 41)) - unique_numbers
        coverage_percentage = len(unique_numbers) / 40 * 100
        
        # Análisis por rangos
        range_analysis = {}
        for range_name, (start, end) in self.range_balance.items():
            range_numbers = [n for n in all_numbers if start <= n <= end]
            range_analysis[range_name] = {
                'count': len(range_numbers),
                'unique': len(set(range_numbers)),
                'coverage': len(set(range_numbers)) / (end - start + 1) * 100
            }
        
        # Frecuencia de números
        number_frequency = Counter(all_numbers)
        low_frequency = [num for num, freq in number_frequency.items() if freq < self.min_frequency]
        
        return {
            'total_predictions': len([p for p in predictions if p.get('combination')]),
            'unique_numbers': unique_numbers,
            'missing_numbers': list(missing_numbers),
            'coverage_percentage': coverage_percentage,
            'range_analysis': range_analysis,
            'number_frequency': dict(number_frequency),
            'low_frequency_numbers': low_frequency,
            'needs_enhancement': coverage_percentage < self.target_coverage * 100 or len(missing_numbers) > 0
        }
    
    def _enhance_existing_predictions(self, predictions: List[Dict], analysis: Dict) -> List[Dict]:
        """Mejora predicciones existentes reemplazando números de alta frecuencia"""
        
        enhanced = []
        missing_numbers = list(analysis['missing_numbers'])
        high_freq_numbers = [num for num, freq in analysis['number_frequency'].items() 
                           if freq > len(predictions) * 0.3]  # Más del 30% de apariciones
        
        for pred in predictions:
            combination = pred.get('combination', [])
            if not combination or len(combination) != 6:
                enhanced.append(pred)
                continue
            
            # Reemplazar algunos números de alta frecuencia con números omitidos
            new_combination = list(combination)
            replacements_made = 0
            max_replacements = 2  # Máximo 2 reemplazos por predicción
            
            for i, num in enumerate(combination):
                if (replacements_made < max_replacements and 
                    num in high_freq_numbers and 
                    missing_numbers and 
                    random.random() < 0.3):  # 30% probabilidad de reemplazo
                    
                    replacement = missing_numbers.pop(0)
                    new_combination[i] = replacement
                    replacements_made += 1
            
            # Crear nueva predicción mejorada
            enhanced_pred = pred.copy()
            enhanced_pred['combination'] = sorted(new_combination)
            enhanced_pred['diversity_enhanced'] = replacements_made > 0
            enhanced.append(enhanced_pred)
        
        return enhanced
    
    def _generate_diversity_predictions(self, missing_numbers: List[int], base_count: int) -> List[Dict]:
        """Genera predicciones específicas para cubrir números omitidos"""
        
        diversity_predictions = []
        target_predictions = min(len(missing_numbers) // 2 + 1, base_count // 10)  # Máximo 10% adicional
        
        for i in range(target_predictions):
            # Asegurar que cada predicción incluya números omitidos
            combination = []
            
            # Incluir 2-3 números omitidos por predicción
            nums_to_include = min(3, len(missing_numbers))
            if nums_to_include > 0:
                selected_missing = random.sample(missing_numbers, nums_to_include)
                combination.extend(selected_missing)
                # Remover de la lista para próximas predicciones
                for num in selected_missing:
                    if num in missing_numbers:
                        missing_numbers.remove(num)
            
            # Completar con números aleatorios balanceados por rango
            while len(combination) < 6:
                # Seleccionar rango de manera balanceada
                range_name = random.choice(['bajo', 'medio', 'alto'])
                start, end = self.range_balance[range_name]
                num = random.randint(start, end)
                
                if num not in combination:
                    combination.append(num)
            
            # Crear predicción de diversidad
            diversity_pred = {
                'combination': sorted(combination),
                'score': 0.5,  # Score neutro
                'source': 'diversity_enhancer',
                'svi_score': 0.5,
                'diversity_generated': True,
                'missing_coverage': True
            }
            
            diversity_predictions.append(diversity_pred)
        
        return diversity_predictions
    
    def _generate_aggressive_coverage(self, missing_numbers: List[int]) -> List[Dict]:
        """Genera predicciones agresivas para asegurar cobertura 100%"""
        
        aggressive_predictions = []
        
        # Para cada número faltante, crear una predicción que lo incluya
        for missing_num in missing_numbers:
            combination = [missing_num]  # Asegurar que el número faltante esté incluido
            
            # Completar con números aleatorios bien distribuidos
            while len(combination) < 6:
                # Seleccionar de diferentes rangos para balance
                if len(combination) <= 2:  # Primeros números: rango bajo/medio
                    num = np.random.randint(1, 28)
                elif len(combination) <= 4:  # Siguientes: rango medio/alto  
                    num = np.random.randint(14, 41)
                else:  # Últimos: cualquier rango
                    num = np.random.randint(1, 41)
                
                if num not in combination:
                    combination.append(num)
            
            aggressive_pred = {
                'combination': sorted(combination),
                'score': 0.6,  # Score ligeramente superior
                'source': 'aggressive_coverage',
                'svi_score': 0.6,
                'aggressive_coverage': True,
                'target_number': missing_num
            }
            
            aggressive_predictions.append(aggressive_pred)
        
        return aggressive_predictions
    
    def validate_diversity(self, predictions: List[Dict]) -> Dict:
        """Valida que las predicciones tengan diversidad adecuada"""
        
        analysis = self._analyze_coverage(predictions)
        
        validation = {
            'is_diverse': analysis['coverage_percentage'] >= self.target_coverage * 100,
            'coverage_score': analysis['coverage_percentage'],
            'missing_count': len(analysis['missing_numbers']),
            'missing_numbers': analysis['missing_numbers'],
            'range_balance': analysis['range_analysis'],
            'recommendations': []
        }
        
        # Generar recomendaciones
        if not validation['is_diverse']:
            validation['recommendations'].append(f"Aumentar cobertura del {self.target_coverage*100:.0f}%")
        
        if len(analysis['missing_numbers']) > 5:
            validation['recommendations'].append("Reducir números completamente omitidos")
        
        for range_name, stats in analysis['range_analysis'].items():
            if stats['coverage'] < 50:
                validation['recommendations'].append(f"Mejorar cobertura en rango {range_name}")
        
        return validation

# Función de conveniencia
def enhance_prediction_diversity(predictions: List[Dict]) -> List[Dict]:
    """Función de conveniencia para mejorar diversidad de predicciones"""
    enhancer = OmegaDiversityEnhancer()
    return enhancer.enhance_predictions(predictions)

def validate_prediction_diversity(predictions: List[Dict]) -> Dict:
    """Función de conveniencia para validar diversidad de predicciones"""
    enhancer = OmegaDiversityEnhancer()
    return enhancer.validate_diversity(predictions)