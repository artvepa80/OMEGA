"""
Conversational AI System
Advanced conversational AI with Claude integration, voice support, and smart recommendations
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import asyncio
import json
import logging
import base64
from enum import Enum
import aiohttp
import speech_recognition as sr
import pyttsx3
from io import BytesIO
import wave

logger = logging.getLogger(__name__)
router = APIRouter()

class ConversationMode(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    MIXED = "mixed"

class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ConversationTopic(str, Enum):
    LOTTERY_PREDICTIONS = "lottery_predictions"
    SPORTS_BETTING = "sports_betting"
    ASIAN_MARKETS = "asian_markets"
    GENERAL_HELP = "general_help"
    ACCOUNT_MANAGEMENT = "account_management"

class ChatMessage(BaseModel):
    message_id: str
    session_id: str
    message_type: MessageType
    content: str
    timestamp: datetime
    topic: Optional[ConversationTopic] = None
    metadata: Optional[Dict[str, Any]] = None

class ConversationRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    mode: ConversationMode = ConversationMode.TEXT
    language: str = "en"
    context: Optional[Dict[str, Any]] = None

class ConversationResponse(BaseModel):
    response: str
    session_id: str
    suggested_actions: List[str] = []
    follow_up_questions: List[str] = []
    topic: ConversationTopic
    confidence: float
    audio_response: Optional[str] = None  # Base64 encoded audio

class ClaudeAIManager:
    """Manager for Claude AI integration"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.api_key = "your_claude_api_key"
        self.base_url = "https://api.anthropic.com"
        self.model = "claude-3-sonnet-20240229"
        
        # Conversation context templates
        self.system_prompts = {
            ConversationTopic.LOTTERY_PREDICTIONS: """You are an expert lottery prediction assistant for OMEGA PRO AI. 
            You help users understand lottery predictions, analyze patterns, and make informed decisions. 
            Be precise, analytical, and always remind users that lottery outcomes are probabilistic.""",
            
            ConversationTopic.SPORTS_BETTING: """You are a sports betting expert for OMEGA PRO AI. 
            You provide insights on odds, betting strategies, bankroll management, and help users understand 
            different bet types. Always promote responsible gambling.""",
            
            ConversationTopic.ASIAN_MARKETS: """You are an Asian betting markets specialist. 
            You explain Asian handicaps, cultural betting preferences, and help users navigate 
            Asian sportsbooks and markets with cultural sensitivity.""",
            
            ConversationTopic.GENERAL_HELP: """You are a helpful assistant for OMEGA PRO AI platform. 
            You help users navigate the platform, understand features, and provide general support."""
        }
    
    async def generate_response(self, message: str, session_id: str, context: Dict[str, Any] = None) -> ConversationResponse:
        """Generate AI response using Claude"""
        try:
            # Detect topic from message
            topic = await self._detect_topic(message)
            
            # Get conversation history
            history = await self._get_conversation_history(session_id)
            
            # Prepare context
            system_prompt = self.system_prompts.get(topic, self.system_prompts[ConversationTopic.GENERAL_HELP])
            
            # Prepare messages for Claude API
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history
            for hist_msg in history[-5:]:  # Last 5 messages for context
                messages.append({
                    "role": "user" if hist_msg["message_type"] == MessageType.USER else "assistant",
                    "content": hist_msg["content"]
                })
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Call Claude API (mock implementation)
            response_text = await self._call_claude_api(messages, topic, context)
            
            # Generate suggested actions and follow-ups
            suggested_actions = await self._generate_suggested_actions(topic, message, response_text)
            follow_up_questions = await self._generate_follow_up_questions(topic, message)
            
            # Calculate confidence
            confidence = await self._calculate_confidence(message, response_text, topic)
            
            response = ConversationResponse(
                response=response_text,
                session_id=session_id,
                suggested_actions=suggested_actions,
                follow_up_questions=follow_up_questions,
                topic=topic,
                confidence=confidence
            )
            
            # Store conversation
            await self._store_conversation(session_id, message, response_text, topic)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate AI response: {e}")
            raise HTTPException(status_code=500, detail=f"AI response generation failed: {str(e)}")
    
    async def _call_claude_api(self, messages: List[Dict], topic: ConversationTopic, context: Dict[str, Any] = None) -> str:
        """Call Claude API (mock implementation)"""
        
        # Mock responses based on topic and message content
        mock_responses = {
            ConversationTopic.LOTTERY_PREDICTIONS: {
                "default": "Based on OMEGA's advanced AI analysis, I can help you understand the prediction patterns. Our system analyzes historical data, frequency patterns, and statistical probabilities to generate lottery series. Would you like me to explain how our prediction algorithm works or help you interpret specific results?",
                "how": "OMEGA PRO AI uses a sophisticated ensemble of machine learning models including transformer networks, statistical analyzers, and pattern recognition systems. We analyze over 10,000+ historical lottery draws to identify subtle patterns and probability distributions.",
                "results": "I can see you're asking about prediction results. Our system generates series based on probability analysis. Remember that lottery outcomes are inherently random, and our predictions are statistical estimates to help inform your choices."
            },
            ConversationTopic.SPORTS_BETTING: {
                "default": "I'm here to help you with sports betting strategies and analysis. OMEGA PRO AI provides advanced odds analysis, edge calculation, and ROI tracking. What specific aspect of sports betting would you like to explore?",
                "odds": "Odds represent the probability and potential payout of a bet. Our system analyzes odds from multiple bookmakers to find the best value and calculate your potential edge. Lower odds mean higher probability but lower payout.",
                "strategy": "Successful sports betting requires disciplined bankroll management, value betting, and emotional control. I recommend using only 1-3% of your bankroll per bet and focusing on bets where you have a statistical edge."
            },
            ConversationTopic.ASIAN_MARKETS: {
                "default": "I specialize in Asian betting markets and handicap systems. Asian handicaps are popular because they eliminate the draw and provide more balanced odds. Would you like me to explain specific handicap types or Asian betting culture?",
                "handicap": "Asian handicaps give one team a virtual head start. For example, -0.5 means your team must win by at least 1 goal. Quarter handicaps like -0.25 split your bet between two lines for reduced risk.",
                "culture": "Asian betting culture varies by region. Japanese bettors prefer conservative strategies, while Chinese markets favor high-volume trading. Understanding local preferences helps identify value opportunities."
            },
            ConversationTopic.GENERAL_HELP: {
                "default": "Welcome to OMEGA PRO AI! I'm here to help you navigate our platform. We offer lottery predictions, sports betting analysis, Asian markets, and crypto payments. What would you like to learn about?",
                "features": "OMEGA PRO AI includes: Advanced lottery predictions, Live sports odds analysis, Asian handicap markets, KYC verification, Crypto payments, ROI analytics, and Multi-language support.",
                "account": "For account-related questions, I can help with basic information. For sensitive operations like payments or identity verification, please use our secure endpoints or contact support."
            }
        }
        
        # Simple keyword matching for mock responses
        message_lower = messages[-1]["content"].lower()
        topic_responses = mock_responses.get(topic, mock_responses[ConversationTopic.GENERAL_HELP])
        
        for keyword, response in topic_responses.items():
            if keyword in message_lower:
                return response
        
        return topic_responses["default"]
    
    async def _detect_topic(self, message: str) -> ConversationTopic:
        """Detect conversation topic from message content"""
        message_lower = message.lower()
        
        # Keyword-based topic detection
        topic_keywords = {
            ConversationTopic.LOTTERY_PREDICTIONS: ["lottery", "prediction", "numbers", "series", "draw", "omega", "jackpot"],
            ConversationTopic.SPORTS_BETTING: ["sports", "betting", "odds", "bet", "game", "match", "wager", "stake"],
            ConversationTopic.ASIAN_MARKETS: ["asian", "handicap", "quarter", "half", "asian betting", "j-league", "k-league"],
            ConversationTopic.ACCOUNT_MANAGEMENT: ["account", "profile", "settings", "kyc", "verification", "payment", "crypto"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return topic
        
        return ConversationTopic.GENERAL_HELP
    
    async def _get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history from Redis"""
        try:
            if self.redis:
                history_key = f"chat_history:{session_id}"
                history_data = await self.redis.lrange(history_key, 0, -1)
                return [json.loads(item) for item in history_data]
            return []
        except Exception as e:
            logger.warning(f"Failed to get conversation history: {e}")
            return []
    
    async def _store_conversation(self, session_id: str, user_message: str, ai_response: str, topic: ConversationTopic):
        """Store conversation in Redis"""
        try:
            if self.redis:
                history_key = f"chat_history:{session_id}"
                
                # Store user message
                user_msg = {
                    "message_type": MessageType.USER,
                    "content": user_message,
                    "timestamp": datetime.now().isoformat(),
                    "topic": topic
                }
                
                # Store AI response
                ai_msg = {
                    "message_type": MessageType.ASSISTANT, 
                    "content": ai_response,
                    "timestamp": datetime.now().isoformat(),
                    "topic": topic
                }
                
                await self.redis.lpush(history_key, json.dumps(user_msg))
                await self.redis.lpush(history_key, json.dumps(ai_msg))
                await self.redis.expire(history_key, 86400)  # 24 hours
                
        except Exception as e:
            logger.warning(f"Failed to store conversation: {e}")
    
    async def _generate_suggested_actions(self, topic: ConversationTopic, user_message: str, ai_response: str) -> List[str]:
        """Generate contextual suggested actions"""
        actions_by_topic = {
            ConversationTopic.LOTTERY_PREDICTIONS: [
                "Generate new lottery predictions",
                "Analyze recent results",
                "View prediction history",
                "Adjust prediction settings"
            ],
            ConversationTopic.SPORTS_BETTING: [
                "View live odds",
                "Get betting picks",
                "Check ROI analytics",
                "Set betting limits"
            ],
            ConversationTopic.ASIAN_MARKETS: [
                "Explore Asian handicaps",
                "View live Asian markets",
                "Learn about quarter handicaps",
                "Check cultural preferences"
            ],
            ConversationTopic.GENERAL_HELP: [
                "Take platform tour",
                "View documentation",
                "Contact support",
                "Access user guide"
            ]
        }
        
        return actions_by_topic.get(topic, actions_by_topic[ConversationTopic.GENERAL_HELP])[:3]
    
    async def _generate_follow_up_questions(self, topic: ConversationTopic, user_message: str) -> List[str]:
        """Generate relevant follow-up questions"""
        questions_by_topic = {
            ConversationTopic.LOTTERY_PREDICTIONS: [
                "Would you like to see the confidence scores for these predictions?",
                "Shall I explain how our AI calculates these numbers?",
                "Do you want to adjust the prediction parameters?"
            ],
            ConversationTopic.SPORTS_BETTING: [
                "Would you like me to explain the edge calculation?",
                "Should I show you similar betting opportunities?",
                "Do you want to set up automated alerts for high-value bets?"
            ],
            ConversationTopic.ASIAN_MARKETS: [
                "Would you like to see examples of quarter handicap outcomes?",
                "Shall I show you the current Asian league schedules?",
                "Do you want to learn about other Asian betting cultures?"
            ]
        }
        
        return questions_by_topic.get(topic, [])[:2]
    
    async def _calculate_confidence(self, user_message: str, ai_response: str, topic: ConversationTopic) -> float:
        """Calculate confidence in the AI response"""
        # Simple confidence calculation based on topic match and response length
        base_confidence = 0.8
        
        # Adjust based on topic specificity
        if topic != ConversationTopic.GENERAL_HELP:
            base_confidence += 0.1
        
        # Adjust based on response completeness
        if len(ai_response) > 100:
            base_confidence += 0.05
        
        return min(base_confidence, 0.95)

class VoiceManager:
    """Manager for voice processing (STT/TTS)"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.tts_engine = pyttsx3.init()
        self.supported_languages = ["en", "zh", "ja", "ko", "th"]
    
    async def speech_to_text(self, audio_data: bytes, language: str = "en") -> str:
        """Convert speech to text"""
        try:
            # Convert bytes to audio format
            audio_io = BytesIO(audio_data)
            
            with sr.AudioFile(audio_io) as source:
                audio = self.recognizer.record(source)
            
            # Recognize speech
            language_code = self._get_language_code(language)
            text = self.recognizer.recognize_google(audio, language=language_code)
            
            return text
            
        except sr.UnknownValueError:
            raise HTTPException(status_code=400, detail="Could not understand audio")
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {e}")
            raise HTTPException(status_code=500, detail="Speech recognition service error")
    
    async def text_to_speech(self, text: str, language: str = "en") -> bytes:
        """Convert text to speech"""
        try:
            # Configure TTS
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.8)
            
            # Set voice based on language
            voices = self.tts_engine.getProperty('voices')
            for voice in voices:
                if language in voice.id.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
            
            # Generate speech
            audio_io = BytesIO()
            self.tts_engine.save_to_file(text, audio_io)
            self.tts_engine.runAndWait()
            
            return audio_io.getvalue()
            
        except Exception as e:
            logger.error(f"Text-to-speech error: {e}")
            raise HTTPException(status_code=500, detail="Text-to-speech conversion failed")
    
    def _get_language_code(self, language: str) -> str:
        """Get Google Speech API language code"""
        language_codes = {
            "en": "en-US",
            "zh": "zh-CN", 
            "ja": "ja-JP",
            "ko": "ko-KR",
            "th": "th-TH"
        }
        return language_codes.get(language, "en-US")

class ConversationAnalytics:
    """Analytics for conversation patterns and user satisfaction"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def track_conversation_metrics(self, session_id: str, user_message: str, ai_response: str, topic: ConversationTopic, satisfaction_score: Optional[float] = None):
        """Track conversation analytics"""
        try:
            metrics = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "topic": topic,
                "user_message_length": len(user_message),
                "ai_response_length": len(ai_response),
                "satisfaction_score": satisfaction_score
            }
            
            if self.redis:
                await self.redis.lpush("conversation_analytics", json.dumps(metrics))
                
        except Exception as e:
            logger.warning(f"Failed to track conversation metrics: {e}")
    
    async def get_conversation_insights(self, timeframe_days: int = 7) -> Dict[str, Any]:
        """Get conversation analytics and insights"""
        try:
            # Mock analytics data
            insights = {
                "total_conversations": 1250,
                "avg_session_length": 8.5,
                "topic_distribution": {
                    "lottery_predictions": 35,
                    "sports_betting": 30,
                    "asian_markets": 20,
                    "general_help": 15
                },
                "satisfaction_score": 4.2,
                "most_common_questions": [
                    "How do lottery predictions work?",
                    "What's the best betting strategy?",
                    "How do Asian handicaps work?"
                ],
                "peak_hours": ["14:00-16:00", "20:00-22:00"],
                "language_distribution": {
                    "en": 50,
                    "zh": 20,
                    "ja": 15,
                    "ko": 10,
                    "th": 5
                }
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get conversation insights: {e}")
            return {}

# Initialize managers
claude_manager = None
voice_manager = VoiceManager()
conversation_analytics = None

@router.on_event("startup")
async def startup_conversational():
    global claude_manager, conversation_analytics
    logger.info("Conversational AI system initialized")

@router.post("/chat")
async def chat_with_ai(request: ConversationRequest):
    """Main chat endpoint for text conversations"""
    try:
        if not claude_manager:
            # Mock manager for demonstration
            claude_manager = ClaudeAIManager(None)
        
        # Generate session ID if not provided
        if not request.session_id:
            request.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Generate AI response
        response = await claude_manager.generate_response(
            request.message,
            request.session_id,
            request.context
        )
        
        # Add voice response if requested
        if request.mode in [ConversationMode.VOICE, ConversationMode.MIXED]:
            try:
                audio_bytes = await voice_manager.text_to_speech(response.response, request.language)
                response.audio_response = base64.b64encode(audio_bytes).decode()
            except Exception as e:
                logger.warning(f"Voice generation failed: {e}")
        
        return {
            "success": True,
            "response": response.dict(),
            "mode": request.mode,
            "language": request.language
        }
        
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.post("/voice-chat")
async def voice_chat(
    audio_file: UploadFile = File(...),
    language: str = "en",
    session_id: Optional[str] = None
):
    """Voice chat endpoint with STT and TTS"""
    try:
        # Validate audio file
        if not audio_file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="Invalid audio file format")
        
        # Read audio data
        audio_data = await audio_file.read()
        
        # Convert speech to text
        user_message = await voice_manager.speech_to_text(audio_data, language)
        
        # Process with Claude AI
        chat_request = ConversationRequest(
            message=user_message,
            session_id=session_id,
            mode=ConversationMode.VOICE,
            language=language
        )
        
        chat_response = await chat_with_ai(chat_request)
        
        return {
            "success": True,
            "transcribed_text": user_message,
            "response": chat_response["response"],
            "language": language
        }
        
    except Exception as e:
        logger.error(f"Voice chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice chat failed: {str(e)}")

@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Process chat request
            request = ConversationRequest(
                message=data["message"],
                session_id=session_id,
                mode=ConversationMode(data.get("mode", "text")),
                language=data.get("language", "en"),
                context=data.get("context")
            )
            
            # Generate response
            if not claude_manager:
                claude_manager = ClaudeAIManager(None)
            
            response = await claude_manager.generate_response(
                request.message,
                request.session_id,
                request.context
            )
            
            # Send response back to client
            await websocket.send_json({
                "type": "response",
                "data": response.dict()
            })
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })

@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, limit: int = 20):
    """Get chat history for a session"""
    try:
        if not claude_manager:
            claude_manager = ClaudeAIManager(None)
        
        history = await claude_manager._get_conversation_history(session_id)
        
        # Limit results
        limited_history = history[:limit] if history else []
        
        return {
            "success": True,
            "session_id": session_id,
            "message_count": len(limited_history),
            "history": limited_history
        }
        
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")

@router.post("/feedback")
async def submit_chat_feedback(
    session_id: str,
    message_id: str,
    rating: int = Field(..., ge=1, le=5),
    feedback: Optional[str] = None
):
    """Submit feedback for chat interaction"""
    try:
        feedback_data = {
            "session_id": session_id,
            "message_id": message_id,
            "rating": rating,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store feedback (mock implementation)
        if conversation_analytics:
            await conversation_analytics.track_conversation_metrics(
                session_id, "", "", ConversationTopic.GENERAL_HELP, rating
            )
        
        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "feedback_id": f"fb_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Feedback submission failed: {str(e)}")

@router.get("/analytics/conversations")
async def get_conversation_analytics(timeframe_days: int = 7):
    """Get conversation analytics and insights"""
    try:
        if not conversation_analytics:
            conversation_analytics = ConversationAnalytics(None)
        
        insights = await conversation_analytics.get_conversation_insights(timeframe_days)
        
        return {
            "success": True,
            "timeframe_days": timeframe_days,
            "insights": insights,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get conversation analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")

@router.get("/supported-languages")
async def get_supported_languages():
    """Get list of supported languages for conversations"""
    try:
        languages = {
            "en": {"name": "English", "native_name": "English", "voice_support": True},
            "zh": {"name": "Chinese", "native_name": "中文", "voice_support": True},
            "ja": {"name": "Japanese", "native_name": "日本語", "voice_support": True},
            "ko": {"name": "Korean", "native_name": "한국어", "voice_support": True},
            "th": {"name": "Thai", "native_name": "ไทย", "voice_support": True},
            "hi": {"name": "Hindi", "native_name": "हिन्दी", "voice_support": False}
        }
        
        return {
            "success": True,
            "supported_languages": languages,
            "total_languages": len(languages),
            "voice_enabled_count": sum(1 for lang in languages.values() if lang["voice_support"])
        }
        
    except Exception as e:
        logger.error(f"Failed to get supported languages: {e}")
        raise HTTPException(status_code=500, detail=f"Language info failed: {str(e)}")

@router.post("/train-response")
async def train_custom_response(
    topic: ConversationTopic,
    trigger_phrases: List[str],
    response_template: str,
    confidence_threshold: float = Field(0.8, ge=0.0, le=1.0)
):
    """Train custom responses for specific topics (admin only)"""
    try:
        training_data = {
            "topic": topic,
            "trigger_phrases": trigger_phrases,
            "response_template": response_template,
            "confidence_threshold": confidence_threshold,
            "created_at": datetime.now().isoformat(),
            "status": "training"
        }
        
        # Store training data (mock implementation)
        training_id = f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return {
            "success": True,
            "training_id": training_id,
            "status": "training",
            "estimated_completion": "5-10 minutes",
            "message": "Custom response training initiated"
        }
        
    except Exception as e:
        logger.error(f"Failed to train custom response: {e}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")