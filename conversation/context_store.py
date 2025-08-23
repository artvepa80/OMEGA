#!/usr/bin/env python3
"""
💾 OMEGA Context Store - Persistent conversation memory
Redis-backed with TTL and memory fallback
"""

from typing import Dict, Any, Optional, List
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class ConversationContext:
    """Optimized conversation context for Redis storage"""
    user_id: str
    conversation_id: str
    last_messages: List[Dict[str, Any]]  # Only last 10 messages
    user_expertise_level: str  # "beginner", "intermediate", "expert"
    preferred_explanation_style: str  # "accessible", "technical", "mathematical"
    conversation_topic: str
    technical_depth: float  # 0.0 to 1.0
    created_at: str
    updated_at: str
    message_count: int
    locale: str
    honesty_preferences: Dict[str, bool]  # User preferences for disclaimers
    last_intent_type: Optional[str] = None
    statistical_context: Dict[str, Any] = None  # Context about statistical discussions

class ContextStore:
    """
    Conversation context store with Redis backend and memory fallback
    Handles TTL, memory management, and graceful degradation
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379", ttl_hours: int = 72):
        self.redis_client = None
        self.ttl_seconds = ttl_hours * 3600
        self._memory_store = {}  # Fallback storage
        self._memory_ttl = {}   # TTL tracking for memory store
        
        # Try to initialize Redis
        self._init_redis(redis_url)
        
        # Start cleanup task for memory store
        if not self.redis_client:
            asyncio.create_task(self._cleanup_memory_store())
    
    def _init_redis(self, redis_url: str):
        """Initialize Redis connection with error handling"""
        try:
            import redis
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info(f"✅ Redis connected: {redis_url}")
        except ImportError:
            logger.warning("❌ Redis library not available - install with: pip install redis")
        except Exception as e:
            logger.warning(f"❌ Redis connection failed, using memory fallback: {e}")
            self.redis_client = None
    
    def _get_key(self, user_id: str, conversation_id: str) -> str:
        """Generate Redis key for conversation context"""
        return f"omega:ctx:{user_id}:{conversation_id}"
    
    async def get_context(self, user_id: str, conversation_id: str) -> Optional[ConversationContext]:
        """Get conversation context from Redis or memory"""
        key = self._get_key(user_id, conversation_id)
        
        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    ctx_dict = json.loads(data)
                    # Handle backward compatibility
                    if 'honesty_preferences' not in ctx_dict:
                        ctx_dict['honesty_preferences'] = {'show_disclaimers': True, 'emphasize_randomness': True}
                    if 'statistical_context' not in ctx_dict:
                        ctx_dict['statistical_context'] = {}
                    return ConversationContext(**ctx_dict)
            except Exception as e:
                logger.error(f"Redis get error for {key}: {e}")
        
        # Fallback to memory store
        if key in self._memory_store:
            # Check TTL
            if key in self._memory_ttl and datetime.now() > self._memory_ttl[key]:
                del self._memory_store[key]
                del self._memory_ttl[key]
                return None
            return self._memory_store[key]
        
        return None
    
    async def save_context(self, context: ConversationContext):
        """Save context to Redis with TTL or memory fallback"""
        key = self._get_key(context.user_id, context.conversation_id)
        context.updated_at = datetime.now().isoformat()
        
        # Ensure required fields have defaults
        if not hasattr(context, 'honesty_preferences') or context.honesty_preferences is None:
            context.honesty_preferences = {'show_disclaimers': True, 'emphasize_randomness': True}
        if not hasattr(context, 'statistical_context') or context.statistical_context is None:
            context.statistical_context = {}
        
        if self.redis_client:
            try:
                data = json.dumps(asdict(context), ensure_ascii=False)
                self.redis_client.setex(key, self.ttl_seconds, data)
                return
            except Exception as e:
                logger.error(f"Redis save error for {key}: {e}")
        
        # Fallback to memory store
        self._memory_store[key] = context
        self._memory_ttl[key] = datetime.now() + timedelta(seconds=self.ttl_seconds)
        logger.debug(f"Context saved to memory: {key}")
    
    async def add_message(self, user_id: str, conversation_id: str, 
                         role: str, content: str, metadata: Optional[Dict] = None):
        """Add message to conversation context"""
        context = await self.get_context(user_id, conversation_id)
        if not context:
            logger.warning(f"No context found for {user_id}:{conversation_id}")
            return
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        context.last_messages.append(message)
        
        # Keep only last 10 messages for memory efficiency
        if len(context.last_messages) > 10:
            context.last_messages = context.last_messages[-10:]
        
        context.message_count += 1
        
        # Update statistical context if it's a statistical discussion
        if metadata and 'intent_type' in metadata:
            context.last_intent_type = metadata['intent_type']
            
            if metadata['intent_type'] in ['statistical_question', 'analysis_request']:
                if not context.statistical_context:
                    context.statistical_context = {}
                context.statistical_context['last_statistical_topic'] = metadata.get('entities', {})
                context.statistical_context['statistical_discussion_count'] = (
                    context.statistical_context.get('statistical_discussion_count', 0) + 1
                )
        
        await self.save_context(context)
    
    async def create_context(self, user_id: str, conversation_id: str, 
                           initial_message: str, locale: str = "es") -> ConversationContext:
        """Create new conversation context"""
        
        # Infer user expertise from initial message
        expertise = self._infer_expertise(initial_message)
        topic = self._infer_topic(initial_message)
        explanation_style = self._infer_explanation_style(initial_message, expertise)
        
        context = ConversationContext(
            user_id=user_id,
            conversation_id=conversation_id,
            last_messages=[],
            user_expertise_level=expertise,
            preferred_explanation_style=explanation_style,
            conversation_topic=topic,
            technical_depth=self._calculate_initial_tech_depth(expertise),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            message_count=0,
            locale=locale,
            honesty_preferences={
                'show_disclaimers': True,
                'emphasize_randomness': True,
                'statistical_warnings': True
            },
            last_intent_type=None,
            statistical_context={}
        )
        
        await self.save_context(context)
        logger.info(f"Created new context: {user_id}:{conversation_id} (expertise: {expertise})")
        
        return context
    
    def _infer_expertise(self, message: str) -> str:
        """Infer user expertise level from initial message"""
        message_lower = message.lower()
        
        expert_terms = [
            "backtest", "ensemble", "lstm", "transformer", "brier", "calibration",
            "anti-leakage", "drift", "auc", "precision", "recall", "f1", "mape", 
            "rmse", "sharpe", "volatility", "statistical significance", "p-value",
            "monte carlo", "bayesian", "regression", "neural network"
        ]
        
        beginner_terms = [
            "no entiendo", "explica simple", "soy nuevo", "principiante", "basico",
            "que significa", "dont understand", "explain simple", "for beginners",
            "easy explanation", "no se nada", "empezando"
        ]
        
        intermediate_terms = [
            "algoritmo", "algorithm", "patron", "pattern", "estadistica", "statistics",
            "probabilidad", "probability", "analisis", "analysis"
        ]
        
        expert_score = sum(1 for term in expert_terms if term in message_lower)
        beginner_score = sum(1 for term in beginner_terms if term in message_lower)
        intermediate_score = sum(1 for term in intermediate_terms if term in message_lower)
        
        if expert_score >= 2:
            return "expert"
        elif beginner_score >= 1:
            return "beginner"
        elif intermediate_score >= 1:
            return "intermediate"
        else:
            return "intermediate"  # Default
    
    def _infer_topic(self, message: str) -> str:
        """Infer main conversation topic"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["loteria", "lottery", "kabala", "mega", "powerball"]):
            return "lottery_analysis"
        elif any(word in message_lower for word in ["probabilidad", "probability", "estadistica", "statistics"]):
            return "statistical_concepts"
        elif any(word in message_lower for word in ["algoritmo", "algorithm", "como funciona", "how it works"]):
            return "system_explanation"
        else:
            return "general"
    
    def _infer_explanation_style(self, message: str, expertise: str) -> str:
        """Infer preferred explanation style"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["simple", "facil", "basico", "easy", "basic"]):
            return "accessible"
        elif any(word in message_lower for word in ["tecnico", "technical", "detallado", "detailed"]):
            return "technical"
        elif any(word in message_lower for word in ["matematico", "mathematical", "formula", "ecuacion"]):
            return "mathematical"
        else:
            # Default based on expertise
            return {
                "beginner": "accessible",
                "intermediate": "accessible", 
                "expert": "technical"
            }.get(expertise, "accessible")
    
    def _calculate_initial_tech_depth(self, expertise: str) -> float:
        """Calculate initial technical depth"""
        return {
            "beginner": 0.2,
            "intermediate": 0.5,
            "expert": 0.8
        }.get(expertise, 0.5)
    
    async def update_user_preferences(self, user_id: str, conversation_id: str, 
                                    preferences: Dict[str, Any]):
        """Update user preferences in context"""
        context = await self.get_context(user_id, conversation_id)
        if not context:
            return
        
        # Update honesty preferences
        if 'honesty_preferences' in preferences:
            context.honesty_preferences.update(preferences['honesty_preferences'])
        
        # Update explanation style if requested
        if 'explanation_style' in preferences:
            context.preferred_explanation_style = preferences['explanation_style']
        
        # Update technical depth
        if 'technical_depth' in preferences:
            context.technical_depth = max(0.0, min(1.0, preferences['technical_depth']))
        
        await self.save_context(context)
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics across conversations"""
        if not self.redis_client:
            return {"error": "Stats require Redis backend"}
        
        try:
            # Find all conversations for user
            pattern = f"omega:ctx:{user_id}:*"
            keys = self.redis_client.keys(pattern)
            
            total_conversations = len(keys)
            total_messages = 0
            topics = set()
            expertise_levels = set()
            
            for key in keys[:10]:  # Limit to prevent performance issues
                try:
                    data = self.redis_client.get(key)
                    if data:
                        ctx_dict = json.loads(data)
                        total_messages += ctx_dict.get('message_count', 0)
                        topics.add(ctx_dict.get('conversation_topic', 'unknown'))
                        expertise_levels.add(ctx_dict.get('user_expertise_level', 'unknown'))
                except:
                    continue
            
            return {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "topics": list(topics),
                "expertise_levels": list(expertise_levels)
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats for {user_id}: {e}")
            return {"error": str(e)}
    
    async def _cleanup_memory_store(self):
        """Background task to cleanup expired memory store entries"""
        while True:
            try:
                await asyncio.sleep(3600)  # Cleanup every hour
                
                current_time = datetime.now()
                expired_keys = [
                    key for key, expiry in self._memory_ttl.items() 
                    if current_time > expiry
                ]
                
                for key in expired_keys:
                    self._memory_store.pop(key, None)
                    self._memory_ttl.pop(key, None)
                
                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired context entries")
                    
            except Exception as e:
                logger.error(f"Error in memory cleanup: {e}")
    
    def get_store_info(self) -> Dict[str, Any]:
        """Get information about the context store"""
        return {
            "backend": "redis" if self.redis_client else "memory",
            "ttl_hours": self.ttl_seconds // 3600,
            "memory_contexts": len(self._memory_store) if not self.redis_client else "N/A",
            "redis_available": self.redis_client is not None
        }