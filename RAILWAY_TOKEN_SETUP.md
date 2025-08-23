# 🔐 RAILWAY TOKEN SETUP - 2 MINUTOS

## 🚀 PASO A PASO RÁPIDO

### 1. **Obtener RAILWAY_TOKEN** (1 minuto)
1. Ve a https://railway.app/account/tokens
2. Click "**Create Token**"  
3. Nombre: `omega-deploy`
4. **Copia el token** (empieza con `railway_`)

### 2. **Ejecutar Deploy** (1 comando)
```bash
RAILWAY_TOKEN=railway_tu_token_aqui ./deploy-railway.sh omega-pro-ai
```

## ⚡ **ALTERNATIVA RÁPIDA - Railway Web**

Si no quieres usar CLI:

1. **Ve a https://railway.app**
2. **"New Project"** → **"Deploy from GitHub"**
3. **Conecta tu repo OMEGA**
4. Railway detecta `Dockerfile.railway` automáticamente
5. **Deploy automático** en 5-15 minutos

## 🎯 **RESULTADO ESPERADO**

Cualquier método te dará:
- ✅ **URL**: `https://omega-pro-ai-production.up.railway.app`
- ✅ **Endpoints**: `/health`, `/status`, `/predict`, `/`
- ✅ **OMEGA completo** funcionando con 24,110+ archivos
- ✅ **HTTPS automático** y escalabilidad

## 💡 **RECOMENDACIÓN**

**Usa Railway Web** - es más rápido y no requiere CLI setup.

---
*En 5 minutos tendrás OMEGA funcionando en Railway* 🚀