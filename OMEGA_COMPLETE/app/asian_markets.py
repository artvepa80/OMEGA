"""
Asian Markets System
Specialized Asian betting markets with handicap support, Asian sports, and cultural localization
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import logging
from decimal import Decimal
import numpy as np

logger = logging.getLogger(__name__)
router = APIRouter()

class AsianSport(str, Enum):
    ASIAN_FOOTBALL = "asian_football"
    CRICKET = "cricket"
    BADMINTON = "badminton"
    TABLE_TENNIS = "table_tennis"
    KABADDI = "kabaddi"
    SEPAK_TAKRAW = "sepak_takraw"
    VOLLEYBALL = "volleyball"
    ESPORTS_MOBILE = "esports_mobile"

class AsianLeague(str, Enum):
    # Football
    J_LEAGUE = "j_league"
    K_LEAGUE = "k_league"
    CHINESE_SUPER = "chinese_super"
    THAI_LEAGUE = "thai_league"
    
    # Cricket
    IPL = "ipl"
    BPL = "bpl"
    PSL = "psl"
    BBL = "bbl"
    
    # Badminton
    BWF_SUPER_SERIES = "bwf_super_series"
    
    # Esports
    MOBILE_LEGENDS = "mobile_legends"
    PUBG_MOBILE = "pubg_mobile"

class HandicapType(str, Enum):
    ASIAN_HANDICAP = "asian_handicap"
    QUARTER_HANDICAP = "quarter_handicap" 
    HALF_HANDICAP = "half_handicap"
    EUROPEAN_HANDICAP = "european_handicap"
    CORNER_HANDICAP = "corner_handicap"
    GOAL_LINE = "goal_line"

class AsianMarket(BaseModel):
    market_id: str
    sport: AsianSport
    league: AsianLeague
    event_name: str
    event_time: datetime
    home_team: str
    away_team: str
    handicap_type: HandicapType
    handicap_line: float
    home_odds: float
    away_odds: float
    draw_odds: Optional[float] = None
    total_line: Optional[float] = None
    over_odds: Optional[float] = None
    under_odds: Optional[float] = None
    live_score: Optional[Dict[str, Any]] = None
    market_status: str = "active"

class AsianHandicapEngine:
    """Advanced Asian Handicap calculation and edge detection"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        
    def calculate_asian_handicap(self, home_strength: float, away_strength: float, 
                               venue_advantage: float = 0.1) -> Dict[str, Any]:
        """Calculate Asian handicap lines and odds"""
        
        # Calculate team strength differential
        strength_diff = home_strength - away_strength + venue_advantage
        
        # Base handicap calculation
        base_handicap = round(strength_diff * 2) / 2  # Round to nearest 0.5
        
        # Generate multiple handicap lines
        handicap_lines = {
            "main_line": base_handicap,
            "quarter_lines": [
                base_handicap - 0.25,
                base_handicap + 0.25
            ],
            "half_lines": [
                base_handicap - 0.5,
                base_handicap + 0.5
            ]
        }
        
        # Calculate odds for each line
        odds_data = {}
        for line_type, lines in handicap_lines.items():
            if isinstance(lines, list):
                odds_data[line_type] = []
                for line in lines:
                    odds = self._calculate_handicap_odds(line, strength_diff)
                    odds_data[line_type].append({
                        "handicap": line,
                        "home_odds": odds["home"],
                        "away_odds": odds["away"]
                    })
            else:
                odds = self._calculate_handicap_odds(lines, strength_diff)
                odds_data[line_type] = {
                    "handicap": lines,
                    "home_odds": odds["home"],
                    "away_odds": odds["away"]
                }
        
        return {
            "handicap_analysis": odds_data,
            "recommended_line": base_handicap,
            "confidence": min(abs(strength_diff) / 2, 0.95),
            "edge_opportunities": self._find_edge_opportunities(odds_data)
        }
    
    def _calculate_handicap_odds(self, handicap: float, strength_diff: float) -> Dict[str, float]:
        """Calculate odds for a specific handicap line"""
        
        # Adjust for handicap
        adjusted_diff = strength_diff - handicap
        
        # Convert to probability using logistic function
        home_prob = 1 / (1 + np.exp(-adjusted_diff))
        away_prob = 1 - home_prob
        
        # Add bookmaker margin (typically 5%)
        margin = 0.05
        home_prob_with_margin = home_prob * (1 - margin)
        away_prob_with_margin = away_prob * (1 - margin)
        
        # Convert to odds
        home_odds = 1 / home_prob_with_margin if home_prob_with_margin > 0 else 10
        away_odds = 1 / away_prob_with_margin if away_prob_with_margin > 0 else 10
        
        return {
            "home": round(home_odds, 2),
            "away": round(away_odds, 2)
        }
    
    def _find_edge_opportunities(self, odds_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find potential edge betting opportunities"""
        opportunities = []
        
        for line_type, data in odds_data.items():
            if isinstance(data, list):
                for item in data:
                    edge = self._calculate_edge(item["home_odds"], item["away_odds"])
                    if edge > 2:  # Edge > 2%
                        opportunities.append({
                            "line_type": line_type,
                            "handicap": item["handicap"],
                            "recommended_bet": "home" if item["home_odds"] > item["away_odds"] else "away",
                            "edge_percentage": edge
                        })
            else:
                edge = self._calculate_edge(data["home_odds"], data["away_odds"])
                if edge > 2:
                    opportunities.append({
                        "line_type": line_type,
                        "handicap": data["handicap"],
                        "recommended_bet": "home" if data["home_odds"] > data["away_odds"] else "away",
                        "edge_percentage": edge
                    })
        
        return opportunities
    
    def _calculate_edge(self, home_odds: float, away_odds: float) -> float:
        """Calculate betting edge based on odds imbalance"""
        home_prob = 1 / home_odds
        away_prob = 1 / away_odds
        total_prob = home_prob + away_prob
        
        # Edge is the overround converted to percentage
        overround = (total_prob - 1) * 100
        return max(0, 5 - overround)  # Assume fair odds have 5% margin

class AsianSportsDataProvider:
    """Provider for Asian sports data and odds"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.api_endpoints = {
            "betinasia": "https://api.betinasia.com/v1/",
            "isports": "https://api.isports.com/v2/",
            "sbobet": "https://api.sbobet.com/web-root/restricted/"
        }
    
    async def get_asian_markets(self, sport: AsianSport, league: Optional[AsianLeague] = None) -> List[AsianMarket]:
        """Get markets for Asian sports"""
        try:
            # Mock data for demonstration
            markets = await self._generate_mock_asian_markets(sport, league)
            
            # Enhance with handicap analysis
            enhanced_markets = []
            for market_data in markets:
                # Add handicap analysis
                if hasattr(self, 'handicap_engine'):
                    handicap_analysis = self.handicap_engine.calculate_asian_handicap(
                        market_data.get("home_strength", 0.5),
                        market_data.get("away_strength", 0.5)
                    )
                    market_data["handicap_analysis"] = handicap_analysis
                
                market = AsianMarket(**market_data)
                enhanced_markets.append(market)
            
            return enhanced_markets
            
        except Exception as e:
            logger.error(f"Failed to get Asian markets: {e}")
            raise HTTPException(status_code=500, detail=f"Asian markets fetch failed: {str(e)}")
    
    async def _generate_mock_asian_markets(self, sport: AsianSport, league: Optional[AsianLeague]) -> List[Dict[str, Any]]:
        """Generate mock Asian sports markets"""
        
        mock_events = {
            AsianSport.ASIAN_FOOTBALL: [
                {
                    "market_id": "j_league_001",
                    "sport": AsianSport.ASIAN_FOOTBALL,
                    "league": AsianLeague.J_LEAGUE,
                    "event_name": "Tokyo FC vs Yokohama Marinos",
                    "home_team": "Tokyo FC",
                    "away_team": "Yokohama Marinos",
                    "handicap_type": HandicapType.ASIAN_HANDICAP,
                    "handicap_line": -0.5,
                    "home_odds": 1.85,
                    "away_odds": 1.95,
                    "event_time": (datetime.now() + timedelta(hours=8)).isoformat(),
                    "home_strength": 0.6,
                    "away_strength": 0.4
                },
                {
                    "market_id": "k_league_001", 
                    "sport": AsianSport.ASIAN_FOOTBALL,
                    "league": AsianLeague.K_LEAGUE,
                    "event_name": "Seoul FC vs Busan IPark",
                    "home_team": "Seoul FC",
                    "away_team": "Busan IPark",
                    "handicap_type": HandicapType.QUARTER_HANDICAP,
                    "handicap_line": -0.25,
                    "home_odds": 1.90,
                    "away_odds": 1.90,
                    "event_time": (datetime.now() + timedelta(hours=12)).isoformat(),
                    "home_strength": 0.55,
                    "away_strength": 0.45
                }
            ],
            AsianSport.CRICKET: [
                {
                    "market_id": "ipl_001",
                    "sport": AsianSport.CRICKET,
                    "league": AsianLeague.IPL,
                    "event_name": "Mumbai Indians vs Chennai Super Kings",
                    "home_team": "Mumbai Indians",
                    "away_team": "Chennai Super Kings",
                    "handicap_type": HandicapType.ASIAN_HANDICAP,
                    "handicap_line": 0,
                    "home_odds": 1.95,
                    "away_odds": 1.85,
                    "total_line": 170.5,
                    "over_odds": 1.90,
                    "under_odds": 1.90,
                    "event_time": (datetime.now() + timedelta(hours=16)).isoformat(),
                    "home_strength": 0.48,
                    "away_strength": 0.52
                }
            ],
            AsianSport.BADMINTON: [
                {
                    "market_id": "bwf_001",
                    "sport": AsianSport.BADMINTON,
                    "league": AsianLeague.BWF_SUPER_SERIES,
                    "event_name": "Chen Long vs Kento Momota",
                    "home_team": "Chen Long",
                    "away_team": "Kento Momota", 
                    "handicap_type": HandicapType.ASIAN_HANDICAP,
                    "handicap_line": 0.5,
                    "home_odds": 2.10,
                    "away_odds": 1.75,
                    "event_time": (datetime.now() + timedelta(hours=6)).isoformat(),
                    "home_strength": 0.42,
                    "away_strength": 0.58
                }
            ]
        }
        
        events = mock_events.get(sport, [])
        
        # Filter by league if specified
        if league:
            events = [e for e in events if e.get("league") == league]
        
        return events

class AsianLocalizationManager:
    """Handle multi-language and cultural localization for Asian markets"""
    
    def __init__(self):
        self.supported_languages = ["en", "zh", "ja", "ko", "th", "hi"]
        self.currency_mappings = {
            "en": "USD",
            "zh": "CNY", 
            "ja": "JPY",
            "ko": "KRW",
            "th": "THB",
            "hi": "INR"
        }
        
        # Load translations (in real app, from database/files)
        self.translations = self._load_translations()
    
    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """Load translation dictionaries"""
        return {
            "en": {
                "home_team": "Home Team",
                "away_team": "Away Team", 
                "handicap": "Handicap",
                "odds": "Odds",
                "total": "Total",
                "over": "Over",
                "under": "Under"
            },
            "zh": {
                "home_team": "主队",
                "away_team": "客队",
                "handicap": "让球",
                "odds": "赔率",
                "total": "总数",
                "over": "大",
                "under": "小"
            },
            "ja": {
                "home_team": "ホームチーム",
                "away_team": "アウェイチーム",
                "handicap": "ハンディキャップ",
                "odds": "オッズ",
                "total": "トータル",
                "over": "オーバー",
                "under": "アンダー"
            },
            "ko": {
                "home_team": "홈팀",
                "away_team": "원정팀",
                "handicap": "핸디캡",
                "odds": "배당률",
                "total": "총합",
                "over": "오버",
                "under": "언더"
            }
        }
    
    def localize_market(self, market: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Localize market data for specific language"""
        if language not in self.supported_languages:
            language = "en"
        
        translations = self.translations.get(language, self.translations["en"])
        localized_market = market.copy()
        
        # Add localized fields
        localized_market["localization"] = {
            "language": language,
            "currency": self.currency_mappings.get(language, "USD"),
            "translations": translations,
            "formatted_odds": self._format_odds_for_region(market, language)
        }
        
        return localized_market
    
    def _format_odds_for_region(self, market: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Format odds according to regional preferences"""
        formatted_odds = {}
        
        if language in ["zh", "ko", "ja"]:
            # Asian decimal format
            if "home_odds" in market:
                formatted_odds["home_odds_decimal"] = f"{market['home_odds']:.2f}"
            if "away_odds" in market:
                formatted_odds["away_odds_decimal"] = f"{market['away_odds']:.2f}"
        else:
            # Standard decimal format
            if "home_odds" in market:
                formatted_odds["home_odds"] = market["home_odds"]
            if "away_odds" in market:
                formatted_odds["away_odds"] = market["away_odds"]
        
        return formatted_odds

# Initialize components
asian_handicap_engine = None
asian_sports_provider = None
localization_manager = AsianLocalizationManager()

@router.on_event("startup")
async def startup_asian_markets():
    global asian_handicap_engine, asian_sports_provider
    logger.info("Asian markets system initialized")

@router.get("/handicaps")
async def get_asian_handicaps(
    sport: AsianSport,
    league: Optional[AsianLeague] = None,
    language: str = Query("en", description="Language code (en, zh, ja, ko, th, hi)")
):
    """Get Asian handicap markets with localization"""
    try:
        if not asian_sports_provider:
            # Mock provider for demonstration
            from unittest.mock import AsyncMock
            asian_sports_provider = AsyncMock()
            
            # Mock markets
            mock_markets = [
                AsianMarket(
                    market_id="mock_asian_001",
                    sport=sport,
                    league=league or AsianLeague.J_LEAGUE,
                    event_name="Mock Asian Event",
                    event_time=datetime.now() + timedelta(hours=8),
                    home_team="Team A",
                    away_team="Team B",
                    handicap_type=HandicapType.ASIAN_HANDICAP,
                    handicap_line=-0.5,
                    home_odds=1.85,
                    away_odds=1.95
                )
            ]
            
            asian_sports_provider.get_asian_markets = AsyncMock(return_value=mock_markets)
        
        markets = await asian_sports_provider.get_asian_markets(sport, league)
        
        # Localize markets
        localized_markets = []
        for market in markets:
            market_dict = market.dict()
            localized_market = localization_manager.localize_market(market_dict, language)
            localized_markets.append(localized_market)
        
        return {
            "success": True,
            "sport": sport,
            "league": league,
            "language": language,
            "markets_count": len(localized_markets),
            "markets": localized_markets,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get Asian handicaps: {e}")
        raise HTTPException(status_code=500, detail=f"Asian handicaps failed: {str(e)}")

@router.get("/live-asian")
async def get_live_asian_markets(
    sport: Optional[AsianSport] = None,
    language: str = Query("en", description="Language code")
):
    """Get live Asian sports markets"""
    try:
        # Mock live markets
        live_markets = [
            {
                "market_id": "live_asian_001",
                "sport": AsianSport.ASIAN_FOOTBALL,
                "league": AsianLeague.J_LEAGUE,
                "event_name": "Tokyo FC vs Yokohama",
                "home_team": "Tokyo FC",
                "away_team": "Yokohama",
                "live_score": {
                    "home": 1,
                    "away": 0,
                    "minute": 67,
                    "status": "2nd_half"
                },
                "handicap_type": HandicapType.ASIAN_HANDICAP,
                "handicap_line": -1.0,
                "home_odds": 2.15,
                "away_odds": 1.68,
                "event_time": datetime.now().isoformat()
            }
        ]
        
        if sport:
            live_markets = [m for m in live_markets if m["sport"] == sport]
        
        # Localize markets
        localized_markets = []
        for market in live_markets:
            localized_market = localization_manager.localize_market(market, language)
            localized_markets.append(localized_market)
        
        return {
            "success": True,
            "live_markets_count": len(localized_markets),
            "markets": localized_markets,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get live Asian markets: {e}")
        raise HTTPException(status_code=500, detail=f"Live markets failed: {str(e)}")

@router.get("/leagues")
async def get_asian_leagues(
    sport: Optional[AsianSport] = None,
    language: str = Query("en", description="Language code")
):
    """Get available Asian leagues and competitions"""
    try:
        # League information with localization
        leagues_data = {
            AsianSport.ASIAN_FOOTBALL: {
                AsianLeague.J_LEAGUE: {
                    "name": "J-League Division 1",
                    "country": "Japan",
                    "teams": 18,
                    "season": "2024"
                },
                AsianLeague.K_LEAGUE: {
                    "name": "K League 1",
                    "country": "South Korea", 
                    "teams": 12,
                    "season": "2024"
                },
                AsianLeague.CHINESE_SUPER: {
                    "name": "Chinese Super League",
                    "country": "China",
                    "teams": 16,
                    "season": "2024"
                }
            },
            AsianSport.CRICKET: {
                AsianLeague.IPL: {
                    "name": "Indian Premier League",
                    "country": "India",
                    "teams": 10,
                    "season": "2024"
                },
                AsianLeague.BPL: {
                    "name": "Bangladesh Premier League",
                    "country": "Bangladesh",
                    "teams": 8,
                    "season": "2024"
                }
            }
        }
        
        if sport:
            leagues_info = leagues_data.get(sport, {})
        else:
            leagues_info = leagues_data
        
        return {
            "success": True,
            "sport_filter": sport,
            "language": language,
            "leagues": leagues_info
        }
        
    except Exception as e:
        logger.error(f"Failed to get leagues: {e}")
        raise HTTPException(status_code=500, detail=f"Leagues fetch failed: {str(e)}")

@router.post("/calculate-handicap")
async def calculate_handicap_analysis(
    home_strength: float = Query(..., ge=0, le=1, description="Home team strength (0-1)"),
    away_strength: float = Query(..., ge=0, le=1, description="Away team strength (0-1)"),
    venue_advantage: float = Query(0.1, ge=0, le=0.3, description="Home venue advantage")
):
    """Calculate detailed handicap analysis"""
    try:
        if not asian_handicap_engine:
            # Mock engine for demonstration
            asian_handicap_engine = AsianHandicapEngine(None)
        
        analysis = asian_handicap_engine.calculate_asian_handicap(
            home_strength, away_strength, venue_advantage
        )
        
        return {
            "success": True,
            "input_parameters": {
                "home_strength": home_strength,
                "away_strength": away_strength,
                "venue_advantage": venue_advantage
            },
            "analysis": analysis,
            "calculated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Handicap calculation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Handicap calculation failed: {str(e)}")

@router.get("/cultural-preferences/{region}")
async def get_cultural_preferences(region: str):
    """Get cultural betting preferences for different Asian regions"""
    try:
        cultural_data = {
            "japan": {
                "preferred_sports": ["baseball", "soccer", "sumo"],
                "betting_culture": "conservative",
                "popular_bet_types": ["moneyline", "totals"],
                "currency": "JPY",
                "language": "ja",
                "timezone": "JST"
            },
            "south_korea": {
                "preferred_sports": ["soccer", "baseball", "esports"],
                "betting_culture": "tech_savvy",
                "popular_bet_types": ["handicap", "live_betting"],
                "currency": "KRW", 
                "language": "ko",
                "timezone": "KST"
            },
            "china": {
                "preferred_sports": ["soccer", "basketball", "table_tennis"],
                "betting_culture": "high_volume",
                "popular_bet_types": ["asian_handicap", "totals"],
                "currency": "CNY",
                "language": "zh",
                "timezone": "CST"
            },
            "thailand": {
                "preferred_sports": ["soccer", "muay_thai", "sepak_takraw"],
                "betting_culture": "social",
                "popular_bet_types": ["moneyline", "props"],
                "currency": "THB",
                "language": "th", 
                "timezone": "ICT"
            },
            "india": {
                "preferred_sports": ["cricket", "kabaddi", "soccer"],
                "betting_culture": "cricket_focused",
                "popular_bet_types": ["match_winner", "tournament_specials"],
                "currency": "INR",
                "language": "hi",
                "timezone": "IST"
            }
        }
        
        region_data = cultural_data.get(region.lower())
        if not region_data:
            raise HTTPException(status_code=404, detail="Region not found")
        
        return {
            "success": True,
            "region": region,
            "cultural_preferences": region_data,
            "localization_support": True
        }
        
    except Exception as e:
        logger.error(f"Failed to get cultural preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Cultural preferences failed: {str(e)}")

@router.get("/quarter-handicap-explained")
async def explain_quarter_handicap():
    """Educational endpoint explaining quarter handicap betting"""
    try:
        explanation = {
            "concept": "Quarter handicap splits your bet between two handicap lines",
            "examples": {
                "-0.25": {
                    "split": "Half on 0 handicap, half on -0.5 handicap",
                    "outcomes": {
                        "win_by_1+": "Full win",
                        "draw": "Half refund, half loss",
                        "lose": "Full loss"
                    }
                },
                "-0.75": {
                    "split": "Half on -0.5 handicap, half on -1 handicap", 
                    "outcomes": {
                        "win_by_2+": "Full win",
                        "win_by_1": "Half win, half refund",
                        "draw_or_lose": "Full loss"
                    }
                }
            },
            "advantages": [
                "Reduces risk compared to full handicap",
                "Better odds than double chance",
                "Popular in Asian markets"
            ],
            "calculation_example": {
                "bet_amount": 100,
                "handicap": -0.25,
                "odds": 1.90,
                "scenario_1": {
                    "result": "Win by 1 goal",
                    "outcome": "Full win",
                    "payout": 190
                },
                "scenario_2": {
                    "result": "Draw",
                    "outcome": "Half refund, half loss",
                    "payout": 50
                }
            }
        }
        
        return {
            "success": True,
            "explanation": explanation
        }
        
    except Exception as e:
        logger.error(f"Failed to get explanation: {e}")
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")