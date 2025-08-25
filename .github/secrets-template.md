# 🔐 GitHub Secrets Configuration

Para que el workflow de GitHub Actions funcione correctamente, necesitas configurar estos secrets en tu repositorio:

## Configuración en GitHub

1. Ve a tu repositorio en GitHub
2. Navega a **Settings** → **Secrets and variables** → **Actions**
3. Agrega los siguientes secrets:

## Required Secrets

### Docker Hub
```
DOCKERHUB_USERNAME=tu_username_dockerhub
DOCKERHUB_TOKEN=tu_personal_access_token
```

### Akash Network (Opcional - solo para auto-deployment)
```
AKASH_WALLET_SEED=tu_wallet_seed_phrase
AKASH_KEYRING_BACKEND=os
AKASH_FROM=tu_wallet_name
```

## Cómo obtener los tokens

### Docker Hub Token
1. Ve a [Docker Hub](https://hub.docker.com)
2. Settings → Security → New Access Token
3. Copia el token y guárdalo como `DOCKERHUB_TOKEN`

### GitHub Token (Ya disponible)
El `GITHUB_TOKEN` se genera automáticamente para cada workflow.

## Repositorio URL
Asegúrate de que la URL del repositorio en el Dockerfile esté correcta:
```
LABEL org.opencontainers.image.source="https://github.com/artvepa80/OMEGA_PRO_AI_v10.1"
```

## Verificación
Después de configurar los secrets, el workflow debería:
1. ✅ Build multi-arch (AMD64 + ARM64)
2. ✅ Push to GitHub Container Registry
3. ✅ Push to Docker Hub  
4. ✅ Run security scans
5. ✅ Generate build summary

## Imágenes resultantes
- `ghcr.io/artvepa80/omega-ai:latest`
- `ghcr.io/artvepa80/omega-ai:complete-v10.1`
- `artvepa80/omega-ai:latest`
- `artvepa80/omega-ai:complete-v10.1`