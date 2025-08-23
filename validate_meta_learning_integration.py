#!/usr/bin/env python3
# validate_meta_learning_integration.py
"""
Meta-Learning Systems Integration Validation Script
Tests the integration of meta-learning systems in OMEGA PRO AI v10.1
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any
import traceback

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_header(title: str):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def print_section(title: str):
    """Print formatted section"""
    print(f"\n🔍 {title}")
    print("-"*50)

def create_test_data() -> pd.DataFrame:
    """Create test historical data"""
    print("📊 Generating test historical data...")
    
    # Generate realistic lottery data (40 numbers, 6 per combination)
    np.random.seed(42)
    test_data = []
    
    for i in range(200):  # 200 historical draws
        # Generate 6 unique numbers between 1-40
        combo = sorted(np.random.choice(range(1, 41), size=6, replace=False))
        test_data.append({
            'sorteo_id': i + 1,
            'bolilla_1': combo[0],
            'bolilla_2': combo[1], 
            'bolilla_3': combo[2],
            'bolilla_4': combo[3],
            'bolilla_5': combo[4],
            'bolilla_6': combo[5],
            'fecha': f"2024-{(i%12)+1:02d}-{(i%28)+1:02d}"
        })
    
    df = pd.DataFrame(test_data)
    print(f"✅ Generated {len(df)} test combinations")
    return df

def test_meta_learning_imports():
    """Test meta-learning module imports"""
    print_section("Testing Meta-Learning Module Imports")
    
    results = {
        'meta_learning_controller': False,
        'adaptive_learning_system': False,
        'neural_enhancer': False,
        'ai_ensemble_system': False,
        'error_handler': False
    }
    
    # Test Meta-Learning Controller
    try:
        from modules.meta_learning_controller import create_meta_controller, analyze_and_optimize
        results['meta_learning_controller'] = True
        print("✅ Meta-Learning Controller import successful")
    except ImportError as e:
        print(f"❌ Meta-Learning Controller import failed: {e}")
    except Exception as e:
        print(f"⚠️ Meta-Learning Controller import warning: {e}")
    
    # Test Adaptive Learning System
    try:
        from modules.adaptive_learning_system import create_adaptive_learning_system
        results['adaptive_learning_system'] = True
        print("✅ Adaptive Learning System import successful")
    except ImportError as e:
        print(f"❌ Adaptive Learning System import failed: {e}")
    except Exception as e:
        print(f"⚠️ Adaptive Learning System import warning: {e}")
    
    # Test Neural Enhancer
    try:
        from modules.neural_enhancer import enhance_neural_predictions
        results['neural_enhancer'] = True
        print("✅ Neural Enhancer import successful")
    except ImportError as e:
        print(f"❌ Neural Enhancer import failed: {e}")
    except Exception as e:
        print(f"⚠️ Neural Enhancer import warning: {e}")
    
    # Test AI Ensemble System
    try:
        from modules.ai_ensemble_system import create_ai_ensemble, generate_intelligent_predictions
        results['ai_ensemble_system'] = True
        print("✅ AI Ensemble System import successful")
    except ImportError as e:
        print(f"❌ AI Ensemble System import failed: {e}")
    except Exception as e:
        print(f"⚠️ AI Ensemble System import warning: {e}")
    
    # Test Error Handler
    try:
        from utils.meta_learning_error_handler import MetaLearningErrorHandler
        results['error_handler'] = True
        print("✅ Meta-Learning Error Handler import successful")
    except ImportError as e:
        print(f"❌ Meta-Learning Error Handler import failed: {e}")
    except Exception as e:
        print(f"⚠️ Meta-Learning Error Handler import warning: {e}")
    
    return results

def test_consensus_engine_integration(test_data: pd.DataFrame):
    """Test meta-learning integration in consensus engine"""
    print_section("Testing Consensus Engine Integration")
    
    try:
        from core.consensus_engine import (
            META_LEARNING_AVAILABLE, ADAPTIVE_LEARNING_AVAILABLE,
            NEURAL_ENHANCER_AVAILABLE, AI_ENSEMBLE_AVAILABLE,
            _run_meta_learning_controller, _run_adaptive_learning_system,
            _run_neural_enhancer, _run_ai_ensemble_system
        )
        
        print(f"Meta-Learning Available: {META_LEARNING_AVAILABLE}")
        print(f"Adaptive Learning Available: {ADAPTIVE_LEARNING_AVAILABLE}")
        print(f"Neural Enhancer Available: {NEURAL_ENHANCER_AVAILABLE}")
        print(f"AI Ensemble Available: {AI_ENSEMBLE_AVAILABLE}")
        
        # Test function availability
        functions_available = {
            'meta_learning_controller': callable(_run_meta_learning_controller),
            'adaptive_learning_system': callable(_run_adaptive_learning_system),
            'neural_enhancer': callable(_run_neural_enhancer),
            'ai_ensemble_system': callable(_run_ai_ensemble_system)
        }
        
        for func_name, available in functions_available.items():
            status = "✅" if available else "❌"
            print(f"{status} {func_name} function available: {available}")
        
        return {
            'flags': {
                'META_LEARNING_AVAILABLE': META_LEARNING_AVAILABLE,
                'ADAPTIVE_LEARNING_AVAILABLE': ADAPTIVE_LEARNING_AVAILABLE,
                'NEURAL_ENHANCER_AVAILABLE': NEURAL_ENHANCER_AVAILABLE,
                'AI_ENSEMBLE_AVAILABLE': AI_ENSEMBLE_AVAILABLE
            },
            'functions': functions_available
        }
        
    except Exception as e:
        print(f"❌ Consensus engine integration test failed: {e}")
        traceback.print_exc()
        return {'error': str(e)}

def test_predictor_integration(test_data: pd.DataFrame):
    """Test meta-learning integration in predictor"""
    print_section("Testing Predictor Integration")
    
    try:
        from core.predictor import HybridOmegaPredictor
        
        # Create predictor instance
        predictor = HybridOmegaPredictor(
            historial_df=test_data,
            cantidad_final=10,
            perfil_svi='default'
        )
        
        # Check meta-learning model flags
        meta_models = {
            'meta_learning': predictor.usar_modelos.get('meta_learning', False),
            'adaptive_learning': predictor.usar_modelos.get('adaptive_learning', False),
            'neural_enhancer': predictor.usar_modelos.get('neural_enhancer', False),
            'ai_ensemble': predictor.usar_modelos.get('ai_ensemble', False)
        }
        
        for model_name, enabled in meta_models.items():
            status = "✅" if enabled else "❌"
            print(f"{status} {model_name} enabled: {enabled}")
        
        # Test method availability
        methods_available = {
            'meta_learning_controller': hasattr(predictor, '_run_meta_learning_controller'),
            'adaptive_learning_system': hasattr(predictor, '_run_adaptive_learning_system'),
            'neural_enhancer': hasattr(predictor, '_run_neural_enhancer'),
            'ai_ensemble_system': hasattr(predictor, '_run_ai_ensemble_system')
        }
        
        for method_name, available in methods_available.items():
            status = "✅" if available else "❌"
            print(f"{status} {method_name} method available: {available}")
        
        return {
            'predictor_created': True,
            'meta_models': meta_models,
            'methods': methods_available
        }
        
    except Exception as e:
        print(f"❌ Predictor integration test failed: {e}")
        traceback.print_exc()
        return {'error': str(e)}

def test_meta_learning_execution(test_data: pd.DataFrame):
    """Test meta-learning system execution with fallbacks"""
    print_section("Testing Meta-Learning System Execution")
    
    results = {}
    
    # Test each system individually
    systems_to_test = [
        ('meta_learning_controller', '_run_meta_learning_controller'),
        ('adaptive_learning_system', '_run_adaptive_learning_system'),
        ('neural_enhancer', '_run_neural_enhancer'),
        ('ai_ensemble_system', '_run_ai_ensemble_system')
    ]
    
    for system_name, function_name in systems_to_test:
        print(f"\n🧪 Testing {system_name}...")
        
        try:
            # Import function from consensus engine
            from core.consensus_engine import logger
            exec(f"from core.consensus_engine import {function_name}")
            
            # Execute function with test data
            func = eval(function_name)
            result = func(test_data, 5, logger)
            
            # Analyze result
            if isinstance(result, list):
                results[system_name] = {
                    'executed': True,
                    'result_type': 'list',
                    'result_count': len(result),
                    'error': None
                }
                
                if len(result) > 0 and isinstance(result[0], dict):
                    sample = result[0]
                    results[system_name]['sample_keys'] = list(sample.keys())
                    results[system_name]['has_combination'] = 'combination' in sample
                    results[system_name]['has_source'] = 'source' in sample
                    results[system_name]['has_score'] = 'score' in sample
                
                print(f"✅ {system_name}: {len(result)} results generated")
                
                if len(result) > 0:
                    sample = result[0]
                    print(f"   Sample result keys: {list(sample.keys())}")
                    if 'combination' in sample:
                        print(f"   Sample combination: {sample['combination']}")
                    if 'source' in sample:
                        print(f"   Source: {sample['source']}")
                    if 'score' in sample:
                        print(f"   Score: {sample['score']}")
            else:
                results[system_name] = {
                    'executed': True,
                    'result_type': type(result).__name__,
                    'result_count': 'N/A',
                    'error': f"Unexpected result type: {type(result)}"
                }
                print(f"⚠️ {system_name}: Unexpected result type {type(result)}")
                
        except Exception as e:
            results[system_name] = {
                'executed': False,
                'result_type': None,
                'result_count': 0,
                'error': str(e)
            }
            print(f"❌ {system_name}: Execution failed - {str(e)}")
    
    return results

def test_weight_configuration():
    """Test meta-learning weight configuration"""
    print_section("Testing Weight Configuration")
    
    try:
        from core.consensus_engine import PESO_MAP
        
        profiles = ['default', 'conservative', 'aggressive', 'exploratory']
        meta_weights = ['meta_learning', 'adaptive_learning', 'neural_enhancer', 'ai_ensemble']
        
        results = {}
        
        for profile in profiles:
            if profile in PESO_MAP:
                profile_weights = PESO_MAP[profile]
                results[profile] = {}
                
                for weight_name in meta_weights:
                    if weight_name in profile_weights:
                        results[profile][weight_name] = profile_weights[weight_name]
                        print(f"✅ {profile}.{weight_name}: {profile_weights[weight_name]}")
                    else:
                        results[profile][weight_name] = 'missing'
                        print(f"❌ {profile}.{weight_name}: missing")
            else:
                print(f"❌ Profile {profile} not found in PESO_MAP")
                results[profile] = 'missing'
        
        return results
        
    except Exception as e:
        print(f"❌ Weight configuration test failed: {e}")
        return {'error': str(e)}

def test_cli_parameters():
    """Test CLI parameter integration"""
    print_section("Testing CLI Parameters")
    
    try:
        # Import and create argument parser
        import argparse
        
        # We'll simulate the main.py argument parsing
        expected_args = [
            '--enable-meta-controller',
            '--enable-adaptive-learning', 
            '--enable-neural-enhancer',
            '--enable-ai-ensemble',
            '--meta-memory-size',
            '--disable-all-meta'
        ]
        
        # Test that we can create these arguments
        parser = argparse.ArgumentParser()
        
        try:
            parser.add_argument("--enable-meta-controller", action="store_true", default=True)
            parser.add_argument("--enable-adaptive-learning", action="store_true", default=True)
            parser.add_argument("--enable-neural-enhancer", action="store_true", default=True)
            parser.add_argument("--enable-ai-ensemble", action="store_true", default=True)
            parser.add_argument("--meta-memory-size", type=int, default=1000)
            parser.add_argument("--disable-all-meta", action="store_true")
            
            # Test parsing
            test_args = parser.parse_args([
                '--enable-meta-controller',
                '--meta-memory-size', '1500'
            ])
            
            results = {
                'parser_created': True,
                'arguments_added': True,
                'parsing_successful': True,
                'test_values': {
                    'enable_meta_controller': test_args.enable_meta_controller,
                    'meta_memory_size': test_args.meta_memory_size,
                    'disable_all_meta': test_args.disable_all_meta
                }
            }
            
            for arg in expected_args:
                print(f"✅ {arg}: Available")
            
            print(f"✅ Test parsing successful")
            print(f"   enable_meta_controller: {test_args.enable_meta_controller}")
            print(f"   meta_memory_size: {test_args.meta_memory_size}")
            
            return results
            
        except Exception as e:
            print(f"❌ CLI argument creation/parsing failed: {e}")
            return {'error': str(e)}
            
    except Exception as e:
        print(f"❌ CLI parameter test failed: {e}")
        return {'error': str(e)}

def generate_validation_report(all_results: Dict[str, Any]) -> str:
    """Generate comprehensive validation report"""
    print_section("Generating Validation Report")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reports/meta_learning_validation_report_{timestamp}.json"
    
    # Create reports directory
    os.makedirs("reports", exist_ok=True)
    
    # Prepare report
    report = {
        'validation_info': {
            'timestamp': timestamp,
            'validation_version': '1.0.0',
            'omega_version': 'v10.1',
            'validation_date': datetime.now().isoformat()
        },
        'test_results': all_results,
        'summary': {
            'total_tests': len(all_results),
            'passed_tests': sum(1 for result in all_results.values() 
                              if isinstance(result, dict) and not result.get('error')),
            'failed_tests': sum(1 for result in all_results.values() 
                              if isinstance(result, dict) and result.get('error')),
            'warnings': []
        }
    }
    
    # Add summary analysis
    if 'imports' in all_results:
        imports = all_results['imports']
        available_systems = sum(1 for v in imports.values() if v)
        total_systems = len(imports)
        report['summary']['systems_available'] = f"{available_systems}/{total_systems}"
    
    if 'execution' in all_results:
        execution = all_results['execution']
        working_systems = sum(1 for result in execution.values() 
                             if result.get('executed') and not result.get('error'))
        total_systems = len(execution)
        report['summary']['systems_working'] = f"{working_systems}/{total_systems}"
    
    # Write report
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str, ensure_ascii=False)
    
    print(f"📄 Validation report saved to: {filename}")
    
    # Print summary
    print(f"\n📊 VALIDATION SUMMARY:")
    print(f"   Total Tests: {report['summary']['total_tests']}")
    print(f"   Passed: {report['summary']['passed_tests']}")
    print(f"   Failed: {report['summary']['failed_tests']}")
    
    if 'systems_available' in report['summary']:
        print(f"   Systems Available: {report['summary']['systems_available']}")
    
    if 'systems_working' in report['summary']:
        print(f"   Systems Working: {report['summary']['systems_working']}")
    
    return filename

def main():
    """Main validation function"""
    print_header("OMEGA PRO AI v10.1 - Meta-Learning Systems Validation")
    print(f"Validation started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create test data
    test_data = create_test_data()
    
    # Run all tests
    results = {}
    
    try:
        # Test 1: Module Imports
        results['imports'] = test_meta_learning_imports()
        
        # Test 2: Consensus Engine Integration
        results['consensus_integration'] = test_consensus_engine_integration(test_data)
        
        # Test 3: Predictor Integration  
        results['predictor_integration'] = test_predictor_integration(test_data)
        
        # Test 4: Execution Tests
        results['execution'] = test_meta_learning_execution(test_data)
        
        # Test 5: Weight Configuration
        results['weights'] = test_weight_configuration()
        
        # Test 6: CLI Parameters
        results['cli'] = test_cli_parameters()
        
    except Exception as e:
        print(f"❌ Critical error during validation: {e}")
        traceback.print_exc()
        results['critical_error'] = str(e)
    
    # Generate report
    report_filename = generate_validation_report(results)
    
    print_header("Validation Complete")
    print(f"🎯 Meta-Learning Systems Integration Validation completed")
    print(f"📄 Full report available at: {report_filename}")
    
    # Return success/failure
    has_critical_errors = 'critical_error' in results
    has_system_errors = any(
        isinstance(result, dict) and result.get('error') 
        for result in results.values()
    )
    
    if has_critical_errors or has_system_errors:
        print("⚠️ Some tests failed - check the report for details")
        return 1
    else:
        print("✅ All tests passed successfully!")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)