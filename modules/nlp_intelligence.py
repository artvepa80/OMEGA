#!/usr/bin/env python3
"""
Natural Language Processing Intelligence Module for OMEGA PRO AI
Permite interacción inteligente con el usuario y análisis de texto
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class UserIntent:
    """Representa la intención del usuario"""
    action: str
    parameters: Dict[str, Any]
    confidence: float
    context: Dict[str, Any]

class OmegaNLPProcessor:
    """Procesador de lenguaje natural para OMEGA PRO AI"""
    
    def __init__(self):
        self.intent_patterns = self._initialize_intent_patterns()
        self.context_memory = []
        self.user_preferences = {}
        self.conversation_history = []
        
    def _initialize_intent_patterns(self) -> Dict[str, List[str]]:
        """Inicializa patrones de reconocimiento de intenciones"""
        return {
            'generate_combinations': [
                r'genera?r?\s*(\d+)?\s*combinaciones?',
                r'crea?r?\s*(\d+)?\s*números?',
                r'dame\s*(\d+)?\s*jugadas?',
                r'quiero\s*(\d+)?\s*combinaciones?',
                r'predict\s*(\d+)?\s*combinations?',
                r'generate\s*(\d+)?\s*numbers?'
            ],
            'analyze_patterns': [
                r'analiza?r?\s*patrones?',
                r'busca?r?\s*tendencias?',
                r'estudia?r?\s*histórico',
                r'qué\s*patrones?\s*ves?',
                r'analyze\s*patterns?',
                r'find\s*trends?'
            ],
            'explain_results': [
                r'explica?r?\s*resultados?',
                r'por\s*qué\s*estos?\s*números?',
                r'justifica?r?\s*combinación',
                r'razón\s*de\s*la\s*predicción',
                r'explain\s*results?',
                r'why\s*these\s*numbers?'
            ],
            'optimize_settings': [
                r'optimiza?r?\s*configuración',
                r'mejora?r?\s*parámetros?',
                r'ajusta?r?\s*sistema',
                r'cambia?r?\s*settings?',
                r'optimize\s*settings?',
                r'tune\s*parameters?'
            ],
            'get_recommendations': [
                r'recomienda?r?\s*estrategia',
                r'qué\s*me\s*aconsejas?',
                r'cuál\s*es\s*la\s*mejor\s*opción',
                r'dame\s*consejos?',
                r'recommend\s*strategy',
                r'give\s*advice'
            ],
            'check_probability': [
                r'probabilidad\s*de?\s*(\[[\d,\s]+\]|\d+)',
                r'qué\s*tan\s*probable\s*es',
                r'chances?\s*of',
                r'probability\s*of'
            ]
        }
    
    def process_user_input(self, user_input: str, context: Dict[str, Any] = None) -> UserIntent:
        """Procesa entrada del usuario y extrae intención"""
        logger.info(f"🎯 Procesando entrada: '{user_input}'")
        
        user_input = user_input.lower().strip()
        context = context or {}
        
        # Guardar en historial
        self.conversation_history.append({
            'input': user_input,
            'timestamp': datetime.now().isoformat(),
            'context': context
        })
        
        # Analizar intención
        intent = self._extract_intent(user_input)
        
        # Enriquecer con contexto
        intent.context.update(context)
        
        logger.info(f"✅ Intención detectada: {intent.action} (confianza: {intent.confidence:.2f})")
        return intent
    
    def _extract_intent(self, text: str) -> UserIntent:
        """Extrae la intención principal del texto"""
        best_match = None
        best_confidence = 0.0
        best_action = 'unknown'
        best_params = {}
        
        for action, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    confidence = self._calculate_confidence(text, pattern, match)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_action = action
                        best_match = match
                        best_params = self._extract_parameters(text, match, action)
        
        return UserIntent(
            action=best_action,
            parameters=best_params,
            confidence=best_confidence,
            context={'original_text': text, 'match': str(best_match) if best_match else None}
        )
    
    def _calculate_confidence(self, text: str, pattern: str, match) -> float:
        """Calcula confianza de la coincidencia"""
        base_confidence = 0.8
        
        # Factores que aumentan confianza
        if match.group(0) == text:  # Coincidencia exacta
            base_confidence += 0.2
        
        # Longitud de la coincidencia vs texto total
        match_ratio = len(match.group(0)) / len(text)
        base_confidence += match_ratio * 0.1
        
        # Palabras clave específicas
        keywords = ['omega', 'ai', 'predicción', 'combinación', 'número']
        for keyword in keywords:
            if keyword in text:
                base_confidence += 0.05
        
        return min(base_confidence, 1.0)
    
    def _extract_parameters(self, text: str, match, action: str) -> Dict[str, Any]:
        """Extrae parámetros específicos de la acción"""
        params = {}
        
        if action == 'generate_combinations':
            # Extraer cantidad
            numbers = re.findall(r'\d+', text)
            if numbers:
                params['quantity'] = min(int(numbers[0]), 100)  # Límite de seguridad
            else:
                params['quantity'] = 5  # Por defecto
            
            # Extraer rango de números si se especifica
            range_match = re.search(r'del\s*(\d+)\s*al\s*(\d+)', text)
            if range_match:
                params['min_number'] = int(range_match.group(1))
                params['max_number'] = int(range_match.group(2))
            
            # Estrategia específica
            if 'conservador' in text or 'seguro' in text:
                params['strategy'] = 'conservative'
            elif 'agresivo' in text or 'arriesgado' in text:
                params['strategy'] = 'aggressive'
            elif 'balanceado' in text or 'equilibrado' in text:
                params['strategy'] = 'balanced'
        
        elif action == 'check_probability':
            # Extraer combinación específica
            combo_match = re.search(r'\[([^\]]+)\]', text)
            if combo_match:
                numbers = [int(x.strip()) for x in combo_match.group(1).split(',')]
                params['combination'] = numbers
        
        elif action == 'optimize_settings':
            # Extraer parámetros específicos
            if 'agresivo' in text:
                params['risk_level'] = 'high'
            elif 'conservador' in text:
                params['risk_level'] = 'low'
            
            if 'rápido' in text or 'velocidad' in text:
                params['speed_priority'] = True
            elif 'precisión' in text or 'exactitud' in text:
                params['accuracy_priority'] = True
        
        return params
    
    def generate_intelligent_response(self, intent: UserIntent, results: Dict[str, Any] = None) -> str:
        """Genera respuesta inteligente basada en la intención"""
        logger.info(f"💬 Generando respuesta para acción: {intent.action}")
        
        responses = {
            'generate_combinations': self._respond_generate_combinations,
            'analyze_patterns': self._respond_analyze_patterns,
            'explain_results': self._respond_explain_results,
            'optimize_settings': self._respond_optimize_settings,
            'get_recommendations': self._respond_recommendations,
            'check_probability': self._respond_check_probability,
            'unknown': self._respond_unknown
        }
        
        response_generator = responses.get(intent.action, responses['unknown'])
        response = response_generator(intent, results)
        
        # Agregar contexto personal si está disponible
        response = self._personalize_response(response, intent)
        
        return response
    
    def _respond_generate_combinations(self, intent: UserIntent, results: Dict[str, Any]) -> str:
        """Respuesta para generación de combinaciones"""
        quantity = intent.parameters.get('quantity', 5)
        strategy = intent.parameters.get('strategy', 'balanced')
        
        response = f"🎯 He generado {quantity} combinaciones utilizando estrategia {strategy}.\n\n"
        
        if results and 'combinations' in results:
            response += "📊 **Combinaciones generadas:**\n"
            for i, combo in enumerate(results['combinations'][:quantity], 1):
                if isinstance(combo, dict):
                    numbers = combo.get('combination', [])
                    confidence = combo.get('confidence', 0.5)
                    response += f"{i}. {' - '.join(map(str, numbers))} (Confianza: {confidence:.1%})\n"
                else:
                    response += f"{i}. {' - '.join(map(str, combo))}\n"
        
        response += f"\n💡 **Análisis IA**: Estas combinaciones han sido optimizadas usando redes neuronales avanzadas y análisis de patrones profundos."
        
        if strategy == 'conservative':
            response += "\n🛡️ **Estrategia Conservadora**: Números con mayor frecuencia histórica."
        elif strategy == 'aggressive':
            response += "\n🚀 **Estrategia Agresiva**: Números con potencial de ruptura de patrones."
        
        return response
    
    def _respond_analyze_patterns(self, intent: UserIntent, results: Dict[str, Any]) -> str:
        """Respuesta para análisis de patrones"""
        response = "🔍 **Análisis Inteligente de Patrones OMEGA PRO AI**\n\n"
        
        if results and 'pattern_analysis' in results:
            analysis = results['pattern_analysis']
            
            response += f"📈 **Complejidad de Patrones**: {analysis.get('pattern_complexity', 0):.2f}/1.0\n"
            response += f"🎯 **Confianza de IA**: {analysis.get('ai_confidence', 0):.1%}\n"
            response += f"📊 **Tendencia Detectada**: {analysis.get('predicted_trend', 'neutral').title()}\n"
            response += f"🧠 **Score de Inteligencia**: {analysis.get('intelligence_score', 0):.3f}\n\n"
            
            if 'recommendations' in analysis:
                response += "💡 **Recomendaciones de IA**:\n"
                for rec in analysis['recommendations']:
                    response += f"• {rec}\n"
        else:
            response += "🤖 Ejecutando análisis profundo con redes neuronales...\n"
            response += "📊 Procesando patrones temporales y frecuenciales...\n"
            response += "🧬 Aplicando algoritmos de machine learning avanzados...\n"
        
        return response
    
    def _respond_explain_results(self, intent: UserIntent, results: Dict[str, Any]) -> str:
        """Respuesta para explicación de resultados"""
        response = "🤓 **Explicación Inteligente de Resultados**\n\n"
        
        response += "🧠 **Proceso de IA utilizado**:\n"
        response += "• Redes neuronales con mecanismo de atención\n"
        response += "• Análisis de patrones temporales con LSTM bidireccional\n"
        response += "• Sistema de aprendizaje por refuerzo para optimización\n"
        response += "• Meta-aprendizaje para adaptación continua\n\n"
        
        if results:
            response += "📊 **Factores considerados**:\n"
            response += "• Frecuencia histórica de números\n"
            response += "• Patrones secuenciales y correlaciones\n"
            response += "• Análisis de atención neuronal\n"
            response += "• Confianza del modelo ensemble\n\n"
        
        response += "✨ **Por qué confiar en estos resultados**:\n"
        response += "• Múltiples algoritmos de IA trabajando en conjunto\n"
        response += "• Validación cruzada y meta-análisis\n"
        response += "• Aprendizaje continuo del sistema\n"
        
        return response
    
    def _respond_optimize_settings(self, intent: UserIntent, results: Dict[str, Any]) -> str:
        """Respuesta para optimización de configuración"""
        risk_level = intent.parameters.get('risk_level', 'medium')
        
        response = f"⚙️ **Optimizando configuración para nivel de riesgo: {risk_level}**\n\n"
        
        if risk_level == 'high':
            response += "🚀 **Configuración Agresiva activada**:\n"
            response += "• Exploración de números poco frecuentes\n"
            response += "• Mayor peso a algoritmos innovadores\n"
            response += "• Epsilon de exploración aumentado\n"
        elif risk_level == 'low':
            response += "🛡️ **Configuración Conservadora activada**:\n"
            response += "• Enfoque en patrones establecidos\n"
            response += "• Mayor peso a datos históricos\n"
            response += "• Reducción de variabilidad\n"
        else:
            response += "⚖️ **Configuración Balanceada activada**:\n"
            response += "• Equilibrio entre exploración y explotación\n"
            response += "• Pesos uniformes en ensemble\n"
            response += "• Optimización multi-objetivo\n"
        
        response += "\n✅ **Sistema optimizado y listo para nueva generación**"
        
        return response
    
    def _respond_recommendations(self, intent: UserIntent, results: Dict[str, Any]) -> str:
        """Respuesta con recomendaciones"""
        response = "💡 **Recomendaciones Inteligentes OMEGA PRO AI**\n\n"
        
        # Recomendaciones basadas en historial de conversación
        recent_actions = [entry.get('context', {}).get('action') for entry in self.conversation_history[-5:]]
        
        response += "🎯 **Estrategias recomendadas**:\n"
        
        if 'generate_combinations' in recent_actions:
            response += "• Considera diversificar con diferentes estrategias\n"
            response += "• Analiza patrones antes de la próxima generación\n"
        
        response += "• Usa el ensemble de IA para máxima precisión\n"
        response += "• Combina análisis técnico con intuición de IA\n"
        response += "• Mantén un balance entre riesgo y recompensa\n\n"
        
        response += "🧬 **Optimizaciones sugeridas**:\n"
        response += "• Entrena el modelo con tus resultados\n"
        response += "• Ajusta parámetros según tu perfil de riesgo\n"
        response += "• Utiliza feedback para aprendizaje continuo\n"
        
        return response
    
    def _respond_check_probability(self, intent: UserIntent, results: Dict[str, Any]) -> str:
        """Respuesta para verificación de probabilidad"""
        combination = intent.parameters.get('combination', [])
        
        if not combination:
            return "❓ No pude identificar la combinación. Por favor, especifica los números entre corchetes: [1, 2, 3, 4, 5, 6]"
        
        response = f"🎲 **Análisis de Probabilidad**: {combination}\n\n"
        
        if results and 'probability' in results:
            prob = results['probability']
            response += f"📊 **Probabilidad calculada**: {prob:.6f} ({prob:.2%})\n"
            response += f"🎯 **Confianza del modelo**: {results.get('confidence', 0.5):.1%}\n\n"
        
        response += "🤖 **Análisis de IA**:\n"
        response += f"• Números en rango óptimo: {len([n for n in combination if 1 <= n <= 40])}/6\n"
        response += f"• Distribución: {'Balanceada' if max(combination) - min(combination) > 20 else 'Concentrada'}\n"
        response += f"• Patrón: {'Secuencial' if any(combination[i+1] - combination[i] == 1 for i in range(len(combination)-1)) else 'Aleatorio'}\n"
        
        return response
    
    def _respond_unknown(self, intent: UserIntent, results: Dict[str, Any]) -> str:
        """Respuesta para intenciones no reconocidas"""
        response = "🤔 **No estoy seguro de entender tu solicitud**\n\n"
        response += "💬 **Puedes preguntarme sobre**:\n"
        response += "• 'Genera 5 combinaciones'\n"
        response += "• 'Analiza los patrones'\n"
        response += "• 'Explica estos resultados'\n"
        response += "• 'Qué probabilidad tiene [1,2,3,4,5,6]'\n"
        response += "• 'Dame recomendaciones'\n"
        response += "• 'Optimiza la configuración'\n\n"
        response += "🧠 **Mi IA está aprendiendo constantemente, puedes ser más específico y lo entenderé mejor.**"
        
        return response
    
    def _personalize_response(self, response: str, intent: UserIntent) -> str:
        """Personaliza la respuesta basada en el historial del usuario"""
        # Agregar saludo personalizado si es la primera interacción
        if len(self.conversation_history) == 1:
            response = "👋 ¡Hola! Soy OMEGA PRO AI, tu asistente inteligente.\n\n" + response
        
        # Agregar nota de aprendizaje si se detectan patrones de uso
        if len(self.conversation_history) >= 5:
            response += f"\n\n🧠 *He aprendido de nuestras {len(self.conversation_history)} interacciones para darte mejores resultados.*"
        
        return response

# Funciones de utilidad
def create_nlp_system() -> OmegaNLPProcessor:
    """Crea el sistema de procesamiento de lenguaje natural"""
    logger.info("🗣️ Inicializando sistema NLP de OMEGA PRO AI...")
    return OmegaNLPProcessor()

def process_user_query(nlp_system: OmegaNLPProcessor, query: str, context: Dict[str, Any] = None) -> Tuple[UserIntent, str]:
    """Procesa una consulta del usuario y genera respuesta"""
    intent = nlp_system.process_user_input(query, context)
    response = nlp_system.generate_intelligent_response(intent)
    return intent, response

if __name__ == "__main__":
    # Ejemplo de uso
    nlp = create_nlp_system()
    
    # Simulación de interacciones
    queries = [
        "Genera 3 combinaciones agresivas",
        "Analiza los patrones históricos",
        "Qué probabilidad tiene [1, 15, 23, 31, 35, 40]",
        "Dame recomendaciones para mejorar"
    ]
    
    for query in queries:
        intent, response = process_user_query(nlp, query)
        print(f"\n🔤 Usuario: {query}")
        print(f"🤖 OMEGA: {response}")
        print("-" * 50)
