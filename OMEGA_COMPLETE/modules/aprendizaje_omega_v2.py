#!/usr/bin/env python3
"""
Aprendizaje OMEGA v2.0 - Motor Adaptativo Central de OMEGA PRO AI
Sistema que se ejecuta después de cada sorteo, analiza rendimiento, refuerza patrones exitosos,
ajusta pesos de modelos, penaliza estructuras ineficientes, y guarda log de aprendizaje.
"""

import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

# Almacenamiento global de patrones y pesos (en memoria y persistente)
PATRONES_REFUERZOS = defaultdict(int)
PATRONES_PENALIZADOS = defaultdict(int)
PESOS_MODELOS_DINAMICOS = {
    "lstm_v2": 1.0,
    "transformer": 1.0,
    "clustering": 1.0,
    "montecarlo": 1.0,
    "genetic": 1.0,
    "gboost": 1.0,
    "ensemble_ai": 1.2
}

# Configuración dinámica del sistema
CONFIGURACION_DINAMICA = {
    "score_minimo": 26.0,
    "filtro_agresividad": 1.0,
    "modo_asalto": False,
    "ghost_rng_activo": False,
    "refuerzo_clustering": False,
    "boost_frecuencias": False
}

# Funciones principales del motor adaptativo

def calcular_aciertos(combinacion: List[int], resultado_oficial: List[int]) -> int:
    """Calcula aciertos entre combinación predicha y resultado oficial"""
    return len(set(combinacion) & set(resultado_oficial))

def extraer_patron(combinacion: List[int]) -> Dict[str, Any]:
    """Extrae patrón estructural de una combinación"""
    sorted_combo = sorted(combinacion)
    
    # Análisis de décadas (0, 1, 2, 3 = números 1-10, 11-20, 21-30, 31-40)
    decadas = Counter([num // 10 for num in combinacion if num > 0])
    
    # Análisis de paridad
    pares = sum(1 for num in combinacion if num % 2 == 0)
    impares = 6 - pares
    
    # Análisis de gaps (saltos entre números consecutivos)
    gaps = [sorted_combo[i+1] - sorted_combo[i] for i in range(5)]
    gap_promedio = np.mean(gaps)
    gap_max = max(gaps)
    
    # Análisis de suma y rango
    suma_total = sum(combinacion)
    rango_total = max(combinacion) - min(combinacion)
    
    # Análisis de zonas (1-13, 14-26, 27-40)
    zona_baja = sum(1 for num in combinacion if 1 <= num <= 13)
    zona_media = sum(1 for num in combinacion if 14 <= num <= 26)
    zona_alta = sum(1 for num in combinacion if 27 <= num <= 40)
    
    return {
        "decadas": dict(decadas),
        "pares": pares,
        "impares": impares,
        "suma": suma_total,
        "rango": rango_total,
        "gap_promedio": gap_promedio,
        "gap_max": gap_max,
        "zona_baja": zona_baja,
        "zona_media": zona_media,
        "zona_alta": zona_alta,
        "perfil": clasificar_perfil_combinacion(combinacion)
    }

def clasificar_perfil_combinacion(combinacion: List[int]) -> str:
    """Clasifica el perfil de una combinación (A, B, C)"""
    suma = sum(combinacion)
    rango = max(combinacion) - min(combinacion)
    
    # Perfil A: Suma baja-media, rango moderado
    if 80 <= suma <= 140 and 120 <= rango <= 200:
        return "A"
    # Perfil C: Suma muy alta o muy baja, rango extremo
    elif suma < 80 or suma > 180 or rango < 100 or rango > 250:
        return "C"
    # Perfil B: Moderado, balanceado
    else:
        return "B"

def reforzar_patron(patron: Dict[str, Any], fuerza: float = 1.0):
    """Refuerza un patrón exitoso observado"""
    clave_patron = f"perfil:{patron.get('perfil')}_dec:{patron.get('decadas')}_pares:{patron.get('pares')}_zona:{patron.get('zona_baja')}-{patron.get('zona_media')}-{patron.get('zona_alta')}"
    
    PATRONES_REFUERZOS[clave_patron] += fuerza
    
    # Ajustar configuración dinámica basada en el patrón
    if patron.get('perfil') == 'A':
        CONFIGURACION_DINAMICA['refuerzo_clustering'] = True
    elif patron.get('perfil') == 'C':
        CONFIGURACION_DINAMICA['ghost_rng_activo'] = True
    
    if patron.get('suma', 0) > 150:
        CONFIGURACION_DINAMICA['boost_frecuencias'] = True
    
    logger.info(f"✅ Patrón reforzado (fuerza: {fuerza}): {clave_patron}")

def penalizar_patron(patron: Dict[str, Any], severidad: float = 1.0):
    """Penaliza un patrón ineficiente"""
    clave_patron = f"perfil:{patron.get('perfil')}"
    
    PATRONES_PENALIZADOS[clave_patron] += severidad
    
    # Ajustar configuración para evitar patrones penalizados
    if patron.get('perfil') == 'A' and severidad > 0.5:
        CONFIGURACION_DINAMICA['filtro_agresividad'] *= 1.2
    
    logger.info(f"🚫 Patrón penalizado (severidad: {severidad}): {clave_patron}")

def ajustar_pesos_modelos(rendimiento_modelos: Dict[str, float], aciertos_combinaciones: List[int]) -> Dict[str, float]:
    """Ajusta dinámicamente los pesos de los modelos según su rendimiento"""
    
    logger.info("⚙️ Ajustando pesos de modelos basado en rendimiento...")
    
    promedio_aciertos = np.mean(aciertos_combinaciones) if aciertos_combinaciones else 0
    max_aciertos = max(aciertos_combinaciones) if aciertos_combinaciones else 0
    
    # Factor de ajuste basado en rendimiento general
    if max_aciertos >= 5:
        factor_global = 1.3  # Refuerzo fuerte si hubo 5+ aciertos
    elif max_aciertos >= 3:
        factor_global = 1.1  # Refuerzo moderado si hubo 3-4 aciertos
    elif promedio_aciertos < 1.5:
        factor_global = 0.8  # Penalización si promedio muy bajo
    else:
        factor_global = 1.0  # Sin cambios
    
    nuevos_pesos = {}
    
    for modelo, score in rendimiento_modelos.items():
        peso_actual = PESOS_MODELOS_DINAMICOS.get(modelo, 1.0)
        
        # Ajuste específico por modelo basado en score
        if score > 28:
            ajuste_especifico = 1.15  # Buen score
        elif score > 25:
            ajuste_especifico = 1.05  # Score decente
        elif score < 22:
            ajuste_especifico = 0.9   # Score bajo
        else:
            ajuste_especifico = 1.0   # Score neutral
        
        # Combinar factor global y específico
        ajuste_total = factor_global * ajuste_especifico
        nuevo_peso = peso_actual * ajuste_total
        
        # Limitar pesos entre 0.3 y 2.5
        nuevo_peso = max(0.3, min(2.5, nuevo_peso))
        
        PESOS_MODELOS_DINAMICOS[modelo] = round(nuevo_peso, 2)
        nuevos_pesos[modelo] = nuevo_peso
        
        logger.info(f"🔧 {modelo}: {peso_actual:.2f} → {nuevo_peso:.2f} (score: {score:.1f})")
    
    return nuevos_pesos

def activar_modo_asalto(promedio_aciertos: float, max_aciertos: int):
    """Activa modo asalto cuando el rendimiento es muy bueno"""
    if max_aciertos >= 4 or promedio_aciertos >= 2.5:
        CONFIGURACION_DINAMICA['modo_asalto'] = True
        CONFIGURACION_DINAMICA['score_minimo'] = 24.0  # Más permisivo
        CONFIGURACION_DINAMICA['filtro_agresividad'] = 0.8  # Menos filtros
        logger.info("🔥 MODO ASALTO ACTIVADO - Configuración optimizada para ataque")
    else:
        CONFIGURACION_DINAMICA['modo_asalto'] = False
        CONFIGURACION_DINAMICA['score_minimo'] = 26.0  # Más restrictivo
        CONFIGURACION_DINAMICA['filtro_agresividad'] = 1.0  # Filtros normales

def ajustar_configuracion_dinamica(perfil_real: str, regime_actual: str, promedio_aciertos: float):
    """Ajusta la configuración dinámica del sistema basada en contexto"""
    
    # Ajustes basados en perfil real del sorteo
    if perfil_real == "A":
        CONFIGURACION_DINAMICA['refuerzo_clustering'] = True
        PESOS_MODELOS_DINAMICOS['clustering'] *= 1.1
    elif perfil_real == "C":
        CONFIGURACION_DINAMICA['ghost_rng_activo'] = True
        PESOS_MODELOS_DINAMICOS['genetic'] *= 1.1
    
    # Ajustes basados en régimen RNG
    if regime_actual == "high_frequency":
        CONFIGURACION_DINAMICA['boost_frecuencias'] = True
        PESOS_MODELOS_DINAMICOS['lstm_v2'] *= 1.15
    elif regime_actual == "low_frequency":
        CONFIGURACION_DINAMICA['ghost_rng_activo'] = True
        PESOS_MODELOS_DINAMICOS['montecarlo'] *= 1.1
    
    # Ajustes basados en rendimiento
    if promedio_aciertos < 1.0:
        CONFIGURACION_DINAMICA['filtro_agresividad'] = 0.7  # Menos filtros
        CONFIGURACION_DINAMICA['score_minimo'] = 23.0      # Más permisivo
        logger.info("⚠️ Rendimiento bajo detectado - Relajando filtros")

class OmegaLearningSystem:
    """Sistema de Aprendizaje Adaptativo OMEGA v2.0"""
    
    def __init__(self, log_directory: str = "logs", config_file: str = "config/omega_adaptive.json"):
        self.log_directory = log_directory
        self.config_file = config_file
        self.sorteo_history = []
        
        # Crear directorio de logs
        os.makedirs(log_directory, exist_ok=True)
        
        # Cargar configuración existente si existe
        self._cargar_configuracion()
        
        logger.info("🧠 Sistema de Aprendizaje OMEGA v2.0 inicializado")
        logger.info(f"   Logs: {log_directory}, Config: {config_file}")
    
    def _cargar_configuracion(self):
        """Carga configuración existente desde archivo"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    
                # Actualizar configuración global
                CONFIGURACION_DINAMICA.update(config_data.get('configuracion_dinamica', {}))
                PESOS_MODELOS_DINAMICOS.update(config_data.get('pesos_modelos', {}))
                
                logger.info("📂 Configuración adaptativa cargada desde archivo")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo cargar configuración: {e}")
    
    def _guardar_configuracion(self):
        """Guarda configuración actual a archivo"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            config_data = {
                'configuracion_dinamica': CONFIGURACION_DINAMICA,
                'pesos_modelos': PESOS_MODELOS_DINAMICOS,
                'patrones_refuerzos': dict(PATRONES_REFUERZOS),
                'patrones_penalizados': dict(PATRONES_PENALIZADOS),
                'ultima_actualizacion': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
            logger.info(f"💾 Configuración guardada en {self.config_file}")
        except Exception as e:
            logger.error(f"❌ Error guardando configuración: {e}")
    
    def aprendizaje_post_sorteo(self,
                              combinaciones: List[Dict[str, Any]],
                              resultado_oficial: List[int],
                              modelos_scores: Dict[str, float],
                              perfil_real: str = "B",
                              regime_actual: str = "moderate",
                              fecha_sorteo: datetime = None) -> Dict[str, Any]:
        """
        🧠 FUNCIÓN PRINCIPAL: Ejecuta aprendizaje adaptativo post-sorteo
        
        Esta función analiza el rendimiento, refuerza patrones exitosos,
        ajusta pesos de modelos y guarda el log de aprendizaje.
        """
        
        if fecha_sorteo is None:
            fecha_sorteo = datetime.now()
        
        logger.info(f"🎯 Iniciando aprendizaje post-sorteo para {fecha_sorteo.strftime('%Y-%m-%d')}")
        logger.info(f"   Resultado oficial: {' - '.join(map(str, resultado_oficial))}")
        logger.info(f"   Combinaciones analizadas: {len(combinaciones)}")
        
        # 1. EVALUACIÓN DE ACIERTOS
        aciertos_por_combinacion = []
        combinaciones_exitosas = []
        combinaciones_analisis = []
        
        for i, comb_data in enumerate(combinaciones):
            if isinstance(comb_data, dict):
                combinacion = comb_data.get('combination', comb_data.get('combinacion', []))
                score = comb_data.get('score', 0)
                source = comb_data.get('source', 'unknown')
            else:
                combinacion = comb_data  # Asumimos que es una lista directa
                score = 0
                source = 'unknown'
            
            aciertos = calcular_aciertos(combinacion, resultado_oficial)
            aciertos_por_combinacion.append(aciertos)
            
            combinaciones_analisis.append({
                'combinacion': combinacion,
                'aciertos': aciertos,
                'score': score,
                'source': source,
                'patron': extraer_patron(combinacion)
            })
            
            # Identificar combinaciones exitosas (3+ aciertos)
            if aciertos >= 3:
                combinaciones_exitosas.append({
                    'combinacion': combinacion,
                    'aciertos': aciertos,
                    'patron': extraer_patron(combinacion)
                })
        
        # 2. MÉTRICAS GENERALES
        promedio_aciertos = np.mean(aciertos_por_combinacion) if aciertos_por_combinacion else 0
        max_aciertos = max(aciertos_por_combinacion) if aciertos_por_combinacion else 0
        total_aciertos = sum(aciertos_por_combinacion)
        
        logger.info(f"📊 Análisis de rendimiento:")
        logger.info(f"   • Promedio de aciertos: {promedio_aciertos:.2f}")
        logger.info(f"   • Máximo aciertos: {max_aciertos}")
        logger.info(f"   • Combinaciones exitosas (3+): {len(combinaciones_exitosas)}")
        
        # 3. REFORZAMIENTO DE PATRONES EXITOSOS
        patrones_reforzados = []
        for comb_exitosa in combinaciones_exitosas:
            patron = comb_exitosa['patron']
            fuerza_refuerzo = comb_exitosa['aciertos'] / 6.0  # Fuerza proporcional a aciertos
            
            reforzar_patron(patron, fuerza_refuerzo)
            patrones_reforzados.append({
                'patron': patron,
                'aciertos': comb_exitosa['aciertos'],
                'fuerza': fuerza_refuerzo
            })
        
        # 4. PENALIZACIÓN DE PATRONES INEFICIENTES
        patrones_penalizados = []
        if promedio_aciertos < 1.5:
            # Penalizar patrones de combinaciones con 0 aciertos
            for analisis in combinaciones_analisis:
                if analisis['aciertos'] == 0:
                    patron = analisis['patron']
                    severidad = 0.5  # Penalización moderada
                    
                    penalizar_patron(patron, severidad)
                    patrones_penalizados.append({
                        'patron': patron,
                        'severidad': severidad
                    })
        
        # 5. AJUSTE DE PESOS DE MODELOS
        nuevos_pesos = ajustar_pesos_modelos(modelos_scores, aciertos_por_combinacion)
        
        # 6. ACTIVACIÓN DE MODO ASALTO
        activar_modo_asalto(promedio_aciertos, max_aciertos)
        
        # 7. AJUSTES DE CONFIGURACIÓN DINÁMICA
        ajustar_configuracion_dinamica(perfil_real, regime_actual, promedio_aciertos)
        
        # 8. ANÁLISIS DE PERFIL DEL RESULTADO OFICIAL
        patron_resultado = extraer_patron(resultado_oficial)
        perfil_calculado = clasificar_perfil_combinacion(resultado_oficial)
        
        # 9. CREACIÓN DEL LOG DE APRENDIZAJE
        log_aprendizaje = {
            "metadata": {
                "fecha_sorteo": fecha_sorteo.strftime("%Y-%m-%d"),
                "timestamp_procesamiento": datetime.now().isoformat(),
                "version_sistema": "OMEGA v2.0"
            },
            "resultado_sorteo": {
                "combinacion": resultado_oficial,
                "perfil_real": perfil_real,
                "perfil_calculado": perfil_calculado,
                "patron": patron_resultado,
                "regime_rng": regime_actual
            },
            "rendimiento_predicciones": {
                "total_combinaciones": len(combinaciones),
                "promedio_aciertos": round(promedio_aciertos, 2),
                "maximo_aciertos": max_aciertos,
                "total_aciertos": total_aciertos,
                "combinaciones_exitosas": len(combinaciones_exitosas),
                "tasa_exito": len(combinaciones_exitosas) / len(combinaciones) if combinaciones else 0
            },
            "aprendizaje_realizado": {
                "patrones_reforzados": len(patrones_reforzados),
                "patrones_penalizados": len(patrones_penalizados),
                "modelos_ajustados": len(nuevos_pesos),
                "modo_asalto_activo": CONFIGURACION_DINAMICA['modo_asalto'],
                "configuracion_modificada": True
            },
            "detalles_refuerzos": patrones_reforzados[:5],  # Primeros 5
            "detalles_penalizaciones": patrones_penalizados[:3],  # Primeros 3
            "pesos_modelos_actualizados": nuevos_pesos,
            "configuracion_actual": CONFIGURACION_DINAMICA.copy(),
            "rendimiento_por_fuente": self._analizar_rendimiento_por_fuente(combinaciones_analisis)
        }
        
        # 10. GUARDAR LOG DE APRENDIZAJE
        log_filename = f"{self.log_directory}/aprendizaje_omega_{fecha_sorteo.strftime('%Y%m%d')}.json"
        
        try:
            with open(log_filename, 'w', encoding='utf-8') as f:
                json.dump(log_aprendizaje, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📚 Log de aprendizaje guardado en: {log_filename}")
        except Exception as e:
            logger.error(f"❌ Error guardando log: {e}")
        
        # 11. GUARDAR CONFIGURACIÓN ACTUALIZADA
        self._guardar_configuracion()
        
        # 12. AGREGAR AL HISTORIAL
        self.sorteo_history.append({
            'fecha': fecha_sorteo,
            'promedio_aciertos': promedio_aciertos,
            'max_aciertos': max_aciertos,
            'adaptaciones': len(patrones_reforzados) + len(patrones_penalizados)
        })
        
        # Mantener historial limitado
        if len(self.sorteo_history) > 50:
            self.sorteo_history = self.sorteo_history[-50:]
        
        # 13. RESUMEN FINAL
        logger.info("✅ Aprendizaje post-sorteo completado")
        logger.info(f"   • Refuerzos aplicados: {len(patrones_reforzados)}")
        logger.info(f"   • Penalizaciones aplicadas: {len(patrones_penalizados)}")
        logger.info(f"   • Modelos reajustados: {len(nuevos_pesos)}")
        logger.info(f"   • Modo asalto: {'🔥 ACTIVO' if CONFIGURACION_DINAMICA['modo_asalto'] else '🔒 INACTIVO'}")
        
        return log_aprendizaje
    
    def _analizar_rendimiento_por_fuente(self, combinaciones_analisis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza rendimiento agrupado por fuente/modelo"""
        
        rendimiento_por_fuente = defaultdict(list)
        
        for analisis in combinaciones_analisis:
            source = analisis.get('source', 'unknown')
            aciertos = analisis.get('aciertos', 0)
            rendimiento_por_fuente[source].append(aciertos)
        
        resumen = {}
        for source, aciertos_list in rendimiento_por_fuente.items():
            resumen[source] = {
                'count': len(aciertos_list),
                'promedio': round(np.mean(aciertos_list), 2),
                'maximo': max(aciertos_list),
                'total': sum(aciertos_list)
            }
        
        return resumen

# Funciones de utilidad para integración

def create_omega_learning_system_v2(log_directory: str = "logs") -> OmegaLearningSystem:
    """Crea sistema de aprendizaje OMEGA v2.0"""
    return OmegaLearningSystem(log_directory=log_directory)

def ejecutar_aprendizaje_post_sorteo(combinaciones: List[Dict[str, Any]],
                                   resultado_oficial: List[int],
                                   modelos_scores: Dict[str, float] = None,
                                   perfil_real: str = "B",
                                   regime_actual: str = "moderate") -> Dict[str, Any]:
    """
    🧠 FUNCIÓN PRINCIPAL PARA LLAMAR DESDE MAIN.PY
    
    Esta es la función que se debe llamar desde el sistema principal
    después de cada sorteo para ejecutar el aprendizaje adaptativo.
    """
    
    # Usar scores por defecto si no se proporcionan
    if modelos_scores is None:
        modelos_scores = {
            "lstm_v2": 26.5,
            "transformer": 27.0,
            "clustering": 25.8,
            "montecarlo": 26.2,
            "genetic": 25.5
        }
    
    # Crear sistema si no existe
    learning_system = create_omega_learning_system_v2()
    
    # Ejecutar aprendizaje
    resultado = learning_system.aprendizaje_post_sorteo(
        combinaciones=combinaciones,
        resultado_oficial=resultado_oficial,
        modelos_scores=modelos_scores,
        perfil_real=perfil_real,
        regime_actual=regime_actual
    )
    
    return resultado

def obtener_configuracion_aprendida() -> Dict[str, Any]:
    """Obtiene la configuración actual aprendida por el sistema"""
    return {
        'pesos_modelos': PESOS_MODELOS_DINAMICOS.copy(),
        'configuracion_dinamica': CONFIGURACION_DINAMICA.copy(),
        'patrones_reforzados': dict(PATRONES_REFUERZOS),
        'patrones_penalizados': dict(PATRONES_PENALIZADOS)
    }

def aplicar_pesos_aprendidos_a_sistema(config_file: str = "config/pesos_modelos.json"):
    """Aplica los pesos aprendidos al archivo de configuración del sistema"""
    
    try:
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        # Actualizar archivo de pesos
        with open(config_file, 'w') as f:
            json.dump(PESOS_MODELOS_DINAMICOS, f, indent=2)
        
        logger.info(f"✅ Pesos actualizados en {config_file}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error actualizando pesos: {e}")
        return False

if __name__ == "__main__":
    # Demo del sistema de aprendizaje OMEGA v2.0
    print("🧠 Demo Sistema de Aprendizaje OMEGA v2.0")
    print("="*60)
    
    # Simular combinaciones generadas
    combinaciones_test = [
        {"combination": [5, 12, 18, 25, 31, 38], "score": 27.5, "source": "lstm_v2"},
        {"combination": [3, 15, 22, 28, 33, 40], "score": 26.8, "source": "transformer"},
        {"combination": [1, 14, 19, 26, 32, 39], "score": 25.2, "source": "clustering"},
        {"combination": [7, 16, 23, 29, 35, 37], "score": 26.1, "source": "montecarlo"},
        {"combination": [9, 13, 20, 27, 34, 36], "score": 24.8, "source": "genetic"}
    ]
    
    # Simular resultado oficial (con algunos aciertos para demo)
    resultado_oficial = [5, 15, 22, 25, 35, 38]  # 4 aciertos con primera combinación
    
    # Simular scores de modelos
    modelos_scores = {
        "lstm_v2": 27.5,
        "transformer": 26.8,
        "clustering": 25.2,
        "montecarlo": 26.1,
        "genetic": 24.8
    }
    
    print(f"📊 Datos de prueba:")
    print(f"   • Combinaciones: {len(combinaciones_test)}")
    print(f"   • Resultado oficial: {' - '.join(map(str, resultado_oficial))}")
    print(f"   • Modelos evaluados: {len(modelos_scores)}")
    
    print(f"\n🎯 Ejecutando aprendizaje post-sorteo...")
    
    # Ejecutar aprendizaje
    resultado = ejecutar_aprendizaje_post_sorteo(
        combinaciones=combinaciones_test,
        resultado_oficial=resultado_oficial,
        modelos_scores=modelos_scores,
        perfil_real="A",
        regime_actual="high_frequency"
    )
    
    print(f"\n✅ Aprendizaje completado:")
    print(f"   • Combinaciones exitosas: {resultado['rendimiento_predicciones']['combinaciones_exitosas']}")
    print(f"   • Promedio aciertos: {resultado['rendimiento_predicciones']['promedio_aciertos']}")
    print(f"   • Máximo aciertos: {resultado['rendimiento_predicciones']['maximo_aciertos']}")
    print(f"   • Patrones reforzados: {resultado['aprendizaje_realizado']['patrones_reforzados']}")
    print(f"   • Modelos reajustados: {resultado['aprendizaje_realizado']['modelos_ajustados']}")
    print(f"   • Modo asalto: {'🔥 ACTIVO' if resultado['aprendizaje_realizado']['modo_asalto_activo'] else '🔒 INACTIVO'}")
    
    print(f"\n🔧 Pesos de modelos actualizados:")
    for modelo, peso in resultado['pesos_modelos_actualizados'].items():
        print(f"   • {modelo}: {peso:.2f}")
    
    print(f"\n⚙️ Configuración dinámica:")
    config = resultado['configuracion_actual']
    print(f"   • Score mínimo: {config['score_minimo']}")
    print(f"   • Agresividad filtros: {config['filtro_agresividad']}")
    print(f"   • Ghost RNG: {'🟢' if config['ghost_rng_activo'] else '🔴'}")
    print(f"   • Refuerzo clustering: {'🟢' if config['refuerzo_clustering'] else '🔴'}")
    
    print(f"\n🎉 Demo completado - El sistema ha aprendido de este sorteo!")
    print(f"\n📋 Para integrar con main.py, usa:")
    print(f"from modules.aprendizaje_omega_v2 import ejecutar_aprendizaje_post_sorteo")
    print(f"resultado = ejecutar_aprendizaje_post_sorteo(combinaciones, resultado_oficial, modelos_scores)")
