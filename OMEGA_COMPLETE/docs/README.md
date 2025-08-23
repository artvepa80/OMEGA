# OMEGA PRO AI v4.0 - Complete Package

## 🚀 Advanced AI System for Lottery Predictions, Sports Betting & Asian Markets

OMEGA PRO AI is a comprehensive platform combining cutting-edge artificial intelligence with lottery predictions, sports betting analysis, Asian market specialization, and conversational AI capabilities.

---

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

---

## ✨ Features

### 🎲 BASE MVP
- **FastAPI Backend** with async support
- **Redis** caching and session management
- **Rate limiting** and security middleware
- **Docker** containerization
- **Production-ready** deployment

### 🏀 Sports Betting System
- **Live odds tracking** from multiple bookmakers
- **Asian handicap** support with advanced calculations
- **Edge detection** and value betting
- **ROI analytics** and performance tracking
- **Live scores** and real-time updates

### 🌏 Asian Markets Expansion
- **Multi-language support** (English, Chinese, Japanese, Korean, Thai, Hindi)
- **Cultural localization** for different regions
- **Asian sports focus** (Cricket, Badminton, J-League, K-League)
- **Quarter handicap** and specialized betting types
- **Regional payment methods**

### 🤖 Conversational AI
- **Claude AI integration** for natural language processing
- **Voice support** (Speech-to-Text & Text-to-Speech)
- **Multi-language conversations**
- **Context-aware responses**
- **WebSocket support** for real-time chat

### 💳 Payment System
- **Cryptocurrency support** (Bitcoin, Ethereum, USDT, USDC)
- **Traditional payments** (Credit cards, PayPal, Bank transfers)
- **Asian payment methods** (Alipay, WeChat Pay)
- **Real-time payment tracking**
- **Automated refund processing**

### 🔐 Security & Compliance
- **KYC verification** with document validation
- **Biometric verification** with liveness detection
- **Multi-factor authentication**
- **Compliance reporting**
- **Anti-fraud measures**

---

## 🏗 Architecture

```
OMEGA_COMPLETE/
├── app/                     # FastAPI application
│   ├── main.py             # Main application entry
│   ├── kyc.py              # KYC verification
│   ├── sports.py           # Sports betting
│   ├── asian_markets.py    # Asian markets
│   ├── conversational.py   # AI chat system
│   ├── payments.py         # Payment processing
│   └── templates/          # HTML templates
├── core/                   # Core business logic
│   ├── omega_flow.py       # Lottery predictions
│   ├── omega_sports_flow.py # Sports analysis
│   ├── asian_handicap_engine.py # Handicap calculations
│   └── conversation_manager.py # Chat management
├── modules/                # Specialized modules
│   ├── sports/            # Sports betting modules
│   ├── asian/             # Asian market modules
│   ├── payments/          # Payment modules
│   ├── localization/      # Language support
│   └── analytics/         # Analytics modules
├── scripts/               # Utility scripts
│   ├── retrain_after_draw.py # Model retraining
│   ├── asian_market_sync.py # Market data sync
│   └── conversation_training.py # AI training
├── deploy/                # Deployment configurations
│   ├── Dockerfile.api     # Main API container
│   ├── Dockerfile.asian   # Asian markets container
│   ├── docker-compose.yml # Full stack deployment
│   ├── docker-compose.asian.yml # Asian-specific deployment
│   └── akash-deploy.yaml  # Akash Network deployment
├── tests/                 # Comprehensive test suite
├── docs/                  # Documentation
└── requirements.txt       # Python dependencies
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Redis
- PostgreSQL (optional)

### 1. Clone and Setup
```bash
# Extract the OMEGA_COMPLETE package
cd OMEGA_COMPLETE

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

Required environment variables:
```env
REDIS_URL=redis://localhost:6379
CLAUDE_API_KEY=your_claude_api_key
OAUTH_SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://user:pass@localhost/omega_db
```

### 3. Docker Deployment (Recommended)
```bash
# Start full stack
docker-compose -f deploy/docker-compose.yml up -d

# Or start Asian markets only
docker-compose -f deploy/docker-compose.asian.yml up -d
```

### 4. Manual Deployment
```bash
# Start Redis
redis-server

# Start the application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5. Verify Installation
```bash
curl http://localhost:8000/health
```

---

## 📖 API Documentation

### Core Endpoints

#### Lottery Predictions
```http
POST /entregar_series
Content-Type: application/json

{
    "lottery_type": "kabala",
    "series_count": 5,
    "filters": {
        "exclude_numbers": [13],
        "include_numbers": [7, 21]
    }
}
```

#### Sports Betting
```http
GET /sports/odds?sport=football&region=us
GET /sports/picks?min_edge=2.0&min_confidence=0.7
GET /sports/analytics/{user_id}?timeframe=30
```

#### Asian Markets
```http
GET /asian/handicaps?sport=asian_football&league=j_league&language=zh
POST /asian/calculate-handicap?home_strength=0.6&away_strength=0.4
GET /asian/cultural-preferences/japan
```

#### Conversational AI
```http
POST /chat/chat
Content-Type: application/json

{
    "message": "How do lottery predictions work?",
    "session_id": "session_123",
    "mode": "text",
    "language": "en"
}
```

#### Payment System
```http
GET /payments/methods?user_region=us
POST /payments/create
GET /payments/status/{payment_id}
```

#### KYC System
```http
POST /kyc/submit
GET /kyc/status/{application_id}
POST /kyc/verify?user_id=123&application_id=app_456
```

### Authentication

Most endpoints support optional authentication:
```http
Authorization: Bearer your_jwt_token
```

---

## 🌐 Deployment Options

### Docker Compose (Recommended)
```bash
# Full deployment with monitoring
docker-compose -f deploy/docker-compose.yml up -d

# Asian markets specialized
docker-compose -f deploy/docker-compose.asian.yml up -d
```

### Akash Network (Decentralized Cloud)
```bash
# Deploy to Akash Network
akash tx deployment create deploy/akash-deploy.yaml --from mykey

# Check deployment status
akash provider lease-status --dseq $DSEQ --provider $PROVIDER
```

### Manual Production Deployment
```bash
# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Start with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Environment-Specific Deployments

#### Development
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Staging
```bash
docker-compose -f deploy/docker-compose.yml -f deploy/docker-compose.staging.yml up -d
```

#### Production
```bash
docker-compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml up -d
```

---

## ⚙️ Configuration

### Core Configuration
```env
# Application
ENVIRONMENT=production
LOG_LEVEL=info
DEBUG=false

# Database
DATABASE_URL=postgresql://user:pass@host:5432/omega_db
REDIS_URL=redis://localhost:6379

# AI Services
CLAUDE_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_key (optional)

# Security
OAUTH_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Sports Betting APIs
ODDS_API_KEY=your_odds_api_key
RAPIDAPI_KEY=your_rapidapi_key

# Asian Markets
BETINASIA_API_KEY=your_betinasia_key
ISPORTS_API_KEY=your_isports_key

# Payment Processing
STRIPE_SECRET_KEY=your_stripe_key
PAYPAL_CLIENT_ID=your_paypal_id
COINBASE_API_KEY=your_coinbase_key

# Monitoring
SENTRY_DSN=your_sentry_dsn
PROMETHEUS_ENABLED=true
```

### Feature Flags
```env
# Enable/Disable Features
LOTTERY_PREDICTIONS_ENABLED=true
SPORTS_BETTING_ENABLED=true
ASIAN_MARKETS_ENABLED=true
CONVERSATIONAL_AI_ENABLED=true
CRYPTO_PAYMENTS_ENABLED=true
KYC_VERIFICATION_ENABLED=true
```

### Localization
```env
# Supported Languages
SUPPORTED_LANGUAGES=en,zh,ja,ko,th,hi
DEFAULT_LANGUAGE=en

# Regional Settings
DEFAULT_CURRENCY=USD
SUPPORTED_CURRENCIES=USD,EUR,GBP,JPY,CNY,KRW,THB,INR
```

---

## 🛠 Development

### Setup Development Environment
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run linting
black .
flake8 .
mypy .
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_main.py -v

# Run integration tests
pytest tests/integration/ -v
```

### Development Workflow
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/new-feature
```

### Adding New Features

1. **Create module in appropriate directory**
2. **Add tests in tests/ directory**
3. **Update documentation**
4. **Add to requirements if needed**
5. **Update Docker configurations**

---

## 🧪 Testing

### Test Structure
```
tests/
├── test_main.py           # Main API tests
├── test_kyc.py           # KYC system tests
├── test_sports.py        # Sports betting tests
├── test_asian_markets.py # Asian markets tests
├── test_conversational.py # AI chat tests
├── test_payments.py      # Payment system tests
├── integration/          # Integration tests
├── load/                 # Load testing
└── fixtures/             # Test data
```

### Running Different Test Types
```bash
# Unit tests
pytest tests/test_*.py

# Integration tests
pytest tests/integration/

# Load tests
pytest tests/load/ --maxfail=1

# End-to-end tests
pytest tests/e2e/
```

### Test Coverage
```bash
# Generate coverage report
pytest --cov=app --cov-report=html tests/

# View coverage
open htmlcov/index.html
```

---

## 🔧 Troubleshooting

### Common Issues

#### Redis Connection Issues
```bash
# Check Redis status
redis-cli ping

# Check connection
redis-cli -h localhost -p 6379
```

#### Docker Issues
```bash
# Check container logs
docker-compose logs omega-api

# Restart services
docker-compose restart

# Clean rebuild
docker-compose down -v && docker-compose up -d --build
```

#### Performance Issues
```bash
# Monitor resource usage
docker stats

# Check API performance
curl -w "@curl-format.txt" -o /dev/null http://localhost:8000/health
```

### Debugging

Enable debug mode:
```env
DEBUG=true
LOG_LEVEL=debug
```

View logs:
```bash
# Application logs
tail -f logs/app.log

# Docker logs
docker-compose logs -f omega-api
```

---

## 📊 Monitoring & Analytics

### Built-in Monitoring
- **Health checks** at `/health`
- **Metrics** at `/metrics` (Prometheus format)
- **Performance tracking** with request timing
- **Error logging** with Sentry integration

### Grafana Dashboards
Access Grafana at `http://localhost:3000` (admin/admin123)

Pre-configured dashboards:
- API Performance
- Sports Betting Analytics
- Payment Processing
- User Activity

### Log Analysis
```bash
# View application logs
docker-compose exec omega-api tail -f /app/logs/app.log

# Search logs
grep "ERROR" logs/app.log

# Monitor real-time
tail -f logs/app.log | grep "lottery_prediction"
```

---

## 🔒 Security

### Security Features
- **Rate limiting** on all endpoints
- **Input validation** and sanitization
- **JWT authentication** with refresh tokens
- **CORS** protection
- **SQL injection** prevention
- **XSS** protection
- **CSRF** tokens

### Security Best Practices
1. **Use HTTPS** in production
2. **Rotate API keys** regularly
3. **Monitor** suspicious activity
4. **Update dependencies** frequently
5. **Backup** data regularly

---

## 🚀 Performance

### Optimization Features
- **Redis caching** for frequently accessed data
- **Async processing** for I/O operations
- **Connection pooling** for databases
- **CDN integration** for static assets
- **Load balancing** with Nginx

### Performance Tuning
```python
# Adjust worker processes
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Configure Redis
redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru

# Database optimization
# Use connection pooling, query optimization
```

---

## 📈 Scaling

### Horizontal Scaling
```yaml
# Docker Swarm
docker service create --replicas 3 omega/omega-pro-ai

# Kubernetes
kubectl scale deployment omega-api --replicas=5
```

### Vertical Scaling
```yaml
# Increase container resources
resources:
  limits:
    cpu: "2"
    memory: "4Gi"
```

---

## 🌍 Multi-Language Support

### Supported Languages
- **English** (en) - Primary
- **Chinese** (zh) - Simplified & Traditional
- **Japanese** (ja) - Full support
- **Korean** (ko) - Full support
- **Thai** (th) - Full support
- **Hindi** (hi) - Text only

### Adding New Languages
1. Add translations to `modules/localization/`
2. Update language detection logic
3. Add voice support if needed
4. Test thoroughly with native speakers

---

## 🤝 Contributing

### How to Contribute
1. **Fork** the repository
2. **Create** feature branch
3. **Make** changes with tests
4. **Submit** pull request

### Contribution Guidelines
- Follow PEP 8 style guide
- Write comprehensive tests
- Update documentation
- Use conventional commits

### Code Review Process
1. Automated tests must pass
2. Code review by maintainers
3. Security review for sensitive changes
4. Performance testing for critical paths

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

### Getting Help
- **Documentation**: Check this README and `/docs`
- **Issues**: Create GitHub issues for bugs
- **Discussions**: Use GitHub discussions for questions
- **Email**: support@omega-pro-ai.com

### Commercial Support
Enterprise support and custom development available.
Contact: enterprise@omega-pro-ai.com

---

## 🚀 What's Next

### Roadmap
- **v4.1**: Enhanced AI models
- **v4.2**: Mobile app integration
- **v4.3**: Advanced analytics dashboard
- **v4.4**: Blockchain integration
- **v5.0**: Machine learning optimization

### Stay Updated
- **GitHub**: Watch for releases
- **Newsletter**: Subscribe for updates
- **Blog**: Follow development blog

---

**Built with ❤️ by the OMEGA PRO AI Team**

*Ready to revolutionize lottery predictions and sports betting with AI!*