# OMEGA PRO AI - API Documentation

## Base URL
```
Production: https://api.omega-pro-ai.com
Development: http://localhost:8000
```

## Authentication

### JWT Authentication (Optional)
```http
Authorization: Bearer your_jwt_token
```

### API Key Authentication (Optional)
```http
X-API-Key: your_api_key
```

---

## 🎲 Lottery Predictions API

### Generate Series Predictions
Generate AI-powered lottery number predictions.

```http
POST /entregar_series
```

**Request Body:**
```json
{
    "lottery_type": "kabala",
    "series_count": 5,
    "filters": {
        "exclude_numbers": [13, 666],
        "include_numbers": [7, 21],
        "odd_even_ratio": 0.5,
        "sum_range": [90, 120]
    },
    "preferences": {
        "prediction_mode": "balanced",
        "confidence_threshold": 0.7
    }
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "series": [
            {
                "numbers": [1, 7, 14, 21, 28, 35],
                "confidence": 0.85,
                "pattern_score": 0.78,
                "frequency_score": 0.82,
                "statistical_score": 0.79,
                "meta_data": {
                    "generation_method": "ensemble_ml",
                    "model_version": "4.0.1"
                }
            }
        ],
        "analysis": {
            "prediction_quality": {
                "avg_confidence": 0.83,
                "confidence_range": [0.75, 0.89]
            },
            "number_analysis": {
                "hot_numbers": [7, 14, 21],
                "cold_numbers": [2, 9, 33]
            }
        },
        "recommendations": [
            "High confidence predictions - consider playing multiple series",
            "Strong pattern matching detected"
        ]
    },
    "timestamp": "2024-08-12T10:30:00Z"
}
```

---

## 🏀 Sports Betting API

### Get Live Odds
Retrieve live odds from multiple bookmakers with edge analysis.

```http
GET /sports/odds?sport={sport}&region={region}&bet_type={bet_type}
```

**Parameters:**
- `sport` (required): football, basketball, tennis, soccer, baseball, hockey, cricket, badminton, esports
- `region` (optional): us, uk, eu (default: us)
- `bet_type` (optional): moneyline, spread, total, prop, live, futures

**Response:**
```json
{
    "success": true,
    "sport": "football",
    "region": "us",
    "markets_count": 25,
    "markets": [
        {
            "market_id": "nfl_001",
            "sport": "football",
            "event_name": "Chiefs vs Bills",
            "team_home": "Kansas City Chiefs",
            "team_away": "Buffalo Bills",
            "event_time": "2024-08-13T20:00:00Z",
            "odds_data": [
                {
                    "bookmaker": "draftkings",
                    "odds": 1.95,
                    "probability": 0.513,
                    "last_updated": "2024-08-12T10:25:00Z"
                }
            ],
            "best_odds": {
                "bookmaker": "pinnacle",
                "odds": 2.05,
                "advantage": 0.10
            },
            "edge_analysis": {
                "edge_percentage": 2.5,
                "confidence": 0.75,
                "recommended_stake": 0.02
            }
        }
    ],
    "last_updated": "2024-08-12T10:30:00Z"
}
```

### Get AI Betting Picks
Get AI-generated betting recommendations based on edge analysis.

```http
GET /sports/picks?sport={sport}&min_edge={min_edge}&min_confidence={min_confidence}
```

**Response:**
```json
{
    "success": true,
    "picks_count": 3,
    "picks": [
        {
            "market_id": "pick_001",
            "recommended_bet": "Kansas City Chiefs ML",
            "stake_size": 2.5,
            "expected_value": 3.2,
            "confidence": 0.78,
            "risk_level": "medium",
            "reasoning": [
                "Positive edge of 3.2%",
                "High confidence level: 0.78",
                "Based on multi-bookmaker odds analysis"
            ]
        }
    ],
    "generated_at": "2024-08-12T10:30:00Z"
}
```

### Get Betting Analytics
Retrieve comprehensive betting performance analytics.

```http
GET /sports/analytics/{user_id}?timeframe={days}
```

**Response:**
```json
{
    "success": true,
    "user_id": "user_123",
    "analytics": {
        "timeframe_days": 30,
        "total_bets": 25,
        "total_stakes": 1250.00,
        "total_returns": 1387.50,
        "profit_loss": 137.50,
        "roi_percentage": 11.0,
        "win_rate": 48.0,
        "sport_breakdown": {
            "football": {"roi": 15.5, "win_rate": 52.0},
            "basketball": {"roi": 8.2, "win_rate": 44.0}
        },
        "recommendations": [
            "Great ROI! Keep up the current strategy",
            "Consider increasing stakes on high-confidence picks"
        ]
    }
}
```

---

## 🌏 Asian Markets API

### Get Asian Handicap Markets
Retrieve Asian handicap betting markets with localization.

```http
GET /asian/handicaps?sport={sport}&league={league}&language={language}
```

**Parameters:**
- `sport`: asian_football, cricket, badminton, table_tennis, kabaddi, esports_mobile
- `league`: j_league, k_league, chinese_super, ipl, bpl, etc.
- `language`: en, zh, ja, ko, th, hi

**Response:**
```json
{
    "success": true,
    "sport": "asian_football",
    "league": "j_league",
    "language": "zh",
    "markets": [
        {
            "market_id": "j_league_001",
            "sport": "asian_football",
            "event_name": "Tokyo FC vs Yokohama Marinos",
            "handicap_type": "asian_handicap",
            "handicap_line": -0.5,
            "home_odds": 1.85,
            "away_odds": 1.95,
            "localization": {
                "language": "zh",
                "currency": "CNY",
                "translations": {
                    "home_team": "主队",
                    "away_team": "客队",
                    "handicap": "让球"
                }
            }
        }
    ]
}
```

### Calculate Handicap Analysis
Generate detailed handicap analysis and recommendations.

```http
POST /asian/calculate-handicap?home_strength={strength}&away_strength={strength}&venue_advantage={advantage}
```

**Response:**
```json
{
    "success": true,
    "analysis": {
        "handicap_analysis": {
            "main_line": {
                "handicap": -0.5,
                "home_odds": 1.85,
                "away_odds": 1.95
            },
            "quarter_lines": [
                {
                    "handicap": -0.25,
                    "home_odds": 1.90,
                    "away_odds": 1.90
                }
            ]
        },
        "recommended_line": -0.5,
        "confidence": 0.78,
        "edge_opportunities": [
            {
                "handicap": -0.25,
                "recommended_bet": "away",
                "edge_percentage": 2.8
            }
        ]
    }
}
```

---

## 🤖 Conversational AI API

### Text Chat
Interact with Claude AI for lottery predictions, sports betting, and general assistance.

```http
POST /chat/chat
```

**Request Body:**
```json
{
    "message": "How do lottery predictions work?",
    "session_id": "session_123",
    "mode": "text",
    "language": "en",
    "context": {
        "user_preferences": {"topic": "lottery_predictions"}
    }
}
```

**Response:**
```json
{
    "success": true,
    "response": {
        "response": "OMEGA PRO AI uses advanced machine learning models including transformer networks to analyze historical lottery data...",
        "session_id": "session_123",
        "suggested_actions": [
            "Generate new lottery predictions",
            "Analyze recent results",
            "View prediction history"
        ],
        "follow_up_questions": [
            "Would you like to see the confidence scores for these predictions?",
            "Shall I explain how our AI calculates these numbers?"
        ],
        "topic": "lottery_predictions",
        "confidence": 0.92
    }
}
```

### Voice Chat
Submit audio for speech-to-text processing and receive AI response.

```http
POST /chat/voice-chat
Content-Type: multipart/form-data
```

**Form Data:**
- `audio_file`: Audio file (WAV, MP3, etc.)
- `language`: Language code (en, zh, ja, ko, th)
- `session_id`: Optional session ID

### Get Chat History
Retrieve conversation history for a session.

```http
GET /chat/history/{session_id}?limit={limit}
```

**Response:**
```json
{
    "success": true,
    "session_id": "session_123",
    "message_count": 10,
    "history": [
        {
            "message_type": "user",
            "content": "How do lottery predictions work?",
            "timestamp": "2024-08-12T10:25:00Z",
            "topic": "lottery_predictions"
        },
        {
            "message_type": "assistant",
            "content": "OMEGA PRO AI uses advanced machine learning...",
            "timestamp": "2024-08-12T10:25:05Z",
            "topic": "lottery_predictions"
        }
    ]
}
```

---

## 💳 Payment System API

### Get Payment Methods
Retrieve available payment methods for user's region.

```http
GET /payments/methods?user_region={region}
```

**Response:**
```json
{
    "success": true,
    "available_methods": {
        "bitcoin": {
            "name": "Bitcoin",
            "type": "cryptocurrency",
            "processing_time": "10-30 minutes",
            "fees": "Network fees apply",
            "limits": {"min": 10, "max": 100000}
        },
        "credit_card": {
            "name": "Credit/Debit Card",
            "type": "traditional",
            "processing_time": "Instant",
            "fees": "2.9% + $0.30",
            "limits": {"min": 1, "max": 10000}
        }
    },
    "total_methods": 5
}
```

### Create Payment
Create a new payment transaction.

```http
POST /payments/create
```

**Request Body:**
```json
{
    "user_id": "user_123",
    "amount": 100.0,
    "currency": "USD",
    "payment_method": "bitcoin",
    "description": "OMEGA PRO subscription",
    "return_url": "https://yourapp.com/payment/success",
    "webhook_url": "https://yourapp.com/webhook/payment"
}
```

**Response:**
```json
{
    "success": true,
    "payment": {
        "payment_id": "crypto_abc123def456",
        "status": "pending",
        "amount": 0.002,
        "currency": "BTC",
        "payment_method": "bitcoin",
        "crypto_address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        "qr_code": "bitcoin:bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh?amount=0.002",
        "expires_at": "2024-08-12T11:00:00Z",
        "instructions": {
            "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
            "amount": 0.002,
            "network": "Bitcoin Mainnet",
            "confirmation_required": 3,
            "warning": "Double-check address - Bitcoin transactions are irreversible"
        }
    }
}
```

### Get Payment Status
Check the status of a payment transaction.

```http
GET /payments/status/{payment_id}
```

**Response:**
```json
{
    "success": true,
    "payment": {
        "payment_id": "crypto_abc123def456",
        "status": "completed",
        "amount": 100.0,
        "currency": "USD",
        "payment_method": "bitcoin",
        "confirmations": 3,
        "required_confirmations": 3,
        "confirmed_at": "2024-08-12T10:45:00Z"
    }
}
```

---

## 🔐 KYC Verification API

### Submit KYC Application
Submit identity verification documents and information.

```http
POST /kyc/submit
Content-Type: multipart/form-data
```

**Form Data:**
- `kyc_data`: JSON with user information
- `document_front`: Document front image
- `document_back`: Document back image (optional)
- `selfie`: Selfie photo

**KYC Data JSON:**
```json
{
    "user_id": "user_123",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1990-01-01",
    "nationality": "US",
    "address": "123 Main St",
    "city": "New York",
    "postal_code": "10001",
    "country": "US",
    "phone": "+1234567890",
    "document_type": "passport",
    "document_number": "P123456789"
}
```

**Response:**
```json
{
    "success": true,
    "application_id": "kyc_abc123def456",
    "status": "in_review",
    "estimated_processing_time": "2-5 business days",
    "next_steps": [
        "Document verification in progress",
        "Biometric verification in progress",
        "Final review pending"
    ]
}
```

### Get KYC Status
Check the status of a KYC application.

```http
GET /kyc/status/{application_id}
```

**Response:**
```json
{
    "application_id": "kyc_abc123def456",
    "status": "approved",
    "progress": 100,
    "current_step": "Verification complete",
    "submitted_at": "2024-08-10T09:00:00Z",
    "approved_at": "2024-08-12T10:30:00Z",
    "required_actions": []
}
```

### Verify Identity
Verify user identity against KYC data.

```http
POST /kyc/verify?user_id={user_id}&application_id={application_id}
```

**Response:**
```json
{
    "verified": true,
    "confidence_score": 0.95,
    "verification_level": "full_kyc",
    "verified_at": "2024-08-12T10:30:00Z",
    "valid_until": "2025-08-12T10:30:00Z",
    "verified_attributes": [
        "identity",
        "address",
        "document_authenticity",
        "biometric_match"
    ]
}
```

---

## 📊 Health & System API

### Health Check
Check system health and status.

```http
GET /health
```

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2024-08-12T10:30:00Z",
    "systems": {
        "redis": "connected",
        "omega_flow": "initialized",
        "sports_flow": "initialized",
        "conversation_manager": "initialized"
    }
}
```

### System Information
Get system information and available features.

```http
GET /
```

**Response:**
```json
{
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
```

---

## 🔄 WebSocket API

### Real-time Chat
Connect to WebSocket for real-time conversational AI.

```javascript
const ws = new WebSocket('ws://localhost:8000/chat/ws/session_123');

// Send message
ws.send(JSON.stringify({
    message: "Hello, OMEGA!",
    mode: "text",
    language: "en"
}));

// Receive response
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('AI Response:', data.response);
};
```

---

## 📊 Rate Limits

- **General API**: 100 requests per minute per IP
- **Chat API**: 50 requests per minute per session
- **Payment API**: 20 requests per minute per user
- **KYC API**: 10 requests per minute per user

Rate limit headers:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1692696000
```

---

## ❌ Error Responses

### Standard Error Format
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": {
            "field": "lottery_type",
            "issue": "Must be one of: kabala, powerball, mega_millions"
        }
    },
    "timestamp": "2024-08-12T10:30:00Z",
    "request_id": "req_abc123def456"
}
```

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request (validation error)
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Too Many Requests
- `500` - Internal Server Error
- `503` - Service Unavailable

---

## 🔧 SDK Examples

### Python SDK
```python
import requests

class OmegaProAI:
    def __init__(self, api_key=None, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key} if api_key else {}
    
    def generate_lottery_series(self, lottery_type, series_count=5):
        response = requests.post(
            f"{self.base_url}/entregar_series",
            json={"lottery_type": lottery_type, "series_count": series_count},
            headers=self.headers
        )
        return response.json()
    
    def get_sports_odds(self, sport, region="us"):
        response = requests.get(
            f"{self.base_url}/sports/odds",
            params={"sport": sport, "region": region},
            headers=self.headers
        )
        return response.json()

# Usage
omega = OmegaProAI()
predictions = omega.generate_lottery_series("kabala", 3)
odds = omega.get_sports_odds("football")
```

### JavaScript SDK
```javascript
class OmegaProAI {
    constructor(apiKey = null, baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.headers = apiKey ? { 'X-API-Key': apiKey } : {};
    }
    
    async generateLotterySeries(lotteryType, seriesCount = 5) {
        const response = await fetch(`${this.baseUrl}/entregar_series`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...this.headers },
            body: JSON.stringify({ lottery_type: lotteryType, series_count: seriesCount })
        });
        return response.json();
    }
    
    async getSportsOdds(sport, region = 'us') {
        const response = await fetch(`${this.baseUrl}/sports/odds?sport=${sport}&region=${region}`, {
            headers: this.headers
        });
        return response.json();
    }
}

// Usage
const omega = new OmegaProAI();
const predictions = await omega.generateLotterySeries('kabala', 3);
const odds = await omega.getSportsOdds('football');
```

---

*For more examples and detailed integration guides, visit the [Developer Portal](https://developers.omega-pro-ai.com)*