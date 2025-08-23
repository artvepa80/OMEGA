#!/usr/bin/env python3
# OMEGA_PRO_AI_v10.1/omega_ml_optimization_integration.py
"""
OMEGA PRO AI ML Optimization Integration Script
Integrates all ML enhancements targeting 65-70% accuracy improvement
Main execution script for enhanced OMEGA system
"""

import logging
import sys
import pandas as pd
import numpy as np
from pathlib import Path
import json
from typing import Dict, List, Any
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('omega_ml_optimization.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Import enhanced modules
from modules.advanced_feature_engineering import AdvancedFeatureEngineer, create_enhanced_features
from modules.lstm_model_enhanced import generar_combinaciones_lstm_enhanced
from modules.advanced_ensemble_system import generar_combinaciones_ensemble_advanced
from modules.model_optimization_suite import (
    generar_combinaciones_transformer_optimized,
    generar_combinaciones_gboost_optimized,
    HyperparameterOptimizer
)
from modules.accuracy_validation_framework import run_accuracy_validation

class OmegaMLOptimizationSystem:
    """
    Main ML Optimization System for OMEGA PRO AI
    
    Coordinates all enhanced models and validation processes
    Targeting 65-70% accuracy improvement from 50% baseline
    """
    
    def __init__(self, data_path: str = "data/historial_kabala_github.csv"):
        self.data_path = data_path
        self.historial_df = None
        self.enhanced_models = {}
        self.validation_results = {}
        
        # ML Enhancement Status
        self.enhancement_status = {
            'feature_engineering': False,
            'lstm_enhanced': False,
            'advanced_ensemble': False,
            'model_optimization': False,
            'validation_complete': False
        }
        
        logger.info("🚀 OMEGA ML Optimization System initialized")
        
    def load_and_prepare_data(self) -> bool:
        """Load and prepare historical data"""
        try:
            logger.info(f"📊 Loading data from {self.data_path}")
            
            if not Path(self.data_path).exists():
                logger.error(f"Data file not found: {self.data_path}")
                return False
            
            self.historial_df = pd.read_csv(self.data_path)
            
            # Validate data structure
            numeric_cols = [col for col in self.historial_df.columns 
                           if 'bolilla' in col.lower() or col.startswith('Bolilla')]
            
            if len(numeric_cols) < 6:
                logger.error(f"Insufficient lottery columns: {len(numeric_cols)}")
                return False
            
            logger.info(f"✅ Data loaded successfully: {len(self.historial_df)} draws, {len(numeric_cols)} ball columns")
            
            # Basic data validation
            for col in numeric_cols[:6]:
                if self.historial_df[col].isnull().any():
                    logger.warning(f"Null values found in {col}, filling with mode")
                    self.historial_df[col].fillna(self.historial_df[col].mode()[0], inplace=True)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading data: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def initialize_enhanced_feature_engineering(self) -> bool:
        """Initialize enhanced feature engineering"""
        try:
            logger.info("🔧 Initializing enhanced feature engineering...")
            
            engineer = AdvancedFeatureEngineer()
            
            # Test feature extraction
            feature_matrix = engineer.extract_comprehensive_features(self.historial_df.head(50))
            
            logger.info(f"✅ Feature engineering initialized: {feature_matrix.shape} features per draw")
            logger.info(f"📋 Feature categories: recency-weighted, position-specific, consecutive patterns, mathematical, temporal, momentum")
            
            self.enhancement_status['feature_engineering'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Feature engineering initialization failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_enhanced_lstm(self) -> bool:
        """Test enhanced LSTM with attention mechanisms"""
        try:
            logger.info("🧠 Testing enhanced LSTM model...")
            
            # Use subset for testing
            test_data = self.historial_df.head(100) if len(self.historial_df) > 100 else self.historial_df
            
            config = {
                'epochs': 20,  # Reduced for testing
                'use_attention': True,
                'use_bidirectional': True,
                'use_feature_fusion': True,
                'n_units': 128
            }
            
            combinations = generar_combinaciones_lstm_enhanced(test_data, cantidad=5, config=config)
            
            if len(combinations) == 5:
                logger.info("✅ Enhanced LSTM test successful")
                logger.info(f"📊 Sample combination: {combinations[0]['combination']}")
                logger.info(f"📊 Sample score: {combinations[0]['score']:.4f}")
                
                self.enhanced_models['enhanced_lstm'] = True
                self.enhancement_status['lstm_enhanced'] = True
                return True
            else:
                logger.error(f"Enhanced LSTM returned {len(combinations)} combinations, expected 5")
                return False
                
        except Exception as e:
            logger.error(f"❌ Enhanced LSTM test failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_advanced_ensemble(self) -> bool:
        """Test advanced ensemble system"""
        try:
            logger.info("🎯 Testing advanced ensemble system...")
            
            # Use subset for testing
            test_data = self.historial_df.head(150) if len(self.historial_df) > 150 else self.historial_df
            
            combinations = generar_combinaciones_ensemble_advanced(test_data, cantidad=10)
            
            if len(combinations) >= 5:  # Allow some flexibility
                logger.info("✅ Advanced ensemble test successful")
                logger.info(f"📊 Generated {len(combinations)} consensus combinations")
                
                # Analyze ensemble metrics
                consensus_ratios = []
                for combo in combinations:
                    metrics = combo.get('metrics', {})
                    if 'consensus_ratio' in metrics:
                        consensus_ratios.append(metrics['consensus_ratio'])
                
                if consensus_ratios:
                    avg_consensus = np.mean(consensus_ratios)
                    logger.info(f"📊 Average consensus ratio: {avg_consensus:.2%}")
                
                self.enhanced_models['advanced_ensemble'] = True
                self.enhancement_status['advanced_ensemble'] = True
                return True
            else:
                logger.error(f"Advanced ensemble returned {len(combinations)} combinations, expected ≥5")
                return False
                
        except Exception as e:
            logger.error(f"❌ Advanced ensemble test failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_optimized_models(self) -> bool:
        """Test optimized Transformer and GBoost models"""
        try:
            logger.info("🔧 Testing optimized models...")
            
            test_data = self.historial_df.head(100) if len(self.historial_df) > 100 else self.historial_df
            
            # Test optimized transformer
            try:
                transformer_combos = generar_combinaciones_transformer_optimized(test_data, cantidad=3)
                if len(transformer_combos) >= 2:  # Allow flexibility
                    logger.info("✅ Optimized Transformer working")
                    self.enhanced_models['optimized_transformer'] = True
                else:
                    logger.warning("⚠️ Optimized Transformer returned fewer combinations than expected")
            except Exception as e:
                logger.warning(f"⚠️ Optimized Transformer test failed: {e}")
                self.enhanced_models['optimized_transformer'] = False
            
            # Test optimized GBoost
            try:
                gboost_combos = generar_combinaciones_gboost_optimized(test_data, cantidad=3)
                if len(gboost_combos) >= 2:  # Allow flexibility
                    logger.info("✅ Optimized GBoost working")
                    self.enhanced_models['optimized_gboost'] = True
                else:
                    logger.warning("⚠️ Optimized GBoost returned fewer combinations than expected")
            except Exception as e:
                logger.warning(f"⚠️ Optimized GBoost test failed: {e}")
                self.enhanced_models['optimized_gboost'] = False
            
            # Consider successful if at least one optimized model works
            success = any([
                self.enhanced_models.get('optimized_transformer', False),
                self.enhanced_models.get('optimized_gboost', False)
            ])
            
            if success:
                self.enhancement_status['model_optimization'] = True
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Optimized models test failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def run_accuracy_validation(self) -> bool:
        """Run comprehensive accuracy validation"""
        try:
            logger.info("🧪 Running comprehensive accuracy validation...")
            
            # Use more data for validation if available
            validation_data = self.historial_df
            
            # Run validation with 50% baseline
            validation_results = run_accuracy_validation(validation_data, baseline_accuracy=0.50)
            
            self.validation_results = validation_results
            
            # Check if any model achieved target accuracy
            target_achieved = validation_results.get('assessment', {}).get('target_achieved', False)
            best_accuracy = validation_results.get('assessment', {}).get('best_accuracy', 0)
            
            logger.info(f"📊 Validation completed - Best accuracy: {best_accuracy:.1%}")
            logger.info(f"🎯 Target (65%) achieved: {'Yes' if target_achieved else 'No'}")
            
            self.enhancement_status['validation_complete'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Accuracy validation failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        
        report = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'system_status': 'OMEGA PRO AI ML Optimization Report',
            'data_info': {
                'total_draws': len(self.historial_df) if self.historial_df is not None else 0,
                'data_source': self.data_path
            },
            'enhancement_status': self.enhancement_status,
            'enhanced_models': self.enhanced_models,
            'validation_summary': {}
        }
        
        # Add validation summary if available
        if self.validation_results:
            assessment = self.validation_results.get('assessment', {})
            report['validation_summary'] = {
                'best_model': assessment.get('best_model'),
                'best_accuracy': assessment.get('best_accuracy'),
                'target_achieved': assessment.get('target_achieved'),
                'models_tested': assessment.get('models_tested'),
                'successful_models': assessment.get('successful_models')
            }
        
        # Calculate overall success
        enhancements_completed = sum(self.enhancement_status.values())
        total_enhancements = len(self.enhancement_status)
        
        report['overall_success'] = {
            'enhancements_completed': enhancements_completed,
            'total_enhancements': total_enhancements,
            'completion_rate': enhancements_completed / total_enhancements,
            'system_ready': enhancements_completed >= 3  # At least 3/5 enhancements working
        }
        
        return report
    
    def save_optimization_report(self, report: Dict[str, Any]):
        """Save optimization report to file"""
        try:
            output_dir = Path("results")
            output_dir.mkdir(exist_ok=True)
            
            filename = f"omega_ml_optimization_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = output_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"💾 Optimization report saved to {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Error saving report: {e}")
    
    def run_complete_optimization(self) -> Dict[str, Any]:
        """
        Run complete ML optimization process
        
        Returns comprehensive report on optimization results
        """
        logger.info("=" * 80)
        logger.info("🚀 STARTING OMEGA PRO AI ML OPTIMIZATION")
        logger.info("Target: Improve accuracy from 50% baseline to 65-70%")
        logger.info("=" * 80)
        
        success_steps = 0
        total_steps = 5
        
        # Step 1: Load and prepare data
        logger.info(f"\n[STEP 1/{total_steps}] Loading and preparing data...")
        if self.load_and_prepare_data():
            success_steps += 1
            logger.info("✅ Data loading successful")
        else:
            logger.error("❌ Data loading failed - aborting optimization")
            return {'error': 'Data loading failed', 'success': False}
        
        # Step 2: Initialize feature engineering
        logger.info(f"\n[STEP 2/{total_steps}] Initializing enhanced feature engineering...")
        if self.initialize_enhanced_feature_engineering():
            success_steps += 1
            logger.info("✅ Feature engineering successful")
        else:
            logger.error("❌ Feature engineering failed")
        
        # Step 3: Test enhanced LSTM
        logger.info(f"\n[STEP 3/{total_steps}] Testing enhanced LSTM with attention...")
        if self.test_enhanced_lstm():
            success_steps += 1
            logger.info("✅ Enhanced LSTM successful")
        else:
            logger.error("❌ Enhanced LSTM failed")
        
        # Step 4: Test advanced ensemble
        logger.info(f"\n[STEP 4/{total_steps}] Testing advanced ensemble system...")
        if self.test_advanced_ensemble():
            success_steps += 1
            logger.info("✅ Advanced ensemble successful")
        else:
            logger.error("❌ Advanced ensemble failed")
        
        # Step 5: Run validation
        logger.info(f"\n[STEP 5/{total_steps}] Running accuracy validation...")
        if self.run_accuracy_validation():
            success_steps += 1
            logger.info("✅ Validation successful")
        else:
            logger.error("❌ Validation failed")
        
        # Also test optimized models (bonus step)
        logger.info(f"\n[BONUS STEP] Testing optimized models...")
        self.test_optimized_models()
        
        # Generate final report
        report = self.generate_optimization_report()
        self.save_optimization_report(report)
        
        # Final summary
        logger.info("=" * 80)
        logger.info("🏁 OMEGA ML OPTIMIZATION COMPLETE")
        logger.info(f"✅ Successful steps: {success_steps}/{total_steps}")
        
        if self.validation_results:
            assessment = self.validation_results.get('assessment', {})
            best_accuracy = assessment.get('best_accuracy', 0)
            target_achieved = assessment.get('target_achieved', False)
            
            logger.info(f"🎯 Best accuracy achieved: {best_accuracy:.1%}")
            logger.info(f"🏆 Target (65%) achieved: {'YES' if target_achieved else 'NO'}")
            
            if target_achieved:
                logger.info("🎉 CONGRATULATIONS! Target accuracy improvement achieved!")
            else:
                improvement = (best_accuracy - 0.50) / 0.50 * 100
                logger.info(f"📈 Improvement over baseline: {improvement:.1f}%")
        
        logger.info("=" * 80)
        
        return report

def main():
    """Main execution function"""
    try:
        # Initialize optimization system
        optimizer = OmegaMLOptimizationSystem()
        
        # Run complete optimization
        report = optimizer.run_complete_optimization()
        
        # Print final status
        overall_success = report.get('overall_success', {})
        if overall_success.get('system_ready', False):
            print("\n🎉 OMEGA PRO AI ML Optimization SUCCESSFUL!")
            print("🚀 Enhanced system is ready for production use")
        else:
            print("\n⚠️ OMEGA PRO AI ML Optimization PARTIALLY SUCCESSFUL")
            print("🔧 Some enhancements may need additional tuning")
        
        return report
        
    except Exception as e:
        logger.error(f"❌ Critical error in main execution: {e}")
        logger.error(traceback.format_exc())
        return {'error': str(e), 'success': False}

if __name__ == "__main__":
    result = main()
    
    # Exit with appropriate code
    if result.get('success', True) and result.get('overall_success', {}).get('system_ready', False):
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Partial success or failure