"""
Sports Betting System
Advanced sports betting with live odds, edge calculation, and ROI analytics
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import aiohttp
import json
import logging
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)
router = APIRouter()

class Sport(str, Enum):
    FOOTBALL = "football"
    BASKETBALL = "basketball"
    TENNIS = "tennis"
    SOCCER = "soccer"
    BASEBALL = "baseball"
    HOCKEY = "hockey"
    CRICKET = "cricket"
    BADMINTON = "badminton"
    ESPORTS = "esports"

class BetType(str, Enum):
    MONEYLINE = "moneyline"
    SPREAD = "spread"
    TOTAL = "total"
    PROP = "prop"
    LIVE = "live"
    FUTURES = "futures"

class MarketStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    SETTLED = "settled"
    CANCELLED = "cancelled"

@dataclass
class OddsData:
    bookmaker: str
    odds: float
    probability: float
    edge: float
    confidence: float
    last_updated: datetime

class BettingMarket(BaseModel):
    market_id: str
    sport: Sport
    bet_type: BetType
    event_name: str
    event_time: datetime
    team_home: str
    team_away: str
    status: MarketStatus
    odds_data: List[Dict[str, Any]]
    best_odds: Dict[str, Any]
    edge_analysis: Dict[str, Any]
    recommendation: Optional[str] = None

class BetRecommendation(BaseModel):
    market_id: str
    recommended_bet: str
    stake_size: float
    expected_value: float
    confidence: float
    risk_level: str
    reasoning: List[str]

class SportsOddsManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.api_keys = {
            "odds_api": "your_odds_api_key",
            "rapidapi": "your_rapidapi_key"
        }
        self.bookmakers = [
            "draftkings", "fanduel", "betmgm", "caesars", 
            "bet365", "pinnacle", "betfair"
        ]
        
    async def get_live_odds(self, sport: Sport, region: str = "us") -> List[BettingMarket]:
        """Fetch live odds from multiple sources"""
        try:
            markets = []
            
            # Mock data for demonstration - replace with actual API calls
            mock_markets = await self._generate_mock_markets(sport)
            
            for market_data in mock_markets:
                # Calculate edge and best odds
                edge_analysis = await self._calculate_edge(market_data["odds_data"])
                best_odds = await self._find_best_odds(market_data["odds_data"])
                
                market = BettingMarket(
                    market_id=market_data["market_id"],
                    sport=sport,
                    bet_type=BetType(market_data["bet_type"]),
                    event_name=market_data["event_name"],
                    event_time=datetime.fromisoformat(market_data["event_time"]),
                    team_home=market_data["team_home"],
                    team_away=market_data["team_away"],
                    status=MarketStatus.ACTIVE,
                    odds_data=market_data["odds_data"],
                    best_odds=best_odds,
                    edge_analysis=edge_analysis,
                    recommendation=await self._generate_recommendation(edge_analysis)
                )
                
                markets.append(market)
            
            # Store in Redis for caching
            await self._cache_markets(markets)
            
            return markets
            
        except Exception as e:
            logger.error(f"Failed to fetch live odds: {e}")
            raise HTTPException(status_code=500, detail=f"Odds fetch failed: {str(e)}")
    
    async def _generate_mock_markets(self, sport: Sport) -> List[Dict[str, Any]]:
        """Generate mock market data for demonstration"""
        mock_events = {
            Sport.FOOTBALL: [
                {
                    "market_id": "nfl_001",
                    "event_name": "Chiefs vs Bills",
                    "team_home": "Kansas City Chiefs",
                    "team_away": "Buffalo Bills",
                    "bet_type": "moneyline",
                    "event_time": (datetime.now() + timedelta(hours=24)).isoformat()
                },
                {
                    "market_id": "nfl_002",
                    "event_name": "Cowboys vs Giants",
                    "team_home": "Dallas Cowboys",
                    "team_away": "New York Giants", 
                    "bet_type": "spread",
                    "event_time": (datetime.now() + timedelta(hours=48)).isoformat()
                }
            ],
            Sport.BASKETBALL: [
                {
                    "market_id": "nba_001",
                    "event_name": "Lakers vs Warriors",
                    "team_home": "Los Angeles Lakers",
                    "team_away": "Golden State Warriors",
                    "bet_type": "total",
                    "event_time": (datetime.now() + timedelta(hours=12)).isoformat()
                }
            ],
            Sport.SOCCER: [
                {
                    "market_id": "epl_001",
                    "event_name": "Arsenal vs Chelsea",
                    "team_home": "Arsenal",
                    "team_away": "Chelsea",
                    "bet_type": "moneyline",
                    "event_time": (datetime.now() + timedelta(hours=36)).isoformat()
                }
            ]
        }
        
        events = mock_events.get(sport, [])
        
        # Add mock odds data
        for event in events:
            event["odds_data"] = await self._generate_mock_odds(event["bet_type"])
        
        return events
    
    async def _generate_mock_odds(self, bet_type: str) -> List[Dict[str, Any]]:
        """Generate mock odds data from different bookmakers"""
        base_odds = np.random.uniform(1.8, 2.2)
        
        odds_data = []
        for bookmaker in self.bookmakers[:4]:  # Use first 4 bookmakers
            # Add some variation to odds
            variation = np.random.uniform(-0.1, 0.1)
            odds = round(base_odds + variation, 2)
            
            odds_entry = {
                "bookmaker": bookmaker,
                "odds": odds,
                "probability": round(1 / odds, 4),
                "last_updated": datetime.now().isoformat()
            }
            
            odds_data.append(odds_entry)
        
        return odds_data
    
    async def _calculate_edge(self, odds_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate betting edge and value"""
        if not odds_data:
            return {"edge": 0, "confidence": 0, "analysis": "No odds data"}
        
        # Calculate true probability using odds from multiple bookmakers
        implied_probs = [1 / odd["odds"] for odd in odds_data]
        avg_implied_prob = sum(implied_probs) / len(implied_probs)
        
        # Find best odds
        best_odds = max(odds_data, key=lambda x: x["odds"])["odds"]
        
        # Calculate edge (Kelly criterion)
        edge = (best_odds * (1 - avg_implied_prob)) - avg_implied_prob
        edge_percentage = edge * 100
        
        # Confidence based on odds consistency
        prob_variance = np.var(implied_probs)
        confidence = max(0, 1 - prob_variance * 10)  # Higher variance = lower confidence
        
        analysis = {
            "edge_percentage": round(edge_percentage, 2),
            "confidence": round(confidence, 3),
            "best_odds": best_odds,
            "avg_implied_probability": round(avg_implied_prob, 4),
            "variance": round(prob_variance, 6),
            "recommended_stake": self._calculate_kelly_stake(edge, best_odds) if edge > 0 else 0
        }
        
        return analysis
    
    def _calculate_kelly_stake(self, edge: float, odds: float, bankroll_fraction: float = 0.25) -> float:
        """Calculate optimal stake using Kelly criterion (conservative)"""
        if edge <= 0:
            return 0
        
        # Conservative Kelly: fraction of the full Kelly
        kelly_fraction = edge / (odds - 1)
        conservative_fraction = kelly_fraction * bankroll_fraction
        
        # Cap at 5% of bankroll
        return min(conservative_fraction, 0.05)
    
    async def _find_best_odds(self, odds_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find best odds across all bookmakers"""
        if not odds_data:
            return {}
        
        best_odds_entry = max(odds_data, key=lambda x: x["odds"])
        
        return {
            "bookmaker": best_odds_entry["bookmaker"],
            "odds": best_odds_entry["odds"],
            "advantage": round(best_odds_entry["odds"] - min(odd["odds"] for odd in odds_data), 3)
        }
    
    async def _generate_recommendation(self, edge_analysis: Dict[str, Any]) -> Optional[str]:
        """Generate betting recommendation based on edge analysis"""
        edge = edge_analysis.get("edge_percentage", 0)
        confidence = edge_analysis.get("confidence", 0)
        
        if edge > 3 and confidence > 0.7:
            return "STRONG_BUY"
        elif edge > 1 and confidence > 0.6:
            return "BUY"
        elif edge < -2:
            return "AVOID"
        else:
            return "HOLD"
    
    async def _cache_markets(self, markets: List[BettingMarket]):
        """Cache markets in Redis"""
        try:
            for market in markets:
                cache_key = f"sports:market:{market.market_id}"
                await self.redis.setex(
                    cache_key,
                    300,  # 5 minutes cache
                    market.json()
                )
        except Exception as e:
            logger.warning(f"Failed to cache markets: {e}")

class SportsAnalytics:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def calculate_roi(self, user_id: str, timeframe_days: int = 30) -> Dict[str, Any]:
        """Calculate ROI and betting analytics"""
        try:
            # Mock data - in real implementation, fetch from database
            mock_bets = await self._get_user_bets(user_id, timeframe_days)
            
            total_stakes = sum(bet["stake"] for bet in mock_bets)
            total_returns = sum(bet["return"] for bet in mock_bets if bet["status"] == "won")
            total_bets = len(mock_bets)
            won_bets = len([bet for bet in mock_bets if bet["status"] == "won"])
            
            roi = ((total_returns - total_stakes) / total_stakes * 100) if total_stakes > 0 else 0
            win_rate = (won_bets / total_bets * 100) if total_bets > 0 else 0
            
            analytics = {
                "timeframe_days": timeframe_days,
                "total_bets": total_bets,
                "total_stakes": round(total_stakes, 2),
                "total_returns": round(total_returns, 2),
                "profit_loss": round(total_returns - total_stakes, 2),
                "roi_percentage": round(roi, 2),
                "win_rate": round(win_rate, 2),
                "avg_stake": round(total_stakes / total_bets, 2) if total_bets > 0 else 0,
                "avg_odds": round(sum(bet["odds"] for bet in mock_bets) / total_bets, 2) if total_bets > 0 else 0,
                "sport_breakdown": await self._analyze_by_sport(mock_bets),
                "monthly_trend": await self._get_monthly_trend(mock_bets),
                "recommendations": await self._generate_improvement_suggestions(roi, win_rate)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"ROI calculation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Analytics calculation failed: {str(e)}")
    
    async def _get_user_bets(self, user_id: str, timeframe_days: int) -> List[Dict[str, Any]]:
        """Get user betting history (mock data)"""
        # In real implementation, fetch from database
        mock_bets = []
        
        for i in range(20):  # Generate 20 mock bets
            bet = {
                "bet_id": f"bet_{i+1}",
                "sport": np.random.choice(list(Sport)),
                "stake": round(np.random.uniform(10, 100), 2),
                "odds": round(np.random.uniform(1.5, 3.0), 2),
                "status": np.random.choice(["won", "lost", "pending"], p=[0.4, 0.5, 0.1]),
                "placed_at": (datetime.now() - timedelta(days=np.random.randint(0, timeframe_days))).isoformat()
            }
            
            if bet["status"] == "won":
                bet["return"] = bet["stake"] * bet["odds"]
            else:
                bet["return"] = 0
            
            mock_bets.append(bet)
        
        return mock_bets
    
    async def _analyze_by_sport(self, bets: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze performance by sport"""
        sport_stats = {}
        
        for bet in bets:
            sport = bet["sport"]
            if sport not in sport_stats:
                sport_stats[sport] = {
                    "total_bets": 0,
                    "total_stakes": 0,
                    "total_returns": 0,
                    "won_bets": 0
                }
            
            sport_stats[sport]["total_bets"] += 1
            sport_stats[sport]["total_stakes"] += bet["stake"]
            sport_stats[sport]["total_returns"] += bet["return"]
            
            if bet["status"] == "won":
                sport_stats[sport]["won_bets"] += 1
        
        # Calculate metrics for each sport
        for sport, stats in sport_stats.items():
            total_stakes = stats["total_stakes"]
            total_returns = stats["total_returns"]
            total_bets = stats["total_bets"]
            won_bets = stats["won_bets"]
            
            stats["roi"] = round(((total_returns - total_stakes) / total_stakes * 100), 2) if total_stakes > 0 else 0
            stats["win_rate"] = round((won_bets / total_bets * 100), 2) if total_bets > 0 else 0
            stats["profit_loss"] = round(total_returns - total_stakes, 2)
        
        return sport_stats
    
    async def _get_monthly_trend(self, bets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get monthly performance trend"""
        monthly_data = {}
        
        for bet in bets:
            bet_date = datetime.fromisoformat(bet["placed_at"])
            month_key = bet_date.strftime("%Y-%m")
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "month": month_key,
                    "total_stakes": 0,
                    "total_returns": 0,
                    "total_bets": 0
                }
            
            monthly_data[month_key]["total_stakes"] += bet["stake"]
            monthly_data[month_key]["total_returns"] += bet["return"]
            monthly_data[month_key]["total_bets"] += 1
        
        # Calculate monthly ROI
        for data in monthly_data.values():
            total_stakes = data["total_stakes"]
            total_returns = data["total_returns"]
            data["roi"] = round(((total_returns - total_stakes) / total_stakes * 100), 2) if total_stakes > 0 else 0
            data["profit_loss"] = round(total_returns - total_stakes, 2)
        
        return list(monthly_data.values())
    
    async def _generate_improvement_suggestions(self, roi: float, win_rate: float) -> List[str]:
        """Generate suggestions for improvement"""
        suggestions = []
        
        if roi < 0:
            suggestions.append("Your ROI is negative - consider reducing stake sizes and focusing on higher probability bets")
        
        if win_rate < 40:
            suggestions.append("Your win rate is below average - focus on value betting and avoid long-shot bets")
        
        if win_rate > 60 and roi < 10:
            suggestions.append("High win rate but low ROI - consider betting on higher odds for better returns")
        
        suggestions.extend([
            "Use the edge calculator to identify value bets",
            "Diversify across different sports and bet types",
            "Set strict bankroll management rules",
            "Track all bets and analyze performance regularly"
        ])
        
        return suggestions

# Initialize managers
sports_odds_manager = None
sports_analytics = None

@router.on_event("startup")
async def startup_sports():
    global sports_odds_manager, sports_analytics
    # These would be initialized with Redis client
    logger.info("Sports betting system initialized")

@router.get("/odds")
async def get_sports_odds(
    sport: Sport,
    region: str = Query("us", description="Region for odds (us, uk, eu)"),
    bet_type: Optional[BetType] = Query(None, description="Filter by bet type")
):
    """Get live sports odds with edge analysis"""
    try:
        if not sports_odds_manager:
            # Create mock manager for demonstration
            from unittest.mock import AsyncMock
            sports_odds_manager = AsyncMock()
            sports_odds_manager.get_live_odds = AsyncMock(return_value=[
                BettingMarket(
                    market_id="mock_001",
                    sport=sport,
                    bet_type=BetType.MONEYLINE,
                    event_name="Mock Event",
                    event_time=datetime.now() + timedelta(hours=24),
                    team_home="Team A",
                    team_away="Team B",
                    status=MarketStatus.ACTIVE,
                    odds_data=[{"bookmaker": "draftkings", "odds": 1.95}],
                    best_odds={"bookmaker": "draftkings", "odds": 1.95},
                    edge_analysis={"edge_percentage": 2.5, "confidence": 0.75}
                )
            ])
        
        markets = await sports_odds_manager.get_live_odds(sport, region)
        
        # Filter by bet type if specified
        if bet_type:
            markets = [m for m in markets if m.bet_type == bet_type]
        
        return {
            "success": True,
            "sport": sport,
            "region": region,
            "markets_count": len(markets),
            "markets": [market.dict() for market in markets],
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get odds: {e}")
        raise HTTPException(status_code=500, detail=f"Odds retrieval failed: {str(e)}")

@router.get("/picks")
async def get_betting_picks(
    sport: Optional[Sport] = None,
    min_edge: float = Query(1.0, description="Minimum edge percentage"),
    min_confidence: float = Query(0.6, description="Minimum confidence level")
):
    """Get AI-generated betting picks based on edge analysis"""
    try:
        # Mock picks generation
        picks = []
        
        # Generate mock picks for demonstration
        mock_picks_data = [
            {
                "market_id": "pick_001",
                "sport": Sport.FOOTBALL,
                "event": "Chiefs vs Bills",
                "pick": "Kansas City Chiefs ML",
                "odds": 1.85,
                "edge": 3.2,
                "confidence": 0.78,
                "stake": 2.5
            },
            {
                "market_id": "pick_002", 
                "sport": Sport.BASKETBALL,
                "event": "Lakers vs Warriors",
                "pick": "Over 220.5 Total Points",
                "odds": 1.91,
                "edge": 2.8,
                "confidence": 0.72,
                "stake": 2.1
            }
        ]
        
        for pick_data in mock_picks_data:
            if pick_data["edge"] >= min_edge and pick_data["confidence"] >= min_confidence:
                if not sport or pick_data["sport"] == sport:
                    pick = BetRecommendation(
                        market_id=pick_data["market_id"],
                        recommended_bet=pick_data["pick"],
                        stake_size=pick_data["stake"],
                        expected_value=pick_data["edge"],
                        confidence=pick_data["confidence"],
                        risk_level="medium" if pick_data["edge"] < 5 else "low",
                        reasoning=[
                            f"Positive edge of {pick_data['edge']}%",
                            f"High confidence level: {pick_data['confidence']}",
                            "Based on multi-bookmaker odds analysis"
                        ]
                    )
                    picks.append(pick)
        
        return {
            "success": True,
            "picks_count": len(picks),
            "filters": {
                "sport": sport,
                "min_edge": min_edge,
                "min_confidence": min_confidence
            },
            "picks": [pick.dict() for pick in picks],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate picks: {e}")
        raise HTTPException(status_code=500, detail=f"Picks generation failed: {str(e)}")

@router.get("/analytics/{user_id}")
async def get_betting_analytics(
    user_id: str,
    timeframe: int = Query(30, description="Timeframe in days")
):
    """Get comprehensive betting analytics and ROI"""
    try:
        if not sports_analytics:
            # Create mock analytics for demonstration
            from unittest.mock import AsyncMock
            sports_analytics = AsyncMock()
            
            mock_analytics = {
                "timeframe_days": timeframe,
                "total_bets": 25,
                "total_stakes": 1250.00,
                "total_returns": 1387.50,
                "profit_loss": 137.50,
                "roi_percentage": 11.0,
                "win_rate": 48.0,
                "avg_stake": 50.00,
                "avg_odds": 2.15,
                "sport_breakdown": {
                    "football": {"roi": 15.5, "win_rate": 52.0},
                    "basketball": {"roi": 8.2, "win_rate": 44.0}
                },
                "recommendations": [
                    "Great ROI! Keep up the current strategy",
                    "Consider increasing stakes on high-confidence picks"
                ]
            }
            
            sports_analytics.calculate_roi = AsyncMock(return_value=mock_analytics)
        
        analytics = await sports_analytics.calculate_roi(user_id, timeframe)
        
        return {
            "success": True,
            "user_id": user_id,
            "analytics": analytics,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")

@router.post("/track-bet")
async def track_bet(
    bet_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Track a placed bet for analytics"""
    try:
        # Validate bet data
        required_fields = ["user_id", "market_id", "stake", "odds", "bet_type"]
        for field in required_fields:
            if field not in bet_data:
                raise HTTPException(status_code=400, detail=f"Missing field: {field}")
        
        # Generate bet ID
        bet_id = f"bet_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{bet_data['user_id'][:8]}"
        
        # Store bet data
        bet_record = {
            "bet_id": bet_id,
            "user_id": bet_data["user_id"],
            "market_id": bet_data["market_id"],
            "stake": float(bet_data["stake"]),
            "odds": float(bet_data["odds"]),
            "bet_type": bet_data["bet_type"],
            "sport": bet_data.get("sport"),
            "event": bet_data.get("event"),
            "selection": bet_data.get("selection"),
            "status": "pending",
            "placed_at": datetime.now().isoformat()
        }
        
        # Store in Redis (mock implementation)
        # await redis_client.hset(f"bet:{bet_id}", mapping=bet_record)
        
        # Schedule result tracking
        background_tasks.add_task(
            schedule_bet_settlement,
            bet_id,
            bet_record
        )
        
        return {
            "success": True,
            "bet_id": bet_id,
            "status": "tracked",
            "message": "Bet tracked successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to track bet: {e}")
        raise HTTPException(status_code=500, detail=f"Bet tracking failed: {str(e)}")

async def schedule_bet_settlement(bet_id: str, bet_record: Dict[str, Any]):
    """Background task to track bet settlement"""
    try:
        logger.info(f"Scheduled settlement tracking for bet: {bet_id}")
        
        # In real implementation, this would check for bet results
        # and update the bet record accordingly
        await asyncio.sleep(10)  # Simulate processing
        
        logger.info(f"Bet settlement check completed for: {bet_id}")
        
    except Exception as e:
        logger.error(f"Bet settlement tracking failed for {bet_id}: {e}")

@router.get("/live-scores")
async def get_live_scores(sport: Optional[Sport] = None):
    """Get live scores and game updates"""
    try:
        # Mock live scores
        scores = [
            {
                "game_id": "live_001",
                "sport": Sport.FOOTBALL,
                "home_team": "Chiefs",
                "away_team": "Bills", 
                "home_score": 14,
                "away_score": 10,
                "quarter": 2,
                "time_remaining": "3:45",
                "status": "live"
            },
            {
                "game_id": "live_002",
                "sport": Sport.BASKETBALL,
                "home_team": "Lakers",
                "away_team": "Warriors",
                "home_score": 98,
                "away_score": 105,
                "quarter": 4,
                "time_remaining": "2:23",
                "status": "live"
            }
        ]
        
        if sport:
            scores = [score for score in scores if score["sport"] == sport]
        
        return {
            "success": True,
            "live_games": len(scores),
            "scores": scores,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get live scores: {e}")
        raise HTTPException(status_code=500, detail=f"Live scores failed: {str(e)}")