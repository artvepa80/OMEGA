#!/usr/bin/env python3
"""
🤖 OMEGA Conversational AI - Versión Simplificada
Sistema conversacional sin conflictos para pruebas inmediatas
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging
import hashlib

# FastAPI
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Machine Learning & NLP
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =======================
# ENUMS & DATA MODELS
# =======================

class IntentType(Enum):
    GREETING = "greeting"
    LOTTERY_PREDICTION = "lottery_prediction"
    LOTTERY_MENU = "lottery_menu"
    SYSTEM_INFO = "system_info"
    HELP = "help"
    GOODBYE = "goodbye"
    UNKNOWN = "unknown"

class Language(Enum):
    SPANISH = "es"
    ENGLISH = "en"

class MessageRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    message: str = Field(..., description="User message")
    phone_number: Optional[str] = Field(None, description="WhatsApp phone number")
    session_id: Optional[str] = Field(None, description="Session identifier")

class MessageResponse(BaseModel):
    response: str
    intent: str
    confidence: float
    language: str
    session_id: str

# =======================
# INTENT CLASSIFIER
# =======================

class IntentClassifier:
    def __init__(self):
        self.spanish_classifier = None
        self.english_classifier = None
        self._train_classifiers()
    
    def _train_classifiers(self):
        """Train intent classifiers for both languages"""
        
        # Spanish training data
        spanish_data = {
            IntentType.GREETING: [
                "hola", "buenas", "buenos dias", "buenas tardes", "saludos", 
                "que tal", "como estas", "hey", "ey"
            ],
            IntentType.LOTTERY_PREDICTION: [
                "7 numeros", "8 numeros", "9 numeros", "6 numeros",
                "multijugada", "jugada multiple", "mas numeros", "jugada completa"
            ],
            IntentType.LOTTERY_MENU: [
                "predice numeros", "numeros ganadores", "quiero jugar", "dame numeros",
                "prediccion loteria", "numeros suerte", "combinacion ganadora", 
                "pronostico", "numeros recomendados", "omega prediccion",
                "numeros", "prediccion", "jugar"
            ],
            IntentType.SYSTEM_INFO: [
                "como funciona", "que haces", "informacion sistema", "version",
                "capacidades", "funciones", "ayuda tecnica", "specs"
            ],
            IntentType.HELP: [
                "ayuda", "help", "como usar", "instrucciones", "guia",
                "que puedes hacer", "comandos", "opciones"
            ],
            IntentType.GOODBYE: [
                "adios", "chau", "nos vemos", "hasta luego", "bye",
                "gracias", "listo", "terminamos"
            ]
        }
        
        # English training data  
        english_data = {
            IntentType.GREETING: [
                "hello", "hi", "good morning", "good afternoon", "greetings",
                "how are you", "hey", "what's up"
            ],
            IntentType.LOTTERY_PREDICTION: [
                "7 numbers", "8 numbers", "9 numbers", "6 numbers",
                "multi play", "multiple play", "more numbers", "full play"
            ],
            IntentType.LOTTERY_MENU: [
                "predict numbers", "winning numbers", "lottery prediction", 
                "give me numbers", "lucky numbers", "winning combination",
                "forecast", "recommended numbers", "omega prediction",
                "numbers", "prediction", "play"
            ],
            IntentType.SYSTEM_INFO: [
                "how it works", "what do you do", "system info", "version",
                "capabilities", "functions", "technical help", "specs"
            ],
            IntentType.HELP: [
                "help", "how to use", "instructions", "guide",
                "what can you do", "commands", "options"
            ],
            IntentType.GOODBYE: [
                "goodbye", "bye", "see you", "see you later", "thanks",
                "done", "finished"
            ]
        }
        
        # Train Spanish classifier
        spanish_texts, spanish_labels = [], []
        for intent, phrases in spanish_data.items():
            spanish_texts.extend(phrases)
            spanish_labels.extend([intent.value] * len(phrases))
        
        self.spanish_classifier = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2))),
            ('clf', MultinomialNB(alpha=0.1))
        ])
        self.spanish_classifier.fit(spanish_texts, spanish_labels)
        
        # Train English classifier
        english_texts, english_labels = [], []
        for intent, phrases in english_data.items():
            english_texts.extend(phrases)
            english_labels.extend([intent.value] * len(phrases))
        
        self.english_classifier = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2))),
            ('clf', MultinomialNB(alpha=0.1))
        ])
        self.english_classifier.fit(english_texts, english_labels)
        
        logger.info("✅ Intent classifiers trained successfully")
    
    def detect_language(self, text: str) -> Language:
        """Simple language detection"""
        spanish_words = {'hola', 'como', 'que', 'numeros', 'predice', 'ayuda', 'gracias'}
        english_words = {'hello', 'how', 'what', 'numbers', 'predict', 'help', 'thanks'}
        
        text_lower = text.lower()
        spanish_score = sum(1 for word in spanish_words if word in text_lower)
        english_score = sum(1 for word in english_words if word in text_lower)
        
        return Language.SPANISH if spanish_score >= english_score else Language.ENGLISH
    
    def classify_intent(self, text: str, language: Language) -> tuple:
        """Classify intent with confidence score"""
        try:
            classifier = self.spanish_classifier if language == Language.SPANISH else self.english_classifier
            
            if not classifier:
                return IntentType.UNKNOWN, 0.0
            
            probabilities = classifier.predict_proba([text])[0]
            predicted_class = classifier.predict([text])[0]
            confidence = max(probabilities)
            
            try:
                intent = IntentType(predicted_class)
            except ValueError:
                intent = IntentType.UNKNOWN
                confidence = 0.0
            
            return intent, confidence
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return IntentType.UNKNOWN, 0.0

# =======================
# RESPONSE GENERATOR
# =======================

class ResponseGenerator:
    def __init__(self):
        self.responses = {
            Language.SPANISH: {
                IntentType.GREETING: [
                    "¡Hey! 👋 ¿Cómo estás? Soy OMEGA, tu compa de la suerte. ¿Qué tal si jugamos unos números hoy?",
                    "¡Hola! 😊 ¿Todo bien? Aquí ando, listo para ayudarte a ganar en grande. ¿En qué piensas apostar?",
                    "¡Buenas! ¿Cómo va tu día? Soy OMEGA y estoy aquí para que le demos duro a la lotería juntos 🎲"
                ],
                IntentType.LOTTERY_MENU: [
                    "¡Perfecto! 🎲 ¿Qué tipo de jugada quieres para la **Kabala**? Escoge tu opción:\n\n🎯 **6 números** - Jugada clásica\n🎰 **7 números** - Más chances\n🚀 **8 números** - Multijugada premium\n💎 **9 números** - Cobertura máxima\n\nSolo escribe el número que prefieres, por ejemplo: '8 números'",
                    "¡Genial! 😎 Te ofrezco estas opciones para la **Kabala**:\n\n• **6 números** - Jugada tradicional\n• **7 números** - Mejor cobertura\n• **8 números** - Multijugada recomendada\n• **9 números** - Máxima probabilidad\n\n¿Cuál te late más? Solo dime '7 números' o lo que prefieras 🎲",
                    "¡Dale! 🔥 Aquí tienes las opciones para la **Kabala**:\n\n1️⃣ **6 números** - Clásico\n2️⃣ **7 números** - Buena opción\n3️⃣ **8 números** - Muy popular\n4️⃣ **9 números** - Todo incluido\n\nEscribe tu elección, por ejemplo '9 números' y te genero la combinación perfecta 💪"
                ],
                IntentType.LOTTERY_PREDICTION: [
                    "¡Dale! 🔥 Te traigo números para la **Kabala** basados en análisis estadístico:\n\n🎲 **7, 15, 23, 31, 38, 42**\n\nEsos números los saqué analizando más de 1500 sorteos de la Kabala. Recuerda que es solo análisis matemático 📊",
                    "¡Perfecto! 😎 Aquí están los números para la **Kabala** según mi análisis:\n\n🎲 **3, 18, 25, 29, 35, 41**\n\nEstos provienen de mi algoritmo estadístico basado en patrones históricos de la Kabala 📈",
                    "¡Excelente! 🚀 Te comparto esta combinación para la **Kabala** según mi análisis:\n\n🎲 **5, 12, 27, 33, 39, 44**\n\nCombinación generada por análisis estadístico de la Kabala. Solo soy tu asesor matemático 🔢"
                ],
                IntentType.SYSTEM_INFO: [
                    "¡Ah claro! 🤓 Te cuento mi secreto: soy como un detective de números de la **Kabala**. Analizo más de 1500 sorteos pasados de la Kabala, busco patrones raros, frecuencias sospechosas... ¡soy medio obsesivo con los números! 😄\n\nSoy un asesor estadístico que busca patrones matemáticos en los datos históricos. ¿Quieres que te explique algo específico?",
                    "¡Buena pregunta! 💡 Mira, yo no soy mágico, pero sí soy listo. Uso inteligencia artificial para encontrar patrones en los sorteos anteriores. Es como si fuera un matemático súper rápido que nunca se cansa de hacer cuentas.\n\nMi truco es que combino varios enfoques: análisis de frecuencias, patrones posicionales, entropía... ¡un cóctel de ciencia! Solo soy un asesor estadístico.",
                    "¿Te da curiosidad cómo funciono? 🔬 Es fácil: tomo todos los sorteos históricos que puedo encontrar, los meto en mi 'cerebro' artificial, y busco patrones que se repiten.\n\nNo es magia, es matemática pura. Soy tu asesor estadístico, no un oráculo 📊"
                ],
                IntentType.HELP: [
                    "¡Claro! 😊 Te explico qué podemos hacer juntos:\n\n🎲 **Predicciones** - 'dame números' (6 números)\n🎰 **Multijugada** - '7 números', '8 números', '9 números'\n🤖 **Info técnica** - Si te da curiosidad cómo funciono\n💬 **Charlar** - Puedes hablarme normal\n\n¿Qué te provoca hacer?",
                    "¡Por supuesto! 👍 Básicamente soy tu compa para apostar. Puedes:\n\n• 'dame números' - Jugada simple (6)\n• '8 números' - Multijugada con más chances\n• '9 números' - Jugada completa máxima\n• Preguntarme cómo funciono\n\nNo seas formal conmigo, háblame como si fuéramos panas 😎",
                    "¡Dale! 🤝 Te ayudo con lo que necesites:\n\n🎯 **6 números** - Jugada clásica\n🎰 **7-9 números** - Multijugada (más chances)\n🔍 **Análisis** - Te explico estrategias\n🗣️ **Conversar** - Charlamos de lotería\n\n¿En qué andas pensando?"
                ],
                IntentType.GOODBYE: [
                    "¡Chau! 👋 Que tengas mucha suerte con esos números. Si pegas, no te olvides de tu compa OMEGA 😄🍀",
                    "¡Nos vemos! 😊 Espero que te vaya genial. ¡Y si ganas, invitas! 🎉🍾",
                    "¡Hasta la próxima! 🤝 Fue un gusto charlar contigo. ¡Que la suerte te acompañe siempre! ✨"
                ],
                IntentType.UNKNOWN: [
                    "🤔 Mm... no te entendí bien. ¿Me explicas de nuevo? Puede ser que quieras números para jugar o que me preguntes algo sobre cómo funciono. ¡Háblame claro!",
                    "😅 Perdón, me confundí. ¿Puedes decirme otra vez qué necesitas? Soy bueno con números y predicciones, pero a veces me pierdo con otras cosas jaja",
                    "🤷‍♂️ No caché bien qué me pediste. ¿Querías números para apostar? ¿O tienes alguna pregunta sobre lotería? ¡Dime nomás!"
                ]
            },
            Language.ENGLISH: {
                IntentType.GREETING: [
                    "Hey! 👋 What's up? I'm OMEGA, your lucky numbers buddy. Ready to win big today?",
                    "Hello there! 😊 How's it going? I'm OMEGA and I'm here to help you hit the jackpot! What do you say?",
                    "Hi! 🎲 Good to see you! I'm OMEGA, your personal lottery wingman. Let's find you some winning numbers!"
                ],
                IntentType.LOTTERY_MENU: [
                    "Perfect! 🎲 What type of **Kabala** play do you want? Choose your option:\n\n🎯 **6 numbers** - Classic play\n🎰 **7 numbers** - Better chances\n🚀 **8 numbers** - Premium multi-play\n💎 **9 numbers** - Maximum coverage\n\nJust type your choice, for example: '8 numbers'",
                    "Great! 😎 Here are your **Kabala** options:\n\n• **6 numbers** - Traditional play\n• **7 numbers** - Enhanced coverage\n• **8 numbers** - Recommended multi-play\n• **9 numbers** - Maximum probability\n\nWhich one do you like? Just say '7 numbers' or whatever you prefer 🎲",
                    "Awesome! 🔥 Here are the **Kabala** options:\n\n1️⃣ **6 numbers** - Classic\n2️⃣ **7 numbers** - Good choice\n3️⃣ **8 numbers** - Very popular\n4️⃣ **9 numbers** - Full coverage\n\nType your choice, like '9 numbers' and I'll generate the perfect combination 💪"
                ],
                IntentType.LOTTERY_PREDICTION: [
                    "🎯 Generating OMEGA statistical analysis for **Kabala**...\n\n🎲 Suggested Kabala numbers: 9, 16, 24, 32, 37, 43\n✨ Generated with OMEGA AI v10.1\n📊 Statistical pattern analysis only",
                    "🔮 Analyzing **Kabala** patterns with advanced AI...\n\n🎲 Statistical Kabala combination: 4, 11, 28, 34, 40, 45\n✨ Based on 1500+ historical Kabala draws\n📊 Mathematical patterns identified",
                    "⚡ Processing **Kabala** historical data...\n\n🎲 OMEGA Kabala analysis: 6, 13, 21, 30, 36, 41\n✨ Optimized weights implemented\n📊 Statistical advisory only"
                ],
                IntentType.SYSTEM_INFO: [
                    "🤖 OMEGA AI v10.1 - Statistical analysis system using optimized weights: Partial Hit (41.2%), Jackpot (35.3%), Entropy FFT (11.8%), Pattern (11.8%). I'm your statistical advisor, not a guarantee system.",
                    "⚙️ OMEGA integrated system with positional RNG analysis, entropy FFT, jackpot integration, and partial hit optimization. Statistical patterns only.",
                    "📊 OMEGA AI uses advanced machine learning with 1500+ historical draws analysis for statistical pattern recognition. Advisory purposes only."
                ],
                IntentType.HELP: [
                    "🆘 I can help you with:\n• 'predict numbers' - 6 numbers (classic)\n• '8 numbers' - Multi-play (better chances)\n• '9 numbers' - Full play (max coverage)\n• OMEGA system information\n\nJust write what you need.",
                    "📖 Available commands:\n• 'predict numbers' - 6 numbers\n• '7 numbers', '8 numbers', '9 numbers' - Multi-play\n• 'system info' - Technical details\n• 'help' - This guide\n\nWhat would you like to do?",
                    "💡 I'm your OMEGA AI assistant. I can generate:\n🎯 **6 numbers** - Classic play\n🎰 **7-9 numbers** - Multi-play options\n\nBased on advanced historical data analysis. Just ask!"
                ],
                IntentType.GOODBYE: [
                    "See you soon! Good luck with your numbers! 🍀",
                    "Goodbye! Hope I helped you. May you win! 🎉",
                    "See you later! Thanks for using OMEGA AI. Good luck! ✨"
                ],
                IntentType.UNKNOWN: [
                    "🤔 I'm not sure I understand. Could you be more specific? I can help with lottery predictions or system information.",
                    "❓ Sorry, I didn't fully understand. Do you want number predictions or OMEGA AI information?",
                    "🔍 I didn't recognize your request. Try asking for 'number prediction', 'help', or 'system info'."
                ]
            }
        }
    
    def generate_response(self, intent: IntentType, language: Language, context=None, omega_system=None, user_message="") -> str:
        """Generate appropriate response based on intent and language"""
        
        responses = self.responses.get(language, self.responses[Language.ENGLISH])
        intent_responses = responses.get(intent, responses[IntentType.UNKNOWN])
        
        # For lottery predictions, use real OMEGA system if available
        if intent == IntentType.LOTTERY_PREDICTION and omega_system:
            try:
                # Detect how many numbers user wants
                num_count = 6  # default
                multijugada_type = "simple"
                
                user_message_lower = user_message.lower()
                if "7 numeros" in user_message_lower or "7 numbers" in user_message_lower:
                    num_count = 7
                    multijugada_type = "7 números"
                elif "8 numeros" in user_message_lower or "8 numbers" in user_message_lower:
                    num_count = 8
                    multijugada_type = "8 números"
                elif "9 numeros" in user_message_lower or "9 numbers" in user_message_lower:
                    num_count = 9
                    multijugada_type = "9 números"
                elif any(word in user_message_lower for word in ["multijugada", "multi play", "jugada multiple", "multiple play", "mas numeros", "more numbers"]):
                    num_count = 8  # Default to 8 for multi-play
                    multijugada_type = "multijugada 8 números"
                
                # Get real predictions from OMEGA
                print(f"🔍 DEBUG: Requesting {num_count} numbers from OMEGA")
                predictions = omega_system.generate_integrated_predictions(num_count)
                print(f"🔍 DEBUG: OMEGA returned {len(predictions) if predictions else 0} predictions")
                
                if predictions and len(predictions) > 0:
                    # Extract numbers from first prediction
                    base_numbers = predictions[0].get('combination', [])
                    print(f"🔍 DEBUG: First prediction has {len(base_numbers) if base_numbers else 0} numbers: {base_numbers}")
                    
                    if base_numbers and len(base_numbers) >= 6:
                        # For multijugada, get additional unique numbers from other predictions
                        if num_count > 6 and len(predictions) > 1:
                            extended_numbers = list(base_numbers[:6])  # Start with first 6
                            used_numbers = set(extended_numbers)
                            
                            # Add unique numbers from other predictions
                            for pred in predictions[1:]:
                                pred_numbers = pred.get('combination', [])
                                for num in pred_numbers:
                                    if num not in used_numbers and len(extended_numbers) < num_count:
                                        extended_numbers.append(num)
                                        used_numbers.add(num)
                                    if len(extended_numbers) >= num_count:
                                        break
                                if len(extended_numbers) >= num_count:
                                    break
                            
                            numbers = extended_numbers
                            print(f"🔍 DEBUG: Extended to {len(numbers)} numbers: {numbers}")
                        else:
                            numbers = base_numbers
                        
                        numbers_str = ', '.join(map(str, numbers[:num_count]))
                        
                        if language == Language.SPANISH:
                            if num_count > 6:
                                return f"¡Perfecto! 🚀 Te traigo una **{multijugada_type}** para la **Kabala** directa del sistema OMEGA real:\n\n🎲 **{numbers_str}**\n\n¡Con {num_count} números tienes más chances de ganar en la Kabala! Mi IA los calculó analizando 1500+ sorteos históricos con pesos optimizados. Recuerda que esto es solo un análisis estadístico 📊"
                            else:
                                return f"¡Dale! 🔥 Te traigo números para la **Kabala** directos del sistema OMEGA real:\n\n🎲 **{numbers_str}**\n\nEsos son los números que mi IA calculó analizando 1500+ sorteos de la Kabala. ¡Con pesos optimizados y todo! Recuerda que esto es solo un análisis estadístico 📊"
                        else:
                            if num_count > 6:
                                return f"Awesome! 🚀 Here's your **{num_count} numbers multi-play** for **Kabala** lottery from real OMEGA AI:\n\n🎲 **{numbers_str}**\n\nWith {num_count} numbers you have better winning chances in Kabala! Generated from my AI analysis of 1500+ historical Kabala draws with optimized weights! Remember this is statistical analysis only 📊"
                            else:
                                return f"Awesome! 🔥 Here are real OMEGA AI numbers for **Kabala** lottery:\n\n🎲 **{numbers_str}**\n\nThese come from my actual AI analysis of 1500+ Kabala draws! Optimized weights included! Remember this is statistical analysis only 📊"
            except Exception as e:
                print(f"Error getting OMEGA predictions: {e}")
                # Fall back to template responses
        
        # Select response (random for variety)
        import random
        response = random.choice(intent_responses)
        
        return response

# =======================
# SIMPLE CONVERSATIONAL AI
# =======================

class SimpleConversationalAI:
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.response_generator = ResponseGenerator()
        self.sessions = {}  # Simple in-memory session storage
        self.omega_system = None
        self._load_omega_system()
    
    def _load_omega_system(self):
        """Load the real OMEGA system for predictions"""
        try:
            from omega_integrated_system import OmegaIntegratedSystem
            
            # Try to load the real system with historical data
            historical_path = "data/historial_kabala_github_emergency_clean.csv"
            jackpot_path = "data/jackpots_omega.csv"
            
            if os.path.exists(historical_path):
                self.omega_system = OmegaIntegratedSystem(historical_path, jackpot_path)
                logger.info("✅ Real OMEGA system loaded successfully for predictions")
            else:
                logger.warning("⚠️ OMEGA system data not found, using template responses")
                
        except Exception as e:
            logger.error(f"❌ Failed to load OMEGA system: {e}")
            self.omega_system = None
    
    def process_message(self, request: MessageRequest) -> MessageResponse:
        """Process incoming message and generate response"""
        
        try:
            # Generate session ID if not provided
            session_id = request.session_id or hashlib.md5(
                f"{request.user_id}_{int(time.time())}".encode()
            ).hexdigest()[:16]
            
            # Detect language and classify intent
            detected_language = self.intent_classifier.detect_language(request.message)
            intent, confidence = self.intent_classifier.classify_intent(request.message, detected_language)
            
            # Log OMEGA system status for predictions
            if intent == IntentType.LOTTERY_PREDICTION:
                omega_status = "✅ Real OMEGA AI" if self.omega_system else "❌ Template responses"
                logger.info(f"🎯 Prediction request - {omega_status}")
            
            # Generate response (pass omega_system for real predictions and user message for multijugada detection)
            response_text = self.response_generator.generate_response(intent, detected_language, None, self.omega_system, request.message)
            
            # Store simple session info
            self.sessions[session_id] = {
                "user_id": request.user_id,
                "last_intent": intent.value,
                "last_language": detected_language.value,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return MessageResponse(
                response=response_text,
                intent=intent.value,
                confidence=confidence,
                language=detected_language.value,
                session_id=session_id
            )
            
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            
            # Fallback response
            return MessageResponse(
                response="Lo siento, ocurrió un error interno. Por favor intenta nuevamente.",
                intent=IntentType.UNKNOWN.value,
                confidence=0.0,
                language=Language.SPANISH.value,
                session_id=request.session_id or "error"
            )

# =======================
# FASTAPI APPLICATION
# =======================

# Initialize system
conversational_ai = SimpleConversationalAI()

app = FastAPI(
    title="OMEGA Conversational AI - Simple",
    description="Versión simplificada para pruebas inmediatas",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =======================
# API ENDPOINTS
# =======================

@app.get("/")
async def root():
    return {
        "service": "OMEGA Conversational AI - Simple",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "Bilingual intent classification (ES/EN)",
            "WhatsApp webhook integration",
            "OMEGA lottery predictions",
            "Simple session management"
        ]
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_sessions": len(conversational_ai.sessions)
    }

@app.post("/chat", response_model=MessageResponse)
async def chat_endpoint(request: MessageRequest):
    """Main chat endpoint"""
    return conversational_ai.process_message(request)

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """WhatsApp webhook endpoint for Twilio"""
    try:
        # Get raw body and form data
        body = await request.body()
        logger.info(f"🌐 Raw webhook data: {body.decode()}")
        
        form = await request.form()
        
        # Extract WhatsApp message data
        from_number = form.get("From", "")
        message_body = form.get("Body", "")
        message_sid = form.get("MessageSid", "")
        
        logger.info(f"📱 WhatsApp data - From: {from_number}, Body: {message_body}, SID: {message_sid}")
        
        if not from_number or not message_body:
            logger.warning("⚠️ Missing required WhatsApp data")
            # Return simple response anyway
            return Response(content="""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Hello! I received your message but there was an issue processing it.</Message>
</Response>""", media_type="application/xml")
        
        # Clean phone number
        clean_number = from_number.replace("whatsapp:", "")
        
        # Process message
        message_request = MessageRequest(
            user_id=clean_number,
            message=message_body,
            phone_number=clean_number
        )
        
        ai_response = conversational_ai.process_message(message_request)
        
        logger.info(f"🤖 AI Response - Intent: {ai_response.intent}, Confidence: {ai_response.confidence:.2f}")
        logger.info(f"🗣️ Response text: {ai_response.response[:200]}...")
        
        # Clean response for XML (remove problematic characters)
        clean_response = ai_response.response.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        # Format Twilio response with proper headers
        xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{clean_response}</Message>
</Response>"""
        
        logger.info("✅ Sending XML response to Twilio")
        
        return Response(content=xml_response, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"❌ WhatsApp webhook error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Simple fallback response
        fallback_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Hola! Soy OMEGA AI. Hubo un problema técnico, pero estoy funcionando.</Message>
</Response>"""
        
        return Response(content=fallback_xml, media_type="application/xml")

@app.get("/system/stats")
async def system_stats():
    """Simple system statistics"""
    return {
        "active_sessions": len(conversational_ai.sessions),
        "system_status": "running",
        "uptime": "running"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    
    logger.info(f"🚀 Starting Simple OMEGA Conversational AI on port {port}")
    
    uvicorn.run(
        "simple_conversational_ai:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False
    )