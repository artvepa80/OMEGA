#!/usr/bin/env python3
"""
🎰 Jackpot Integrator - Integración de datos de jackpots históricos
Analiza patrones en los últimos jackpots y los integra con el sistema OMEGA
"""

import numpy as np
import pandas as pd
import ast
from typing import List, Dict, Tuple, Optional
from collections import Counter, defaultdict
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class JackpotIntegrator:
    """Integrador de datos de jackpots en el sistema OMEGA"""
    
    def __init__(self, jackpot_data_path: str, historical_data_path: str):
        self.jackpot_data = self._load_jackpot_data(jackpot_data_path)
        self.historical_data = pd.read_csv(historical_data_path)
        
        # Extraer combinaciones ganadoras
        self.winning_combinations = self._extract_winning_combinations()
        self.jackpot_patterns = {}
        self.integration_analysis = {}
        
        logger.info("🎰 Jackpot Integrator inicializado")
        logger.info(f"   Jackpots: {len(self.jackpot_data)} | Históricos: {len(self.historical_data)}")
    
    def _load_jackpot_data(self, data_path: str) -> pd.DataFrame:
        """Carga y procesa los datos de jackpots"""
        try:
            df = pd.read_csv(data_path)
            df['fecha'] = pd.to_datetime(df['fecha'])
            
            # Parsear las combinaciones numéricas
            df['numeros_parsed'] = df['numeros'].apply(self._parse_numbers)
            
            return df.sort_values('fecha', ascending=False)
        except Exception as e:
            logger.error(f"Error cargando jackpots: {e}")
            return pd.DataFrame()
    
    def _parse_numbers(self, numbers_str: str) -> List[int]:
        """Parsea string de números a lista"""
        try:
            # Manejar tanto formato "[1,2,3]" como "1,2,3"
            if numbers_str.startswith('[') and numbers_str.endswith(']'):
                return ast.literal_eval(numbers_str)
            else:
                return [int(x.strip()) for x in numbers_str.split(',')]
        except:
            logger.warning(f"No se pudo parsear: {numbers_str}")
            return []
    
    def _extract_winning_combinations(self) -> List[List[int]]:
        """Extrae las combinaciones ganadoras de jackpots"""
        combinations = []
        
        for _, row in self.jackpot_data.iterrows():
            combo = row['numeros_parsed']
            if combo and len(combo) == 6:
                combinations.append(sorted(combo))
        
        return combinations
    
    def analyze_jackpot_patterns(self) -> Dict:
        """Analiza patrones en los jackpots históricos"""
        
        if not self.winning_combinations:
            return {'error': 'No hay combinaciones de jackpot válidas'}
        
        results = {
            'frequency_analysis': self._analyze_number_frequency(),
            'positional_analysis': self._analyze_positional_patterns(),
            'range_analysis': self._analyze_range_distribution(),
            'temporal_analysis': self._analyze_temporal_patterns(),
            'gap_analysis': self._analyze_number_gaps(),
            'correlation_analysis': self._analyze_number_correlations(),
            'deviation_analysis': self._analyze_statistical_deviations()
        }
        
        self.jackpot_patterns = results
        logger.info("🔍 Análisis de patrones de jackpot completado")
        
        return results
    
    def _analyze_number_frequency(self) -> Dict:
        """Analiza frecuencia de números en jackpots"""
        all_numbers = []
        for combo in self.winning_combinations:
            all_numbers.extend(combo)
        
        frequency = Counter(all_numbers)
        total_appearances = len(all_numbers)
        
        # Estadísticas por número
        number_stats = {}
        for num in range(1, 41):
            count = frequency.get(num, 0)
            expected = total_appearances / 40  # Frecuencia esperada
            
            number_stats[num] = {
                'count': count,
                'frequency': count / len(self.winning_combinations) if self.winning_combinations else 0,
                'expected': expected,
                'deviation': count - expected,
                'relative_deviation': (count - expected) / expected if expected > 0 else 0
            }
        
        # Top números más/menos frecuentes
        sorted_by_freq = sorted(number_stats.items(), key=lambda x: x[1]['count'], reverse=True)
        
        return {
            'total_numbers_drawn': total_appearances,
            'unique_numbers_drawn': len(frequency),
            'number_statistics': number_stats,
            'most_frequent': sorted_by_freq[:10],
            'least_frequent': sorted_by_freq[-10:],
            'never_drawn': [num for num in range(1, 41) if frequency.get(num, 0) == 0]
        }
    
    def _analyze_positional_patterns(self) -> Dict:
        """Analiza patrones por posición en los jackpots"""
        
        position_stats = {}
        
        for pos in range(6):
            position_numbers = []
            for combo in self.winning_combinations:
                if len(combo) > pos:
                    position_numbers.append(combo[pos])
            
            if position_numbers:
                position_freq = Counter(position_numbers)
                
                position_stats[f'position_{pos+1}'] = {
                    'numbers': position_numbers,
                    'frequency': position_freq,
                    'most_common': position_freq.most_common(5),
                    'average': np.mean(position_numbers),
                    'std': np.std(position_numbers),
                    'min': min(position_numbers),
                    'max': max(position_numbers),
                    'range': max(position_numbers) - min(position_numbers)
                }
        
        # Analizar tendencias posicionales
        position_trends = {}
        for pos in range(6):
            pos_key = f'position_{pos+1}'
            if pos_key in position_stats:
                avg = position_stats[pos_key]['average']
                if avg <= 10:
                    position_trends[pos_key] = 'very_low'
                elif avg <= 20:
                    position_trends[pos_key] = 'low'
                elif avg <= 30:
                    position_trends[pos_key] = 'medium'
                else:
                    position_trends[pos_key] = 'high'
        
        return {
            'position_statistics': position_stats,
            'position_trends': position_trends
        }
    
    def _analyze_range_distribution(self) -> Dict:
        """Analiza distribución por rangos en jackpots"""
        
        range_analysis = {
            'bajo': {'range': (1, 13), 'counts': []},
            'medio': {'range': (14, 27), 'counts': []},
            'alto': {'range': (28, 40), 'counts': []}
        }
        
        for combo in self.winning_combinations:
            bajo_count = sum(1 for n in combo if 1 <= n <= 13)
            medio_count = sum(1 for n in combo if 14 <= n <= 27)
            alto_count = sum(1 for n in combo if 28 <= n <= 40)
            
            range_analysis['bajo']['counts'].append(bajo_count)
            range_analysis['medio']['counts'].append(medio_count)
            range_analysis['alto']['counts'].append(alto_count)
        
        # Estadísticas por rango
        for range_name, data in range_analysis.items():
            counts = data['counts']
            if counts:
                range_analysis[range_name].update({
                    'average': np.mean(counts),
                    'std': np.std(counts),
                    'most_common_count': Counter(counts).most_common(1)[0],
                    'distribution': Counter(counts)
                })
        
        # Patrones de balance más comunes
        balance_patterns = []
        for combo in self.winning_combinations:
            bajo = sum(1 for n in combo if 1 <= n <= 13)
            medio = sum(1 for n in combo if 14 <= n <= 27)
            alto = sum(1 for n in combo if 28 <= n <= 40)
            balance_patterns.append(f"{bajo}-{medio}-{alto}")
        
        balance_freq = Counter(balance_patterns)
        
        return {
            'range_statistics': range_analysis,
            'balance_patterns': balance_freq.most_common(),
            'most_common_balance': balance_freq.most_common(1)[0] if balance_freq else None
        }
    
    def _analyze_temporal_patterns(self) -> Dict:
        """Analiza patrones temporales en los jackpots"""
        
        if self.jackpot_data.empty or 'fecha' not in self.jackpot_data.columns:
            return {'error': 'No hay datos de fecha disponibles'}
        
        temporal_stats = {
            'by_year': {},
            'by_month': {},
            'by_day_of_week': {},
            'intervals_between_jackpots': []
        }
        
        # Análisis por año, mes, día de semana
        for _, row in self.jackpot_data.iterrows():
            fecha = row['fecha']
            combo = row['numeros_parsed']
            
            if not combo:
                continue
            
            year = fecha.year
            month = fecha.month
            day_of_week = fecha.weekday()
            
            if year not in temporal_stats['by_year']:
                temporal_stats['by_year'][year] = []
            temporal_stats['by_year'][year].append(combo)
            
            if month not in temporal_stats['by_month']:
                temporal_stats['by_month'][month] = []
            temporal_stats['by_month'][month].append(combo)
            
            if day_of_week not in temporal_stats['by_day_of_week']:
                temporal_stats['by_day_of_week'][day_of_week] = []
            temporal_stats['by_day_of_week'][day_of_week].append(combo)
        
        # Calcular intervalos entre jackpots
        fechas_sorted = sorted(self.jackpot_data['fecha'])
        for i in range(1, len(fechas_sorted)):
            interval = (fechas_sorted[i] - fechas_sorted[i-1]).days
            temporal_stats['intervals_between_jackpots'].append(interval)
        
        # Estadísticas de intervalos
        if temporal_stats['intervals_between_jackpots']:
            intervals = temporal_stats['intervals_between_jackpots']
            temporal_stats['interval_statistics'] = {
                'average_days': np.mean(intervals),
                'median_days': np.median(intervals),
                'min_days': min(intervals),
                'max_days': max(intervals),
                'std_days': np.std(intervals)
            }
        
        return temporal_stats
    
    def _analyze_number_gaps(self) -> Dict:
        """Analiza gaps entre números consecutivos en jackpots"""
        
        gap_analysis = {
            'consecutive_gaps': [],
            'gap_statistics': {},
            'gap_patterns': Counter()
        }
        
        for combo in self.winning_combinations:
            sorted_combo = sorted(combo)
            gaps = []
            
            for i in range(1, len(sorted_combo)):
                gap = sorted_combo[i] - sorted_combo[i-1]
                gaps.append(gap)
            
            gap_analysis['consecutive_gaps'].append(gaps)
            gap_analysis['gap_patterns'][tuple(gaps)] += 1
        
        # Estadísticas de gaps
        all_gaps = []
        for gaps in gap_analysis['consecutive_gaps']:
            all_gaps.extend(gaps)
        
        if all_gaps:
            gap_analysis['gap_statistics'] = {
                'average_gap': np.mean(all_gaps),
                'median_gap': np.median(all_gaps),
                'min_gap': min(all_gaps),
                'max_gap': max(all_gaps),
                'std_gap': np.std(all_gaps),
                'most_common_gaps': Counter(all_gaps).most_common(10)
            }
        
        return gap_analysis
    
    def _analyze_number_correlations(self) -> Dict:
        """Analiza correlaciones entre números en jackpots"""
        
        # Matriz de co-ocurrencia
        cooccurrence_matrix = np.zeros((40, 40))
        
        for combo in self.winning_combinations:
            for i, num1 in enumerate(combo):
                for j, num2 in enumerate(combo):
                    if i != j:
                        cooccurrence_matrix[num1-1][num2-1] += 1
        
        # Pares más frecuentes
        pair_frequencies = {}
        for combo in self.winning_combinations:
            for i in range(len(combo)):
                for j in range(i+1, len(combo)):
                    pair = tuple(sorted([combo[i], combo[j]]))
                    pair_frequencies[pair] = pair_frequencies.get(pair, 0) + 1
        
        most_frequent_pairs = sorted(pair_frequencies.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'cooccurrence_matrix': cooccurrence_matrix.tolist(),
            'most_frequent_pairs': most_frequent_pairs[:20],
            'total_pairs': len(pair_frequencies)
        }
    
    def _analyze_statistical_deviations(self) -> Dict:
        """Analiza desviaciones estadísticas de los patrones esperados"""
        
        deviations = {
            'sum_analysis': {},
            'parity_analysis': {},
            'consecutive_analysis': {}
        }
        
        # Análisis de sumas
        sums = [sum(combo) for combo in self.winning_combinations]
        expected_sum = 6 * 20.5  # Promedio teórico para 6 números de 1-40
        
        deviations['sum_analysis'] = {
            'observed_sums': sums,
            'average_sum': np.mean(sums),
            'expected_sum': expected_sum,
            'deviation_from_expected': np.mean(sums) - expected_sum,
            'sum_range': (min(sums), max(sums)),
            'sum_std': np.std(sums)
        }
        
        # Análisis de paridad (pares/impares)
        parity_patterns = []
        for combo in self.winning_combinations:
            pares = sum(1 for n in combo if n % 2 == 0)
            impares = 6 - pares
            parity_patterns.append((pares, impares))
        
        parity_counter = Counter(parity_patterns)
        
        deviations['parity_analysis'] = {
            'parity_patterns': parity_counter.most_common(),
            'expected_parity': (3, 3),  # Esperado: 3 pares, 3 impares
            'most_common_parity': parity_counter.most_common(1)[0] if parity_counter else None
        }
        
        # Análisis de números consecutivos
        consecutive_counts = []
        for combo in self.winning_combinations:
            sorted_combo = sorted(combo)
            consecutive_count = 0
            
            for i in range(1, len(sorted_combo)):
                if sorted_combo[i] == sorted_combo[i-1] + 1:
                    consecutive_count += 1
            
            consecutive_counts.append(consecutive_count)
        
        deviations['consecutive_analysis'] = {
            'consecutive_counts': consecutive_counts,
            'average_consecutives': np.mean(consecutive_counts),
            'max_consecutives': max(consecutive_counts),
            'combinations_with_consecutives': sum(1 for c in consecutive_counts if c > 0)
        }
        
        return deviations
    
    def integrate_with_omega_predictions(self, omega_combinations: List[List[int]]) -> Dict:
        """Integra patrones de jackpot con predicciones de OMEGA"""
        
        if not self.jackpot_patterns:
            self.analyze_jackpot_patterns()
        
        integration_results = {
            'jackpot_compatibility_scores': [],
            'enhanced_combinations': [],
            'risk_assessment': {}
        }
        
        # Analizar cada combinación OMEGA contra patrones de jackpot
        for combo in omega_combinations:
            compatibility_score = self._calculate_jackpot_compatibility(combo)
            enhanced_combo = self._enhance_combination_with_jackpot_patterns(combo)
            
            integration_results['jackpot_compatibility_scores'].append({
                'combination': combo,
                'compatibility_score': compatibility_score,
                'enhanced_combination': enhanced_combo
            })
        
        # Generar combinaciones híbridas
        hybrid_combinations = self._generate_hybrid_combinations(omega_combinations)
        integration_results['enhanced_combinations'] = hybrid_combinations
        
        # Evaluación de riesgos
        integration_results['risk_assessment'] = self._assess_integration_risks(omega_combinations)
        
        self.integration_analysis = integration_results
        return integration_results
    
    def _calculate_jackpot_compatibility(self, combination: List[int]) -> float:
        """Calcula qué tan compatible es una combinación con patrones de jackpot"""
        
        if not self.jackpot_patterns:
            return 0.0
        
        score = 0.0
        weight_sum = 0.0
        
        # Score basado en frecuencia de números
        freq_analysis = self.jackpot_patterns.get('frequency_analysis', {})
        if 'number_statistics' in freq_analysis:
            for num in combination:
                num_stats = freq_analysis['number_statistics'].get(num, {})
                frequency = num_stats.get('frequency', 0)
                score += frequency * 0.3
            weight_sum += 0.3
        
        # Score basado en balance de rangos
        range_analysis = self.jackpot_patterns.get('range_analysis', {})
        if 'most_common_balance' in range_analysis and range_analysis['most_common_balance']:
            combo_balance = self._get_range_balance(combination)
            optimal_balance = range_analysis['most_common_balance'][0]
            
            balance_similarity = self._calculate_balance_similarity(combo_balance, optimal_balance)
            score += balance_similarity * 0.25
            weight_sum += 0.25
        
        # Score basado en gaps
        gap_analysis = self.jackpot_patterns.get('gap_analysis', {})
        if 'gap_statistics' in gap_analysis:
            combo_gaps = self._calculate_combination_gaps(combination)
            target_avg_gap = gap_analysis['gap_statistics'].get('average_gap', 6)
            
            gap_score = 1 - abs(np.mean(combo_gaps) - target_avg_gap) / target_avg_gap
            score += max(0, gap_score) * 0.2
            weight_sum += 0.2
        
        # Score basado en suma
        deviation_analysis = self.jackpot_patterns.get('deviation_analysis', {})
        if 'sum_analysis' in deviation_analysis:
            combo_sum = sum(combination)
            target_sum = deviation_analysis['sum_analysis'].get('average_sum', 123)
            
            sum_score = 1 - abs(combo_sum - target_sum) / target_sum
            score += max(0, sum_score) * 0.15
            weight_sum += 0.15
        
        # Score basado en paridad
        if 'parity_analysis' in deviation_analysis and deviation_analysis['parity_analysis'].get('most_common_parity'):
            combo_parity = self._get_parity_balance(combination)
            target_parity = deviation_analysis['parity_analysis']['most_common_parity'][0]
            
            parity_score = 1 - abs(combo_parity[0] - target_parity[0]) / 6
            score += max(0, parity_score) * 0.1
            weight_sum += 0.1
        
        return score / weight_sum if weight_sum > 0 else 0.0
    
    def _enhance_combination_with_jackpot_patterns(self, combination: List[int]) -> List[int]:
        """Mejora una combinación usando patrones de jackpot"""
        
        enhanced = combination.copy()
        
        if not self.jackpot_patterns:
            return enhanced
        
        # Reemplazar números menos frecuentes con más frecuentes si mejora el score
        freq_analysis = self.jackpot_patterns.get('frequency_analysis', {})
        if 'most_frequent' in freq_analysis:
            frequent_numbers = [num for num, stats in freq_analysis['most_frequent'][:15]]
            
            for i, num in enumerate(enhanced):
                num_stats = freq_analysis.get('number_statistics', {}).get(num, {})
                current_freq = num_stats.get('frequency', 0)
                
                # Buscar reemplazo mejor
                for candidate in frequent_numbers:
                    if candidate not in enhanced:
                        candidate_stats = freq_analysis.get('number_statistics', {}).get(candidate, {})
                        candidate_freq = candidate_stats.get('frequency', 0)
                        
                        if candidate_freq > current_freq * 1.5:  # Mejora significativa
                            test_combo = enhanced.copy()
                            test_combo[i] = candidate
                            
                            if self._is_balanced_combination(test_combo):
                                enhanced[i] = candidate
                                break
        
        return sorted(enhanced)
    
    def _generate_hybrid_combinations(self, omega_combinations: List[List[int]]) -> List[Dict]:
        """Genera combinaciones híbridas OMEGA + Jackpot patterns"""
        
        hybrid_combinations = []
        
        if not self.jackpot_patterns:
            return hybrid_combinations
        
        # Obtener números más frecuentes en jackpots
        freq_analysis = self.jackpot_patterns.get('frequency_analysis', {})
        if 'most_frequent' in freq_analysis:
            hot_numbers = [num for num, stats in freq_analysis['most_frequent'][:20]]
            
            # Para cada combinación OMEGA, crear versión híbrida
            for omega_combo in omega_combinations:
                hybrid = self._create_hybrid_combination(omega_combo, hot_numbers)
                compatibility = self._calculate_jackpot_compatibility(hybrid)
                
                hybrid_combinations.append({
                    'original_omega': omega_combo,
                    'hybrid_combination': hybrid,
                    'jackpot_compatibility': compatibility,
                    'strategy': 'omega_jackpot_hybrid'
                })
        
        return sorted(hybrid_combinations, key=lambda x: x['jackpot_compatibility'], reverse=True)
    
    def _create_hybrid_combination(self, omega_combo: List[int], hot_numbers: List[int]) -> List[int]:
        """Crea una combinación híbrida entre OMEGA y números calientes de jackpots"""
        
        hybrid = omega_combo.copy()
        
        # Reemplazar 1-2 números con números calientes de jackpots
        replacements_made = 0
        max_replacements = 2
        
        for i, num in enumerate(hybrid):
            if replacements_made >= max_replacements:
                break
            
            # Buscar reemplazo en números calientes
            for hot_num in hot_numbers:
                if hot_num not in hybrid:
                    # Verificar que el reemplazo mantenga balance
                    test_combo = hybrid.copy()
                    test_combo[i] = hot_num
                    
                    if self._is_balanced_combination(test_combo):
                        hybrid[i] = hot_num
                        replacements_made += 1
                        break
        
        return sorted(hybrid)
    
    def _assess_integration_risks(self, omega_combinations: List[List[int]]) -> Dict:
        """Evalúa riesgos de la integración con patrones de jackpot"""
        
        risk_assessment = {
            'overfitting_risk': 0.0,
            'pattern_dependency': 0.0,
            'jackpot_bias': 0.0,
            'recommendations': []
        }
        
        # Evaluar overfitting
        if len(self.winning_combinations) < 10:
            risk_assessment['overfitting_risk'] = 0.8
            risk_assessment['recommendations'].append("Pocos jackpots históricos - alto riesgo de overfitting")
        
        # Evaluar dependencia de patrones
        unique_patterns = len(set(tuple(combo) for combo in self.winning_combinations))
        pattern_diversity = unique_patterns / len(self.winning_combinations) if self.winning_combinations else 0
        
        if pattern_diversity < 0.8:
            risk_assessment['pattern_dependency'] = 0.6
            risk_assessment['recommendations'].append("Baja diversidad en patrones de jackpot")
        
        # Evaluar sesgo hacia jackpots
        avg_compatibility = np.mean([
            self._calculate_jackpot_compatibility(combo) 
            for combo in omega_combinations
        ])
        
        if avg_compatibility > 0.7:
            risk_assessment['jackpot_bias'] = 0.5
            risk_assessment['recommendations'].append("Alto sesgo hacia patrones de jackpot históricos")
        
        return risk_assessment
    
    # Métodos auxiliares
    def _get_range_balance(self, combination: List[int]) -> str:
        """Obtiene el balance de rangos de una combinación"""
        bajo = sum(1 for n in combination if 1 <= n <= 13)
        medio = sum(1 for n in combination if 14 <= n <= 27)
        alto = sum(1 for n in combination if 28 <= n <= 40)
        return f"{bajo}-{medio}-{alto}"
    
    def _get_parity_balance(self, combination: List[int]) -> Tuple[int, int]:
        """Obtiene el balance de paridad (pares, impares)"""
        pares = sum(1 for n in combination if n % 2 == 0)
        impares = len(combination) - pares
        return (pares, impares)
    
    def _calculate_balance_similarity(self, balance1: str, balance2: str) -> float:
        """Calcula similaridad entre balances de rango"""
        try:
            b1 = [int(x) for x in balance1.split('-')]
            b2 = [int(x) for x in balance2.split('-')]
            
            diff = sum(abs(a - b) for a, b in zip(b1, b2))
            max_diff = 6  # Máxima diferencia posible
            
            return 1 - (diff / max_diff)
        except:
            return 0.0
    
    def _calculate_combination_gaps(self, combination: List[int]) -> List[int]:
        """Calcula gaps entre números consecutivos"""
        sorted_combo = sorted(combination)
        gaps = []
        
        for i in range(1, len(sorted_combo)):
            gaps.append(sorted_combo[i] - sorted_combo[i-1])
        
        return gaps
    
    def _is_balanced_combination(self, combination: List[int]) -> bool:
        """Verifica si una combinación está balanceada"""
        # Verificar balance de rangos
        bajo = sum(1 for n in combination if 1 <= n <= 13)
        medio = sum(1 for n in combination if 14 <= n <= 27)
        alto = sum(1 for n in combination if 28 <= n <= 40)
        
        # Aceptar si no hay desbalance extremo
        return min(bajo, medio, alto) >= 1 and max(bajo, medio, alto) <= 4

def integrate_jackpots_with_omega(jackpot_path: str, historical_path: str, omega_combinations: List[List[int]]) -> Dict:
    """Función principal para integrar jackpots con OMEGA"""
    
    # Crear integrador
    integrator = JackpotIntegrator(jackpot_path, historical_path)
    
    # Analizar patrones de jackpot
    jackpot_patterns = integrator.analyze_jackpot_patterns()
    
    # Integrar con OMEGA
    integration_results = integrator.integrate_with_omega_predictions(omega_combinations)
    
    return {
        'jackpot_patterns': jackpot_patterns,
        'integration_results': integration_results,
        'integrator': integrator
    }

if __name__ == "__main__":
    # Demo del integrador
    # Esto requeriría combinaciones OMEGA como input
    print("🎰 Jackpot Integrator - Demo")
    print("Use integrate_jackpots_with_omega() con combinaciones OMEGA")