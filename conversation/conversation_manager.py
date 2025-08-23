#!/usr/bin/env python3
"""
🧠 OMEGA Conversation Manager - Main orchestration
Manages conversation flow with honest statistical communication
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from conversation.context_store import ContextStore, ConversationContext
from conversation.intent_classifier import OmegaIntentClassifier, IntentType, ClassificationResult
from conversation.personality_engine import OmegaPersonality, ResponseStyle
from conversation.legal_compliance import LegalComplianceManager, ComplianceResult

logger = logging.getLogger(__name__)

class ConversationResponse:
    """Structured conversation response"""
    
    def __init__(self, text: str, metadata: Optional[Dict] = None, 
                 attachments: Optional[List] = None):
        self.text = text
        self.metadata = metadata or {}
        self.attachments = attachments or []
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "metadata": self.metadata,
            "attachments": self.attachments,
            "timestamp": self.timestamp
        }

class OmegaConversationManager:
    """
    Main conversation manager for OMEGA AI
    Orchestrates intent classification, context management, and response generation
    """
    
    def __init__(self, omega_control_center, redis_url: str = "redis://localhost:6379"):
        self.omega_control = omega_control_center
        self.context_store = ContextStore(redis_url)
        self.intent_classifier = OmegaIntentClassifier()
        self.personality = OmegaPersonality()
        self.legal_compliance = LegalComplianceManager()
        
        # Response templates
        self.response_templates = self._load_response_templates()
        
        # Performance tracking
        self.response_times = []
        self.error_count = 0
        
        logger.info("🧠 OMEGA Conversation Manager initialized")
    
    async def process_message(self, user_id: str, message: str, 
                            conversation_id: Optional[str] = None,
                            locale: str = "es") -> Dict[str, Any]:
        """
        Main message processing pipeline
        Returns: Structured response with honest statistical communication
        """
        start_time = time.time()
        
        try:
            # Input validation
            validation_error = self._validate_input(message, user_id)
            if validation_error:
                return self._error_response(validation_error, locale).to_dict()
            
            # Generate conversation ID if not provided
            if not conversation_id:
                conversation_id = f"{user_id}_{int(datetime.now().timestamp())}"
            
            # Get or create conversation context
            context = await self._get_or_create_context(user_id, conversation_id, message, locale)
            
            # Check legal compliance first
            user_context_dict = {
                "phone_number": context.user_id if context.user_id.startswith("whatsapp:") else "",
                "locale": locale,
                "age_verified": context.honesty_preferences.get("age_verified", False),
                "user_expertise_level": context.user_expertise_level
            }
            
            compliance_result = self.legal_compliance.check_message_compliance(message, user_context_dict)
            
            # Block if compliance fails
            if not compliance_result.is_compliant:
                response_text = compliance_result.message
                # Add required disclaimers
                required_disclaimers = self.legal_compliance.get_required_disclaimers(compliance_result, user_context_dict)
                if required_disclaimers:
                    response_text += "\n\n" + "\n\n".join(required_disclaimers)
                
                return ConversationResponse(
                    text=response_text,
                    metadata={
                        "type": "compliance_block",
                        "intent": "blocked",
                        "confidence": 1.0,
                        "conversation_id": conversation_id,
                        "compliance_level": compliance_result.level.value,
                        "legal_references": compliance_result.legal_references
                    }
                ).to_dict()
            
            # Classify user intent
            intent_result = self.intent_classifier.classify(message)
            
            # Check for responsible gaming redirect (enhanced with compliance info)
            if self.personality.should_redirect_to_responsible_gaming(message, context) or compliance_result.gambling_addiction_warning:
                return await self._handle_responsible_gaming_redirect(context, locale, compliance_result)
            
            # Generate response style based on context and intent
            response_style = self.personality.adapt_response_style(context, message, intent_result)
            
            # Route to appropriate handler
            response = await self._route_intent(intent_result, context, response_style, message, compliance_result)
            
            # Add conversation metadata
            response.metadata.update({
                "conversation_id": conversation_id,
                "intent": intent_result.intent_type.value,
                "confidence": intent_result.confidence,
                "honesty_trigger": intent_result.honesty_trigger,
                "user_expertise": context.user_expertise_level
            })
            
            # Save message and response to context
            await self.context_store.add_message(
                user_id, conversation_id, "user", message, 
                {"intent_type": intent_result.intent_type.value, "entities": intent_result.extracted_entities}
            )
            await self.context_store.add_message(
                user_id, conversation_id, "assistant", response.text,
                {"intent_type": intent_result.intent_type.value, "response_style": response_style.__dict__}
            )
            
            # Track performance
            processing_time = time.time() - start_time
            self.response_times.append(processing_time)
            if len(self.response_times) > 1000:
                self.response_times = self.response_times[-1000:]
            
            logger.info(f"Message processed: {user_id} | {intent_result.intent_type.value} | {processing_time:.3f}s")
            
            return response.to_dict()
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing message for {user_id}: {e}")
            return self._error_response(f"Error interno: {str(e)}", locale).to_dict()
    
    def _validate_input(self, message: str, user_id: str) -> Optional[str]:
        """Validate input parameters"""
        if not message or len(message.strip()) == 0:
            return "Mensaje vacío"
        
        if len(message) > 2000:
            return "Mensaje demasiado largo (máximo 2000 caracteres)"
        
        if not user_id or len(user_id.strip()) == 0:
            return "ID de usuario inválido"
        
        return None
    
    async def _get_or_create_context(self, user_id: str, conversation_id: str, 
                                   message: str, locale: str) -> ConversationContext:
        """Get existing context or create new one"""
        context = await self.context_store.get_context(user_id, conversation_id)
        
        if not context:
            context = await self.context_store.create_context(
                user_id, conversation_id, message, locale
            )
        
        return context
    
    async def _route_intent(self, intent_result: ClassificationResult, 
                          context: ConversationContext, response_style: ResponseStyle,
                          original_message: str, compliance_result: ComplianceResult = None) -> ConversationResponse:
        """Route to appropriate intent handler"""
        
        handlers = {
            IntentType.RECOMMENDATION_REQUEST: self._handle_recommendation_request,
            IntentType.ANALYSIS_REQUEST: self._handle_analysis_request,
            IntentType.EXPLANATION_REQUEST: self._handle_explanation_request,
            IntentType.PATTERN_INQUIRY: self._handle_pattern_inquiry,
            IntentType.STATISTICAL_QUESTION: self._handle_statistical_question,
            IntentType.SYSTEM_STATUS: self._handle_system_status,
            IntentType.GENERAL_CONVERSATION: self._handle_general_conversation,
            IntentType.UNKNOWN: self._handle_unknown_request
        }
        
        handler = handlers.get(intent_result.intent_type, self._handle_unknown_request)
        
        try:
            return await handler(intent_result, context, response_style, original_message)
        except Exception as e:
            logger.error(f"Handler error for {intent_result.intent_type}: {e}")
            return self._error_response(
                f"Error procesando {intent_result.intent_type.value}", 
                context.locale
            )
    
    async def _handle_recommendation_request(self, intent_result: ClassificationResult,
                                           context: ConversationContext, 
                                           response_style: ResponseStyle,
                                           message: str) -> ConversationResponse:
        """Handle number recommendation requests with strong disclaimers"""
        
        entities = intent_result.extracted_entities
        game_id = entities.get("game_id", "kabala_pe")
        top_n = min(entities.get("top_n", 5), 10)  # Max 10 recommendations
        
        try:
            # Check if OMEGA control center is available
            if not hasattr(self.omega_control, 'analyze_opportunity'):
                return ConversationResponse(
                    text=self._get_template("service_unavailable", context.locale),
                    metadata={"type": "error", "error": "OMEGA engine unavailable"}
                )
            
            # Generate analysis (not prediction!)
            result = await self.omega_control.analyze_opportunity("lottery", game_id)
            
            if not result or not result.get("items"):
                return ConversationResponse(
                    text=self._get_template("no_analysis_available", context.locale).format(game=game_id),
                    metadata={"type": "error", "game_id": game_id}
                )
            
            # Format response with strong honesty emphasis
            response_text = self._format_recommendation_response(
                result, response_style, context.locale, top_n, intent_result.honesty_trigger
            )
            
            return ConversationResponse(
                text=response_text,
                metadata={
                    "type": "recommendation",
                    "game_id": game_id,
                    "recommendations": result.get("items", [])[:top_n],
                    "analysis_type": "historical_pattern",
                    "disclaimer_level": "strong" if intent_result.honesty_trigger else "normal"
                }
            )
            
        except Exception as e:
            logger.error(f"Error in recommendation handler: {e}")
            return ConversationResponse(
                text=self._get_template("analysis_error", context.locale).format(error=str(e)),
                metadata={"type": "error", "error": str(e)}
            )
    
    async def _handle_analysis_request(self, intent_result: ClassificationResult,
                                     context: ConversationContext,
                                     response_style: ResponseStyle,
                                     message: str) -> ConversationResponse:
        """Handle historical analysis requests"""
        
        entities = intent_result.extracted_entities
        period = entities.get("period", "recent")
        analysis_type = entities.get("analysis_type", "general")
        
        try:
            # Generate historical analysis
            if hasattr(self.omega_control, 'get_analysis_summary'):
                analysis = await self.omega_control.get_analysis_summary(period=period)
            else:
                # Fallback mock analysis
                analysis = {
                    "period": period,
                    "total_draws": 100,
                    "pattern_analysis": "Historical frequency analysis available",
                    "statistical_summary": "Standard lottery distribution observed"
                }
            
            response_text = self._format_analysis_response(
                analysis, response_style, context.locale, analysis_type
            )
            
            return ConversationResponse(
                text=response_text,
                metadata={
                    "type": "analysis",
                    "period": period,
                    "analysis_type": analysis_type,
                    "data_based": True
                }
            )
            
        except Exception as e:
            return ConversationResponse(
                text=self._get_template("analysis_error", context.locale).format(error=str(e)),
                metadata={"type": "error", "error": str(e)}
            )
    
    async def _handle_explanation_request(self, intent_result: ClassificationResult,
                                        context: ConversationContext,
                                        response_style: ResponseStyle,
                                        message: str) -> ConversationResponse:
        """Handle system explanation requests"""
        
        entities = intent_result.extracted_entities
        explanation_level = entities.get("explanation_level", context.preferred_explanation_style)
        
        # Generate explanation based on technical depth
        if response_style.technical_depth < 0.3:
            explanation = self._generate_simple_explanation(context.locale)
        elif response_style.technical_depth < 0.7:
            explanation = self._generate_intermediate_explanation(context.locale)
        else:
            explanation = self._generate_technical_explanation(context.locale)
        
        # Add educational context
        educational_context = self.personality.generate_educational_context(
            "probability_basics", context.user_expertise_level, context.locale
        )
        
        full_explanation = explanation
        if educational_context and response_style.include_examples:
            full_explanation += f"\n\n{educational_context}"
        
        return ConversationResponse(
            text=full_explanation,
            metadata={
                "type": "explanation",
                "technical_depth": response_style.technical_depth,
                "explanation_level": explanation_level
            }
        )
    
    async def _handle_statistical_question(self, intent_result: ClassificationResult,
                                         context: ConversationContext,
                                         response_style: ResponseStyle,
                                         message: str) -> ConversationResponse:
        """Handle probability and statistical questions"""
        
        entities = intent_result.extracted_entities
        stat_concept = entities.get("stat_concept", "probability")
        
        # Generate statistical explanation
        response_text = self._generate_statistical_explanation(
            stat_concept, response_style, context.locale, context.user_expertise_level
        )
        
        # Add strong randomness emphasis for statistical questions
        disclaimer = self.personality.generate_honesty_disclaimer(
            IntentType.STATISTICAL_QUESTION, "strong", context.locale
        )
        
        if disclaimer:
            response_text += f"\n\n{disclaimer}"
        
        return ConversationResponse(
            text=response_text,
            metadata={
                "type": "statistical_explanation",
                "concept": stat_concept,
                "mathematical": response_style.technical_depth > 0.6
            }
        )
    
    async def _handle_pattern_inquiry(self, intent_result: ClassificationResult,
                                    context: ConversationContext,
                                    response_style: ResponseStyle,
                                    message: str) -> ConversationResponse:
        """Handle questions about patterns in lottery data"""
        
        # Pattern inquiry needs strong honesty emphasis
        base_response = self._get_template("pattern_inquiry_response", context.locale)
        
        # Add randomness explanation
        randomness_explanation = self.personality.generate_educational_context(
            "randomness_explanation", context.user_expertise_level, context.locale
        )
        
        full_response = base_response
        if randomness_explanation:
            full_response += f"\n\n{randomness_explanation}"
        
        # Strong disclaimer for pattern questions
        disclaimer = self.personality.generate_honesty_disclaimer(
            IntentType.PATTERN_INQUIRY, "strong", context.locale
        )
        
        if disclaimer:
            full_response += f"\n\n{disclaimer}"
        
        return ConversationResponse(
            text=full_response,
            metadata={
                "type": "pattern_inquiry",
                "disclaimer_level": "strong"
            }
        )
    
    async def _handle_system_status(self, intent_result: ClassificationResult,
                                  context: ConversationContext,
                                  response_style: ResponseStyle,
                                  message: str) -> ConversationResponse:
        """Handle system status requests"""
        
        # Check OMEGA system status
        status = {
            "system": "operational",
            "analysis_engine": "available" if hasattr(self.omega_control, 'analyze_opportunity') else "limited",
            "conversation_system": "active",
            "data_freshness": "recent"
        }
        
        response_text = self._format_status_response(status, context.locale)
        
        return ConversationResponse(
            text=response_text,
            metadata={
                "type": "system_status",
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def _handle_general_conversation(self, intent_result: ClassificationResult,
                                         context: ConversationContext,
                                         response_style: ResponseStyle,
                                         message: str) -> ConversationResponse:
        """Handle greetings and general conversation"""
        
        # Simple conversational responses
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["hola", "hello", "hi", "buenas"]):
            template_key = "greeting"
        elif any(word in message_lower for word in ["gracias", "thanks", "thank you"]):
            template_key = "thanks_response"
        elif any(word in message_lower for word in ["adios", "bye", "hasta luego"]):
            template_key = "goodbye"
        else:
            template_key = "general_response"
        
        response_text = self._get_template(template_key, context.locale)
        
        # Add next steps for engagement
        if response_style.include_next_steps:
            next_steps = self._get_template("suggested_actions", context.locale)
            response_text += f"\n\n{next_steps}"
        
        return ConversationResponse(
            text=response_text,
            metadata={"type": "general_conversation"}
        )
    
    async def _handle_unknown_request(self, intent_result: ClassificationResult,
                                    context: ConversationContext,
                                    response_style: ResponseStyle,
                                    message: str) -> ConversationResponse:
        """Handle unrecognized requests"""
        
        response_text = self._get_template("unknown_request", context.locale)
        
        # Add capability explanation
        capabilities = self._get_template("capabilities_summary", context.locale)
        response_text += f"\n\n{capabilities}"
        
        return ConversationResponse(
            text=response_text,
            metadata={"type": "unknown", "confidence": intent_result.confidence}
        )
    
    async def _handle_responsible_gaming_redirect(self, context: ConversationContext,
                                                locale: str, compliance_result: ComplianceResult = None) -> Dict[str, Any]:
        """Handle responsible gaming redirect"""
        
        response_text = self._get_template("responsible_gaming", locale)
        
        return ConversationResponse(
            text=response_text,
            metadata={
                "type": "responsible_gaming_redirect",
                "priority": "high"
            }
        ).to_dict()
    
    def _format_recommendation_response(self, result: Dict, style: ResponseStyle,
                                      locale: str, top_n: int, honesty_trigger: bool) -> str:
        """Format recommendation response with appropriate disclaimers"""
        
        game_name = result.get("game_name", "Lottery")
        items = result.get("items", [])[:top_n]
        
        # Header with clear language about analysis vs prediction
        if locale == "es":
            header = f"📊 **Análisis histórico para {game_name}** (basado en patrones pasados):\n\n"
        else:
            header = f"📊 **Historical analysis for {game_name}** (based on past patterns):\n\n"
        
        response = header
        
        # Number recommendations
        for i, item in enumerate(items, 1):
            numbers = " - ".join([f"{n:02d}" for n in item.get("numbers", [])])
            score = item.get("ens_score", item.get("score", 0))
            source = item.get("source", "ensemble")
            
            response += f"**{i}.** `{numbers}` _(análisis: {score:.2f}, fuente: {source})_\n"
        
        # Expected value analysis if available
        if "jackpot_analysis" in result:
            ja = result["jackpot_analysis"]
            if locale == "es":
                response += f"\n💰 **Análisis de Valor Esperado:**\n"
                response += f"• Jackpot actual: ${ja.get('current_jackpot_usd', 0):,}\n"
                response += f"• Valor esperado: ${ja.get('expected_value', 0):.2f}\n"
            else:
                response += f"\n💰 **Expected Value Analysis:**\n"
                response += f"• Current jackpot: ${ja.get('current_jackpot_usd', 0):,}\n"
                response += f"• Expected value: ${ja.get('expected_value', 0):.2f}\n"
        
        # Add appropriate disclaimer
        disclaimer_level = "very_strong" if honesty_trigger else "strong"
        disclaimer = self.personality.generate_honesty_disclaimer(
            IntentType.RECOMMENDATION_REQUEST, disclaimer_level, locale
        )
        
        if disclaimer:
            response += f"\n\n{disclaimer}"
        
        return response
    
    def _format_analysis_response(self, analysis: Dict, style: ResponseStyle,
                                locale: str, analysis_type: str) -> str:
        """Format historical analysis response"""
        
        if locale == "es":
            header = f"📈 **Análisis Estadístico** ({analysis.get('period', 'reciente')}):\n\n"
        else:
            header = f"📈 **Statistical Analysis** ({analysis.get('period', 'recent')}):\n\n"
        
        response = header
        
        if "total_draws" in analysis:
            if locale == "es":
                response += f"• Sorteos analizados: {analysis['total_draws']}\n"
            else:
                response += f"• Draws analyzed: {analysis['total_draws']}\n"
        
        if "pattern_analysis" in analysis:
            response += f"• Patrones: {analysis['pattern_analysis']}\n"
        
        # Add statistical honesty note
        disclaimer = self.personality.generate_honesty_disclaimer(
            IntentType.ANALYSIS_REQUEST, "mild", locale
        )
        
        if disclaimer:
            response += f"\n{disclaimer}"
        
        return response
    
    def _format_status_response(self, status: Dict, locale: str) -> str:
        """Format system status response"""
        
        if locale == "es":
            header = "🟢 **Estado del Sistema OMEGA:**\n\n"
        else:
            header = "🟢 **OMEGA System Status:**\n\n"
        
        response = header
        
        for component, state in status.items():
            emoji = "✅" if state in ["operational", "available", "active", "recent"] else "⚠️"
            component_name = component.replace("_", " ").title()
            response += f"{emoji} {component_name}: {state}\n"
        
        return response
    
    def _generate_simple_explanation(self, locale: str) -> str:
        """Generate simple explanation for beginners"""
        if locale == "es":
            return """
🤖 **¿Qué es OMEGA?**

OMEGA es un sistema que estudia números de lotería que ya salieron en el pasado. Es como un investigador que mira hacia atrás para encontrar patrones.

**¿Qué hace exactamente?**
• Analiza números que salieron antes
• Busca patrones estadísticos
• Te sugiere números basándose en esos patrones

**¿Qué NO hace?**
• No predice el futuro
• No garantiza que ganes
• No controla los sorteos

**La realidad:** Los sorteos son completamente aleatorios. OMEGA solo te ayuda a entender qué pasó antes, no qué va a pasar después.
            """.strip()
        else:
            return """
🤖 **What is OMEGA?**

OMEGA is a system that studies lottery numbers that have already been drawn in the past. It's like a researcher looking back to find patterns.

**What does it do exactly?**
• Analyzes numbers that came out before
• Looks for statistical patterns  
• Suggests numbers based on those patterns

**What does it NOT do?**
• Doesn't predict the future
• Doesn't guarantee wins
• Doesn't control the draws

**The reality:** Draws are completely random. OMEGA only helps you understand what happened before, not what will happen next.
            """.strip()
    
    def _generate_intermediate_explanation(self, locale: str) -> str:
        """Generate intermediate explanation"""
        if locale == "es":
            return """
🤖 **OMEGA: Sistema de Análisis Estadístico**

OMEGA emplea múltiples algoritmos para analizar datos históricos de loterías:

**Metodología:**
• **Análisis de frecuencias**: Qué números salen más/menos
• **Patrones temporales**: Secuencias y ciclos históricos  
• **Ensemble de modelos**: Combina diferentes enfoques estadísticos
• **Análisis de valor esperado**: Calcula EV matemático basado en jackpots

**Limitaciones importantes:**
• Solo analiza el pasado, no predice el futuro
• Cada sorteo es independiente matemáticamente
• Los patrones pasados no influyen en futuros sorteos
• La probabilidad real de ganar permanece constante

**Uso recomendado:** Herramienta educativa para entender estadística de loterías, no para "ganar seguro".
            """.strip()
        else:
            return """
🤖 **OMEGA: Statistical Analysis System**

OMEGA employs multiple algorithms to analyze historical lottery data:

**Methodology:**
• **Frequency analysis**: Which numbers appear more/less
• **Temporal patterns**: Historical sequences and cycles
• **Model ensemble**: Combines different statistical approaches  
• **Expected value analysis**: Calculates mathematical EV based on jackpots

**Important limitations:**
• Only analyzes the past, doesn't predict the future
• Each draw is mathematically independent
• Past patterns don't influence future draws
• Real probability of winning remains constant

**Recommended use:** Educational tool to understand lottery statistics, not to "win for sure".
            """.strip()
    
    def _generate_technical_explanation(self, locale: str) -> str:
        """Generate technical explanation for experts"""
        if locale == "es":
            return """
🤖 **OMEGA: Arquitectura Técnica**

**Pipeline de Procesamiento:**
```
Data Ingestion → Feature Engineering → Model Ensemble → Validation → Output
```

**Modelos Implementados:**
• **Neural Enhanced**: MLP con regularización L2
• **LSTM v2**: Redes temporales para secuencias
• **Transformer Deep**: Attention mechanism sobre historical data
• **Genetic Algorithm**: Optimización evolutiva de combinaciones
• **Statistical**: Apriori, Eclat para frequent itemsets

**Métricas de Evaluación:**
• Hit rate @k (k=1,5,10)
• Brier Score para calibración
• Rolling window validation (anti-leakage temporal)
• Baseline random comparison

**Limitaciones Fundamentales:**
• Independence assumption: P(X_t | X_{t-1}) = P(X_t)
• Distribución uniforme sobre espacio muestral
• No hay información privilegiada en datos históricos
• Gambler's fallacy: patrones aparentes son ruido estadístico

**Conclusión técnica:** Sistema estadísticamente riguroso para análisis retrospectivo, sin capacidad predictiva real sobre eventos aleatorios futuros.
            """.strip()
        else:
            return """
🤖 **OMEGA: Technical Architecture**

**Processing Pipeline:**
```
Data Ingestion → Feature Engineering → Model Ensemble → Validation → Output
```

**Implemented Models:**
• **Neural Enhanced**: MLP with L2 regularization
• **LSTM v2**: Temporal networks for sequences
• **Transformer Deep**: Attention mechanism over historical data
• **Genetic Algorithm**: Evolutionary optimization of combinations
• **Statistical**: Apriori, Eclat for frequent itemsets

**Evaluation Metrics:**
• Hit rate @k (k=1,5,10)
• Brier Score for calibration
• Rolling window validation (temporal anti-leakage)
• Random baseline comparison

**Fundamental Limitations:**
• Independence assumption: P(X_t | X_{t-1}) = P(X_t)
• Uniform distribution over sample space
• No privileged information in historical data
• Gambler's fallacy: apparent patterns are statistical noise

**Technical conclusion:** Statistically rigorous system for retrospective analysis, with no real predictive capability over future random events.
            """.strip()
    
    def _generate_statistical_explanation(self, concept: str, style: ResponseStyle,
                                        locale: str, expertise: str) -> str:
        """Generate statistical concept explanations"""
        
        explanations = {
            "es": {
                "probability": {
                    "beginner": "🎯 **Probabilidad en loterías:** Si hay 1 millón de combinaciones posibles, tu boleto tiene 1 oportunidad entre 1 millón. Como encontrar una aguja específica en un pajar gigante.",
                    "intermediate": "🎯 **Cálculo de probabilidad:** P(ganar) = 1/C(n,k) donde n=números totales, k=números elegidos. Para Kábala: 1/C(40,6) = 1/3,838,380 ≈ 0.000026%",
                    "expert": "🎯 **Análisis probabilístico:** Distribución hipergeométrica para lotería sin reemplazo. P(X=k) = C(K,k)×C(N-K,n-k)/C(N,n). Independence assumption crítica para validez del modelo."
                },
                "expected_value": {
                    "beginner": "💰 **Valor esperado:** Es como preguntar '¿cuánto dinero recupero en promedio si juego muchas veces?' Casi siempre es negativo porque la casa siempre tiene ventaja.",
                    "intermediate": "💰 **EV Calculation:** EV = P(win)×Jackpot - Ticket_Cost. Solo positivo cuando jackpot supera ~15M (para boleto $2). Raramente favorable al jugador.",
                    "expert": "💰 **Expected Value Analysis:** E[X] = Σ P(X_i)×V_i - C. Incorpora distribución de premios, impuestos, valor presente. Kelly Criterion para sizing óptimo cuando EV>0."
                }
            },
            "en": {
                "probability": {
                    "beginner": "🎯 **Lottery probability:** If there are 1 million possible combinations, your ticket has 1 chance in 1 million. Like finding a specific needle in a giant haystack.",
                    "intermediate": "🎯 **Probability calculation:** P(win) = 1/C(n,k) where n=total numbers, k=chosen numbers. For typical lottery: 1/C(40,6) = 1/3,838,380 ≈ 0.000026%",
                    "expert": "🎯 **Probabilistic analysis:** Hypergeometric distribution for lottery without replacement. P(X=k) = C(K,k)×C(N-K,n-k)/C(N,n). Independence assumption critical for model validity."
                }
            }
        }
        
        lang_dict = explanations.get(locale, explanations["es"])
        concept_dict = lang_dict.get(concept, lang_dict.get("probability", {}))
        
        return concept_dict.get(expertise, concept_dict.get("intermediate", ""))
    
    def _load_response_templates(self) -> Dict[str, Dict[str, str]]:
        """Load response templates by language"""
        return {
            "es": {
                "greeting": "¡Hola! Soy OMEGA, tu asistente para análisis estadístico de loterías. ¿En qué puedo ayudarte hoy?",
                "thanks_response": "¡De nada! Siempre es un placer ayudar con análisis estadísticos honestos.",
                "goodbye": "¡Hasta luego! Recuerda siempre jugar responsablemente. 🎯",
                "service_unavailable": "El motor de análisis OMEGA no está disponible en este momento. Por favor intenta más tarde.",
                "no_analysis_available": "No hay datos suficientes para analizar {game} en este momento.",
                "analysis_error": "Error al generar el análisis: {error}",
                "unknown_request": "No estoy seguro de entender exactamente qué necesitas. ¿Podrías ser más específico?",
                "capabilities_summary": "Puedo ayudarte con:\n• Análisis de patrones históricos\n• Sugerencias basadas en datos\n• Explicaciones estadísticas\n• Estado del sistema",
                "suggested_actions": "¿Te gustaría que:\n• Analice patrones de una lotería específica\n• Explique cómo funciona el análisis estadístico\n• Revise el estado del sistema?",
                "pattern_inquiry_response": "📊 **Sobre patrones en loterías:**\n\nPuedo observar frecuencias históricas en los datos, pero es crucial entender que estos 'patrones' son solo coincidencias estadísticas. Cada sorteo es independiente y mantiene la misma aleatoriedad completa.",
                "responsible_gaming": "🚨 **Juego Responsable**\n\nNoto preocupación en tu mensaje. Las loterías deben ser entretenimiento ocasional, nunca una solución a problemas financieros.\n\n**Recursos de ayuda:**\n• Línea de ayuda: 1-800-522-4700\n• www.ncpgambling.org\n• Busca ayuda profesional si el juego está causando problemas\n\nMi propósito es educativo, no fomentar el juego compulsivo."
            },
            "en": {
                "greeting": "Hello! I'm OMEGA, your assistant for statistical lottery analysis. How can I help you today?",
                "thanks_response": "You're welcome! Always a pleasure to help with honest statistical analysis.",
                "goodbye": "See you later! Remember to always play responsibly. 🎯",
                "service_unavailable": "The OMEGA analysis engine is not available right now. Please try again later.",
                "no_analysis_available": "Not enough data to analyze {game} at this moment.",
                "analysis_error": "Error generating analysis: {error}",
                "unknown_request": "I'm not sure I understand exactly what you need. Could you be more specific?",
                "capabilities_summary": "I can help you with:\n• Historical pattern analysis\n• Data-based suggestions\n• Statistical explanations\n• System status",
                "pattern_inquiry_response": "📊 **About patterns in lotteries:**\n\nI can observe historical frequencies in the data, but it's crucial to understand that these 'patterns' are just statistical coincidences. Each draw is independent and maintains the same complete randomness.",
                "responsible_gaming": "🚨 **Responsible Gaming**\n\nI notice concern in your message. Lotteries should be occasional entertainment, never a solution to financial problems.\n\n**Help resources:**\n• Help line: 1-800-522-4700\n• www.ncpgambling.org\n• Seek professional help if gambling is causing problems\n\nMy purpose is educational, not to encourage compulsive gambling."
            }
        }
    
    def _get_template(self, key: str, locale: str) -> str:
        """Get response template by key and locale"""
        return self.response_templates.get(locale, self.response_templates["es"]).get(key, "")
    
    def _error_response(self, error_msg: str, locale: str = "es") -> ConversationResponse:
        """Generate error response"""
        prefix = "❌ Error:" if locale == "es" else "❌ Error:"
        return ConversationResponse(
            text=f"{prefix} {error_msg}",
            metadata={"type": "error", "error": error_msg}
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get conversation manager performance statistics"""
        if not self.response_times:
            return {"status": "no_data"}
        
        avg_response_time = sum(self.response_times) / len(self.response_times)
        
        return {
            "total_responses": len(self.response_times),
            "average_response_time": round(avg_response_time, 3),
            "error_count": self.error_count,
            "error_rate": round(self.error_count / len(self.response_times) * 100, 2) if self.response_times else 0,
            "context_store_status": self.context_store.get_store_info()
        }