#!/usr/bin/env python3
"""
🎯 Positional RNG Analyzer - Análisis Específico por Posición de Bolilla
El número 20 en bolilla_1 ≠ número 20 en bolilla_5
Cada posición puede tener seeds/algoritmos diferentes
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from collections import Counter, defaultdict
import datetime
import logging
from scipy import stats
from scipy.fft import fft
import itertools

logger = logging.getLogger(__name__)

class PositionalRNGAnalyzer:
    """Analizador de RNG específico por posición de bolilla"""
    
    def __init__(self, historical_data: pd.DataFrame):
        self.data = historical_data
        self.bolilla_cols = [c for c in historical_data.columns if "bolilla" in c.lower()][:6]
        
        # Extraer datos por posición
        self.positional_data = self._extract_positional_data()
        self.positional_patterns = {}
        self.cross_positional_correlations = {}
        self.positional_seeds = {}
        
        logger.info("🎯 Positional RNG Analyzer inicializado")
        logger.info(f"   Posiciones analizadas: {len(self.bolilla_cols)}")
        logger.info(f"   Datos por posición: {len(self.positional_data['bolilla_1']) if 'bolilla_1' in self.positional_data else 0}")
    
    def _extract_positional_data(self) -> Dict[str, List[int]]:
        """Extrae secuencias por posición específica"""
        positional_data = {}
        
        for col in self.bolilla_cols:
            positional_data[col] = []
            for _, row in self.data.iterrows():
                try:
                    number = int(row[col])
                    positional_data[col].append(number)
                except (ValueError, TypeError):
                    continue
        
        return positional_data
    
    def analyze_positional_rng_patterns(self) -> Dict:
        """Análisis completo por posición"""
        
        results = {}
        
        # Análisis individual por posición
        for position, sequence in self.positional_data.items():
            logger.info(f"🔍 Analizando {position}...")
            
            results[position] = {
                'basic_stats': self._analyze_position_stats(sequence, position),
                'rng_signature': self._analyze_position_rng_signature(sequence, position),
                'predictive_patterns': self._find_positional_predictive_patterns(sequence, position),
                'timing_correlation': self._analyze_position_timing_correlation(sequence, position),
                'seed_analysis': self._analyze_position_seeds(sequence, position)
            }
        
        # Análisis cruzado entre posiciones
        results['cross_positional'] = self._analyze_cross_positional_patterns()
        results['position_dependencies'] = self._analyze_position_dependencies()
        results['rng_architecture'] = self._infer_rng_architecture()
        
        self.positional_patterns = results
        logger.info("🎯 Análisis posicional completado")
        
        return results
    
    def _analyze_position_stats(self, sequence: List[int], position: str) -> Dict:
        """Estadísticas básicas por posición"""
        
        if not sequence:
            return {'error': 'Secuencia vacía'}
        
        counter = Counter(sequence)
        
        # Distribución de frecuencias
        freq_analysis = {}
        total = len(sequence)
        expected_freq = total / 40  # Para números 1-40
        
        for num in range(1, 41):
            observed = counter.get(num, 0)
            freq_analysis[num] = {
                'count': observed,
                'frequency': observed / total,
                'expected': expected_freq,
                'deviation': (observed - expected_freq) / expected_freq if expected_freq > 0 else 0
            }
        
        # Identificar números favorecidos/evitados por posición
        favored_numbers = []
        avoided_numbers = []
        
        for num, data in freq_analysis.items():
            if abs(data['deviation']) > 0.3:  # 30% de desviación
                if data['deviation'] > 0:
                    favored_numbers.append((num, data['frequency']))
                else:
                    avoided_numbers.append((num, data['frequency']))
        
        # Test de uniformidad específico por posición
        chi2_stat = sum(((counter.get(num, 0) - expected_freq) ** 2) / expected_freq 
                       for num in range(1, 41))
        chi2_p_value = 1 - stats.chi2.cdf(chi2_stat, df=39)
        
        # Rangos preferidos por posición
        range_analysis = {
            'bajo_1_13': sum(1 for n in sequence if 1 <= n <= 13) / total,
            'medio_14_27': sum(1 for n in sequence if 14 <= n <= 27) / total,
            'alto_28_40': sum(1 for n in sequence if 28 <= n <= 40) / total
        }
        
        return {
            'position': position,
            'total_samples': total,
            'unique_numbers': len(counter),
            'most_frequent': counter.most_common(5),
            'least_frequent': counter.most_common()[-5:],
            'favored_numbers': sorted(favored_numbers, key=lambda x: x[1], reverse=True),
            'avoided_numbers': sorted(avoided_numbers, key=lambda x: x[1]),
            'uniformity_test': {
                'chi2_statistic': chi2_stat,
                'p_value': chi2_p_value,
                'is_uniform': chi2_p_value > 0.05
            },
            'range_preferences': range_analysis,
            'position_bias_score': max(abs(v - 1/3) for v in range_analysis.values())  # Desviación de 33.33%
        }
    
    def _analyze_position_rng_signature(self, sequence: List[int], position: str) -> Dict:
        """Analiza firma RNG específica de cada posición"""
        
        if len(sequence) < 50:
            return {'error': 'Secuencia insuficiente'}
        
        # Análisis de gaps consecutivos
        gaps = []
        for i in range(1, len(sequence)):
            gap = sequence[i] - sequence[i-1]
            gaps.append(gap)
        
        gap_stats = {
            'mean': np.mean(gaps),
            'std': np.std(gaps),
            'median': np.median(gaps),
            'range': max(gaps) - min(gaps)
        }
        
        # Análisis de periodicidad específica
        autocorrelations = []
        max_lag = min(len(sequence) // 4, 200)
        
        for lag in range(1, max_lag):
            if len(sequence) > lag:
                corr = np.corrcoef(sequence[:-lag], sequence[lag:])[0,1]
                if not np.isnan(corr):
                    autocorrelations.append({'lag': lag, 'correlation': corr})
        
        # Ordenar por correlación más fuerte
        autocorrelations = sorted(autocorrelations, key=lambda x: abs(x['correlation']), reverse=True)
        
        # Análisis espectral para detectar periodicidades ocultas
        if len(sequence) >= 128:
            # Padding a potencia de 2 para FFT eficiente
            n_fft = 2 ** int(np.ceil(np.log2(len(sequence))))
            padded_sequence = np.pad(sequence, (0, n_fft - len(sequence)), 'constant')
            
            fft_result = fft(padded_sequence)
            frequencies = np.fft.fftfreq(n_fft)
            power_spectrum = np.abs(fft_result)**2
            
            # Encontrar picos significativos
            threshold = np.mean(power_spectrum) + 2 * np.std(power_spectrum)
            spectral_peaks = []
            
            for i, power in enumerate(power_spectrum[:len(power_spectrum)//2]):
                if power > threshold and frequencies[i] > 0:
                    period = 1 / frequencies[i] if frequencies[i] != 0 else float('inf')
                    spectral_peaks.append({
                        'frequency': frequencies[i],
                        'period': period,
                        'power': float(power)
                    })
            
            spectral_peaks = sorted(spectral_peaks, key=lambda x: x['power'], reverse=True)[:10]
        else:
            spectral_peaks = []
        
        # Análisis de runs (secuencias ascendentes/descendentes)
        runs = {'ascending': 0, 'descending': 0, 'equal': 0}
        for i in range(1, len(sequence)):
            if sequence[i] > sequence[i-1]:
                runs['ascending'] += 1
            elif sequence[i] < sequence[i-1]:
                runs['descending'] += 1
            else:
                runs['equal'] += 1
        
        total_runs = sum(runs.values())
        run_ratios = {k: v/total_runs for k, v in runs.items()} if total_runs > 0 else runs
        
        return {
            'position': position,
            'gap_analysis': gap_stats,
            'strongest_autocorrelations': autocorrelations[:10],
            'spectral_peaks': spectral_peaks,
            'run_analysis': run_ratios,
            'signature_strength': abs(max(autocorrelations, key=lambda x: abs(x['correlation']))['correlation']) if autocorrelations else 0
        }
    
    def _find_positional_predictive_patterns(self, sequence: List[int], position: str) -> Dict:
        """Busca patrones predictivos específicos por posición"""
        
        patterns = {
            'sequential_patterns': {},
            'cyclical_patterns': {},
            'mathematical_patterns': {},
            'conditional_patterns': {}
        }
        
        if len(sequence) < 10:
            return patterns
        
        # Patrones secuenciales (n-gramas)
        for n in range(2, min(6, len(sequence)//3)):
            ngrams = {}
            for i in range(len(sequence) - n):
                ngram = tuple(sequence[i:i+n])
                next_value = sequence[i+n]
                
                if ngram not in ngrams:
                    ngrams[ngram] = []
                ngrams[ngram].append(next_value)
            
            # Encontrar n-gramas predictivos
            predictive_ngrams = {}
            for ngram, next_values in ngrams.items():
                if len(next_values) >= 3:  # Al menos 3 ocurrencias
                    counter = Counter(next_values)
                    most_common = counter.most_common(1)[0]
                    prediction_accuracy = most_common[1] / len(next_values)
                    
                    if prediction_accuracy >= 0.5:  # Al menos 50% de precisión
                        predictive_ngrams[ngram] = {
                            'predicted_value': most_common[0],
                            'accuracy': prediction_accuracy,
                            'occurrences': len(next_values),
                            'confidence': prediction_accuracy * (len(next_values) / len(sequence))
                        }
            
            if predictive_ngrams:
                patterns['sequential_patterns'][f'{n}_gram'] = predictive_ngrams
        
        # Patrones cíclicos específicos por posición
        cycle_lengths = [7, 14, 30, 365]  # Semanal, quincenal, mensual, anual
        for cycle_len in cycle_lengths:
            if len(sequence) >= cycle_len * 3:  # Al menos 3 ciclos
                cycle_matches = 0
                total_comparisons = 0
                
                for i in range(cycle_len, len(sequence)):
                    if i - cycle_len >= 0:
                        if sequence[i] == sequence[i - cycle_len]:
                            cycle_matches += 1
                        total_comparisons += 1
                
                if total_comparisons > 0:
                    cycle_accuracy = cycle_matches / total_comparisons
                    if cycle_accuracy > 0.15:  # Significativamente mayor que random (1/40 = 0.025)
                        patterns['cyclical_patterns'][f'cycle_{cycle_len}'] = {
                            'accuracy': cycle_accuracy,
                            'matches': cycle_matches,
                            'total_comparisons': total_comparisons
                        }
        
        # Patrones matemáticos
        # Buscar progresiones aritméticas
        arithmetic_patterns = {}
        for step in range(1, 11):  # Pasos de 1 a 10
            matches = 0
            for i in range(2, len(sequence)):
                if (sequence[i] == sequence[i-1] + step and 
                    sequence[i-1] == sequence[i-2] + step):
                    matches += 1
            
            if matches > 0:
                arithmetic_patterns[f'step_{step}'] = {
                    'matches': matches,
                    'frequency': matches / (len(sequence) - 2)
                }
        
        if arithmetic_patterns:
            patterns['mathematical_patterns']['arithmetic'] = arithmetic_patterns
        
        # Buscar progresiones geométricas (multiplicativas)
        geometric_patterns = {}
        for factor in [2, 3]:
            matches = 0
            for i in range(2, len(sequence)):
                if (sequence[i-2] * factor == sequence[i-1] and 
                    sequence[i-1] * factor == sequence[i] and
                    sequence[i] <= 40):  # Dentro del rango válido
                    matches += 1
            
            if matches > 0:
                geometric_patterns[f'factor_{factor}'] = {
                    'matches': matches,
                    'frequency': matches / (len(sequence) - 2)
                }
        
        if geometric_patterns:
            patterns['mathematical_patterns']['geometric'] = geometric_patterns
        
        return patterns
    
    def _analyze_position_timing_correlation(self, sequence: List[int], position: str) -> Dict:
        """Analiza correlación con timing específico por posición"""
        
        if 'fecha' not in self.data.columns:
            return {'error': 'No hay datos de timing disponibles'}
        
        timing_correlations = {}
        
        # Obtener timestamps correspondientes
        timestamps = []
        position_numbers = []
        
        for idx, (_, row) in enumerate(self.data.iterrows()):
            if idx >= len(sequence):
                break
            
            try:
                fecha = pd.to_datetime(row['fecha'])
                timestamps.append({
                    'timestamp': fecha.timestamp(),
                    'day_of_week': fecha.weekday(),
                    'day_of_month': fecha.day,
                    'month': fecha.month,
                    'year': fecha.year,
                    'hour': fecha.hour if hasattr(fecha, 'hour') else 12,  # Default noon
                    'unix_time': int(fecha.timestamp())
                })
                position_numbers.append(sequence[idx])
            except:
                continue
        
        if len(timestamps) != len(position_numbers) or len(timestamps) < 10:
            return {'error': 'Datos de timing insuficientes o inconsistentes'}
        
        # Calcular correlaciones con diferentes componentes temporales
        time_components = ['timestamp', 'day_of_week', 'day_of_month', 'month', 'year', 'unix_time']
        
        for component in time_components:
            try:
                time_values = [t[component] for t in timestamps]
                correlation = np.corrcoef(time_values, position_numbers)[0,1]
                
                if not np.isnan(correlation):
                    timing_correlations[component] = correlation
            except Exception as e:
                logger.debug(f"Error calculando correlación {component} para {position}: {e}")
        
        # Buscar patrones de timing específicos por posición
        timing_patterns = {}
        
        # Análisis por día de la semana
        dow_patterns = defaultdict(list)
        for timestamp, number in zip(timestamps, position_numbers):
            dow_patterns[timestamp['day_of_week']].append(number)
        
        dow_analysis = {}
        for dow, numbers in dow_patterns.items():
            if len(numbers) >= 5:  # Al menos 5 muestras
                dow_analysis[dow] = {
                    'mean': np.mean(numbers),
                    'std': np.std(numbers),
                    'most_common': Counter(numbers).most_common(3),
                    'sample_size': len(numbers)
                }
        
        timing_patterns['day_of_week'] = dow_analysis
        
        # Análisis por mes
        month_patterns = defaultdict(list)
        for timestamp, number in zip(timestamps, position_numbers):
            month_patterns[timestamp['month']].append(number)
        
        month_analysis = {}
        for month, numbers in month_patterns.items():
            if len(numbers) >= 3:  # Al menos 3 muestras
                month_analysis[month] = {
                    'mean': np.mean(numbers),
                    'std': np.std(numbers),
                    'most_common': Counter(numbers).most_common(3),
                    'sample_size': len(numbers)
                }
        
        timing_patterns['month'] = month_analysis
        
        return {
            'position': position,
            'correlations': timing_correlations,
            'strongest_correlation': max(timing_correlations.items(), 
                                       key=lambda x: abs(x[1])) if timing_correlations else None,
            'timing_patterns': timing_patterns,
            'timing_dependency_score': max(abs(v) for v in timing_correlations.values()) if timing_correlations else 0.0
        }
    
    def _analyze_position_seeds(self, sequence: List[int], position: str) -> Dict:
        """Análisis de seeds específico por posición"""
        
        if len(sequence) < 20:
            return {'error': 'Secuencia insuficiente para análisis de seeds'}
        
        seed_analysis = {
            'seed_type_hypothesis': 'unknown',
            'seed_patterns': {},
            'predictability': 0.0
        }
        
        # Hipótesis 1: Seeds secuenciales por posición
        sequential_score = 0
        for i in range(1, min(len(sequence), 50)):
            if sequence[i] == sequence[i-1] + 1:
                sequential_score += 1
        
        sequential_ratio = sequential_score / min(len(sequence) - 1, 49)
        
        # Hipótesis 2: Seeds basados en timestamp por posición
        if 'fecha' in self.data.columns:
            timestamps = []
            try:
                for idx in range(min(len(sequence), len(self.data))):
                    fecha = pd.to_datetime(self.data.iloc[idx]['fecha'])
                    timestamps.append(int(fecha.timestamp()))
                
                if len(timestamps) == len(sequence[:len(timestamps)]):
                    timestamp_correlation = np.corrcoef(timestamps, sequence[:len(timestamps)])[0,1]
                    if not np.isnan(timestamp_correlation):
                        seed_analysis['seed_patterns']['timestamp_correlation'] = timestamp_correlation
            except:
                pass
        
        # Hipótesis 3: Seeds basados en posición específica con offset
        position_offsets = {}
        position_num = int(position.split('_')[1]) if '_' in position else 1
        
        for offset in [0, 1, 2, 3, 5, 7, 10]:
            offset_pattern = [(position_num + offset + i) % 40 + 1 for i in range(len(sequence))]
            correlation = np.corrcoef(sequence, offset_pattern)[0,1]
            if not np.isnan(correlation) and abs(correlation) > 0.1:
                position_offsets[f'offset_{offset}'] = correlation
        
        seed_analysis['seed_patterns']['position_offsets'] = position_offsets
        seed_analysis['seed_patterns']['sequential_ratio'] = sequential_ratio
        
        # Determinar tipo de seed más probable
        max_correlation = 0
        best_hypothesis = 'random'
        
        if sequential_ratio > 0.1:
            max_correlation = sequential_ratio
            best_hypothesis = 'sequential'
        
        if 'timestamp_correlation' in seed_analysis['seed_patterns']:
            timestamp_corr = abs(seed_analysis['seed_patterns']['timestamp_correlation'])
            if timestamp_corr > max_correlation:
                max_correlation = timestamp_corr
                best_hypothesis = 'timestamp_based'
        
        if position_offsets:
            max_pos_corr = max(abs(v) for v in position_offsets.values())
            if max_pos_corr > max_correlation:
                max_correlation = max_pos_corr
                best_hypothesis = 'position_based'
        
        seed_analysis['seed_type_hypothesis'] = best_hypothesis
        seed_analysis['predictability'] = max_correlation
        
        return seed_analysis
    
    def _analyze_cross_positional_patterns(self) -> Dict:
        """Analiza patrones entre diferentes posiciones"""
        
        cross_patterns = {}
        
        # Correlaciones directas entre posiciones
        position_correlations = {}
        positions = list(self.positional_data.keys())
        
        for i, pos1 in enumerate(positions):
            for j, pos2 in enumerate(positions[i+1:], i+1):
                seq1 = self.positional_data[pos1]
                seq2 = self.positional_data[pos2]
                
                min_len = min(len(seq1), len(seq2))
                if min_len >= 10:
                    correlation = np.corrcoef(seq1[:min_len], seq2[:min_len])[0,1]
                    if not np.isnan(correlation):
                        position_correlations[f'{pos1}_vs_{pos2}'] = correlation
        
        cross_patterns['direct_correlations'] = position_correlations
        
        # Patrones de lag entre posiciones
        lag_patterns = {}
        for i, pos1 in enumerate(positions):
            for j, pos2 in enumerate(positions[i+1:], i+1):
                seq1 = self.positional_data[pos1]
                seq2 = self.positional_data[pos2]
                
                # Buscar correlación con diferentes lags
                best_lag = 0
                best_correlation = 0
                
                for lag in range(1, min(20, len(seq1)//4)):
                    if len(seq1) > lag and len(seq2) > lag:
                        try:
                            corr = np.corrcoef(seq1[:-lag], seq2[lag:])[0,1]
                            if not np.isnan(corr) and abs(corr) > abs(best_correlation):
                                best_correlation = corr
                                best_lag = lag
                        except:
                            continue
                
                if abs(best_correlation) > 0.2:  # Correlación significativa
                    lag_patterns[f'{pos1}_to_{pos2}'] = {
                        'lag': best_lag,
                        'correlation': best_correlation
                    }
        
        cross_patterns['lag_correlations'] = lag_patterns
        
        # Dependencias causales (X[n] influye en Y[n+1])
        causal_patterns = {}
        for i, pos1 in enumerate(positions):
            for j, pos2 in enumerate(positions):
                if i != j:
                    seq1 = self.positional_data[pos1]  # Variable predictora
                    seq2 = self.positional_data[pos2]  # Variable dependiente
                    
                    if len(seq1) > 1 and len(seq2) > 1:
                        min_len = min(len(seq1) - 1, len(seq2) - 1)
                        if min_len >= 10:
                            # X[n] predice Y[n+1]
                            try:
                                corr = np.corrcoef(seq1[:min_len], seq2[1:min_len+1])[0,1]
                                if not np.isnan(corr) and abs(corr) > 0.2:
                                    causal_patterns[f'{pos1}_predicts_{pos2}'] = corr
                            except:
                                continue
        
        cross_patterns['causal_dependencies'] = causal_patterns
        
        return cross_patterns
    
    def _analyze_position_dependencies(self) -> Dict:
        """Analiza dependencias específicas entre posiciones"""
        
        dependencies = {
            'sequential_dependencies': {},
            'mathematical_relationships': {},
            'conditional_dependencies': {}
        }
        
        positions = list(self.positional_data.keys())
        
        # Dependencias secuenciales (bolilla_n depende de bolilla_n-1)
        for i in range(1, len(positions)):
            prev_pos = positions[i-1]
            curr_pos = positions[i]
            
            prev_seq = self.positional_data[prev_pos]
            curr_seq = self.positional_data[curr_pos]
            
            min_len = min(len(prev_seq), len(curr_seq))
            if min_len >= 10:
                # Dependencia directa
                direct_corr = np.corrcoef(prev_seq[:min_len], curr_seq[:min_len])[0,1]
                if not np.isnan(direct_corr):
                    dependencies['sequential_dependencies'][f'{prev_pos}_to_{curr_pos}'] = {
                        'direct_correlation': direct_corr
                    }
                
                # Buscar relaciones matemáticas
                math_relationships = {}
                
                # Suma/diferencia constante
                differences = [curr_seq[j] - prev_seq[j] for j in range(min_len)]
                diff_counter = Counter(differences)
                most_common_diff = diff_counter.most_common(1)[0]
                
                if most_common_diff[1] / min_len > 0.1:  # Al menos 10% de las veces
                    math_relationships['constant_difference'] = {
                        'difference': most_common_diff[0],
                        'frequency': most_common_diff[1] / min_len
                    }
                
                # Proporción constante
                ratios = []
                for j in range(min_len):
                    if prev_seq[j] != 0:
                        ratios.append(curr_seq[j] / prev_seq[j])
                
                if ratios:
                    ratio_counter = Counter([round(r, 2) for r in ratios])
                    most_common_ratio = ratio_counter.most_common(1)[0]
                    
                    if most_common_ratio[1] / len(ratios) > 0.1:
                        math_relationships['constant_ratio'] = {
                            'ratio': most_common_ratio[0],
                            'frequency': most_common_ratio[1] / len(ratios)
                        }
                
                if math_relationships:
                    dependencies['mathematical_relationships'][f'{prev_pos}_to_{curr_pos}'] = math_relationships
        
        return dependencies
    
    def _infer_rng_architecture(self) -> Dict:
        """Infiere la arquitectura del RNG basada en patrones encontrados"""
        
        architecture = {
            'rng_type': 'unknown',
            'position_independence': True,
            'seed_strategy': 'unknown',
            'vulnerability_level': 'unknown',
            'confidence': 0.0
        }
        
        if not hasattr(self, 'positional_patterns') or not self.positional_patterns:
            return architecture
        
        # Analizar independencia entre posiciones
        cross_patterns = self.positional_patterns.get('cross_positional', {})
        direct_correlations = cross_patterns.get('direct_correlations', {})
        
        if direct_correlations:
            max_correlation = max(abs(v) for v in direct_correlations.values())
            if max_correlation > 0.3:
                architecture['position_independence'] = False
                architecture['confidence'] = max_correlation
        
        # Inferir tipo de RNG basado en patrones individuales
        rng_signatures = []
        for position, data in self.positional_patterns.items():
            if position.startswith('bolilla_'):
                signature = data.get('rng_signature', {})
                if 'signature_strength' in signature:
                    rng_signatures.append(signature['signature_strength'])
        
        if rng_signatures:
            avg_signature_strength = np.mean(rng_signatures)
            if avg_signature_strength > 0.5:
                architecture['rng_type'] = 'deterministic_with_patterns'
            elif avg_signature_strength > 0.2:
                architecture['rng_type'] = 'pseudo_random_with_weaknesses'
            else:
                architecture['rng_type'] = 'strong_pseudo_random'
        
        # Inferir estrategia de seeds
        seed_types = []
        for position, data in self.positional_patterns.items():
            if position.startswith('bolilla_'):
                seed_data = data.get('seed_analysis', {})
                if 'seed_type_hypothesis' in seed_data:
                    seed_types.append(seed_data['seed_type_hypothesis'])
        
        if seed_types:
            most_common_seed_type = Counter(seed_types).most_common(1)[0][0]
            architecture['seed_strategy'] = most_common_seed_type
        
        # Evaluar vulnerabilidad general
        vulnerability_indicators = 0
        total_indicators = 0
        
        # Indicador 1: Correlaciones entre posiciones
        if not architecture['position_independence']:
            vulnerability_indicators += 1
        total_indicators += 1
        
        # Indicador 2: Patrones predictivos detectados
        predictive_patterns_found = False
        for position, data in self.positional_patterns.items():
            if position.startswith('bolilla_'):
                patterns = data.get('predictive_patterns', {})
                if any(patterns.get(pattern_type, {}) for pattern_type in patterns):
                    predictive_patterns_found = True
                    break
        
        if predictive_patterns_found:
            vulnerability_indicators += 1
        total_indicators += 1
        
        # Indicador 3: Seeds predecibles
        predictable_seeds = sum(1 for position, data in self.positional_patterns.items()
                               if position.startswith('bolilla_') and
                               data.get('seed_analysis', {}).get('predictability', 0) > 0.3)
        
        if predictable_seeds > len([p for p in self.positional_patterns if p.startswith('bolilla_')]) // 2:
            vulnerability_indicators += 1
        total_indicators += 1
        
        vulnerability_ratio = vulnerability_indicators / total_indicators if total_indicators > 0 else 0
        
        if vulnerability_ratio >= 0.67:
            architecture['vulnerability_level'] = 'high'
        elif vulnerability_ratio >= 0.33:
            architecture['vulnerability_level'] = 'medium'
        else:
            architecture['vulnerability_level'] = 'low'
        
        architecture['confidence'] = max(architecture['confidence'], vulnerability_ratio)
        
        return architecture
    
    def generate_positional_exploit_strategy(self) -> Dict:
        """Genera estrategia de explotación basada en análisis posicional"""
        
        if not hasattr(self, 'positional_patterns') or not self.positional_patterns:
            self.analyze_positional_rng_patterns()
        
        strategy = {
            'exploit_method': 'positional_optimization',
            'position_strategies': {},
            'cross_position_strategies': {},
            'overall_confidence': 0.0,
            'recommended_combinations': []
        }
        
        # Estrategias por posición individual
        for position, data in self.positional_patterns.items():
            if not position.startswith('bolilla_'):
                continue
            
            pos_strategy = {
                'favored_numbers': [],
                'avoided_numbers': [],
                'predictive_patterns': [],
                'timing_strategy': {},
                'confidence': 0.0
            }
            
            # Números favorecidos/evitados
            basic_stats = data.get('basic_stats', {})
            if 'favored_numbers' in basic_stats:
                pos_strategy['favored_numbers'] = [num for num, freq in basic_stats['favored_numbers'][:5]]
            if 'avoided_numbers' in basic_stats:
                pos_strategy['avoided_numbers'] = [num for num, freq in basic_stats['avoided_numbers'][:3]]
            
            # Patrones predictivos
            predictive_patterns = data.get('predictive_patterns', {})
            if predictive_patterns:
                best_patterns = []
                for pattern_type, patterns in predictive_patterns.items():
                    if isinstance(patterns, dict):
                        for pattern_key, pattern_data in patterns.items():
                            if isinstance(pattern_data, dict) and 'confidence' in pattern_data:
                                if pattern_data['confidence'] > 0.3:
                                    best_patterns.append({
                                        'type': pattern_type,
                                        'pattern': pattern_key,
                                        'confidence': pattern_data['confidence']
                                    })
                
                pos_strategy['predictive_patterns'] = sorted(best_patterns, 
                                                           key=lambda x: x['confidence'], 
                                                           reverse=True)[:3]
            
            # Estrategia de timing
            timing_data = data.get('timing_correlation', {})
            if 'strongest_correlation' in timing_data and timing_data['strongest_correlation']:
                component, correlation = timing_data['strongest_correlation']
                if abs(correlation) > 0.3:
                    pos_strategy['timing_strategy'] = {
                        'component': component,
                        'correlation': correlation,
                        'strategy': 'time_based_prediction'
                    }
            
            # Calcular confianza de posición
            confidence_factors = []
            
            if pos_strategy['favored_numbers']:
                confidence_factors.append(len(pos_strategy['favored_numbers']) / 40)
            
            if pos_strategy['predictive_patterns']:
                max_pattern_conf = max(p['confidence'] for p in pos_strategy['predictive_patterns'])
                confidence_factors.append(max_pattern_conf)
            
            if pos_strategy['timing_strategy']:
                confidence_factors.append(abs(pos_strategy['timing_strategy']['correlation']))
            
            pos_strategy['confidence'] = np.mean(confidence_factors) if confidence_factors else 0.0
            strategy['position_strategies'][position] = pos_strategy
        
        # Estrategias cruzadas entre posiciones
        cross_patterns = self.positional_patterns.get('cross_positional', {})
        
        # Dependencias causales
        causal_deps = cross_patterns.get('causal_dependencies', {})
        for relationship, correlation in causal_deps.items():
            if abs(correlation) > 0.3:
                strategy['cross_position_strategies'][relationship] = {
                    'correlation': correlation,
                    'strategy': 'causal_prediction',
                    'confidence': abs(correlation)
                }
        
        # Calcular confianza general
        all_confidences = []
        for pos_strategy in strategy['position_strategies'].values():
            all_confidences.append(pos_strategy['confidence'])
        
        for cross_strategy in strategy['cross_position_strategies'].values():
            all_confidences.append(cross_strategy['confidence'])
        
        strategy['overall_confidence'] = np.mean(all_confidences) if all_confidences else 0.0
        
        # Generar combinaciones recomendadas basadas en estrategias
        if strategy['overall_confidence'] > 0.2:
            strategy['recommended_combinations'] = self._generate_optimal_combinations_from_strategy(strategy)
        
        return strategy
    
    def _generate_optimal_combinations_from_strategy(self, strategy: Dict) -> List[List[int]]:
        """Genera combinaciones óptimas basadas en estrategia posicional"""
        
        combinations = []
        
        # Generar combinaciones basadas en números favorecidos por posición
        for attempt in range(5):  # Generar 5 combinaciones
            combination = []
            
            positions = sorted([pos for pos in strategy['position_strategies'].keys() if pos.startswith('bolilla_')])
            
            for position in positions:
                pos_strategy = strategy['position_strategies'][position]
                
                # Elegir número basado en estrategia de posición
                candidates = []
                
                # Priorizar números favorecidos
                if pos_strategy['favored_numbers']:
                    candidates.extend(pos_strategy['favored_numbers'])
                
                # Evitar números evitados
                avoided = set(pos_strategy['avoided_numbers'])
                candidates = [n for n in candidates if n not in avoided]
                
                # Si no hay candidatos favorecidos, usar rango completo excepto evitados
                if not candidates:
                    candidates = [n for n in range(1, 41) if n not in avoided]
                
                # Evitar duplicados en la misma combinación
                available_candidates = [n for n in candidates if n not in combination]
                if not available_candidates:
                    available_candidates = [n for n in range(1, 41) if n not in combination]
                
                if available_candidates:
                    # Seleccionar con alguna variación
                    if len(available_candidates) > 1:
                        selected = available_candidates[attempt % len(available_candidates)]
                    else:
                        selected = available_candidates[0]
                    combination.append(selected)
                else:
                    # Fallback: número aleatorio no usado
                    for n in range(1, 41):
                        if n not in combination:
                            combination.append(n)
                            break
            
            if len(combination) == 6 and combination not in combinations:
                combinations.append(sorted(combination))
        
        return combinations

def analyze_positional_rng(data_path: str) -> Dict:
    """Función principal para análisis posicional del RNG"""
    
    # Cargar datos
    df = pd.read_csv(data_path)
    
    # Crear analizador posicional
    analyzer = PositionalRNGAnalyzer(df)
    
    # Ejecutar análisis completo
    positional_patterns = analyzer.analyze_positional_rng_patterns()
    exploit_strategy = analyzer.generate_positional_exploit_strategy()
    
    return {
        'positional_analysis': positional_patterns,
        'exploit_strategy': exploit_strategy,
        'analyzer': analyzer
    }

if __name__ == "__main__":
    # Demo del analizador posicional
    result = analyze_positional_rng("data/historial_kabala_github_emergency_clean.csv")
    print("🎯 Análisis posicional RNG completado")
    print(f"Overall confidence: {result['exploit_strategy']['overall_confidence']:.3f}")
    
    # Mostrar estrategias por posición
    for position, strategy in result['exploit_strategy']['position_strategies'].items():
        print(f"\n{position}:")
        print(f"  Números favorecidos: {strategy['favored_numbers']}")
        print(f"  Confianza: {strategy['confidence']:.3f}")