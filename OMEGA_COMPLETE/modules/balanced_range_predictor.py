#!/usr/bin/env python3
"""
⚖️ Balanced Range Predictor - Predictor con Balanceo de Rangos Optimizado
Corrige el sesgo hacia números altos y mejora la cobertura de números bajos
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from collections import Counter
import random
import logging

logger = logging.getLogger(__name__)

class BalancedRangePredictor:
    """Predictor que balancea automáticamente los rangos numéricos"""
    
    def __init__(self, historial_df: pd.DataFrame):
        self.historial_df = historial_df
        
        # Definir rangos
        self.rangos = {
            "bajo": (1, 13),      # 13 números
            "medio": (14, 27),    # 14 números  
            "alto": (28, 40)      # 13 números
        }
        
        # Analizar distribución histórica
        self.distribucion_historica = self._analizar_distribucion_historica()
        self.probabilidades_balanceadas = self._calcular_probabilidades_balanceadas()
        
    def _analizar_distribucion_historica(self) -> Dict:
        """Analiza cómo se distribuyen históricamente los números por rangos"""
        
        # Obtener columnas de bolillas
        cols_bolillas = [c for c in self.historial_df.columns if "bolilla" in c.lower()][:6]
        
        if len(cols_bolillas) < 6:
            logger.warning("Insuficientes columnas de bolillas para análisis")
            return self._distribucion_default()
        
        contadores_rangos = {rango: 0 for rango in self.rangos.keys()}
        total_numeros = 0
        
        for _, fila in self.historial_df.iterrows():
            numeros_sorteo = []
            for col in cols_bolillas:
                try:
                    num = int(fila[col])
                    if 1 <= num <= 40:
                        numeros_sorteo.append(num)
                except (ValueError, TypeError):
                    continue
            
            if len(numeros_sorteo) == 6:
                for num in numeros_sorteo:
                    total_numeros += 1
                    for rango, (min_val, max_val) in self.rangos.items():
                        if min_val <= num <= max_val:
                            contadores_rangos[rango] += 1
                            break
        
        if total_numeros == 0:
            return self._distribucion_default()
        
        # Calcular proporciones
        proporciones = {rango: count / total_numeros for rango, count in contadores_rangos.items()}
        
        logger.info(f"📊 Distribución histórica real:")
        for rango, prop in proporciones.items():
            logger.info(f"   • {rango}: {prop:.3f} ({contadores_rangos[rango]}/{total_numeros})")
        
        return {
            "proporciones": proporciones,
            "contadores": contadores_rangos,
            "total_numeros": total_numeros
        }
    
    def _distribucion_default(self) -> Dict:
        """Distribución por defecto si no hay datos suficientes"""
        return {
            "proporciones": {"bajo": 0.32, "medio": 0.35, "alto": 0.33},
            "contadores": {"bajo": 32, "medio": 35, "alto": 33},
            "total_numeros": 100
        }
    
    def _calcular_probabilidades_balanceadas(self) -> Dict:
        """Calcula probabilidades balanceadas para cada número"""
        
        proporciones_historicas = self.distribucion_historica["proporciones"]
        
        # Objetivo: distribución más balanceada (ideal sería 33.3% cada rango)
        objetivo_ideal = 1.0 / 3.0  # 33.3%
        
        # Calcular factores de corrección
        factores_correccion = {}
        for rango, prop_actual in proporciones_historicas.items():
            if prop_actual > 0:
                # Si un rango está sobrerrepresentado, reducir su peso
                # Si está subrepresentado, aumentar su peso
                factor = objetivo_ideal / prop_actual
                # Limitar el factor para evitar cambios extremos
                factor = max(0.5, min(2.0, factor))
            else:
                factor = 2.0  # Máximo boost para rangos sin representación
            
            factores_correccion[rango] = factor
        
        logger.info(f"🔧 Factores de corrección calculados:")
        for rango, factor in factores_correccion.items():
            accion = "BOOST" if factor > 1.0 else "REDUCE" if factor < 1.0 else "MANTENER"
            logger.info(f"   • {rango}: {factor:.3f} ({accion})")
        
        # Calcular probabilidad individual por número
        probabilidades = {}
        for num in range(1, 41):
            rango = self._get_rango_numero(num)
            if rango:
                # Probabilidad base uniforme dentro del rango
                nums_en_rango = self.rangos[rango][1] - self.rangos[rango][0] + 1
                prob_base = 1.0 / nums_en_rango
                
                # Aplicar factor de corrección
                prob_ajustada = prob_base * factores_correccion[rango]
                probabilidades[num] = prob_ajustada
        
        # Normalizar probabilidades
        suma_total = sum(probabilidades.values())
        if suma_total > 0:
            probabilidades = {num: prob / suma_total for num, prob in probabilidades.items()}
        
        return probabilidades
    
    def _get_rango_numero(self, numero: int) -> Optional[str]:
        """Determina a qué rango pertenece un número"""
        for rango, (min_val, max_val) in self.rangos.items():
            if min_val <= numero <= max_val:
                return rango
        return None
    
    def generar_combinaciones_balanceadas(self, cantidad: int = 8, 
                                        enforce_distribution: bool = True) -> List[Dict]:
        """
        Genera combinaciones con distribución balanceada de rangos
        
        Args:
            cantidad: Número de combinaciones a generar
            enforce_distribution: Si forzar distribución específica por rango
            
        Returns:
            Lista de combinaciones balanceadas
        """
        
        combinaciones = []
        
        for i in range(cantidad):
            if enforce_distribution:
                # Método 1: Forzar distribución específica (ej: 2 bajos, 2 medios, 2 altos)
                combinacion = self._generar_combinacion_distribuida()
            else:
                # Método 2: Usar probabilidades balanceadas pero sin forzar distribución exacta
                combinacion = self._generar_combinacion_probabilistica()
            
            if combinacion and len(combinacion) == 6:
                combo_dict = {
                    "combination": sorted(combinacion),
                    "source": "balanced_range",
                    "score": self._calcular_score_balanceado(combinacion),
                    "svi_score": 0.5,  # Placeholder
                    "original_score": self._calcular_score_balanceado(combinacion),
                    "balance_info": self._analizar_balance_combinacion(combinacion)
                }
                combinaciones.append(combo_dict)
        
        logger.info(f"✅ Generadas {len(combinaciones)} combinaciones balanceadas")
        
        return combinaciones
    
    def _generar_combinacion_distribuida(self) -> List[int]:
        """Genera una combinación con distribución específica de rangos"""
        
        # Distribuciones posibles (suma debe ser 6)
        distribuciones_posibles = [
            {"bajo": 2, "medio": 2, "alto": 2},  # Perfectamente balanceada
            {"bajo": 3, "medio": 2, "alto": 1},  # Más números bajos
            {"bajo": 2, "medio": 3, "alto": 1},  # Más números medios
            {"bajo": 1, "medio": 3, "alto": 2},  # Balanceada con sesgo medio
            {"bajo": 1, "medio": 2, "alto": 3},  # Más números altos (controlado)
            {"bajo": 2, "medio": 1, "alto": 3},  # Balanceada con sesgo alto
        ]
        
        # Elegir distribución (con sesgo hacia más balanceadas)
        pesos_distribuciones = [0.4, 0.2, 0.2, 0.1, 0.05, 0.05]  # Favorece distribución balanceada
        distribucion = np.random.choice(distribuciones_posibles, p=pesos_distribuciones)
        
        combinacion = []
        
        for rango, cantidad_needed in distribucion.items():
            min_val, max_val = self.rangos[rango]
            
            # Generar números únicos en este rango
            numeros_rango = list(range(min_val, max_val + 1))
            
            # Filtrar números ya seleccionados
            numeros_disponibles = [n for n in numeros_rango if n not in combinacion]
            
            if len(numeros_disponibles) >= cantidad_needed:
                seleccionados = random.sample(numeros_disponibles, cantidad_needed)
                combinacion.extend(seleccionados)
        
        return combinacion if len(combinacion) == 6 else []
    
    def _generar_combinacion_probabilistica(self) -> List[int]:
        """Genera combinación usando probabilidades balanceadas"""
        
        combinacion = []
        intentos = 0
        max_intentos = 100
        
        while len(combinacion) < 6 and intentos < max_intentos:
            # Elegir número basado en probabilidades balanceadas
            numeros = list(self.probabilidades_balanceadas.keys())
            probabilidades = list(self.probabilidades_balanceadas.values())
            
            numero = np.random.choice(numeros, p=probabilidades)
            
            if numero not in combinacion:
                combinacion.append(numero)
            
            intentos += 1
        
        return combinacion if len(combinacion) == 6 else []
    
    def _calcular_score_balanceado(self, combinacion: List[int]) -> float:
        """Calcula score basado en qué tan balanceada está la combinación"""
        
        if len(combinacion) != 6:
            return 0.0
        
        # Contar números por rango
        conteo_rangos = {rango: 0 for rango in self.rangos.keys()}
        
        for num in combinacion:
            rango = self._get_rango_numero(num)
            if rango:
                conteo_rangos[rango] += 1
        
        # Score base: qué tan cerca está de la distribución ideal (2,2,2)
        ideal_por_rango = 2
        diferencias = [abs(count - ideal_por_rango) for count in conteo_rangos.values()]
        desviacion_total = sum(diferencias)
        
        # Score: 1.0 para distribución perfecta, decrece con desviación
        score_balance = max(0.0, 1.0 - (desviacion_total / 6.0))
        
        # Bonus por diversidad numérica
        gaps = [combinacion[i+1] - combinacion[i-1] for i in range(1, len(combinacion)-1)]
        diversidad = min(1.0, np.mean(gaps) / 10.0) if gaps else 0.5
        
        # Score final
        score_final = (score_balance * 0.7) + (diversidad * 0.3)
        
        return min(1.0, score_final)
    
    def _analizar_balance_combinacion(self, combinacion: List[int]) -> Dict:
        """Analiza el balance de una combinación específica"""
        
        conteo_rangos = {rango: [] for rango in self.rangos.keys()}
        
        for num in combinacion:
            rango = self._get_rango_numero(num)
            if rango:
                conteo_rangos[rango].append(num)
        
        return {
            "distribucion": {rango: len(nums) for rango, nums in conteo_rangos.items()},
            "numeros_por_rango": conteo_rangos,
            "balance_score": self._calcular_score_balanceado(combinacion)
        }
    
    def analizar_mejoras_necesarias(self, predicciones_actuales: List[Dict]) -> Dict:
        """Analiza qué mejoras de balance son necesarias en las predicciones actuales"""
        
        if not predicciones_actuales:
            return {"mensaje": "No hay predicciones para analizar"}
        
        # Analizar distribución actual
        todos_numeros = []
        for pred in predicciones_actuales:
            todos_numeros.extend(pred.get("combination", []))
        
        distribucion_actual = {rango: 0 for rango in self.rangos.keys()}
        for num in todos_numeros:
            rango = self._get_rango_numero(num)
            if rango:
                distribucion_actual[rango] += 1
        
        total_predicho = sum(distribucion_actual.values())
        proporciones_actuales = {
            rango: count / total_predicho if total_predicho > 0 else 0 
            for rango, count in distribucion_actual.items()
        }
        
        # Comparar con objetivo balanceado (33.3% cada rango)
        objetivo = 1.0 / 3.0
        desbalances = {
            rango: abs(prop - objetivo) 
            for rango, prop in proporciones_actuales.items()
        }
        
        # Identificar rangos problemáticos
        rango_mas_sobreestimado = max(proporciones_actuales.items(), key=lambda x: x[1])
        rango_mas_subestimado = min(proporciones_actuales.items(), key=lambda x: x[1])
        
        return {
            "distribucion_actual": distribucion_actual,
            "proporciones_actuales": proporciones_actuales,
            "desbalances": desbalances,
            "desbalance_total": sum(desbalances.values()),
            "rango_sobreestimado": rango_mas_sobreestimado,
            "rango_subestimado": rango_mas_subestimado,
            "necesita_balance": sum(desbalances.values()) > 0.2  # Threshold del 20%
        }

def crear_predictor_balanceado(historial_df: pd.DataFrame) -> BalancedRangePredictor:
    """Factory function para crear el predictor balanceado"""
    return BalancedRangePredictor(historial_df)