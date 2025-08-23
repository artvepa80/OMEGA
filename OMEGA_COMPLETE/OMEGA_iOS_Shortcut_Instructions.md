# 📱 OMEGA iOS Shortcut Setup

## Crear Shortcut en iPhone/iPad:

### 1. Abrir Shortcuts App
- Busca "Shortcuts" o "Atajos" en tu iPhone
- Toca el ícono "+"

### 2. Configurar la Acción Web Request:
1. **Busca "Get Contents of URL"** y agrégala
2. **URL**: `https://a17d0f2p7pbkp4bc0pjgbsmp8o.ingress.paradigmapolitico.online/api/v1/predictions`
3. **Method**: POST
4. **Headers**:
   - Key: `Content-Type`
   - Value: `application/json`
5. **Request Body**: 
   ```json
   {"count": 10, "perfil_svi": "moderado"}
   ```

### 3. Procesar la Respuesta:
1. **Agrega "Get Value for"** 
   - Get: `predictions`
   - In: Contents of URL
2. **Agrega "Repeat with Each"**
3. **Agrega "Get Value for"**
   - Get: `combination` 
   - In: Repeat Item
4. **Agrega "Get Text from Input"**
5. **Agrega "Show Result"**

### 4. Nombrar y Guardar:
- **Nombre**: "OMEGA Predicciones"
- **Ícono**: Elige uno colorido
- **Toca "Done"**

## 🚀 Uso del Shortcut:
1. Di "Hey Siri, OMEGA Predicciones"
2. O toca el shortcut en la app
3. ¡Obtienes 10 predicciones instantáneas!

## 📋 Ejemplo de Resultado:
```
Predicciones OMEGA:
1. [5, 12, 18, 24, 31, 37] - Score: 0.89
2. [2, 9, 15, 22, 28, 35] - Score: 0.76
3. [7, 14, 19, 26, 33, 39] - Score: 0.82
...
```

## ⚙️ Personalización Avanzada:
- Cambia `"count": 10` por cualquier número (1-50)
- Cambia `"perfil_svi": "moderado"` por:
  - `"conservador"` (predicciones más seguras)
  - `"agresivo"` (predicciones más arriesgadas)
  - `"balanceado"` (equilibrio perfecto)