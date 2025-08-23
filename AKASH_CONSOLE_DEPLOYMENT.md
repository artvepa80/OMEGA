# 🚀 OMEGA PRO AI v10.1 - Akash Console Deployment

## 📋 Deployment Instructions for Akash Console

### Option 1: Direct GitHub Clone (Recommended)

```yaml
---
version: "2.0"

services:
  omega-ai:
    image: python:3.11-slim
    command:
      - "bash"
      - "-c"
      - |
        echo "🚀 OMEGA PRO AI v10.1 - Akash Network"
        apt-get update && apt-get install -y curl git build-essential && \
        git clone https://github.com/artvepa80/OMEGA.git /app && \
        cd /app && \
        pip install --no-cache-dir -r requirements.txt && \
        echo "✅ OMEGA Ready!" && \
        python3 omega_server.py
        
    env:
      - "OMEGA_VERSION=v10.1"
      - "PORT=8000" 
      - "PYTHONPATH=/app"
      
    expose:
      - port: 8000
        as: 80
        to:
          - global: true

profiles:
  compute:
    omega-ai:
      resources:
        cpu:
          units: 8000m    # 8 CPU cores
        memory:
          size: 17Gi     # 17GB RAM
        storage:
          - size: 107Gi  # 107GB storage
  placement:
    akash:
      pricing:
        omega-ai:
          denom: uakt
          amount: 1000000

deployment:
  omega-ai:
    akash:
      profile: omega-ai
      count: 1
```

### Option 2: Code-Server Style (Development)

Use the Code-Server template and modify:

**Required Variables:**
- `PUID=1000`
- `PGID=1000` 
- `PASSWORD=omega-secure-2025`
- `SUDO_PASSWORD=omega-admin-2025`

**Resources:**
- CPU: 8000m (8 cores)
- Memory: 17Gi 
- Storage: 107Gi

## 🎯 Steps to Deploy:

1. **Go to Akash Console** → Templates → Code-Server
2. **Click "Deploy"** 
3. **Modify the YAML** with the OMEGA configuration above
4. **Set your resources** to match your available allocation
5. **Deploy!**

## 🌐 After Deployment:

Your OMEGA system will be available at:
- **Main API**: `http://your-akash-url/`
- **Health Check**: `http://your-akash-url/health`
- **Predictions**: `http://your-akash-url/predict`

## ✅ System Features Available:

- ✅ Complete OMEGA AI system (39,925 files)
- ✅ 11 AI models and ensemble system
- ✅ REST API with all endpoints
- ✅ Production-ready with 5.2GB of data
- ✅ Full ML pipeline and predictions
- ✅ Security hardened with SSL/TLS ready

**Total Resources Used:** 8 CPU + 17GB RAM + 107GB Storage - Perfect match for your allocation!