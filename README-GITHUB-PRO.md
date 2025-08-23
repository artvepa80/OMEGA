# 🚀 OMEGA PRO AI v10.1 - GitHub Pro Multi-Architecture

[![Build OMEGA Multi-Arch](https://github.com/artvepa80/-Users-user-Documents-OMEGA_PRO_AI_v10.1/actions/workflows/build-omega-multiarch.yml/badge.svg)](https://github.com/artvepa80/-Users-user-Documents-OMEGA_PRO_AI_v10.1/actions/workflows/build-omega-multiarch.yml)

**Sistema de predicción OMEGA avanzado con soporte multi-arquitectura construido con GitHub Pro**

## 🌟 Características

- ✅ **Multi-Arquitectura**: AMD64 + ARM64
- ✅ **GitHub Pro Optimizado**: Runners de 4 cores, 2GB storage
- ✅ **Algoritmos OMEGA Reales**: Sin simulaciones
- ✅ **Akash Network Ready**: Deployments optimizados
- ✅ **Cache Inteligente**: Builds súper rápidos
- ✅ **Auto-cleanup**: Gestión automática de imágenes

## 🏗️ Build Status

| Platform | Status | Size |
|----------|---------|------|
| AMD64 | ✅ Ready | ~1.5GB |
| ARM64 | ✅ Ready | ~1.5GB |

## 📦 Container Registry

```bash
# Pull la imagen multi-arquitectura
docker pull ghcr.io/artvepa80/omega-pro-ai:latest

# Run localmente
docker run -p 8000:8000 ghcr.io/artvepa80/omega-pro-ai:latest
```

## 🚀 Deploy en Akash Network

### Opción 1: Descarga el SDL generado

1. Ve a las [GitHub Actions](../../actions)
2. Descarga `omega-akash-github-pro.yaml`
3. Deploya en Akash:

```bash
akash tx deployment create omega-github-pro.yaml \
  --from tu-wallet \
  --node https://rpc.akashnet.net:443 \
  --chain-id akashnet-2 \
  --gas-prices 0.025uakt \
  -y
```

### Opción 2: SDL Manual

```yaml
version: "2.0"

services:
  omegaproaiv101:
    image: ghcr.io/artvepa80/omega-pro-ai:latest
    command:
      - "bash"
      - "-c"
      - "cd /app && python3 main.py --server-mode --port 8000"
    expose:
      - port: 8000
        as: 80
        to:
          - global: true
    env:
      - OMEGA_ENV=production
      - REAL_ALGORITHMS=true
      - GITHUB_PRO=true
    resources:
      cpu:
        units: "8.0"
      memory:
        size: 17Gi
      storage:
        - size: 107Gi
```

## 🔧 Desarrollo

### Build local multi-arch

```bash
# Setup buildx
docker buildx create --use

# Build para ambas arquitecturas
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f Dockerfile.github \
  -t omega-local:multiarch \
  --push .
```

### Trigger build manual

```bash
# Via GitHub CLI
gh workflow run build-omega-multiarch.yml

# Con force rebuild
gh workflow run build-omega-multiarch.yml -f force_build=true
```

## 📊 Recursos GitHub Pro Utilizados

| Recurso | Límite | Usado Aprox. |
|---------|--------|--------------|
| Storage | 2GB | ~1.5GB |
| Bandwidth | 10GB/mes | ~3GB/mes |
| Build Minutes | Unlimited | ~30 min/build |

## 🔍 Debugging

### Check container health

```bash
# Test health endpoint
curl https://tu-deployment.akash.pro/health

# Expected response
{
  "status": "healthy",
  "service": "OMEGA PRO AI v10.1 - GitHub Pro Multi-Arch",
  "algorithms": "REAL",
  "github_pro": true,
  "multi_arch": true
}
```

### Check logs

```bash
# Akash logs
akash provider lease-logs \
  --dseq TU_DSEQ \
  --provider TU_PROVIDER

# Docker logs local
docker logs container-id
```

## 🔄 CI/CD Workflow

1. **Push** to `main` → Auto build multi-arch
2. **Tag** `v*` → Release build
3. **PR** → Test build (no push)
4. **Manual** → Force rebuild

## 📈 Performance

| Métrica | GitHub Pro | Local Build |
|---------|------------|-------------|
| Build Time | ~15 min | ~45 min |
| Cache Hit | 90%+ | 0% |
| Multi-Arch | ✅ | ❌ |
| Auto Deploy | ✅ | ❌ |

## 🛠️ Troubleshooting

### Build fails

1. Check [Actions](../../actions) logs
2. Verify Dockerfile.github syntax
3. Check GitHub Pro storage usage

### Deployment fails

1. Verify SDL syntax
2. Check Akash provider compatibility
3. Verify image accessibility

## 🤝 Contributing

1. Fork el repo
2. Create feature branch
3. Submit PR
4. GitHub Actions will test automáticamente

## 📄 License

OMEGA PRO AI v10.1 - Proprietary