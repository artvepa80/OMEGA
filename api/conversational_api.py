#!/usr/bin/env python3
"""
🌐 OMEGA Conversational API - Production-ready endpoints
FastAPI with rate limiting, validation, and honest statistical communication
"""

import time
import logging
from typing import Optional, Dict, Any, List
from collections import defaultdict, deque
from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator, Field
from datetime import datetime
import asyncio
import json

from conversation.conversation_manager import OmegaConversationManager

logger = logging.getLogger(__name__)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ChatMessage(BaseModel):
    """Chat message request model with validation"""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    user_id: str = Field(..., min_length=1, max_length=100, description="Unique user identifier") 
    conversation_id: Optional[str] = Field(None, max_length=100, description="Conversation identifier")
    locale: str = Field("es", description="Response language (es/en)")
    
    @validator('message')
    def validate_message_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Message cannot be empty or whitespace only')
        
        # Basic content moderation
        prohibited_words = ['hack', 'cheat', 'exploit', 'guarantee win']
        message_lower = v.lower()
        if any(word in message_lower for word in prohibited_words):
            raise ValueError('Message contains prohibited content')
        
        return v.strip()
    
    @validator('locale')
    def validate_locale(cls, v):
        if v not in ['es', 'en']:
            raise ValueError('Locale must be "es" or "en"')
        return v

class ChatResponse(BaseModel):
    """Standardized chat response"""
    text: str
    metadata: Dict[str, Any]
    conversation_id: str
    timestamp: str
    performance: Optional[Dict[str, float]] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: float
    version: str
    components: Dict[str, str]
    performance: Dict[str, Any]

class ConversationHistory(BaseModel):
    """Conversation history response"""
    user_id: str
    conversations: List[Dict[str, Any]]
    total_conversations: int
    total_messages: int

# ============================================================================
# RATE LIMITING
# ============================================================================

class TokenBucketRateLimiter:
    """
    Token bucket rate limiter with burst support
    More sophisticated than simple sliding window
    """
    
    def __init__(self, rate: float, burst: int, window: int = 60):
        """
        rate: tokens per second
        burst: maximum tokens in bucket
        window: refill window in seconds
        """
        self.rate = rate
        self.burst = burst
        self.window = window
        self.buckets = defaultdict(lambda: {"tokens": burst, "last_update": time.time()})
    
    def is_allowed(self, key: str) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed and return rate limit info
        Returns: (allowed, rate_limit_info)
        """
        now = time.time()
        bucket = self.buckets[key]
        
        # Calculate tokens to add based on elapsed time
        elapsed = now - bucket["last_update"]
        tokens_to_add = elapsed * self.rate
        bucket["tokens"] = min(self.burst, bucket["tokens"] + tokens_to_add)
        bucket["last_update"] = now
        
        # Check if request is allowed
        if bucket["tokens"] >= 1.0:
            bucket["tokens"] -= 1.0
            allowed = True
        else:
            allowed = False
        
        rate_limit_info = {
            "remaining": int(bucket["tokens"]),
            "reset_time": now + (self.burst - bucket["tokens"]) / self.rate,
            "retry_after": max(0, (1.0 - bucket["tokens"]) / self.rate) if not allowed else None
        }
        
        return allowed, rate_limit_info

class RateLimitManager:
    """Manages multiple rate limiters for different endpoints"""
    
    def __init__(self):
        # Different limits for different endpoints
        self.limiters = {
            "chat": TokenBucketRateLimiter(rate=1.0, burst=10),      # 1/sec, burst 10
            "websocket": TokenBucketRateLimiter(rate=2.0, burst=20), # 2/sec, burst 20  
            "global": TokenBucketRateLimiter(rate=0.5, burst=30),    # Global limit per IP
        }
    
    def check_limits(self, key: str, endpoint: str) -> tuple[bool, Dict[str, Any]]:
        """Check both endpoint-specific and global limits"""
        
        # Check endpoint-specific limit
        endpoint_allowed, endpoint_info = self.limiters[endpoint].is_allowed(f"{endpoint}:{key}")
        
        # Check global limit
        global_allowed, global_info = self.limiters["global"].is_allowed(f"global:{key}")
        
        # Must pass both limits
        allowed = endpoint_allowed and global_allowed
        
        # Return most restrictive info
        if not endpoint_allowed:
            return False, {"limit_type": endpoint, **endpoint_info}
        elif not global_allowed:
            return False, {"limit_type": "global", **global_info}
        else:
            return True, {"limit_type": "ok", **endpoint_info}

# ============================================================================
# DEPENDENCIES
# ============================================================================

def get_client_id(request: Request) -> str:
    """Extract client identifier (IP + User-Agent hash)"""
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "unknown")
    return f"{client_ip}:{hash(user_agent) % 10000}"

async def rate_limit_dependency(request: Request, endpoint: str) -> None:
    """Rate limiting dependency"""
    rate_limiter = request.app.state.rate_limiter
    client_id = get_client_id(request)
    
    allowed, rate_info = rate_limiter.check_limits(client_id, endpoint)
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "limit_type": rate_info["limit_type"],
                "retry_after": rate_info.get("retry_after", 60)
            },
            headers={"Retry-After": str(int(rate_info.get("retry_after", 60)))}
        )

# ============================================================================
# API CREATION
# ============================================================================

def create_conversational_api(omega_control_center, redis_url: str = "redis://localhost:6379") -> FastAPI:
    """
    Create FastAPI application with conversational endpoints
    Production-ready with proper error handling, logging, and rate limiting
    """
    
    app = FastAPI(
        title="OMEGA Conversational AI API",
        version="3.0.0",
        description="Honest statistical analysis and conversational interface for OMEGA AI",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # ============================================================================
    # MIDDLEWARE
    # ============================================================================
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure based on deployment needs
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(
            f"{request.method} {request.url} - {response.status_code} - {process_time:.3f}s"
        )
        
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # ============================================================================
    # APPLICATION STATE
    # ============================================================================
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize application state"""
        app.state.conversation_manager = OmegaConversationManager(omega_control_center, redis_url)
        app.state.rate_limiter = RateLimitManager()
        app.state.start_time = time.time()
        logger.info("🚀 OMEGA Conversational API started")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown"""
        logger.info("🛑 OMEGA Conversational API stopping")
    
    # ============================================================================
    # ENDPOINTS
    # ============================================================================
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check(request: Request):
        """Comprehensive health check endpoint"""
        try:
            conversation_manager = request.app.state.conversation_manager
            performance_stats = conversation_manager.get_performance_stats()
            
            return HealthResponse(
                status="healthy",
                timestamp=time.time(),
                version="3.0.0",
                components={
                    "conversation_manager": "ok",
                    "omega_control": "ok" if hasattr(omega_control_center, 'analyze_opportunity') else "limited",
                    "context_store": "redis" if performance_stats.get("context_store_status", {}).get("redis_available") else "memory",
                    "rate_limiter": "ok"
                },
                performance=performance_stats
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    
    @app.post("/v3/chat", response_model=ChatResponse)
    async def chat_endpoint(
        chat_message: ChatMessage, 
        request: Request,
        _: None = Depends(lambda r: rate_limit_dependency(r, "chat"))
    ):
        """
        Main conversational endpoint
        Provides honest statistical analysis with appropriate disclaimers
        """
        start_time = time.time()
        
        try:
            conversation_manager = request.app.state.conversation_manager
            
            # Process message
            response = await conversation_manager.process_message(
                user_id=chat_message.user_id,
                message=chat_message.message,
                conversation_id=chat_message.conversation_id,
                locale=chat_message.locale
            )
            
            # Add performance info
            processing_time = time.time() - start_time
            
            return ChatResponse(
                text=response["text"],
                metadata=response["metadata"],
                conversation_id=response["metadata"]["conversation_id"],
                timestamp=response["timestamp"],
                performance={"processing_time": round(processing_time, 3)}
            )
            
        except Exception as e:
            logger.error(f"Chat endpoint error for user {chat_message.user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Internal server error",
                    "message": "Unable to process your message at this time. Please try again later."
                }
            )
    
    @app.websocket("/v3/chat/stream")
    async def chat_websocket(websocket: WebSocket):
        """
        WebSocket endpoint for real-time conversation
        Handles disconnections gracefully and enforces rate limits
        """
        await websocket.accept()
        
        client_ip = websocket.client.host
        logger.info(f"WebSocket connected: {client_ip}")
        
        try:
            conversation_manager = websocket.app.state.conversation_manager
            rate_limiter = websocket.app.state.rate_limiter
            
            while True:
                # Receive message
                try:
                    data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await websocket.send_json({"type": "ping", "timestamp": time.time()})
                    continue
                
                # Validate message format
                if not isinstance(data, dict) or "message" not in data or "user_id" not in data:
                    await websocket.send_json({
                        "type": "error",
                        "error": "Invalid message format. Required: message, user_id"
                    })
                    continue
                
                # Rate limiting
                allowed, rate_info = rate_limiter.check_limits(client_ip, "websocket")
                if not allowed:
                    await websocket.send_json({
                        "type": "rate_limit",
                        "error": "Rate limit exceeded",
                        "retry_after": rate_info.get("retry_after", 30)
                    })
                    continue
                
                # Validate message content
                try:
                    message = ChatMessage(
                        message=data["message"],
                        user_id=data["user_id"],
                        conversation_id=data.get("conversation_id"),
                        locale=data.get("locale", "es")
                    )
                except Exception as e:
                    await websocket.send_json({
                        "type": "validation_error", 
                        "error": str(e)
                    })
                    continue
                
                # Process message
                try:
                    response = await conversation_manager.process_message(
                        user_id=message.user_id,
                        message=message.message,
                        conversation_id=message.conversation_id,
                        locale=message.locale
                    )
                    
                    # Send response
                    await websocket.send_json({
                        "type": "response",
                        **response
                    })
                    
                except Exception as e:
                    logger.error(f"WebSocket processing error: {e}")
                    await websocket.send_json({
                        "type": "processing_error",
                        "error": "Unable to process your message. Please try again."
                    })
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected normally: {client_ip}")
        except Exception as e:
            logger.error(f"WebSocket error for {client_ip}: {e}")
            try:
                await websocket.close(code=1011)  # Server error
            except:
                pass
    
    @app.get("/v3/conversations/{user_id}/history", response_model=ConversationHistory)
    async def get_conversation_history(
        user_id: str,
        request: Request,
        limit: int = 10,
        _: None = Depends(lambda r: rate_limit_dependency(r, "chat"))
    ):
        """Get conversation history for a user"""
        try:
            conversation_manager = request.app.state.conversation_manager
            
            # Get user stats from context store
            user_stats = await conversation_manager.context_store.get_user_stats(user_id)
            
            return ConversationHistory(
                user_id=user_id,
                conversations=[],  # Placeholder - implement full history if needed
                total_conversations=user_stats.get("total_conversations", 0),
                total_messages=user_stats.get("total_messages", 0)
            )
            
        except Exception as e:
            logger.error(f"Error getting conversation history for {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve conversation history"
            )
    
    @app.get("/v3/admin/stats")
    async def get_admin_stats(request: Request):
        """Admin endpoint for system statistics (add authentication in production)"""
        try:
            conversation_manager = request.app.state.conversation_manager
            performance_stats = conversation_manager.get_performance_stats()
            
            # Add uptime
            uptime = time.time() - request.app.state.start_time
            
            return {
                "uptime_seconds": round(uptime, 1),
                "performance": performance_stats,
                "system_info": {
                    "version": "3.0.0",
                    "endpoints_available": ["chat", "websocket", "health", "history"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting admin stats: {e}")
            raise HTTPException(status_code=500, detail="Unable to retrieve stats")
    
    # ============================================================================
    # ERROR HANDLERS
    # ============================================================================
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Custom HTTP exception handler with structured response"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "status_code": exc.status_code,
                "detail": exc.detail,
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url)
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """General exception handler for unexpected errors"""
        logger.error(f"Unexpected error: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "status_code": 500,
                "detail": "Internal server error",
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url)
            }
        )
    
    return app

# ============================================================================
# STANDALONE SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Mock control center for testing
    class MockOmegaControl:
        async def analyze_opportunity(self, domain: str, game_id: str):
            return {
                "game_name": "Test Game",
                "items": [
                    {"numbers": [1, 2, 3, 4, 5, 6], "ens_score": 0.75, "source": "test"}
                ]
            }
    
    app = create_conversational_api(MockOmegaControl())
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")