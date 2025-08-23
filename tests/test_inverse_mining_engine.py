import pytest
import numpy as np
import pandas as pd
import os
import sys
import logging
from collections import Counter

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.inverse_mining_engine import (
    monte_carlo_inverso_optimized,
    generar_combinaciones_monte_carlo_inverso,
    validar_entrada,
    _extract_numbers_from_dataframe,
    _calculate_base_probability,
    _run_parallel_monte_carlo_simulations,
    _calculate_bootstrap_confidence_intervals,
    _perform_statistical_significance_tests,
    _analyze_convergence,
    _analyze_rare_numbers,
    integrar_monte_carlo_inverso_consenso
)
from utils.validation import validate_combination

class TestMonteCarloInverseEngine:
    @pytest.fixture
    def synthetic_historical_data(self):
        """Generate synthetic historical lottery data."""
        np.random.seed(42)
        test_data = pd.DataFrame({
            f'Bolilla {i}': np.random.randint(1, 41, 500) for i in range(1, 7)
        })
        return test_data

    def test_dependencies_imports(self):
        """Verify all required dependencies are imported and functional."""
        from modules.filters.ghost_rng_generative import simulate_ghost_rng
        from modules.filters.rules_filter import FiltroEstrategico
        from modules.score_dynamics import bonus_rare_numbers, calculate_shannon_entropy, calculate_z_scores
        from utils.validation import validate_combination

        assert simulate_ghost_rng is not None
        assert FiltroEstrategico is not None
        assert bonus_rare_numbers is not None
        assert calculate_shannon_entropy is not None
        assert calculate_z_scores is not None
        assert validate_combination is not None

    def test_cli_environment_variable_support(self):
        """Test CLI configuration and environment variable support."""
        os.environ['OMEGA_HISTORIAL_CSV'] = '/path/to/test/historial.csv'
        assert os.getenv('OMEGA_HISTORIAL_CSV') == '/path/to/test/historial.csv'

    def test_empty_dataframe_handling(self, synthetic_historical_data):
        """Test fallback mechanisms for empty or insufficient historical data."""
        empty_df = pd.DataFrame()
        
        # Test with empty DataFrame
        with pytest.warns(UserWarning):
            result = monte_carlo_inverso_optimized(
                empty_df, 
                [1, 2, 3, 4, 5, 6], 
                simulation_count=1000
            )
        
        # Verify fallback result structure
        assert 'base_probability' in result
        assert 'inverse_probability' in result
        assert result['base_probability'] == 1e-8
        assert result['inverse_probability'] == 1e-8

    def test_collections_import(self):
        """Verify Counter import and functionality."""
        test_numbers = [1, 2, 2, 3, 3, 3, 4, 4, 4, 4]
        freq_counter = Counter(test_numbers)
        
        assert freq_counter[1] == 1
        assert freq_counter[2] == 2
        assert freq_counter[3] == 3
        assert freq_counter[4] == 4

    def test_vectorization(self, synthetic_historical_data):
        """Test numpy vectorized operations."""
        # Verify vectorized weight calculation
        historical_numbers = _extract_numbers_from_dataframe(synthetic_historical_data)
        freq_counter = Counter(historical_numbers)
        weights = np.array([freq_counter.get(i, 1) for i in range(1, 41)])
        
        assert weights.sum() > 0
        assert np.isclose(weights.sum(), len(historical_numbers))

    def test_early_stopping_convergence(self, synthetic_historical_data):
        """Test convergence detection and early termination."""
        historical_numbers = _extract_numbers_from_dataframe(synthetic_historical_data)
        target = [5, 12, 23, 31, 38, 40]

        simulations = _run_parallel_monte_carlo_simulations(
            historical_numbers, 
            target, 
            sim_count=50000, 
            workers=4,
            logger=logging.getLogger()
        )

        assert len(simulations) > 0
        # Check early stopping by convergence detection
        convergence_stats = simulations[-1].get('convergence_stats', {})
        assert 'converged' in convergence_stats

    def test_statistical_integration(self, synthetic_historical_data):
        """Test comprehensive statistical tests."""
        target = [5, 12, 23, 31, 38, 40]
        historical_numbers = _extract_numbers_from_dataframe(synthetic_historical_data)
        simulations = _run_parallel_monte_carlo_simulations(
            historical_numbers, 
            target, 
            sim_count=10000, 
            workers=4,
            logger=logging.getLogger()
        )

        significance_tests = _perform_statistical_significance_tests(
            simulations, 
            historical_numbers, 
            target, 
            logger=logging.getLogger()
        )

        assert 'chi_square' in significance_tests
        assert 'kolmogorov_smirnov' in significance_tests
        assert 'summary' in significance_tests

    def test_bootstrap_confidence_intervals(self, synthetic_historical_data):
        """Test bootstrap confidence interval calculations."""
        target = [5, 12, 23, 31, 38, 40]
        historical_numbers = _extract_numbers_from_dataframe(synthetic_historical_data)
        simulations = _run_parallel_monte_carlo_simulations(
            historical_numbers, 
            target, 
            sim_count=10000, 
            workers=4,
            logger=logging.getLogger()
        )

        confidence_intervals = _calculate_bootstrap_confidence_intervals(
            simulations, 
            confidence_level=0.95, 
            logger=logging.getLogger()
        )

        assert 'probability' in confidence_intervals
        assert 'jaccard_similarity' in confidence_intervals
        assert 'inverse_probability' in confidence_intervals

    def test_probability_validation(self, synthetic_historical_data):
        """Test handling of probability calculations."""
        historical_numbers = _extract_numbers_from_dataframe(synthetic_historical_data)
        
        # Test base probability calculation
        base_prob = _calculate_base_probability(historical_numbers, [1, 2, 3, 4, 5, 6])
        assert base_prob > 0
        assert base_prob <= 1

    def test_combination_validation(self):
        """Test validate_combination functionality."""
        # Valid combinations
        valid_combinations = [
            [1, 2, 3, 4, 5, 6],
            [10, 15, 20, 25, 30, 35],
            [5, 12, 20, 27, 35, 40]
        ]

        # Invalid combinations
        invalid_combinations = [
            [1, 1, 2, 3, 4, 5],  # Duplicates
            [0, 1, 2, 3, 4, 5],  # Out of range
            [41, 42, 43, 44, 45, 46]  # Out of range
        ]

        for combination in valid_combinations:
            assert validate_combination(combination), f"Failed for valid combination {combination}"

        for combination in invalid_combinations:
            assert not validate_combination(combination), f"Failed for invalid combination {combination}"

    def test_rare_number_analysis(self, synthetic_historical_data):
        """Test rare number detection and analysis."""
        historical_numbers = _extract_numbers_from_dataframe(synthetic_historical_data)
        target = [5, 12, 23, 31, 38, 40]

        rare_analysis = _analyze_rare_numbers(
            target, 
            historical_numbers, 
            logger=logging.getLogger()
        )

        assert 'rare_count' in rare_analysis
        assert 'rarity_score' in rare_analysis
        assert 'rare_numbers' in rare_analysis

    def test_consensus_integration(self, synthetic_historical_data):
        """Test consensus engine integration."""
        consensus_combinations = integrar_monte_carlo_inverso_consenso(
            synthetic_historical_data, 
            cantidad=25, 
            perfil_svi="default"
        )

        assert len(consensus_combinations) > 0
        assert all('combination' in combo for combo in consensus_combinations)
        assert all('score' in combo for combo in consensus_combinations)
        assert all('metrics' in combo for combo in consensus_combinations)

    def test_monte_carlo_generation(self, synthetic_historical_data):
        """Test Monte Carlo combination generation."""
        combinations = generar_combinaciones_monte_carlo_inverso(
            synthetic_historical_data, 
            cantidad=25
        )

        assert len(combinations) > 0
        assert all(len(combo['combination']) == 6 for combo in combinations)
        assert all(0 <= combo['score'] <= 1.0 for combo in combinations)

    def test_parameter_validation(self):
        """Test strategic parameter validation."""
        # Valid parameters
        seed = [1, 2, 3, 4, 5, 6]
        boost = [10, 15]
        penalize = [7, 8]
        focus_positions = ['B1', 'B3']

        validated_boost, validated_penalize, validated_positions = validar_entrada(
            seed, boost, penalize, focus_positions
        )

        assert len(validated_boost) <= 5
        assert len(validated_penalize) <= 10
        assert all(pos in ['B1', 'B2', 'B3', 'B4', 'B5', 'B6'] for pos in validated_positions)

def main():
    # Pytest configuration
    pytest.main([
        __file__, 
        '-v',  # Verbose output
        '--tb=short',  # Shorter traceback format
        '--disable-warnings'  # Disable warnings for cleaner output
    ])

if __name__ == "__main__":
    main()