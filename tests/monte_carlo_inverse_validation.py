"""
Monte Carlo Inverse Integration and Validation Test Suite
=========================================================

This test suite validates the Monte Carlo Inverse integration for OMEGA PRO AI v10.1,
focusing on:
1. Inverse Mining Engine functionality
2. Statistical validation framework
3. Integration with consensus engine
4. Scoring system and rare number detection
5. Performance improvements tracking

Key Metrics:
- Rare number detection accuracy
- Scoring system stability
- Consensus integration robustness
"""

import sys
import os
import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Imports for testing
from modules.inverse_mining_engine import (
    monte_carlo_inverso_optimized,
    generar_combinaciones_monte_carlo_inverso,
    integrar_monte_carlo_inverso_consenso
)
from core.consensus_engine import generar_combinaciones_consenso
from modules.score_dynamics import bonus_rare_numbers, calculate_shannon_entropy
from utils.validation import validate_combination

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MonteCarloInverseValidationTest:
    def __init__(self, historial_path: str = 'data/historial_kabala_github.csv'):
        """
        Initialize test suite with historical lottery data.
        
        Args:
            historial_path (str): Path to historical lottery data CSV
        """
        try:
            self.historial_df = pd.read_csv(historial_path)
            expected_cols = [f'Bolilla {i}' for i in range(1, 7)]
            
            # Validate DataFrame columns and content
            if not all(col in self.historial_df.columns for col in expected_cols):
                raise ValueError(f"Missing expected columns: {expected_cols}")
            
            self.historial_df = self.historial_df[expected_cols]
            
            logger.info(f"✅ Loaded historical data: {len(self.historial_df)} rows")
        except Exception as e:
            logger.error(f"❌ Failed to load historical data: {e}")
            raise
    
    def test_monte_carlo_inverse_basic(self, target_combination: List[int] = None) -> Dict[str, Any]:
        """
        Test basic Monte Carlo Inverse functionality.
        
        Args:
            target_combination (List[int], optional): Custom target combination. 
                                                     If None, generate a random one.
        
        Returns:
            Dict with analysis results and performance metrics
        """
        if target_combination is None:
            # Generate a random valid combination
            target_combination = sorted(np.random.choice(range(1, 41), size=6, replace=False))
        
        logger.info(f"🎲 Testing Monte Carlo Inverse for target: {target_combination}")
        
        result = monte_carlo_inverso_optimized(
            self.historial_df, 
            target_combination, 
            simulation_count=10000,
            confidence_level=0.95
        )
        
        # Validation checks
        assert 'enhanced_score' in result, "Missing enhanced score"
        assert 'rare_analysis' in result, "Missing rare analysis"
        assert 'confidence_intervals' in result, "Missing confidence intervals"
        
        logger.info(f"🚀 Analysis Results:")
        logger.info(f"   Enhanced Score: {result['enhanced_score']:.4f}")
        logger.info(f"   Rare Numbers: {result['rare_analysis']['rare_count']}")
        logger.info(f"   Rarity Score: {result['rare_analysis']['rarity_score']:.4f}")
        
        return result
    
    def test_rare_number_detection(self, rare_threshold: float = 0.15) -> float:
        """
        Test rare number detection performance.
        
        Args:
            rare_threshold (float): Threshold for considering a number rare
        
        Returns:
            Percentage of improved rare number detections
        """
        logger.info("🔍 Testing Rare Number Detection Performance")
        
        # Generate multiple combinations
        combinations = generar_combinaciones_monte_carlo_inverso(
            self.historial_df, 
            cantidad=50,  # Generate 50 combinations
            simulation_count=5000
        )
        
        # Track rare number performance
        total_rare_bonus = 0.0
        improved_rare_detections = 0
        
        for combo in combinations:
            rare_bonus = bonus_rare_numbers(combo['combination'], self.historial_df)
            total_rare_bonus += rare_bonus
            
            # Check for improved rare number detection
            entropy = calculate_shannon_entropy(combo['combination'])
            if entropy > 2.0 and rare_bonus > rare_threshold:
                improved_rare_detections += 1
        
        improvement_rate = (improved_rare_detections / len(combinations)) * 100
        
        logger.info(f"📊 Rare Number Detection Performance:")
        logger.info(f"   Total Combinations: {len(combinations)}")
        logger.info(f"   Improved Rare Detections: {improved_rare_detections}")
        logger.info(f"   Improvement Rate: {improvement_rate:.2f}%")
        logger.info(f"   Mean Rare Bonus: {total_rare_bonus / len(combinations):.4f}")
        
        return improvement_rate
    
    def test_consensus_integration(self, perfil_svi: str = 'exploratory') -> List[Dict[str, Any]]:
        """
        Test Monte Carlo Inverse integration with consensus engine.
        
        Args:
            perfil_svi (str): SVI profile for consensus generation
        
        Returns:
            List of combinations generated through consensus
        """
        logger.info(f"🤝 Testing Consensus Integration (Profile: {perfil_svi})")
        
        try:
            # Test consensus generation with Monte Carlo Inverse
            combinations = generar_combinaciones_consenso(
                self.historial_df,
                cantidad=50,
                perfil_svi=perfil_svi,
                exploration_mode=True,
                exploration_intensity=0.4
            )
            
            # Filter for Monte Carlo Inverse source
            mc_inverse_combos = [
                combo for combo in combinations 
                if combo.get('source', '') == 'monte_carlo_inverse'
            ]
            
            logger.info("📊 Consensus Integration Results:")
            logger.info(f"   Total Combinations: {len(combinations)}")
            logger.info(f"   Monte Carlo Inverse Combinations: {len(mc_inverse_combos)}")
            
            return mc_inverse_combos
        
        except Exception as e:
            logger.error(f"❌ Consensus integration failed: {e}")
            raise
    
    def run_comprehensive_validation(self):
        """
        Run comprehensive validation suite for Monte Carlo Inverse.
        """
        logger.info("🧪 Starting Comprehensive Monte Carlo Inverse Validation")
        
        # Test results storage
        test_results = {
            'basic_analysis': None,
            'rare_number_detection': None,
            'consensus_integration': None
        }
        
        # 1. Basic Monte Carlo Inverse Analysis
        test_results['basic_analysis'] = self.test_monte_carlo_inverse_basic()
        
        # 2. Rare Number Detection Performance
        test_results['rare_number_detection'] = self.test_rare_number_detection()
        
        # 3. Consensus Integration
        test_results['consensus_integration'] = self.test_consensus_integration()
        
        # Validation Reporting
        logger.info("\n🏆 VALIDATION SUMMARY 🏆")
        logger.info("1. Basic Monte Carlo Inverse Analysis:")
        logger.info(f"   Enhanced Score: {test_results['basic_analysis']['enhanced_score']:.4f}")
        logger.info(f"   Rare Numbers Detected: {test_results['basic_analysis']['rare_analysis']['rare_count']}")
        
        logger.info("\n2. Rare Number Detection Performance:")
        logger.info(f"   Improvement Rate: {test_results['rare_number_detection']:.2f}%")
        
        logger.info("\n3. Consensus Integration:")
        logger.info(f"   Total Combinations from Monte Carlo Inverse: {len(test_results['consensus_integration'])}")
        
        # Performance Assessment
        assert test_results['rare_number_detection'] >= 15, "Rare number detection improvement below threshold"
        assert test_results['basic_analysis']['enhanced_score'] > 0.5, "Basic analysis score too low"
        assert len(test_results['consensus_integration']) > 10, "Insufficient Monte Carlo Inverse combinations in consensus"
        
        logger.info("\n✅ VALIDATION PASSED SUCCESSFULLY ✅")
        return test_results

def main():
    validation_test = MonteCarloInverseValidationTest()
    validation_test.run_comprehensive_validation()

if __name__ == '__main__':
    main()