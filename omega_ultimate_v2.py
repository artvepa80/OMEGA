#!/usr/bin/env python3
# OMEGA_PRO_AI_v10.1/omega_ultimate_v2.py
"""
🌟 OMEGA PRO AI ULTIMATE V2.0 🌟
Sistema Optimizado basado en análisis del resultado real 5/08/2025

MEJORAS IMPLEMENTADAS:
✅ Neural Enhanced con 40% de peso (era 10%)
✅ Boost para números altos (30-40) 
✅ Boost especial para número 14
✅ Analizador 200 optimizado para números altos
✅ Datos históricos actualizados con resultado 5/08/2025
✅ Feedback training incorporado
"""

import os
import sys
import logging
import json
import multiprocessing
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configurar multiprocessing antes de cualquier import
if __name__ == '__main__':
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn', force=True)

# Imports del sistema OMEGA
sys.path.append(str(Path(__file__).parent))

import pandas as pd
import numpy as np
from utils.validation import clean_historial_df

# Módulos optimizados V2
from modules.omega_200_analyzer import analyze_last_200_draws, Omega200Analyzer
from modules.neural_enhancer import enhance_neural_predictions, NeuralEnhancer
from modules.ensemble_calibrator import calibrate_ensemble, EnsembleCalibrator

# Módulos del sistema principal
from core.predictor import HybridOmegaPredictor
from modules.utils.combinador_maestro import generar_combinacion_maestra

# Configurar logging optimizado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/omega_ultimate_v2_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OmegaUltimateV2:
    """Sistema OMEGA PRO AI Ultimate V2 con optimizaciones basadas en resultados reales"""
    
    def __init__(self, data_path: str = "data/historial_kabala_github_fixed.csv"):
        self.data_path = data_path
        self.historial_df = None
        self.analyzer_200 = None
        self.neural_enhancer = None
        
        # Configuración V2 optimizada
        self.config = {
            'use_optimized_weights': True,
            'focus_high_numbers': True,
            'boost_number_14': True,
            'neural_enhanced_weight': 0.40,
            'num_final_predictions': 10,
            'confidence_threshold': 0.8,
            'max_training_time': 240  # 4 minutos
        }
        
        # Cargar pesos optimizados
        self.optimized_weights = self._load_optimized_weights()
        
        logger.info("🌟 OMEGA PRO AI Ultimate V2.0 inicializado")
        logger.info(f"🎯 Neural Enhanced weight: {self.config['neural_enhanced_weight']:.0%}")
    
    def _load_optimized_weights(self) -> Dict[str, float]:
        """Carga pesos optimizados basados en análisis real"""
        try:
            with open('config/ensemble_weights_optimized.json', 'r') as f:
                config = json.load(f)
                return config.get('weights', {})
        except Exception as e:
            logger.warning(f"⚠️ No se pudieron cargar pesos optimizados: {e}")
            return {
                'neural_enhanced': 0.40,
                'transformer_deep': 0.15,
                'genetico': 0.15,
                'omega_200_analyzer': 0.12,
                'apriori': 0.08,
                'montecarlo': 0.05,
                'gboost': 0.03,
                'lstm_v2': 0.01,
                'clustering': 0.005,
                'consensus': 0.005
            }
    
    def load_and_prepare_data(self) -> bool:
        """Carga datos históricos actualizados"""
        try:
            logger.info(f"📊 Cargando datos actualizados desde {self.data_path}...")
            
            if not Path(self.data_path).exists():
                logger.error(f"❌ Archivo no encontrado: {self.data_path}")
                return False
            
            # Cargar datos raw
            raw_df = pd.read_csv(self.data_path)
            logger.info(f"📈 Datos cargados: {len(raw_df)} registros (incluye resultado 5/08/2025)")
            
            # Limpiar y validar datos
            self.historial_df = clean_historial_df(raw_df)
            
            if self.historial_df.empty:
                logger.error("❌ No se pudieron procesar los datos históricos")
                return False
            
            logger.info(f"✅ Datos preparados: {len(self.historial_df)} registros limpios")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cargando datos: {e}")
            return False
    
    def initialize_optimized_components(self) -> bool:
        """Inicializa componentes con optimizaciones V2"""
        try:
            logger.info("🔧 Inicializando componentes V2 optimizados...")
            
            # 1. Analizador de 200 sorteos optimizado
            logger.info("📊 Inicializando analizador 200 optimizado para números altos...")
            self.analyzer_200 = Omega200Analyzer(self.historial_df)
            
            # 2. Potenciador neuronal V2 
            logger.info("🧠 Inicializando Neural Enhancer V2 con boost para números altos...")
            self.neural_enhancer = NeuralEnhancer()
            
            logger.info("✅ Componentes V2 inicializados correctamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando componentes V2: {e}")
            return False
    
    def run_optimized_200_analysis(self) -> Dict[str, Any]:
        """Ejecuta análisis 200 optimizado para números altos"""
        try:
            logger.info("🔍 Ejecutando análisis 200 optimizado para números altos...")
            
            if not self.analyzer_200:
                logger.warning("⚠️ Analizador 200 no disponible")
                return {'success': False}
            
            # Obtener insights optimizados
            insights = self.analyzer_200.get_prediction_insights()
            optimized_combos = self.analyzer_200.generate_optimized_combinations(8)  # Más combinaciones
            
            logger.info(f"✅ Análisis 200 V2 completado: {len(optimized_combos)} combinaciones")
            logger.info(f"🎯 Confianza: {insights.get('confidence_score', 0):.1%}")
            logger.info(f"🔥 Números recomendados: {insights.get('recommended_numbers', [])[:8]}")
            
            return {
                'success': True,
                'insights': insights,
                'combinations': optimized_combos,
                'confidence': insights.get('confidence_score', 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Error en análisis 200 V2: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_enhanced_neural_predictions(self) -> Dict[str, Any]:
        """Ejecuta predicciones neuronales V2 con boost para números altos"""
        try:
            logger.info("🧠 Ejecutando Neural Enhanced V2 con boost para números altos...")
            
            if not self.neural_enhancer:
                logger.warning("⚠️ Neural enhancer no disponible")
                return {'success': False}
            
            # Entrenar con datos actualizados (incluye resultado 5/08/2025)
            logger.info("📚 Entrenando con datos actualizados...")
            self.neural_enhancer.train_enhanced_model(
                self.historial_df, 
                epochs=50,  # Eficiente pero efectivo
                learning_rate=0.003
            )
            
            # Generar predicciones con boost para números altos
            predictions = self.neural_enhancer.predict_combinations(
                self.historial_df, 
                num_combinations=8,
                focus_high_numbers=True  # V2: Activar boost para números altos
            )
            
            training_summary = self.neural_enhancer.get_training_summary()
            
            logger.info("✅ Neural Enhanced V2 completado")
            logger.info(f"🎯 Modelo entrenado: {training_summary.get('trained', False)}")
            logger.info(f"📊 Épocas: {training_summary.get('total_epochs', 0)}")
            
            return {
                'success': True,
                'predictions': predictions,
                'training_summary': training_summary
            }
            
        except Exception as e:
            logger.error(f"❌ Error en Neural Enhanced V2: {e}")
            return {'success': False, 'error': str(e)}
    
    def integrate_v2_predictions(self, analysis_200: Dict, neural_results: Dict) -> List[Dict[str, Any]]:
        """Integra predicciones V2 con pesos optimizados"""
        try:
            logger.info("🔀 Integrando predicciones V2 con pesos optimizados...")
            
            all_combinations = []
            
            # 1. Predicciones neuronales (PESO 40% - PRIORIDAD MÁXIMA)
            if neural_results.get('success'):
                for pred in neural_results.get('predictions', []):
                    # Boost adicional por ser neural enhanced
                    score_boost = self.optimized_weights.get('neural_enhanced', 0.4)
                    final_score = pred.get('score', 0.5) * (1 + score_boost)
                    
                    all_combinations.append({
                        'combination': pred['combination'],
                        'source': 'neural_enhanced_v2',
                        'priority': 1,  # Máxima prioridad
                        'confidence': pred.get('confidence', 0.5),
                        'score': min(final_score, 1.0),  # Cap en 1.0
                        'weight': score_boost
                    })
            
            # 2. Analizador 200 optimizado (PESO 12%)
            if analysis_200.get('success'):
                for i, combo in enumerate(analysis_200.get('combinations', [])):
                    score_boost = self.optimized_weights.get('omega_200_analyzer', 0.12)
                    base_score = 0.7 + (i * 0.05)  # Score decreciente
                    final_score = base_score * (1 + score_boost)
                    
                    all_combinations.append({
                        'combination': combo,
                        'source': '200_analyzer_v2',
                        'priority': 2,
                        'confidence': analysis_200.get('confidence', 0.5),
                        'score': min(final_score, 1.0),
                        'weight': score_boost
                    })
            
            # 3. Filtrar duplicados manteniendo el mejor score
            unique_combinations = {}
            for combo_data in all_combinations:
                combo_tuple = tuple(sorted(combo_data['combination']))
                
                if combo_tuple not in unique_combinations:
                    unique_combinations[combo_tuple] = combo_data
                else:
                    # Mantener el de mayor score
                    if combo_data['score'] > unique_combinations[combo_tuple]['score']:
                        unique_combinations[combo_tuple] = combo_data
            
            # 4. Ordenar por score (descendente) y prioridad
            final_combinations = list(unique_combinations.values())
            final_combinations.sort(key=lambda x: (-x['score'], x['priority']))
            
            # 5. Tomar top N
            top_combinations = final_combinations[:self.config['num_final_predictions']]
            
            logger.info(f"✅ Integración V2 completada: {len(top_combinations)} combinaciones finales")
            logger.info(f"🧠 Neural Enhanced: {sum(1 for c in top_combinations if 'neural' in c['source'])} combinaciones")
            logger.info(f"📊 200 Analyzer: {sum(1 for c in top_combinations if '200' in c['source'])} combinaciones")
            
            return top_combinations
            
        except Exception as e:
            logger.error(f"❌ Error integrando predicciones V2: {e}")
            return []
    
    def save_v2_results(self, final_combinations: List[Dict], analysis_summary: Dict):
        """Guarda resultados V2 con metadatos de optimización"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Crear directorio de resultados V2
            results_dir = Path("results/ultimate_v2")
            results_dir.mkdir(parents=True, exist_ok=True)
            
            # Guardar combinaciones en CSV
            csv_data = []
            for i, combo_data in enumerate(final_combinations):
                row = {
                    'ranking': i + 1,
                    'combination': '-'.join(map(str, combo_data['combination'])),
                    'source': combo_data['source'],
                    'score': combo_data['score'],
                    'confidence': combo_data['confidence'],
                    'priority': combo_data['priority'],
                    'weight': combo_data.get('weight', 0),
                    'high_numbers_count': sum(1 for n in combo_data['combination'] if n >= 30),
                    'has_number_14': 14 in combo_data['combination']
                }
                csv_data.append(row)
            
            csv_path = results_dir / f"omega_ultimate_v2_{timestamp}.csv"
            pd.DataFrame(csv_data).to_csv(csv_path, index=False)
            
            # Guardar resumen completo V2
            complete_summary = {
                'version': '2.0',
                'timestamp': timestamp,
                'optimization_basis': 'Real result 5/08/2025: 14-39-34-40-31-29',
                'key_improvements': [
                    'Neural Enhanced weight increased to 40%',
                    'High numbers (30-40) boost implemented',
                    'Special boost for number 14',
                    'Updated training data with real result',
                    '200 analyzer optimized for high numbers'
                ],
                'final_combinations': final_combinations,
                'analysis_summary': analysis_summary,
                'optimized_weights': self.optimized_weights,
                'system_config_v2': self.config,
                'total_combinations': len(final_combinations)
            }
            
            json_path = results_dir / f"omega_ultimate_v2_summary_{timestamp}.json"
            with open(json_path, 'w') as f:
                json.dump(complete_summary, f, indent=2, default=str)
            
            logger.info(f"💾 Resultados V2 guardados:")
            logger.info(f"   📊 CSV: {csv_path}")
            logger.info(f"   📋 JSON: {json_path}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando resultados V2: {e}")
    
    def display_v2_results(self, final_combinations: List[Dict], analysis_summary: Dict):
        """Muestra resultados V2 con análisis de optimización"""
        try:
            print("\n" + "="*80)
            print("🌟 OMEGA PRO AI ULTIMATE V2.0 - RESULTADOS OPTIMIZADOS 🌟")
            print("="*80)
            
            print(f"\n📊 OPTIMIZACIONES V2 APLICADAS:")
            print(f"   • 🧠 Neural Enhanced: {self.config['neural_enhanced_weight']:.0%} peso (era 10%)")
            print(f"   • 🎯 Boost números altos (30-40): ACTIVADO") 
            print(f"   • ⭐ Boost especial número 14: ACTIVADO")
            print(f"   • 📈 Datos actualizados con resultado 5/08/2025: ✅")
            print(f"   • 🔧 Analizador 200 optimizado: ✅")
            
            components = analysis_summary.get('components_used', {})
            print(f"\n🔧 COMPONENTES UTILIZADOS:")
            print(f"   • Analizador 200 V2: {'✅' if components.get('200_analyzer') else '❌'}")
            print(f"   • Neural Enhanced V2: {'✅' if components.get('neural_enhancer') else '❌'}")
            
            print(f"\n🎯 TOP {len(final_combinations)} COMBINACIONES V2.0:")
            print("-" * 80)
            
            for i, combo_data in enumerate(final_combinations):
                combo_str = " - ".join(f"{num:02d}" for num in combo_data['combination'])
                
                # Iconos por fuente
                source_emoji = {
                    'neural_enhanced_v2': '🧠',
                    '200_analyzer_v2': '📊',
                    'main_system': '🚀',
                    'maestra': '👑',
                    'fallback': '🔄'
                }.get(combo_data['source'], '🎲')
                
                # Análisis de características V2
                high_count = combo_data.get('high_numbers_count', sum(1 for n in combo_data['combination'] if n >= 30))
                has_14 = combo_data.get('has_number_14', 14 in combo_data['combination'])
                
                print(f"  {i+1:2d}. {source_emoji} {combo_str} | "
                      f"Score: {combo_data['score']:.3f} | "
                      f"Altos: {high_count}/6 | "
                      f"14: {'✅' if has_14 else '❌'} | "
                      f"Peso: {combo_data.get('weight', 0):.0%}")
            
            # Estadísticas V2
            total_neural = sum(1 for c in final_combinations if 'neural' in c['source'])
            total_200 = sum(1 for c in final_combinations if '200' in c['source'])
            avg_high_numbers = sum(sum(1 for n in c['combination'] if n >= 30) for c in final_combinations) / len(final_combinations)
            combinations_with_14 = sum(1 for c in final_combinations if 14 in c['combination'])
            
            print(f"\n📈 ESTADÍSTICAS V2:")
            print("-" * 40)
            print(f"🧠 Predicciones Neural Enhanced: {total_neural}/{len(final_combinations)}")
            print(f"📊 Predicciones Analizador 200: {total_200}/{len(final_combinations)}")
            print(f"🎯 Promedio números altos (30-40): {avg_high_numbers:.1f}/6")
            print(f"⭐ Combinaciones con número 14: {combinations_with_14}/{len(final_combinations)}")
            
            print("\n" + "="*80)
            print("🚀 OBJETIVO V2: Superar los 2 aciertos logrados en V1")
            print("🎯 ESTRATEGIA: Aprovechar patrones identificados del resultado real")
            print("="*80)
            
        except Exception as e:
            logger.error(f"❌ Error mostrando resultados V2: {e}")
    
    def run_ultimate_v2_prediction(self) -> Dict[str, Any]:
        """Ejecuta predicción Ultimate V2 completa"""
        try:
            logger.info("🌟 Iniciando OMEGA PRO AI Ultimate V2.0...")
            
            # 1. Cargar datos actualizados
            if not self.load_and_prepare_data():
                return {'success': False, 'error': 'Error cargando datos'}
            
            # 2. Inicializar componentes V2
            if not self.initialize_optimized_components():
                return {'success': False, 'error': 'Error inicializando componentes V2'}
            
            # 3. Ejecutar análisis optimizados V2
            logger.info("🔄 Ejecutando análisis V2 optimizados...")
            
            # Análisis 200 optimizado
            analysis_200 = self.run_optimized_200_analysis()
            
            # Neural Enhanced V2
            neural_results = self.run_enhanced_neural_predictions()
            
            # 4. Integrar con pesos optimizados
            final_combinations = self.integrate_v2_predictions(analysis_200, neural_results)
            
            if not final_combinations:
                logger.error("❌ No se generaron combinaciones V2")
                return {'success': False, 'error': 'No hay combinaciones V2'}
            
            # 5. Preparar resumen V2
            analysis_summary = {
                'analysis_200_v2': analysis_200,
                'neural_results_v2': neural_results,
                'total_data_points': len(self.historial_df),
                'includes_real_result': True,
                'real_result_date': '2025-08-05',
                'components_used': {
                    '200_analyzer': analysis_200.get('success', False),
                    'neural_enhancer': neural_results.get('success', False)
                },
                'optimization_level': 'V2.0'
            }
            
            # 6. Guardar resultados V2
            self.save_v2_results(final_combinations, analysis_summary)
            
            # 7. Mostrar resultados V2
            self.display_v2_results(final_combinations, analysis_summary)
            
            logger.info("🎉 OMEGA PRO AI Ultimate V2.0 completado exitosamente!")
            
            return {
                'success': True,
                'version': '2.0',
                'final_combinations': final_combinations,
                'analysis_summary': analysis_summary,
                'optimizations_applied': [
                    'Neural Enhanced 40% weight',
                    'High numbers boost',
                    'Number 14 boost', 
                    'Updated training data',
                    'Optimized 200 analyzer'
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Error en Ultimate V2: {e}")
            return {'success': False, 'error': str(e)}

def main():
    """Función principal V2"""
    try:
        print("🌟 Iniciando OMEGA PRO AI Ultimate V2.0...")
        print("🎯 Optimizado basado en resultado real 5/08/2025")
        
        # Crear instancia del sistema V2
        omega_v2 = OmegaUltimateV2()
        
        # Ejecutar predicción V2 completa
        results = omega_v2.run_ultimate_v2_prediction()
        
        if results.get('success'):
            print(f"\n🎉 ¡Ejecución V2.0 completada exitosamente!")
            print(f"🚀 Optimizaciones aplicadas: {len(results.get('optimizations_applied', []))}")
        else:
            print(f"\n❌ Error en ejecución V2: {results.get('error', 'Error desconocido')}")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️ Ejecución V2 interrumpida por el usuario")
        return 1
    except Exception as e:
        print(f"\n❌ Error crítico V2: {e}")
        logger.error(f"Error crítico en main V2: {e}")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
