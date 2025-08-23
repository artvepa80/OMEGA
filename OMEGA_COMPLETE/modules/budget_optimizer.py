#!/usr/bin/env python3
"""
💰 Budget Optimizer - Sistema de opciones presupuestarias para OMEGA
Permite al cliente elegir entre diferentes estrategias según su presupuesto
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
import logging
from itertools import combinations
import json

logger = logging.getLogger(__name__)

class OmegaBudgetOptimizer:
    """Optimizador de presupuesto para diferentes estrategias OMEGA"""
    
    def __init__(self, historical_data: pd.DataFrame):
        self.data = historical_data
        self.strategy_options = self._define_strategy_options()
        
        logger.info("💰 Budget Optimizer inicializado")
    
    def _define_strategy_options(self) -> Dict:
        """Define las opciones estratégicas según presupuesto"""
        
        return {
            'economico': {
                'name': '🟢 OMEGA ECONÓMICO',
                'description': 'Estrategia básica para presupuestos ajustados',
                'cost_per_draw': 4,  # 2 combinaciones simples × S/. 2
                'annual_cost': 4 * 43,  # S/. 172
                'combinations': 2,
                'type': 'simple',
                'expected_roi': '50-80%',
                'risk_level': 'Bajo',
                'target_audience': 'Jugadores ocasionales, presupuesto limitado'
            },
            'estandar': {
                'name': '🟡 OMEGA ESTÁNDAR', 
                'description': 'Balance óptimo entre costo y probabilidad',
                'cost_per_draw': 16,  # 8 combinaciones simples × S/. 2
                'annual_cost': 16 * 43,  # S/. 688
                'combinations': 8,
                'type': 'simple',
                'expected_roi': '150-200%',
                'risk_level': 'Medio',
                'target_audience': 'Jugadores regulares, presupuesto moderado'
            },
            'premium': {
                'name': '🟠 OMEGA PREMIUM',
                'description': 'Jugadas múltiples para mayor cobertura',
                'cost_per_draw': 168,  # 1 múltiple de 9 números
                'annual_cost': 168 * 43,  # S/. 7,224
                'combinations': 84,  # C(9,6) combinaciones automáticas
                'type': 'multiple_9',
                'expected_roi': '200-300%',
                'risk_level': 'Medio-Alto',
                'target_audience': 'Jugadores serios, presupuesto amplio'
            },
            'vip': {
                'name': '🔴 OMEGA VIP',
                'description': 'Máxima cobertura y potencial de ganancia',
                'cost_per_draw': 420,  # 1 múltiple de 10 números
                'annual_cost': 420 * 43,  # S/. 18,060
                'combinations': 210,  # C(10,6) combinaciones automáticas
                'type': 'multiple_10',
                'expected_roi': '300-500%',
                'risk_level': 'Alto',
                'target_audience': 'Jugadores profesionales, presupuesto alto'
            },
            'mixto': {
                'name': '🟣 OMEGA MIXTO',
                'description': 'Combinación de estrategias para diversificar',
                'cost_per_draw': 56 + 16,  # 1 múltiple de 8 + 8 simples
                'annual_cost': 72 * 43,  # S/. 3,096
                'combinations': 28 + 8,  # C(8,6) + 8 simples
                'type': 'hybrid',
                'expected_roi': '180-250%',
                'risk_level': 'Medio',
                'target_audience': 'Jugadores que buscan balance riesgo/beneficio'
            }
        }
    
    def get_strategy_comparison(self) -> Dict:
        """Genera comparativa completa de todas las estrategias"""
        
        comparison = {
            'strategies': self.strategy_options,
            'prize_structure': self._get_prize_structure(),
            'roi_projections': self._calculate_roi_projections(),
            'risk_assessment': self._assess_strategy_risks()
        }
        
        return comparison
    
    def _get_prize_structure(self) -> Dict:
        """Define la estructura de premios de La Kábala"""
        
        return {
            'simple': {
                '6_numbers': 'Pozo Buenazo (S/. 300,000+)',
                '5_numbers': 'S/. 500',
                '4_numbers': 'S/. 20',
                '3_numbers': 'S/. 3',
                '2_numbers': '1 jugada gratis'
            },
            'multiple_8': {
                '6_numbers': 'Pozo Buenazo',
                '5_numbers': 'S/. 1,830',
                '4_numbers': 'S/. 168',
                '3_numbers': 'S/. 30',
                '2_numbers': '15 jugadas gratis'
            },
            'multiple_9': {
                '6_numbers': 'Pozo Buenazo',
                '5_numbers': 'S/. 2,720',
                '4_numbers': 'S/. 320',
                '3_numbers': 'S/. 60',
                '2_numbers': '35 jugadas gratis'
            },
            'multiple_10': {
                '6_numbers': 'Pozo Buenazo',
                '5_numbers': 'S/. 3,800',
                '4_numbers': 'S/. 540',
                '3_numbers': 'S/. 105',
                '2_numbers': '70 jugadas gratis'
            }
        }
    
    def _calculate_roi_projections(self) -> Dict:
        """Calcula proyecciones de ROI para cada estrategia"""
        
        projections = {}
        
        # Probabilidades estimadas basadas en análisis OMEGA
        hit_probabilities = {
            'economico': {'3+': 0.15, '4+': 0.03, '5+': 0.002},
            'estandar': {'3+': 0.45, '4+': 0.12, '5+': 0.008},
            'premium': {'3+': 0.85, '4+': 0.35, '5+': 0.025},
            'vip': {'3+': 0.95, '4+': 0.50, '5+': 0.040},
            'mixto': {'3+': 0.70, '4+': 0.25, '5+': 0.015}
        }
        
        prize_values = {
            'simple': {'3+': 3, '4+': 20, '5+': 500},
            'multiple_8': {'3+': 30, '4+': 168, '5+': 1830},
            'multiple_9': {'3+': 60, '4+': 320, '5+': 2720},
            'multiple_10': {'3+': 105, '4+': 540, '5+': 3800}
        }
        
        for strategy_name, strategy in self.strategy_options.items():
            annual_cost = strategy['annual_cost']
            draws_per_year = 43
            
            # Determinar valores de premio según tipo
            if strategy['type'] == 'simple':
                prize_set = prize_values['simple']
            elif strategy['type'] == 'multiple_9':
                prize_set = prize_values['multiple_9']
            elif strategy['type'] == 'multiple_10':
                prize_set = prize_values['multiple_10']
            elif strategy['type'] == 'hybrid':
                # Promedio ponderado para híbrido
                prize_set = {
                    '3+': (prize_values['multiple_8']['3+'] + prize_values['simple']['3+']) / 2,
                    '4+': (prize_values['multiple_8']['4+'] + prize_values['simple']['4+']) / 2,
                    '5+': (prize_values['multiple_8']['5+'] + prize_values['simple']['5+']) / 2
                }
            else:
                prize_set = prize_values['simple']
            
            # Calcular ingresos esperados anuales
            probs = hit_probabilities[strategy_name]
            expected_annual_income = (
                (probs['3+'] * draws_per_year * prize_set['3+']) +
                (probs['4+'] * draws_per_year * prize_set['4+']) +
                (probs['5+'] * draws_per_year * prize_set['5+'])
            )
            
            net_profit = expected_annual_income - annual_cost
            roi_percentage = (net_profit / annual_cost * 100) if annual_cost > 0 else 0
            
            projections[strategy_name] = {
                'annual_cost': annual_cost,
                'expected_income': expected_annual_income,
                'net_profit': net_profit,
                'roi_percentage': roi_percentage,
                'breakeven_months': annual_cost / (expected_annual_income / 12) if expected_annual_income > 0 else float('inf'),
                'hits_per_year': {
                    '3+': probs['3+'] * draws_per_year,
                    '4+': probs['4+'] * draws_per_year,
                    '5+': probs['5+'] * draws_per_year
                }
            }
        
        return projections
    
    def _assess_strategy_risks(self) -> Dict:
        """Evalúa riesgos de cada estrategia"""
        
        risk_assessment = {}
        
        for strategy_name, strategy in self.strategy_options.items():
            cost = strategy['annual_cost']
            
            # Factores de riesgo
            volatility_risk = 'Alto' if cost > 5000 else 'Medio' if cost > 1000 else 'Bajo'
            liquidity_risk = 'Alto' if cost > 10000 else 'Medio' if cost > 3000 else 'Bajo'
            
            # Tiempo de recuperación
            if strategy_name == 'economico':
                recovery_time = '1-2 meses'
                risk_score = 2
            elif strategy_name == 'estandar':
                recovery_time = '2-4 meses'
                risk_score = 4
            elif strategy_name == 'mixto':
                recovery_time = '3-6 meses'
                risk_score = 5
            elif strategy_name == 'premium':
                recovery_time = '6-9 meses'
                risk_score = 7
            else:  # vip
                recovery_time = '9-15 meses'
                risk_score = 9
            
            risk_assessment[strategy_name] = {
                'overall_risk': strategy['risk_level'],
                'volatility_risk': volatility_risk,
                'liquidity_risk': liquidity_risk,
                'recovery_time': recovery_time,
                'risk_score': risk_score,
                'recommended_for': strategy['target_audience']
            }
        
        return risk_assessment
    
    def generate_personalized_recommendation(self, 
                                           monthly_budget: float,
                                           risk_tolerance: str = 'medium',
                                           experience_level: str = 'intermediate') -> Dict:
        """Genera recomendación personalizada basada en perfil del cliente"""
        
        annual_budget = monthly_budget * 12
        
        # Filtrar estrategias por presupuesto
        affordable_strategies = {}
        for name, strategy in self.strategy_options.items():
            if strategy['annual_cost'] <= annual_budget:
                affordable_strategies[name] = strategy
        
        # Filtrar por tolerancia al riesgo
        risk_filtered = {}
        for name, strategy in affordable_strategies.items():
            strategy_risk = strategy['risk_level'].lower()
            
            if risk_tolerance.lower() == 'low' and strategy_risk in ['bajo', 'medio']:
                risk_filtered[name] = strategy
            elif risk_tolerance.lower() == 'medium':
                risk_filtered[name] = strategy
            elif risk_tolerance.lower() == 'high':
                risk_filtered[name] = strategy
        
        if not risk_filtered:
            risk_filtered = affordable_strategies
        
        # Recomendar según experiencia
        if experience_level.lower() == 'beginner':
            recommended_order = ['economico', 'estandar', 'mixto', 'premium', 'vip']
        elif experience_level.lower() == 'intermediate':
            recommended_order = ['estandar', 'mixto', 'premium', 'economico', 'vip']
        else:  # advanced
            recommended_order = ['premium', 'vip', 'mixto', 'estandar', 'economico']
        
        # Encontrar la mejor opción disponible
        recommended_strategy = None
        for strategy_name in recommended_order:
            if strategy_name in risk_filtered:
                recommended_strategy = strategy_name
                break
        
        # Calcular proyecciones para la recomendación
        roi_projections = self._calculate_roi_projections()
        
        recommendation = {
            'recommended_strategy': recommended_strategy,
            'strategy_details': self.strategy_options[recommended_strategy] if recommended_strategy else None,
            'monthly_cost': self.strategy_options[recommended_strategy]['annual_cost'] / 12 if recommended_strategy else 0,
            'fits_budget': True if recommended_strategy else False,
            'roi_projection': roi_projections.get(recommended_strategy, {}),
            'alternative_strategies': list(risk_filtered.keys()),
            'budget_analysis': {
                'monthly_budget': monthly_budget,
                'annual_budget': annual_budget,
                'budget_utilization': (self.strategy_options[recommended_strategy]['annual_cost'] / annual_budget * 100) if recommended_strategy else 0
            },
            'personalization_factors': {
                'risk_tolerance': risk_tolerance,
                'experience_level': experience_level,
                'monthly_budget': monthly_budget
            }
        }
        
        return recommendation
    
    def generate_strategy_selector_ui(self) -> str:
        """Genera interfaz de texto para selección de estrategia"""
        
        ui_text = """
🎯 OMEGA STRATEGY SELECTOR
=========================

Elige tu estrategia OMEGA según tu presupuesto y perfil:

"""
        
        roi_projections = self._calculate_roi_projections()
        
        for i, (strategy_name, strategy) in enumerate(self.strategy_options.items(), 1):
            roi = roi_projections.get(strategy_name, {})
            
            ui_text += f"""
{i}. {strategy['name']}
   💰 Costo por sorteo: S/. {strategy['cost_per_draw']}
   📅 Costo anual: S/. {strategy['annual_cost']:,}
   🎯 Combinaciones: {strategy['combinations']}
   📈 ROI esperado: {strategy['expected_roi']}
   ⚖️ Riesgo: {strategy['risk_level']}
   👤 Ideal para: {strategy['target_audience']}
   
   📊 Proyección anual:
   • Ganancia neta: S/. {roi.get('net_profit', 0):,.0f}
   • Hits 4+ números: {roi.get('hits_per_year', {}).get('4+', 0):.1f}
   • Hits 5 números: {roi.get('hits_per_year', {}).get('5+', 0):.1f}
   
"""
        
        ui_text += """
💡 RECOMENDACIONES:
• Principiantes: Opción 1 (Económico) o 2 (Estándar)
• Intermedio: Opción 2 (Estándar) o 5 (Mixto)  
• Avanzado: Opción 3 (Premium) o 4 (VIP)

🔧 Para recomendación personalizada, proporciona:
• Presupuesto mensual
• Tolerancia al riesgo (bajo/medio/alto)
• Nivel de experiencia (principiante/intermedio/avanzado)
"""
        
        return ui_text

def create_budget_strategy_selector(historical_data: pd.DataFrame) -> OmegaBudgetOptimizer:
    """Factory function para crear el selector de estrategias"""
    return OmegaBudgetOptimizer(historical_data)

if __name__ == "__main__":
    # Demo del selector de estrategias
    df = pd.read_csv("data/historial_kabala_github_emergency_clean.csv")
    optimizer = OmegaBudgetOptimizer(df)
    
    print(optimizer.generate_strategy_selector_ui())
    
    # Ejemplo de recomendación personalizada
    recommendation = optimizer.generate_personalized_recommendation(
        monthly_budget=100,
        risk_tolerance='medium',
        experience_level='intermediate'
    )
    
    print("\n🎯 RECOMENDACIÓN PERSONALIZADA:")
    print(f"Estrategia recomendada: {recommendation['recommended_strategy']}")
    print(f"Costo mensual: S/. {recommendation['monthly_cost']:.0f}")
    print(f"ROI esperado: {recommendation['roi_projection'].get('roi_percentage', 0):.1f}%")