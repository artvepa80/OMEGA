# 📊 Guía de Actualización de Datos Integrada - OMEGA PRO AI

## ✅ **INTEGRACIÓN COMPLETADA**

Los scripts de actualización de datos (`update_sorteo.py` y `update_historical_data.py`) han sido **completamente integrados** en el sistema principal `main.py`.

## 🚀 **Comandos Disponibles**

### **1. Ver Información del Dataset**
```bash
python main.py --data-info
```
**Muestra:**
- Total de registros
- Rango de fechas
- Último sorteo registrado
- Calidad de datos

### **2. Actualizar Dataset con Nuevo Sorteo**
```bash
python main.py --update-data --fecha-sorteo 2025-08-16 --numeros-sorteo "1,15,23,31,35,40"
```

### **3. Actualizar con Backup Automático**
```bash
python main.py --update-data --fecha-sorteo 2025-08-16 --numeros-sorteo "1,15,23,31,35,40" --backup-data
```

### **4. Solo Ver Info (sin actualizar)**
```bash
python main.py --data-info
```

## 📋 **Formatos Soportados**

### **Fecha:**
- ✅ `2025-08-16` (YYYY-MM-DD)
- ❌ `16/08/2025` (formato incorrecto)
- ❌ `2025/08/16` (formato incorrecto)

### **Números:**
- ✅ `"1,2,3,4,5,6"` (con comas)
- ✅ `"1 2 3 4 5 6"` (con espacios)
- ✅ `"1,2, 3, 4,5,6"` (mixto)
- ❌ `"1,2,3,4,5"` (solo 5 números)
- ❌ `"1,2,3,4,5,6,7"` (7 números)
- ❌ `"0,1,2,3,4,5"` (números fuera de rango 1-40)

## 🛠️ **Validaciones Automáticas**

### ✅ **Exitosas:**
- Exactamente 6 números
- Números entre 1 y 40
- Formato de fecha correcto
- Dataset actualizado correctamente
- Backup creado (si se solicita)

### ❌ **Errores Manejados:**
- Número incorrecto de números
- Números fuera del rango válido
- Formato de fecha inválido
- Faltan argumentos requeridos
- Problemas de escritura de archivos

## 📊 **Ejemplo de Uso Completo**

```bash
# 1. Ver estado actual
python main.py --data-info

# 2. Actualizar con nuevo sorteo (con backup)
python main.py --update-data --fecha-sorteo 2025-08-17 --numeros-sorteo "7,14,21,28,35,39" --backup-data

# 3. Verificar actualización
python main.py --data-info
```

## 🎯 **Ventajas de la Integración**

### **Antes (Scripts Separados):**
```bash
python update_sorteo.py --fecha 2025-08-16 --numeros "1,2,3,4,5,6" --backup
```

### **Ahora (Integrado):**
```bash
python main.py --update-data --fecha-sorteo 2025-08-16 --numeros-sorteo "1,2,3,4,5,6" --backup-data
```

## ✅ **Beneficios:**

1. **🔄 Unificado**: Todo desde un solo comando
2. **🛡️ Consistente**: Mismo logging y manejo de errores
3. **⚡ Eficiente**: No duplicación de inicialización
4. **🔧 Mantenible**: Código centralizado
5. **📊 Integrado**: Usa el mismo sistema de datos
6. **🎯 Robusto**: Validaciones completas

## 📁 **Archivos Afectados**

### **Modificados:**
- ✅ `main.py` - Integración completa
- ✅ Argumentos agregados al parser
- ✅ Funcionalidad integrada en función principal

### **Preservados:**
- ✅ `update_sorteo.py` - Mantiene funcionalidad independiente
- ✅ `update_historical_data.py` - Disponible para casos específicos
- ✅ `modules/data_manager.py` - Sin cambios, usado por ambos

## 🚀 **Estado: COMPLETAMENTE INTEGRADO**

La funcionalidad de actualización de datos está **100% integrada** en el sistema principal OMEGA PRO AI y lista para uso en producción.

---
*Integración completada: 2025-08-16*  
*Versión: OMEGA PRO AI v10.1*