#!/usr/bin/env python3
"""
🔬 RNG Seed Analyzer - Análisis de Seeds del RNG de Kabala
Busca patrones, ciclos y vulnerabilidades en el generador de números aleatorios específico
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from collections import Counter, defaultdict
import datetime
import logging
from scipy import stats
from scipy.fft import fft
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

class KabalaRNGAnalyzer:
    """Analizador especializado en el RNG específico de Kabala"""
    
    def __init__(self, historical_data: pd.DataFrame):
        self.data = historical_data
        self.bolilla_cols = [c for c in historical_data.columns if "bolilla" in c.lower()][:6]
        
        # Extraer secuencias numéricas
        self.number_sequences = self._extract_number_sequences()
        self.timing_data = self._extract_timing_data()
        
        # Análisis de patrones RNG
        self.rng_patterns = {}
        self.seed_analysis = {}
        self.vulnerability_report = {}
        
        logger.info("🔬 Kabala RNG Analyzer inicializado")
        logger.info(f"   Datos: {len(historical_data)} sorteos | Secuencias: {len(self.number_sequences)}")
    
    def _extract_number_sequences(self) -> List[List[int]]:
        """Extrae secuencias numéricas de todos los sorteos"""
        sequences = []
        for _, row in self.data.iterrows():
            sequence = [int(row[col]) for col in self.bolilla_cols]
            sequences.append(sequence)
        return sequences
    
    def _extract_timing_data(self) -> List[Dict]:
        """Extrae datos de timing si están disponibles"""
        timing_data = []
        
        if 'fecha' in self.data.columns:
            for _, row in self.data.iterrows():
                try:
                    fecha = pd.to_datetime(row['fecha'])
                    timing_data.append({
                        'fecha': fecha,
                        'timestamp': fecha.timestamp(),
                        'day_of_week': fecha.weekday(),
                        'day_of_month': fecha.day,
                        'month': fecha.month,
                        'year': fecha.year,
                        'unix_time': int(fecha.timestamp())
                    })
                except:
                    timing_data.append({'timestamp': None})
        
        return timing_data
    
    def analyze_rng_patterns(self) -> Dict:
        """Análisis completo de patrones RNG"""
        
        results = {
            'linear_congruential_analysis': self._analyze_lcg_patterns(),
            'mersenne_twister_analysis': self._analyze_mt_patterns(),
            'seed_correlation_analysis': self._analyze_seed_correlations(),
            'periodicity_analysis': self._analyze_periodicity(),
            'bias_analysis': self._analyze_rng_bias(),
            'timing_correlation': self._analyze_timing_correlations(),
            'hardware_signatures': self._detect_hardware_signatures(),
            'vulnerability_assessment': self._assess_vulnerabilities()
        }
        
        self.rng_patterns = results
        logger.info("🔍 Análisis de patrones RNG completado")
        
        return results
    
    def _analyze_lcg_patterns(self) -> Dict:
        """Análisis de Linear Congruential Generator (LCG)"""
        # LCG: X(n+1) = (a * X(n) + c) mod m
        
        # Convertir secuencias a stream único
        flat_sequence = []
        for seq in self.number_sequences:
            flat_sequence.extend(seq)
        
        # Buscar patrones LCG
        potential_lcg = {}
        
        # Analizar diferencias consecutivas
        differences = []
        for i in range(1, len(flat_sequence)):
            diff = flat_sequence[i] - flat_sequence[i-1]
            differences.append(diff)
        
        # Buscar periodicidad en diferencias
        diff_counter = Counter(differences)
        most_common_diffs = diff_counter.most_common(10)
        
        # Analizar posibles parámetros LCG
        possible_moduli = [2**16, 2**31-1, 2**32, 2**48, 2**64]  # Módulos comunes
        
        lcg_candidates = []
        for m in possible_moduli:
            # Intentar detectar patrón LCG con módulo m
            pattern_strength = self._test_lcg_hypothesis(flat_sequence, m)
            if pattern_strength > 0.1:  # Threshold para patrón significativo
                lcg_candidates.append({
                    'modulus': m,
                    'pattern_strength': pattern_strength
                })
        
        return {
            'flat_sequence_length': len(flat_sequence),
            'difference_patterns': most_common_diffs,
            'lcg_candidates': sorted(lcg_candidates, key=lambda x: x['pattern_strength'], reverse=True),
            'analysis_confidence': 'medium'
        }
    
    def _test_lcg_hypothesis(self, sequence: List[int], modulus: int) -> float:
        """Test si la secuencia sigue patrón LCG con módulo dado"""
        if len(sequence) < 10:
            return 0.0
        
        # Buscar correlación entre X(n) y X(n+1) mod m
        x_n = [x % modulus for x in sequence[:-1]]
        x_n1 = [x % modulus for x in sequence[1:]]
        
        try:
            correlation, p_value = stats.pearsonr(x_n, x_n1)
            if p_value < 0.05:  # Significativo
                return abs(correlation)
        except:
            pass
        
        return 0.0
    
    def _analyze_mt_patterns(self) -> Dict:
        """Análisis de Mersenne Twister patterns"""
        
        # MT tiene período de 2^19937 - 1, buscar características específicas
        flat_sequence = []
        for seq in self.number_sequences:
            flat_sequence.extend(seq)
        
        # Análisis espectral
        if len(flat_sequence) >= 1024:
            fft_result = fft(flat_sequence[:1024])
            power_spectrum = np.abs(fft_result)**2
            dominant_frequencies = np.argsort(power_spectrum)[-5:]
        else:
            dominant_frequencies = []
        
        # Test de distribución uniforme (MT debería ser uniforme)
        uniform_test = stats.kstest(flat_sequence, 'uniform', args=(1, 40))
        
        # Buscar correlaciones de largo alcance (MT característica)
        autocorrelations = []
        for lag in [1, 2, 3, 5, 8, 13, 21]:  # Fibonacci lags
            if len(flat_sequence) > lag:
                corr = np.corrcoef(flat_sequence[:-lag], flat_sequence[lag:])[0,1]
                autocorrelations.append({'lag': lag, 'correlation': corr})
        
        return {
            'sequence_length': len(flat_sequence),
            'uniformity_test': {
                'statistic': uniform_test.statistic,
                'p_value': uniform_test.pvalue,
                'is_uniform': uniform_test.pvalue > 0.05
            },
            'dominant_frequencies': dominant_frequencies.tolist() if len(dominant_frequencies) > 0 else [],
            'autocorrelations': autocorrelations,
            'mt_likelihood': 'high' if uniform_test.pvalue > 0.05 else 'low'
        }
    
    def _analyze_seed_correlations(self) -> Dict:
        """Analiza correlaciones entre seeds y timing"""
        
        if not self.timing_data or not all('timestamp' in t and t['timestamp'] for t in self.timing_data):
            return {'error': 'Datos de timing insuficientes'}
        
        correlations = {}
        
        # Correlación con timestamps
        timestamps = [t['timestamp'] for t in self.timing_data if t['timestamp']]
        first_numbers = [seq[0] for seq in self.number_sequences[:len(timestamps)]]
        
        if len(timestamps) == len(first_numbers) and len(timestamps) > 10:
            time_corr = np.corrcoef(timestamps, first_numbers)[0,1]
            correlations['timestamp_correlation'] = time_corr
            
            # Correlación con componentes de tiempo
            for time_component in ['day_of_week', 'day_of_month', 'month', 'year']:
                if time_component in self.timing_data[0]:
                    time_values = [t[time_component] for t in self.timing_data[:len(first_numbers)]]
                    corr = np.corrcoef(time_values, first_numbers)[0,1]
                    correlations[f'{time_component}_correlation'] = corr
        
        # Buscar patrones en seeds
        seed_patterns = self._detect_seed_patterns()
        
        return {
            'correlations': correlations,
            'seed_patterns': seed_patterns,
            'timing_dependency': max(abs(v) for v in correlations.values()) if correlations else 0.0
        }
    
    def _detect_seed_patterns(self) -> Dict:
        """Detecta patrones en posibles seeds"""
        
        patterns = {
            'sequential_seeds': 0,
            'timestamp_based': 0,
            'date_based': 0,
            'periodic_seeds': 0
        }
        
        # Analizar primeros números como posibles seeds
        first_numbers = [seq[0] for seq in self.number_sequences]
        
        # Detectar seeds secuenciales
        sequential_count = 0
        for i in range(1, len(first_numbers)):
            if first_numbers[i] == first_numbers[i-1] + 1:
                sequential_count += 1
        patterns['sequential_seeds'] = sequential_count / len(first_numbers) if first_numbers else 0
        
        # Detectar periodicidad en seeds
        if len(first_numbers) >= 20:
            periods_to_test = [7, 30, 365]  # semanal, mensual, anual
            for period in periods_to_test:
                if len(first_numbers) >= period * 2:
                    period_correlation = np.corrcoef(
                        first_numbers[:-period], 
                        first_numbers[period:]
                    )[0,1]
                    patterns[f'period_{period}_correlation'] = period_correlation
        
        return patterns
    
    def _analyze_periodicity(self) -> Dict:
        """Análisis de periodicidad en las secuencias"""
        
        flat_sequence = []
        for seq in self.number_sequences:
            flat_sequence.extend(seq)
        
        if len(flat_sequence) < 100:
            return {'error': 'Secuencia demasiado corta para análisis de periodicidad'}
        
        # FFT para encontrar periodicidades
        fft_result = fft(flat_sequence)
        frequencies = np.fft.fftfreq(len(flat_sequence))
        power_spectrum = np.abs(fft_result)**2
        
        # Encontrar picos en el espectro
        peaks = []
        threshold = np.mean(power_spectrum) + 2 * np.std(power_spectrum)
        
        for i, power in enumerate(power_spectrum[:len(power_spectrum)//2]):
            if power > threshold and frequencies[i] > 0:
                period = 1 / frequencies[i]
                peaks.append({
                    'frequency': frequencies[i],
                    'period': period,
                    'power': power
                })
        
        # Ordenar por potencia
        peaks = sorted(peaks, key=lambda x: x['power'], reverse=True)[:10]
        
        # Test de periodicidad estadística
        autocorr_results = []
        max_lag = min(len(flat_sequence) // 4, 1000)
        
        for lag in range(1, min(50, max_lag)):
            if len(flat_sequence) > lag:
                autocorr = np.corrcoef(flat_sequence[:-lag], flat_sequence[lag:])[0,1]
                autocorr_results.append({'lag': lag, 'autocorrelation': autocorr})
        
        return {
            'sequence_length': len(flat_sequence),
            'spectral_peaks': peaks,
            'autocorrelations': sorted(autocorr_results, key=lambda x: abs(x['autocorrelation']), reverse=True)[:10],
            'dominant_periods': [p['period'] for p in peaks[:3]]
        }
    
    def _analyze_rng_bias(self) -> Dict:
        """Analiza sesgos específicos del RNG"""
        
        # Análisis de distribución de números
        flat_sequence = []
        for seq in self.number_sequences:
            flat_sequence.extend(seq)
        
        # Test chi-cuadrado para uniformidad
        expected_freq = len(flat_sequence) / 40  # Esperado para 1-40
        observed_freq = Counter(flat_sequence)
        
        chi2_stat = 0
        for num in range(1, 41):
            observed = observed_freq.get(num, 0)
            chi2_stat += ((observed - expected_freq) ** 2) / expected_freq
        
        chi2_p_value = 1 - stats.chi2.cdf(chi2_stat, df=39)
        
        # Análisis de gaps entre números consecutivos
        gaps = []
        for i in range(1, len(flat_sequence)):
            gap = abs(flat_sequence[i] - flat_sequence[i-1])
            gaps.append(gap)
        
        gap_stats = {
            'mean_gap': np.mean(gaps),
            'std_gap': np.std(gaps),
            'max_gap': max(gaps),
            'min_gap': min(gaps)
        }
        
        # Detectar números favorecidos/evitados
        freq_analysis = Counter(flat_sequence)
        total_numbers = len(flat_sequence)
        
        biased_numbers = {}
        for num, count in freq_analysis.items():
            expected = total_numbers / 40
            bias_ratio = count / expected
            if abs(bias_ratio - 1.0) > 0.2:  # 20% de desviación
                biased_numbers[num] = {
                    'count': count,
                    'expected': expected,
                    'bias_ratio': bias_ratio,
                    'type': 'favored' if bias_ratio > 1.0 else 'avoided'
                }
        
        return {
            'uniformity_test': {
                'chi2_statistic': chi2_stat,
                'p_value': chi2_p_value,
                'is_uniform': chi2_p_value > 0.05
            },
            'gap_analysis': gap_stats,
            'biased_numbers': biased_numbers,
            'bias_severity': len(biased_numbers) / 40  # Proporción de números sesgados
        }
    
    def _analyze_timing_correlations(self) -> Dict:
        """Analiza correlaciones con timing específico"""
        
        if not self.timing_data:
            return {'error': 'No hay datos de timing disponibles'}
        
        timing_correlations = {}
        
        # Correlación con hora/día específico
        for seq_idx, timing in enumerate(self.timing_data):
            if seq_idx >= len(self.number_sequences):
                break
                
            if timing.get('timestamp'):
                # Correlaciones por posición en la secuencia
                sequence = self.number_sequences[seq_idx]
                
                for pos, number in enumerate(sequence):
                    key = f'position_{pos}_timing'
                    if key not in timing_correlations:
                        timing_correlations[key] = {'timestamps': [], 'numbers': []}
                    
                    timing_correlations[key]['timestamps'].append(timing['timestamp'])
                    timing_correlations[key]['numbers'].append(number)
        
        # Calcular correlaciones
        correlation_results = {}
        for key, data in timing_correlations.items():
            if len(data['timestamps']) > 10:
                corr = np.corrcoef(data['timestamps'], data['numbers'])[0,1]
                correlation_results[key] = corr
        
        return {
            'timing_correlations': correlation_results,
            'strongest_correlation': max(correlation_results.items(), 
                                       key=lambda x: abs(x[1])) if correlation_results else None
        }
    
    def _detect_hardware_signatures(self) -> Dict:
        """Detecta firmas específicas del hardware RNG"""
        
        signatures = {
            'bit_patterns': {},
            'entropy_analysis': {},
            'hardware_bias': {}
        }
        
        flat_sequence = []
        for seq in self.number_sequences:
            flat_sequence.extend(seq)
        
        # Análisis de bits
        if flat_sequence:
            # Convertir números a representación binaria
            bit_patterns = []
            for num in flat_sequence:
                bits = format(num, '06b')  # 6 bits para números 1-40
                bit_patterns.append(bits)
            
            # Analizar distribución de bits
            bit_counts = {'0': 0, '1': 0}
            for pattern in bit_patterns:
                bit_counts['0'] += pattern.count('0')
                bit_counts['1'] += pattern.count('1')
            
            total_bits = bit_counts['0'] + bit_counts['1']
            bit_ratio = bit_counts['1'] / total_bits if total_bits > 0 else 0
            
            signatures['bit_patterns'] = {
                'total_bits': total_bits,
                'ones_ratio': bit_ratio,
                'is_balanced': abs(bit_ratio - 0.5) < 0.05  # 5% tolerance
            }
        
        # Análisis de entropía
        if len(flat_sequence) > 100:
            # Entropía de Shannon
            freq_dist = Counter(flat_sequence)
            total = len(flat_sequence)
            entropy = -sum((count/total) * np.log2(count/total) 
                          for count in freq_dist.values() if count > 0)
            
            # Entropía máxima teórica para 40 números
            max_entropy = np.log2(40)
            entropy_ratio = entropy / max_entropy
            
            signatures['entropy_analysis'] = {
                'shannon_entropy': entropy,
                'max_entropy': max_entropy,
                'entropy_ratio': entropy_ratio,
                'quality': 'high' if entropy_ratio > 0.95 else 'medium' if entropy_ratio > 0.8 else 'low'
            }
        
        return signatures
    
    def _assess_vulnerabilities(self) -> Dict:
        """Evalúa vulnerabilidades potenciales del RNG"""
        
        vulnerabilities = {
            'predictability_risk': 'unknown',
            'seed_exposure_risk': 'unknown',
            'timing_dependency': 'unknown',
            'bias_exploitation': 'unknown',
            'recommendations': []
        }
        
        # Evaluar basado en análisis previos
        if hasattr(self, 'rng_patterns') and self.rng_patterns:
            patterns = self.rng_patterns
            
            # Riesgo de predictibilidad
            if 'periodicity_analysis' in patterns:
                period_data = patterns['periodicity_analysis']
                if 'dominant_periods' in period_data and period_data['dominant_periods']:
                    if any(p < 1000 for p in period_data['dominant_periods']):
                        vulnerabilities['predictability_risk'] = 'high'
                        vulnerabilities['recommendations'].append(
                            "Detectados períodos cortos - RNG potencialmente predecible"
                        )
            
            # Riesgo de exposición de seed
            if 'seed_correlation_analysis' in patterns:
                seed_data = patterns['seed_correlation_analysis']
                if 'timing_dependency' in seed_data and seed_data['timing_dependency'] > 0.3:
                    vulnerabilities['seed_exposure_risk'] = 'high'
                    vulnerabilities['recommendations'].append(
                        "Seeds correlacionados con timing - posible predicción basada en tiempo"
                    )
            
            # Riesgo de explotación de sesgos
            if 'bias_analysis' in patterns:
                bias_data = patterns['bias_analysis']
                if 'bias_severity' in bias_data and bias_data['bias_severity'] > 0.1:
                    vulnerabilities['bias_exploitation'] = 'medium'
                    vulnerabilities['recommendations'].append(
                        "Sesgos detectados en distribución - optimizar para números favorecidos"
                    )
        
        return vulnerabilities
    
    def generate_rng_exploit_strategy(self) -> Dict:
        """Genera estrategia de explotación basada en vulnerabilidades detectadas"""
        
        if not hasattr(self, 'rng_patterns') or not self.rng_patterns:
            self.analyze_rng_patterns()
        
        strategy = {
            'exploit_type': 'unknown',
            'confidence': 0.0,
            'recommended_numbers': [],
            'timing_strategy': {},
            'pattern_exploitation': {}
        }
        
        patterns = self.rng_patterns
        
        # Estrategia basada en sesgos
        if 'bias_analysis' in patterns:
            bias_data = patterns['bias_analysis']
            if 'biased_numbers' in bias_data:
                favored_numbers = [
                    num for num, data in bias_data['biased_numbers'].items()
                    if data['type'] == 'favored'
                ]
                
                if favored_numbers:
                    strategy['exploit_type'] = 'bias_exploitation'
                    strategy['recommended_numbers'] = sorted(favored_numbers)
                    strategy['confidence'] = min(0.8, len(favored_numbers) / 10)
        
        # Estrategia basada en periodicidad
        if 'periodicity_analysis' in patterns:
            period_data = patterns['periodicity_analysis']
            if 'dominant_periods' in period_data:
                short_periods = [p for p in period_data['dominant_periods'] if p < 500]
                if short_periods:
                    strategy['pattern_exploitation'] = {
                        'periods': short_periods,
                        'exploitation_method': 'cycle_prediction'
                    }
                    strategy['confidence'] = max(strategy['confidence'], 0.6)
        
        # Estrategia basada en timing
        if 'timing_correlation' in patterns:
            timing_data = patterns['timing_correlation']
            if 'strongest_correlation' in timing_data and timing_data['strongest_correlation']:
                strategy['timing_strategy'] = {
                    'correlation_type': timing_data['strongest_correlation'][0],
                    'correlation_strength': abs(timing_data['strongest_correlation'][1])
                }
                
                if abs(timing_data['strongest_correlation'][1]) > 0.3:
                    strategy['confidence'] = max(strategy['confidence'], 0.5)
        
        return strategy

def analyze_kabala_rng(data_path: str) -> Dict:
    """Función principal para analizar el RNG de Kabala"""
    
    # Cargar datos
    df = pd.read_csv(data_path)
    
    # Crear analizador
    analyzer = KabalaRNGAnalyzer(df)
    
    # Ejecutar análisis completo
    rng_patterns = analyzer.analyze_rng_patterns()
    exploit_strategy = analyzer.generate_rng_exploit_strategy()
    
    return {
        'rng_analysis': rng_patterns,
        'exploit_strategy': exploit_strategy,
        'analyzer': analyzer
    }

if __name__ == "__main__":
    # Demo del analizador
    result = analyze_kabala_rng("data/historial_kabala_github_emergency_clean.csv")
    print("🔬 Análisis RNG completado")
    print(f"Strategy confidence: {result['exploit_strategy']['confidence']:.2f}")