# 📱 OMEGA Pro AI - iOS App Instructions

## 🎯 **App Lista para Usar**

Tu app iOS está completamente configurada y conectada a OMEGA API en Akash Network:

### 📍 **URL de tu API:**
```
https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win
```

## 🚀 **Cómo Abrir la App**

### **Opción 1: Xcode (Recomendado)**
1. **Abre Finder** y navega a:
   ```
   /Users/user/Documents/OMEGA_PRO_AI_v10.1/ios/OmegaApp_Clean/Omega/
   ```

2. **Doble-click en:** `Omega.xcodeproj`

3. **En Xcode:**
   - Selecciona el **iPhone Simulator** (iPhone 15 Pro recomendado)
   - **Click en el botón ▶️ "Run"**
   - ¡La app se abrirá en el simulador!

### **Opción 2: Abrir desde Terminal**
```bash
cd /Users/user/Documents/OMEGA_PRO_AI_v10.1/ios/OmegaApp_Clean/Omega/
open Omega.xcodeproj
```

## 🎨 **Características de la App**

### **🧠 Tab Principal - Predicciones:**
- **Conecta directamente** con tu OMEGA API en Akash
- **Genera predicciones** con un click
- **Configurar cantidad** (5-20 predicciones)
- **Seleccionar perfil**: conservador, moderado, agresivo, balanceado
- **Visualización moderna** con scores de confianza y SVI

### **🕒 Tab Historial:**
- **Guarda automáticamente** todas las predicciones generadas
- **Ver detalles** de cada predicción con timestamp
- **Calidad visual** con códigos de colores

### **📊 Tab Estado del Sistema:**
- **Monitoreo en tiempo real** del estado de OMEGA
- **Health check** automático
- **Información del servidor** Akash Network
- **Versiones y configuración**

### **⚙️ Tab Ajustes:**
- **Configuraciones de la app**
- **Información de versión**
- **Enlaces de soporte**

## 🔧 **Funcionalidades Técnicas**

### **✅ Configurado Automáticamente:**
- **SSL Certificate bypass** para Akash Network
- **Error handling** robusto
- **Retry logic** para conexiones
- **Haptic feedback** para interacciones
- **Loading states** y animaciones
- **Dark/Light mode** support

### **🌐 API Integration:**
- **POST** requests para generar predicciones
- **JSON** parsing automático
- **Real-time** conexión con tu OMEGA API
- **Health checks** periódicos

## 🚨 **Si Encuentras Problemas:**

### **Error de Certificado SSL:**
- ✅ **Ya está solucionado** - La app acepta certificados auto-firmados de Akash

### **Error de Conexión:**
- Verifica que OMEGA esté corriendo: `https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win/health`
- Verifica tu conexión a Internet

### **Error de Build:**
- Asegúrate de tener **Xcode 15+** instalado
- Selecciona **iOS 17.0+** como target

## 🎯 **Usar la App:**

1. **Abre la app** en el simulador
2. **Tab "Predicciones"**
3. **Selecciona configuración:**
   - Perfil: "moderado" (recomendado)
   - Cantidad: 10 predicciones
4. **Click "Generar Predicciones"**
5. **¡Disfruta tus predicciones OMEGA!** 🎉

## 📱 **Para Dispositivo Real:**

Si quieres instalar en tu iPhone real:

1. **Conecta tu iPhone** al Mac
2. **En Xcode**, selecciona tu iPhone en lugar del simulador
3. **Configura tu Apple ID** en Signing & Capabilities
4. **Click Run** - Se instalará en tu iPhone

## 🎊 **¡Resultado Final!**

Tendrás una **app nativa iOS moderna** que:
- Se conecta a **tu OMEGA API en Akash Network**
- Genera **predicciones reales** usando tus modelos ML
- **Interfaz súper bonita** con animaciones y efectos
- **Funciona offline** para historial
- **Ready para App Store** (con algunos ajustes adicionales)

¡Tu OMEGA ahora funciona desde iPhone, web, API, y CLI! 🚀