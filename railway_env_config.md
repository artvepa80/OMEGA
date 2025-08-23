# 🔧 Variables de Entorno para Railway

## Variables CRÍTICAS (añadir en Railway Dashboard → Variables):

```bash
# === BÁSICAS ===
PORT=8000
ENVIRONMENT=production
PYTHONUNBUFFERED=1

# === SEGURIDAD ===
JWT_SECRET=omega_super_secret_jwt_key_2024_railway
CORS_ORIGINS=https://tu-app.railway.app,https://tudominio.com

# === OPCIONAL (si necesitas) ===
# Para base de datos (Railway puede agregar automáticamente)
# DATABASE_URL=(Railway lo asigna automáticamente si agregas PostgreSQL)

# Para WhatsApp (opcional)
# WHATSAPP_TOKEN=tu_token_whatsapp
# WHATSAPP_PHONE_ID=tu_phone_id

# Para notificaciones (opcional)
# TWILIO_ACCOUNT_SID=tu_twilio_sid
# TWILIO_AUTH_TOKEN=tu_twilio_token
```

## 📋 Pasos en Railway Dashboard:

1. **Abrir tu proyecto** en Railway
2. **Click en "Variables"** (pestaña)
3. **Agregar una por una**:
   - `PORT` = `8000`
   - `ENVIRONMENT` = `production` 
   - `PYTHONUNBUFFERED` = `1`
   - `JWT_SECRET` = `omega_super_secret_jwt_key_2024_railway`
   - `CORS_ORIGINS` = `*` (por ahora, cambiar después)

4. **Click "Deploy"** para aplicar cambios

## 🌍 URL que obtendrás:
Railway te dará una URL como: `https://omega-api-production-xxxx.up.railway.app`

## 📱 Para la app iOS:
Actualiza `OmegaAPIClient.swift` con la nueva URL.
