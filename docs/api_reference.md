# 📚 OMEGA Pro AI - API Reference

## Descripción General

La API de OMEGA Pro AI proporciona acceso programático al sistema avanzado de predicción de lotería. Utiliza múltiples modelos de inteligencia artificial para generar predicciones optimizadas.

## Base URL

```
https://api.omega-ai.com/api/v1
```

## Autenticación

La API utiliza tokens JWT (JSON Web Tokens) para autenticación. Todos los endpoints excepto `/health` y `/auth/login` requieren autenticación.

### Obtener Token

```http
POST /auth/login
Content-Type: application/json

{
  "username": "tu_usuario",
  "password": "tu_contraseña"
}
```

**Respuesta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### Usar Token

Incluye el token en el header `Authorization`:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Endpoints

### 🏠 Root

**GET** `/`

Información básica de la API.

**Respuesta:**
```json
{
  "message": "🎯 OMEGA Pro AI - Advanced Lottery Prediction System",
  "version": "10.1.0",
  "api_version": "v1",
  "docs_url": "/api/v1/docs",
  "status": "active",
  "features": [
    "Multi-model AI predictions",
    "Adaptive learning",
    "SVI scoring",
    "Real-time metrics",
    "JWT authentication"
  ]
}
```

### 🏥 Health Check

**GET** `/health`

Verifica el estado de salud del sistema.

**Respuesta:**
```json
{
  "status": "healthy",
  "uptime_seconds": 3600.5,
  "version": "10.1.0",
  "models_active": 6,
  "memory_usage_mb": 256.7,
  "cpu_usage_percent": 15.2
}
```

### 🔐 Autenticación

**POST** `/auth/login`

Autentica usuario y retorna JWT token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Respuesta Exitosa (200):**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Errores:**
- `401` - Credenciales inválidas

### 🎯 Generar Predicciones

**POST** `/predictions/generate`

Genera predicciones usando modelos de IA configurados.

**Requiere Autenticación:** ✅

**Request Body:**
```json
{
  "count": 8,
  "models": ["neural_enhanced", "lstm_v2", "transformer_deep"],
  "enable_learning": true,
  "svi_profile": "default"
}
```

**Parámetros:**
- `count` (integer, 1-50): Número de predicciones a generar
- `models` (array, opcional): Modelos específicos a usar
- `enable_learning` (boolean): Activar aprendizaje adaptativo
- `svi_profile` (string): Perfil SVI (default, conservative, aggressive, neural_optimized)

**Respuesta Exitosa (200):**
```json
{
  "session_id": "20250810_143022",
  "predictions": [
    {
      "combination": [1, 15, 23, 31, 35, 40],
      "confidence": 0.85,
      "svi_score": 0.78,
      "source_model": "neural_enhanced",
      "final_score": 0.82
    },
    {
      "combination": [3, 12, 19, 26, 33, 38],
      "confidence": 0.79,
      "svi_score": 0.71,
      "source_model": "lstm_v2", 
      "final_score": 0.76
    }
  ],
  "generation_time": 2.345,
  "models_used": ["neural_enhanced", "lstm_v2", "transformer_deep"],
  "metadata": {
    "cycle_time": 2.345,
    "predictions_generated": 8,
    "data_records_processed": 1000,
    "models_used": ["neural_enhanced", "lstm_v2"]
  }
}
```

**Errores:**
- `401` - Token inválido o expirado
- `422` - Parámetros de entrada inválidos
- `500` - Error interno del sistema

### 🧠 Aprendizaje Adaptativo

**POST** `/learning/learn-from-result`

Ejecuta aprendizaje adaptativo basado en resultado oficial.

**Requiere Autenticación:** ✅

**Request Body:**
```json
{
  "official_result": [7, 14, 21, 28, 35, 42],
  "date": "2025-08-10"
}
```

**Parámetros:**
- `official_result` (array): Resultado oficial (6 números entre 1-40)
- `date` (string): Fecha del sorteo (YYYY-MM-DD)

**Respuesta Exitosa (200):**
```json
{
  "success": true,
  "learning_score": 0.73,
  "improvements": {
    "accuracy_increase": 0.05,
    "model_adjustments": 3,
    "patterns_learned": 12
  },
  "model_adjustments": {
    "neural_enhanced": {"weight_change": 0.02},
    "lstm_v2": {"weight_change": -0.01}
  },
  "message": "Aprendizaje completado exitosamente"
}
```

### ⚙️ Estado del Sistema

**GET** `/system/status`

Estado detallado del sistema y componentes.

**Requiere Autenticación:** ✅

**Respuesta:**
```json
{
  "status": "healthy",
  "uptime_seconds": 7200.5,
  "version": "10.1.0",
  "models_active": 6,
  "memory_usage_mb": 512.3,
  "cpu_usage_percent": 25.7
}
```

### 📊 Métricas del Sistema

**GET** `/metrics`

Métricas detalladas del sistema.

**Requiere Autenticación:** ✅

**Respuesta:**
```json
{
  "timestamp": "2025-08-10T14:30:22Z",
  "counters": {
    "api_requests_total": 150,
    "predictions_generated": 45,
    "auth_success": 12
  },
  "gauges": {
    "system_cpu_percent": 25.7,
    "system_memory_percent": 34.2,
    "active_models": 6
  },
  "errors": {
    "prediction_errors": 2,
    "auth_failures": 1
  },
  "active_timers": 0,
  "system_metrics": {
    "cpu_percent": 25.7,
    "memory_percent": 34.2,
    "memory_used_mb": 512.3,
    "disk_percent": 15.8,
    "disk_free_gb": 45.2
  }
}
```

**GET** `/metrics/prometheus`

Métricas en formato Prometheus para integración con sistemas de monitoreo.

## Modelos Disponibles

| Modelo | Descripción | Peso por Defecto |
|--------|-------------|------------------|
| `neural_enhanced` | Red neuronal avanzada | 45% |
| `transformer_deep` | Arquitectura transformer | 15% |
| `lstm_v2` | LSTM bidireccional v2 | 12% |
| `genetic` | Algoritmo genético | 15% |
| `clustering` | Clustering inteligente | 8% |
| `montecarlo` | Simulación Monte Carlo | 5% |

## Perfiles SVI

| Perfil | Descripción | Uso Recomendado |
|--------|-------------|-----------------|
| `default` | Balance general | Uso cotidiano |
| `conservative` | Números frecuentes | Juego seguro |
| `aggressive` | Alto riesgo/premio | Jackpots grandes |
| `neural_optimized` | Optimizado por IA | **Recomendado** |

## Rate Limits

| Endpoint | Límite |
|----------|--------|
| `/predictions/generate` | 100/hora |
| `/learning/*` | 50/hora |
| `/system/*` | 200/hora |
| Otros endpoints | 1000/hora |

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| `400` | Bad Request - Parámetros inválidos |
| `401` | Unauthorized - Token faltante o inválido |
| `403` | Forbidden - Sin permisos |
| `404` | Not Found - Endpoint no encontrado |
| `422` | Unprocessable Entity - Validación fallida |
| `429` | Too Many Requests - Rate limit excedido |
| `500` | Internal Server Error - Error del sistema |
| `503` | Service Unavailable - Sistema no disponible |

## Estructura de Error

Todos los errores siguen esta estructura:

```json
{
  "error": true,
  "message": "Descripción del error",
  "status_code": 400,
  "timestamp": "2025-08-10T14:30:22Z",
  "path": "/api/v1/predictions/generate"
}
```

## Ejemplos de Uso

### Python

```python
import requests
import json

# Configuración
BASE_URL = "https://api.omega-ai.com/api/v1"

# Autenticación
auth_response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "omega_user",
    "password": "secure_password"
})

if auth_response.status_code == 200:
    token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Generar predicciones
    prediction_response = requests.post(
        f"{BASE_URL}/predictions/generate",
        json={
            "count": 8,
            "models": ["neural_enhanced", "lstm_v2"],
            "svi_profile": "neural_optimized"
        },
        headers=headers
    )
    
    if prediction_response.status_code == 200:
        predictions = prediction_response.json()
        print(f"Generadas {len(predictions['predictions'])} predicciones")
        
        for i, pred in enumerate(predictions['predictions'], 1):
            combination = pred['combination']
            confidence = pred['confidence']
            print(f"{i}. {combination} (Confianza: {confidence:.1%})")
```

### JavaScript

```javascript
const OMEGA_API = {
  baseURL: 'https://api.omega-ai.com/api/v1',
  
  async login(username, password) {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    
    if (response.ok) {
      const data = await response.json();
      this.token = data.access_token;
      return data;
    }
    throw new Error('Authentication failed');
  },
  
  async generatePredictions(options = {}) {
    const response = await fetch(`${this.baseURL}/predictions/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`
      },
      body: JSON.stringify({
        count: options.count || 8,
        models: options.models,
        svi_profile: options.svi_profile || 'default'
      })
    });
    
    if (response.ok) {
      return await response.json();
    }
    throw new Error('Prediction generation failed');
  }
};

// Uso
async function main() {
  try {
    await OMEGA_API.login('omega_user', 'secure_password');
    const predictions = await OMEGA_API.generatePredictions({
      count: 5,
      svi_profile: 'neural_optimized'
    });
    
    console.log('Predicciones generadas:', predictions);
  } catch (error) {
    console.error('Error:', error.message);
  }
}
```

### cURL

```bash
# Autenticación
TOKEN=$(curl -s -X POST "https://api.omega-ai.com/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"omega_user","password":"secure_password"}' \
  | jq -r '.access_token')

# Generar predicciones
curl -X POST "https://api.omega-ai.com/api/v1/predictions/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "count": 8,
    "models": ["neural_enhanced", "lstm_v2"],
    "svi_profile": "neural_optimized"
  }' | jq '.'
```

## Monitoreo y Métricas

La API expone métricas detalladas para monitoreo:

- **Performance**: Tiempos de respuesta, throughput
- **Sistema**: CPU, memoria, disco
- **Errores**: Conteo y tipos de errores
- **Modelos**: Estado y performance de modelos IA

Estas métricas están disponibles en formato JSON (`/metrics`) y Prometheus (`/metrics/prometheus`).

## Soporte

- **Documentación Interactiva**: `/api/v1/docs`
- **Email**: support@omega-ai.com
- **GitHub**: [Issues](https://github.com/omega-ai/omega-pro/issues)

## Changelog

### v10.1.0
- ✅ API refactorizada con FastAPI
- ✅ Autenticación JWT mejorada
- ✅ Documentación OpenAPI completa
- ✅ Métricas y monitoreo avanzado
- ✅ Sistema de logging estructurado
- ✅ Rate limiting configurable