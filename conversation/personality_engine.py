#!/usr/bin/env python3
"""
🎭 OMEGA Personality Engine - Honest Statistical Communication
Adaptive personality that emphasizes statistical honesty and manages user expectations
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from conversation.context_store import ConversationContext
from conversation.intent_classifier import IntentType

logger = logging.getLogger(__name__)

@dataclass
class ResponseStyle:
    """Configuration for response generation"""
    verbosity: str  # "concise", "balanced", "detailed"
    technical_depth: float  # 0.0 to 1.0
    include_examples: bool
    include_disclaimers: bool
    emphasize_randomness: bool
    use_analogies: bool
    show_statistics: bool
    include_next_steps: bool
    tone: str  # "friendly", "professional", "academic"

class OmegaPersonality:
    """
    OMEGA's conversational personality engine
    Core traits: Honest, analytical, helpful, cautious about prediction claims
    """
    
    def __init__(self):
        self.core_traits = {
            "honest": True,           # Always transparent about limitations
            "analytical": True,       # Data-driven explanations
            "helpful": True,          # Genuinely tries to assist
            "cautious": True,         # Careful with prediction language
            "educational": True,      # Teaches statistical concepts
            "empathetic": True,       # Understands user hopes but stays realistic
            "precise": True,          # Technically accurate
            "encouraging": True       # Supports informed decision-making
        }
        
        self.communication_principles = {
            "never_guarantee_wins": True,
            "always_mention_randomness": True,
            "distinguish_analysis_from_prediction": True,
            "provide_context_for_statistics": True,
            "acknowledge_user_emotions": True,
            "educate_on_probability": True,
            "be_transparent_about_methods": True
        }
        
        self.expertise_adaptations = {
            "beginner": {
                "use_analogies": True,
                "avoid_jargon": True,
                "explain_basic_concepts": True,
                "emphasize_randomness_strongly": True,
                "provide_context": True
            },
            "intermediate": {
                "use_some_technical_terms": True,
                "provide_deeper_explanations": True,
                "show_methodology": True,
                "balance_technical_and_accessible": True
            },
            "expert": {
                "use_technical_language": True,
                "show_detailed_methodology": True,
                "include_statistical_measures": True,
                "reference_academic_concepts": True,
                "focus_on_limitations": True
            }
        }
    
    def adapt_response_style(self, context: ConversationContext, message: str, 
                           intent_result: Any) -> ResponseStyle:
        """
        Adapt response style based on user context and intent
        Prioritizes statistical honesty over user expectations
        """
        
        # Base style from user expertise
        base_config = self.expertise_adaptations.get(context.user_expertise_level, 
                                                   self.expertise_adaptations["intermediate"])
        
        # Technical depth based on context and intent
        tech_depth = self._calculate_technical_depth(context, intent_result)
        
        # Verbosity based on intent type and context
        verbosity = self._choose_verbosity(intent_result.intent_type, context)
        
        # Tone adaptation
        tone = self._choose_tone(context, intent_result)
        
        # Disclaimer requirements
        include_disclaimers = self._should_include_disclaimers(intent_result, context)
        emphasize_randomness = self._should_emphasize_randomness(intent_result, message)
        
        return ResponseStyle(
            verbosity=verbosity,
            technical_depth=tech_depth,
            include_examples=base_config.get("provide_context", False),
            include_disclaimers=include_disclaimers,
            emphasize_randomness=emphasize_randomness,
            use_analogies=base_config.get("use_analogies", False),
            show_statistics=intent_result.intent_type == IntentType.STATISTICAL_QUESTION,
            include_next_steps=self._should_include_next_steps(intent_result, context),
            tone=tone
        )
    
    def _calculate_technical_depth(self, context: ConversationContext, 
                                 intent_result: Any) -> float:
        """Calculate appropriate technical depth"""
        
        base_depth = context.technical_depth
        
        # Adjust based on intent type
        intent_adjustments = {
            IntentType.EXPLANATION_REQUEST: 0.2,  # More detailed for explanations
            IntentType.STATISTICAL_QUESTION: 0.3,  # Higher for statistics
            IntentType.GENERAL_CONVERSATION: -0.2,  # Less technical for general chat
            IntentType.RECOMMENDATION_REQUEST: -0.1,  # Slightly less for recommendations
        }
        
        adjustment = intent_adjustments.get(intent_result.intent_type, 0)
        adjusted_depth = base_depth + adjustment
        
        # Expertise constraints
        expertise_limits = {
            "beginner": (0.0, 0.4),
            "intermediate": (0.2, 0.7),
            "expert": (0.4, 1.0)
        }
        
        min_depth, max_depth = expertise_limits.get(context.user_expertise_level, (0.2, 0.7))
        return max(min_depth, min(max_depth, adjusted_depth))
    
    def _choose_verbosity(self, intent_type: IntentType, context: ConversationContext) -> str:
        """Choose response verbosity level"""
        
        # Intent-based defaults
        if intent_type == IntentType.GENERAL_CONVERSATION:
            return "concise"
        elif intent_type in [IntentType.EXPLANATION_REQUEST, IntentType.STATISTICAL_QUESTION]:
            return "detailed"
        elif intent_type == IntentType.SYSTEM_STATUS:
            return "balanced"
        else:
            return "balanced"
    
    def _choose_tone(self, context: ConversationContext, intent_result: Any) -> str:
        """Choose appropriate conversational tone"""
        
        if context.user_expertise_level == "expert":
            return "professional"
        elif intent_result.intent_type == IntentType.STATISTICAL_QUESTION:
            return "academic"
        else:
            return "friendly"
    
    def _should_include_disclaimers(self, intent_result: Any, context: ConversationContext) -> bool:
        """Determine if disclaimers should be included"""
        
        # Always include for recommendation requests
        if intent_result.intent_type == IntentType.RECOMMENDATION_REQUEST:
            return True
        
        # Include if honesty trigger detected
        if hasattr(intent_result, 'honesty_trigger') and intent_result.honesty_trigger:
            return True
        
        # Include for analysis requests about patterns
        if intent_result.intent_type in [IntentType.ANALYSIS_REQUEST, IntentType.PATTERN_INQUIRY]:
            return True
        
        # Respect user preferences if available
        if hasattr(context, 'honesty_preferences') and context.honesty_preferences:
            return context.honesty_preferences.get('show_disclaimers', True)
        
        return False
    
    def _should_emphasize_randomness(self, intent_result: Any, message: str) -> bool:
        """Determine if randomness should be strongly emphasized"""
        
        # Strong emphasis for prediction-like language
        if hasattr(intent_result, 'honesty_trigger') and intent_result.honesty_trigger:
            return True
        
        # Check for strong prediction words in message
        prediction_words = [
            "va a salir", "will come", "seguro", "sure", "garantiza", "guarantee",
            "siempre", "always", "nunca falla", "never fails", "exacto", "exact"
        ]
        
        message_lower = message.lower()
        if any(word in message_lower for word in prediction_words):
            return True
        
        return False
    
    def _should_include_next_steps(self, intent_result: Any, context: ConversationContext) -> bool:
        """Determine if next steps should be suggested"""
        
        # Include for explanation requests to encourage deeper learning
        if intent_result.intent_type == IntentType.EXPLANATION_REQUEST:
            return True
        
        # Include for beginners to guide them
        if context.user_expertise_level == "beginner":
            return True
        
        # Include for general conversation to keep engagement
        if intent_result.intent_type == IntentType.GENERAL_CONVERSATION:
            return True
        
        return False
    
    def generate_honesty_disclaimer(self, intent_type: IntentType, 
                                  emphasis_level: str, locale: str = "es") -> str:
        """
        Generate appropriate honesty disclaimer based on context
        emphasis_level: "mild", "strong", "very_strong"
        """
        
        disclaimers = {
            "es": {
                "mild": {
                    IntentType.RECOMMENDATION_REQUEST: (
                        "📊 *Nota*: Estas sugerencias se basan en análisis histórico. "
                        "Los sorteos son aleatorios y no hay garantías."
                    ),
                    IntentType.ANALYSIS_REQUEST: (
                        "📈 *Importante*: Este análisis examina datos pasados. "
                        "Cada sorteo es independiente de los anteriores."
                    ),
                    IntentType.PATTERN_INQUIRY: (
                        "🎲 *Realidad*: Aunque podemos observar patrones en datos históricos, "
                        "cada sorteo mantiene su aleatoriedad completa."
                    )
                },
                "strong": {
                    IntentType.RECOMMENDATION_REQUEST: (
                        "⚠️ **IMPORTANTE**: OMEGA analiza patrones históricos para sugerir números, "
                        "pero las loterías son juegos completamente aleatorios. "
                        "**No hay método que garantice ganar**. Juega solo lo que puedas permitirte perder."
                    ),
                    IntentType.ANALYSIS_REQUEST: (
                        "⚠️ **REALIDAD ESTADÍSTICA**: Este análisis examina el pasado, "
                        "pero cada sorteo es matemáticamente independiente. "
                        "Los resultados anteriores **no influyen** en futuros sorteos."
                    ),
                    IntentType.PATTERN_INQUIRY: (
                        "⚠️ **VERDAD MATEMÁTICA**: Aunque veamos 'patrones' en datos históricos, "
                        "esto es solo coincidencia estadística. Cada sorteo mantiene "
                        "exactamente la misma probabilidad aleatoria."
                    )
                },
                "very_strong": {
                    IntentType.RECOMMENDATION_REQUEST: (
                        "🚨 **ADVERTENCIA CRÍTICA**: \n\n"
                        "• Las loterías son **COMPLETAMENTE ALEATORIAS**\n"
                        "• **NINGÚN análisis predice resultados futuros**\n"
                        "• La probabilidad real de ganar es extremadamente baja\n"
                        "• Solo juega dinero que puedas permitirte perder completamente\n\n"
                        "OMEGA analiza patrones históricos únicamente para propósitos educativos."
                    )
                }
            },
            "en": {
                "mild": {
                    IntentType.RECOMMENDATION_REQUEST: (
                        "📊 *Note*: These suggestions are based on historical analysis. "
                        "Draws are random and there are no guarantees."
                    ),
                    IntentType.ANALYSIS_REQUEST: (
                        "📈 *Important*: This analysis examines past data. "
                        "Each draw is independent of previous ones."
                    )
                },
                "strong": {
                    IntentType.RECOMMENDATION_REQUEST: (
                        "⚠️ **IMPORTANT**: OMEGA analyzes historical patterns to suggest numbers, "
                        "but lotteries are completely random games. "
                        "**No method guarantees winning**. Only play what you can afford to lose."
                    )
                },
                "very_strong": {
                    IntentType.RECOMMENDATION_REQUEST: (
                        "🚨 **CRITICAL WARNING**: \n\n"
                        "• Lotteries are **COMPLETELY RANDOM**\n"
                        "• **NO analysis predicts future results**\n"
                        "• The real probability of winning is extremely low\n"
                        "• Only play money you can afford to lose completely\n\n"
                        "OMEGA analyzes historical patterns for educational purposes only."
                    )
                }
            }
        }
        
        try:
            return disclaimers[locale][emphasis_level].get(intent_type, 
                disclaimers[locale]["mild"].get(intent_type, ""))
        except KeyError:
            return disclaimers["es"]["mild"].get(intent_type, "")
    
    def generate_educational_context(self, topic: str, expertise_level: str, 
                                   locale: str = "es") -> str:
        """Generate educational context for statistical concepts"""
        
        contexts = {
            "es": {
                "probability_basics": {
                    "beginner": (
                        "🎯 **¿Qué significa probabilidad?**\n"
                        "Imagina una moneda: 50% cara, 50% cruz. En loterías es similar, "
                        "pero con millones de combinaciones posibles. Tu número tiene "
                        "la misma probabilidad que cualquier otro."
                    ),
                    "intermediate": (
                        "🎯 **Probabilidad en loterías:**\n"
                        "En Kábala (6 números de 40): 1 entre 3,838,380 combinaciones. "
                        "Esto significa 0.0000260% de probabilidad. Cada combinación "
                        "tiene exactamente la misma probabilidad, siempre."
                    ),
                    "expert": (
                        "🎯 **Análisis probabilístico:**\n"
                        "P(ganar) = 1/C(40,6) = 1/3,838,380 ≈ 2.6e-7\n"
                        "Distribución uniforme sobre el espacio muestral. "
                        "Independence assumption: cada sorteo es i.i.d."
                    )
                },
                "randomness_explanation": {
                    "beginner": (
                        "🎲 **¿Qué significa 'aleatorio'?**\n"
                        "Como tirar dados: no puedes controlar el resultado. "
                        "Las máquinas de lotería funcionan igual - cada número "
                        "tiene la misma oportunidad, sin importar qué salió antes."
                    ),
                    "intermediate": (
                        "🎲 **Aleatoriedad en sistemas de lotería:**\n"
                        "Los sorteos usan generadores de aleatoriedad certificados. "
                        "Cada evento es independiente - el resultado anterior "
                        "no afecta el siguiente. Es imposible predecir patrones futuros."
                    )
                }
            }
        }
        
        return contexts.get(locale, contexts["es"]).get(topic, {}).get(expertise_level, "")
    
    def generate_empathetic_response(self, user_emotion: str, locale: str = "es") -> str:
        """Generate empathetic responses that acknowledge emotions while staying honest"""
        
        responses = {
            "es": {
                "hopeful": (
                    "Entiendo tu esperanza de encontrar una ventaja en las loterías. "
                    "Es natural querer mejorar las probabilidades. OMEGA puede ayudarte "
                    "a entender los datos históricos, pero siempre manteniendo la "
                    "transparencia sobre las limitaciones reales."
                ),
                "frustrated": (
                    "Sé que puede ser frustrante que no existan métodos garantizados. "
                    "La realidad matemática de las loterías es difícil de aceptar. "
                    "Mi papel es darte información honesta para que tomes decisiones informadas."
                ),
                "curious": (
                    "¡Excelente curiosidad! La estadística detrás de las loterías "
                    "es fascinante, aunque los resultados prácticos son limitados. "
                    "Vamos a explorar los datos de manera educativa y transparente."
                )
            }
        }
        
        return responses.get(locale, responses["es"]).get(user_emotion, "")
    
    def should_redirect_to_responsible_gaming(self, message: str, context: ConversationContext) -> bool:
        """Determine if we should redirect to responsible gaming resources"""
        
        risk_indicators = [
            "necesito ganar", "need to win", "debo ganar", "must win",
            "perdi mucho", "lost a lot", "recuperar", "recover",
            "deuda", "debt", "prestamo", "loan", "urgente", "urgent",
            "ultima oportunidad", "last chance", "todo mi dinero", "all my money"
        ]
        
        message_lower = message.lower()
        return any(indicator in message_lower for indicator in risk_indicators)