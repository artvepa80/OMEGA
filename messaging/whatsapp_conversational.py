#!/usr/bin/env python3
"""
📱 OMEGA WhatsApp Conversational Bot
Intelligent WhatsApp integration with honest statistical communication
"""

import re
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json

from conversation.conversation_manager import OmegaConversationManager
from conversation.intent_classifier import IntentType

logger = logging.getLogger(__name__)

class WhatsAppFormatter:
    """
    WhatsApp-specific message formatting
    Handles WhatsApp markdown, length limits, and conversational flow
    """
    
    MAX_MESSAGE_LENGTH = 1600  # WhatsApp practical limit
    
    @staticmethod
    def format_for_whatsapp(text: str) -> str:
        """
        Format text for WhatsApp with proper markdown and length handling
        """
        # Convert common markdown to WhatsApp format
        # Bold: **text** -> *text*  
        text = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', text)
        
        # Italic: _text_ -> _text_ (same)
        # Code: `text` -> ```text``` (WhatsApp code blocks)
        text = re.sub(r'`([^`]+)`', r'```\1```', text)
        
        # Strikethrough: ~~text~~ -> ~text~
        text = re.sub(r'~~([^~]+)~~', r'~\1~', text)
        
        # Clean up excess whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Max 2 consecutive newlines
        
        return text.strip()
    
    @staticmethod
    def split_long_message(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> List[str]:
        """
        Split long messages intelligently for WhatsApp
        Preserves formatting and splits at natural break points
        """
        if len(text) <= max_length:
            return [WhatsAppFormatter.format_for_whatsapp(text)]
        
        messages = []
        current_message = ""
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        for i, paragraph in enumerate(paragraphs):
            # If adding this paragraph would exceed limit
            if len(current_message + paragraph) > max_length - 50:  # Leave room for continuation
                
                # Send current message if not empty
                if current_message.strip():
                    continuation_note = "\n\n_(continúa...)_" if i < len(paragraphs) - 1 else ""
                    messages.append(WhatsAppFormatter.format_for_whatsapp(current_message + continuation_note))
                    current_message = ""
                
                # If single paragraph is too long, split by sentences
                if len(paragraph) > max_length - 100:
                    sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                    temp_para = ""
                    
                    for sentence in sentences:
                        if len(temp_para + sentence) <= max_length - 100:
                            temp_para += sentence + " "
                        else:
                            if temp_para.strip():
                                messages.append(WhatsAppFormatter.format_for_whatsapp(temp_para + "\n\n_(continúa...)_"))
                            temp_para = sentence + " "
                    
                    current_message = temp_para
                else:
                    current_message = paragraph
            else:
                if current_message:
                    current_message += "\n\n" + paragraph
                else:
                    current_message = paragraph
        
        # Add final message
        if current_message.strip():
            messages.append(WhatsAppFormatter.format_for_whatsapp(current_message))
        
        return messages if messages else [WhatsAppFormatter.format_for_whatsapp(text[:max_length])]
    
    @staticmethod
    def add_whatsapp_styling(text: str, intent_type: IntentType) -> str:
        """Add appropriate WhatsApp styling based on intent type"""
        
        # Add emoji headers based on intent
        emoji_headers = {
            IntentType.RECOMMENDATION_REQUEST: "📊 *OMEGA - Análisis Estadístico*\n\n",
            IntentType.ANALYSIS_REQUEST: "📈 *Análisis de Datos*\n\n", 
            IntentType.EXPLANATION_REQUEST: "🤓 *Explicación OMEGA*\n\n",
            IntentType.STATISTICAL_QUESTION: "🎲 *Estadística de Loterías*\n\n",
            IntentType.SYSTEM_STATUS: "🔧 *Estado del Sistema*\n\n",
            IntentType.GENERAL_CONVERSATION: "",  # No header for casual chat
        }
        
        header = emoji_headers.get(intent_type, "🤖 *OMEGA*\n\n")
        
        # Add footer for important intents
        footer_intents = [IntentType.RECOMMENDATION_REQUEST, IntentType.STATISTICAL_QUESTION]
        footer = ""
        
        if intent_type in footer_intents:
            footer = "\n\n_Responde 'ayuda' para más opciones_"
        
        return header + text + footer

class WhatsAppConversationTracker:
    """
    Tracks WhatsApp conversation state and user preferences
    Handles user shortcuts and quick responses
    """
    
    def __init__(self):
        self.user_shortcuts = {}
        self.quick_responses = {
            "es": {
                "ayuda": "🆘 *Comandos OMEGA*:\n\n• *'números kabala'* - Análisis de Kábala\n• *'explicar omega'* - Cómo funciona\n• *'probabilidades'* - Info estadística\n• *'estado'* - Estado del sistema\n\nEscribe tu consulta normalmente y te ayudo con análisis honestos.",
                "gracias": "¡De nada! 😊 Recuerda que OMEGA analiza patrones históricos, no predice resultados futuros. ¿Algo más en que pueda ayudarte?",
                "stop": "👋 Entendido. Si necesitas análisis estadísticos honestos sobre loterías, estaré aquí. ¡Que tengas un buen día!",
                "info": "🤖 *Sobre OMEGA*:\n\nSoy un sistema de análisis estadístico que estudia patrones históricos en loterías. NO predigo resultados - solo analizo datos pasados.\n\n⚠️ *Importante*: Los sorteos son aleatorios. Juega responsablemente."
            },
            "en": {
                "help": "🆘 *OMEGA Commands*:\n\n• *'kabala numbers'* - Kabala analysis\n• *'explain omega'* - How it works\n• *'probabilities'* - Statistical info\n• *'status'* - System status\n\nWrite your question normally and I'll help with honest analysis.",
                "thanks": "You're welcome! 😊 Remember OMEGA analyzes historical patterns, doesn't predict future results. Anything else I can help with?",
                "stop": "👋 Understood. If you need honest statistical analysis about lotteries, I'll be here. Have a great day!",
                "info": "🤖 *About OMEGA*:\n\nI'm a statistical analysis system that studies historical patterns in lotteries. I DON'T predict results - only analyze past data.\n\n⚠️ *Important*: Draws are random. Play responsibly."
            }
        }
    
    def detect_shortcut(self, message: str, locale: str = "es") -> Optional[str]:
        """Detect if message is a shortcut command"""
        message_clean = message.lower().strip()
        
        shortcuts = self.quick_responses.get(locale, self.quick_responses["es"])
        
        if message_clean in shortcuts:
            return shortcuts[message_clean]
        
        # Fuzzy matching for common shortcuts
        fuzzy_matches = {
            "es": {
                ("ayuda", "help", "?"): "ayuda",
                ("gracias", "thanks", "thx"): "gracias", 
                ("para", "stop", "basta"): "stop",
                ("info", "sobre omega", "que es omega"): "info"
            },
            "en": {
                ("help", "ayuda", "?"): "help",
                ("thanks", "gracias", "thx"): "thanks",
                ("stop", "para", "enough"): "stop", 
                ("info", "about omega", "what is omega"): "info"
            }
        }
        
        locale_fuzzy = fuzzy_matches.get(locale, fuzzy_matches["es"])
        
        for keywords, shortcut_key in locale_fuzzy.items():
            if any(keyword in message_clean for keyword in keywords):
                return shortcuts[shortcut_key]
        
        return None

class WhatsAppConversationalBot:
    """
    Main WhatsApp conversational bot with honest statistical communication
    Integrates with OMEGA conversation manager for intelligent responses
    """
    
    def __init__(self, omega_control_center, redis_url: str = "redis://localhost:6379"):
        self.conversation_manager = OmegaConversationManager(omega_control_center, redis_url)
        self.formatter = WhatsAppFormatter()
        self.tracker = WhatsAppConversationTracker()
        
        # WhatsApp specific settings
        self.response_delay = 1.0  # Simulate typing delay
        self.max_consecutive_messages = 3  # Max messages to send in sequence
        
        logger.info("📱 WhatsApp Conversational Bot initialized")
    
    async def handle_incoming_message(self, from_number: str, message_body: str,
                                    media_url: Optional[str] = None) -> List[str]:
        """
        Process incoming WhatsApp message and return list of response messages
        Returns multiple messages if response is too long for single WhatsApp message
        """
        try:
            # Extract user ID from phone number
            user_id = self._extract_user_id(from_number)
            
            # Detect locale from message or phone number
            locale = self._detect_locale(message_body, from_number)
            
            # Check for shortcuts first
            shortcut_response = self.tracker.detect_shortcut(message_body, locale)
            if shortcut_response:
                return [self.formatter.format_for_whatsapp(shortcut_response)]
            
            # Handle media messages
            if media_url:
                return await self._handle_media_message(user_id, media_url, message_body, locale)
            
            # Process with conversation manager
            response = await self.conversation_manager.process_message(
                user_id=user_id,
                message=message_body,
                locale=locale
            )
            
            # Format response for WhatsApp
            formatted_responses = await self._format_response_for_whatsapp(response, message_body)
            
            return formatted_responses
            
        except Exception as e:
            logger.error(f"Error handling WhatsApp message from {from_number}: {e}")
            error_msg = "Lo siento, hubo un error procesando tu mensaje. Intenta nuevamente." if locale == "es" else "Sorry, there was an error processing your message. Please try again."
            return [error_msg]
    
    async def send_proactive_message(self, to_number: str, message_type: str,
                                   context: Optional[Dict] = None) -> List[str]:
        """
        Send proactive messages (alerts, notifications, etc.)
        """
        user_id = self._extract_user_id(to_number)
        locale = self._detect_locale("", to_number)
        
        if message_type == "prediction_alert":
            return await self._generate_prediction_alert(user_id, context, locale)
        elif message_type == "system_update":
            return await self._generate_system_update(context, locale)
        elif message_type == "responsible_gaming_check":
            return await self._generate_responsible_gaming_message(locale)
        else:
            return ["Mensaje no reconocido"]
    
    def _extract_user_id(self, from_number: str) -> str:
        """Extract clean user ID from WhatsApp number"""
        # Remove WhatsApp prefix and clean number
        clean_number = from_number.replace("whatsapp:", "").replace("+", "").replace("-", "").replace(" ", "")
        return f"wa_{clean_number}"
    
    def _detect_locale(self, message: str, phone_number: str) -> str:
        """Detect user locale from message content and phone number"""
        
        # English indicators in message
        english_indicators = [
            "hello", "hi there", "thank you", "please", "explain", "what is",
            "how does", "can you", "i want", "help me"
        ]
        
        spanish_indicators = [
            "hola", "gracias", "por favor", "explica", "que es", "como funciona",
            "puedes", "quiero", "ayudame", "necesito"
        ]
        
        message_lower = message.lower()
        
        english_score = sum(1 for indicator in english_indicators if indicator in message_lower)
        spanish_score = sum(1 for indicator in spanish_indicators if indicator in message_lower)
        
        # Phone number country code hints (rough)
        if phone_number.startswith("+1"):  # US/Canada
            return "en" if english_score >= spanish_score else "es"
        elif phone_number.startswith("+52"):  # Mexico
            return "es"
        elif phone_number.startswith("+51"):  # Peru
            return "es"
        
        # Default based on message content, fallback to Spanish
        return "en" if english_score > spanish_score else "es"
    
    async def _format_response_for_whatsapp(self, response: Dict, original_message: str) -> List[str]:
        """Format conversation manager response for WhatsApp"""
        
        text = response["text"]
        metadata = response.get("metadata", {})
        intent_type = metadata.get("intent")
        
        # Add WhatsApp styling
        if intent_type:
            try:
                intent_enum = IntentType(intent_type)
                styled_text = self.formatter.add_whatsapp_styling(text, intent_enum)
            except ValueError:
                styled_text = text
        else:
            styled_text = text
        
        # Split if too long
        messages = self.formatter.split_long_message(styled_text)
        
        # Limit number of messages to avoid spam
        if len(messages) > self.max_consecutive_messages:
            # Truncate and add "more info" option
            messages = messages[:self.max_consecutive_messages - 1]
            messages.append("_Respuesta muy larga. Escribe 'continuar' para ver el resto._")
        
        return messages
    
    async def _handle_media_message(self, user_id: str, media_url: str, 
                                  caption: str, locale: str) -> List[str]:
        """Handle WhatsApp media messages (images, documents, etc.)"""
        
        if locale == "es":
            response = "📎 He recibido tu archivo, pero por ahora solo puedo procesar mensajes de texto. " \
                      "Por favor describe tu consulta por escrito y te ayudo con el análisis estadístico."
        else:
            response = "📎 I received your file, but I can currently only process text messages. " \
                      "Please describe your query in writing and I'll help with statistical analysis."
        
        # If caption provided, process it as text
        if caption and caption.strip():
            text_response = await self.conversation_manager.process_message(
                user_id=user_id,
                message=caption,
                locale=locale
            )
            
            media_note = response
            text_responses = await self._format_response_for_whatsapp(text_response, caption)
            
            return [media_note] + text_responses
        
        return [response]
    
    async def _generate_prediction_alert(self, user_id: str, context: Dict, locale: str) -> List[str]:
        """Generate proactive prediction alert"""
        
        # Simulate request for latest analysis
        fake_message = "números recomendados hoy" if locale == "es" else "recommended numbers today"
        
        response = await self.conversation_manager.process_message(
            user_id=user_id,
            message=fake_message,
            locale=locale
        )
        
        # Add proactive context
        if locale == "es":
            header = "🔔 *Análisis Diario OMEGA*\n\n"
        else:
            header = "🔔 *OMEGA Daily Analysis*\n\n"
        
        response["text"] = header + response["text"]
        
        return await self._format_response_for_whatsapp(response, fake_message)
    
    async def _generate_system_update(self, context: Dict, locale: str) -> List[str]:
        """Generate system update notification"""
        
        if locale == "es":
            message = f"🔧 *Actualización OMEGA*\n\n{context.get('message', 'Sistema actualizado')}\n\nTodo funcionando normalmente."
        else:
            message = f"🔧 *OMEGA Update*\n\n{context.get('message', 'System updated')}\n\nEverything working normally."
        
        return [self.formatter.format_for_whatsapp(message)]
    
    async def _generate_responsible_gaming_message(self, locale: str) -> List[str]:
        """Generate responsible gaming reminder"""
        
        if locale == "es":
            message = """🎲 *Recordatorio de Juego Responsable*

Las loterías deben ser entretenimiento ocasional, no una estrategia financiera.

*Recuerda:*
• Solo juega dinero que puedas permitirte perder
• Los sorteos son completamente aleatorios
• No hay métodos que garanticen ganar

Si sientes que el juego está afectando tu vida, busca ayuda profesional.

OMEGA está aquí para educación estadística, no para fomentar el juego."""
        else:
            message = """🎲 *Responsible Gaming Reminder*

Lotteries should be occasional entertainment, not a financial strategy.

*Remember:*
• Only play money you can afford to lose
• Draws are completely random
• No methods guarantee winning

If you feel gambling is affecting your life, seek professional help.

OMEGA is here for statistical education, not to promote gambling."""
        
        return [self.formatter.format_for_whatsapp(message)]
    
    async def get_conversation_context(self, user_id: str) -> Dict[str, Any]:
        """Get conversation context for user (for analytics/support)"""
        try:
            context = await self.conversation_manager.context_store.get_context(user_id, "main")
            if context:
                return {
                    "user_expertise": context.user_expertise_level,
                    "total_messages": context.message_count,
                    "last_intent": context.last_intent_type,
                    "locale": context.locale,
                    "created": context.created_at
                }
            return {"status": "no_context"}
        except Exception as e:
            logger.error(f"Error getting context for {user_id}: {e}")
            return {"error": str(e)}
    
    def get_bot_stats(self) -> Dict[str, Any]:
        """Get bot performance statistics"""
        try:
            manager_stats = self.conversation_manager.get_performance_stats()
            
            return {
                "whatsapp_bot": {
                    "version": "3.0.0",
                    "max_message_length": self.formatter.MAX_MESSAGE_LENGTH,
                    "response_delay": self.response_delay,
                    "supported_locales": ["es", "en"]
                },
                "conversation_manager": manager_stats
            }
        except Exception as e:
            return {"error": str(e)}

# ============================================================================
# WEBHOOK INTEGRATION
# ============================================================================

class WhatsAppWebhookHandler:
    """
    Handles WhatsApp webhook integration with Twilio/other providers
    """
    
    def __init__(self, conversational_bot: WhatsAppConversationalBot):
        self.bot = conversational_bot
    
    async def handle_twilio_webhook(self, webhook_data: Dict) -> Dict[str, Any]:
        """Handle Twilio WhatsApp webhook"""
        try:
            from_number = webhook_data.get("From", "")
            message_body = webhook_data.get("Body", "")
            media_url = webhook_data.get("MediaUrl0")  # First media attachment
            
            # Process message
            responses = await self.bot.handle_incoming_message(
                from_number=from_number,
                message_body=message_body,
                media_url=media_url
            )
            
            return {
                "success": True,
                "responses": responses,
                "user_id": self.bot._extract_user_id(from_number)
            }
            
        except Exception as e:
            logger.error(f"Twilio webhook error: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_response_via_twilio(self, to_number: str, message: str, 
                                     twilio_client) -> bool:
        """Send response back via Twilio"""
        try:
            # Format number for Twilio WhatsApp
            whatsapp_number = to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"
            
            message_obj = twilio_client.messages.create(
                body=message,
                from_="whatsapp:+14155238886",  # Twilio sandbox number
                to=whatsapp_number
            )
            
            logger.info(f"WhatsApp message sent: {message_obj.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False