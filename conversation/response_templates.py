#!/usr/bin/env python3
"""
📝 OMEGA Response Templates - Honest Statistical Communication
Comprehensive templates for consistent and honest messaging across all channels
"""

from typing import Dict, Any, Optional
from datetime import datetime
from conversation.intent_classifier import IntentType

class ResponseTemplates:
    """
    Comprehensive response templates for OMEGA conversational AI
    Emphasizes statistical honesty and proper expectation management
    """
    
    def __init__(self):
        self.templates = self._load_all_templates()
    
    def _load_all_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load all response templates organized by language and category"""
        
        return {
            "es": {
                # ============================================================================
                # CORE MESSAGING
                # ============================================================================
                "core_identity": {
                    "what_is_omega": """🤖 **¿Qué es OMEGA?**

Soy un sistema de análisis estadístico que estudia patrones en datos históricos de loterías. 

**Lo que SÍ hago:**
• Analizo frecuencias y patrones pasados
• Sugiero números basándome en análisis estadístico
• Calculo probabilidades y valores esperados
• Proporciono educación sobre estadística

**Lo que NO hago:**
• Predecir resultados futuros
• Garantizar que ganes
• Controlar los sorteos
• Generar números "mágicos"

**La realidad:** Los sorteos son completamente aleatorios. Mi análisis es educativo e informativo.""",
                    
                    "mission_statement": "Mi misión es proporcionar análisis estadístico honesto y educación sobre loterías, manteniendo siempre la transparencia sobre las limitaciones reales.",
                    
                    "honesty_principle": "La honestidad estadística es mi principio fundamental. Nunca prometo lo que no puedo cumplir."
                },
                
                # ============================================================================
                # DISCLAIMERS POR NIVEL DE IMPORTANCIA
                # ============================================================================
                "disclaimers": {
                    "mild": "📊 *Nota*: Este análisis se basa en datos históricos. Los sorteos son aleatorios y no hay garantías.",
                    
                    "standard": "⚠️ **Importante**: OMEGA analiza patrones históricos, pero las loterías son juegos completamente aleatorios. No hay método que garantice ganar. Juega solo lo que puedas permitirte perder.",
                    
                    "strong": """⚠️ **ADVERTENCIA IMPORTANTE**:

• Los sorteos de lotería son **COMPLETAMENTE ALEATORIOS**
• Cada resultado es independiente de los anteriores  
• **NO existe método para predecir resultados futuros**
• La probabilidad real de ganar es extremadamente baja
• Solo juega dinero que puedas permitirte perder completamente

OMEGA proporciona análisis educativo, no ventajas reales para ganar.""",
                    
                    "critical": """🚨 **ADVERTENCIA CRÍTICA**:

Las loterías son sistemas diseñados para que la casa siempre gane a largo plazo.

**REALIDADES MATEMÁTICAS:**
• Probabilidad típica: 1 en varios millones
• Valor esperado: Siempre negativo (excepto jackpots extremos)
• Casa tiene ventaja matemática garantizada
• Patrones aparentes son solo coincidencia estadística

**SI SIENTES NECESIDAD DE GANAR:** Busca ayuda profesional. El juego problemático es una condición médica tratable.

🆘 **Ayuda**: 1-800-522-4700 | www.ncpgambling.org"""
                },
                
                # ============================================================================
                # RESPUESTAS POR TIPO DE INTENCIÓN
                # ============================================================================
                "intent_responses": {
                    IntentType.RECOMMENDATION_REQUEST: {
                        "header": "📊 **Análisis Estadístico OMEGA**",
                        "intro": "Basándome en el análisis de patrones históricos, estos son los números que muestran frecuencias interesantes:",
                        "explanation": "Estos números se seleccionan por análisis de frecuencias, patrones temporales y algoritmos de ensemble. **Importante**: Esto NO predice resultados futuros.",
                        "footer": "Recuerda: Cada sorteo es independiente. Esta es una herramienta educativa, no una ventaja real."
                    },
                    
                    IntentType.ANALYSIS_REQUEST: {
                        "header": "📈 **Análisis de Datos Históricos**",
                        "intro": "He analizado los datos históricos disponibles:",
                        "methodology": "Metodología: Análisis de frecuencias, patrones temporales, distribuciones estadísticas",
                        "limitation": "**Limitación**: Este análisis describe el pasado, no influye en futuros sorteos."
                    },
                    
                    IntentType.EXPLANATION_REQUEST: {
                        "header": "🎓 **Explicación Educativa**",
                        "intro": "Te explico cómo funciona el análisis estadístico:",
                        "disclaimer": "Esta explicación es para propósitos educativos. Entender estadística no proporciona ventajas para ganar."
                    },
                    
                    IntentType.STATISTICAL_QUESTION: {
                        "header": "🎲 **Conceptos Estadísticos**",
                        "reality_check": "**Realidad matemática**: En sistemas verdaderamente aleatorios, la probabilidad permanece constante sin importar patrones pasados.",
                        "gambler_fallacy": "⚠️ **Falacia del apostador**: Creer que eventos pasados afectan probabilidades futuras en sistemas aleatorios es un error lógico común."
                    },
                    
                    IntentType.PATTERN_INQUIRY: {
                        "header": "🔍 **Sobre Patrones en Loterías**",
                        "explanation": "Puedo observar patrones en datos históricos, pero es crucial entender que son coincidencias estadísticas.",
                        "truth": "**La verdad**: Los generadores de números aleatorios certificados aseguran que cada sorteo sea independiente.",
                        "illusion": "Los 'patrones' que percibimos son ilusiones estadísticas - nuestro cerebro busca orden en la aleatoriedad."
                    }
                },
                
                # ============================================================================
                # MENSAJES DE ERROR Y ESTADO
                # ============================================================================
                "errors": {
                    "service_unavailable": "🔧 El motor de análisis OMEGA no está disponible temporalmente. Por favor intenta más tarde.",
                    "no_data": "📊 No hay suficientes datos históricos para realizar este análisis en este momento.",
                    "analysis_failed": "❌ Error al generar el análisis: {error}. Inténtalo nuevamente.",
                    "rate_limited": "⏰ Has hecho muchas consultas recientemente. Por favor espera {wait_time} segundos.",
                    "invalid_game": "🎮 El juego '{game}' no está disponible. Juegos soportados: {available_games}",
                    "processing_error": "⚙️ Error procesando tu solicitud. Nuestro equipo ha sido notificado."
                },
                
                "status": {
                    "system_healthy": "🟢 **Sistema OMEGA Operativo**\n\nTodos los componentes funcionando normalmente.",
                    "limited_service": "🟡 **Servicio Limitado**\n\nAlgunas funciones pueden estar temporalmente restringidas.",
                    "maintenance": "🔧 **Mantenimiento Programado**\n\nEl sistema está siendo actualizado. Servicio completo se restablecerá pronto."
                },
                
                # ============================================================================
                # CONVERSACIÓN GENERAL
                # ============================================================================
                "conversation": {
                    "greeting": "¡Hola! 👋 Soy OMEGA, tu asistente para análisis estadístico honesto de loterías. ¿En qué puedo ayudarte?",
                    
                    "thanks": "¡De nada! 😊 Mi propósito es proporcionar información estadística transparente. ¿Hay algo más que quieras saber?",
                    
                    "goodbye": "¡Hasta luego! 👋 Recuerda siempre jugar responsablemente y que OMEGA está aquí para educación estadística. ¡Que tengas un excelente día!",
                    
                    "confused": "🤔 No estoy seguro de entender tu consulta. ¿Podrías reformularla? Puedo ayudarte con:\n• Análisis de patrones históricos\n• Explicaciones estadísticas\n• Información sobre probabilidades\n• Estado del sistema",
                    
                    "help_menu": """🆘 **¿Cómo puedo ayudarte?**

**Análisis disponibles:**
• *"números para kabala"* - Análisis estadístico
• *"probabilidades de ganar"* - Info matemática
• *"cómo funciona omega"* - Explicación técnica
• *"estado del sistema"* - Información operativa

**Recuerda**: Proporciono análisis educativo, no ventajas para ganar."""
                },
                
                # ============================================================================
                # JUEGO RESPONSABLE - PERÚ ESPECÍFICO
                # ============================================================================
                "responsible_gaming": {
                    "concern_detected": """🚨 **Mensaje Importante**

He notado algunas señales de preocupación en tu mensaje. Las loterías deben ser entretenimiento ocasional, nunca una solución a problemas financieros.

**Si necesitas ganar dinero urgentemente**, la lotería NO es la respuesta. La probabilidad real es extremadamente baja.

**Recursos de ayuda en Perú:**
📞 Línea MINJUS: 113 (gratuita)
🏥 CEDRO: (01) 445-6665
🌐 Instituto Nacional de Salud Mental
📧 Jugadores Anónimos Lima

Busca ayuda profesional si el juego está causando estrés o problemas financieros.""",
                    
                    "general_reminder": """🎲 **Recordatorio de Juego Responsable - Perú**

• Juega solo por entretenimiento (Mayor de 18 años)
• Nunca juegues dinero que necesitas para gastos esenciales
• No persiguas pérdidas con más juego
• Los sorteos son aleatorios - no hay "sistemas" que funcionen
• Si sientes que pierdes el control, busca ayuda

⚖️ **Legal**: Conforme a regulaciones MINJUS Perú, OMEGA es herramienta educativa únicamente.""",
                    
                    "warning_signs": """⚠️ **Señales de Advertencia del Juego Problemático:**

• Gastar más dinero del planeado
• Mentir sobre cuánto juegas
• Sentir ansiedad cuando no puedes jugar  
• Usar el juego para escapar de problemas
• Pedir dinero prestado para jugar

**Si reconoces estas señales**: En Perú, la ludopatía es reconocida como enfermedad. Busca ayuda profesional inmediatamente.

📞 CEDRO: (01) 445-6665 | Línea MINJUS: 113""",
                    
                    "peru_age_verification": """🔞 **Verificación de Edad - Perú**

Según el Código Penal Peruano Art. 279, debes ser MAYOR DE 18 AÑOS para acceder a información sobre juegos de azar.

Por favor confirma que eres mayor de edad antes de continuar.""",
                    
                    "peru_legal_compliance": """🏛️ **Cumplimiento Legal - Perú**

• OMEGA cumple con regulaciones MINJUS
• Sistema de análisis estadístico educativo únicamente
• NO predice ni garantiza resultados
• Usuario responsable de cumplir leyes locales
• Prohibido para menores de 18 años"""
                },
                
                # ============================================================================
                # EDUCACIÓN ESTADÍSTICA
                # ============================================================================
                "education": {
                    "probability_basics": """🎯 **Probabilidad en Loterías (Nivel Básico)**

Imagina una moneda: 50% cara, 50% cruz. En loterías es similar, pero con millones de combinaciones.

**Para Kábala (6 números de 40):**
• Total de combinaciones posibles: 3,838,380
• Tu probabilidad: 1 en 3,838,380 (0.000026%)
• Como encontrar una persona específica en una ciudad de 4 millones

**Punto clave**: Cada sorteo es independiente. Los resultados pasados no afectan futuros sorteos.""",
                    
                    "expected_value": """💰 **Valor Esperado (EV) - Concepto Clave**

El valor esperado es cuánto dinero recuperas "en promedio" si juegas muchas veces.

**Fórmula simple:**
EV = (Probabilidad de ganar × Premio) - Costo del boleto

**Ejemplo Kábala:**
• Probabilidad: 1/3,838,380
• Premio promedio: $500,000  
• Costo boleto: $2
• EV = ($500,000 × 0.00000026) - $2 = -$1.87

**Resultado**: Pierdes $1.87 por cada boleto en promedio.""",
                    
                    "randomness_explanation": """🎲 **¿Qué Significa "Aleatorio"?**

Un sistema aleatorio significa que cada resultado tiene la misma probabilidad, sin importar lo que pasó antes.

**En loterías:**
• Cada bola tiene exactamente la misma probabilidad de salir
• Los números "calientes" no tienen más probabilidad de repetirse
• Los números "fríos" no están "debidos" a salir
• Las máquinas no tienen "memoria" de sorteos anteriores

**Analogía**: Es como si el universo tirara dados perfectos cada vez, sin recordar tiradas anteriores.""",
                    
                    "gambler_fallacy": """🧠 **La Falacia del Apostador**

Error común: Creer que eventos pasados afectan probabilidades futuras en sistemas aleatorios.

**Ejemplos de la falacia:**
• "El 7 no ha salido en 20 sorteos, ya debe salir"
• "Esa combinación ya salió, no puede repetirse pronto"
• "He perdido 10 veces, debo ganar la próxima"

**La realidad**: En sistemas verdaderamente aleatorios, cada evento es independiente. La probabilidad es siempre la misma.

**¿Por qué sucede?**: Nuestro cerebro busca patrones incluso en la aleatoriedad pura."""
                }
            },
            
            # ============================================================================
            # ENGLISH TEMPLATES
            # ============================================================================
            "en": {
                "core_identity": {
                    "what_is_omega": """🤖 **What is OMEGA?**

I'm a statistical analysis system that studies patterns in historical lottery data.

**What I DO:**
• Analyze frequencies and past patterns
• Suggest numbers based on statistical analysis
• Calculate probabilities and expected values
• Provide education about statistics

**What I DON'T do:**
• Predict future results
• Guarantee you'll win
• Control the drawings
• Generate "magic" numbers

**Reality:** Drawings are completely random. My analysis is educational and informational.""",
                    
                    "mission_statement": "My mission is to provide honest statistical analysis and lottery education, always maintaining transparency about real limitations.",
                    
                    "honesty_principle": "Statistical honesty is my fundamental principle. I never promise what I cannot deliver."
                },
                
                "disclaimers": {
                    "mild": "📊 *Note*: This analysis is based on historical data. Drawings are random and there are no guarantees.",
                    
                    "standard": "⚠️ **Important**: OMEGA analyzes historical patterns, but lotteries are completely random games. No method guarantees winning. Only play what you can afford to lose.",
                    
                    "strong": """⚠️ **IMPORTANT WARNING**:

• Lottery drawings are **COMPLETELY RANDOM**
• Each result is independent of previous ones
• **NO method exists to predict future results**
• Real probability of winning is extremely low
• Only play money you can afford to lose completely

OMEGA provides educational analysis, not real advantages for winning.""",
                    
                    "critical": """🚨 **CRITICAL WARNING**:

Lotteries are systems designed so the house always wins long-term.

**MATHEMATICAL REALITIES:**
• Typical probability: 1 in several million
• Expected value: Always negative (except extreme jackpots)
• House has guaranteed mathematical advantage
• Apparent patterns are just statistical coincidence

**IF YOU FEEL YOU NEED TO WIN:** Seek professional help. Problem gambling is a treatable medical condition.

🆘 **Help**: 1-800-522-4700 | www.ncpgambling.org"""
                },
                
                "conversation": {
                    "greeting": "Hello! 👋 I'm OMEGA, your assistant for honest statistical lottery analysis. How can I help you?",
                    
                    "thanks": "You're welcome! 😊 My purpose is to provide transparent statistical information. Is there anything else you'd like to know?",
                    
                    "goodbye": "See you later! 👋 Always remember to play responsibly and that OMEGA is here for statistical education. Have an excellent day!",
                    
                    "confused": "🤔 I'm not sure I understand your query. Could you rephrase it? I can help you with:\n• Historical pattern analysis\n• Statistical explanations\n• Probability information\n• System status"
                }
            }
        }
    
    def get_template(self, category: str, key: str, locale: str = "es", **kwargs) -> str:
        """
        Get a template with optional formatting
        
        Args:
            category: Template category (e.g., 'disclaimers', 'conversation')
            key: Specific template key
            locale: Language locale ('es' or 'en')
            **kwargs: Formatting variables
        """
        try:
            template = self.templates[locale][category][key]
            
            # Handle enum keys for intent_responses
            if category == "intent_responses" and isinstance(key, IntentType):
                template = self.templates[locale][category][key]
            
            # Format template if it's a string
            if isinstance(template, str) and kwargs:
                return template.format(**kwargs)
            
            return template
            
        except (KeyError, TypeError) as e:
            # Fallback to Spanish if English not available
            if locale == "en":
                return self.get_template(category, key, "es", **kwargs)
            
            # Final fallback
            return f"Template not found: {category}.{key}"
    
    def get_disclaimer(self, level: str, intent_type: Optional[IntentType] = None, 
                      locale: str = "es") -> str:
        """Get appropriate disclaimer based on context"""
        
        base_disclaimer = self.get_template("disclaimers", level, locale)
        
        # Add intent-specific context if provided
        if intent_type and intent_type in [IntentType.RECOMMENDATION_REQUEST, 
                                          IntentType.STATISTICAL_QUESTION]:
            if level in ["strong", "critical"]:
                return base_disclaimer
        
        return base_disclaimer
    
    def get_complete_response(self, intent_type: IntentType, content: str,
                            disclaimer_level: str = "standard", 
                            locale: str = "es", **kwargs) -> str:
        """
        Generate complete response with header, content, and disclaimer
        """
        response_parts = []
        
        # Add header if available
        try:
            header = self.get_template("intent_responses", intent_type, locale)
            if isinstance(header, dict) and "header" in header:
                response_parts.append(header["header"])
        except:
            pass
        
        # Add main content
        response_parts.append(content)
        
        # Add appropriate disclaimer
        disclaimer = self.get_disclaimer(disclaimer_level, intent_type, locale)
        if disclaimer:
            response_parts.append(disclaimer)
        
        return "\n\n".join(response_parts)
    
    def get_educational_content(self, topic: str, expertise_level: str = "intermediate",
                              locale: str = "es") -> str:
        """Get educational content based on user expertise level"""
        
        base_content = self.get_template("education", topic, locale)
        
        # Adjust complexity based on expertise level
        if expertise_level == "beginner":
            # Use simpler language, add analogies
            if "probability_basics" in topic:
                return base_content
        elif expertise_level == "expert":
            # Add more technical details
            technical_additions = {
                "es": {
                    "probability_basics": "\n\n**Análisis técnico**: P(X) = 1/C(n,k) donde n=población, k=muestra. Distribución hipergeométrica para muestreo sin reemplazo.",
                    "expected_value": "\n\n**Consideraciones avanzadas**: EV debe ajustarse por impuestos, valor presente del dinero, y distribución de premios secundarios."
                }
            }
            
            addition = technical_additions.get(locale, {}).get(topic, "")
            return base_content + addition
        
        return base_content
    
    def get_responsible_gaming_message(self, trigger_level: str = "general", 
                                     locale: str = "es") -> str:
        """Get responsible gaming message based on trigger level"""
        
        if trigger_level == "urgent":
            return self.get_template("responsible_gaming", "concern_detected", locale)
        elif trigger_level == "warning":
            return self.get_template("responsible_gaming", "warning_signs", locale)
        else:
            return self.get_template("responsible_gaming", "general_reminder", locale)
    
    def format_prediction_response(self, predictions: list, game_name: str,
                                 analysis_info: dict, locale: str = "es",
                                 user_expertise: str = "intermediate") -> str:
        """Format prediction response with appropriate honesty level"""
        
        # Header
        header = f"📊 **Análisis Estadístico - {game_name}**" if locale == "es" else f"📊 **Statistical Analysis - {game_name}**"
        
        # Predictions section
        if locale == "es":
            pred_header = "**Números sugeridos por análisis histórico:**"
        else:
            pred_header = "**Numbers suggested by historical analysis:**"
        
        predictions_text = f"{pred_header}\n\n"
        
        for i, pred in enumerate(predictions, 1):
            numbers = " - ".join([f"{n:02d}" for n in pred.get("numbers", [])])
            score = pred.get("ens_score", pred.get("score", 0))
            source = pred.get("source", "ensemble")
            
            predictions_text += f"**{i}.** `{numbers}` _(confianza: {score:.2f}, fuente: {source})_\n"
        
        # Analysis context
        if locale == "es":
            context = f"\n**Metodología**: {analysis_info.get('methodology', 'Ensemble de modelos estadísticos')}"
            context += f"\n**Datos analizados**: {analysis_info.get('data_points', 'N/A')} sorteos históricos"
        else:
            context = f"\n**Methodology**: {analysis_info.get('methodology', 'Statistical model ensemble')}"
            context += f"\n**Data analyzed**: {analysis_info.get('data_points', 'N/A')} historical drawings"
        
        # Strong disclaimer for predictions
        disclaimer = self.get_disclaimer("strong", IntentType.RECOMMENDATION_REQUEST, locale)
        
        return "\n\n".join([header, predictions_text, context, disclaimer])
    
    def get_all_templates(self) -> Dict[str, Dict[str, Any]]:
        """Return all templates for external access"""
        return self.templates

# Global instance for easy access
response_templates = ResponseTemplates()