#!/usr/bin/env python3
# OMEGA_PRO_AI_v10.1/omega_ultimate.py
"""
🌟 OMEGA PRO AI ULTIMATE 🌟
Sistema de Predicción de Lotería con IA Avanzada
Integra todas las optimizaciones y mejoras más recientes

Características:
- Análisis específico de últimos 200 sorteos
- Redes neuronales mejoradas con atención y LSTM
- Calibración automática del ensemble
- Eliminación de warnings de multiprocessing
- Predicciones optimizadas para máxima precisión
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

# Nuevos módulos optimizados
from modules.omega_200_analyzer import analyze_last_200_draws, Omega200Analyzer
from modules.neural_enhancer import enhance_neural_predictions, NeuralEnhancer
from modules.ensemble_calibrator import calibrate_ensemble, EnsembleCalibrator

# Módulos del sistema principal
from core.predictor import HybridOmegaPredictor
from modules.utils.combinador_maestro import generar_combinacion_maestra
from utils.viabilidad import calcular_svi

# Configurar logging optimizado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/omega_ultimate_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OmegaUltimate:
    """Sistema OMEGA PRO AI Ultimate con todas las optimizaciones"""
    
    def __init__(self, data_path: str = "data/historial_kabala_github_fixed.csv"):
        self.data_path = data_path
        self.historial_df = None
        self.analyzer_200 = None
        self.neural_enhancer = None
        self.ensemble_calibrator = None
        self.predictor = None
        
        # Configuración optimizada
        self.config = {
            'use_200_analysis': True,
            'use_neural_enhancement': True,
            'use_ensemble_calibration': True,
            'num_final_predictions': 10,
            'confidence_threshold': 0.7,
            'max_training_time': 300  # 5 minutos máximo
        }
        
        logger.info("🌟 OMEGA PRO AI Ultimate inicializado")
    
    def load_and_prepare_data(self) -> bool:
        """Carga y prepara los datos históricos"""
        try:
            logger.info(f"📊 Cargando datos desde {self.data_path}...")
            
            if not Path(self.data_path).exists():
                logger.error(f"❌ Archivo no encontrado: {self.data_path}")
                return False
            
            # Cargar datos raw
            raw_df = pd.read_csv(self.data_path)
            logger.info(f"📈 Datos cargados: {len(raw_df)} registros")
            
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
    
    def initialize_components(self) -> bool:
        """Inicializa todos los componentes optimizados"""
        try:
            logger.info("🔧 Inicializando componentes optimizados...")
            
            # 1. Analizador de 200 sorteos
            if self.config['use_200_analysis']:
                logger.info("📊 Inicializando analizador de 200 sorteos...")
                self.analyzer_200 = Omega200Analyzer(self.historial_df)
            
            # 2. Potenciador neuronal
            if self.config['use_neural_enhancement']:
                logger.info("🧠 Inicializando potenciador neuronal...")
                self.neural_enhancer = NeuralEnhancer()
            
            # 3. Calibrador del ensemble
            if self.config['use_ensemble_calibration']:
                logger.info("⚖️ Inicializando calibrador del ensemble...")
                self.ensemble_calibrator = EnsembleCalibrator()
            
            # 4. Predictor principal (optimizado)
            logger.info("🚀 Inicializando predictor principal...")
            self.predictor = HybridOmegaPredictor(
                data_path=self.data_path,
                historial_df=self.historial_df,
                cantidad_final=self.config['num_final_predictions'],
                perfil_svi='default'
            )
            
            logger.info("✅ Todos los componentes inicializados correctamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando componentes: {e}")
            return False
    
    def run_200_analysis(self) -> Dict[str, Any]:
        """Ejecuta análisis específico de últimos 200 sorteos"""
        try:
            logger.info("🔍 Ejecutando análisis de últimos 200 sorteos...")
            
            if not self.analyzer_200:
                logger.warning("⚠️ Analizador 200 no disponible")
                return {'success': False}
            
            # Obtener insights y combinaciones optimizadas
            insights = self.analyzer_200.get_prediction_insights()
            optimized_combos = self.analyzer_200.generate_optimized_combinations(5)
            
            logger.info(f"✅ Análisis 200 completado: {len(optimized_combos)} combinaciones generadas")
            logger.info(f"🎯 Confianza del análisis: {insights.get('confidence_score', 0):.1%}")
            
            return {
                'success': True,
                'insights': insights,
                'combinations': optimized_combos,
                'confidence': insights.get('confidence_score', 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Error en análisis 200: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_neural_enhancement(self) -> Dict[str, Any]:
        """Ejecuta predicciones neuronales mejoradas"""
        try:
            logger.info("🧠 Ejecutando predicciones neuronales mejoradas...")
            
            if not self.neural_enhancer:
                logger.warning("⚠️ Potenciador neuronal no disponible")
                return {'success': False}
            
            # Entrenar y predecir con tiempo límite
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Tiempo de entrenamiento excedido")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.config['max_training_time'])
            
            try:
                # Entrenar modelo
                self.neural_enhancer.train_enhanced_model(
                    self.historial_df, 
                    epochs=60,  # Reducido para evitar timeout
                    learning_rate=0.002
                )
                
                # Generar predicciones
                predictions = self.neural_enhancer.predict_combinations(
                    self.historial_df, 
                    num_combinations=5
                )
                
                signal.alarm(0)  # Cancelar alarma
                
                training_summary = self.neural_enhancer.get_training_summary()
                
                logger.info("✅ Predicciones neuronales completadas")
                logger.info(f"🎯 Modelo entrenado: {training_summary.get('trained', False)}")
                
                return {
                    'success': True,
                    'predictions': predictions,
                    'training_summary': training_summary
                }
                
            except TimeoutError:
                logger.warning("⏰ Timeout en entrenamiento neuronal, usando fallback")
                signal.alarm(0)
                return {'success': False, 'error': 'timeout'}
            
        except Exception as e:
            logger.error(f"❌ Error en predicciones neuronales: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_ensemble_calibration(self) -> Dict[str, Any]:
        """Ejecuta calibración del ensemble"""
        try:
            logger.info("⚖️ Ejecutando calibración del ensemble...")
            
            if not self.ensemble_calibrator:
                logger.warning("⚠️ Calibrador del ensemble no disponible")
                return {'success': False}
            
            # Calibrar pesos
            optimized_weights = self.ensemble_calibrator.calibrate_weights(self.historial_df)
            summary = self.ensemble_calibrator.get_calibration_summary()
            
            logger.info("✅ Calibración del ensemble completada")
            logger.info(f"🏆 Mejor modelo: {summary.get('calibration_metrics', {}).get('best_model', 'N/A')}")
            
            return {
                'success': True,
                'weights': optimized_weights,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"❌ Error en calibración del ensemble: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_main_prediction(self) -> Dict[str, Any]:
        """Ejecuta predicción principal del sistema"""
        try:
            logger.info("🚀 Ejecutando predicción principal...")
            
            if not self.predictor:
                logger.error("❌ Predictor principal no disponible")
                return {'success': False}
            
            # Ejecutar predicción principal
            main_results = self.predictor.predecir()
            
            if not main_results:
                logger.warning("⚠️ Predicción principal retornó resultados vacíos")
                return {'success': False}
            
            logger.info(f"✅ Predicción principal completada: {len(main_results)} combinaciones")
            
            return {
                'success': True,
                'results': main_results
            }
            
        except Exception as e:
            logger.error(f"❌ Error en predicción principal: {e}")
            return {'success': False, 'error': str(e)}
    
    def integrate_all_predictions(self, analysis_200: Dict, neural_results: Dict, 
                                 calibration_results: Dict, main_results: Dict) -> List[Dict[str, Any]]:
        """Integra todas las predicciones en un resultado final optimizado"""
        try:
            logger.info("🔀 Integrando todas las predicciones...")
            
            all_combinations = []
            
            # 1. Añadir combinaciones del análisis 200 (alta prioridad)
            if analysis_200.get('success'):
                for i, combo in enumerate(analysis_200.get('combinations', [])):
                    all_combinations.append({
                        'combination': combo,
                        'source': '200_analyzer',
                        'priority': 1,
                        'confidence': analysis_200.get('confidence', 0.5),
                        'score': 0.8 + (analysis_200.get('confidence', 0) * 0.2)
                    })
            
            # 2. Añadir predicciones neuronales (alta prioridad)
            if neural_results.get('success'):
                for pred in neural_results.get('predictions', []):
                    all_combinations.append({
                        'combination': pred['combination'],
                        'source': 'neural_enhanced',
                        'priority': 1,
                        'confidence': pred.get('confidence', 0.5),
                        'score': pred.get('score', 0.5)
                    })
            
            # 3. Añadir resultados principales (prioridad media)
            if main_results.get('success'):
                for result in main_results.get('results', []):
                    all_combinations.append({
                        'combination': result.get('combination', result.get('combinacion', [])),
                        'source': result.get('source', 'main_system'),
                        'priority': 2,
                        'confidence': 0.6,
                        'score': result.get('score', 0.5)
                    })
            
            # 4. Filtrar duplicados y rankear
            unique_combinations = {}
            for combo_data in all_combinations:
                combo_tuple = tuple(sorted(combo_data['combination']))
                
                if combo_tuple not in unique_combinations:
                    unique_combinations[combo_tuple] = combo_data
                else:
                    # Mantener el de mayor score
                    if combo_data['score'] > unique_combinations[combo_tuple]['score']:
                        unique_combinations[combo_tuple] = combo_data
            
            # 5. Ordenar por score y prioridad
            final_combinations = list(unique_combinations.values())
            final_combinations.sort(key=lambda x: (x['priority'], -x['score']))
            
            # 6. Tomar top N
            top_combinations = final_combinations[:self.config['num_final_predictions']]
            
            logger.info(f"✅ Integración completada: {len(top_combinations)} combinaciones finales")
            
            return top_combinations
            
        except Exception as e:
            logger.error(f"❌ Error integrando predicciones: {e}")
            return []
    
    def save_results(self, final_combinations: List[Dict], analysis_summary: Dict):
        """Guarda los resultados finales"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Crear directorio de resultados
            results_dir = Path("results/ultimate")
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
                    'priority': combo_data['priority']
                }
                csv_data.append(row)
            
            csv_path = results_dir / f"omega_ultimate_{timestamp}.csv"
            pd.DataFrame(csv_data).to_csv(csv_path, index=False)
            
            # Guardar resumen completo en JSON
            complete_summary = {
                'timestamp': timestamp,
                'final_combinations': final_combinations,
                'analysis_summary': analysis_summary,
                'system_config': self.config,
                'total_combinations': len(final_combinations)
            }
            
            json_path = results_dir / f"omega_ultimate_summary_{timestamp}.json"
            with open(json_path, 'w') as f:
                json.dump(complete_summary, f, indent=2, default=str)
            
            logger.info(f"💾 Resultados guardados:")
            logger.info(f"   📊 CSV: {csv_path}")
            logger.info(f"   📋 JSON: {json_path}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando resultados: {e}")
    
    def run_ultimate_prediction(self) -> Dict[str, Any]:
        """Ejecuta predicción ultimate completa"""
        try:
            logger.info("🌟 Iniciando OMEGA PRO AI Ultimate...")
            
            # 1. Cargar datos
            if not self.load_and_prepare_data():
                return {'success': False, 'error': 'Error cargando datos'}
            
            # 2. Inicializar componentes
            if not self.initialize_components():
                return {'success': False, 'error': 'Error inicializando componentes'}
            
            # 3. Ejecutar todos los análisis
            logger.info("🔄 Ejecutando análisis avanzados...")
            
            # Análisis de 200 sorteos
            analysis_200 = self.run_200_analysis()
            
            # Predicciones neuronales
            neural_results = self.run_neural_enhancement()
            
            # Calibración del ensemble
            calibration_results = self.run_ensemble_calibration()
            
            # Predicción principal
            main_results = self.run_main_prediction()
            
            # 4. Integrar todas las predicciones
            final_combinations = self.integrate_all_predictions(
                analysis_200, neural_results, calibration_results, main_results
            )
            
            if not final_combinations:
                logger.error("❌ No se generaron combinaciones finales")
                return {'success': False, 'error': 'No hay combinaciones'}
            
            # 5. Preparar resumen
            analysis_summary = {
                'analysis_200': analysis_200,
                'neural_results': neural_results,
                'calibration_results': calibration_results,
                'main_results': main_results,
                'total_data_points': len(self.historial_df),
                'components_used': {
                    '200_analyzer': analysis_200.get('success', False),
                    'neural_enhancer': neural_results.get('success', False),
                    'ensemble_calibrator': calibration_results.get('success', False),
                    'main_predictor': main_results.get('success', False)
                }
            }
            
            # 6. Guardar resultados
            self.save_results(final_combinations, analysis_summary)
            
            # 7. Mostrar resultados finales
            self.display_final_results(final_combinations, analysis_summary)
            
            logger.info("🎉 OMEGA PRO AI Ultimate completado exitosamente!")
            
            return {
                'success': True,
                'final_combinations': final_combinations,
                'analysis_summary': analysis_summary
            }
            
        except Exception as e:
            logger.error(f"❌ Error en predicción ultimate: {e}")
            return {'success': False, 'error': str(e)}
    
    def display_final_results(self, final_combinations: List[Dict], analysis_summary: Dict):
        """Muestra los resultados finales en consola"""
        try:
            print("\n" + "="*80)
            print("🌟 OMEGA PRO AI ULTIMATE - RESULTADOS FINALES 🌟")
            print("="*80)
            
            print(f"\n📊 RESUMEN DEL ANÁLISIS:")
            print(f"   • Total de registros históricos: {analysis_summary.get('total_data_points', 'N/A')}")
            
            components = analysis_summary.get('components_used', {})
            print(f"   • Analizador 200 sorteos: {'✅' if components.get('200_analyzer') else '❌'}")
            print(f"   • Potenciador neuronal: {'✅' if components.get('neural_enhancer') else '❌'}")
            print(f"   • Calibrador ensemble: {'✅' if components.get('ensemble_calibrator') else '❌'}")
            print(f"   • Predictor principal: {'✅' if components.get('main_predictor') else '❌'}")
            
            print(f"\n🎯 TOP {len(final_combinations)} COMBINACIONES ULTIMATE:")
            print("-" * 80)
            
            for i, combo_data in enumerate(final_combinations):
                combo_str = " - ".join(f"{num:02d}" for num in combo_data['combination'])
                source_emoji = {
                    '200_analyzer': '📊',
                    'neural_enhanced': '🧠',
                    'main_system': '🚀',
                    'maestra': '👑',
                    'fallback': '🔄'
                }.get(combo_data['source'], '🎲')
                
                print(f"  {i+1:2d}. {source_emoji} {combo_str} | "
                      f"Score: {combo_data['score']:.3f} | "
                      f"Conf: {combo_data['confidence']:.3f} | "
                      f"Fuente: {combo_data['source']}")
            
            print("\n" + "="*80)
            print("🍀 ¡Buena suerte con tus predicciones! 🍀")
            print("="*80)
            
        except Exception as e:
            logger.error(f"❌ Error mostrando resultados: {e}")

def main():
    """Función principal"""
    try:
        print("🌟 Iniciando OMEGA PRO AI Ultimate...")
        
        # Crear instancia del sistema ultimate
        omega_ultimate = OmegaUltimate()
        
        # Ejecutar predicción completa
        results = omega_ultimate.run_ultimate_prediction()
        
        if results.get('success'):
            print("\n🎉 ¡Ejecución completada exitosamente!")
        else:
            print(f"\n❌ Error en ejecución: {results.get('error', 'Error desconocido')}")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️ Ejecución interrumpida por el usuario")
        return 1
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        logger.error(f"Error crítico en main: {e}")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
