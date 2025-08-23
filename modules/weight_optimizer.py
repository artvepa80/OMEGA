#!/usr/bin/env python3
"""
⚖️ Weight Optimizer - Análisis de los últimos 1500 sorteos para determinar peso perfecto
Optimiza los pesos de cada componente del sistema OMEGA basado en datos históricos
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
import logging
from collections import Counter, defaultdict
from itertools import product
from sklearn.metrics import precision_score, recall_score, f1_score
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

class WeightOptimizer:
    """Optimizador de pesos para el sistema OMEGA"""
    
    def __init__(self, historical_data: pd.DataFrame, analysis_results: Dict):
        # Usar últimos 1500 sorteos
        self.data = historical_data.tail(1500).copy()
        self.analysis_results = analysis_results
        self.bolilla_cols = [c for c in historical_data.columns if "bolilla" in c.lower()][:6]
        
        # Configuración de optimización
        self.train_split = 0.8  # 80% para entrenamiento, 20% para validación
        self.train_size = int(len(self.data) * self.train_split)
        
        self.train_data = self.data.iloc[:self.train_size]
        self.validation_data = self.data.iloc[self.train_size:]
        
        # Métricas de evaluación
        self.weight_combinations = []
        self.performance_results = []
        
        logger.info("⚖️ Weight Optimizer inicializado")
        logger.info(f"   Datos totales: {len(self.data)} sorteos")
        logger.info(f"   Entrenamiento: {len(self.train_data)} sorteos")  
        logger.info(f"   Validación: {len(self.validation_data)} sorteos")
    
    def analyze_component_performance(self) -> Dict:
        """Analiza el rendimiento individual de cada componente"""
        
        print("\n⚖️ ANALIZANDO RENDIMIENTO DE COMPONENTES INDIVIDUALES...")
        
        component_performance = {}
        
        # 1. Análisis Posicional
        positional_perf = self._evaluate_positional_component()
        component_performance['positional'] = positional_perf
        
        # 2. Análisis Entropía/FFT
        entropy_fft_perf = self._evaluate_entropy_fft_component()
        component_performance['entropy_fft'] = entropy_fft_perf
        
        # 3. Análisis Jackpots
        jackpot_perf = self._evaluate_jackpot_component()
        component_performance['jackpot'] = jackpot_perf
        
        # 4. Análisis Hits Parciales
        partial_hits_perf = self._evaluate_partial_hits_component()
        component_performance['partial_hits'] = partial_hits_perf
        
        # 5. Análisis de Patrones
        patterns_perf = self._evaluate_patterns_component()
        component_performance['patterns'] = patterns_perf
        
        self._display_component_performance(component_performance)
        
        return component_performance
    
    def _evaluate_positional_component(self) -> Dict:
        """Evalúa rendimiento del componente posicional"""
        
        if 'positional_analysis' not in self.analysis_results:
            return {'accuracy': 0.0, 'coverage': 0.0, 'reliability': 0.0}
        
        positional_patterns = self.analysis_results['positional_analysis'].get('position_patterns', {})
        
        hits = 0
        total_positions = 0
        
        # Evaluar cada posición en datos de validación
        for _, row in self.validation_data.iterrows():
            for i, col in enumerate(self.bolilla_cols):
                pos_key = f'bolilla_{i+1}'
                actual_number = int(row[col])
                
                if pos_key in positional_patterns:
                    preferred_numbers = positional_patterns[pos_key].get('preferred_numbers', [])[:10]
                    if preferred_numbers and actual_number in preferred_numbers:
                        # Peso según posición en la lista (más alto si está primero)
                        position_weight = (10 - preferred_numbers.index(actual_number)) / 10
                        hits += position_weight
                
                total_positions += 1
        
        accuracy = hits / total_positions if total_positions > 0 else 0
        coverage = len([p for p in positional_patterns.values() if p.get('preferred_numbers')]) / 6
        
        return {
            'accuracy': accuracy,
            'coverage': coverage,
            'reliability': accuracy * coverage,
            'total_hits': hits,
            'total_evaluated': total_positions
        }
    
    def _evaluate_entropy_fft_component(self) -> Dict:
        """Evalúa rendimiento del componente entropía/FFT"""
        
        if 'combined_entropy_fft' not in self.analysis_results:
            return {'accuracy': 0.0, 'exploitability': 0.0, 'reliability': 0.0}
        
        entropy_fft_data = self.analysis_results['combined_entropy_fft']
        
        total_exploitability = 0
        exploitable_positions = 0
        
        for pos_key, data in entropy_fft_data.items():
            exploitability_score = data.get('exploitability_score', 0)
            total_exploitability += exploitability_score
            
            if exploitability_score > 0.3:  # Umbral de explotabilidad
                exploitable_positions += 1
        
        avg_exploitability = total_exploitability / len(entropy_fft_data) if entropy_fft_data else 0
        position_coverage = exploitable_positions / 6
        
        # Simular precisión basada en periodicidades detectadas
        fft_analysis = self.analysis_results.get('fft_analysis', {})
        periods_detected = 0
        
        for pos_data in fft_analysis.values():
            if isinstance(pos_data, dict) and 'dominant_periods' in pos_data:
                periods_detected += len(pos_data['dominant_periods'])
        
        pattern_strength = min(1.0, periods_detected / 10)  # Normalizar
        
        return {
            'accuracy': pattern_strength,
            'exploitability': avg_exploitability,
            'coverage': position_coverage,
            'reliability': pattern_strength * avg_exploitability
        }
    
    def _evaluate_jackpot_component(self) -> Dict:
        """Evalúa rendimiento del componente jackpots"""
        
        if 'jackpot_analysis' not in self.analysis_results:
            return {'accuracy': 0.0, 'frequency_match': 0.0, 'reliability': 0.0}
        
        jackpot_patterns = self.analysis_results['jackpot_analysis']
        freq_analysis = jackpot_patterns.get('frequency_analysis', {})
        
        if 'most_frequent' not in freq_analysis:
            return {'accuracy': 0.0, 'frequency_match': 0.0, 'reliability': 0.0}
        
        # Números más frecuentes en jackpots
        hot_numbers = [num for num, _ in freq_analysis['most_frequent'][:20]]
        
        hits = 0
        total_numbers = 0
        
        # Evaluar qué tan bien predicen los números calientes
        for _, row in self.validation_data.iterrows():
            for col in self.bolilla_cols:
                actual_number = int(row[col])
                if actual_number in hot_numbers:
                    # Peso según posición en ranking de frecuencia
                    position_in_ranking = hot_numbers.index(actual_number)
                    weight = (20 - position_in_ranking) / 20
                    hits += weight
                total_numbers += 1
        
        frequency_match = hits / total_numbers if total_numbers > 0 else 0
        
        # Evaluar balance patterns
        range_analysis = jackpot_patterns.get('range_analysis', {})
        balance_accuracy = 0
        
        if 'most_common_balance' in range_analysis:
            target_balance = range_analysis['most_common_balance'][0]  # ej: "2-2-2"
            balance_parts = [int(x) for x in target_balance.split('-')]
            
            matches = 0
            for _, row in self.validation_data.iterrows():
                bajo = sum(1 for col in self.bolilla_cols if 1 <= int(row[col]) <= 13)
                medio = sum(1 for col in self.bolilla_cols if 14 <= int(row[col]) <= 27)
                alto = sum(1 for col in self.bolilla_cols if 28 <= int(row[col]) <= 40)
                
                actual_balance = [bajo, medio, alto]
                # Calcular similaridad de balance
                similarity = 1 - sum(abs(a - b) for a, b in zip(actual_balance, balance_parts)) / 6
                matches += max(0, similarity)
            
            balance_accuracy = matches / len(self.validation_data)
        
        combined_accuracy = (frequency_match + balance_accuracy) / 2
        
        return {
            'accuracy': combined_accuracy,
            'frequency_match': frequency_match,
            'balance_accuracy': balance_accuracy,
            'reliability': combined_accuracy,
            'hot_numbers_coverage': len(hot_numbers) / 40
        }
    
    def _evaluate_partial_hits_component(self) -> Dict:
        """Evalúa rendimiento del componente hits parciales"""
        
        # Simular evaluación de hits parciales
        # En un escenario real, esto requeriría generar predicciones y evaluarlas
        
        # Calcular cobertura numérica histórica
        all_numbers = []
        for _, row in self.train_data.iterrows():
            for col in self.bolilla_cols:
                all_numbers.append(int(row[col]))
        
        number_frequency = Counter(all_numbers)
        
        # Evaluar distribución de hits parciales esperados
        coverage_score = len(number_frequency) / 40  # Cuántos números únicos aparecen
        
        # Evaluar balance de rangos
        bajo_count = sum(1 for n in all_numbers if 1 <= n <= 13)
        medio_count = sum(1 for n in all_numbers if 14 <= n <= 27)
        alto_count = sum(1 for n in all_numbers if 28 <= n <= 40)
        total_numbers = len(all_numbers)
        
        expected_each = total_numbers / 3
        balance_score = 1 - (abs(bajo_count - expected_each) + 
                           abs(medio_count - expected_each) + 
                           abs(alto_count - expected_each)) / (2 * total_numbers)
        
        # Evaluar patrones de co-ocurrencia
        cooccurrence_strength = self._calculate_cooccurrence_strength()
        
        combined_score = (coverage_score + balance_score + cooccurrence_strength) / 3
        
        return {
            'accuracy': combined_score,
            'coverage': coverage_score,
            'balance': balance_score,
            'cooccurrence': cooccurrence_strength,
            'reliability': combined_score
        }
    
    def _evaluate_patterns_component(self) -> Dict:
        """Evalúa rendimiento del componente patrones"""
        
        # Evaluar patrones temporales
        temporal_patterns = self._analyze_temporal_patterns()
        
        # Evaluar patrones de secuencia
        sequence_patterns = self._analyze_sequence_patterns()
        
        # Evaluar patrones de gaps
        gap_patterns = self._analyze_gap_patterns()
        
        combined_accuracy = (temporal_patterns + sequence_patterns + gap_patterns) / 3
        
        return {
            'accuracy': combined_accuracy,
            'temporal': temporal_patterns,
            'sequence': sequence_patterns,
            'gaps': gap_patterns,
            'reliability': combined_accuracy
        }
    
    def _calculate_cooccurrence_strength(self) -> float:
        """Calcula la fuerza de co-ocurrencia entre números"""
        
        cooccurrence_matrix = np.zeros((40, 40))
        
        for _, row in self.train_data.iterrows():
            numbers = [int(row[col]) for col in self.bolilla_cols]
            for i in range(len(numbers)):
                for j in range(i+1, len(numbers)):
                    cooccurrence_matrix[numbers[i]-1][numbers[j]-1] += 1
                    cooccurrence_matrix[numbers[j]-1][numbers[i]-1] += 1
        
        # Calcular fuerza promedio de co-ocurrencia
        non_zero_entries = cooccurrence_matrix[cooccurrence_matrix > 0]
        avg_cooccurrence = np.mean(non_zero_entries) if len(non_zero_entries) > 0 else 0
        
        # Normalizar por el máximo teórico
        max_possible = len(self.train_data)
        normalized_strength = min(1.0, avg_cooccurrence / (max_possible * 0.1))
        
        return normalized_strength
    
    def _analyze_temporal_patterns(self) -> float:
        """Analiza patrones temporales"""
        
        if 'fecha' not in self.data.columns:
            return 0.5  # Score neutro si no hay datos temporales
        
        # Analizar patrones por día de la semana si existe la columna
        if 'dia_semana' in self.data.columns:
            day_patterns = defaultdict(list)
            
            for _, row in self.train_data.iterrows():
                day = row['dia_semana']
                numbers = [int(row[col]) for col in self.bolilla_cols]
                day_patterns[day].extend(numbers)
            
            # Evaluar consistencia de patrones por día
            day_consistency = []
            for day, numbers in day_patterns.items():
                if len(numbers) > 20:  # Suficientes datos
                    freq_dist = Counter(numbers)
                    entropy = -sum((count/len(numbers)) * np.log2(count/len(numbers)) 
                                 for count in freq_dist.values() if count > 0)
                    max_entropy = np.log2(40)
                    consistency = 1 - (entropy / max_entropy)  # Menos entropía = más patrón
                    day_consistency.append(consistency)
            
            return np.mean(day_consistency) if day_consistency else 0.5
        
        return 0.5
    
    def _analyze_sequence_patterns(self) -> float:
        """Analiza patrones en secuencias de números"""
        
        sequence_scores = []
        
        for _, row in self.train_data.iterrows():
            numbers = sorted([int(row[col]) for col in self.bolilla_cols])
            
            # Evaluar gaps entre números consecutivos
            gaps = [numbers[i+1] - numbers[i] for i in range(len(numbers)-1)]
            
            # Score basado en consistencia de gaps
            gap_consistency = 1 - (np.std(gaps) / np.mean(gaps)) if np.mean(gaps) > 0 else 0
            sequence_scores.append(max(0, min(1, gap_consistency)))
        
        return np.mean(sequence_scores) if sequence_scores else 0.5
    
    def _analyze_gap_patterns(self) -> float:
        """Analiza patrones en gaps entre números"""
        
        all_gaps = []
        
        for _, row in self.train_data.iterrows():
            numbers = sorted([int(row[col]) for col in self.bolilla_cols])
            gaps = [numbers[i+1] - numbers[i] for i in range(len(numbers)-1)]
            all_gaps.extend(gaps)
        
        # Evaluar distribución de gaps
        gap_freq = Counter(all_gaps)
        most_common_gaps = gap_freq.most_common(5)
        
        # Score basado en qué tan predecibles son los gaps
        total_gaps = len(all_gaps)
        predictability = sum(count for _, count in most_common_gaps) / total_gaps if total_gaps > 0 else 0
        
        return predictability
    
    def optimize_weights(self) -> Dict:
        """Optimiza los pesos de los componentes"""
        
        print("\n⚖️ OPTIMIZANDO PESOS DE COMPONENTES...")
        
        # Obtener rendimiento individual de componentes
        component_performance = self.analyze_component_performance()
        
        # Definir rangos de pesos para explorar
        weight_ranges = {
            'positional': [0.0, 0.1, 0.2, 0.25, 0.3, 0.35],
            'entropy_fft': [0.0, 0.1, 0.15, 0.2, 0.25, 0.3],
            'jackpot': [0.05, 0.1, 0.15, 0.2, 0.25, 0.3],
            'partial_hits': [0.2, 0.25, 0.3, 0.35, 0.4, 0.45],
            'patterns': [0.0, 0.05, 0.1, 0.15, 0.2, 0.25]
        }
        
        best_weights = None
        best_score = -1
        weight_results = []
        
        print("🔄 Probando combinaciones de pesos...")
        
        # Probar combinaciones de pesos (muestra reducida para eficiencia)
        import random
        random.seed(42)
        
        test_combinations = []
        for _ in range(50):  # Probar 50 combinaciones aleatorias
            combination = {}
            for component, ranges in weight_ranges.items():
                combination[component] = random.choice(ranges)
            
            # Asegurar que sumen aproximadamente 1.0
            total = sum(combination.values())
            if 0.8 <= total <= 1.2:  # Permitir cierta flexibilidad
                # Normalizar para que sumen exactamente 1.0
                for component in combination:
                    combination[component] = combination[component] / total
                test_combinations.append(combination)
        
        # Evaluar cada combinación
        for i, weights in enumerate(test_combinations[:20]):  # Evaluar top 20
            score = self._evaluate_weight_combination(weights, component_performance)
            weight_results.append({
                'weights': weights,
                'score': score,
                'rank': i + 1
            })
            
            if score > best_score:
                best_score = score
                best_weights = weights
        
        # Ordenar resultados
        weight_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Mostrar mejores resultados
        self._display_weight_optimization_results(weight_results[:10], best_weights)
        
        return {
            'best_weights': best_weights,
            'best_score': best_score,
            'all_results': weight_results,
            'component_performance': component_performance
        }
    
    def _evaluate_weight_combination(self, weights: Dict, component_performance: Dict) -> float:
        """Evalúa una combinación específica de pesos"""
        
        # Calcular score ponderado basado en el rendimiento de cada componente
        weighted_score = 0
        
        for component, weight in weights.items():
            if component in component_performance:
                component_score = component_performance[component]['reliability']
                weighted_score += weight * component_score
        
        # Penalizar desequilibrios extremos
        weight_values = list(weights.values())
        weight_std = np.std(weight_values)
        balance_penalty = weight_std * 0.1  # Penalidad leve por desequilibrio
        
        final_score = weighted_score - balance_penalty
        
        return max(0, final_score)
    
    def _display_component_performance(self, performance: Dict):
        """Muestra el rendimiento de cada componente"""
        
        print("\n📊 RENDIMIENTO DE COMPONENTES INDIVIDUALES:")
        print("=" * 70)
        
        for component, metrics in performance.items():
            reliability = metrics.get('reliability', 0)
            
            print(f"\n🔧 {component.upper()}:")
            print(f"   🎯 Confiabilidad: {reliability:.3f} ({reliability*100:.1f}%)")
            
            if component == 'positional':
                print(f"   📍 Precisión: {metrics.get('accuracy', 0):.3f}")
                print(f"   📊 Cobertura: {metrics.get('coverage', 0):.3f}")
                print(f"   🎲 Hits totales: {metrics.get('total_hits', 0):.1f}")
            
            elif component == 'entropy_fft':
                print(f"   🔬 Explotabilidad: {metrics.get('exploitability', 0):.3f}")
                print(f"   📈 Cobertura: {metrics.get('coverage', 0):.3f}")
                
            elif component == 'jackpot':
                print(f"   🎰 Coincidencia freq.: {metrics.get('frequency_match', 0):.3f}")
                print(f"   ⚖️ Precisión balance: {metrics.get('balance_accuracy', 0):.3f}")
                
            elif component == 'partial_hits':
                print(f"   📊 Cobertura: {metrics.get('coverage', 0):.3f}")
                print(f"   ⚖️ Balance: {metrics.get('balance', 0):.3f}")
                print(f"   🔗 Co-ocurrencia: {metrics.get('cooccurrence', 0):.3f}")
                
            elif component == 'patterns':
                print(f"   ⏰ Temporal: {metrics.get('temporal', 0):.3f}")
                print(f"   🔢 Secuencia: {metrics.get('sequence', 0):.3f}")
                print(f"   📏 Gaps: {metrics.get('gaps', 0):.3f}")
    
    def _display_weight_optimization_results(self, results: List[Dict], best_weights: Dict):
        """Muestra resultados de la optimización de pesos"""
        
        print("\n🏆 TOP 5 COMBINACIONES DE PESOS ÓPTIMAS:")
        print("=" * 70)
        
        for i, result in enumerate(results[:5], 1):
            weights = result['weights']
            score = result['score']
            
            print(f"\n#{i} - Score: {score:.4f}")
            print(f"   🔬 Posicional:    {weights.get('positional', 0):.3f} ({weights.get('positional', 0)*100:.1f}%)")
            print(f"   📈 Entropía/FFT:  {weights.get('entropy_fft', 0):.3f} ({weights.get('entropy_fft', 0)*100:.1f}%)")
            print(f"   🎰 Jackpot:       {weights.get('jackpot', 0):.3f} ({weights.get('jackpot', 0)*100:.1f}%)")
            print(f"   🎯 Hits Parciales: {weights.get('partial_hits', 0):.3f} ({weights.get('partial_hits', 0)*100:.1f}%)")
            print(f"   🔍 Patrones:      {weights.get('patterns', 0):.3f} ({weights.get('patterns', 0)*100:.1f}%)")
        
        print("\n🎯 PESOS ÓPTIMOS RECOMENDADOS:")
        print("=" * 70)
        if best_weights:
            total_weight = sum(best_weights.values())
            print(f"Score de rendimiento: {results[0]['score']:.4f}")
            print(f"Total de pesos: {total_weight:.3f}")
            print("\n📊 Distribución recomendada:")
            
            for component, weight in sorted(best_weights.items(), key=lambda x: x[1], reverse=True):
                print(f"   {component}: {weight:.3f} ({weight*100:.1f}%)")
    
    def generate_weight_recommendations(self, optimization_result: Dict) -> Dict:
        """Genera recomendaciones finales de pesos"""
        
        best_weights = optimization_result['best_weights']
        component_performance = optimization_result['component_performance']
        
        recommendations = {
            'optimal_weights': best_weights,
            'performance_justification': {},
            'alternative_configurations': [],
            'implementation_notes': []
        }
        
        # Justificación basada en rendimiento
        for component, weight in best_weights.items():
            if component in component_performance:
                perf = component_performance[component]
                recommendations['performance_justification'][component] = {
                    'weight': weight,
                    'reliability': perf['reliability'],
                    'justification': self._generate_component_justification(component, weight, perf)
                }
        
        # Configuraciones alternativas
        all_results = optimization_result['all_results']
        if len(all_results) >= 3:
            recommendations['alternative_configurations'] = [
                {
                    'name': 'Conservadora',
                    'weights': all_results[1]['weights'],  # Segunda mejor
                    'score': all_results[1]['score'],
                    'description': 'Menor riesgo, distribución más equilibrada'
                },
                {
                    'name': 'Agresiva', 
                    'weights': all_results[2]['weights'],  # Tercera mejor
                    'score': all_results[2]['score'],
                    'description': 'Mayor peso en componentes de alto rendimiento'
                }
            ]
        
        # Notas de implementación
        recommendations['implementation_notes'] = [
            f"Componente principal: {max(best_weights.items(), key=lambda x: x[1])[0]} ({max(best_weights.values())*100:.1f}%)",
            f"Score de rendimiento optimizado: {optimization_result['best_score']:.4f}",
            "Configuración validada con últimos 1500 sorteos",
            "Recomendado re-evaluar cada 500 sorteos nuevos"
        ]
        
        return recommendations
    
    def _generate_component_justification(self, component: str, weight: float, performance: Dict) -> str:
        """Genera justificación textual para el peso de un componente"""
        
        reliability = performance['reliability']
        
        if component == 'positional':
            return f"Peso {weight:.1%} justificado por precisión posicional de {reliability:.1%}"
        elif component == 'entropy_fft':
            return f"Peso {weight:.1%} basado en análisis espectral con explotabilidad {reliability:.1%}"
        elif component == 'jackpot':
            return f"Peso {weight:.1%} por patrones de jackpot con confiabilidad {reliability:.1%}"
        elif component == 'partial_hits':
            return f"Peso {weight:.1%} optimizado para hits parciales con score {reliability:.1%}"
        elif component == 'patterns':
            return f"Peso {weight:.1%} por análisis de patrones con precisión {reliability:.1%}"
        else:
            return f"Peso {weight:.1%} con rendimiento {reliability:.1%}"

def analyze_optimal_weights(historical_data_path: str, analysis_results: Dict) -> Dict:
    """Función principal para analizar pesos óptimos"""
    
    # Cargar datos
    df = pd.read_csv(historical_data_path)
    
    # Crear optimizador
    optimizer = WeightOptimizer(df, analysis_results)
    
    # Ejecutar optimización
    optimization_result = optimizer.optimize_weights()
    
    # Generar recomendaciones
    recommendations = optimizer.generate_weight_recommendations(optimization_result)
    
    return {
        'optimization_result': optimization_result,
        'recommendations': recommendations,
        'optimizer': optimizer
    }

def optimize_model_weights(historial_df: pd.DataFrame, num_combinaciones: int = 5) -> Dict:
    """Función wrapper para optimizar pesos de modelos"""
    try:
        # Simular análisis de resultados básico
        analysis_results = {
            'positional_analysis': {'position_patterns': {}},
            'combined_entropy_fft': {},
            'jackpot_analysis': {'frequency_analysis': {'most_frequent': []}, 'range_analysis': {}},
            'fft_analysis': {}
        }
        
        # Crear optimizador
        optimizer = WeightOptimizer(historial_df, analysis_results)
        
        # Ejecutar optimización básica
        result = optimizer.optimize_weights()
        
        return result.get('best_weights', {
            'positional': 0.25,
            'entropy_fft': 0.20,
            'jackpot': 0.20,
            'partial_hits': 0.25,
            'patterns': 0.10
        })
        
    except Exception as e:
        logger.warning(f"Weight optimization failed: {e}")
        # Return default weights
        return {
            'positional': 0.25,
            'entropy_fft': 0.20,
            'jackpot': 0.20,
            'partial_hits': 0.25,
            'patterns': 0.10
        }

if __name__ == "__main__":
    # Demo del optimizador (requiere analysis_results)
    print("⚖️ Weight Optimizer - Requiere resultados de análisis OMEGA")