# 🚀 OMEGA PRO AI - Quick Start Guide

Get OMEGA PRO AI running in under 5 minutes!

## 📦 What's Included

✅ **Complete FastAPI Application** with async support  
✅ **Lottery Predictions** with advanced AI models  
✅ **Sports Betting System** with live odds & edge analysis  
✅ **Asian Markets** with handicap calculations & localization  
✅ **Conversational AI** with Claude integration  
✅ **Crypto Payments** (Bitcoin, Ethereum, USDT, USDC)  
✅ **KYC Verification** with document & biometric validation  
✅ **Docker Deployment** ready for production  
✅ **Akash Network** deployment configuration  
✅ **Comprehensive Tests** and documentation  

---

## ⚡ 30-Second Setup

### Option 1: Docker (Recommended)
```bash
# 1. Navigate to the package
cd OMEGA_COMPLETE

# 2. Start the deployment script
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# 3. Select option 1 (Full Stack)
# 4. Wait 30 seconds for startup
# 5. Visit http://localhost:8000
```

### Option 2: Manual Python Setup
```bash
# 1. Setup environment
cd OMEGA_COMPLETE
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start Redis (required)
redis-server &

# 4. Start the application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5. Visit http://localhost:8000
```

---

## 🧪 Test the System

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Generate Lottery Predictions
```bash
curl -X POST http://localhost:8000/entregar_series \
  -H "Content-Type: application/json" \
  -d '{"lottery_type": "kabala", "series_count": 3}'
```

### 3. Get Sports Odds
```bash
curl http://localhost:8000/sports/odds?sport=football
```

### 4. Chat with AI
```bash
curl -X POST http://localhost:8000/chat/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do lottery predictions work?", "language": "en"}'
```

### 5. Asian Markets
```bash
curl http://localhost:8000/asian/handicaps?sport=asian_football&language=zh
```

---

## 🌐 Access Points

After deployment, these services will be available:

| Service | URL | Description |
|---------|-----|-------------|
| **Main API** | http://localhost:8000 | Core OMEGA system |
| **API Documentation** | http://localhost:8000/docs | Interactive API docs |
| **Health Check** | http://localhost:8000/health | System status |
| **Asian Markets** | http://localhost:8001 | Specialized Asian betting |
| **Grafana Dashboard** | http://localhost:3000 | Monitoring (admin/admin123) |
| **Prometheus Metrics** | http://localhost:9090 | System metrics |

---

## 🔧 Configuration

### Environment Setup
```bash
# Copy and customize environment variables
cp .env.example .env
nano .env  # Edit with your API keys
```

### Essential API Keys
```env
# Required for full functionality
CLAUDE_API_KEY=your_claude_api_key
REDIS_URL=redis://localhost:6379

# Optional but recommended
STRIPE_SECRET_KEY=sk_test_your_stripe_key
COINBASE_API_KEY=your_coinbase_key
ODDS_API_KEY=your_odds_api_key
```

---

## 🎯 Key Features Demo

### 🎲 Lottery Predictions
```python
import requests

response = requests.post('http://localhost:8000/entregar_series', json={
    "lottery_type": "kabala",
    "series_count": 5,
    "filters": {
        "exclude_numbers": [13],
        "include_numbers": [7, 21]
    }
})

predictions = response.json()
print(f"Generated {len(predictions['data']['series'])} series")
print(f"Average confidence: {predictions['data']['analysis']['prediction_quality']['avg_confidence']}")
```

### 🏀 Sports Betting Analysis
```python
# Get live odds with edge analysis
odds_response = requests.get('http://localhost:8000/sports/odds?sport=football')
markets = odds_response.json()['markets']

for market in markets[:3]:
    edge = market['edge_analysis']['edge_percentage']
    print(f"{market['event_name']}: {edge}% edge")

# Get AI betting picks
picks_response = requests.get('http://localhost:8000/sports/picks?min_edge=2.0')
picks = picks_response.json()['picks']

for pick in picks:
    print(f"Recommended: {pick['recommended_bet']} (EV: {pick['expected_value']}%)")
```

### 🌏 Asian Markets
```python
# Get Asian handicap markets
asian_response = requests.get('http://localhost:8000/asian/handicaps?sport=asian_football&language=zh')
markets = asian_response.json()['markets']

for market in markets:
    print(f"{market['event_name']}: {market['handicap_line']}")
    print(f"Localized: {market['localization']['language']}")
```

### 🤖 Conversational AI
```python
# Chat with Claude AI
chat_response = requests.post('http://localhost:8000/chat/chat', json={
    "message": "Explain how Asian handicaps work",
    "session_id": "demo_session",
    "language": "en"
})

ai_response = chat_response.json()['response']
print(f"AI: {ai_response['response']}")
print(f"Suggested actions: {ai_response['suggested_actions']}")
```

### 💳 Crypto Payments
```python
# Create Bitcoin payment
payment_response = requests.post('http://localhost:8000/payments/create', json={
    "user_id": "demo_user",
    "amount": 100.0,
    "currency": "USD",
    "payment_method": "bitcoin",
    "description": "OMEGA PRO subscription"
})

payment = payment_response.json()['payment']
print(f"Payment ID: {payment['payment_id']}")
print(f"Send {payment['amount']} BTC to: {payment['crypto_address']}")
```

---

## 🔍 Monitoring & Debugging

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f omega-api

# Real-time application logs
tail -f logs/app.log
```

### Check Service Status
```bash
# Docker services
docker-compose ps

# Health checks
curl http://localhost:8000/health
curl http://localhost:8001/health  # Asian markets
```

### Performance Monitoring
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **API Metrics**: http://localhost:8000/metrics

---

## 🚀 Deployment Options

### Local Development
```bash
# Start in development mode with hot reload
docker-compose -f deploy/docker-compose.yml -f deploy/docker-compose.dev.yml up -d
```

### Production Deployment
```bash
# Full production stack
docker-compose -f deploy/docker-compose.yml up -d

# With SSL and reverse proxy
docker-compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml up -d
```

### Asian Markets Only
```bash
# Specialized deployment for Asian markets
docker-compose -f deploy/docker-compose.asian.yml up -d
```

### Akash Network (Decentralized Cloud)
```bash
# Deploy to Akash Network
akash tx deployment create deploy/akash-deploy.yaml --from mykey
```

---

## 🧪 Testing

### Run Test Suite
```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test category
pytest tests/test_main.py -v
```

### Load Testing
```bash
# Install load testing tools
pip install locust

# Run load tests
locust -f tests/load/locustfile.py --host http://localhost:8000
```

---

## 🔧 Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9
```

**Redis Connection Error:**
```bash
# Start Redis manually
redis-server --daemonize yes

# Or use Docker
docker run -d -p 6379:6379 redis:alpine
```

**Docker Issues:**
```bash
# Clean rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

**Permission Issues:**
```bash
# Fix permissions
chmod +x scripts/deploy.sh
sudo chown -R $USER:$USER data/ logs/
```

---

## 📚 Next Steps

1. **Customize Configuration**: Edit `.env` with your API keys
2. **Explore API Documentation**: Visit http://localhost:8000/docs
3. **Set Up Monitoring**: Configure Grafana dashboards
4. **Add Your Data**: Import historical lottery data
5. **Integrate Payments**: Configure cryptocurrency wallets
6. **Deploy to Production**: Use Docker Compose or Akash Network

---

## 💡 Tips for Success

### Performance Optimization
- Use Redis for caching frequently accessed predictions
- Configure connection pooling for databases
- Enable Prometheus monitoring for performance insights

### Security Best Practices
- Use HTTPS in production
- Rotate API keys regularly
- Enable rate limiting
- Configure proper CORS settings

### Scaling
- Use Docker Swarm or Kubernetes for horizontal scaling
- Configure load balancing with Nginx
- Separate read/write database operations

---

## 📞 Support

- **Documentation**: Check `/docs` directory
- **API Reference**: http://localhost:8000/docs
- **Issues**: Create GitHub issues for bugs
- **Community**: Join our Discord server

---

**🎉 You're now ready to use OMEGA PRO AI!**

*Generate lottery predictions, analyze sports bets, explore Asian markets, and chat with AI - all powered by cutting-edge machine learning and deployed in minutes.*