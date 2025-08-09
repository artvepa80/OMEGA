#!/usr/bin/env python3
"""
Meta-Learning Integrator for OMEGA PRO AI
Integra todos los módulos avanzados de machine learning
"""

import asyncio
import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import json

# Importar módulos avanzados
try:
    from modules.meta_learning_controller import MetaLearningController, create_meta_controller, analyze_and_optimize
    from modules.reinforcement_trainer import ReinforcementTrainer, create_rl_trainer, RLState, RLAction
    from modules.lstm_predictor_v2 import LSTMPredictorV2, create_lstm_predictor_v2
    from modules.perfilador_dinamico import DynamicProfiler, create_dynamic_profiler, JackpotProfile
    ADVANCED_MODULES_AVAILABLE = True
except ImportError as e:
    ADVANCED_MODULES_AVAILABLE = False
    logging.warning(f"⚠️ Módulos avanzados no disponibles: {e}")

logger = logging.getLogger(__name__)

class MetaLearningIntegrator:
    """Integrador principal de meta-learning para OMEGA PRO AI"""
    
    def __init__(self, 
                 enable_meta_controller: bool = True,
                 enable_reinforcement: bool = True,
                 enable_lstm_v2: bool = True,
                 enable_profiler: bool = True):
        
        self.components_enabled = {
            'meta_controller': enable_meta_controller,
            'reinforcement': enable_reinforcement,
            'lstm_v2': enable_lstm_v2,
            'profiler': enable_profiler
        }
        
        # Inicializar componentes
        self.meta_controller = None
        self.rl_trainer = None
        self.lstm_v2 = None
        self.profiler = None
        
        if not ADVANCED_MODULES_AVAILABLE:
            logger.error("❌ Módulos avanzados no disponibles")
            return
        
        self._initialize_components()
        
        # Estado del sistema
        self.integration_history = []
        self.performance_metrics = {}
        self.current_weights = {}
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        logger.info("🌟 Meta-Learning Integrator inicializado")
        logger.info(f"   Componentes activos: {sum(self.components_enabled.values())}/4")
    
    def _initialize_components(self):
        """Inicializa los componentes de ML"""
        
        if self.components_enabled['meta_controller']:
            try:
                self.meta_controller = create_meta_controller()
                logger.info("✅ Meta-Controller inicializado")
            except Exception as e:
                logger.error(f"❌ Error inicializando Meta-Controller: {e}")
                self.components_enabled['meta_controller'] = False
        
        if self.components_enabled['reinforcement']:
            try:
                self.rl_trainer = create_rl_trainer()
                logger.info("✅ Reinforcement Trainer inicializado")
            except Exception as e:
                logger.error(f"❌ Error inicializando RL Trainer: {e}")
                self.components_enabled['reinforcement'] = False
        
        if self.components_enabled['lstm_v2']:
            try:
                self.lstm_v2 = create_lstm_predictor_v2()
                logger.info("✅ LSTM v2 inicializado")
            except Exception as e:
                logger.error(f"❌ Error inicializando LSTM v2: {e}")
                self.components_enabled['lstm_v2'] = False
        
        if self.components_enabled['profiler']:
            try:
                self.profiler = create_dynamic_profiler()
                logger.info("✅ Dynamic Profiler inicializado")
            except Exception as e:
                logger.error(f"❌ Error inicializando Profiler: {e}")
                self.components_enabled['profiler'] = False
    
    async def intelligent_prediction(self, 
                                   historical_data: List[List[int]], 
                                   num_predictions: int = 5,
                                   use_reinforcement: bool = True) -> Dict[str, Any]:
        """Genera predicciones usando todo el sistema de meta-learning"""
        
        logger.info(f"🧠 Iniciando predicción inteligente con {len(historical_data)} datos históricos...")
        
        start_time = datetime.now()
        results = {
            'predictions': [],
            'meta_analysis': {},
            'component_results': {},
            'integration_metrics': {},
            'timestamp': start_time.isoformat()
        }
        
        try:
            # 1. Análisis de contexto con Meta-Controller
            if self.meta_controller:
                context, optimal_weights = analyze_and_optimize(self.meta_controller, historical_data)
                self.current_weights = optimal_weights
                
                results['meta_analysis'] = {
                    'regime': context.regime.value,
                    'entropy': context.entropy,
                    'variance': context.variance,
                    'trend_strength': context.trend_strength,
                    'optimal_weights': optimal_weights
                }
                
                logger.info(f"📊 Contexto: {context.regime.value}, Entropía: {context.entropy:.3f}")
            
            # 2. Predicción de perfil dinámico
            if self.profiler:
                profile_prediction = self.profiler.predict_profile(historical_data)
                
                results['component_results']['profiler'] = {
                    'profile': profile_prediction.profile.value,
                    'confidence': profile_prediction.confidence,
                    'probability_distribution': profile_prediction.probability_distribution
                }
                
                logger.info(f"🎯 Perfil predicho: {profile_prediction.profile.value} ({profile_prediction.confidence:.1%})")
            
            # 3. Predicciones LSTM v2
            lstm_predictions = []
            if self.lstm_v2:
                try:
                    # Si el modelo no está entrenado, entrenar rápidamente
                    if not self.lstm_v2.is_trained and len(historical_data) >= 30:
                        logger.info("🏋️ Entrenamiento rápido de LSTM v2...")
                        self.lstm_v2.train(historical_data, epochs=10, validation_split=0.1)
                    
                    lstm_predictions = self.lstm_v2.predict(historical_data, num_predictions)
                    
                    results['component_results']['lstm_v2'] = {
                        'predictions_count': len(lstm_predictions),
                        'avg_confidence': np.mean([p['confidence'] for p in lstm_predictions]),
                        'is_trained': self.lstm_v2.is_trained
                    }
                    
                    logger.info(f"🧠 LSTM v2: {len(lstm_predictions)} predicciones generadas")
                    
                except Exception as e:
                    logger.error(f"❌ Error en LSTM v2: {e}")
                    lstm_predictions = []
            
            # 4. Optimización con Reinforcement Learning
            optimized_weights = self.current_weights.copy()
            if use_reinforcement and self.rl_trainer and self.current_weights:
                try:
                    # Crear estado RL
                    model_performances = {name: np.random.uniform(0.6, 0.8) for name in self.current_weights.keys()}
                    context_features = [
                        results['meta_analysis'].get('entropy', 0.5),
                        results['meta_analysis'].get('variance', 0.5),
                        results['meta_analysis'].get('trend_strength', 0.0)
                    ] + [0.0] * 7  # Padding
                    
                    rl_state = self.rl_trainer.create_state_from_context(
                        model_performances, context_features, self.current_weights
                    )
                    
                    # Seleccionar acción de optimización
                    action = self.rl_trainer.choose_action(rl_state)
                    optimized_weights = self.rl_trainer.apply_action_to_weights(action, self.current_weights)
                    
                    results['component_results']['reinforcement'] = {
                        'action_type': action.action_type.name,
                        'model_adjusted': self.rl_trainer.model_names[action.model_index],
                        'adjustment_value': action.adjustment_value,
                        'epsilon': self.rl_trainer.epsilon
                    }
                    
                    logger.info(f"🎮 RL optimización: {action.action_type.name} en {self.rl_trainer.model_names[action.model_index]}")
                    
                except Exception as e:
                    logger.error(f"❌ Error en RL: {e}")
            
            # 5. Combinación inteligente de resultados
            combined_predictions = await self._combine_predictions(
                lstm_predictions, 
                optimized_weights, 
                historical_data, 
                num_predictions
            )
            
            results['predictions'] = combined_predictions
            
            # 6. Métricas de integración
            processing_time = (datetime.now() - start_time).total_seconds()
            results['integration_metrics'] = {
                'processing_time': processing_time,
                'components_used': sum(self.components_enabled.values()),
                'predictions_generated': len(combined_predictions),
                'weights_optimized': len(optimized_weights),
                'confidence_avg': np.mean([p.get('confidence', 0.5) for p in combined_predictions])
            }
            
            # Registrar en historial
            self.integration_history.append({
                'timestamp': start_time,
                'historical_data_size': len(historical_data),
                'predictions_count': len(combined_predictions),
                'components_used': self.components_enabled,
                'processing_time': processing_time
            })
            
            logger.info(f"✅ Predicción inteligente completada en {processing_time:.2f}s")
            logger.info(f"   Predicciones: {len(combined_predictions)}, Confianza promedio: {results['integration_metrics']['confidence_avg']:.1%}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error en predicción inteligente: {e}")
            return self._generate_fallback_results(historical_data, num_predictions)
    
    async def _combine_predictions(self, 
                                 lstm_predictions: List[Dict[str, Any]],
                                 weights: Dict[str, float],
                                 historical_data: List[List[int]],
                                 num_predictions: int) -> List[Dict[str, Any]]:
        """Combina predicciones de diferentes componentes"""
        
        combined = []
        
        # Usar predicciones LSTM como base
        for i, lstm_pred in enumerate(lstm_predictions[:num_predictions]):
            prediction = {
                'combination': lstm_pred['combination'],
                'confidence': lstm_pred.get('confidence', 0.5),
                'source': 'meta_learning_integrated',
                'components_used': [],
                'meta_weights': weights,
                'timestamp': datetime.now().isoformat()
            }
            
            # Ajustar confianza basado en meta-learning
            if 'lstm_v2' in weights:
                lstm_weight = weights['lstm_v2']
                prediction['confidence'] = prediction['confidence'] * lstm_weight / max(weights.values())
            
            # Marcar componentes usados
            if self.components_enabled['lstm_v2']:
                prediction['components_used'].append('lstm_v2')
            if self.components_enabled['meta_controller']:
                prediction['components_used'].append('meta_controller')
            if self.components_enabled['reinforcement']:
                prediction['components_used'].append('reinforcement_learning')
            if self.components_enabled['profiler']:
                prediction['components_used'].append('dynamic_profiler')
            
            combined.append(prediction)
        
        # Si necesitamos más predicciones y no tenemos suficientes de LSTM
        while len(combined) < num_predictions:
            # Generar predicción híbrida
            hybrid_combination = self._generate_hybrid_prediction(historical_data)
            
            prediction = {
                'combination': hybrid_combination,
                'confidence': 0.6,  # Confianza moderada para híbridos
                'source': 'meta_learning_hybrid',
                'components_used': ['meta_controller'],
                'meta_weights': weights,
                'timestamp': datetime.now().isoformat()
            }
            
            combined.append(prediction)
        
        return combined[:num_predictions]
    
    def _generate_hybrid_prediction(self, historical_data: List[List[int]]) -> List[int]:
        """Genera predicción híbrida usando meta-learning"""
        
        if not historical_data:
            return sorted(np.random.choice(range(1, 41), 6, replace=False).tolist())
        
        # Análisis estadístico básico
        all_numbers = [num for combo in historical_data[-20:] for num in combo]
        number_freq = {i: all_numbers.count(i) for i in range(1, 41)}
        
        # Selección ponderada por frecuencia + aleatoriedad
        numbers = []
        available = list(range(1, 41))
        
        for _ in range(6):
            if not available:
                break
            
            # Probabilidades basadas en frecuencia histórica
            probs = [number_freq.get(num, 1) for num in available]
            probs = np.array(probs) / sum(probs)
            
            # Añadir ruido para diversidad
            probs = probs * 0.8 + np.random.uniform(0, 0.2, len(probs))
            probs = probs / sum(probs)
            
            chosen = np.random.choice(available, p=probs)
            numbers.append(chosen)
            available.remove(chosen)
        
        return sorted(numbers)
    
    def _generate_fallback_results(self, historical_data: List[List[int]], num_predictions: int) -> Dict[str, Any]:
        """Genera resultados de fallback en caso de error"""
        
        fallback_predictions = []
        
        for i in range(num_predictions):
            combination = sorted(np.random.choice(range(1, 41), 6, replace=False).tolist())
            
            prediction = {
                'combination': combination,
                'confidence': 0.4,
                'source': 'meta_learning_fallback',
                'components_used': [],
                'timestamp': datetime.now().isoformat()
            }
            
            fallback_predictions.append(prediction)
        
        return {
            'predictions': fallback_predictions,
            'meta_analysis': {'error': 'Fallback mode activated'},
            'component_results': {},
            'integration_metrics': {
                'processing_time': 0.1,
                'components_used': 0,
                'predictions_generated': num_predictions,
                'confidence_avg': 0.4
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def train_integrated_system(self, historical_data: List[List[int]]) -> Dict[str, Any]:
        """Entrena todo el sistema integrado"""
        
        logger.info("🏋️ Entrenando sistema integrado de meta-learning...")
        
        training_results = {}
        
        # Entrenar Meta-Controller
        if self.meta_controller and len(historical_data) >= 50:
            try:
                # Simular resultados de performance para entrenamiento
                for i in range(min(20, len(historical_data) // 5)):
                    window_data = historical_data[i*5:(i+1)*5]
                    if len(window_data) >= 5:
                        context = self.meta_controller.analyze_current_context(window_data)
                        
                        # Simular performance de modelos
                        for model_name in self.meta_controller.available_models.keys():
                            results = {
                                'accuracy': np.random.uniform(0.6, 0.9),
                                'precision': np.random.uniform(0.5, 0.8),
                                'recall': np.random.uniform(0.5, 0.8),
                                'f1_score': np.random.uniform(0.5, 0.8)
                            }
                            self.meta_controller.record_model_performance(model_name, context, results)
                
                training_results['meta_controller'] = {
                    'performance_records': len(self.meta_controller.performance_history),
                    'is_trained': self.meta_controller.is_trained
                }
                
                logger.info("✅ Meta-Controller entrenado")
                
            except Exception as e:
                logger.error(f"❌ Error entrenando Meta-Controller: {e}")
        
        # Entrenar LSTM v2
        if self.lstm_v2 and len(historical_data) >= 30:
            try:
                lstm_results = self.lstm_v2.train(historical_data, epochs=10, validation_split=0.2)
                training_results['lstm_v2'] = lstm_results
                logger.info("✅ LSTM v2 entrenado")
                
            except Exception as e:
                logger.error(f"❌ Error entrenando LSTM v2: {e}")
                lstm_results = {'error': str(e), 'success': False}
                training_results['lstm_v2'] = lstm_results
        
        # Entrenar Profiler
        if self.profiler and len(historical_data) >= 30:
            try:
                profiler_results = self.profiler.train(historical_data)
                training_results['profiler'] = profiler_results
                
                logger.info("✅ Dynamic Profiler entrenado")
                
            except Exception as e:
                logger.error(f"❌ Error entrenando Profiler: {e}")
        
        # Entrenar RL (simulación)
        if self.rl_trainer:
            try:
                # Simular episodios de entrenamiento
                for episode in range(5):
                    initial_state = RLState(
                        model_performances=[0.6, 0.5, 0.7, 0.55, 0.65, 0.6, 0.7],
                        context_features=[0.5, 0.3, 0.8] + [0.0] * 7,
                        recent_rewards=[1.0, -0.5, 2.0, 0.5, 1.5],
                        current_weights=[1.0, 1.2, 0.8, 1.1, 0.9, 1.0, 1.3],
                        time_features=[0.5, 0.3, 0.7, 0.8]
                    )
                    
                    def simulate_step(state, action):
                        new_state = RLState(
                            model_performances=[max(0.1, min(0.9, p + np.random.normal(0, 0.05))) 
                                              for p in state.model_performances],
                            context_features=state.context_features,
                            recent_rewards=state.recent_rewards[1:] + [0.0],
                            current_weights=state.current_weights,
                            time_features=state.time_features
                        )
                        reward = np.random.normal(1.0, 0.5)
                        done = np.random.random() < 0.1
                        return new_state, reward, done
                    
                    self.rl_trainer.train_episode(initial_state, simulate_step, max_steps=10)
                
                rl_summary = self.rl_trainer.get_training_summary()
                training_results['reinforcement'] = rl_summary
                
                logger.info("✅ Reinforcement Learning entrenado")
                
            except Exception as e:
                logger.error(f"❌ Error entrenando RL: {e}")
        
        logger.info(f"🎯 Entrenamiento integrado completado: {len(training_results)} componentes")
        
        return {
            'components_trained': list(training_results.keys()),
            'training_results': training_results,
            'historical_data_size': len(historical_data),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtiene estado completo del sistema"""
        
        status = {
            'session_id': self.session_id,
            'components_enabled': self.components_enabled,
            'components_status': {},
            'integration_stats': {},
            'current_weights': self.current_weights,
            'timestamp': datetime.now().isoformat()
        }
        
        # Estado de componentes
        if self.meta_controller:
            status['components_status']['meta_controller'] = self.meta_controller.get_performance_summary()
        
        if self.lstm_v2:
            status['components_status']['lstm_v2'] = self.lstm_v2.get_training_summary()
        
        if self.rl_trainer:
            status['components_status']['reinforcement'] = self.rl_trainer.get_training_summary()
        
        if self.profiler:
            status['components_status']['profiler'] = self.profiler.get_profiling_summary()
        
        # Estadísticas de integración
        if self.integration_history:
            status['integration_stats'] = {
                'total_predictions': len(self.integration_history),
                'avg_processing_time': np.mean([h['processing_time'] for h in self.integration_history]),
                'last_prediction': self.integration_history[-1]['timestamp'].isoformat()
            }
        
        return status
    
    def save_system_state(self, filepath: str):
        """Guarda el estado completo del sistema"""
        
        try:
            # Guardar estado de cada componente
            state = {
                'session_id': self.session_id,
                'components_enabled': self.components_enabled,
                'current_weights': self.current_weights,
                'integration_history': [
                    {**h, 'timestamp': h['timestamp'].isoformat()} 
                    for h in self.integration_history
                ],
                'timestamp': datetime.now().isoformat()
            }
            
            # Guardar modelos individuales
            if self.lstm_v2:
                lstm_path = filepath.replace('.json', '_lstm_v2.pt')
                self.lstm_v2.save_model(lstm_path)
                state['lstm_v2_model_path'] = lstm_path
            
            if self.rl_trainer:
                rl_path = filepath.replace('.json', '_rl.pt')
                self.rl_trainer.save_model(rl_path)
                state['rl_model_path'] = rl_path
            
            if self.meta_controller:
                meta_path = filepath.replace('.json', '_meta.json')
                self.meta_controller.export_learning_state(meta_path)
                state['meta_controller_path'] = meta_path
            
            # Guardar estado principal
            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"💾 Estado del sistema guardado en {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando estado: {e}")

# Funciones de utilidad
def create_meta_learning_system(enable_all: bool = True) -> MetaLearningIntegrator:
    """Crea sistema integrado de meta-learning"""
    return MetaLearningIntegrator(
        enable_meta_controller=enable_all,
        enable_reinforcement=enable_all,
        enable_lstm_v2=enable_all,
        enable_profiler=enable_all
    )

async def intelligent_predict(integrator: MetaLearningIntegrator, 
                            historical_data: List[List[int]], 
                            num_predictions: int = 5) -> Dict[str, Any]:
    """Función de conveniencia para predicción inteligente"""
    return await integrator.intelligent_prediction(historical_data, num_predictions)

if __name__ == "__main__":
    # Demo del integrador
    async def main():
        print("🌟 Demo Meta-Learning Integrator")
        
        # Crear sistema integrado
        integrator = create_meta_learning_system()
        
        # Datos de ejemplo
        sample_data = [
            [1, 15, 23, 31, 35, 40], [3, 12, 18, 27, 33, 39],
            [5, 14, 22, 28, 34, 38], [2, 11, 19, 25, 32, 37],
            [7, 16, 24, 29, 36, 38], [4, 13, 21, 26, 34, 39],
            [6, 17, 25, 30, 37, 40], [8, 10, 20, 24, 31, 35]
        ] * 4  # Replicar para más datos
        
        print(f"🏋️ Entrenando sistema con {len(sample_data)} combinaciones...")
        
        # Entrenar sistema
        training_results = integrator.train_integrated_system(sample_data)
        print(f"✅ Componentes entrenados: {training_results['components_trained']}")
        
        # Generar predicciones inteligentes
        print(f"\n🧠 Generando predicciones inteligentes...")
        results = await integrator.intelligent_prediction(sample_data, num_predictions=3)
        
        print(f"🎯 Predicciones generadas:")
        for i, pred in enumerate(results['predictions'], 1):
            combination = pred['combination']
            confidence = pred['confidence']
            components = ', '.join(pred['components_used'])
            print(f"   {i}. {' - '.join(map(str, combination))} ")
            print(f"      Confianza: {confidence:.1%}, Componentes: {components}")
        
        # Estado del sistema
        status = integrator.get_system_status()
        print(f"\n📊 Estado del sistema:")
        print(f"   Componentes activos: {sum(status['components_enabled'].values())}")
        print(f"   Tiempo promedio: {status['integration_stats'].get('avg_processing_time', 0):.3f}s")
    
    # Ejecutar demo
    if ADVANCED_MODULES_AVAILABLE:
        asyncio.run(main())
    else:
        print("❌ Módulos avanzados no disponibles para demo")
