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
from dataclasses import dataclass, asdict
from enum import Enum
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

class AccuracyLevel(Enum):
    """Niveles de precisión de predicciones"""
    EXCELLENT = "excellent"      # 5-6 aciertos
    GOOD = "good"               # 3-4 aciertos
    AVERAGE = "average"         # 1-2 aciertos
    POOR = "poor"              # 0 aciertos

class LearningAction(Enum):
    """Acciones de aprendizaje disponibles"""
    INCREASE_WEIGHT = "increase_weight"
    DECREASE_WEIGHT = "decrease_weight"
    ADJUST_FILTER = "adjust_filter"
    CHANGE_STRATEGY = "change_strategy"
    MODIFY_SVI = "modify_svi"
    ACTIVATE_BOOST = "activate_boost"

@dataclass
class SorteoResult:
    """Resultado de un sorteo para aprendizaje"""
    fecha: datetime
    combinacion_ganadora: List[int]
    combinaciones_predichas: List[List[int]]
    modelo_weights: Dict[str, float]
    filtros_activos: Dict[str, Any]
    svi_profile: str
    aciertos_por_combinacion: List[int]
    accuracy_level: AccuracyLevel
    contexto: Dict[str, Any]

@dataclass
class LearningRule:
    """Regla de aprendizaje"""
    condition: str
    action: LearningAction
    target: str
    adjustment: float
    confidence: float
    description: str

@dataclass
class AdaptiveConfig:
    """Configuración adaptativa del sistema"""
    model_weights: Dict[str, float]
    filter_params: Dict[str, Any]
    generation_params: Dict[str, Any]
    svi_adjustments: Dict[str, float]
    boost_activations: Dict[str, bool]
    learning_rate: float
    last_updated: datetime

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
    
    def obtener_configuracion_para_prediccion(self) -> Dict[str, Any]:
        """Obtiene la configuración actual optimizada para usar en predicción"""
        
        return {
            'pesos_modelos': PESOS_MODELOS_DINAMICOS.copy(),
            'configuracion_dinamica': CONFIGURACION_DINAMICA.copy(),
            'patrones_reforzados': dict(PATRONES_REFUERZOS),
            'patrones_penalizados': dict(PATRONES_PENALIZADOS),
            'timestamp': datetime.now().isoformat()
        }
    
    def aplicar_configuracion_a_sistema(self, sistema_omega) -> Dict[str, Any]:
        """Aplica la configuración adaptativa aprendida al sistema principal"""
        
        cambios_aplicados = []
        
        try:
            # Aplicar pesos de modelos
            if hasattr(sistema_omega, 'consensus_engine'):
                # Actualizar pesos en el consensus engine
                for modelo, peso in PESOS_MODELOS_DINAMICOS.items():
                    if hasattr(sistema_omega.consensus_engine, 'model_weights'):
                        sistema_omega.consensus_engine.model_weights[modelo] = peso
                        cambios_aplicados.append(f"peso_{modelo}")
            
            # Aplicar configuración de score dinámico
            if hasattr(sistema_omega, 'score_dynamics'):
                if CONFIGURACION_DINAMICA['score_minimo'] != 26.0:
                    sistema_omega.score_dynamics.score_threshold = CONFIGURACION_DINAMICA['score_minimo']
                    cambios_aplicados.append("score_threshold")
            
            # Activar boosts si están configurados
            if CONFIGURACION_DINAMICA['ghost_rng_activo']:
                # Activar ghost RNG si está disponible
                cambios_aplicados.append("ghost_rng_boost")
            
            if CONFIGURACION_DINAMICA['refuerzo_clustering']:
                # Reforzar clustering si está disponible
                cambios_aplicados.append("clustering_boost")
            
            logger.info(f"🔧 Configuración aplicada al sistema: {len(cambios_aplicados)} cambios")
            
        except Exception as e:
            logger.error(f"❌ Error aplicando configuración: {e}")
        
        return {
            'cambios_aplicados': cambios_aplicados,
            'configuracion_actual': CONFIGURACION_DINAMICA.copy(),
            'pesos_actuales': PESOS_MODELOS_DINAMICOS.copy()
        }
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Obtiene resumen del aprendizaje realizado"""
        
        return {
            'total_sorteos_procesados': len(self.sorteo_history),
            'patrones_reforzados': len(PATRONES_REFUERZOS),
            'patrones_penalizados': len(PATRONES_PENALIZADOS),
            'configuracion_actual': CONFIGURACION_DINAMICA.copy(),
            'pesos_modelos_actuales': PESOS_MODELOS_DINAMICOS.copy(),
            'rendimiento_reciente': self.sorteo_history[-5:] if len(self.sorteo_history) >= 5 else self.sorteo_history,
            'modo_asalto_activo': CONFIGURACION_DINAMICA['modo_asalto']
        }

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
    Función de conveniencia para ejecutar aprendizaje post-sorteo
    
    Esta es la función principal que se debe llamar desde main.py o el sistema principal
    después de cada sorteo.
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
    
    # Mostrar configuración para aplicar
    print(f"\n📋 Configuración aprendida disponible para aplicar al sistema principal")
    config_aprendida = obtener_configuracion_aprendida()
    print(f"   • Patrones reforzados: {len(config_aprendida['patrones_reforzados'])}")
    print(f"   • Patrones penalizados: {len(config_aprendida['patrones_penalizados'])}")
    
    print(f"\n🎉 Demo completado - El sistema ha aprendido de este sorteo!")
                'pattern_filter': {'diversity_threshold': 0.7, 'weight': 1.0}
            },
            generation_params={
                'num_combinations': 30,
                'exploration_factor': 0.3,
                'exploitation_factor': 0.7,
                'diversity_weight': 0.5
            },
            svi_adjustments={
                'conservative_boost': 0.0,
                'aggressive_boost': 0.0,
                'balanced_preference': 1.0
            },
            boost_activations={
                'ghost_rng': False,
                'score_dynamics': False,
                'frequency_boost': False,
                'clustering_enhance': False
            },
            learning_rate=self.learning_rate,
            last_updated=datetime.now()
        )
    
    def _initialize_learning_rules(self) -> List[LearningRule]:
        """Inicializa reglas de aprendizaje"""
        return [
            # Reglas para modelos exitosos
            LearningRule(
                condition="accuracy >= 3 and model_performed_best",
                action=LearningAction.INCREASE_WEIGHT,
                target="best_model",
                adjustment=0.15,
                confidence=0.8,
                description="Aumentar peso del modelo con mejor rendimiento"
            ),
            
            # Reglas para modelos fallidos
            LearningRule(
                condition="accuracy == 0 and model_contributed_most",
                action=LearningAction.DECREASE_WEIGHT,
                target="worst_model",
                adjustment=-0.1,
                confidence=0.7,
                description="Reducir peso del modelo con peor rendimiento"
            ),
            
            # Reglas para filtros
            LearningRule(
                condition="accuracy < 2 and high_filter_rejection",
                action=LearningAction.ADJUST_FILTER,
                target="restrictive_filters",
                adjustment=-0.2,
                confidence=0.6,
                description="Relajar filtros si rechazan demasiado"
            ),
            
            # Reglas para estrategia
            LearningRule(
                condition="accuracy_trend_declining for 3 sorteos",
                action=LearningAction.CHANGE_STRATEGY,
                target="generation_strategy",
                adjustment=0.3,
                confidence=0.75,
                description="Cambiar estrategia si tendencia declinante"
            ),
            
            # Reglas para SVI
            LearningRule(
                condition="regime_changed and accuracy < average",
                action=LearningAction.MODIFY_SVI,
                target="svi_profile",
                adjustment=0.25,
                confidence=0.65,
                description="Ajustar SVI cuando cambia régimen"
            ),
            
            # Reglas para boosts
            LearningRule(
                condition="accuracy == 0 for 2 consecutive sorteos",
                action=LearningAction.ACTIVATE_BOOST,
                target="emergency_boost",
                adjustment=1.0,
                confidence=0.9,
                description="Activar boost de emergencia"
            )
        ]
    
    def process_sorteo_result(self, 
                            fecha: datetime,
                            combinacion_ganadora: List[int],
                            combinaciones_predichas: List[List[int]],
                            modelo_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Procesa resultado de sorteo y ejecuta aprendizaje"""
        
        logger.info(f"🎯 Procesando resultado del sorteo {fecha.strftime('%Y-%m-%d')}")
        
        # Calcular aciertos por combinación
        aciertos_por_combinacion = []
        for combo_pred in combinaciones_predichas:
            aciertos = len(set(combo_pred) & set(combinacion_ganadora))
            aciertos_por_combinacion.append(aciertos)
        
        # Determinar nivel de accuracy
        max_aciertos = max(aciertos_por_combinacion) if aciertos_por_combinacion else 0
        if max_aciertos >= 5:
            accuracy_level = AccuracyLevel.EXCELLENT
        elif max_aciertos >= 3:
            accuracy_level = AccuracyLevel.GOOD
        elif max_aciertos >= 1:
            accuracy_level = AccuracyLevel.AVERAGE
        else:
            accuracy_level = AccuracyLevel.POOR
        
        # Crear registro de resultado
        resultado = SorteoResult(
            fecha=fecha,
            combinacion_ganadora=combinacion_ganadora,
            combinaciones_predichas=combinaciones_predichas,
            modelo_weights=self.adaptive_config.model_weights.copy(),
            filtros_activos=self.adaptive_config.filter_params.copy(),
            svi_profile=modelo_config.get('svi_profile', 'default') if modelo_config else 'default',
            aciertos_por_combinacion=aciertos_por_combinacion,
            accuracy_level=accuracy_level,
            contexto=self._extract_context(combinacion_ganadora, combinaciones_predichas)
        )
        
        # Agregar a historia
        self.sorteo_history.append(resultado)
        if len(self.sorteo_history) > self.memory_size:
            self.sorteo_history.pop(0)
        
        # Ejecutar aprendizaje
        learning_actions = self._execute_learning(resultado)
        
        # Actualizar métricas
        self._update_performance_metrics()
        
        # Guardar estado
        self._save_learning_state()
        
        logger.info(f"✅ Aprendizaje completado: {len(learning_actions)} ajustes realizados")
        logger.info(f"   Max aciertos: {max_aciertos}, Nivel: {accuracy_level.value}")
        
        return {
            'sorteo_result': asdict(resultado),
            'learning_actions': learning_actions,
            'updated_config': asdict(self.adaptive_config),
            'performance_metrics': self.performance_metrics.copy(),
            'boost_status': self.boost_system.copy()
        }
    
    def _extract_context(self, ganadora: List[int], predichas: List[List[int]]) -> Dict[str, Any]:
        """Extrae contexto del sorteo para aprendizaje"""
        
        # Análisis de la combinación ganadora
        ganadora_sorted = sorted(ganadora)
        
        context = {
            'ganadora_sum': sum(ganadora),
            'ganadora_range': max(ganadora) - min(ganadora),
            'ganadora_gaps': [ganadora_sorted[i+1] - ganadora_sorted[i] for i in range(5)],
            'ganadora_pattern': self._detect_pattern(ganadora_sorted),
            
            # Análisis de predicciones
            'predichas_coverage': len(set().union(*predichas)) if predichas else 0,
            'predichas_overlap': self._calculate_overlap(predichas),
            'predichas_diversity': self._calculate_diversity(predichas),
            
            # Métricas de distribución
            'numbers_frequency': self._analyze_frequency(ganadora, predichas),
            'zone_analysis': self._analyze_zones(ganadora, predichas),
            
            # Contexto temporal
            'timestamp': datetime.now().isoformat(),
            'sorteo_count': len(self.sorteo_history) + 1
        }
        
        return context
    
    def _detect_pattern(self, combination: List[int]) -> str:
        """Detecta patrón en combinación"""
        gaps = [combination[i+1] - combination[i] for i in range(5)]
        
        if all(g <= 5 for g in gaps):
            return "clustered"
        elif any(g >= 15 for g in gaps):
            return "spaced"
        elif len(set(gaps)) <= 2:
            return "regular"
        else:
            return "random"
    
    def _calculate_overlap(self, predichas: List[List[int]]) -> float:
        """Calcula solapamiento entre predicciones"""
        if len(predichas) < 2:
            return 0.0
        
        total_overlap = 0
        comparisons = 0
        
        for i in range(len(predichas)):
            for j in range(i + 1, len(predichas)):
                overlap = len(set(predichas[i]) & set(predichas[j]))
                total_overlap += overlap
                comparisons += 1
        
        return total_overlap / (comparisons * 6) if comparisons > 0 else 0.0
    
    def _calculate_diversity(self, predichas: List[List[int]]) -> float:
        """Calcula diversidad de predicciones"""
        if not predichas:
            return 0.0
        
        all_numbers = set().union(*predichas)
        max_possible = 40  # Números del 1 al 40
        
        return len(all_numbers) / max_possible
    
    def _analyze_frequency(self, ganadora: List[int], predichas: List[List[int]]) -> Dict[str, Any]:
        """Analiza frecuencias de números"""
        
        # Frecuencia en predicciones
        pred_freq = {}
        for combo in predichas:
            for num in combo:
                pred_freq[num] = pred_freq.get(num, 0) + 1
        
        # Análisis de aciertos por frecuencia
        hits_by_freq = {}
        for num in ganadora:
            freq = pred_freq.get(num, 0)
            hits_by_freq[freq] = hits_by_freq.get(freq, 0) + 1
        
        return {
            'predicted_frequencies': pred_freq,
            'hits_by_frequency': hits_by_freq,
            'most_predicted': max(pred_freq.items(), key=lambda x: x[1]) if pred_freq else (0, 0),
            'least_predicted': min(pred_freq.items(), key=lambda x: x[1]) if pred_freq else (0, 0)
        }
    
    def _analyze_zones(self, ganadora: List[int], predichas: List[List[int]]) -> Dict[str, Any]:
        """Analiza distribución por zonas (1-10, 11-20, 21-30, 31-40)"""
        
        zones = {1: 0, 2: 0, 3: 0, 4: 0}  # Zona 1: 1-10, etc.
        
        def get_zone(num):
            return min(4, (num - 1) // 10 + 1)
        
        # Contar por zonas en ganadora
        ganadora_zones = {1: 0, 2: 0, 3: 0, 4: 0}
        for num in ganadora:
            zone = get_zone(num)
            ganadora_zones[zone] += 1
        
        # Contar por zonas en predicciones
        pred_zones = {1: 0, 2: 0, 3: 0, 4: 0}
        for combo in predichas:
            for num in combo:
                zone = get_zone(num)
                pred_zones[zone] += 1
        
        return {
            'ganadora_zones': ganadora_zones,
            'predicted_zones': pred_zones,
            'zone_accuracy': {
                zone: ganadora_zones[zone] / max(1, pred_zones[zone]) 
                for zone in range(1, 5)
            }
        }
    
    def _execute_learning(self, resultado: SorteoResult) -> List[Dict[str, Any]]:
        """Ejecuta algoritmo de aprendizaje"""
        
        learning_actions = []
        
        # Analizar tendencias recientes
        recent_results = self.sorteo_history[-5:] if len(self.sorteo_history) >= 5 else self.sorteo_history
        trend_analysis = self._analyze_trends(recent_results)
        
        # Aplicar reglas de aprendizaje
        for rule in self.learning_rules:
            if self._evaluate_condition(rule.condition, resultado, trend_analysis):
                action_result = self._apply_learning_action(rule, resultado, trend_analysis)
                if action_result:
                    learning_actions.append({
                        'rule': rule.description,
                        'action': rule.action.value,
                        'target': rule.target,
                        'adjustment': rule.adjustment,
                        'confidence': rule.confidence,
                        'result': action_result
                    })
        
        # Aprendizaje específico basado en accuracy
        accuracy_actions = self._learn_from_accuracy(resultado)
        learning_actions.extend(accuracy_actions)
        
        # Aprendizaje de patrones
        pattern_actions = self._learn_from_patterns(resultado)
        learning_actions.extend(pattern_actions)
        
        # Actualizar timestamp
        self.adaptive_config.last_updated = datetime.now()
        
        # Registrar en historial
        self.learning_history.append({
            'timestamp': datetime.now().isoformat(),
            'sorteo_fecha': resultado.fecha.isoformat(),
            'accuracy_level': resultado.accuracy_level.value,
            'actions_count': len(learning_actions),
            'actions': learning_actions
        })
        
        if len(self.learning_history) > self.memory_size:
            self.learning_history.pop(0)
        
        return learning_actions
    
    def _analyze_trends(self, recent_results: List[SorteoResult]) -> Dict[str, Any]:
        """Analiza tendencias en resultados recientes"""
        
        if not recent_results:
            return {'no_data': True}
        
        # Tendencia de accuracy
        accuracies = [max(r.aciertos_por_combinacion) if r.aciertos_por_combinacion else 0 
                     for r in recent_results]
        
        trend_analysis = {
            'accuracy_trend': 'stable',
            'avg_accuracy': np.mean(accuracies),
            'accuracy_variance': np.var(accuracies),
            'best_model_consistency': {},
            'pattern_changes': 0,
            'regime_stability': True
        }
        
        # Analizar tendencia
        if len(accuracies) >= 3:
            if accuracies[-1] > accuracies[-2] > accuracies[-3]:
                trend_analysis['accuracy_trend'] = 'improving'
            elif accuracies[-1] < accuracies[-2] < accuracies[-3]:
                trend_analysis['accuracy_trend'] = 'declining'
        
        # Consistencia de modelos
        model_performance = {}
        for result in recent_results:
            for model, weight in result.modelo_weights.items():
                if model not in model_performance:
                    model_performance[model] = []
                # Simular performance basado en accuracy y peso
                performance = max(result.aciertos_por_combinacion) * weight / sum(result.modelo_weights.values())
                model_performance[model].append(performance)
        
        # Calcular consistencia
        for model, performances in model_performance.items():
            if len(performances) >= 2:
                consistency = 1.0 - (np.std(performances) / (np.mean(performances) + 1e-10))
                trend_analysis['best_model_consistency'][model] = consistency
        
        return trend_analysis
    
    def _evaluate_condition(self, condition: str, resultado: SorteoResult, trends: Dict[str, Any]) -> bool:
        """Evalúa condición de regla de aprendizaje"""
        
        max_accuracy = max(resultado.aciertos_por_combinacion) if resultado.aciertos_por_combinacion else 0
        
        # Condiciones básicas de accuracy
        if "accuracy >= 3" in condition:
            if max_accuracy < 3:
                return False
        
        if "accuracy == 0" in condition:
            if max_accuracy != 0:
                return False
        
        if "accuracy < 2" in condition:
            if max_accuracy >= 2:
                return False
        
        # Condiciones de tendencias
        if "accuracy_trend_declining for 3 sorteos" in condition:
            if trends.get('accuracy_trend') != 'declining':
                return False
        
        # Condiciones de modelos
        if "model_performed_best" in condition:
            # Simplificación: asumimos que el modelo con mayor peso performó mejor
            best_model = max(resultado.modelo_weights.items(), key=lambda x: x[1])
            if best_model[1] <= 1.0:  # Peso no destacado
                return False
        
        if "model_contributed_most" in condition:
            # Similar pero para el que más contribuyó (independiente del resultado)
            return True  # Siempre hay un modelo que contribuye más
        
        # Condiciones de filtros
        if "high_filter_rejection" in condition:
            # Simulamos que si accuracy es baja, probablemente los filtros fueron muy restrictivos
            return max_accuracy < 2
        
        # Condiciones de régimen
        if "regime_changed" in condition:
            # Simplificación: asumimos cambio si hay cambio en patrón
            pattern = resultado.contexto.get('ganadora_pattern', 'random')
            return pattern != 'regular'  # Cambio detectado
        
        return True  # Default: condición cumplida
    
    def _apply_learning_action(self, rule: LearningRule, resultado: SorteoResult, trends: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica acción de aprendizaje"""
        
        action_result = {}
        
        if rule.action == LearningAction.INCREASE_WEIGHT:
            if rule.target == "best_model":
                best_model = max(resultado.modelo_weights.items(), key=lambda x: x[1])[0]
                old_weight = self.adaptive_config.model_weights[best_model]
                new_weight = min(2.0, old_weight + rule.adjustment)
                self.adaptive_config.model_weights[best_model] = new_weight
                
                action_result = {
                    'model': best_model,
                    'old_weight': old_weight,
                    'new_weight': new_weight,
                    'change': new_weight - old_weight
                }
        
        elif rule.action == LearningAction.DECREASE_WEIGHT:
            if rule.target == "worst_model":
                worst_model = min(resultado.modelo_weights.items(), key=lambda x: x[1])[0]
                old_weight = self.adaptive_config.model_weights[worst_model]
                new_weight = max(0.1, old_weight + rule.adjustment)  # adjustment es negativo
                self.adaptive_config.model_weights[worst_model] = new_weight
                
                action_result = {
                    'model': worst_model,
                    'old_weight': old_weight,
                    'new_weight': new_weight,
                    'change': new_weight - old_weight
                }
        
        elif rule.action == LearningAction.ADJUST_FILTER:
            if rule.target == "restrictive_filters":
                # Relajar filtros de rango y suma
                old_range_max = self.adaptive_config.filter_params['range_filter']['max']
                new_range_max = old_range_max * (1 + abs(rule.adjustment))
                self.adaptive_config.filter_params['range_filter']['max'] = new_range_max
                
                old_sum_range = self.adaptive_config.filter_params['sum_filter']['max'] - self.adaptive_config.filter_params['sum_filter']['min']
                new_sum_range = old_sum_range * (1 + abs(rule.adjustment))
                center = (self.adaptive_config.filter_params['sum_filter']['max'] + self.adaptive_config.filter_params['sum_filter']['min']) / 2
                
                self.adaptive_config.filter_params['sum_filter']['min'] = center - new_sum_range / 2
                self.adaptive_config.filter_params['sum_filter']['max'] = center + new_sum_range / 2
                
                action_result = {
                    'filter_type': 'range_and_sum',
                    'range_adjustment': new_range_max / old_range_max,
                    'sum_adjustment': new_sum_range / old_sum_range
                }
        
        elif rule.action == LearningAction.CHANGE_STRATEGY:
            if rule.target == "generation_strategy":
                # Aumentar exploración si accuracy baja
                old_exploration = self.adaptive_config.generation_params['exploration_factor']
                new_exploration = min(0.8, old_exploration + rule.adjustment)
                new_exploitation = 1.0 - new_exploration
                
                self.adaptive_config.generation_params['exploration_factor'] = new_exploration
                self.adaptive_config.generation_params['exploitation_factor'] = new_exploitation
                
                action_result = {
                    'old_exploration': old_exploration,
                    'new_exploration': new_exploration,
                    'strategy_shift': 'more_exploratory' if new_exploration > old_exploration else 'more_exploitative'
                }
        
        elif rule.action == LearningAction.MODIFY_SVI:
            if rule.target == "svi_profile":
                # Ajustar preferencias SVI
                if resultado.accuracy_level in [AccuracyLevel.POOR, AccuracyLevel.AVERAGE]:
                    # Aumentar agresividad si accuracy baja
                    old_aggressive = self.adaptive_config.svi_adjustments['aggressive_boost']
                    new_aggressive = min(1.0, old_aggressive + rule.adjustment)
                    self.adaptive_config.svi_adjustments['aggressive_boost'] = new_aggressive
                    
                    # Reducir conservativo
                    old_conservative = self.adaptive_config.svi_adjustments['conservative_boost']
                    new_conservative = max(0.0, old_conservative - rule.adjustment / 2)
                    self.adaptive_config.svi_adjustments['conservative_boost'] = new_conservative
                    
                    action_result = {
                        'svi_direction': 'more_aggressive',
                        'aggressive_boost': new_aggressive,
                        'conservative_boost': new_conservative
                    }
        
        elif rule.action == LearningAction.ACTIVATE_BOOST:
            if rule.target == "emergency_boost":
                # Activar múltiples boosts
                boosts_activated = []
                
                for boost_name, boost_config in self.boost_system.items():
                    if not boost_config['active']:
                        boost_config['active'] = True
                        boost_config['strength'] = 1.5  # Boost fuerte
                        boosts_activated.append(boost_name)
                        
                        # Reflejar en configuración adaptativa
                        self.adaptive_config.boost_activations[boost_name] = True
                
                action_result = {
                    'boosts_activated': boosts_activated,
                    'total_boosts': len(boosts_activated)
                }
        
        return action_result
    
    def _learn_from_accuracy(self, resultado: SorteoResult) -> List[Dict[str, Any]]:
        """Aprendizaje específico basado en nivel de accuracy"""
        
        actions = []
        max_accuracy = max(resultado.aciertos_por_combinacion) if resultado.aciertos_por_combinacion else 0
        
        # Aprendizaje para accuracy excelente
        if resultado.accuracy_level == AccuracyLevel.EXCELLENT:
            # Reforzar configuración actual
            for model in self.adaptive_config.model_weights:
                self.adaptive_config.model_weights[model] *= 1.05  # Pequeño refuerzo
                self.adaptive_config.model_weights[model] = min(2.0, self.adaptive_config.model_weights[model])
            
            actions.append({
                'type': 'excellence_reinforcement',
                'description': 'Reforzar configuración exitosa',
                'adjustment': 0.05
            })
        
        # Aprendizaje para accuracy pobre
        elif resultado.accuracy_level == AccuracyLevel.POOR:
            # Activar modo exploración
            old_exploration = self.adaptive_config.generation_params['exploration_factor']
            self.adaptive_config.generation_params['exploration_factor'] = min(0.7, old_exploration + 0.2)
            self.adaptive_config.generation_params['exploitation_factor'] = 1.0 - self.adaptive_config.generation_params['exploration_factor']
            
            actions.append({
                'type': 'poor_performance_adjustment',
                'description': 'Aumentar exploración por bajo rendimiento',
                'old_exploration': old_exploration,
                'new_exploration': self.adaptive_config.generation_params['exploration_factor']
            })
            
            # Activar boosts si están disponibles
            available_boosts = [name for name, config in self.boost_system.items() if not config['active']]
            if available_boosts:
                boost_to_activate = available_boosts[0]  # Activar el primero disponible
                self.boost_system[boost_to_activate]['active'] = True
                self.adaptive_config.boost_activations[boost_to_activate] = True
                
                actions.append({
                    'type': 'boost_activation',
                    'description': f'Activar boost {boost_to_activate}',
                    'boost': boost_to_activate
                })
        
        return actions
    
    def _learn_from_patterns(self, resultado: SorteoResult) -> List[Dict[str, Any]]:
        """Aprendizaje basado en patrones detectados"""
        
        actions = []
        pattern = resultado.contexto.get('ganadora_pattern', 'random')
        
        # Ajustes basados en patrón ganador
        if pattern == 'clustered':
            # Si ganó patrón agrupado, favorecer clustering
            old_weight = self.adaptive_config.model_weights.get('clustering', 1.0)
            new_weight = min(2.0, old_weight + 0.1)
            self.adaptive_config.model_weights['clustering'] = new_weight
            
            actions.append({
                'type': 'pattern_learning',
                'pattern': pattern,
                'model_adjusted': 'clustering',
                'old_weight': old_weight,
                'new_weight': new_weight
            })
        
        elif pattern == 'spaced':
            # Si ganó patrón espaciado, favorecer genetic/montecarlo
            for model in ['genetic', 'montecarlo']:
                old_weight = self.adaptive_config.model_weights.get(model, 1.0)
                new_weight = min(2.0, old_weight + 0.05)
                self.adaptive_config.model_weights[model] = new_weight
                
                actions.append({
                    'type': 'pattern_learning',
                    'pattern': pattern,
                    'model_adjusted': model,
                    'old_weight': old_weight,
                    'new_weight': new_weight
                })
        
        elif pattern == 'regular':
            # Si ganó patrón regular, favorecer transformer/lstm
            for model in ['transformer', 'lstm_v2']:
                old_weight = self.adaptive_config.model_weights.get(model, 1.0)
                new_weight = min(2.0, old_weight + 0.08)
                self.adaptive_config.model_weights[model] = new_weight
                
                actions.append({
                    'type': 'pattern_learning',
                    'pattern': pattern,
                    'model_adjusted': model,
                    'old_weight': old_weight,
                    'new_weight': new_weight
                })
        
        return actions
    
    def _update_performance_metrics(self):
        """Actualiza métricas de rendimiento"""
        
        if not self.sorteo_history:
            return
        
        # Métricas básicas
        self.performance_metrics['total_sorteos'] = len(self.sorteo_history)
        
        # Accuracy promedio
        all_accuracies = []
        for resultado in self.sorteo_history:
            max_accuracy = max(resultado.aciertos_por_combinacion) if resultado.aciertos_por_combinacion else 0
            all_accuracies.append(max_accuracy)
        
        self.performance_metrics['aciertos_promedio'] = np.mean(all_accuracies)
        
        # Tendencia de accuracy (últimos 10)
        recent_accuracies = all_accuracies[-10:] if len(all_accuracies) >= 10 else all_accuracies
        self.performance_metrics['tendencia_accuracy'] = recent_accuracies
        
        # Mejor y peor modelo (basado en pesos actuales)
        current_weights = self.adaptive_config.model_weights
        self.performance_metrics['mejor_modelo'] = max(current_weights.items(), key=lambda x: x[1])[0]
        self.performance_metrics['peor_modelo'] = min(current_weights.items(), key=lambda x: x[1])[0]
        
        # Ajustes realizados
        self.performance_metrics['ajustes_realizados'] = len(self.learning_history)
    
    def _save_learning_state(self):
        """Guarda estado de aprendizaje"""
        
        try:
            # Crear directorio si no existe
            os.makedirs('learning_states', exist_ok=True)
            
            # Preparar datos para guardar
            state_data = {
                'adaptive_config': asdict(self.adaptive_config),
                'performance_metrics': self.performance_metrics,
                'boost_system': self.boost_system,
                'recent_history': [asdict(r) for r in self.sorteo_history[-10:]],
                'recent_learning': self.learning_history[-20:],
                'timestamp': datetime.now().isoformat()
            }
            
            # Convertir datetime objects a strings
            def datetime_converter(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return obj
            
            # Guardar estado
            filename = f"learning_states/omega_learning_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(state_data, f, indent=2, default=datetime_converter)
            
            logger.debug(f"💾 Estado de aprendizaje guardado en {filename}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando estado de aprendizaje: {e}")
    
    def get_current_config(self) -> Dict[str, Any]:
        """Obtiene configuración actual adaptativa"""
        
        return {
            'model_weights': self.adaptive_config.model_weights.copy(),
            'filter_params': self.adaptive_config.filter_params.copy(),
            'generation_params': self.adaptive_config.generation_params.copy(),
            'svi_adjustments': self.adaptive_config.svi_adjustments.copy(),
            'boost_activations': self.adaptive_config.boost_activations.copy(),
            'learning_rate': self.adaptive_config.learning_rate,
            'last_updated': self.adaptive_config.last_updated.isoformat(),
            'performance_metrics': self.performance_metrics.copy()
        }
    
    def apply_config_to_system(self, omega_system) -> Dict[str, Any]:
        """Aplica configuración adaptativa al sistema OMEGA"""
        
        applied_changes = []
        
        try:
            # Aplicar pesos de modelos
            if hasattr(omega_system, 'model_weights'):
                omega_system.model_weights.update(self.adaptive_config.model_weights)
                applied_changes.append('model_weights')
            
            # Aplicar parámetros de filtros
            if hasattr(omega_system, 'filter_config'):
                omega_system.filter_config.update(self.adaptive_config.filter_params)
                applied_changes.append('filter_params')
            
            # Aplicar parámetros de generación
            if hasattr(omega_system, 'generation_config'):
                omega_system.generation_config.update(self.adaptive_config.generation_params)
                applied_changes.append('generation_params')
            
            # Activar boosts
            for boost_name, is_active in self.adaptive_config.boost_activations.items():
                if hasattr(omega_system, f'activate_{boost_name}') and is_active:
                    getattr(omega_system, f'activate_{boost_name}')()
                    applied_changes.append(f'boost_{boost_name}')
            
            logger.info(f"✅ Configuración adaptativa aplicada: {len(applied_changes)} cambios")
            
        except Exception as e:
            logger.error(f"❌ Error aplicando configuración: {e}")
        
        return {
            'applied_changes': applied_changes,
            'timestamp': datetime.now().isoformat(),
            'config_version': self.adaptive_config.last_updated.isoformat()
        }
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Obtiene resumen del sistema de aprendizaje"""
        
        summary = {
            'total_sorteos_procesados': len(self.sorteo_history),
            'total_ajustes_realizados': len(self.learning_history),
            'accuracy_promedio': self.performance_metrics.get('aciertos_promedio', 0.0),
            'mejor_modelo_actual': self.performance_metrics.get('mejor_modelo', ''),
            'boosts_activos': sum(1 for boost in self.boost_system.values() if boost['active']),
            'ultima_actualizacion': self.adaptive_config.last_updated.isoformat()
        }
        
        # Tendencias recientes
        if len(self.sorteo_history) >= 3:
            recent_accuracies = [max(r.aciertos_por_combinacion) if r.aciertos_por_combinacion else 0 
                               for r in self.sorteo_history[-3:]]
            
            if recent_accuracies[-1] > recent_accuracies[0]:
                summary['tendencia_reciente'] = 'mejorando'
            elif recent_accuracies[-1] < recent_accuracies[0]:
                summary['tendencia_reciente'] = 'empeorando'
            else:
                summary['tendencia_reciente'] = 'estable'
        else:
            summary['tendencia_reciente'] = 'insuficientes_datos'
        
        # Distribución de niveles de accuracy
        accuracy_distribution = {level.value: 0 for level in AccuracyLevel}
        for resultado in self.sorteo_history:
            accuracy_distribution[resultado.accuracy_level.value] += 1
        
        summary['distribucion_accuracy'] = accuracy_distribution
        
        return summary

# Funciones de utilidad
def create_omega_learning_system(memory_size: int = 100, learning_rate: float = 0.1) -> OmegaLearningSystem:
    """Crea sistema de aprendizaje OMEGA"""
    return OmegaLearningSystem(memory_size=memory_size, learning_rate=learning_rate)

def simulate_sorteo_learning(learning_system: OmegaLearningSystem, 
                           num_sorteos: int = 10) -> List[Dict[str, Any]]:
    """Simula aprendizaje con múltiples sorteos"""
    
    results = []
    
    for i in range(num_sorteos):
        # Simular sorteo
        fecha = datetime.now() - timedelta(days=num_sorteos - i)
        combinacion_ganadora = sorted(np.random.choice(range(1, 41), 6, replace=False).tolist())
        
        # Simular predicciones
        combinaciones_predichas = []
        for j in range(5):
            combo = sorted(np.random.choice(range(1, 41), 6, replace=False).tolist())
            combinaciones_predichas.append(combo)
        
        # Procesar resultado
        result = learning_system.process_sorteo_result(
            fecha=fecha,
            combinacion_ganadora=combinacion_ganadora,
            combinaciones_predichas=combinaciones_predichas
        )
        
        results.append(result)
    
    return results

if __name__ == "__main__":
    # Demo del sistema de aprendizaje
    print("🧠 Demo Sistema de Aprendizaje OMEGA")
    
    # Crear sistema
    learning_system = create_omega_learning_system()
    
    print(f"📊 Sistema inicializado con {len(learning_system.learning_rules)} reglas de aprendizaje")
    
    # Simular varios sorteos
    print(f"\n🎯 Simulando 5 sorteos con aprendizaje...")
    results = simulate_sorteo_learning(learning_system, num_sorteos=5)
    
    for i, result in enumerate(results, 1):
        sorteo = result['sorteo_result']
        actions = result['learning_actions']
        
        print(f"\nSorteo {i}:")
        print(f"   Ganadora: {' - '.join(map(str, sorteo['combinacion_ganadora']))}")
        print(f"   Max aciertos: {max(sorteo['aciertos_por_combinacion'])}")
        print(f"   Nivel: {sorteo['accuracy_level']}")
        print(f"   Ajustes: {len(actions)}")
        
        for action in actions[:2]:  # Mostrar primeros 2 ajustes
            print(f"     • {action['rule']}")
    
    # Resumen final
    summary = learning_system.get_learning_summary()
    print(f"\n📈 Resumen del aprendizaje:")
    print(f"   Sorteos procesados: {summary['total_sorteos_procesados']}")
    print(f"   Ajustes realizados: {summary['total_ajustes_realizados']}")
    print(f"   Accuracy promedio: {summary['accuracy_promedio']:.2f}")
    print(f"   Mejor modelo: {summary['mejor_modelo_actual']}")
    print(f"   Tendencia: {summary['tendencia_reciente']}")
    
    # Configuración actual
    config = learning_system.get_current_config()
    print(f"\n⚙️ Pesos de modelos actuales:")
    for model, weight in config['model_weights'].items():
        print(f"   {model}: {weight:.3f}")
