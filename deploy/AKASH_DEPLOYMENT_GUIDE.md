# OMEGA PRO AI v10.1 - Akash Network Deployment Guide

## 🎯 Overview
Deploy OMEGA PRO AI v10.1 to the Akash decentralized cloud network for 24/7 availability at approximately $5/month.

## ✅ Prerequisites Verified
- ✅ Akash CLI installed (v0.38.4)
- ✅ Wallet configured: `omega-wallet` 
- ✅ Wallet address: `akash1a7ztnxls3dgzdpm85nthvhdhv8wuttre0ydy8t`
- ✅ Deployment configuration ready: `omega-akash-optimized.yaml`

## 🚨 Required Action: Fund Wallet

**Your wallet currently has 0 AKT balance.** You need to fund it before deployment:

### Option 1: Purchase AKT
1. Buy AKT from exchanges (Osmosis, Kraken, etc.)
2. Send to your wallet: `akash1a7ztnxls3dgzdpm85nthvhdhv8wuttre0ydy8t`
3. Minimum recommended: **10 AKT**

### Option 2: Use Akash Faucet (Testnet only)
For testing, you can use testnet faucet, but mainnet requires purchasing AKT.

## 💰 Cost Analysis
- **Deployment creation**: ~0.05 AKT (transaction fee)
- **Monthly hosting**: ~5 AKT/month (~$5 USD at current rates)
- **Resource allocation**: 0.5 CPU, 1Gi RAM, 2Gi storage
- **Recommended wallet balance**: 10 AKT for safe deployment

## 🚀 Deployment Process

### Step 1: Fund Your Wallet
Transfer at least 10 AKT to: `akash1a7ztnxls3dgzdpm85nthvhdhv8wuttre0ydy8t`

### Step 2: Execute Deployment
```bash
cd /Users/user/Documents/OMEGA_PRO_AI_v10.1/deploy
./deploy-omega-akash.sh
```

### Step 3: Select Provider
After deployment creation, you'll see available providers. Select one based on:
- Price (lowest cost)
- Reputation score
- Geographic location

### Step 4: Create Lease
```bash
./create-lease.sh <DSEQ> <PROVIDER_ADDRESS>
```

### Step 5: Monitor Deployment
```bash
./monitor-deployment.sh <DSEQ> <PROVIDER_ADDRESS>
```

## 📊 API Endpoints

Once deployed, your OMEGA PRO AI will be available at a URL like:
`https://your-deployment-id.provider.akash.pro`

### Available Endpoints:

#### 1. Root Endpoint
```bash
GET /
```
**Response**: Service information and available endpoints

#### 2. Health Check
```bash
GET /health
```
**Response**:
```json
{
  "status": "healthy",
  "service": "OMEGA PRO AI v10.1",
  "platform": "Akash Network",
  "timestamp": "2025-08-14T...",
  "uptime": "Active"
}
```

#### 3. Prediction Endpoint
```bash
POST /predict
Content-Type: application/json
Body: {"quantity": 5}
```
**Response**:
```json
{
  "predictions": [
    {
      "combination": [1, 15, 23, 28, 35, 40],
      "score": 0.687,
      "svi": 0.752,
      "source": "omega-akash",
      "timestamp": "2025-08-14T..."
    }
  ],
  "count": 5,
  "platform": "Akash Network",
  "model": "OMEGA-v10.1-Simplified",
  "accuracy_baseline": "50%",
  "status": "success"
}
```

#### 4. Status Endpoint
```bash
GET /status
```
**Response**:
```json
{
  "omega_version": "10.1",
  "platform": "Akash Decentralized Cloud",
  "models_active": 5,
  "accuracy_baseline": "50%",
  "target_accuracy": "65-70%",
  "deployment_status": "production"
}
```

#### 5. API Documentation
```bash
GET /docs
```
Interactive FastAPI documentation interface.

## 🧪 Testing Examples

### Curl Commands
```bash
# Health check
curl https://your-url/health

# Get predictions
curl -X POST https://your-url/predict \
  -H "Content-Type: application/json" \
  -d '{"quantity": 3}'

# Check status
curl https://your-url/status
```

### Python Integration
```python
import requests

# Your Akash deployment URL
OMEGA_URL = "https://your-deployment-id.provider.akash.pro"

# Health check
health = requests.get(f"{OMEGA_URL}/health")
print("Health:", health.json())

# Get predictions
predictions = requests.post(
    f"{OMEGA_URL}/predict",
    json={"quantity": 5}
)
print("Predictions:", predictions.json())
```

## 📋 Monitoring Commands

### Check Wallet Balance
```bash
akash query bank balances akash1a7ztnxls3dgzdpm85nthvhdhv8wuttre0ydy8t \
  --chain-id akashnet-2 \
  --node https://rpc.akashnet.net:443
```

### List Your Deployments
```bash
akash query deployment list \
  --owner akash1a7ztnxls3dgzdpm85nthvhdhv8wuttre0ydy8t \
  --chain-id akashnet-2 \
  --node https://rpc.akashnet.net:443
```

### Check Deployment Status
```bash
akash query deployment get \
  --owner akash1a7ztnxls3dgzdpm85nthvhdhv8wuttre0ydy8t \
  --dseq <DSEQ> \
  --chain-id akashnet-2 \
  --node https://rpc.akashnet.net:443
```

## 🔧 Troubleshooting

### Common Issues:

1. **"Account not found"**
   - Wallet needs AKT balance
   - Fund wallet first

2. **"No providers found"**
   - Market conditions vary
   - Try adjusting pricing in YAML
   - Wait and retry

3. **"Manifest deployment failed"**
   - Check provider compatibility
   - Verify YAML syntax
   - Try different provider

4. **Service not responding**
   - Check deployment logs
   - Verify provider status
   - Monitor with monitoring script

### Getting Help:
- Akash Discord: https://discord.akash.network
- Akash Documentation: https://docs.akash.network
- Provider status: https://akash.network/providers

## 🎉 Success Indicators

You'll know the deployment is successful when:
1. ✅ Deployment transaction succeeds
2. ✅ Provider accepts bid and lease is created
3. ✅ Service URL responds to `/health` endpoint
4. ✅ Prediction endpoint returns lottery combinations
5. ✅ All API endpoints are functional

## 📈 Next Steps After Deployment

1. **Bookmark your service URL**
2. **Set up monitoring alerts**
3. **Integrate with your applications**
4. **Monitor costs and provider performance**
5. **Scale resources if needed**

---

## 📞 Ready to Deploy?

1. **Fund your wallet** with at least 10 AKT
2. **Run**: `./deploy-omega-akash.sh`
3. **Follow the prompts** to select provider and create lease
4. **Test your deployment** with the monitoring script

Your OMEGA PRO AI v10.1 will then be running 24/7 on Akash Network! 🚀