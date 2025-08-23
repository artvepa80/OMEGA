"""
Conversation Manager
Core conversation management with session handling and context awareness
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

@dataclass
class ConversationContext:
    session_id: str
    user_id: Optional[str]
    language: str
    topic_history: List[str]
    user_preferences: Dict[str, Any]
    conversation_state: Dict[str, Any]

class ConversationManager:
    """Manages conversation sessions and context"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.active_sessions = {}
        self.context_cache = {}
    
    async def initialize(self):
        """Initialize conversation manager"""
        logger.info("Conversation Manager initialized")
    
    async def get_session_context(self, session_id: str) -> ConversationContext:
        """Get conversation context for session"""
        if session_id in self.context_cache:
            return self.context_cache[session_id]
        
        # Load from Redis
        if self.redis:
            context_data = await self.redis.hgetall(f"conversation_context:{session_id}")
            if context_data:
                context = ConversationContext(
                    session_id=session_id,
                    user_id=context_data.get("user_id"),
                    language=context_data.get("language", "en"),
                    topic_history=json.loads(context_data.get("topic_history", "[]")),
                    user_preferences=json.loads(context_data.get("user_preferences", "{}")),
                    conversation_state=json.loads(context_data.get("conversation_state", "{}"))
                )
                self.context_cache[session_id] = context
                return context
        
        # Create new context
        context = ConversationContext(
            session_id=session_id,
            user_id=None,
            language="en",
            topic_history=[],
            user_preferences={},
            conversation_state={}
        )
        
        self.context_cache[session_id] = context
        return context
    
    async def update_session_context(self, context: ConversationContext):
        """Update conversation context"""
        self.context_cache[context.session_id] = context
        
        if self.redis:
            await self.redis.hset(
                f"conversation_context:{context.session_id}",
                mapping={
                    "user_id": context.user_id or "",
                    "language": context.language,
                    "topic_history": json.dumps(context.topic_history),
                    "user_preferences": json.dumps(context.user_preferences),
                    "conversation_state": json.dumps(context.conversation_state)
                }
            )
            await self.redis.expire(f"conversation_context:{context.session_id}", 86400)