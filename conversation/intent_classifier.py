#!/usr/bin/env python3
"""
🧠 OMEGA Intent Classifier - Robust ES/EN Classification
Classifies user intentions with honest statistical language
"""

import re
import unicodedata
import logging
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class IntentType(str, Enum):
    """User intent types - focused on statistical analysis"""
    ANALYSIS_REQUEST = "analysis_request"      # "Analiza los números más frecuentes"
    RECOMMENDATION_REQUEST = "recommendation_request"  # "Qué números me recomiendas"
    EXPLANATION_REQUEST = "explanation_request"  # "Cómo funciona tu análisis"
    PATTERN_INQUIRY = "pattern_inquiry"        # "¿Hay patrones en Kábala?"
    SYSTEM_STATUS = "system_status"            # "¿Está funcionando el sistema?"
    GENERAL_CONVERSATION = "general_conversation"  # "Hola, gracias"
    STATISTICAL_QUESTION = "statistical_question"  # "¿Cuál es la probabilidad real?"
    UNKNOWN = "unknown"

@dataclass
class ClassificationResult:
    """Result of intent classification"""
    intent_type: IntentType
    confidence: float
    matched_patterns: List[str]
    extracted_entities: Dict[str, Any]
    honesty_trigger: bool  # True if needs statistical honesty disclaimer

def strip_accents(text: str) -> str:
    """Remove accents for robust ES/EN normalization"""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

class OmegaIntentClassifier:
    """
    Robust intent classifier for OMEGA conversational AI
    Focus: Statistical analysis communication, not prediction
    """
    
    def __init__(self):
        self._compile_patterns()
        
        # Words that trigger honesty disclaimers
        self.prediction_trigger_words = [
            "predic", "predict", "forecast", "pronostic", "future",
            "futuro", "ganar", "win", "seguro", "guarantee", "exacto"
        ]
    
    def _compile_patterns(self):
        """Compile robust ES/EN patterns without accents"""
        
        self.patterns = {
            IntentType.ANALYSIS_REQUEST: [
                # Analysis of historical data
                re.compile(r"\b(analiz|analys|estudia|study|examina|examine)\w*", re.IGNORECASE),
                re.compile(r"\b(frecuencia|frequency|patron|pattern|tendencia|trend)\w*", re.IGNORECASE),
                re.compile(r"\b(historico|historical|pasado|past|datos|data)\w*", re.IGNORECASE),
                re.compile(r"\b(estadistica|statistics|metricas|metrics)", re.IGNORECASE),
                re.compile(r"\b(como van|how.*doing|rendimiento|performance)", re.IGNORECASE)
            ],
            
            IntentType.RECOMMENDATION_REQUEST: [
                # Asking for number suggestions (not predictions)
                re.compile(r"\b(recomienda|recommend|sugiere|suggest|aconsejas|advise)", re.IGNORECASE),
                re.compile(r"\b(que numeros|what numbers|cuales|which ones)", re.IGNORECASE),
                re.compile(r"\b(mejores|best|optimos|optimal|top)", re.IGNORECASE),
                re.compile(r"\b(jugarias|would.*play|elegirias|would.*choose)", re.IGNORECASE),
                re.compile(r"\b(dame|give me|muestrame|show me).*numeros", re.IGNORECASE)
            ],
            
            IntentType.EXPLANATION_REQUEST: [
                # How the system works
                re.compile(r"\b(explic|explain|como funciona|how.*work)\w*", re.IGNORECASE),
                re.compile(r"\b(que es|what is|que hace|what does|como hace|how does)", re.IGNORECASE),
                re.compile(r"\b(algoritmo|algorithm|metodo|method|proceso|process)", re.IGNORECASE),
                re.compile(r"\b(por que|why|para que|what for|ayudame|help me)", re.IGNORECASE),
                re.compile(r"\b(no entiendo|dont understand|significa|means)", re.IGNORECASE)
            ],
            
            IntentType.PATTERN_INQUIRY: [
                # Questions about patterns in lottery data
                re.compile(r"\b(patron|pattern|ciclo|cycle|secuencia|sequence)", re.IGNORECASE),
                re.compile(r"\b(repetir|repeat|salir|appear|frecuente|frequent)", re.IGNORECASE),
                re.compile(r"\b(hay|there.*is|existe|exists|se puede|can.*be)", re.IGNORECASE),
                re.compile(r"\b(numeros.*calientes|hot.*numbers|frios|cold)", re.IGNORECASE)
            ],
            
            IntentType.STATISTICAL_QUESTION: [
                # Probability and statistical questions
                re.compile(r"\b(probabilidad|probability|chance|posibilidad|odds)", re.IGNORECASE),
                re.compile(r"\b(cuanto.*probable|how.*likely|que tan|how much)", re.IGNORECASE),
                re.compile(r"\b(porcentaje|percentage|ratio|tasa|rate)", re.IGNORECASE),
                re.compile(r"\b(matematicamente|mathematically|estadisticamente)", re.IGNORECASE),
                re.compile(r"\b(valor esperado|expected value|ev|roi)", re.IGNORECASE)
            ],
            
            IntentType.SYSTEM_STATUS: [
                # System health and status
                re.compile(r"\b(status|estado|health|salud|funcionando|working)", re.IGNORECASE),
                re.compile(r"\b(disponible|available|online|activo|active)", re.IGNORECASE),
                re.compile(r"\b(ultimo.*analisis|last.*analysis|reporte|report)", re.IGNORECASE),
                re.compile(r"\b(servidor|server|sistema|system|omega)", re.IGNORECASE)
            ],
            
            IntentType.GENERAL_CONVERSATION: [
                # Greetings and social
                re.compile(r"\b(hola|hello|hi|buenas|good|saludos|greetings)", re.IGNORECASE),
                re.compile(r"\b(gracias|thanks|thank you|merci|muchas gracias)", re.IGNORECASE),
                re.compile(r"\b(que tal|how are you|como estas|como va|adios|bye)", re.IGNORECASE),
                re.compile(r"\b(perdon|sorry|disculpa|excuse)", re.IGNORECASE)
            ]
        }
    
    def classify(self, message: str) -> ClassificationResult:
        """
        Classify user message with confidence scoring
        Returns structured classification result
        """
        normalized = strip_accents(message.lower())
        
        # Check if message contains prediction-trigger words
        honesty_trigger = any(
            trigger in normalized for trigger in self.prediction_trigger_words
        )
        
        # Score each intent type
        scores = {}
        all_matches = {}
        
        for intent_type, pattern_list in self.patterns.items():
            score = 0
            matches = []
            
            for pattern in pattern_list:
                if pattern.search(normalized):
                    score += 1
                    matches.append(pattern.pattern)
            
            if score > 0:
                scores[intent_type] = score
                all_matches[intent_type] = matches
        
        # No matches found
        if not scores:
            return ClassificationResult(
                intent_type=IntentType.UNKNOWN,
                confidence=0.3,
                matched_patterns=[],
                extracted_entities={},
                honesty_trigger=honesty_trigger
            )
        
        # Find best match with confidence calculation
        best_intent, best_score = max(scores.items(), key=lambda x: x[1])
        
        # Confidence based on pattern matches and message length
        base_confidence = 0.4 + (best_score * 0.15)  # 0.4 + 0.15 per match
        length_bonus = min(0.2, len(message.split()) * 0.02)  # Longer = more confident
        confidence = min(0.95, base_confidence + length_bonus)
        
        # Extract entities based on intent type
        entities = self._extract_entities(normalized, best_intent)
        
        return ClassificationResult(
            intent_type=best_intent,
            confidence=confidence,
            matched_patterns=all_matches[best_intent],
            extracted_entities=entities,
            honesty_trigger=honesty_trigger
        )
    
    def _extract_entities(self, normalized_message: str, intent_type: IntentType) -> Dict[str, Any]:
        """Extract entities specific to each intent type"""
        entities = {}
        
        if intent_type == IntentType.RECOMMENDATION_REQUEST:
            # Extract number of recommendations requested
            top_n_patterns = [
                r"\b(\d+)\s*(mejores|top|primeras|best|first)",
                r"\b(top|mejores)\s*(\d+)",
                r"\bdame\s*(\d+)",
                r"\b(\d+)\s*(numeros|numbers|combinaciones|combinations)"
            ]
            
            for pattern in top_n_patterns:
                match = re.search(pattern, normalized_message)
                if match:
                    # Extract the number, handle both capture group positions
                    for group in match.groups():
                        if group and group.isdigit():
                            entities["top_n"] = min(int(group), 10)  # Max 10
                            break
                    break
            
            # Extract specific lottery game
            if any(word in normalized_message for word in ["kabala", "peru", "pe"]):
                entities["game_id"] = "kabala_pe"
            elif any(word in normalized_message for word in ["mega", "brasil", "brazil", "br"]):
                entities["game_id"] = "megasena_br"
            elif any(word in normalized_message for word in ["powerball", "usa", "us"]):
                entities["game_id"] = "powerball_us"
        
        elif intent_type == IntentType.ANALYSIS_REQUEST:
            # Extract analysis period
            if any(word in normalized_message for word in ["ultima semana", "last week", "7 dias", "7 days"]):
                entities["period"] = "week"
            elif any(word in normalized_message for word in ["ultimo mes", "last month", "30 dias", "30 days"]):
                entities["period"] = "month"
            elif any(word in normalized_message for word in ["ultimo ano", "last year", "365 dias"]):
                entities["period"] = "year"
            
            # Extract analysis type
            if any(word in normalized_message for word in ["frecuencia", "frequency"]):
                entities["analysis_type"] = "frequency"
            elif any(word in normalized_message for word in ["patron", "pattern"]):
                entities["analysis_type"] = "pattern"
            elif any(word in normalized_message for word in ["tendencia", "trend"]):
                entities["analysis_type"] = "trend"
        
        elif intent_type == IntentType.STATISTICAL_QUESTION:
            # Extract statistical concept
            if any(word in normalized_message for word in ["probabilidad", "probability"]):
                entities["stat_concept"] = "probability"
            elif any(word in normalized_message for word in ["valor esperado", "expected value", "ev"]):
                entities["stat_concept"] = "expected_value"
            elif any(word in normalized_message for word in ["odds", "chances"]):
                entities["stat_concept"] = "odds"
        
        elif intent_type == IntentType.EXPLANATION_REQUEST:
            # Extract explanation level requested
            if any(word in normalized_message for word in ["simple", "basico", "facil", "principiante"]):
                entities["explanation_level"] = "basic"
            elif any(word in normalized_message for word in ["tecnico", "technical", "detallado", "detailed"]):
                entities["explanation_level"] = "technical"
            elif any(word in normalized_message for word in ["matematico", "mathematical", "estadistico"]):
                entities["explanation_level"] = "mathematical"
        
        return entities
    
    def get_honesty_disclaimer(self, intent_type: IntentType, locale: str = "es") -> Optional[str]:
        """Get appropriate honesty disclaimer for intent type"""
        
        disclaimers = {
            "es": {
                IntentType.RECOMMENDATION_REQUEST: (
                    "⚠️ **Importante**: OMEGA analiza patrones históricos para sugerir números, "
                    "pero las loterías son juegos completamente aleatorios. No hay garantías de ganar."
                ),
                IntentType.ANALYSIS_REQUEST: (
                    "📊 **Nota**: Este análisis se basa en datos históricos. "
                    "Los resultados pasados no influyen en futuros sorteos."
                ),
                IntentType.STATISTICAL_QUESTION: (
                    "🎲 **Realidad matemática**: En loterías, cada sorteo es independiente. "
                    "La probabilidad real siempre es la misma, sin importar patrones pasados."
                )
            },
            "en": {
                IntentType.RECOMMENDATION_REQUEST: (
                    "⚠️ **Important**: OMEGA analyzes historical patterns to suggest numbers, "
                    "but lotteries are completely random games. No guarantees of winning."
                ),
                IntentType.ANALYSIS_REQUEST: (
                    "📊 **Note**: This analysis is based on historical data. "
                    "Past results do not influence future draws."
                ),
                IntentType.STATISTICAL_QUESTION: (
                    "🎲 **Mathematical reality**: In lotteries, each draw is independent. "
                    "The real probability is always the same, regardless of past patterns."
                )
            }
        }
        
        return disclaimers.get(locale, disclaimers["es"]).get(intent_type)
    
    def should_emphasize_randomness(self, message: str) -> bool:
        """
        Determine if we should strongly emphasize randomness
        Returns True for messages with prediction language
        """
        normalized = strip_accents(message.lower())
        
        strong_prediction_words = [
            "predice", "predict", "va a salir", "will come", "seguro que", "sure that",
            "garantiza", "guarantee", "exacto", "exact", "siempre", "always",
            "nunca falla", "never fails", "100%", "infalible", "infallible"
        ]
        
        return any(word in normalized for word in strong_prediction_words)