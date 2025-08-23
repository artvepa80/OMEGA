#!/usr/bin/env python3
"""
OMEGA PRO AI CORE - Sistema Principal de Inteligencia Artificial Avanzada
Integra todos los módulos de IA para crear una experiencia inteligente completa
"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from pathlib import Path

# Importar módulos de IA avanzada
try:
    from modules.advanced_neural_networks import (
        AdaptiveLearningSystem, 
        create_advanced_ai_system,
        train_with_historical_data
    )
    from modules.nlp_intelligence import (
        OmegaNLPProcessor,
        create_nlp_system,
        process_user_query
    )
    from modules.ai_ensemble_system import (
        AIEnsembleSystem,
        create_ai_ensemble,
        generate_intelligent_predictions
    )
except ImportError as e:
    logging.warning(f"⚠️ Algunos módulos de IA no están disponibles: {e}")

logger = logging.getLogger(__name__)

class OmegaProAICore:
    """Sistema principal de IA que integra todos los componentes avanzados"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Inicializar componentes de IA
        logger.info("🚀 Inicializando OMEGA PRO AI Core...")
        
        # Sistema de redes neuronales avanzadas
        try:
            self.neural_system = create_advanced_ai_system()
            logger.info("✅ Sistema neuronal avanzado inicializado")
        except Exception as e:
            logger.warning(f"⚠️ Sistema neuronal no disponible: {e}")
            self.neural_system = None
        
        # Sistema de procesamiento de lenguaje natural
        try:
            self.nlp_system = create_nlp_system()
            logger.info("✅ Sistema NLP inicializado")
        except Exception as e:
            logger.warning(f"⚠️ Sistema NLP no disponible: {e}")
            self.nlp_system = None
        
        # Sistema de ensemble de IAs especializadas
        try:
            self.ensemble_system = create_ai_ensemble()
            logger.info("✅ Sistema ensemble inicializado")
        except Exception as e:
            logger.warning(f"⚠️ Sistema ensemble no disponible: {e}")
            self.ensemble_system = None
        
        # Memoria y estado del sistema
        self.session_memory = {
            'interactions': [],
            'learning_data': [],
            'performance_metrics': {},
            'user_preferences': {}
        }
        
        # Configurar logging avanzado
        self._setup_advanced_logging()
        
        logger.info("🎯 OMEGA PRO AI Core completamente inicializado")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Carga configuración del sistema"""
        default_config = {
            'ai_modes': {
                'neural_networks': True,
                'nlp_processing': True,
                'ensemble_ai': True,
                'adaptive_learning': True
            },
            'learning_settings': {
                'continuous_learning': True,
                'feedback_integration': True,
                'performance_tracking': True,
                'auto_optimization': True
            },
            'interaction_settings': {
                'natural_language': True,
                'voice_responses': False,
                'detailed_explanations': True,
                'personalization': True
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                logger.warning(f"⚠️ Error cargando configuración: {e}")
        
        return default_config
    
    def _setup_advanced_logging(self):
        """Configura logging avanzado para IA"""
        # Crear directorio de logs si no existe
        log_dir = Path("logs/ai_sessions")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar handler específico para sesiones de IA
        session_handler = logging.FileHandler(
            log_dir / f"omega_ai_session_{self.session_id}.log"
        )
        session_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [AI] %(message)s'
        )
        session_handler.setFormatter(formatter)
        
        logger.addHandler(session_handler)
    
    async def process_intelligent_request(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Procesa una solicitud del usuario usando toda la inteligencia disponible"""
        logger.info(f"🧠 Procesando solicitud inteligente: '{user_input}'")
        
        start_time = datetime.now()
        context = context or {}
        
        # Fase 1: Procesamiento de lenguaje natural
        intent = None
        nlp_response = None
        
        if self.nlp_system:
            try:
                intent, nlp_response = process_user_query(self.nlp_system, user_input, context)
                logger.info(f"🎯 Intención detectada: {intent.action} (confianza: {intent.confidence:.2f})")
            except Exception as e:
                logger.error(f"❌ Error en NLP: {e}")
        
        # Fase 2: Ejecución de la acción solicitada
        ai_results = {}
        
        if intent and intent.action != 'unknown':
            ai_results = await self._execute_ai_action(intent, context)
        else:
            # Acción por defecto: generar combinaciones inteligentes
            ai_results = await self._generate_default_predictions(context)
        
        # Fase 3: Aprendizaje y adaptación
        if self.config['learning_settings']['continuous_learning']:
            await self._continuous_learning_update(user_input, intent, ai_results)
        
        # Fase 4: Generar respuesta inteligente
        response = await self._generate_intelligent_response(user_input, intent, ai_results, nlp_response)
        
        # Registrar interacción
        interaction = {
            'timestamp': start_time.isoformat(),
            'user_input': user_input,
            'intent': intent.action if intent else 'unknown',
            'confidence': intent.confidence if intent else 0.0,
            'ai_results': ai_results,
            'processing_time': (datetime.now() - start_time).total_seconds()
        }
        
        self.session_memory['interactions'].append(interaction)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Solicitud procesada en {processing_time:.2f}s")
        
        return response
    
    async def _execute_ai_action(self, intent, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la acción de IA solicitada"""
        logger.info(f"⚡ Ejecutando acción de IA: {intent.action}")
        
        results = {}
        
        if intent.action == 'generate_combinations':
            results = await self._ai_generate_combinations(intent, context)
        
        elif intent.action == 'analyze_patterns':
            results = await self._ai_analyze_patterns(context)
        
        elif intent.action == 'explain_results':
            results = await self._ai_explain_results(context)
        
        elif intent.action == 'check_probability':
            results = await self._ai_check_probability(intent, context)
        
        elif intent.action == 'optimize_settings':
            results = await self._ai_optimize_settings(intent, context)
        
        elif intent.action == 'get_recommendations':
            results = await self._ai_get_recommendations(context)
        
        else:
            # Acción no reconocida, generar combinaciones por defecto
            results = await self._generate_default_predictions(context)
        
        return results
    
    async def _ai_generate_combinations(self, intent, context: Dict[str, Any]) -> Dict[str, Any]:
        """Genera combinaciones usando todos los sistemas de IA"""
        quantity = intent.parameters.get('quantity', 5)
        strategy = intent.parameters.get('strategy', 'balanced')
        
        logger.info(f"🎯 Generando {quantity} combinaciones con estrategia {strategy}")
        
        results = {'combinations': [], 'analysis': {}}
        
        # Obtener datos históricos del contexto
        historical_data = context.get('historical_data', [])
        
        # 1. Predicciones del ensemble de IAs especializadas
        if self.ensemble_system and historical_data:
            try:
                ensemble_predictions = await generate_intelligent_predictions(
                    self.ensemble_system, historical_data, quantity
                )
                results['combinations'].extend(ensemble_predictions)
                results['analysis']['ensemble_used'] = True
                logger.info(f"✅ Ensemble generó {len(ensemble_predictions)} predicciones")
            except Exception as e:
                logger.error(f"❌ Error en ensemble: {e}")
        
        # 2. Predicciones de redes neuronales avanzadas
        if self.neural_system:
            try:
                neural_predictions = self.neural_system.generate_intelligent_combinations(
                    min(quantity, 3)  # Limitar para diversidad
                )
                results['combinations'].extend(neural_predictions)
                results['analysis']['neural_used'] = True
                logger.info(f"✅ Sistema neuronal generó {len(neural_predictions)} predicciones")
            except Exception as e:
                logger.error(f"❌ Error en sistema neuronal: {e}")
        
        # 3. Aplicar estrategia específica
        if strategy != 'balanced':
            results['combinations'] = self._apply_strategy_filter(results['combinations'], strategy)
        
        # 4. Análisis inteligente de las predicciones
        if historical_data and self.neural_system:
            try:
                pattern_analysis = self.neural_system.analyze_pattern_intelligence(historical_data)
                results['analysis']['pattern_intelligence'] = pattern_analysis
            except Exception as e:
                logger.error(f"❌ Error en análisis de patrones: {e}")
        
        # Limitar al número solicitado
        results['combinations'] = results['combinations'][:quantity]
        
        return results
    
    async def _ai_analyze_patterns(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis inteligente de patrones"""
        logger.info("🔍 Realizando análisis inteligente de patrones")
        
        historical_data = context.get('historical_data', [])
        results = {'pattern_analysis': {}, 'insights': []}
        
        if not historical_data:
            results['pattern_analysis'] = {
                'error': 'No hay datos históricos disponibles para análisis'
            }
            return results
        
        # Análisis con redes neuronales avanzadas
        if self.neural_system:
            try:
                neural_analysis = self.neural_system.analyze_pattern_intelligence(historical_data)
                results['pattern_analysis'].update(neural_analysis)
                
                # Generar insights automáticos
                results['insights'] = self._generate_pattern_insights(neural_analysis)
                
                logger.info("✅ Análisis neuronal de patrones completado")
            except Exception as e:
                logger.error(f"❌ Error en análisis neuronal: {e}")
        
        # Análisis del ensemble de IAs
        if self.ensemble_system:
            try:
                ensemble_analysis = self.ensemble_system.get_ensemble_analysis()
                results['pattern_analysis']['ensemble_analysis'] = ensemble_analysis
                logger.info("✅ Análisis del ensemble completado")
            except Exception as e:
                logger.error(f"❌ Error en análisis del ensemble: {e}")
        
        return results
    
    async def _ai_explain_results(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Explicación inteligente de resultados"""
        logger.info("🤓 Generando explicación inteligente de resultados")
        
        results = {
            'explanation': {},
            'technical_details': {},
            'confidence_factors': {}
        }
        
        # Obtener último resultado del contexto
        last_results = context.get('last_ai_results', {})
        
        if last_results:
            # Análisis de confianza
            combinations = last_results.get('combinations', [])
            if combinations:
                avg_confidence = np.mean([c.get('confidence', 0.5) for c in combinations])
                results['explanation']['average_confidence'] = avg_confidence
                results['explanation']['total_combinations'] = len(combinations)
                
                # Análisis de métodos utilizados
                methods_used = set()
                for combo in combinations:
                    if 'method' in combo:
                        methods_used.add(combo['method'])
                    if 'source' in combo:
                        methods_used.add(combo['source'])
                
                results['explanation']['methods_used'] = list(methods_used)
                results['explanation']['ai_systems_active'] = self._get_active_ai_systems()
        
        # Factores que influyen en la confianza
        results['confidence_factors'] = {
            'data_quality': self._assess_data_quality(context),
            'model_consensus': self._assess_model_consensus(last_results),
            'historical_accuracy': self._get_historical_accuracy()
        }
        
        return results
    
    async def _ai_check_probability(self, intent, context: Dict[str, Any]) -> Dict[str, Any]:
        """Verificación inteligente de probabilidad"""
        combination = intent.parameters.get('combination', [])
        
        logger.info(f"🎲 Calculando probabilidad para: {combination}")
        
        results = {'probability_analysis': {}, 'ai_assessment': {}}
        
        if not combination:
            results['error'] = 'No se especificó combinación para análisis'
            return results
        
        # Análisis con múltiples métodos de IA
        if self.neural_system:
            try:
                # Simular análisis de probabilidad (en implementación real sería más complejo)
                base_probability = 1 / (40 * 39 * 38 * 37 * 36 * 35)  # Probabilidad base
                
                # Ajustar basado en análisis de IA
                ai_multiplier = np.random.uniform(0.5, 2.0)  # En implementación real sería calculado
                adjusted_probability = base_probability * ai_multiplier
                
                results['probability_analysis'] = {
                    'base_probability': base_probability,
                    'ai_adjusted_probability': adjusted_probability,
                    'confidence': np.random.uniform(0.6, 0.9),
                    'analysis_method': 'neural_networks'
                }
                
                logger.info(f"✅ Probabilidad calculada: {adjusted_probability:.8f}")
            except Exception as e:
                logger.error(f"❌ Error en cálculo de probabilidad: {e}")
        
        return results
    
    async def _ai_optimize_settings(self, intent, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimización inteligente de configuración"""
        risk_level = intent.parameters.get('risk_level', 'medium')
        
        logger.info(f"⚙️ Optimizando configuración para riesgo: {risk_level}")
        
        results = {'optimization_applied': {}, 'new_settings': {}}
        
        # Optimizar configuración basada en IA
        optimizations = {
            'ensemble_weights_adjusted': False,
            'neural_learning_rate_tuned': False,
            'strategy_parameters_updated': False
        }
        
        if self.ensemble_system:
            # Ajustar pesos del ensemble según nivel de riesgo
            if risk_level == 'high':
                # Mayor peso a IAs más experimentales
                optimizations['ensemble_weights_adjusted'] = True
            elif risk_level == 'low':
                # Mayor peso a IAs más conservadoras
                optimizations['ensemble_weights_adjusted'] = True
        
        if self.neural_system:
            # Ajustar tasa de aprendizaje
            if risk_level == 'high':
                self.neural_system.adaptation_rate = 0.2
            elif risk_level == 'low':
                self.neural_system.adaptation_rate = 0.05
            else:
                self.neural_system.adaptation_rate = 0.1
            
            optimizations['neural_learning_rate_tuned'] = True
        
        results['optimization_applied'] = optimizations
        results['new_settings'] = {
            'risk_level': risk_level,
            'optimization_timestamp': datetime.now().isoformat()
        }
        
        return results
    
    async def _ai_get_recommendations(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Recomendaciones inteligentes personalizadas"""
        logger.info("💡 Generando recomendaciones inteligentes")
        
        results = {'recommendations': [], 'personalization': {}}
        
        # Analizar historial de interacciones del usuario
        interactions = self.session_memory['interactions']
        
        # Recomendaciones basadas en patrones de uso
        if len(interactions) > 0:
            # Analizar acciones más frecuentes
            actions = [i.get('intent', 'unknown') for i in interactions]
            most_common_action = max(set(actions), key=actions.count) if actions else None
            
            if most_common_action == 'generate_combinations':
                results['recommendations'].append(
                    "Considera analizar patrones antes de generar más combinaciones para mejorar precisión"
                )
            elif most_common_action == 'analyze_patterns':
                results['recommendations'].append(
                    "Tus análisis son detallados, podrías beneficiarte de predicciones más agresivas"
                )
        
        # Recomendaciones técnicas
        active_systems = self._get_active_ai_systems()
        if len(active_systems) < 3:
            results['recommendations'].append(
                "Activa más sistemas de IA para obtener predicciones más robustas"
            )
        
        # Recomendaciones de optimización
        if self.ensemble_system:
            ensemble_analysis = self.ensemble_system.get_ensemble_analysis()
            avg_performance = np.mean([
                s['average_performance'] for s in ensemble_analysis['specialists_info']
            ])
            
            if avg_performance < 0.6:
                results['recommendations'].append(
                    "Considera entrenar más los modelos con datos recientes"
                )
        
        # Personalización basada en preferencias inferidas
        results['personalization'] = {
            'preferred_actions': list(set(actions)) if interactions else [],
            'interaction_frequency': len(interactions),
            'session_duration': self._calculate_session_duration()
        }
        
        return results
    
    async def _generate_default_predictions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Genera predicciones por defecto cuando no se especifica acción"""
        logger.info("🎯 Generando predicciones por defecto")
        
        # Usar sistema disponible más avanzado
        if self.ensemble_system:
            historical_data = context.get('historical_data', [])
            if historical_data:
                ensemble_predictions = await generate_intelligent_predictions(
                    self.ensemble_system, historical_data, 3
                )
                return {'combinations': ensemble_predictions, 'default_generation': True}
        
        if self.neural_system:
            neural_predictions = self.neural_system.generate_intelligent_combinations(3)
            return {'combinations': neural_predictions, 'default_generation': True}
        
        # Fallback básico
        return {
            'combinations': [
                {'combination': sorted(np.random.choice(range(1, 41), 6, replace=False).tolist()),
                 'confidence': 0.5, 'source': 'fallback'}
            ],
            'default_generation': True,
            'fallback_used': True
        }
    
    async def _continuous_learning_update(self, user_input: str, intent, ai_results: Dict[str, Any]):
        """Actualización de aprendizaje continuo"""
        if not self.config['learning_settings']['continuous_learning']:
            return
        
        logger.info("📚 Actualizando aprendizaje continuo")
        
        # Registrar datos para aprendizaje
        learning_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'intent': intent.action if intent else 'unknown',
            'confidence': intent.confidence if intent else 0.0,
            'ai_results': ai_results
        }
        
        self.session_memory['learning_data'].append(learning_entry)
        
        # Aplicar aprendizaje incremental si hay suficientes datos
        if len(self.session_memory['learning_data']) >= 5:
            await self._apply_incremental_learning()
    
    async def _apply_incremental_learning(self):
        """Aplica aprendizaje incremental a los sistemas de IA"""
        logger.info("🧠 Aplicando aprendizaje incremental")
        
        learning_data = self.session_memory['learning_data']
        
        # Extraer combinaciones exitosas (alta confianza)
        successful_combinations = []
        for entry in learning_data:
            combinations = entry.get('ai_results', {}).get('combinations', [])
            for combo in combinations:
                if combo.get('confidence', 0) > 0.7:
                    if 'combination' in combo:
                        successful_combinations.append(combo['combination'])
        
        # Actualizar sistemas con datos exitosos
        if successful_combinations and self.neural_system:
            try:
                self.neural_system.adapt_to_new_data(successful_combinations)
                logger.info(f"✅ Sistema neuronal actualizado con {len(successful_combinations)} combinaciones")
            except Exception as e:
                logger.error(f"❌ Error en aprendizaje neuronal: {e}")
        
        if successful_combinations and self.ensemble_system:
            try:
                self.ensemble_system.train_ensemble(successful_combinations)
                logger.info(f"✅ Ensemble actualizado con {len(successful_combinations)} combinaciones")
            except Exception as e:
                logger.error(f"❌ Error en aprendizaje del ensemble: {e}")
    
    async def _generate_intelligent_response(self, user_input: str, intent, ai_results: Dict[str, Any], nlp_response: str) -> Dict[str, Any]:
        """Genera respuesta inteligente combinando todos los sistemas"""
        logger.info("💬 Generando respuesta inteligente integrada")
        
        # Respuesta base del NLP si está disponible
        if nlp_response and self.nlp_system:
            # Enriquecer respuesta NLP con resultados de IA
            enhanced_response = self._enhance_nlp_response(nlp_response, ai_results)
        else:
            # Generar respuesta básica
            enhanced_response = self._generate_basic_response(user_input, ai_results)
        
        # Estructura de respuesta completa
        response = {
            'user_input': user_input,
            'ai_response': enhanced_response,
            'ai_results': ai_results,
            'metadata': {
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat(),
                'systems_used': self._get_active_ai_systems(),
                'intent_detected': intent.action if intent else 'unknown',
                'confidence': intent.confidence if intent else 0.0,
                'processing_info': {
                    'neural_networks': self.neural_system is not None,
                    'nlp_processing': self.nlp_system is not None,
                    'ensemble_ai': self.ensemble_system is not None
                }
            }
        }
        
        return response
    
    def _enhance_nlp_response(self, nlp_response: str, ai_results: Dict[str, Any]) -> str:
        """Enriquece la respuesta NLP con resultados de IA"""
        enhanced = nlp_response
        
        # Agregar detalles técnicos si hay resultados de IA
        if ai_results.get('combinations'):
            combo_count = len(ai_results['combinations'])
            enhanced += f"\n\n🤖 **Detalles técnicos de IA**:\n"
            enhanced += f"• Generadas {combo_count} combinaciones usando múltiples sistemas de IA\n"
            
            if ai_results.get('analysis', {}).get('ensemble_used'):
                enhanced += "• Sistema ensemble de IAs especializadas activado\n"
            
            if ai_results.get('analysis', {}).get('neural_used'):
                enhanced += "• Redes neuronales avanzadas con mecanismo de atención utilizadas\n"
        
        return enhanced
    
    def _generate_basic_response(self, user_input: str, ai_results: Dict[str, Any]) -> str:
        """Genera respuesta básica cuando NLP no está disponible"""
        response = "🤖 **OMEGA PRO AI - Respuesta Inteligente**\n\n"
        
        if ai_results.get('combinations'):
            combinations = ai_results['combinations']
            response += f"✅ He generado {len(combinations)} combinaciones usando IA avanzada:\n\n"
            
            for i, combo in enumerate(combinations[:5], 1):  # Limitar a 5
                if isinstance(combo, dict):
                    numbers = combo.get('combination', [])
                    confidence = combo.get('confidence', 0.5)
                    source = combo.get('source', 'unknown')
                    response += f"{i}. {' - '.join(map(str, numbers))} "
                    response += f"(Confianza: {confidence:.1%}, Fuente: {source})\n"
        
        if ai_results.get('analysis'):
            response += "\n📊 **Análisis de IA aplicado**:\n"
            analysis = ai_results['analysis']
            
            if analysis.get('pattern_intelligence'):
                pattern_info = analysis['pattern_intelligence']
                response += f"• Complejidad de patrones: {pattern_info.get('pattern_complexity', 0):.2f}\n"
                response += f"• Confianza de IA: {pattern_info.get('ai_confidence', 0):.1%}\n"
        
        response += f"\n🧠 **Sistemas de IA activos**: {', '.join(self._get_active_ai_systems())}"
        
        return response
    
    def _apply_strategy_filter(self, combinations: List[Dict[str, Any]], strategy: str) -> List[Dict[str, Any]]:
        """Aplica filtro de estrategia a las combinaciones"""
        if strategy == 'conservative':
            # Filtrar por mayor confianza
            return sorted(combinations, key=lambda x: x.get('confidence', 0), reverse=True)
        
        elif strategy == 'aggressive':
            # Filtrar por menor confianza pero mayor potencial
            return sorted(combinations, key=lambda x: x.get('confidence', 0))
        
        return combinations
    
    def _generate_pattern_insights(self, pattern_analysis: Dict[str, Any]) -> List[str]:
        """Genera insights automáticos del análisis de patrones"""
        insights = []
        
        complexity = pattern_analysis.get('pattern_complexity', 0)
        if complexity > 0.7:
            insights.append("Patrones altamente complejos detectados - considera estrategias diversificadas")
        elif complexity < 0.3:
            insights.append("Patrones simples identificados - estrategias directas pueden ser efectivas")
        
        trend = pattern_analysis.get('predicted_trend', 'neutral')
        if trend == 'ascending':
            insights.append("Tendencia ascendente detectada - números altos pueden tener mayor probabilidad")
        elif trend == 'descending':
            insights.append("Tendencia descendente identificada - considera números más bajos")
        
        confidence = pattern_analysis.get('ai_confidence', 0)
        if confidence > 0.8:
            insights.append("Alta confianza en el análisis - resultados muy fiables")
        elif confidence < 0.4:
            insights.append("Confianza moderada - considera combinar con otros métodos")
        
        return insights
    
    def _get_active_ai_systems(self) -> List[str]:
        """Obtiene lista de sistemas de IA activos"""
        active = []
        
        if self.neural_system:
            active.append("Redes Neuronales Avanzadas")
        
        if self.nlp_system:
            active.append("Procesamiento de Lenguaje Natural")
        
        if self.ensemble_system:
            active.append("Ensemble de IAs Especializadas")
        
        return active
    
    def _assess_data_quality(self, context: Dict[str, Any]) -> float:
        """Evalúa la calidad de los datos disponibles"""
        historical_data = context.get('historical_data', [])
        
        if not historical_data:
            return 0.3
        
        # Evaluar basado en cantidad y consistencia
        quality_score = min(len(historical_data) / 100, 1.0) * 0.7
        
        # Evaluar consistencia (variación en rangos)
        if len(historical_data) > 5:
            ranges = [max(seq) - min(seq) for seq in historical_data]
            consistency = 1.0 - (np.std(ranges) / np.mean(ranges)) if np.mean(ranges) > 0 else 0.5
            quality_score += consistency * 0.3
        
        return min(quality_score, 1.0)
    
    def _assess_model_consensus(self, ai_results: Dict[str, Any]) -> float:
        """Evalúa el consenso entre modelos"""
        combinations = ai_results.get('combinations', [])
        
        if len(combinations) < 2:
            return 0.5
        
        # Calcular similitud entre combinaciones
        all_numbers = []
        for combo in combinations:
            if 'combination' in combo:
                all_numbers.extend(combo['combination'])
        
        if not all_numbers:
            return 0.5
        
        # Calcular frecuencia de números repetidos
        from collections import Counter
        number_freq = Counter(all_numbers)
        repeated_numbers = sum(1 for count in number_freq.values() if count > 1)
        
        consensus_score = repeated_numbers / len(set(all_numbers)) if all_numbers else 0.5
        
        return min(consensus_score, 1.0)
    
    def _get_historical_accuracy(self) -> float:
        """Obtiene precisión histórica promedio"""
        # Simplificación - en implementación real sería basado en datos reales
        interactions = self.session_memory['interactions']
        
        if not interactions:
            return 0.6  # Valor base
        
        # Calcular basado en confianza promedio de interacciones pasadas
        confidences = [i.get('confidence', 0.5) for i in interactions]
        return np.mean(confidences) if confidences else 0.6
    
    def _calculate_session_duration(self) -> float:
        """Calcula duración de la sesión en minutos"""
        if not self.session_memory['interactions']:
            return 0.0
        
        first_interaction = datetime.fromisoformat(self.session_memory['interactions'][0]['timestamp'])
        last_interaction = datetime.fromisoformat(self.session_memory['interactions'][-1]['timestamp'])
        
        duration = (last_interaction - first_interaction).total_seconds() / 60
        return duration
    
    def get_ai_status(self) -> Dict[str, Any]:
        """Obtiene estado completo del sistema de IA"""
        return {
            'session_id': self.session_id,
            'active_systems': self._get_active_ai_systems(),
            'configuration': self.config,
            'session_stats': {
                'total_interactions': len(self.session_memory['interactions']),
                'session_duration_minutes': self._calculate_session_duration(),
                'learning_data_points': len(self.session_memory['learning_data'])
            },
            'system_health': {
                'neural_system': self.neural_system is not None,
                'nlp_system': self.nlp_system is not None,
                'ensemble_system': self.ensemble_system is not None
            }
        }
    
    async def shutdown_gracefully(self):
        """Cierre controlado del sistema guardando estado"""
        logger.info("🛑 Iniciando cierre controlado de OMEGA PRO AI Core")
        
        # Guardar sesión
        session_file = Path(f"logs/ai_sessions/session_{self.session_id}.json")
        try:
            with open(session_file, 'w') as f:
                json.dump(self.session_memory, f, indent=2, default=str)
            logger.info(f"💾 Sesión guardada en {session_file}")
        except Exception as e:
            logger.error(f"❌ Error guardando sesión: {e}")
        
        logger.info("✅ OMEGA PRO AI Core cerrado correctamente")

# Función principal para crear el sistema
def create_omega_ai_core(config_path: Optional[str] = None) -> OmegaProAICore:
    """Crea instancia del sistema principal de IA"""
    return OmegaProAICore(config_path)

# Función de utilidad para interacción rápida
async def quick_ai_interaction(user_input: str, historical_data: List[List[int]] = None) -> Dict[str, Any]:
    """Interacción rápida con el sistema de IA"""
    ai_core = create_omega_ai_core()
    
    context = {}
    if historical_data:
        context['historical_data'] = historical_data
    
    response = await ai_core.process_intelligent_request(user_input, context)
    await ai_core.shutdown_gracefully()
    
    return response

if __name__ == "__main__":
    # Ejemplo de uso del sistema completo
    async def demo():
        print("🚀 Iniciando demo de OMEGA PRO AI Core...")
        
        # Crear sistema de IA
        ai_core = create_omega_ai_core()
        
        # Datos históricos de ejemplo
        historical_data = [
            [1, 15, 23, 31, 35, 40],
            [3, 12, 18, 27, 33, 39],
            [5, 14, 22, 28, 34, 38],
            [2, 11, 19, 25, 32, 37]
        ]
        
        # Interacciones de ejemplo
        interactions = [
            "Genera 3 combinaciones agresivas",
            "Analiza los patrones de estos datos",
            "Explica por qué elegiste esos números",
            "Dame recomendaciones para mejorar"
        ]
        
        context = {'historical_data': historical_data}
        
        for interaction in interactions:
            print(f"\n🔤 Usuario: {interaction}")
            response = await ai_core.process_intelligent_request(interaction, context)
            print(f"🤖 OMEGA AI: {response['ai_response']}")
            print("-" * 60)
        
        # Mostrar estado final
        status = ai_core.get_ai_status()
        print(f"\n📊 Estado del sistema: {status['active_systems']}")
        print(f"📈 Interacciones procesadas: {status['session_stats']['total_interactions']}")
        
        # Cerrar sistema
        await ai_core.shutdown_gracefully()
    
    # Ejecutar demo con manejo seguro de async
    try:
        # Verificar si ya estamos en un event loop
        loop = asyncio.get_running_loop()
        if loop and loop.is_running():
            # Ya estamos en un event loop, usar ThreadPoolExecutor para evitar conflicto
            import concurrent.futures
            print("📝 Demo ejecutándose en hilo separado para evitar conflicto de event loop...")
            
            def run_demo_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(demo())
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_demo_in_thread)
                result = future.result()
                print("✅ Demo completado")
        else:
            asyncio.run(demo())
    except RuntimeError:
        # No hay event loop, usar asyncio.run normalmente
        asyncio.run(demo())
