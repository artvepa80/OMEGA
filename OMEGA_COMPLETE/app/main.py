"""
OMEGA PRO AI - Main FastAPI Application
Complete integrated system with lottery predictions, sports betting, Asian markets, and conversational AI
"""

from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import redis.asyncio as aioredis
import asyncio
import logging
from typing import Optional
import os
from datetime import datetime

# Import routers
from app.kyc import router as kyc_router
from app.sports import router as sports_router
from app.asian_markets import router as asian_router
from app.conversational import router as conversational_router
from app.payments import router as payments_router

# Import core systems
from core.omega_flow_integrated import OmegaFlowIntegrated
from core.omega_sports_flow import OmegaSportsFlowManager
from core.conversation_manager import ConversationManager

# Security
security = HTTPBearer(auto_error=False)

# Global state
redis_client: Optional[aioredis.Redis] = None
omega_flow: Optional[OmegaFlowManager] = None
sports_flow: Optional[OmegaSportsFlowManager] = None
conversation_manager: Optional[ConversationManager] = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global redis_client, omega_flow, sports_flow, conversation_manager
    
    try:
        # Initialize Redis
        redis_client = aioredis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"),
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("Redis connection established")
        
        # Initialize core systems
        omega_flow = OmegaFlowIntegrated(redis_client)
        sports_flow = OmegaSportsFlowManager(redis_client)
        conversation_manager = ConversationManager(redis_client)
        
        # Initialize systems
        await omega_flow.initialize()
        await sports_flow.initialize()
        await conversation_manager.initialize()
        
        logger.info("All systems initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize systems: {e}")
        raise
    finally:
        # Cleanup
        if redis_client:
            await redis_client.close()
        logger.info("Application shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="OMEGA PRO AI",
    description="Advanced AI system for lottery predictions, sports betting, and conversational AI",
    version="4.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    """Rate limiting based on IP address"""
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"
    
    if redis_client:
        current = await redis_client.get(key)
        if current and int(current) > 100:  # 100 requests per minute
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        await redis_client.incr(key)
        await redis_client.expire(key, 60)
    
    response = await call_next(request)
    return response

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Authentication dependency"""
    if not credentials:
        return None
    
    # Validate token
    token = credentials.credentials
    if redis_client:
        user_data = await redis_client.get(f"auth:{token}")
        if user_data:
            return user_data
    
    return None

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        if redis_client:
            await redis_client.ping()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "systems": {
                "redis": "connected" if redis_client else "disconnected",
                "omega_flow": "initialized" if omega_flow else "not_initialized",
                "sports_flow": "initialized" if sports_flow else "not_initialized",
                "conversation_manager": "initialized" if conversation_manager else "not_initialized"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

# Main lottery endpoint
@app.post("/entregar_series")
async def entregar_series(
    request: dict,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user)
):
    """Main OMEGA lottery prediction endpoint"""
    try:
        if not omega_flow:
            raise HTTPException(status_code=503, detail="OMEGA flow not initialized")
        
        # Validate request
        required_fields = ["lottery_type", "series_count"]
        for field in required_fields:
            if field not in request:
                raise HTTPException(status_code=400, detail=f"Missing field: {field}")
        
        # Generate statistical analysis using real OMEGA models
        result = await omega_flow.generate_series(
            lottery_type=request["lottery_type"],
            series_count=request["series_count"],
            filters=request.get("filters", {}),
            user_preferences=request.get("preferences", {})
        )
        
        # Log prediction for analysis
        background_tasks.add_task(
            log_prediction,
            user_id=user,
            request=request,
            result=result
        )
        
        return {
            "success": True,
            "data": {
                "series": [{"numbers": s.numbers, "confidence": s.confidence, 
                           "pattern_score": s.pattern_score, "frequency_score": s.frequency_score,
                           "statistical_score": s.statistical_score, "source": s.source,
                           "svi_score": s.svi_score, "meta_data": s.meta_data} for s in result.series],
                "analysis": result.analysis,
                "recommendations": result.recommendations,
                "disclaimer": result.disclaimer
            },
            "timestamp": datetime.now().isoformat(),
            "expires_at": result.expires_at.isoformat(),
            "type": "statistical_analysis"
        }
        
    except Exception as e:
        logger.error(f"Error in entregar_series: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task for logging
async def log_prediction(user_id: str, request: dict, result: dict):
    """Log prediction for analysis"""
    if redis_client:
        log_data = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "request": request,
            "result": result
        }
        await redis_client.lpush("prediction_logs", str(log_data))

# Include routers
app.include_router(kyc_router, prefix="/kyc", tags=["KYC"])
app.include_router(sports_router, prefix="/sports", tags=["Sports"])
app.include_router(asian_router, prefix="/asian", tags=["Asian Markets"])
app.include_router(conversational_router, prefix="/chat", tags=["Conversational AI"])
app.include_router(payments_router, prefix="/payments", tags=["Payments"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "name": "OMEGA PRO AI",
        "version": "4.0.0",
        "status": "operational",
        "features": [
            "lottery_predictions",
            "sports_betting",
            "asian_markets",
            "conversational_ai",
            "crypto_payments",
            "kyc_verification"
        ],
        "endpoints": {
            "lottery": "/entregar_series",
            "kyc": "/kyc/*",
            "sports": "/sports/*",
            "asian": "/asian/*",
            "chat": "/chat/*",
            "payments": "/payments/*"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=False,
        log_level="info"
    )