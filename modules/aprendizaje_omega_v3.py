#!/usr/bin/env python3
"""
Aprendizaje OMEGA v3.0 - Motor Adaptativo Avanzado de OMEGA PRO AI
Versión expandida con criterios de refuerzo avanzados, análisis de patrones profundos,
y aprendizaje multi-dimensional para máxima adaptabilidad.
"""

import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any, Tuple, Optional, Set, Union
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field, asdict
from enum import Enum
import math
import warnings
warnings.filterwarnings("ignore")

# Importar módulos mejorados si están disponibles
try:
    from modules.utils.validation_enhanced import OmegaValidator, ValidationError
    from modules.utils.error_handling import handle_omega_errors, safe_execute, DataValidationError
    ENHANCED_MODULES_AVAILABLE = True
except ImportError:
    ENHANCED_MODULES_AVAILABLE = False

logger = logging.getLogger(__name__)

class PatternType(Enum):
    """Tipos de patrones para análisis avanzado"""
    BASIC_STATISTICS = "basic_statistics"
    SEQUENTIAL_PATTERNS = "sequential_patterns"
    FREQUENCY_PATTERNS = "frequency_patterns"
    SPATIAL_PATTERNS = "spatial_patterns"
    TEMPORAL_PATTERNS = "temporal_patterns"
    COMBINATORIAL_PATTERNS = "combinatorial_patterns"
    BEHAVIORAL_PATTERNS = "behavioral_patterns"

class ReinforcementAction(Enum):
    """Acciones de refuerzo disponibles"""
    STRENGTHEN = "strengthen"
    WEAKEN = "weaken"
    MAINTAIN = "maintain"
    EXPLORE = "explore"
    EXPLOIT = "exploit"

@dataclass
class AdvancedPattern:
    """Patrón avanzado con metadata completa"""
    pattern_id: str
    pattern_type: PatternType
    pattern_data: Dict[str, Any]
    frequency: int = 0
    success_rate: float = 0.0
    avg_hits: float = 0.0
    confidence: float = 0.0
    stability: float = 1.0
    last_seen: Optional[datetime] = None
    creation_date: datetime = field(default_factory=datetime.now)
    
    # Métricas avanzadas
    consistency_score: float = 0.0
    predictive_power: float = 0.0
    contextual_relevance: float = 0.0
    temporal_stability: float = 1.0
    
    # Historial de performance
    performance_history: List[Tuple[datetime, int]] = field(default_factory=list)
    reinforcement_history: List[Tuple[datetime, ReinforcementAction]] = field(default_factory=list)

@dataclass
class LearningContext:
    """Contexto de aprendizaje para decisiones adaptativas"""
    timestamp: datetime
    regime: str  # A, B, C
    profile: str  # conservador, moderado, agresivo
    system_performance: Dict[str, float]
    recent_accuracy: float
    confidence_level: float
    data_quality: float
    prediction_diversity: float

class AdvancedPatternExtractor:
    """Extractor de patrones avanzados con análisis multi-dimensional"""
    
    def __init__(self):
        self.pattern_cache = {}
        self.temporal_window = 50  # Para análisis temporal
        
    def extract_comprehensive_patterns(self, 
                                     combination: List[int],
                                     context: Optional[LearningContext] = None) -> Dict[PatternType, AdvancedPattern]:
        """Extrae patrones comprehensivos de una combinación"""
        patterns = {}
        
        try:
            # Validar combinación si es posible
            if ENHANCED_MODULES_AVAILABLE:
                combination = OmegaValidator.validate_combination(combination)
            
            # 1. Patrones estadísticos básicos
            patterns[PatternType.BASIC_STATISTICS] = self._extract_basic_statistical_patterns(combination)
            
            # 2. Patrones secuenciales
            patterns[PatternType.SEQUENTIAL_PATTERNS] = self._extract_sequential_patterns(combination)
            
            # 3. Patrones de frecuencia
            patterns[PatternType.FREQUENCY_PATTERNS] = self._extract_frequency_patterns(combination)
            
            # 4. Patrones espaciales
            patterns[PatternType.SPATIAL_PATTERNS] = self._extract_spatial_patterns(combination)
            
            # 5. Patrones temporales (si hay contexto)
            if context:
                patterns[PatternType.TEMPORAL_PATTERNS] = self._extract_temporal_patterns(combination, context)
            
            # 6. Patrones combinatoriales
            patterns[PatternType.COMBINATORIAL_PATTERNS] = self._extract_combinatorial_patterns(combination)
            
            # 7. Patrones comportamentales
            patterns[PatternType.BEHAVIORAL_PATTERNS] = self._extract_behavioral_patterns(combination, context)
            
            return patterns
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo patrones: {e}")
            return {}
    
    def _extract_basic_statistical_patterns(self, combination: List[int]) -> AdvancedPattern:
        """Extrae patrones estadísticos básicos mejorados"""
        sorted_combo = sorted(combination)
        
        pattern_data = {
            # Estadísticas básicas
            'sum': sum(combination),
            'mean': np.mean(combination),
            'std': np.std(combination),
            'median': np.median(combination),
            'range': max(combination) - min(combination),
            
            # Distribución por décadas mejorada
            'decade_0': sum(1 for x in combination if 1 <= x <= 10),
            'decade_1': sum(1 for x in combination if 11 <= x <= 20),
            'decade_2': sum(1 for x in combination if 21 <= x <= 30),
            'decade_3': sum(1 for x in combination if 31 <= x <= 40),
            
            # Análisis de paridad avanzado
            'even_count': sum(1 for x in combination if x % 2 == 0),
            'odd_count': sum(1 for x in combination if x % 2 == 1),
            'even_odd_ratio': sum(1 for x in combination if x % 2 == 0) / 6.0,
            
            # Análisis de primos
            'prime_count': self._count_primes(combination),
            'composite_count': 6 - self._count_primes(combination),
            
            # Distribución por quintiles
            'q1_count': sum(1 for x in combination if 1 <= x <= 8),
            'q2_count': sum(1 for x in combination if 9 <= x <= 16),
            'q3_count': sum(1 for x in combination if 17 <= x <= 24),
            'q4_count': sum(1 for x in combination if 25 <= x <= 32),
            'q5_count': sum(1 for x in combination if 33 <= x <= 40),
            
            # Análisis de balance
            'low_high_balance': self._calculate_balance(combination),
            'decade_entropy': self._calculate_decade_entropy(combination),
            'distribution_uniformity': self._calculate_uniformity(combination)
        }
        
        pattern_id = f"basic_stats_{hash(str(sorted(pattern_data.items())))}"
        
        return AdvancedPattern(
            pattern_id=pattern_id,
            pattern_type=PatternType.BASIC_STATISTICS,
            pattern_data=pattern_data
        )
    
    def _extract_sequential_patterns(self, combination: List[int]) -> AdvancedPattern:
        """Extrae patrones secuenciales avanzados"""
        sorted_combo = sorted(combination)
        
        pattern_data = {
            # Saltos básicos
            'gaps': [sorted_combo[i] - sorted_combo[i-1] for i in range(1, len(sorted_combo))],
            'total_gaps': sum(sorted_combo[i] - sorted_combo[i-1] for i in range(1, len(sorted_combo))),
            'avg_gap': np.mean([sorted_combo[i] - sorted_combo[i-1] for i in range(1, len(sorted_combo))]),
            'gap_variance': np.var([sorted_combo[i] - sorted_combo[i-1] for i in range(1, len(sorted_combo))]),
            
            # Consecutivos avanzados
            'consecutive_pairs': self._count_consecutive_pairs(sorted_combo),
            'consecutive_triplets': self._count_consecutive_triplets(sorted_combo),
            'max_consecutive_run': self._max_consecutive_run(sorted_combo),
            
            # Patrones de incremento
            'increasing_sequences': self._find_increasing_sequences(sorted_combo),
            'arithmetic_progressions': self._find_arithmetic_progressions(sorted_combo),
            
            # Simetrías
            'symmetry_score': self._calculate_symmetry(sorted_combo),
            'mirror_patterns': self._find_mirror_patterns(sorted_combo),
            
            # Clusters espaciales
            'cluster_count': self._count_spatial_clusters(sorted_combo),
            'max_cluster_size': self._max_cluster_size(sorted_combo),
            'cluster_density': self._calculate_cluster_density(sorted_combo)
        }
        
        pattern_id = f"sequential_{hash(str(sorted(pattern_data.items())))}"
        
        return AdvancedPattern(
            pattern_id=pattern_id,
            pattern_type=PatternType.SEQUENTIAL_PATTERNS,
            pattern_data=pattern_data
        )
    
    def _extract_frequency_patterns(self, combination: List[int]) -> AdvancedPattern:
        """Extrae patrones basados en frecuencia histórica simulada"""
        # Simular frecuencias históricas (en implementación real, usar datos reales)
        historical_freq = {i: np.random.uniform(0.8, 1.2) for i in range(1, 41)}
        
        pattern_data = {
            # Análisis de frecuencia
            'hot_numbers': sum(1 for x in combination if historical_freq.get(x, 1.0) > 1.1),
            'cold_numbers': sum(1 for x in combination if historical_freq.get(x, 1.0) < 0.9),
            'avg_frequency': np.mean([historical_freq.get(x, 1.0) for x in combination]),
            'frequency_variance': np.var([historical_freq.get(x, 1.0) for x in combination]),
            
            # Distribución de frecuencias
            'frequency_balance': self._calculate_frequency_balance(combination, historical_freq),
            'overdue_numbers': self._count_overdue_numbers(combination),
            'recent_numbers': self._count_recent_numbers(combination),
            
            # Patrones cíclicos simulados
            'cycle_position': self._estimate_cycle_position(combination),
            'cycle_compliance': self._evaluate_cycle_compliance(combination)
        }
        
        pattern_id = f"frequency_{hash(str(sorted(pattern_data.items())))}"
        
        return AdvancedPattern(
            pattern_id=pattern_id,
            pattern_type=PatternType.FREQUENCY_PATTERNS,
            pattern_data=pattern_data
        )
    
    def _extract_spatial_patterns(self, combination: List[int]) -> AdvancedPattern:
        """Extrae patrones espaciales en el campo numérico"""
        pattern_data = {
            # Distribución espacial
            'left_side': sum(1 for x in combination if x <= 20),  # 1-20
            'right_side': sum(1 for x in combination if x > 20),   # 21-40
            'center_weight': sum(1 for x in combination if 15 <= x <= 25),
            
            # Distribución vertical (si imaginamos una cuadrícula 8x5)
            'top_half': sum(1 for x in combination if x <= 20),
            'bottom_half': sum(1 for x in combination if x > 20),
            
            # Esquinas y bordes (simulado)
            'corner_numbers': sum(1 for x in combination if x in [1, 8, 33, 40]),
            'edge_numbers': sum(1 for x in combination if x <= 8 or x >= 33),
            'center_numbers': sum(1 for x in combination if 16 <= x <= 25),
            
            # Distribución diagonal
            'main_diagonal': self._count_diagonal_numbers(combination, 'main'),
            'anti_diagonal': self._count_diagonal_numbers(combination, 'anti'),
            
            # Simetría espacial
            'horizontal_symmetry': self._calculate_horizontal_symmetry(combination),
            'vertical_symmetry': self._calculate_vertical_symmetry(combination),
            
            # Densidad por cuadrantes
            'q1_density': sum(1 for x in combination if 1 <= x <= 10),
            'q2_density': sum(1 for x in combination if 11 <= x <= 20),
            'q3_density': sum(1 for x in combination if 21 <= x <= 30),
            'q4_density': sum(1 for x in combination if 31 <= x <= 40)
        }
        
        pattern_id = f"spatial_{hash(str(sorted(pattern_data.items())))}"
        
        return AdvancedPattern(
            pattern_id=pattern_id,
            pattern_type=PatternType.SPATIAL_PATTERNS,
            pattern_data=pattern_data
        )
    
    def _extract_temporal_patterns(self, combination: List[int], context: LearningContext) -> AdvancedPattern:
        """Extrae patrones temporales basados en contexto"""
        pattern_data = {
            # Contexto temporal
            'hour_of_day': context.timestamp.hour,
            'day_of_week': context.timestamp.weekday(),
            'day_of_month': context.timestamp.day,
            'month': context.timestamp.month,
            
            # Patrones estacionales simulados
            'seasonal_factor': self._calculate_seasonal_factor(context.timestamp),
            'weekly_cycle': self._calculate_weekly_cycle(context.timestamp),
            'monthly_cycle': self._calculate_monthly_cycle(context.timestamp),
            
            # Correlación con performance del sistema
            'system_performance_correlation': context.system_performance.get('overall', 0.5),
            'confidence_weighted_pattern': self._weight_by_confidence(combination, context.confidence_level),
            
            # Adaptación al régimen
            'regime_compliance': self._evaluate_regime_compliance(combination, context.regime),
            'profile_alignment': self._evaluate_profile_alignment(combination, context.profile)
        }
        
        pattern_id = f"temporal_{hash(str(sorted(pattern_data.items())))}"
        
        return AdvancedPattern(
            pattern_id=pattern_id,
            pattern_type=PatternType.TEMPORAL_PATTERNS,
            pattern_data=pattern_data
        )
    
    def _extract_combinatorial_patterns(self, combination: List[int]) -> AdvancedPattern:
        """Extrae patrones combinatoriales avanzados"""
        pattern_data = {
            # Análisis combinatorial
            'sum_modulo_patterns': {
                'mod_7': sum(combination) % 7,
                'mod_9': sum(combination) % 9,
                'mod_11': sum(combination) % 11
            },
            
            # Patrones de diferencias
            'difference_patterns': self._analyze_difference_patterns(combination),
            'cross_sums': self._calculate_cross_sums(combination),
            'digital_roots': [self._digital_root(x) for x in combination],
            
            # Análisis de factores
            'factor_analysis': self._analyze_prime_factors(combination),
            'gcd_patterns': self._analyze_gcd_patterns(combination),
            'lcm_patterns': self._analyze_lcm_patterns(combination),
            
            # Patrones matemáticos
            'fibonacci_compliance': self._check_fibonacci_compliance(combination),
            'perfect_squares': sum(1 for x in combination if int(x**0.5)**2 == x),
            'triangular_numbers': sum(1 for x in combination if self._is_triangular(x)),
            
            # Sumas parciales
            'partial_sums': self._calculate_partial_sums(combination),
            'cumulative_products': self._calculate_cumulative_products(combination)
        }
        
        pattern_id = f"combinatorial_{hash(str(sorted(str(pattern_data).encode())))}"
        
        return AdvancedPattern(
            pattern_id=pattern_id,
            pattern_type=PatternType.COMBINATORIAL_PATTERNS,
            pattern_data=pattern_data
        )
    
    def _extract_behavioral_patterns(self, combination: List[int], context: Optional[LearningContext]) -> AdvancedPattern:
        """Extrae patrones comportamentales del sistema"""
        pattern_data = {
            # Comportamiento de selección
            'selection_diversity': len(set(combination)) / 6.0,
            'risk_profile': self._calculate_risk_profile(combination),
            'exploration_factor': self._calculate_exploration_factor(combination),
            
            # Adaptabilidad
            'adaptation_score': self._calculate_adaptation_score(combination, context),
            'innovation_index': self._calculate_innovation_index(combination),
            'consistency_index': self._calculate_consistency_index(combination),
            
            # Respuesta al contexto
            'context_sensitivity': 0.5,  # Por defecto
            'performance_correlation': 0.5,  # Por defecto
            'learning_velocity': 0.5  # Por defecto
        }
        
        if context:
            pattern_data.update({
                'context_sensitivity': self._calculate_context_sensitivity(combination, context),
                'performance_correlation': context.recent_accuracy,
                'learning_velocity': self._calculate_learning_velocity(context)
            })
        
        pattern_id = f"behavioral_{hash(str(sorted(pattern_data.items())))}"
        
        return AdvancedPattern(
            pattern_id=pattern_id,
            pattern_type=PatternType.BEHAVIORAL_PATTERNS,
            pattern_data=pattern_data
        )
    
    # Métodos auxiliares para cálculos específicos
    def _count_primes(self, numbers: List[int]) -> int:
        """Cuenta números primos en la lista"""
        primes = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37}
        return sum(1 for x in numbers if x in primes)
    
    def _calculate_balance(self, combination: List[int]) -> float:
        """Calcula balance entre números bajos y altos"""
        low = sum(1 for x in combination if x <= 20)
        high = sum(1 for x in combination if x > 20)
        return abs(low - high) / 6.0
    
    def _calculate_decade_entropy(self, combination: List[int]) -> float:
        """Calcula entropía de distribución por décadas"""
        decades = [sum(1 for x in combination if i*10 < x <= (i+1)*10) for i in range(4)]
        total = sum(decades)
        if total == 0:
            return 0.0
        
        entropy = 0.0
        for count in decades:
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        
        return entropy / 2.0  # Normalizar a 0-1
    
    def _calculate_uniformity(self, combination: List[int]) -> float:
        """Calcula uniformidad de distribución"""
        hist = np.histogram(combination, bins=8, range=(1, 40))[0]
        expected = len(combination) / 8
        variance = np.var(hist)
        return max(0.0, 1.0 - variance / (expected**2 + 1e-6))
    
    def _count_consecutive_pairs(self, sorted_combo: List[int]) -> int:
        """Cuenta pares consecutivos"""
        count = 0
        for i in range(len(sorted_combo) - 1):
            if sorted_combo[i+1] - sorted_combo[i] == 1:
                count += 1
        return count
    
    def _count_consecutive_triplets(self, sorted_combo: List[int]) -> int:
        """Cuenta triplets consecutivos"""
        count = 0
        for i in range(len(sorted_combo) - 2):
            if (sorted_combo[i+1] - sorted_combo[i] == 1 and 
                sorted_combo[i+2] - sorted_combo[i+1] == 1):
                count += 1
        return count
    
    def _max_consecutive_run(self, sorted_combo: List[int]) -> int:
        """Encuentra la secuencia consecutiva más larga"""
        if not sorted_combo:
            return 0
        
        max_run = 1
        current_run = 1
        
        for i in range(1, len(sorted_combo)):
            if sorted_combo[i] - sorted_combo[i-1] == 1:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 1
        
        return max_run
    
    def _find_increasing_sequences(self, sorted_combo: List[int]) -> int:
        """Encuentra secuencias crecientes (no necesariamente consecutivas)"""
        # Ya está ordenado, por lo que toda la lista es una secuencia creciente
        return len(sorted_combo)
    
    def _find_arithmetic_progressions(self, sorted_combo: List[int]) -> int:
        """Encuentra progresiones aritméticas"""
        count = 0
        for i in range(len(sorted_combo) - 2):
            for j in range(i + 1, len(sorted_combo) - 1):
                for k in range(j + 1, len(sorted_combo)):
                    if sorted_combo[j] - sorted_combo[i] == sorted_combo[k] - sorted_combo[j]:
                        count += 1
        return count
    
    def _calculate_symmetry(self, sorted_combo: List[int]) -> float:
        """Calcula score de simetría"""
        center = 20.5  # Centro del rango 1-40
        deviations = [abs(x - center) for x in sorted_combo]
        return 1.0 - (np.std(deviations) / 20.0)  # Normalizar
    
    def _find_mirror_patterns(self, sorted_combo: List[int]) -> int:
        """Encuentra patrones espejo"""
        mirrors = 0
        for x in sorted_combo:
            mirror = 41 - x  # Número espejo
            if mirror in sorted_combo:
                mirrors += 1
        return mirrors // 2  # Cada par se cuenta una vez
    
    def _count_spatial_clusters(self, sorted_combo: List[int], threshold: int = 5) -> int:
        """Cuenta clusters espaciales"""
        if not sorted_combo:
            return 0
        
        clusters = 1
        for i in range(1, len(sorted_combo)):
            if sorted_combo[i] - sorted_combo[i-1] > threshold:
                clusters += 1
        
        return clusters
    
    def _max_cluster_size(self, sorted_combo: List[int], threshold: int = 5) -> int:
        """Encuentra el cluster más grande"""
        if not sorted_combo:
            return 0
        
        max_size = 1
        current_size = 1
        
        for i in range(1, len(sorted_combo)):
            if sorted_combo[i] - sorted_combo[i-1] <= threshold:
                current_size += 1
                max_size = max(max_size, current_size)
            else:
                current_size = 1
        
        return max_size
    
    def _calculate_cluster_density(self, sorted_combo: List[int]) -> float:
        """Calcula densidad de clusters"""
        if len(sorted_combo) < 2:
            return 1.0
        
        total_range = sorted_combo[-1] - sorted_combo[0] + 1
        return len(sorted_combo) / total_range
    
    # Métodos adicionales para otros tipos de patrones
    def _calculate_frequency_balance(self, combination: List[int], freq_dict: Dict[int, float]) -> float:
        """Calcula balance de frecuencias"""
        frequencies = [freq_dict.get(x, 1.0) for x in combination]
        return 1.0 - (np.std(frequencies) / np.mean(frequencies))
    
    def _count_overdue_numbers(self, combination: List[int]) -> int:
        """Cuenta números "vencidos" (simulado)"""
        # Simulación - en implementación real usar datos históricos
        overdue_threshold = np.random.uniform(0.8, 1.0)
        return sum(1 for x in combination if np.random.random() < overdue_threshold)
    
    def _count_recent_numbers(self, combination: List[int]) -> int:
        """Cuenta números recientes (simulado)"""
        # Simulación - en implementación real usar datos históricos
        recent_threshold = np.random.uniform(0.2, 0.4)
        return sum(1 for x in combination if np.random.random() < recent_threshold)
    
    def _estimate_cycle_position(self, combination: List[int]) -> float:
        """Estima posición en ciclo (simulado)"""
        return sum(combination) % 100 / 100.0
    
    def _evaluate_cycle_compliance(self, combination: List[int]) -> float:
        """Evalúa cumplimiento de ciclos (simulado)"""
        return np.random.uniform(0.3, 0.7)  # Simulado
    
    # Métodos para patrones espaciales
    def _count_diagonal_numbers(self, combination: List[int], diagonal_type: str) -> int:
        """Cuenta números en diagonales (simulado para cuadrícula 8x5)"""
        # Simulación de diagonal principal o anti-diagonal
        if diagonal_type == 'main':
            diagonal_nums = [1, 10, 19, 28, 37]  # Ejemplo
        else:
            diagonal_nums = [8, 15, 22, 29, 36]  # Ejemplo
        
        return sum(1 for x in combination if x in diagonal_nums)
    
    def _calculate_horizontal_symmetry(self, combination: List[int]) -> float:
        """Calcula simetría horizontal"""
        left = sum(1 for x in combination if x <= 20)
        right = sum(1 for x in combination if x > 20)
        return 1.0 - abs(left - right) / 6.0
    
    def _calculate_vertical_symmetry(self, combination: List[int]) -> float:
        """Calcula simetría vertical (simulado)"""
        # Simulación basada en disposición vertical imaginaria
        top = sum(1 for x in combination if x % 8 <= 4)
        bottom = sum(1 for x in combination if x % 8 > 4)
        return 1.0 - abs(top - bottom) / 6.0
    
    # Métodos para patrones temporales
    def _calculate_seasonal_factor(self, timestamp: datetime) -> float:
        """Calcula factor estacional"""
        day_of_year = timestamp.timetuple().tm_yday
        return 0.5 + 0.3 * math.sin(2 * math.pi * day_of_year / 365.25)
    
    def _calculate_weekly_cycle(self, timestamp: datetime) -> float:
        """Calcula posición en ciclo semanal"""
        return timestamp.weekday() / 7.0
    
    def _calculate_monthly_cycle(self, timestamp: datetime) -> float:
        """Calcula posición en ciclo mensual"""
        return timestamp.day / 31.0
    
    def _weight_by_confidence(self, combination: List[int], confidence: float) -> float:
        """Pondera patrón por nivel de confianza"""
        base_score = sum(combination) / 6.0 / 40.0  # Normalizado
        return base_score * confidence
    
    def _evaluate_regime_compliance(self, combination: List[int], regime: str) -> float:
        """Evalúa cumplimiento con régimen de datos"""
        if regime == 'A':
            # Régimen A: favorece distribución equilibrada
            return self._calculate_balance(combination)
        elif regime == 'B':
            # Régimen B: favorece números medios
            mid_numbers = sum(1 for x in combination if 15 <= x <= 25)
            return mid_numbers / 6.0
        else:  # Régimen C
            # Régimen C: favorece extremos
            extreme_numbers = sum(1 for x in combination if x <= 10 or x >= 30)
            return extreme_numbers / 6.0
    
    def _evaluate_profile_alignment(self, combination: List[int], profile: str) -> float:
        """Evalúa alineación con perfil de riesgo"""
        if profile == 'conservador':
            # Conservador: evita extremos
            safe_numbers = sum(1 for x in combination if 10 <= x <= 30)
            return safe_numbers / 6.0
        elif profile == 'agresivo':
            # Agresivo: busca patrones únicos
            uniqueness = len(set(combination)) / 40.0 * 6  # Factor de unicidad
            return min(1.0, uniqueness)
        else:  # moderado
            # Moderado: balance general
            return 0.5 + np.random.uniform(-0.2, 0.2)
    
    # Métodos para patrones combinatoriales
    def _analyze_difference_patterns(self, combination: List[int]) -> Dict[str, Any]:
        """Analiza patrones de diferencias"""
        sorted_combo = sorted(combination)
        diffs = [sorted_combo[i] - sorted_combo[i-1] for i in range(1, len(sorted_combo))]
        
        return {
            'min_diff': min(diffs),
            'max_diff': max(diffs),
            'avg_diff': np.mean(diffs),
            'diff_variance': np.var(diffs),
            'unique_diffs': len(set(diffs))
        }
    
    def _calculate_cross_sums(self, combination: List[int]) -> Dict[str, int]:
        """Calcula sumas cruzadas"""
        return {
            'first_half_sum': sum(combination[:3]),
            'second_half_sum': sum(combination[3:]),
            'odd_position_sum': sum(combination[i] for i in range(0, len(combination), 2)),
            'even_position_sum': sum(combination[i] for i in range(1, len(combination), 2))
        }
    
    def _digital_root(self, n: int) -> int:
        """Calcula raíz digital de un número"""
        while n >= 10:
            n = sum(int(digit) for digit in str(n))
        return n
    
    def _analyze_prime_factors(self, combination: List[int]) -> Dict[str, Any]:
        """Analiza factores primos"""
        all_factors = []
        for num in combination:
            factors = self._prime_factors(num)
            all_factors.extend(factors)
        
        return {
            'unique_factors': len(set(all_factors)),
            'most_common_factor': Counter(all_factors).most_common(1)[0][0] if all_factors else 1,
            'total_factors': len(all_factors)
        }
    
    def _prime_factors(self, n: int) -> List[int]:
        """Encuentra factores primos de un número"""
        factors = []
        d = 2
        while d * d <= n:
            while n % d == 0:
                factors.append(d)
                n //= d
            d += 1
        if n > 1:
            factors.append(n)
        return factors
    
    def _analyze_gcd_patterns(self, combination: List[int]) -> Dict[str, int]:
        """Analiza patrones de GCD"""
        import math
        
        gcds = []
        for i in range(len(combination)):
            for j in range(i + 1, len(combination)):
                gcds.append(math.gcd(combination[i], combination[j]))
        
        return {
            'max_gcd': max(gcds) if gcds else 1,
            'avg_gcd': int(np.mean(gcds)) if gcds else 1,
            'gcd_diversity': len(set(gcds)) if gcds else 1
        }
    
    def _analyze_lcm_patterns(self, combination: List[int]) -> Dict[str, Any]:
        """Analiza patrones de LCM"""
        import math
        
        def lcm(a, b):
            return abs(a * b) // math.gcd(a, b)
        
        lcms = []
        for i in range(len(combination)):
            for j in range(i + 1, len(combination)):
                lcms.append(lcm(combination[i], combination[j]))
        
        return {
            'min_lcm': min(lcms) if lcms else 1,
            'max_lcm': max(lcms) if lcms else 1,
            'avg_lcm': int(np.mean(lcms)) if lcms else 1
        }
    
    def _check_fibonacci_compliance(self, combination: List[int]) -> float:
        """Verifica cumplimiento con secuencia de Fibonacci"""
        fib_nums = {1, 2, 3, 5, 8, 13, 21, 34}  # Hasta 40
        fib_count = sum(1 for x in combination if x in fib_nums)
        return fib_count / 6.0
    
    def _is_triangular(self, n: int) -> bool:
        """Verifica si un número es triangular"""
        # Un número triangular satisface: n = k*(k+1)/2
        k = int((-1 + (1 + 8*n)**0.5) / 2)
        return k * (k + 1) // 2 == n
    
    def _calculate_partial_sums(self, combination: List[int]) -> List[int]:
        """Calcula sumas parciales"""
        partial_sums = []
        cumsum = 0
        for num in combination:
            cumsum += num
            partial_sums.append(cumsum)
        return partial_sums
    
    def _calculate_cumulative_products(self, combination: List[int]) -> List[int]:
        """Calcula productos acumulativos (limitados para evitar overflow)"""
        products = []
        cumprod = 1
        for num in combination:
            cumprod *= num
            if cumprod > 1e9:  # Limitar para evitar overflow
                cumprod = cumprod % 1000000
            products.append(cumprod)
        return products
    
    # Métodos para patrones comportamentales
    def _calculate_risk_profile(self, combination: List[int]) -> float:
        """Calcula perfil de riesgo de la combinación"""
        # Riesgo basado en dispersión y extremos
        variance = np.var(combination)
        extreme_count = sum(1 for x in combination if x <= 5 or x >= 35)
        return (variance / 200.0) + (extreme_count / 6.0)  # Normalizado aproximadamente
    
    def _calculate_exploration_factor(self, combination: List[int]) -> float:
        """Calcula factor de exploración"""
        # Exploración basada en unicidad y distribución
        unique_decades = len(set(x // 10 for x in combination))
        return unique_decades / 4.0  # 4 décadas máximo
    
    def _calculate_adaptation_score(self, combination: List[int], context: Optional[LearningContext]) -> float:
        """Calcula score de adaptación"""
        if not context:
            return 0.5
        
        # Adaptación basada en performance del sistema y contexto
        base_adaptability = 0.5
        
        # Bonus por alta confianza del sistema
        confidence_bonus = context.confidence_level * 0.2
        
        # Bonus por alta calidad de datos
        data_quality_bonus = context.data_quality * 0.2
        
        # Penalty por baja diversidad
        diversity_penalty = (1.0 - context.prediction_diversity) * 0.1
        
        return base_adaptability + confidence_bonus + data_quality_bonus - diversity_penalty
    
    def _calculate_innovation_index(self, combination: List[int]) -> float:
        """Calcula índice de innovación"""
        # Innovación basada en patrones únicos
        sorted_combo = sorted(combination)
        
        # Factores de innovación
        gap_uniqueness = len(set(sorted_combo[i] - sorted_combo[i-1] for i in range(1, len(sorted_combo)))) / 5.0
        sum_uniqueness = 1.0 - abs(sum(combination) - 123) / 123.0  # 123 es suma promedio
        
        return (gap_uniqueness + sum_uniqueness) / 2.0
    
    def _calculate_consistency_index(self, combination: List[int]) -> float:
        """Calcula índice de consistencia"""
        # Consistencia basada en distribución equilibrada
        decade_distribution = [sum(1 for x in combination if i*10 < x <= (i+1)*10) for i in range(4)]
        ideal_distribution = [1.5, 1.5, 1.5, 1.5]  # Distribución ideal
        
        deviation = sum(abs(actual - ideal) for actual, ideal in zip(decade_distribution, ideal_distribution))
        return max(0.0, 1.0 - deviation / 6.0)
    
    def _calculate_context_sensitivity(self, combination: List[int], context: LearningContext) -> float:
        """Calcula sensibilidad al contexto"""
        # Sensibilidad basada en adaptación a régimen y perfil
        regime_score = self._evaluate_regime_compliance(combination, context.regime)
        profile_score = self._evaluate_profile_alignment(combination, context.profile)
        
        return (regime_score + profile_score) / 2.0
    
    def _calculate_learning_velocity(self, context: LearningContext) -> float:
        """Calcula velocidad de aprendizaje del sistema"""
        # Velocidad basada en mejora reciente de accuracy
        base_velocity = 0.5
        
        # Bonus por alta accuracy reciente
        accuracy_bonus = context.recent_accuracy * 0.3
        
        # Bonus por alta calidad de datos
        data_bonus = context.data_quality * 0.2
        
        return min(1.0, base_velocity + accuracy_bonus + data_bonus)

class AdvancedLearningEngine:
    """Motor de aprendizaje avanzado con criterios de refuerzo expandidos"""
    
    def __init__(self):
        self.pattern_extractor = AdvancedPatternExtractor()
        self.pattern_database = defaultdict(lambda: defaultdict(list))  # {pattern_type: {pattern_id: [AdvancedPattern]}}
        self.reinforcement_history = deque(maxlen=1000)
        self.model_weights = defaultdict(float)
        self.learning_config = {
            'min_hits_for_reinforcement': 3,
            'reinforcement_strength': 0.1,
            'penalty_strength': 0.05,
            'temporal_decay_factor': 0.95,
            'confidence_threshold': 0.7,
            'stability_requirement': 0.8
        }
        
        logger.info("🧠 Advanced Learning Engine inicializado")
    
    @handle_omega_errors(
        context="Procesamiento de sorteo en Advanced Learning Engine",
        fallback_return={}
    )
    def process_sorteo_result(self,
                            predicted_combinations: List[List[int]],
                            winning_combination: List[int],
                            context: Optional[LearningContext] = None) -> Dict[str, Any]:
        """
        Procesa resultado de sorteo con aprendizaje avanzado
        """
        logger.info("🎯 Procesando resultado de sorteo con aprendizaje avanzado...")
        
        try:
            # Validar entradas
            if ENHANCED_MODULES_AVAILABLE:
                winning_combination = OmegaValidator.validate_combination(winning_combination)
                validated_predictions = []
                for combo in predicted_combinations:
                    try:
                        validated = OmegaValidator.validate_combination(combo)
                        validated_predictions.append(validated)
                    except ValidationError:
                        continue
                predicted_combinations = validated_predictions
            
            learning_results = {
                'timestamp': datetime.now(),
                'winning_combination': winning_combination,
                'total_predictions': len(predicted_combinations),
                'patterns_analyzed': 0,
                'patterns_reinforced': 0,
                'patterns_penalized': 0,
                'model_adjustments': {},
                'performance_metrics': {},
                'learning_insights': []
            }
            
            # Analizar cada combinación predicha
            for i, combo in enumerate(predicted_combinations):
                hits = self._calculate_hits(combo, winning_combination)
                
                # Extraer patrones comprehensivos
                patterns = self.pattern_extractor.extract_comprehensive_patterns(combo, context)
                learning_results['patterns_analyzed'] += len(patterns)
                
                # Procesar cada tipo de patrón
                for pattern_type, pattern in patterns.items():
                    self._process_pattern(pattern, hits, combo, context, learning_results)
            
            # Extraer y reforzar patrones del resultado ganador
            winning_patterns = self.pattern_extractor.extract_comprehensive_patterns(winning_combination, context)
            
            for pattern_type, pattern in winning_patterns.items():
                # Refuerzo fuerte para patrones ganadores
                self._reinforce_winning_pattern(pattern, learning_results)
            
            # Ajustar pesos de modelos basado en performance
            self._adjust_model_weights(predicted_combinations, winning_combination, learning_results)
            
            # Calcular métricas de performance del aprendizaje
            learning_results['performance_metrics'] = self._calculate_learning_performance(
                predicted_combinations, winning_combination, context
            )
            
            # Generar insights de aprendizaje
            learning_results['learning_insights'] = self._generate_learning_insights(learning_results, context)
            
            # Guardar en historial
            self.reinforcement_history.append(learning_results)
            
            logger.info(f"✅ Aprendizaje completado:")
            logger.info(f"   Patrones analizados: {learning_results['patterns_analyzed']}")
            logger.info(f"   Patrones reforzados: {learning_results['patterns_reinforced']}")
            logger.info(f"   Patrones penalizados: {learning_results['patterns_penalized']}")
            
            return learning_results
            
        except Exception as e:
            logger.error(f"❌ Error en procesamiento de aprendizaje: {e}")
            return {'error': str(e), 'timestamp': datetime.now()}
    
    def _calculate_hits(self, prediction: List[int], winning: List[int]) -> int:
        """Calcula aciertos entre predicción y resultado"""
        return len(set(prediction) & set(winning))
    
    def _process_pattern(self,
                        pattern: AdvancedPattern,
                        hits: int,
                        combination: List[int],
                        context: Optional[LearningContext],
                        learning_results: Dict[str, Any]):
        """Procesa un patrón individual con refuerzo/penalización"""
        
        # Actualizar métricas del patrón
        pattern.frequency += 1
        pattern.performance_history.append((datetime.now(), hits))
        pattern.last_seen = datetime.now()
        
        # Calcular métricas avanzadas
        pattern.avg_hits = np.mean([h for _, h in pattern.performance_history])
        pattern.success_rate = sum(1 for _, h in pattern.performance_history if h >= self.learning_config['min_hits_for_reinforcement']) / len(pattern.performance_history)
        
        # Decidir acción de refuerzo
        action = self._decide_reinforcement_action(pattern, hits, context)
        
        # Aplicar refuerzo/penalización
        if action == ReinforcementAction.STRENGTHEN:
            self._apply_reinforcement(pattern, hits, learning_results)
            pattern.reinforcement_history.append((datetime.now(), action))
            learning_results['patterns_reinforced'] += 1
            
        elif action == ReinforcementAction.WEAKEN:
            self._apply_penalty(pattern, hits, learning_results)
            pattern.reinforcement_history.append((datetime.now(), action))
            learning_results['patterns_penalized'] += 1
            
        # Actualizar base de datos de patrones
        self.pattern_database[pattern.pattern_type][pattern.pattern_id].append(pattern)
    
    def _decide_reinforcement_action(self,
                                   pattern: AdvancedPattern,
                                   hits: int,
                                   context: Optional[LearningContext]) -> ReinforcementAction:
        """Decide qué acción de refuerzo aplicar usando criterios avanzados"""
        
        # Criterio básico: número de aciertos
        if hits >= self.learning_config['min_hits_for_reinforcement']:
            base_action = ReinforcementAction.STRENGTHEN
        elif hits == 0:
            base_action = ReinforcementAction.WEAKEN
        else:
            base_action = ReinforcementAction.MAINTAIN
        
        # Ajustes contextuales
        if context:
            # Modificar según confianza del sistema
            if context.confidence_level < self.learning_config['confidence_threshold']:
                if base_action == ReinforcementAction.STRENGTHEN:
                    base_action = ReinforcementAction.MAINTAIN  # Ser más conservador
            
            # Modificar según calidad de datos
            if context.data_quality < 0.7:
                if base_action == ReinforcementAction.WEAKEN:
                    base_action = ReinforcementAction.MAINTAIN  # Evitar penalizaciones agresivas
        
        # Ajustes por historial del patrón
        if len(pattern.performance_history) >= 5:
            recent_performance = np.mean([h for _, h in pattern.performance_history[-5:]])
            
            if recent_performance > pattern.avg_hits * 1.2:
                # Performance reciente excelente
                if base_action == ReinforcementAction.MAINTAIN:
                    base_action = ReinforcementAction.STRENGTHEN
            elif recent_performance < pattern.avg_hits * 0.8:
                # Performance reciente pobre
                if base_action == ReinforcementAction.MAINTAIN:
                    base_action = ReinforcementAction.WEAKEN
        
        # Ajustes por estabilidad del patrón
        if pattern.stability < self.learning_config['stability_requirement']:
            if base_action == ReinforcementAction.STRENGTHEN:
                base_action = ReinforcementAction.EXPLORE  # Explorar variaciones
        
        return base_action
    
    def _apply_reinforcement(self,
                           pattern: AdvancedPattern,
                           hits: int,
                           learning_results: Dict[str, Any]):
        """Aplica refuerzo positivo a un patrón"""
        
        # Calcular fuerza del refuerzo basada en aciertos y contexto
        base_strength = self.learning_config['reinforcement_strength']
        hit_multiplier = (hits / 6.0) ** 2  # Refuerzo cuadrático por aciertos
        stability_multiplier = pattern.stability
        
        reinforcement_strength = base_strength * hit_multiplier * stability_multiplier
        
        # Aplicar refuerzo según tipo de patrón
        self._update_pattern_strength(pattern, reinforcement_strength)
        
        # Registrar refuerzo en resultados
        if 'reinforcements' not in learning_results:
            learning_results['reinforcements'] = []
        
        learning_results['reinforcements'].append({
            'pattern_id': pattern.pattern_id,
            'pattern_type': pattern.pattern_type.value,
            'hits': hits,
            'strength': reinforcement_strength,
            'new_confidence': pattern.confidence
        })
        
        logger.debug(f"   ⬆️ Reforzado patrón {pattern.pattern_id[:8]}... (hits: {hits}, strength: {reinforcement_strength:.3f})")
    
    def _apply_penalty(self,
                      pattern: AdvancedPattern,
                      hits: int,
                      learning_results: Dict[str, Any]):
        """Aplica penalización a un patrón"""
        
        # Calcular fuerza de la penalización
        base_penalty = self.learning_config['penalty_strength']
        failure_multiplier = (6 - hits) / 6.0  # Penalización proporcional a fallos
        
        penalty_strength = base_penalty * failure_multiplier
        
        # Aplicar penalización más suave que refuerzo
        self._update_pattern_strength(pattern, -penalty_strength * 0.5)
        
        # Registrar penalización en resultados
        if 'penalties' not in learning_results:
            learning_results['penalties'] = []
        
        learning_results['penalties'].append({
            'pattern_id': pattern.pattern_id,
            'pattern_type': pattern.pattern_type.value,
            'hits': hits,
            'penalty': penalty_strength,
            'new_confidence': pattern.confidence
        })
        
        logger.debug(f"   ⬇️ Penalizado patrón {pattern.pattern_id[:8]}... (hits: {hits}, penalty: {penalty_strength:.3f})")
    
    def _update_pattern_strength(self, pattern: AdvancedPattern, strength_delta: float):
        """Actualiza la fuerza/confianza de un patrón"""
        
        # Actualizar confianza con límites
        pattern.confidence = max(0.0, min(1.0, pattern.confidence + strength_delta))
        
        # Actualizar poder predictivo
        if len(pattern.performance_history) > 0:
            recent_hits = [h for _, h in pattern.performance_history[-10:]]
            pattern.predictive_power = np.mean(recent_hits) / 6.0
        
        # Actualizar estabilidad basada en varianza de performance
        if len(pattern.performance_history) >= 5:
            recent_performance = [h for _, h in pattern.performance_history[-5:]]
            pattern.stability = max(0.1, 1.0 - np.var(recent_performance) / 6.0)
    
    def _reinforce_winning_pattern(self, pattern: AdvancedPattern, learning_results: Dict[str, Any]):
        """Refuerza fuertemente un patrón del resultado ganador"""
        
        # Refuerzo muy fuerte para patrones ganadores
        winning_reinforcement = self.learning_config['reinforcement_strength'] * 3.0
        
        # Actualizar patrón
        pattern.confidence = min(1.0, pattern.confidence + winning_reinforcement)
        pattern.success_rate = min(1.0, pattern.success_rate + 0.2)
        pattern.performance_history.append((datetime.now(), 6))  # 6 aciertos perfectos
        
        # Registrar refuerzo ganador
        if 'winning_reinforcements' not in learning_results:
            learning_results['winning_reinforcements'] = []
        
        learning_results['winning_reinforcements'].append({
            'pattern_id': pattern.pattern_id,
            'pattern_type': pattern.pattern_type.value,
            'reinforcement_strength': winning_reinforcement,
            'new_confidence': pattern.confidence
        })
        
        logger.debug(f"   🏆 Refuerzo ganador para patrón {pattern.pattern_id[:8]}... (strength: {winning_reinforcement:.3f})")
    
    def _adjust_model_weights(self,
                            predictions: List[List[int]],
                            winning: List[int],
                            learning_results: Dict[str, Any]):
        """Ajusta pesos de modelos basado en performance"""
        
        # Simular identificación de modelos (en implementación real, usar metadata)
        model_performance = {}
        
        for i, pred in enumerate(predictions):
            hits = self._calculate_hits(pred, winning)
            model_name = f"model_{i % 6}"  # Simular diferentes modelos
            
            if model_name not in model_performance:
                model_performance[model_name] = []
            model_performance[model_name].append(hits)
        
        # Ajustar pesos basado en performance promedio
        adjustments = {}
        
        for model_name, hits_list in model_performance.items():
            avg_hits = np.mean(hits_list)
            current_weight = self.model_weights.get(model_name, 1.0)
            
            # Ajuste proporcional a performance
            if avg_hits >= 3:
                weight_adjustment = 0.1 * (avg_hits / 6.0)
                new_weight = min(2.0, current_weight + weight_adjustment)
            elif avg_hits == 0:
                weight_adjustment = -0.05
                new_weight = max(0.5, current_weight + weight_adjustment)
            else:
                weight_adjustment = 0.0
                new_weight = current_weight
            
            self.model_weights[model_name] = new_weight
            adjustments[model_name] = {
                'old_weight': current_weight,
                'new_weight': new_weight,
                'adjustment': weight_adjustment,
                'avg_hits': avg_hits
            }
        
        learning_results['model_adjustments'] = adjustments
        
        logger.debug(f"   ⚖️ Ajustados pesos de {len(adjustments)} modelos")
    
    def _calculate_learning_performance(self,
                                      predictions: List[List[int]],
                                      winning: List[int],
                                      context: Optional[LearningContext]) -> Dict[str, float]:
        """Calcula métricas de performance del aprendizaje"""
        
        # Métricas básicas
        all_hits = [self._calculate_hits(pred, winning) for pred in predictions]
        
        metrics = {
            'avg_hits': np.mean(all_hits),
            'max_hits': max(all_hits) if all_hits else 0,
            'hit_variance': np.var(all_hits),
            'predictions_with_hits': sum(1 for hits in all_hits if hits > 0) / len(all_hits) if all_hits else 0
        }
        
        # Métricas avanzadas de aprendizaje
        if len(self.reinforcement_history) >= 2:
            recent_avg = np.mean([r.get('performance_metrics', {}).get('avg_hits', 0) for r in list(self.reinforcement_history)[-5:]])
            earlier_avg = np.mean([r.get('performance_metrics', {}).get('avg_hits', 0) for r in list(self.reinforcement_history)[-10:-5]]) if len(self.reinforcement_history) >= 10 else recent_avg
            
            metrics['learning_trend'] = (recent_avg - earlier_avg) / (earlier_avg + 1e-6)
            metrics['learning_acceleration'] = metrics['learning_trend'] / 5.0  # Normalizado por ventana
        else:
            metrics['learning_trend'] = 0.0
            metrics['learning_acceleration'] = 0.0
        
        # Métricas contextuales
        if context:
            metrics['context_alignment'] = (context.confidence_level + context.data_quality) / 2.0
            metrics['adaptive_performance'] = metrics['avg_hits'] * metrics['context_alignment']
        else:
            metrics['context_alignment'] = 0.5
            metrics['adaptive_performance'] = metrics['avg_hits'] * 0.5
        
        return metrics
    
    def _generate_learning_insights(self,
                                  learning_results: Dict[str, Any],
                                  context: Optional[LearningContext]) -> List[str]:
        """Genera insights de aprendizaje basados en resultados"""
        
        insights = []
        
        # Insights sobre patrones
        if learning_results['patterns_reinforced'] > learning_results['patterns_penalized']:
            insights.append(f"Tendencia positiva: {learning_results['patterns_reinforced']} patrones reforzados vs {learning_results['patterns_penalized']} penalizados")
        elif learning_results['patterns_penalized'] > learning_results['patterns_reinforced'] * 2:
            insights.append(f"Oportunidad de mejora: alta tasa de penalizaciones ({learning_results['patterns_penalized']})")
        
        # Insights sobre performance
        metrics = learning_results.get('performance_metrics', {})
        avg_hits = metrics.get('avg_hits', 0)
        
        if avg_hits >= 2.5:
            insights.append(f"Excelente performance: {avg_hits:.2f} aciertos promedio")
        elif avg_hits < 1.0:
            insights.append(f"Performance baja: {avg_hits:.2f} aciertos promedio - considerar ajustes")
        
        # Insights sobre aprendizaje
        learning_trend = metrics.get('learning_trend', 0)
        if learning_trend > 0.1:
            insights.append("Tendencia de aprendizaje positiva: el sistema está mejorando")
        elif learning_trend < -0.1:
            insights.append("Declive en aprendizaje: revisar estrategias de refuerzo")
        
        # Insights contextuales
        if context:
            if context.confidence_level < 0.6:
                insights.append("Baja confianza del sistema: considerar más datos o ajustar parámetros")
            
            if context.data_quality < 0.7:
                insights.append("Calidad de datos subóptima: validar fuentes de datos")
        
        # Insights sobre modelos
        model_adjustments = learning_results.get('model_adjustments', {})
        improved_models = [name for name, adj in model_adjustments.items() if adj['adjustment'] > 0]
        degraded_models = [name for name, adj in model_adjustments.items() if adj['adjustment'] < 0]
        
        if improved_models:
            insights.append(f"Modelos mejorados: {', '.join(improved_models)}")
        if degraded_models:
            insights.append(f"Modelos con declive: {', '.join(degraded_models)}")
        
        return insights
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Obtiene resumen del estado de aprendizaje"""
        
        # Estadísticas de patrones
        total_patterns = sum(len(patterns) for patterns in self.pattern_database.values())
        pattern_types_count = {pt.value: len(patterns) for pt, patterns in self.pattern_database.items()}
        
        # Estadísticas de aprendizaje reciente
        recent_history = list(self.reinforcement_history)[-10:]
        
        if recent_history:
            avg_reinforced = np.mean([r['patterns_reinforced'] for r in recent_history])
            avg_penalized = np.mean([r['patterns_penalized'] for r in recent_history])
            avg_performance = np.mean([r.get('performance_metrics', {}).get('avg_hits', 0) for r in recent_history])
        else:
            avg_reinforced = avg_penalized = avg_performance = 0.0
        
        # Top patrones por confianza
        all_patterns = []
        for pattern_type, pattern_dict in self.pattern_database.items():
            for pattern_id, pattern_list in pattern_dict.items():
                if pattern_list:
                    latest_pattern = pattern_list[-1]  # Más reciente
                    all_patterns.append(latest_pattern)
        
        top_patterns = sorted(all_patterns, key=lambda p: p.confidence, reverse=True)[:5]
        
        return {
            'total_patterns_learned': total_patterns,
            'pattern_types_distribution': pattern_types_count,
            'recent_reinforcements_avg': avg_reinforced,
            'recent_penalties_avg': avg_penalized,
            'recent_performance_avg': avg_performance,
            'top_confident_patterns': [
                {
                    'pattern_id': p.pattern_id[:12],
                    'type': p.pattern_type.value,
                    'confidence': p.confidence,
                    'success_rate': p.success_rate,
                    'frequency': p.frequency
                }
                for p in top_patterns
            ],
            'model_weights': dict(self.model_weights),
            'learning_cycles_completed': len(self.reinforcement_history),
            'last_learning_date': self.reinforcement_history[-1]['timestamp'].isoformat() if self.reinforcement_history else None
        }

# Funciones de utilidad para compatibilidad
def create_advanced_learning_engine() -> AdvancedLearningEngine:
    """Crea motor de aprendizaje avanzado"""
    return AdvancedLearningEngine()

def process_advanced_learning(predicted_combinations: List[List[int]],
                            winning_combination: List[int],
                            system_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Función de conveniencia para procesamiento de aprendizaje avanzado
    """
    engine = create_advanced_learning_engine()
    
    # Crear contexto de aprendizaje si se proporciona información del sistema
    context = None
    if system_context:
        context = LearningContext(
            timestamp=datetime.now(),
            regime=system_context.get('regime', 'A'),
            profile=system_context.get('profile', 'moderado'),
            system_performance=system_context.get('performance', {}),
            recent_accuracy=system_context.get('recent_accuracy', 0.5),
            confidence_level=system_context.get('confidence', 0.5),
            data_quality=system_context.get('data_quality', 0.8),
            prediction_diversity=system_context.get('diversity', 0.7)
        )
    
    return engine.process_sorteo_result(predicted_combinations, winning_combination, context)

# Instancia global para compatibilidad con el sistema existente
advanced_learning_engine = create_advanced_learning_engine()

def aprender_de_resultado_avanzado(predicted_combinations: List[List[int]],
                                 winning_combination: List[int],
                                 **kwargs) -> Dict[str, Any]:
    """Función de compatibilidad con la API existente"""
    return advanced_learning_engine.process_sorteo_result(
        predicted_combinations, 
        winning_combination,
        context=kwargs.get('context')
    )
