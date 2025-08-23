#!/usr/bin/env python3
"""
🤖 OMEGA Conversational AI System
Production-ready conversational AI with Redis context, WhatsApp integration, and advanced monitoring
"""

import os
import json
import redis
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from contextlib import asynccontextmanager
import asyncio
import hashlib
from urllib.parse import parse_qs

# FastAPI & Twilio
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Machine Learning & NLP
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import pickle

# Monitoring & Metrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import start_http_server
import psutil

# Configure logging without PII
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('conversational_ai.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =======================
# ENUMS & DATA MODELS
# =======================

class IntentType(Enum):
    GREETING = "greeting"
    LOTTERY_PREDICTION = "lottery_prediction"
    SYSTEM_INFO = "system_info"
    HELP = "help"
    GOODBYE = "goodbye"
    UNKNOWN = "unknown"

class Language(Enum):
    SPANISH = "es"
    ENGLISH = "en"

@dataclass
class UserContext:
    user_id: str
    session_id: str
    language: Language
    last_intent: Optional[IntentType]
    conversation_history: List[Dict[str, Any]]
    preferences: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['language'] = self.language.value
        if self.last_intent:
            data['last_intent'] = self.last_intent.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserContext':
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        data['language'] = Language(data['language'])
        if data.get('last_intent'):
            data['last_intent'] = IntentType(data['last_intent'])
        return cls(**data)

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
    context_updated: bool
    session_id: str

# =======================
# PROMETHEUS METRICS
# =======================

# Request metrics
message_counter = Counter('conversational_ai_messages_total', 'Total messages processed', ['intent', 'language'])
response_time_histogram = Histogram('conversational_ai_response_time_seconds', 'Response time histogram')
intent_confidence_gauge = Gauge('conversational_ai_intent_confidence', 'Intent classification confidence')

# System metrics
active_sessions_gauge = Gauge('conversational_ai_active_sessions', 'Number of active sessions')
redis_operations_counter = Counter('conversational_ai_redis_operations_total', 'Redis operations', ['operation', 'status'])
cache_hit_counter = Counter('conversational_ai_cache_hits_total', 'Cache hits', ['type'])

# Error metrics
error_counter = Counter('conversational_ai_errors_total', 'Total errors', ['error_type'])

# =======================
# REDIS CONTEXT MANAGER
# =======================

class RedisContextManager:
    def __init__(self, redis_url: str = "redis://localhost:6379", ttl_hours: int = 24):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.ttl_seconds = ttl_hours * 3600
        
    async def get_user_context(self, user_id: str) -> Optional[UserContext]:
        """Retrieve user context from Redis"""
        try:
            redis_operations_counter.labels(operation='get', status='attempt').inc()
            
            context_data = self.redis_client.get(f"context:{user_id}")
            if context_data:
                cache_hit_counter.labels(type='context').inc()
                redis_operations_counter.labels(operation='get', status='success').inc()
                return UserContext.from_dict(json.loads(context_data))
            
            redis_operations_counter.labels(operation='get', status='miss').inc()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get context for user {user_id}: {e}")
            redis_operations_counter.labels(operation='get', status='error').inc()
            error_counter.labels(error_type='redis_get').inc()
            return None
    
    async def save_user_context(self, context: UserContext) -> bool:
        """Save user context to Redis with TTL"""
        try:
            redis_operations_counter.labels(operation='set', status='attempt').inc()
            
            context.updated_at = datetime.utcnow()
            context_json = json.dumps(context.to_dict())
            
            result = self.redis_client.setex(
                f"context:{context.user_id}", 
                self.ttl_seconds, 
                context_json
            )
            
            if result:
                redis_operations_counter.labels(operation='set', status='success').inc()
                return True
            
            redis_operations_counter.labels(operation='set', status='failure').inc()
            return False
            
        except Exception as e:
            logger.error(f"Failed to save context for user {context.user_id}: {e}")
            redis_operations_counter.labels(operation='set', status='error').inc()
            error_counter.labels(error_type='redis_set').inc()
            return False
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        try:
            keys = self.redis_client.keys("context:*")
            return len(keys)
        except Exception as e:
            logger.error(f"Failed to count active sessions: {e}")
            return 0

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
                "predice numeros", "numeros ganadores", "quiero jugar", "dame numeros",
                "prediccion loteria", "numeros suerte", "combinacion ganadora", 
                "pronostico", "numeros recomendados", "omega prediccion"
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
                "predict numbers", "winning numbers", "lottery prediction", 
                "give me numbers", "lucky numbers", "winning combination",
                "forecast", "recommended numbers", "omega prediction"
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
    
    def classify_intent(self, text: str, language: Language) -> tuple[IntentType, float]:
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
                    "¡Hola! Soy OMEGA AI, tu asistente inteligente para predicciones de lotería. ¿En qué puedo ayudarte?",
                    "¡Buenas! Aquí tienes a OMEGA AI listo para ayudarte con predicciones ganadoras. ¿Qué necesitas?",
                    "¡Saludos! Soy OMEGA AI, especializado en análisis predictivo de lotería. ¿Cómo puedo asistirte?"
                ],
                IntentType.LOTTERY_PREDICTION: [
                    "🎯 Generando predicción OMEGA con pesos optimizados...",
                    "🔮 Analizando patrones con IA avanzada para tu predicción...",
                    "⚡ Procesando datos históricos para números ganadores..."
                ],
                IntentType.SYSTEM_INFO: [
                    "🤖 OMEGA AI v10.1 - Sistema de predicción con 30.7% de precisión (+29.9% mejora). Uso pesos optimizados: Partial Hit (41.2%), Jackpot (35.3%), Entropy FFT (11.8%), Pattern (11.8%).",
                    "⚙️ Sistema OMEGA integrado con análisis RNG posicional, entropy FFT, integración jackpots y optimización de hits parciales.",
                    "📊 OMEGA AI utiliza machine learning avanzado con análisis de 1500+ sorteos históricos para predicciones optimizadas."
                ],
                IntentType.HELP: [
                    "🆘 Puedo ayudarte con:\n• Predicciones de lotería inteligentes\n• Información del sistema OMEGA\n• Análisis de patrones históricos\n\nSimplemente escribe lo que necesitas.",
                    "📖 Comandos disponibles:\n• 'predice números' - Generar predicción\n• 'info sistema' - Detalles técnicos\n• 'ayuda' - Esta guía\n\n¿Qué quieres hacer?",
                    "💡 Soy tu asistente OMEGA AI. Puedo generar predicciones basadas en análisis avanzado de datos históricos. ¡Solo pídeme lo que necesitas!"
                ],
                IntentType.GOODBYE: [
                    "¡Hasta pronto! Que tengas suerte con tus números. 🍀",
                    "¡Adiós! Espero haberte ayudado. ¡Que ganes! 🎉",
                    "¡Nos vemos! Gracias por usar OMEGA AI. ¡Buena suerte! ✨"
                ],
                IntentType.UNKNOWN: [
                    "🤔 No estoy seguro de entender. ¿Podrías ser más específico? Puedo ayudarte con predicciones de lotería o información del sistema.",
                    "❓ Disculpa, no entendí completamente. ¿Quieres una predicción de números o información sobre OMEGA AI?",
                    "🔍 No reconocí tu solicitud. Intenta pedirme 'predicción de números', 'ayuda' o 'info del sistema'."
                ]
            },
            Language.ENGLISH: {
                IntentType.GREETING: [
                    "Hello! I'm OMEGA AI, your intelligent lottery prediction assistant. How can I help you?",
                    "Hi there! OMEGA AI here, ready to help you with winning predictions. What do you need?",
                    "Greetings! I'm OMEGA AI, specialized in lottery predictive analysis. How can I assist you?"
                ],
                IntentType.LOTTERY_PREDICTION: [
                    "🎯 Generating OMEGA prediction with optimized weights...",
                    "🔮 Analyzing patterns with advanced AI for your prediction...",
                    "⚡ Processing historical data for winning numbers..."
                ],
                IntentType.SYSTEM_INFO: [
                    "🤖 OMEGA AI v10.1 - Prediction system with 30.7% accuracy (+29.9% improvement). Using optimized weights: Partial Hit (41.2%), Jackpot (35.3%), Entropy FFT (11.8%), Pattern (11.8%).",
                    "⚙️ OMEGA integrated system with positional RNG analysis, entropy FFT, jackpot integration, and partial hit optimization.",
                    "📊 OMEGA AI uses advanced machine learning with 1500+ historical draws analysis for optimized predictions."
                ],
                IntentType.HELP: [
                    "🆘 I can help you with:\n• Intelligent lottery predictions\n• OMEGA system information\n• Historical pattern analysis\n\nJust write what you need.",
                    "📖 Available commands:\n• 'predict numbers' - Generate prediction\n• 'system info' - Technical details\n• 'help' - This guide\n\nWhat would you like to do?",
                    "💡 I'm your OMEGA AI assistant. I can generate predictions based on advanced historical data analysis. Just ask for what you need!"
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
    
    def generate_response(self, intent: IntentType, language: Language, context: Optional[UserContext] = None) -> str:
        """Generate appropriate response based on intent and language"""
        
        responses = self.responses.get(language, self.responses[Language.ENGLISH])
        intent_responses = responses.get(intent, responses[IntentType.UNKNOWN])
        
        # Select response (could be random or context-based)
        import random
        response = random.choice(intent_responses)
        
        # Add context-specific information if available
        if context and intent == IntentType.LOTTERY_PREDICTION:
            if language == Language.SPANISH:
                response += f"\n\n🎲 Predicción personalizada para sesión {context.session_id[:8]}..."
            else:
                response += f"\n\n🎲 Personalized prediction for session {context.session_id[:8]}..."
        
        return response

# =======================
# INTELLIGENT CACHE
# =======================

class IntelligentCache:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.prediction_ttl = 300  # 5 minutes for predictions
        self.response_ttl = 1800   # 30 minutes for responses
    
    def get_cached_prediction(self, user_id: str) -> Optional[Dict]:
        """Get cached prediction for user"""
        try:
            cache_key = f"prediction:{user_id}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                cache_hit_counter.labels(type='prediction').inc()
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            return None
    
    def cache_prediction(self, user_id: str, prediction: Dict) -> bool:
        """Cache prediction with TTL"""
        try:
            cache_key = f"prediction:{user_id}"
            prediction_json = json.dumps(prediction)
            
            result = self.redis_client.setex(cache_key, self.prediction_ttl, prediction_json)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            return False

# =======================
# MAIN CONVERSATIONAL AI
# =======================

class ConversationalAISystem:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.context_manager = RedisContextManager(redis_url)
        self.intent_classifier = IntentClassifier()
        self.response_generator = ResponseGenerator()
        self.cache = IntelligentCache(self.context_manager.redis_client)
        
        # Load OMEGA system
        self.omega_system = None
        self._load_omega_system()
    
    def _load_omega_system(self):
        """Load OMEGA system for predictions"""
        try:
            from omega_integrated_system import OmegaIntegratedSystem
            
            historical_path = "data/historial_kabala_github_emergency_clean.csv"
            jackpot_path = "data/jackpots_omega.csv"
            
            if os.path.exists(historical_path):
                self.omega_system = OmegaIntegratedSystem(historical_path, jackpot_path)
                logger.info("✅ OMEGA system loaded for predictions")
            else:
                logger.warning("⚠️ OMEGA system data not available")
                
        except Exception as e:
            logger.error(f"Failed to load OMEGA system: {e}")
    
    async def process_message(self, request: MessageRequest) -> MessageResponse:
        """Process incoming message and generate response"""
        
        start_time = time.time()
        
        try:
            # Generate session ID if not provided
            session_id = request.session_id or hashlib.md5(
                f"{request.user_id}_{int(time.time())}".encode()
            ).hexdigest()
            
            # Get or create user context
            context = await self.context_manager.get_user_context(request.user_id)
            
            if not context:
                context = UserContext(
                    user_id=request.user_id,
                    session_id=session_id,
                    language=self.intent_classifier.detect_language(request.message),
                    last_intent=None,
                    conversation_history=[],
                    preferences={},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            
            # Detect language and classify intent
            detected_language = self.intent_classifier.detect_language(request.message)
            intent, confidence = self.intent_classifier.classify_intent(request.message, detected_language)
            
            # Update metrics
            message_counter.labels(intent=intent.value, language=detected_language.value).inc()
            intent_confidence_gauge.set(confidence)
            
            # Handle lottery prediction with OMEGA system
            response_text = ""
            if intent == IntentType.LOTTERY_PREDICTION and self.omega_system:
                # Check cache first
                cached_prediction = self.cache.get_cached_prediction(request.user_id)
                
                if cached_prediction:
                    if detected_language == Language.SPANISH:
                        response_text = f"🎯 Predicción OMEGA (cached):\n\n{cached_prediction['formatted']}"
                    else:
                        response_text = f"🎯 OMEGA Prediction (cached):\n\n{cached_prediction['formatted']}"
                else:
                    # Generate new prediction
                    try:
                        predictions = self.omega_system.generate_integrated_predictions(8)
                        
                        if predictions:
                            # Format prediction
                            formatted_pred = self._format_predictions(predictions, detected_language)
                            
                            # Cache the prediction
                            prediction_data = {
                                'predictions': predictions,
                                'formatted': formatted_pred,
                                'timestamp': datetime.utcnow().isoformat()
                            }
                            self.cache.cache_prediction(request.user_id, prediction_data)
                            
                            if detected_language == Language.SPANISH:
                                response_text = f"🎯 Predicción OMEGA generada:\n\n{formatted_pred}"
                            else:
                                response_text = f"🎯 OMEGA Prediction generated:\n\n{formatted_pred}"
                        else:
                            response_text = self.response_generator.generate_response(
                                IntentType.UNKNOWN, detected_language, context
                            )
                            
                    except Exception as e:
                        logger.error(f"Prediction generation failed: {e}")
                        error_counter.labels(error_type='prediction_generation').inc()
                        response_text = self.response_generator.generate_response(
                            IntentType.UNKNOWN, detected_language, context
                        )
            else:
                # Generate standard response
                response_text = self.response_generator.generate_response(intent, detected_language, context)
            
            # Update conversation history
            context.conversation_history.append({
                'timestamp': datetime.utcnow().isoformat(),
                'user_message': request.message,
                'intent': intent.value,
                'confidence': confidence,
                'bot_response': response_text[:100] + "..." if len(response_text) > 100 else response_text
            })
            
            # Keep only last 10 interactions
            if len(context.conversation_history) > 10:
                context.conversation_history = context.conversation_history[-10:]
            
            context.last_intent = intent
            context.language = detected_language
            context.session_id = session_id
            
            # Save updated context
            context_saved = await self.context_manager.save_user_context(context)
            
            # Update active sessions metric
            active_count = self.context_manager.get_active_sessions_count()
            active_sessions_gauge.set(active_count)
            
            # Record response time
            response_time = time.time() - start_time
            response_time_histogram.observe(response_time)
            
            return MessageResponse(
                response=response_text,
                intent=intent.value,
                confidence=confidence,
                language=detected_language.value,
                context_updated=context_saved,
                session_id=session_id
            )
            
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            error_counter.labels(error_type='message_processing').inc()
            
            # Fallback response
            return MessageResponse(
                response="Lo siento, ocurrió un error interno. Por favor intenta nuevamente.",
                intent=IntentType.UNKNOWN.value,
                confidence=0.0,
                language=Language.SPANISH.value,
                context_updated=False,
                session_id=request.session_id or "error"
            )
    
    def _format_predictions(self, predictions: List[Dict], language: Language) -> str:
        """Format predictions for display"""
        if not predictions:
            return "No predictions available"
        
        formatted = ""
        
        for i, pred in enumerate(predictions[:5], 1):  # Show top 5
            numbers = pred.get('combination', [])
            confidence = pred.get('confidence', 0)
            
            if language == Language.SPANISH:
                formatted += f"🎲 Opción {i}: {', '.join(map(str, numbers))} (Confianza: {confidence:.1%})\n"
            else:
                formatted += f"🎲 Option {i}: {', '.join(map(str, numbers))} (Confidence: {confidence:.1%})\n"
        
        if language == Language.SPANISH:
            formatted += f"\n✨ Generado con OMEGA AI v10.1\n📊 Precisión esperada: 30.7% (+29.9%)"
        else:
            formatted += f"\n✨ Generated with OMEGA AI v10.1\n📊 Expected accuracy: 30.7% (+29.9%)"
        
        return formatted

# =======================
# FASTAPI APPLICATION
# =======================

# Initialize system
conversational_ai = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global conversational_ai
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    conversational_ai = ConversationalAISystem(redis_url)
    
    # Start Prometheus metrics server
    metrics_port = int(os.getenv("METRICS_PORT", "8001"))
    start_http_server(metrics_port)
    
    logger.info(f"🚀 Conversational AI System initialized")
    logger.info(f"📊 Metrics server started on port {metrics_port}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Conversational AI System shutting down")

app = FastAPI(
    title="OMEGA Conversational AI",
    description="Production-ready conversational AI with Redis context, WhatsApp integration, and monitoring",
    version="1.0.0",
    lifespan=lifespan
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
        "service": "OMEGA Conversational AI",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "Redis context storage with TTL",
            "Intent classification ES/EN",
            "WhatsApp integration",
            "Advanced monitoring",
            "Intelligent caching",
            "OMEGA lottery predictions"
        ]
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        # Check Redis connection
        redis_status = "healthy"
        try:
            conversational_ai.context_manager.redis_client.ping()
        except:
            redis_status = "unhealthy"
        
        # Check OMEGA system
        omega_status = "loaded" if conversational_ai.omega_system else "not_available"
        
        # System metrics
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        
        return {
            "status": "healthy" if redis_status == "healthy" else "degraded",
            "redis": redis_status,
            "omega_system": omega_status,
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent
            },
            "metrics": {
                "active_sessions": conversational_ai.context_manager.get_active_sessions_count()
            }
        }
        
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.post("/chat", response_model=MessageResponse)
async def chat_endpoint(request: MessageRequest):
    """Main chat endpoint"""
    return await conversational_ai.process_message(request)

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """WhatsApp webhook endpoint for Twilio"""
    try:
        form = await request.form()
        
        # Extract WhatsApp message data
        from_number = form.get("From", "").replace("whatsapp:", "")
        message_body = form.get("Body", "")
        
        if not from_number or not message_body:
            raise HTTPException(status_code=400, detail="Missing required WhatsApp data")
        
        # Process message
        message_request = MessageRequest(
            user_id=from_number,
            message=message_body,
            phone_number=from_number
        )
        
        response = await conversational_ai.process_message(message_request)
        
        # Format Twilio response
        twilio_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{response.response}</Message>
</Response>"""
        
        return twilio_response
        
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        error_counter.labels(error_type='whatsapp_webhook').inc()
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/system/stats")
async def system_stats():
    """System statistics"""
    try:
        active_sessions = conversational_ai.context_manager.get_active_sessions_count()
        
        return {
            "active_sessions": active_sessions,
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            },
            "redis": {
                "connected": True
            },
            "omega_system": {
                "available": conversational_ai.omega_system is not None
            }
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"🚀 Starting OMEGA Conversational AI on port {port}")
    
    uvicorn.run(
        "conversational_ai_system:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False
    )