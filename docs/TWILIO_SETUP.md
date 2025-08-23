# 📱 Configuración Twilio para OMEGA AI

Esta guía te llevará paso a paso para integrar tu cuenta Twilio con OMEGA AI y recibir predicciones por SMS/WhatsApp.

## 🚀 Paso 1: Configurar Credenciales

### 1.1 Obtener credenciales de Twilio Console

1. Ve a tu [Twilio Console](https://console.twilio.com/)
2. En el Dashboard principal, copia:
   - **Account SID** 
   - **Auth Token**

### 1.2 Configurar archivo .env

Crea un archivo `.env` en la raíz del proyecto con:

```bash
# Credenciales Twilio (obligatorias)
TWILIO_ACCOUNT_SID=tu_account_sid_aqui
TWILIO_AUTH_TOKEN=tu_auth_token_aqui
TWILIO_FROM_NUMBER=+14155238886  # Tu número de Twilio
TWILIO_TO_NUMBER=+51972514235    # Tu número personal

# Seguridad (opcional)
TWILIO_VERIFY_SIGNATURE=false    # true para producción
TWILIO_WHITELIST=51972514235     # Solo estos números pueden usar OMEGA
```

## 📞 Paso 2: Configurar Webhook (Método Automático)

### 2.1 Usar el script automático

```bash
# Instalar ngrok si no lo tienes
brew install ngrok  # macOS
# o descarga desde https://ngrok.com/download

# Ejecutar script de configuración
python scripts/setup_twilio_ngrok.py
```

El script:
- ✅ Verifica que ngrok esté instalado
- ✅ Crea archivo .env desde template
- ✅ Inicia ngrok en puerto 8000
- ✅ Te muestra la URL del webhook
- ✅ Te da instrucciones para Twilio Console

## 🔧 Paso 3: Configurar Twilio Console

### 3.1 Para SMS (números regulares)

1. Ve a **Phone Numbers > Manage > Active numbers**
2. Selecciona tu número de Twilio
3. En la sección **Messaging**:
   - **Webhook URL**: `https://tu-ngrok-url.ngrok.io/webhooks/twilio/sms`
   - **HTTP Method**: `POST`
4. Guarda los cambios

### 3.2 Para WhatsApp Sandbox

1. Ve a **Messaging > Try it out > WhatsApp Sandbox**
2. En **Sandbox Configuration**:
   - **When a message comes in**: `https://tu-ngrok-url.ngrok.io/webhooks/twilio/sms`
   - **Method**: `POST`
3. Guarda los cambios
4. Únete al sandbox enviando el código que te dan

## 🎯 Paso 4: Iniciar OMEGA

```bash
# Terminal 1: Iniciar la API
uvicorn api_interface:app --reload --port 8000

# Terminal 2: Mantener ngrok activo
ngrok http 8000
```

## 📱 Comandos Disponibles

Envía estos mensajes a tu número Twilio:

- **`predice`** - Solicita nueva predicción
- **`estado`** - Verifica estado del sistema
- **`help`** - Lista de comandos disponibles

### Ejemplo de conversación:

```
Tú: predice
OMEGA: 🎯 OMEGA Predicción
       12 34 56 78 90 99
       Confianza: 75.3%

Tú: estado
OMEGA: ✅ OMEGA Online
       Modelos: 3
       Última pred: 2024-01-08 20:30
```

## 🔒 Seguridad (Producción)

Para entorno de producción:

```bash
# .env
TWILIO_VERIFY_SIGNATURE=true
TWILIO_WHITELIST=51972514235,51999888777  # Solo números autorizados
```

## ❌ Solución de Problemas

### Error: "Webhook timeout"
- Verifica que la API esté corriendo en puerto 8000
- Confirma que ngrok esté activo y la URL sea correcta

### Error: "Invalid Twilio signature"
- Revisa que `TWILIO_AUTH_TOKEN` sea correcto
- Si usas ngrok, desactiva verificación: `TWILIO_VERIFY_SIGNATURE=false`

### Error: "Sistema OMEGA no disponible"
- Verifica que `omega_hybrid_integration.py` funcione
- Revisa logs de la API para errores de inicialización

### WhatsApp no responde
- Confirma que te uniste al Sandbox de Twilio
- Verifica que el webhook esté configurado correctamente
- Usa el formato exacto: `whatsapp:+51972514235`

## 🧪 Testing

### Probar envío saliente:
```bash
# Desde la UI
http://localhost:3000/twilio

# O directamente:
curl -X POST http://localhost:8000/ui/integrations/twilio/test \
  -H "Content-Type: application/json" \
  -d '{"body": "🤖 Test desde OMEGA!"}'
```

### Probar webhook:
```bash
# Simular mensaje entrante
curl -X POST https://tu-ngrok-url.ngrok.io/webhooks/twilio/sms \
  -d "From=%2B51972514235&Body=predice&To=%2B14155238886"
```

## 📊 Logs y Debugging

Los mensajes aparecen en la consola:
```
[Twilio] +51972514235 -> predice | Response: 🎯 OMEGA Predicción...
```

Para logs detallados, activa debug:
```bash
DEBUG=true uvicorn api_interface:app --reload
```

---

🎉 **¡Listo!** Ahora OMEGA puede hablar contigo por SMS/WhatsApp vía Twilio.

**Próximos pasos:**
- Configura el scheduler para predicciones automáticas
- Integra con Meta Cloud API para WhatsApp Business
- Añade más comandos personalizados

