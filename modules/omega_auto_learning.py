#!/usr/bin/env python3
"""
🧠 OMEGA Auto Learning System - Sistema de Aprendizaje Automático
Mejora automáticamente la IA basándose en resultados reales
"""

import os
import json as json_module
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import logging
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

class OmegaAutoLearning:
    """Sistema de aprendizaje automático que mejora la IA con cada resultado"""
    
    def __init__(self):
        self.learning_data_path = "data/omega_learning_data.json"
        self.model_weights_path = "config/adaptive_model_weights.json"
        self.pattern_analysis_path = "data/pattern_analysis.json"
        
        # Configuración inicial
        self.learning_data = self._load_learning_data()
        self.model_weights = self._load_model_weights()
        self.pattern_analysis = self._load_pattern_analysis()
        
    def _load_learning_data(self) -> Dict:
        """Carga datos de aprendizaje histórico"""
        if os.path.exists(self.learning_data_path):
            with open(self.learning_data_path, 'r') as f:
                return json_module.load(f)
        return {
            "resultados_reales": [],
            "predicciones_historicas": [],
            "metricas_performance": {},
            "patrones_omitidos": [],
            "sesgos_detectados": {}
        }
    
    def _load_model_weights(self) -> Dict:
        """Carga pesos adaptativos de modelos"""
        if os.path.exists(self.model_weights_path):
            with open(self.model_weights_path, 'r') as f:
                return json_module.load(f)
        return {
            "consensus": 0.15,
            "ghost_rng": 0.12,
            "inverse_mining": 0.10,
            "lstm_v2": 0.08,
            "montecarlo": 0.08,
            "apriori": 0.12,
            "transformer_deep": 0.15,
            "clustering": 0.08,
            "genetico": 0.12
        }
    
    def _load_pattern_analysis(self) -> Dict:
        """Carga análisis de patrones"""
        if os.path.exists(self.pattern_analysis_path):
            with open(self.pattern_analysis_path, 'r') as f:
                return json_module.load(f)
        return {
            "numeros_subestimados": [],
            "numeros_sobreestimados": [],
            "rangos_debiles": [],
            "patrones_exitosos": [],
            "correlaciones_temporales": {}
        }
    
    def aprender_de_resultado(self, resultado_oficial: List[int], predicciones: List[Dict], 
                             fecha: str = None) -> Dict:
        """
        Aprende de un resultado oficial y ajusta la IA automáticamente
        
        Args:
            resultado_oficial: Lista de 6 números del sorteo oficial
            predicciones: Lista de predicciones generadas por OMEGA
            fecha: Fecha del sorteo (opcional)
            
        Returns:
            Dict con métricas de aprendizaje y ajustes realizados
        """
        if fecha is None:
            fecha = datetime.now().strftime("%Y-%m-%d")
            
        logger.info(f"🧠 Iniciando aprendizaje automático para {fecha}")
        logger.info(f"📊 Resultado oficial: {resultado_oficial}")
        
        # 1. Analizar performance de predicciones
        performance_analysis = self._analizar_performance(resultado_oficial, predicciones)
        
        # 2. Detectar sesgos y patrones omitidos
        bias_analysis = self._detectar_sesgos(resultado_oficial, predicciones)
        
        # 3. Ajustar pesos de modelos
        weight_adjustments = self._ajustar_pesos_modelos(performance_analysis)
        
        # 4. Identificar números subestimados/sobreestimados
        number_analysis = self._analizar_numeros_faltantes(resultado_oficial, predicciones)
        
        # 5. Actualizar datos de aprendizaje
        self._actualizar_datos_aprendizaje(resultado_oficial, predicciones, fecha, 
                                         performance_analysis, bias_analysis)
        
        # 6. Generar recomendaciones de mejora
        recommendations = self._generar_recomendaciones(performance_analysis, bias_analysis, 
                                                      number_analysis)
        
        # Guardar todo
        self._guardar_datos_aprendizaje()
        
        resultado_aprendizaje = {
            "fecha": fecha,
            "resultado_oficial": resultado_oficial,
            "total_predicciones": len(predicciones),
            "performance_analysis": performance_analysis,
            "bias_analysis": bias_analysis,
            "weight_adjustments": weight_adjustments,
            "number_analysis": number_analysis,
            "recommendations": recommendations,
            "learning_score": performance_analysis.get("learning_score", 0)
        }
        
        logger.info(f"✅ Aprendizaje completado. Score: {resultado_aprendizaje['learning_score']:.3f}")
        
        return resultado_aprendizaje
    
    def _analizar_performance(self, resultado_oficial: List[int], predicciones: List[Dict]) -> Dict:
        """Analiza el performance de cada modelo"""
        
        modelo_performance = defaultdict(lambda: {"aciertos": 0, "total": 0, "precision": 0})
        total_aciertos = 0
        total_posibles = 0
        
        for pred in predicciones:
            combination = pred.get("combination", [])
            source = pred.get("source", "unknown")
            
            # Contar aciertos para esta predicción
            aciertos = len(set(combination) & set(resultado_oficial))
            total_aciertos += aciertos
            total_posibles += 6
            
            # Actualizar stats por modelo
            modelo_performance[source]["aciertos"] += aciertos
            modelo_performance[source]["total"] += 6
            modelo_performance[source]["precision"] = (
                modelo_performance[source]["aciertos"] / modelo_performance[source]["total"]
            )
        
        # Calcular métricas generales
        precision_general = total_aciertos / total_posibles if total_posibles > 0 else 0
        expectativa_aleatoria = 1/6.67  # ~15%
        mejora_sobre_azar = precision_general - expectativa_aleatoria
        
        # Score de aprendizaje (0-1)
        learning_score = min(1.0, precision_general / 0.5)  # Normalizado a 50% máximo esperado
        
        return {
            "precision_general": precision_general,
            "expectativa_aleatoria": expectativa_aleatoria,
            "mejora_sobre_azar": mejora_sobre_azar,
            "learning_score": learning_score,
            "total_aciertos": total_aciertos,
            "total_posibles": total_posibles,
            "performance_por_modelo": dict(modelo_performance)
        }
    
    def _detectar_sesgos(self, resultado_oficial: List[int], predicciones: List[Dict]) -> Dict:
        """Detecta sesgos sistemáticos en las predicciones"""
        
        # Recopilar todos los números predichos
        numeros_predichos = []
        for pred in predicciones:
            numeros_predichos.extend(pred.get("combination", []))
        
        contador_predichos = Counter(numeros_predichos)
        numeros_no_predichos = set(range(1, 41)) - set(numeros_predichos)
        numeros_resultado_no_predichos = set(resultado_oficial) - set(numeros_predichos)
        
        # Análisis de rangos
        rangos = {
            "bajo (1-13)": [n for n in numeros_predichos if 1 <= n <= 13],
            "medio (14-27)": [n for n in numeros_predichos if 14 <= n <= 27],
            "alto (28-40)": [n for n in numeros_predichos if 28 <= n <= 40]
        }
        
        rangos_resultado = {
            "bajo (1-13)": [n for n in resultado_oficial if 1 <= n <= 13],
            "medio (14-27)": [n for n in resultado_oficial if 14 <= n <= 27],
            "alto (28-40)": [n for n in resultado_oficial if 28 <= n <= 40]
        }
        
        return {
            "numeros_no_predichos": list(numeros_no_predichos),
            "numeros_resultado_omitidos": list(numeros_resultado_no_predichos),
            "distribucion_rangos_predichos": {k: len(v) for k, v in rangos.items()},
            "distribucion_rangos_resultado": {k: len(v) for k, v in rangos_resultado.items()},
            "numeros_mas_predichos": contador_predichos.most_common(10),
            "sesgo_hacia_altos": len(rangos["alto (28-40)"]) > len(rangos["bajo (1-13)"])
        }
    
    def _ajustar_pesos_modelos(self, performance_analysis: Dict) -> Dict:
        """Ajusta los pesos de modelos basándose en su performance"""
        
        performance_por_modelo = performance_analysis.get("performance_por_modelo", {})
        ajustes = {}
        
        for modelo, stats in performance_por_modelo.items():
            precision_modelo = stats.get("precision", 0)
            peso_actual = self.model_weights.get(modelo, 0.1)
            
            # Factor de ajuste basado en performance vs expectativa
            expectativa = 0.15  # 15% esperado
            factor_ajuste = precision_modelo / expectativa if expectativa > 0 else 1
            
            # Limitar ajustes a ±20%
            factor_ajuste = max(0.8, min(1.2, factor_ajuste))
            
            nuevo_peso = peso_actual * factor_ajuste
            nuevo_peso = max(0.05, min(0.25, nuevo_peso))  # Límites absolutos
            
            ajustes[modelo] = {
                "peso_anterior": peso_actual,
                "peso_nuevo": nuevo_peso,
                "precision": precision_modelo,
                "factor_ajuste": factor_ajuste
            }
            
            self.model_weights[modelo] = nuevo_peso
        
        # Normalizar pesos para que sumen ~1.0
        total_peso = sum(self.model_weights.values())
        if total_peso > 0:
            for modelo in self.model_weights:
                self.model_weights[modelo] /= total_peso
        
        return ajustes
    
    def _analizar_numeros_faltantes(self, resultado_oficial: List[int], predicciones: List[Dict]) -> Dict:
        """Analiza qué números específicos fueron omitidos o mal estimados"""
        
        numeros_predichos = set()
        for pred in predicciones:
            numeros_predichos.update(pred.get("combination", []))
        
        # Convert to standard Python types to avoid numpy int64 issues
        resultado_oficial_py = [int(x) for x in resultado_oficial]
        numeros_predichos_py = set(int(x) for x in numeros_predichos)
        resultado_set = set(resultado_oficial_py)
        
        numeros_omitidos = resultado_set - numeros_predichos_py
        numeros_acertados = resultado_set & numeros_predichos_py
        
        # Actualizar análisis histórico de patrones
        for num in numeros_omitidos:
            if num not in self.pattern_analysis["numeros_subestimados"]:
                self.pattern_analysis["numeros_subestimados"].append(num)
        
        return {
            "numeros_omitidos": list(numeros_omitidos),
            "numeros_acertados": list(numeros_acertados),
            "tasa_cobertura": len(numeros_acertados) / 6,
            "numeros_criticos_perdidos": list(numeros_omitidos)
        }
    
    def _generar_recomendaciones(self, performance_analysis: Dict, bias_analysis: Dict, 
                               number_analysis: Dict) -> List[str]:
        """Genera recomendaciones específicas de mejora"""
        
        recommendations = []
        
        # Basado en performance
        if performance_analysis["precision_general"] < 0.2:
            recommendations.append("🔧 CRÍTICO: Precisión general muy baja. Revisar configuración de todos los modelos.")
        
        # Basado en sesgos
        if bias_analysis["sesgo_hacia_altos"]:
            recommendations.append("⚖️ Balancear mejor los rangos numéricos - reducir sesgo hacia números altos (28-40).")
        
        if len(bias_analysis["numeros_resultado_omitidos"]) >= 3:
            nums = ", ".join(map(str, bias_analysis["numeros_resultado_omitidos"]))
            recommendations.append(f"🎯 URGENTE: Números completamente omitidos: {nums}. Ajustar cobertura.")
        
        # Basado en números faltantes
        if number_analysis["tasa_cobertura"] < 0.3:
            recommendations.append("📊 Mejorar cobertura de números - menos del 30% de números correctos fueron predichos.")
        
        # Recomendaciones específicas
        numeros_criticos = number_analysis.get("numeros_criticos_perdidos", [])
        if numeros_criticos:
            recommendations.append(f"🔍 Incorporar mejor análisis para números: {numeros_criticos}")
        
        if not recommendations:
            recommendations.append("✅ Sistema funcionando dentro de parámetros normales.")
        
        return recommendations
    
    def _actualizar_datos_aprendizaje(self, resultado_oficial: List[int], predicciones: List[Dict],
                                    fecha: str, performance_analysis: Dict, bias_analysis: Dict):
        """Actualiza los datos históricos de aprendizaje"""
        
        nuevo_registro = {
            "fecha": fecha,
            "resultado_oficial": resultado_oficial,
            "total_predicciones": len(predicciones),
            "precision_lograda": performance_analysis["precision_general"],
            "aciertos_totales": performance_analysis["total_aciertos"],
            "numeros_omitidos": bias_analysis["numeros_resultado_omitidos"]
        }
        
        self.learning_data["resultados_reales"].append(nuevo_registro)
        
        # Mantener solo últimos 50 registros
        if len(self.learning_data["resultados_reales"]) > 50:
            self.learning_data["resultados_reales"] = self.learning_data["resultados_reales"][-50:]
    
    def _guardar_datos_aprendizaje(self):
        """Guarda todos los datos de aprendizaje"""
        
        # Guardar datos de aprendizaje
        with open(self.learning_data_path, 'w') as f:
            json_module.dump(self.learning_data, f, indent=2)
        
        # Guardar pesos actualizados
        with open(self.model_weights_path, 'w') as f:
            json_module.dump(self.model_weights, f, indent=2)
        
        # Guardar análisis de patrones
        with open(self.pattern_analysis_path, 'w') as f:
            json_module.dump(self.pattern_analysis, f, indent=2)
    
    def get_optimized_weights(self) -> Dict:
        """Retorna los pesos optimizados de modelos"""
        return self.model_weights.copy()
    
    def get_learning_insights(self) -> Dict:
        """Retorna insights del aprendizaje histórico"""
        
        if not self.learning_data["resultados_reales"]:
            return {"mensaje": "No hay datos de aprendizaje histórico disponibles"}
        
        # Calcular métricas históricas
        precision_historica = [r["precision_lograda"] for r in self.learning_data["resultados_reales"]]
        
        return {
            "total_sorteos_analizados": len(self.learning_data["resultados_reales"]),
            "precision_promedio": np.mean(precision_historica),
            "precision_mejor": max(precision_historica),
            "precision_tendencia": "mejorando" if len(precision_historica) >= 3 and precision_historica[-1] > precision_historica[-3] else "estable",
            "numeros_problematicos": self.pattern_analysis["numeros_subestimados"][-10:],
            "pesos_actuales": self.model_weights
        }

# Función de conveniencia
def aprender_automaticamente(resultado_oficial: List[int], predicciones: List[Dict], 
                           fecha: str = None) -> Dict:
    """
    Función de conveniencia para aprendizaje automático
    """
    learner = OmegaAutoLearning()
    return learner.aprender_de_resultado(resultado_oficial, predicciones, fecha)