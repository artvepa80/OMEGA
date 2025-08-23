#!/usr/bin/env python3
"""
🔬 Entropy and FFT Analyzer - Análisis avanzado de entropía y FFT por posición
Complementa el análisis posicional del RNG con análisis de entropía de Shannon y FFT
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from collections import Counter
import logging
from scipy.fft import fft, fftfreq
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

class EntropyFFTAnalyzer:
    """Analizador especializado en entropía de Shannon y FFT por posición"""
    
    def __init__(self, historical_data: pd.DataFrame):
        self.data = historical_data
        self.bolilla_cols = [c for c in historical_data.columns if "bolilla" in c.lower()][:6]
        
        # Extraer secuencias por posición
        self.positional_sequences = self._extract_positional_sequences()
        
        # Almacenar resultados de análisis
        self.entropy_analysis = {}
        self.fft_analysis = {}
        self.combined_patterns = {}
        
        logger.info("🔬 Entropy & FFT Analyzer inicializado")
        logger.info(f"   Datos: {len(historical_data)} sorteos | Posiciones: {len(self.bolilla_cols)}")
    
    def _extract_positional_sequences(self) -> Dict[str, List[int]]:
        """Extrae secuencias numéricas por cada posición de bolilla"""
        sequences = {}
        
        for pos, col in enumerate(self.bolilla_cols, 1):
            sequences[f'bolilla_{pos}'] = []
            for _, row in self.data.iterrows():
                sequences[f'bolilla_{pos}'].append(int(row[col]))
        
        return sequences
    
    def analyze_positional_entropy(self) -> Dict:
        """Análisis completo de entropía de Shannon por posición"""
        
        results = {}
        
        for position, sequence in self.positional_sequences.items():
            
            # Entropía de Shannon básica
            entropy_basic = self._calculate_shannon_entropy(sequence)
            
            # Entropía condicional (dependencia entre sorteos consecutivos)
            entropy_conditional = self._calculate_conditional_entropy(sequence)
            
            # Entropía normalizada (0-1)
            max_entropy = np.log2(40)  # Máxima entropía para 40 números
            entropy_normalized = entropy_basic / max_entropy
            
            # Análisis de distribución de probabilidades
            freq_dist = Counter(sequence)
            total = len(sequence)
            prob_dist = {num: count/total for num, count in freq_dist.items()}
            
            # Entropía por ventanas deslizantes (detectar cambios temporales)
            window_entropies = self._analyze_entropy_windows(sequence, window_size=100)
            
            # Análisis de uniformidad
            uniformity_score = self._calculate_uniformity_score(sequence)
            
            results[position] = {
                'shannon_entropy': entropy_basic,
                'conditional_entropy': entropy_conditional,
                'normalized_entropy': entropy_normalized,
                'max_entropy': max_entropy,
                'uniformity_score': uniformity_score,
                'probability_distribution': prob_dist,
                'entropy_windows': window_entropies,
                'entropy_quality': self._classify_entropy_quality(entropy_normalized),
                'predictability_index': 1 - entropy_normalized  # Inverso de entropía normalizada
            }
        
        self.entropy_analysis = results
        logger.info("🔍 Análisis de entropía posicional completado")
        
        return results
    
    def _calculate_shannon_entropy(self, sequence: List[int]) -> float:
        """Calcula la entropía de Shannon de una secuencia"""
        if not sequence:
            return 0.0
        
        freq_dist = Counter(sequence)
        total = len(sequence)
        
        entropy = 0.0
        for count in freq_dist.values():
            p = count / total
            if p > 0:
                entropy -= p * np.log2(p)
        
        return entropy
    
    def _calculate_conditional_entropy(self, sequence: List[int]) -> float:
        """Calcula entropía condicional H(X|Y) - dependencia temporal"""
        if len(sequence) < 2:
            return 0.0
        
        # Crear pares (X_i, X_i+1)
        pairs = [(sequence[i], sequence[i+1]) for i in range(len(sequence)-1)]
        
        # Contar transiciones
        transition_counts = Counter(pairs)
        current_counts = Counter([pair[0] for pair in pairs])
        
        conditional_entropy = 0.0
        total_transitions = len(pairs)
        
        for (current, next_val), count in transition_counts.items():
            p_current = current_counts[current] / total_transitions
            p_conditional = count / current_counts[current]
            
            if p_current > 0 and p_conditional > 0:
                conditional_entropy -= (count / total_transitions) * np.log2(p_conditional)
        
        return conditional_entropy
    
    def _analyze_entropy_windows(self, sequence: List[int], window_size: int = 100) -> List[Dict]:
        """Analiza entropía en ventanas deslizantes para detectar cambios temporales"""
        if len(sequence) < window_size:
            return []
        
        window_results = []
        step_size = window_size // 4  # Overlap del 75%
        
        for start in range(0, len(sequence) - window_size + 1, step_size):
            window = sequence[start:start + window_size]
            entropy = self._calculate_shannon_entropy(window)
            
            window_results.append({
                'start_index': start,
                'end_index': start + window_size - 1,
                'entropy': entropy,
                'normalized_entropy': entropy / np.log2(40)
            })
        
        # Detectar cambios significativos
        if len(window_results) > 1:
            entropies = [w['entropy'] for w in window_results]
            entropy_changes = np.diff(entropies)
            threshold = np.std(entropy_changes) * 2
            
            for i, change in enumerate(entropy_changes):
                if abs(change) > threshold:
                    window_results[i+1]['significant_change'] = True
                    window_results[i+1]['change_magnitude'] = change
        
        return window_results
    
    def _calculate_uniformity_score(self, sequence: List[int]) -> float:
        """Calcula qué tan uniforme es la distribución (0 = perfectamente uniforme, 1 = completamente sesgada)"""
        freq_dist = Counter(sequence)
        total = len(sequence)
        expected_freq = total / 40
        
        # Chi-cuadrado normalizado
        chi2_stat = 0
        for num in range(1, 41):
            observed = freq_dist.get(num, 0)
            chi2_stat += ((observed - expected_freq) ** 2) / expected_freq
        
        # Normalizar por grados de libertad
        normalized_chi2 = chi2_stat / 39
        
        # Convertir a score 0-1 (0 = uniforme)
        uniformity_score = min(1.0, normalized_chi2 / 10)  # Ajustar según necesidad
        
        return uniformity_score
    
    def _classify_entropy_quality(self, normalized_entropy: float) -> str:
        """Clasifica la calidad de la entropía"""
        if normalized_entropy >= 0.95:
            return 'excellent'
        elif normalized_entropy >= 0.85:
            return 'good'
        elif normalized_entropy >= 0.70:
            return 'medium'
        elif normalized_entropy >= 0.50:
            return 'poor'
        else:
            return 'very_poor'
    
    def analyze_positional_fft(self) -> Dict:
        """Análisis completo de FFT por posición para detectar periodicidades"""
        
        results = {}
        
        for position, sequence in self.positional_sequences.items():
            
            if len(sequence) < 64:  # Mínimo para FFT útil
                results[position] = {'error': 'Secuencia demasiado corta para FFT'}
                continue
            
            # FFT de la secuencia
            fft_result = fft(sequence)
            frequencies = fftfreq(len(sequence))
            power_spectrum = np.abs(fft_result)**2
            
            # Detectar picos significativos
            peaks = self._detect_spectral_peaks(frequencies, power_spectrum)
            
            # Análisis de periodicidades dominantes
            dominant_periods = self._extract_dominant_periods(frequencies, power_spectrum)
            
            # Análisis de ruido vs señal
            signal_noise_ratio = self._calculate_signal_noise_ratio(power_spectrum)
            
            # Detectar componentes armónicas
            harmonics = self._detect_harmonic_components(frequencies, power_spectrum)
            
            # Análisis de espectro en bandas de frecuencia
            frequency_bands = self._analyze_frequency_bands(frequencies, power_spectrum)
            
            results[position] = {
                'sequence_length': len(sequence),
                'spectral_peaks': peaks,
                'dominant_periods': dominant_periods,
                'signal_noise_ratio': signal_noise_ratio,
                'harmonic_components': harmonics,
                'frequency_bands': frequency_bands,
                'spectral_centroid': self._calculate_spectral_centroid(frequencies, power_spectrum),
                'spectral_rolloff': self._calculate_spectral_rolloff(frequencies, power_spectrum),
                'periodicity_strength': len(dominant_periods) / 10  # Normalizado
            }
        
        self.fft_analysis = results
        logger.info("🔍 Análisis FFT posicional completado")
        
        return results
    
    def _detect_spectral_peaks(self, frequencies: np.ndarray, power_spectrum: np.ndarray) -> List[Dict]:
        """Detecta picos significativos en el espectro de potencia"""
        # Solo considerar frecuencias positivas
        pos_freq_idx = frequencies > 0
        pos_frequencies = frequencies[pos_freq_idx]
        pos_power = power_spectrum[pos_freq_idx]
        
        if len(pos_power) == 0:
            return []
        
        # Umbral dinámico basado en estadísticas del espectro
        mean_power = np.mean(pos_power)
        std_power = np.std(pos_power)
        threshold = mean_power + 2 * std_power
        
        peaks = []
        for i, (freq, power) in enumerate(zip(pos_frequencies, pos_power)):
            if power > threshold:
                period = 1 / freq if freq != 0 else float('inf')
                peaks.append({
                    'frequency': freq,
                    'period': period,
                    'power': power,
                    'significance': power / mean_power
                })
        
        # Ordenar por potencia
        peaks = sorted(peaks, key=lambda x: x['power'], reverse=True)
        
        return peaks[:10]  # Top 10 picos
    
    def _extract_dominant_periods(self, frequencies: np.ndarray, power_spectrum: np.ndarray) -> List[float]:
        """Extrae períodos dominantes del espectro"""
        peaks = self._detect_spectral_peaks(frequencies, power_spectrum)
        
        # Filtrar períodos razonables (entre 2 y 1000 sorteos)
        valid_periods = []
        for peak in peaks:
            period = peak['period']
            if 2 <= period <= 1000:
                valid_periods.append(period)
        
        return sorted(valid_periods)[:5]  # Top 5 períodos
    
    def _calculate_signal_noise_ratio(self, power_spectrum: np.ndarray) -> float:
        """Calcula la relación señal/ruido del espectro"""
        if len(power_spectrum) == 0:
            return 0.0
        
        # Considerar señal como los valores por encima del promedio + 1 std
        mean_power = np.mean(power_spectrum)
        std_power = np.std(power_spectrum)
        signal_threshold = mean_power + std_power
        
        signal_power = np.sum(power_spectrum[power_spectrum > signal_threshold])
        noise_power = np.sum(power_spectrum[power_spectrum <= signal_threshold])
        
        return signal_power / noise_power if noise_power > 0 else float('inf')
    
    def _detect_harmonic_components(self, frequencies: np.ndarray, power_spectrum: np.ndarray) -> List[Dict]:
        """Detecta componentes armónicas en el espectro"""
        peaks = self._detect_spectral_peaks(frequencies, power_spectrum)
        
        if len(peaks) < 2:
            return []
        
        harmonics = []
        
        # Buscar relaciones armónicas entre picos
        for i, peak1 in enumerate(peaks):
            for j, peak2 in enumerate(peaks[i+1:], i+1):
                freq1 = peak1['frequency']
                freq2 = peak2['frequency']
                
                if freq1 == 0 or freq2 == 0:
                    continue
                
                # Verificar si freq2 es armónico de freq1 (o viceversa)
                ratio = max(freq1, freq2) / min(freq1, freq2)
                
                # Verificar si es una relación armónica simple (2x, 3x, 4x, etc.)
                if abs(ratio - round(ratio)) < 0.1 and 2 <= round(ratio) <= 5:
                    harmonics.append({
                        'fundamental_freq': min(freq1, freq2),
                        'harmonic_freq': max(freq1, freq2),
                        'harmonic_ratio': round(ratio),
                        'combined_power': peak1['power'] + peak2['power']
                    })
        
        return sorted(harmonics, key=lambda x: x['combined_power'], reverse=True)
    
    def _analyze_frequency_bands(self, frequencies: np.ndarray, power_spectrum: np.ndarray) -> Dict:
        """Analiza la potencia en diferentes bandas de frecuencia"""
        if len(frequencies) == 0:
            return {}
        
        max_freq = np.max(np.abs(frequencies))
        
        bands = {
            'very_low': (0, max_freq * 0.1),      # Tendencias muy lentas
            'low': (max_freq * 0.1, max_freq * 0.25),     # Tendencias lentas
            'medium': (max_freq * 0.25, max_freq * 0.5),  # Periodicidades medias
            'high': (max_freq * 0.5, max_freq * 0.8),     # Periodicidades rápidas
            'very_high': (max_freq * 0.8, max_freq)       # Ruido/variaciones rápidas
        }
        
        band_power = {}
        total_power = np.sum(power_spectrum)
        
        for band_name, (min_freq, max_freq) in bands.items():
            band_mask = (np.abs(frequencies) >= min_freq) & (np.abs(frequencies) < max_freq)
            band_power_sum = np.sum(power_spectrum[band_mask])
            band_power[band_name] = {
                'absolute_power': band_power_sum,
                'relative_power': band_power_sum / total_power if total_power > 0 else 0
            }
        
        return band_power
    
    def _calculate_spectral_centroid(self, frequencies: np.ndarray, power_spectrum: np.ndarray) -> float:
        """Calcula el centroide espectral (centro de masa del espectro)"""
        if len(frequencies) == 0 or np.sum(power_spectrum) == 0:
            return 0.0
        
        # Solo frecuencias positivas
        pos_freq_idx = frequencies > 0
        pos_frequencies = frequencies[pos_freq_idx]
        pos_power = power_spectrum[pos_freq_idx]
        
        if len(pos_frequencies) == 0:
            return 0.0
        
        centroid = np.sum(pos_frequencies * pos_power) / np.sum(pos_power)
        return centroid
    
    def _calculate_spectral_rolloff(self, frequencies: np.ndarray, power_spectrum: np.ndarray, rolloff_percent: float = 0.85) -> float:
        """Calcula el rolloff espectral (frecuencia donde se acumula el X% de la potencia)"""
        if len(frequencies) == 0:
            return 0.0
        
        # Solo frecuencias positivas
        pos_freq_idx = frequencies > 0
        pos_frequencies = frequencies[pos_freq_idx]
        pos_power = power_spectrum[pos_freq_idx]
        
        if len(pos_frequencies) == 0:
            return 0.0
        
        # Ordenar por frecuencia
        sorted_idx = np.argsort(pos_frequencies)
        sorted_frequencies = pos_frequencies[sorted_idx]
        sorted_power = pos_power[sorted_idx]
        
        total_power = np.sum(sorted_power)
        cumulative_power = np.cumsum(sorted_power)
        
        rolloff_threshold = total_power * rolloff_percent
        rolloff_idx = np.where(cumulative_power >= rolloff_threshold)[0]
        
        if len(rolloff_idx) > 0:
            return sorted_frequencies[rolloff_idx[0]]
        else:
            return sorted_frequencies[-1]
    
    def generate_combined_analysis(self) -> Dict:
        """Genera análisis combinado de entropía y FFT por posición"""
        
        if not self.entropy_analysis or not self.fft_analysis:
            logger.warning("Ejecutar análisis de entropía y FFT primero")
            return {}
        
        combined = {}
        
        for position in self.bolilla_cols:
            pos_key = f'bolilla_{self.bolilla_cols.index(position) + 1}'
            
            entropy_data = self.entropy_analysis.get(pos_key, {})
            fft_data = self.fft_analysis.get(pos_key, {})
            
            if not entropy_data or not fft_data or 'error' in fft_data:
                continue
            
            # Combinar métricas
            predictability_index = entropy_data.get('predictability_index', 0)
            periodicity_strength = fft_data.get('periodicity_strength', 0)
            
            # Score de explotabilidad combinado
            exploitability_score = (predictability_index * 0.6) + (periodicity_strength * 0.4)
            
            # Clasificar la posición
            position_class = self._classify_position_exploitability(
                entropy_data, fft_data, exploitability_score
            )
            
            combined[pos_key] = {
                'entropy_quality': entropy_data.get('entropy_quality', 'unknown'),
                'predictability_index': predictability_index,
                'periodicity_strength': periodicity_strength,
                'exploitability_score': exploitability_score,
                'position_class': position_class,
                'dominant_periods': fft_data.get('dominant_periods', []),
                'signal_noise_ratio': fft_data.get('signal_noise_ratio', 0),
                'uniformity_score': entropy_data.get('uniformity_score', 0),
                'recommendations': self._generate_position_recommendations(
                    entropy_data, fft_data, exploitability_score
                )
            }
        
        self.combined_patterns = combined
        return combined
    
    def _classify_position_exploitability(self, entropy_data: Dict, fft_data: Dict, score: float) -> str:
        """Clasifica qué tan explotable es una posición"""
        if score >= 0.7:
            return 'highly_exploitable'
        elif score >= 0.5:
            return 'moderately_exploitable' 
        elif score >= 0.3:
            return 'slightly_exploitable'
        else:
            return 'not_exploitable'
    
    def _generate_position_recommendations(self, entropy_data: Dict, fft_data: Dict, score: float) -> List[str]:
        """Genera recomendaciones específicas para cada posición"""
        recommendations = []
        
        # Basado en entropía
        entropy_quality = entropy_data.get('entropy_quality', 'unknown')
        if entropy_quality in ['poor', 'very_poor']:
            recommendations.append("Baja entropía - números predictibles")
        
        # Basado en periodicidades
        periods = fft_data.get('dominant_periods', [])
        if periods:
            short_periods = [p for p in periods if p < 50]
            if short_periods:
                recommendations.append(f"Períodos cortos detectados: {short_periods}")
        
        # Basado en uniformidad
        uniformity = entropy_data.get('uniformity_score', 0)
        if uniformity > 0.3:
            recommendations.append("Distribución no uniforme - números favorecidos")
        
        # Score general
        if score >= 0.5:
            recommendations.append("Posición altamente explotable para predicción")
        
        return recommendations

def analyze_entropy_fft_patterns(data_path: str) -> Dict:
    """Función principal para análisis completo de entropía y FFT"""
    
    # Cargar datos
    df = pd.read_csv(data_path)
    
    # Crear analizador
    analyzer = EntropyFFTAnalyzer(df)
    
    # Ejecutar análisis
    entropy_results = analyzer.analyze_positional_entropy()
    fft_results = analyzer.analyze_positional_fft()
    combined_results = analyzer.generate_combined_analysis()
    
    return {
        'entropy_analysis': entropy_results,
        'fft_analysis': fft_results,
        'combined_analysis': combined_results,
        'analyzer': analyzer
    }

if __name__ == "__main__":
    # Demo del analizador
    result = analyze_entropy_fft_patterns("data/historial_kabala_github_emergency_clean.csv")
    print("🔬 Análisis de Entropía y FFT completado")
    print(f"Posiciones analizadas: {len(result['combined_analysis'])}")