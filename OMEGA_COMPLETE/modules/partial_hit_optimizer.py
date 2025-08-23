#!/usr/bin/env python3
"""
🎯 Partial Hit Optimizer - Especializado en obtener 4-5 números consistentemente
Estrategia: Maximizar aciertos parciales en lugar de buscar jackpots imposibles
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Set
from collections import Counter, defaultdict
import logging

logger = logging.getLogger(__name__)

class PartialHitOptimizer:
    """Optimizador especializado en hits parciales (3-5 números)"""
    
    def __init__(self, historical_data: pd.DataFrame):
        self.historical_data = historical_data
        self.bolilla_cols = [c for c in historical_data.columns if "bolilla" in c.lower()][:6]
        
        # Análisis de patrones parciales
        self.partial_patterns = self._analyze_partial_patterns()
        self.number_co_occurrence = self._analyze_co_occurrence()
        self.range_clusters = self._analyze_range_clusters()
        
        logger.info("🎯 Partial Hit Optimizer inicializado")
        logger.info(f"   Datos: {len(historical_data)} sorteos | Patrones: {len(self.partial_patterns)}")
    
    def _analyze_partial_patterns(self) -> Dict:
        """Analiza patrones de números que aparecen juntos frecuentemente"""
        patterns = defaultdict(int)
        
        for _, row in self.historical_data.iterrows():
            numeros = sorted([int(row[col]) for col in self.bolilla_cols])
            
            # Analizar todas las subcombinaciones de 3-5 números
            for size in [3, 4, 5]:
                from itertools import combinations
                for combo in combinations(numeros, size):
                    patterns[combo] += 1
        
        # Filtrar patrones más frecuentes
        threshold = len(self.historical_data) * 0.02  # Al menos 2% de aparición
        frequent_patterns = {k: v for k, v in patterns.items() if v >= threshold}
        
        logger.info(f"🔍 Patrones parciales frecuentes: {len(frequent_patterns)}")
        return frequent_patterns
    
    def _analyze_co_occurrence(self) -> Dict:
        """Analiza qué números tienden a salir juntos"""
        co_matrix = defaultdict(lambda: defaultdict(int))
        
        for _, row in self.historical_data.iterrows():
            numeros = [int(row[col]) for col in self.bolilla_cols]
            
            # Matriz de co-ocurrencia
            for i, num1 in enumerate(numeros):
                for j, num2 in enumerate(numeros):
                    if i != j:
                        co_matrix[num1][num2] += 1
        
        # Convertir a probabilidades
        total_sorteos = len(self.historical_data)
        for num1 in co_matrix:
            for num2 in co_matrix[num1]:
                co_matrix[num1][num2] /= total_sorteos
        
        return dict(co_matrix)
    
    def _analyze_range_clusters(self) -> Dict:
        """Analiza clusters de números por rangos"""
        ranges = {
            'bajo': list(range(1, 14)),     # 1-13
            'medio': list(range(14, 28)),   # 14-27  
            'alto': list(range(28, 41))     # 28-40
        }
        
        range_patterns = defaultdict(list)
        
        for _, row in self.historical_data.iterrows():
            numeros = [int(row[col]) for col in self.bolilla_cols]
            
            distribution = {'bajo': 0, 'medio': 0, 'alto': 0}
            for num in numeros:
                for range_name, range_nums in ranges.items():
                    if num in range_nums:
                        distribution[range_name] += 1
                        break
            
            pattern = f"{distribution['bajo']}-{distribution['medio']}-{distribution['alto']}"
            range_patterns[pattern].append(numeros)
        
        return dict(range_patterns)
    
    def optimize_combinations_for_partial_hits(self, combinations: List[List[int]]) -> List[Dict]:
        """Optimiza combinaciones para maximizar hits parciales"""
        
        optimized = []
        
        for combo in combinations:
            score = self._score_partial_potential(combo)
            coverage = self._calculate_coverage_score(combo, combinations)
            co_occurrence_score = self._calculate_co_occurrence_score(combo)
            
            total_score = (score * 0.4) + (coverage * 0.3) + (co_occurrence_score * 0.3)
            
            optimized.append({
                'combination': combo,
                'partial_hit_score': total_score,
                'pattern_score': score,
                'coverage_score': coverage,
                'co_occurrence_score': co_occurrence_score,
                'strategy': 'partial_hit_optimized'
            })
        
        # Ordenar por score de hits parciales
        optimized.sort(key=lambda x: x['partial_hit_score'], reverse=True)
        
        logger.info(f"🎯 Combinaciones optimizadas para hits parciales")
        logger.info(f"   Mejor score: {optimized[0]['partial_hit_score']:.3f}")
        
        return optimized
    
    def _score_partial_potential(self, combination: List[int]) -> float:
        """Score basado en patrones parciales históricos"""
        score = 0.0
        
        # Evaluar subcombinaciones de 3-5 números
        for size in [3, 4, 5]:
            from itertools import combinations
            for subcombo in combinations(sorted(combination), size):
                if subcombo in self.partial_patterns:
                    frequency = self.partial_patterns[subcombo]
                    # Bonus por tamaño (5 números vale más que 3)
                    size_bonus = size / 3.0
                    score += frequency * size_bonus
        
        return score
    
    def _calculate_coverage_score(self, combination: List[int], all_combinations: List[List[int]]) -> float:
        """Calcula qué tan bien esta combinación complementa las otras"""
        coverage = set(combination)
        
        # Penalizar números muy repetidos en el conjunto
        number_count = Counter()
        for combo in all_combinations:
            number_count.update(combo)
        
        over_representation_penalty = 0
        for num in combination:
            if number_count[num] > 3:  # Si aparece en más de 3 combinaciones
                over_representation_penalty += 0.1
        
        # Score de diversidad de rangos
        ranges = {'bajo': 0, 'medio': 0, 'alto': 0}
        for num in combination:
            if 1 <= num <= 13:
                ranges['bajo'] += 1
            elif 14 <= num <= 27:
                ranges['medio'] += 1
            else:
                ranges['alto'] += 1
        
        # Penalizar distribuciones muy desbalanceadas
        balance_score = 1.0 - abs(ranges['bajo'] - 2) * 0.1 - abs(ranges['medio'] - 2) * 0.1 - abs(ranges['alto'] - 2) * 0.1
        
        return balance_score - over_representation_penalty
    
    def _calculate_co_occurrence_score(self, combination: List[int]) -> float:
        """Score basado en co-ocurrencia histórica"""
        score = 0.0
        count = 0
        
        for i, num1 in enumerate(combination):
            for j, num2 in enumerate(combination):
                if i != j and num1 in self.number_co_occurrence:
                    score += self.number_co_occurrence[num1].get(num2, 0)
                    count += 1
        
        return score / count if count > 0 else 0
    
    def generate_partial_hit_report(self, combinations: List[List[int]]) -> Dict:
        """Genera reporte detallado de potencial de hits parciales"""
        
        report = {
            'coverage_analysis': self._analyze_number_coverage(combinations),
            'expected_hits': self._calculate_expected_partial_hits(combinations),
            'risk_analysis': self._analyze_risk_factors(combinations),
            'recommendations': []
        }
        
        # Recomendaciones basadas en análisis
        if report['coverage_analysis']['total_unique_numbers'] < 25:
            report['recommendations'].append("Aumentar diversidad numérica para mejor cobertura")
        
        if report['expected_hits']['avg_expected_4_numbers'] < 0.1:
            report['recommendations'].append("Optimizar patrones para mejorar chances de 4 números")
        
        return report
    
    def _analyze_number_coverage(self, combinations: List[List[int]]) -> Dict:
        """Analiza cobertura numérica del conjunto de combinaciones"""
        all_numbers = set()
        for combo in combinations:
            all_numbers.update(combo)
        
        ranges = {'bajo': 0, 'medio': 0, 'alto': 0}
        for num in all_numbers:
            if 1 <= num <= 13:
                ranges['bajo'] += 1
            elif 14 <= num <= 27:
                ranges['medio'] += 1
            else:
                ranges['alto'] += 1
        
        return {
            'total_unique_numbers': len(all_numbers),
            'coverage_percentage': len(all_numbers) / 40 * 100,
            'range_distribution': ranges,
            'missing_numbers': sorted(set(range(1, 41)) - all_numbers)
        }
    
    def _calculate_expected_partial_hits(self, combinations: List[List[int]]) -> Dict:
        """Calcula hits parciales esperados basado en patrones históricos"""
        expected = {'3_numbers': 0, '4_numbers': 0, '5_numbers': 0}
        
        for combo in combinations:
            for size in [3, 4, 5]:
                from itertools import combinations as iter_combinations
                for subcombo in iter_combinations(sorted(combo), size):
                    if subcombo in self.partial_patterns:
                        frequency = self.partial_patterns[subcombo]
                        probability = frequency / len(self.historical_data)
                        expected[f'{size}_numbers'] += probability
        
        return {
            'avg_expected_3_numbers': expected['3_numbers'] / len(combinations),
            'avg_expected_4_numbers': expected['4_numbers'] / len(combinations),  
            'avg_expected_5_numbers': expected['5_numbers'] / len(combinations)
        }
    
    def _analyze_risk_factors(self, combinations: List[List[int]]) -> Dict:
        """Analiza factores de riesgo en la estrategia"""
        return {
            'over_concentration': self._check_number_concentration(combinations),
            'pattern_dependency': self._check_pattern_dependency(combinations),
            'range_imbalance': self._check_range_imbalance(combinations)
        }
    
    def _check_number_concentration(self, combinations: List[List[int]]) -> float:
        """Verifica si hay números demasiado concentrados"""
        number_count = Counter()
        for combo in combinations:
            number_count.update(combo)
        
        max_appearances = max(number_count.values())
        return max_appearances / len(combinations)
    
    def _check_pattern_dependency(self, combinations: List[List[int]]) -> float:
        """Verifica dependencia excesiva de patrones específicos"""
        pattern_usage = defaultdict(int)
        
        for combo in combinations:
            for size in [3, 4, 5]:
                from itertools import combinations as iter_combinations
                for subcombo in iter_combinations(sorted(combo), size):
                    if subcombo in self.partial_patterns:
                        pattern_usage[subcombo] += 1
        
        if not pattern_usage:
            return 0.0
        
        max_usage = max(pattern_usage.values())
        return max_usage / len(combinations)
    
    def _check_range_imbalance(self, combinations: List[List[int]]) -> float:
        """Verifica desbalance en distribución de rangos"""
        total_by_range = {'bajo': 0, 'medio': 0, 'alto': 0}
        
        for combo in combinations:
            for num in combo:
                if 1 <= num <= 13:
                    total_by_range['bajo'] += 1
                elif 14 <= num <= 27:
                    total_by_range['medio'] += 1
                else:
                    total_by_range['alto'] += 1
        
        total_numbers = sum(total_by_range.values())
        expected_per_range = total_numbers / 3
        
        imbalance = 0
        for count in total_by_range.values():
            imbalance += abs(count - expected_per_range) / expected_per_range
        
        return imbalance / 3

def optimize_omega_for_partial_hits(historical_data: pd.DataFrame, combinations: List[List[int]]) -> Dict:
    """Función principal para optimizar OMEGA para hits parciales"""
    
    optimizer = PartialHitOptimizer(historical_data)
    optimized_combos = optimizer.optimize_combinations_for_partial_hits(combinations)
    report = optimizer.generate_partial_hit_report(combinations)
    
    return {
        'optimized_combinations': optimized_combos,
        'analysis_report': report,
        'strategy': 'partial_hit_optimization',
        'target': '4-5_numbers_consistently'
    }