#!/usr/bin/env python3
"""
🎯 OMEGA STRATEGY SELECTOR - Interfaz completa de selección de estrategias
Permite al cliente elegir entre diferentes opciones según presupuesto y perfil
"""

import pandas as pd
import sys
import os
from typing import Dict, List
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.budget_optimizer import OmegaBudgetOptimizer
from omega_integrated_system import OmegaIntegratedSystem
import logging
import json
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OmegaStrategySelector:
    """Selector interactivo de estrategias OMEGA"""
    
    def __init__(self, historical_path: str, jackpot_path: str):
        self.historical_path = historical_path
        self.jackpot_path = jackpot_path
        self.historical_data = pd.read_csv(historical_path)
        
        # Inicializar componentes
        self.budget_optimizer = OmegaBudgetOptimizer(self.historical_data)
        self.omega_system = OmegaIntegratedSystem(historical_path, jackpot_path)
        
        # Ejecutar análisis base una vez
        self.base_analysis = self.omega_system.run_complete_analysis()
        
        logger.info("🎯 OMEGA Strategy Selector inicializado")
    
    def show_strategy_menu(self):
        """Muestra el menú principal de selección de estrategias"""
        
        print("🎯" + "="*70)
        print("             OMEGA PRO AI - SELECTOR DE ESTRATEGIAS")
        print("        'Elige tu estrategia según tu presupuesto y perfil'")
        print("="*72)
        
        # Mostrar opciones de estrategia
        ui_text = self.budget_optimizer.generate_strategy_selector_ui()
        print(ui_text)
        
        return self._get_user_strategy_choice()
    
    def _get_user_strategy_choice(self) -> str:
        """Obtiene la elección de estrategia del usuario (simulada)"""
        
        # En un entorno real, esto sería input del usuario
        # Para demo, simular diferentes perfiles
        demo_profiles = [
            {
                'name': 'Usuario Conservador',
                'monthly_budget': 50,
                'risk_tolerance': 'low',
                'experience': 'beginner'
            },
            {
                'name': 'Usuario Estándar', 
                'monthly_budget': 150,
                'risk_tolerance': 'medium',
                'experience': 'intermediate'
            },
            {
                'name': 'Usuario Premium',
                'monthly_budget': 800,
                'risk_tolerance': 'high',
                'experience': 'advanced'
            }
        ]
        
        print("\n🎭 PERFILES DE DEMO:")
        for i, profile in enumerate(demo_profiles, 1):
            print(f"{i}. {profile['name']}: S/. {profile['monthly_budget']}/mes, "
                  f"Riesgo {profile['risk_tolerance']}, {profile['experience']}")
        
        # Para demo, usar perfil estándar
        selected_profile = demo_profiles[1]  # Usuario Estándar
        print(f"\n🎯 Seleccionado: {selected_profile['name']}")
        
        return self._get_personalized_recommendation(selected_profile)
    
    def _get_personalized_recommendation(self, profile: Dict) -> str:
        """Genera recomendación personalizada"""
        
        recommendation = self.budget_optimizer.generate_personalized_recommendation(
            monthly_budget=profile['monthly_budget'],
            risk_tolerance=profile['risk_tolerance'],
            experience_level=profile['experience']
        )
        
        self._display_recommendation(recommendation, profile)
        
        return recommendation['recommended_strategy']
    
    def _display_recommendation(self, recommendation: Dict, profile: Dict):
        """Muestra la recomendación personalizada"""
        
        print("\n" + "="*70)
        print("🎯 RECOMENDACIÓN PERSONALIZADA OMEGA")
        print("="*70)
        
        if recommendation['fits_budget']:
            strategy = recommendation['strategy_details']
            roi = recommendation['roi_projection']
            
            print(f"\n✅ ESTRATEGIA RECOMENDADA: {strategy['name']}")
            print(f"📝 {strategy['description']}")
            print(f"\n💰 COSTOS:")
            print(f"   • Por sorteo: S/. {strategy['cost_per_draw']}")
            print(f"   • Mensual: S/. {recommendation['monthly_cost']:.0f}")
            print(f"   • Anual: S/. {strategy['annual_cost']:,}")
            
            print(f"\n🎯 COBERTURA:")
            print(f"   • Combinaciones: {strategy['combinations']}")
            print(f"   • Tipo: {strategy['type']}")
            print(f"   • ROI esperado: {strategy['expected_roi']}")
            
            print(f"\n📊 PROYECCIÓN ANUAL:")
            print(f"   • Ganancia neta: S/. {roi.get('net_profit', 0):,.0f}")
            print(f"   • ROI: {roi.get('roi_percentage', 0):.1f}%")
            print(f"   • Hits 3+ números: {roi.get('hits_per_year', {}).get('3+', 0):.1f}")
            print(f"   • Hits 4+ números: {roi.get('hits_per_year', {}).get('4+', 0):.1f}")
            print(f"   • Hits 5 números: {roi.get('hits_per_year', {}).get('5+', 0):.1f}")
            
            print(f"\n⚖️ PERFIL DE RIESGO:")
            print(f"   • Nivel: {strategy['risk_level']}")
            print(f"   • Uso de presupuesto: {recommendation['budget_analysis']['budget_utilization']:.1f}%")
            
            if recommendation['alternative_strategies']:
                print(f"\n🔄 ALTERNATIVAS DISPONIBLES:")
                for alt in recommendation['alternative_strategies']:
                    alt_strategy = self.budget_optimizer.strategy_options[alt]
                    print(f"   • {alt_strategy['name']} (S/. {alt_strategy['cost_per_draw']}/sorteo)")
        
        else:
            print("\n❌ PRESUPUESTO INSUFICIENTE")
            print(f"Presupuesto mensual: S/. {profile['monthly_budget']}")
            print("Recomendación: Considerar la opción ECONÓMICA o aumentar presupuesto")
    
    def generate_predictions_for_strategy(self, strategy_name: str) -> List[Dict]:
        """Genera predicciones específicas para la estrategia seleccionada"""
        
        print(f"\n🎯 GENERANDO PREDICCIONES PARA ESTRATEGIA: {strategy_name.upper()}")
        print("="*70)
        
        strategy = self.budget_optimizer.strategy_options[strategy_name]
        
        if strategy['type'] == 'simple':
            # Estrategias de combinaciones simples
            predictions = self._generate_simple_combinations(strategy['combinations'])
        
        elif strategy['type'] in ['multiple_8', 'multiple_9', 'multiple_10']:
            # Estrategias de jugadas múltiples
            num_count = int(strategy['type'].split('_')[1])
            predictions = self._generate_multiple_combination(num_count)
        
        elif strategy['type'] == 'hybrid':
            # Estrategia híbrida
            predictions = self._generate_hybrid_combinations()
        
        else:
            # Default: usar sistema integrado estándar
            predictions = self.omega_system.generate_integrated_predictions(strategy['combinations'])
        
        self._display_strategy_predictions(predictions, strategy)
        
        return predictions
    
    def _generate_simple_combinations(self, num_combinations: int) -> List[Dict]:
        """Genera combinaciones simples usando sistema integrado"""
        
        predictions = self.omega_system.generate_integrated_predictions(num_combinations)
        
        # Convertir al formato esperado
        simple_predictions = []
        for pred in predictions[:num_combinations]:
            simple_predictions.append({
                'combination': pred['combination'],
                'final_score': pred['final_score'],
                'type': 'simple',
                'cost': 2,
                'expected_prize_4': 20,
                'expected_prize_5': 500
            })
        
        return simple_predictions
    
    def _generate_multiple_combination(self, num_count: int) -> List[Dict]:
        """Genera una jugada múltiple óptima"""
        
        # Generar predicción integrada para obtener los mejores números
        base_predictions = self.omega_system.generate_integrated_predictions(8)
        
        # Extraer los números más frecuentes/mejores
        all_numbers = []
        for pred in base_predictions:
            all_numbers.extend(pred['combination'])
        
        # Contar frecuencias y obtener los top números
        from collections import Counter
        number_freq = Counter(all_numbers)
        top_numbers = [num for num, freq in number_freq.most_common(num_count)]
        
        # Si faltan números, completar con análisis de jackpots
        if len(top_numbers) < num_count:
            jackpot_patterns = self.base_analysis.get('jackpot_analysis', {})
            freq_analysis = jackpot_patterns.get('frequency_analysis', {})
            
            if 'most_frequent' in freq_analysis:
                jackpot_numbers = [num for num, _ in freq_analysis['most_frequent'][:15]]
                for num in jackpot_numbers:
                    if num not in top_numbers and len(top_numbers) < num_count:
                        top_numbers.append(num)
        
        # Asegurar balance y completar si es necesario
        top_numbers = self._ensure_balanced_selection(top_numbers, num_count)
        
        # Calcular combinaciones automáticas
        from math import comb
        auto_combinations = comb(num_count, 6)
        
        cost_map = {8: 56, 9: 168, 10: 420}
        prize_map = {
            8: {'4+': 168, '5': 1830},
            9: {'4+': 320, '5': 2720}, 
            10: {'4+': 540, '5': 3800}
        }
        
        return [{
            'combination': sorted(top_numbers),
            'final_score': 0.8,  # Score alto para múltiples
            'type': f'multiple_{num_count}',
            'auto_combinations': auto_combinations,
            'cost': cost_map.get(num_count, 168),
            'expected_prize_4': prize_map.get(num_count, {}).get('4+', 320),
            'expected_prize_5': prize_map.get(num_count, {}).get('5', 2720)
        }]
    
    def _generate_hybrid_combinations(self) -> List[Dict]:
        """Genera combinaciones híbridas (múltiple + simples)"""
        
        # 1 jugada múltiple de 8 números
        multiple_pred = self._generate_multiple_combination(8)
        
        # 8 jugadas simples adicionales
        simple_preds = self._generate_simple_combinations(8)
        
        # Combinar ambas
        hybrid_predictions = multiple_pred + simple_preds
        
        return hybrid_predictions
    
    def _ensure_balanced_selection(self, numbers: List[int], target_count: int) -> List[int]:
        """Asegura una selección balanceada de números"""
        
        if len(numbers) >= target_count:
            return numbers[:target_count]
        
        # Completar manteniendo balance por rangos
        current_numbers = set(numbers)
        
        # Contar por rangos
        bajo = sum(1 for n in numbers if 1 <= n <= 13)
        medio = sum(1 for n in numbers if 14 <= n <= 27)
        alto = sum(1 for n in numbers if 28 <= n <= 40)
        
        needed = target_count - len(numbers)
        
        # Agregar números para mantener balance
        for num in range(1, 41):
            if num not in current_numbers and needed > 0:
                # Priorizar balance
                if bajo < target_count // 3 and 1 <= num <= 13:
                    numbers.append(num)
                    bajo += 1
                    needed -= 1
                elif medio < target_count // 3 and 14 <= num <= 27:
                    numbers.append(num)
                    medio += 1
                    needed -= 1
                elif alto < target_count // 3 and 28 <= num <= 40:
                    numbers.append(num)
                    alto += 1
                    needed -= 1
                elif needed > 0:  # Llenar restantes
                    numbers.append(num)
                    needed -= 1
        
        return sorted(numbers[:target_count])
    
    def _display_strategy_predictions(self, predictions: List[Dict], strategy: Dict):
        """Muestra las predicciones para la estrategia"""
        
        print(f"\n🏆 PREDICCIONES {strategy['name']}")
        print("="*70)
        
        total_cost = 0
        
        for i, pred in enumerate(predictions, 1):
            combo = pred['combination']
            pred_type = pred.get('type', 'simple')
            cost = pred.get('cost', 2)
            total_cost += cost
            
            print(f"\n🎯 PREDICCIÓN #{i}: {combo}")
            print(f"   💰 Costo: S/. {cost}")
            print(f"   🎲 Tipo: {pred_type}")
            
            if pred_type.startswith('multiple'):
                auto_combos = pred.get('auto_combinations', 0)
                print(f"   🔄 Combinaciones auto: {auto_combos}")
            
            print(f"   📈 Score: {pred.get('final_score', 0):.3f}")
            
            # Análisis de balance
            bajo = sum(1 for n in combo if 1 <= n <= 13)
            medio = sum(1 for n in combo if 14 <= n <= 27) 
            alto = sum(1 for n in combo if 28 <= n <= 40)
            print(f"   ⚖️ Balance: {bajo}-{medio}-{alto}")
        
        print(f"\n💰 COSTO TOTAL POR SORTEO: S/. {total_cost}")
        print(f"📅 COSTO MENSUAL (13 sorteos): S/. {total_cost * 13:,.0f}")
        print(f"📅 COSTO ANUAL (43 sorteos): S/. {total_cost * 43:,.0f}")
    
    def save_strategy_session(self, strategy_name: str, predictions: List[Dict]):
        """Guarda la sesión de estrategia seleccionada"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        session_data = {
            'timestamp': timestamp,
            'selected_strategy': strategy_name,
            'strategy_details': self.budget_optimizer.strategy_options[strategy_name],
            'predictions': predictions,
            'base_analysis_summary': {
                'entropy_analysis_positions': len(self.base_analysis.get('combined_entropy_fft', {})),
                'jackpot_patterns_detected': len(self.base_analysis.get('jackpot_analysis', {})),
                'system_confidence': getattr(self.omega_system, 'system_confidence', 0)
            }
        }
        
        # Hacer serializable
        serializable_data = self.omega_system._make_serializable(session_data)
        
        # Guardar
        filename = f"results/omega_strategy_session_{strategy_name}_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(serializable_data, f, indent=2)
        
        print(f"\n💾 SESIÓN GUARDADA: {filename}")
        
        return filename

def run_omega_strategy_selector():
    """Función principal para ejecutar el selector de estrategias"""
    
    # Crear selector
    selector = OmegaStrategySelector(
        historical_path="data/historial_kabala_github_emergency_clean.csv",
        jackpot_path="data/jackpots_omega.csv"
    )
    
    # Mostrar menú y obtener selección
    selected_strategy = selector.show_strategy_menu()
    
    # Generar predicciones para la estrategia seleccionada
    predictions = selector.generate_predictions_for_strategy(selected_strategy)
    
    # Guardar sesión
    session_file = selector.save_strategy_session(selected_strategy, predictions)
    
    print("\n✅ SELECTOR DE ESTRATEGIAS OMEGA COMPLETADO")
    
    return {
        'selected_strategy': selected_strategy,
        'predictions': predictions,
        'session_file': session_file,
        'selector': selector
    }

if __name__ == "__main__":
    result = run_omega_strategy_selector()