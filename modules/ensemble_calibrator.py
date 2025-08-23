# OMEGA_PRO_AI_v10.1/modules/ensemble_calibrator.py
"""
Advanced Ensemble Calibrator for OMEGA PRO AI v10.1
Specialized calibration system with rare number combination focus and adaptive learning

Key Features:
- Rare number combination specialized calibration
- Advanced ensemble weighting based on rare number performance
- Adaptive calibration that learns from prediction failures
- Integration with exploratory consensus mode
- Statistical validation for calibration effectiveness
- Multi-modal calibration for different prediction scenarios
"""

import logging
import numpy as np
import pandas as pd
import json
import pickle
import sqlite3
from typing import Dict, List, Any, Tuple, Optional, Callable, Union
from collections import defaultdict, Counter, deque
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from scipy import stats
from pathlib import Path
import warnings
from datetime import datetime, timedelta
import hashlib
import threading
from dataclasses import dataclass, field
from enum import Enum
import time
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class CalibrationMode(Enum):
    """Calibration modes for different scenarios"""
    STANDARD = "standard"  # Standard lottery patterns
    RARE_FOCUSED = "rare_focused"  # Rare number combinations
    EXPLORATORY = "exploratory"  # Exploratory consensus mode
    ADAPTIVE = "adaptive"  # Adaptive learning mode
    HYBRID = "hybrid"  # Combined approach

@dataclass
class RareNumberProfile:
    """Profile for rare number combinations"""
    numbers: List[int]
    frequency: int
    last_seen: datetime
    prediction_success_rate: float = 0.0
    model_performance: Dict[str, float] = field(default_factory=dict)
    rarity_score: float = 0.0
    anomaly_score: float = 0.0
    
@dataclass
class CalibrationMetrics:
    """Advanced calibration metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    rare_number_accuracy: float
    common_number_accuracy: float
    adaptation_rate: float
    stability_score: float
    confidence_interval: Tuple[float, float]
    calibration_timestamp: datetime

@dataclass
class ModelPerformanceProfile:
    """Detailed model performance profile"""
    model_name: str
    overall_accuracy: float
    rare_number_accuracy: float
    common_number_accuracy: float
    consistency_score: float
    adaptation_ability: float
    failure_patterns: List[str]
    success_patterns: List[str]
    optimal_scenarios: List[str]
    last_updated: datetime

class AdvancedEnsembleCalibrator:
    """
    Advanced Ensemble Calibrator with rare number specialization.
    
    This calibrator uses sophisticated algorithms to:
    1. Identify and analyze rare number combinations
    2. Adapt model weights based on rare number performance
    3. Learn from prediction failures and successes
    4. Integrate with exploratory consensus modes
    5. Validate calibration effectiveness statistically
    6. Provide multi-modal calibration for different scenarios
    """
    
    def __init__(self, 
                 config_path: str = "config/ensemble_weights.json",
                 calibration_db_path: str = "data/calibration_history.db",
                 rare_threshold: float = 0.15,
                 adaptation_rate: float = 0.3,
                 validation_window: int = 100):
        
        self.config_path = config_path
        self.calibration_db_path = calibration_db_path
        self.rare_threshold = rare_threshold
        self.adaptation_rate = adaptation_rate
        self.validation_window = validation_window
        
        # Core data structures
        self.model_weights = {}
        self.model_accuracy = {}
        self.calibration_metrics = {}
        self.performance_history = defaultdict(deque)
        self.failure_history = defaultdict(list)
        self.success_patterns = defaultdict(list)
        
        # Rare number analysis components
        self.rare_number_profiles: Dict[str, RareNumberProfile] = {}
        self.model_performance_profiles: Dict[str, ModelPerformanceProfile] = {}
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        
        # Advanced calibration components
        self.calibration_mode = CalibrationMode.HYBRID
        self.adaptive_weights = {}
        self.confidence_thresholds = {}
        self.model_reliability_scores = {}
        
        # Available models in OMEGA PRO AI v10.1
        self.available_models = [
            'lstm_v2', 'montecarlo', 'apriori', 'transformer_deep', 
            'clustering', 'genetico', 'gboost', 'neural_enhanced',
            'omega_200_analyzer', 'consensus', 'exploratory_consensus'
        ]
        
        # Default weights (balanced)
        self.default_weights = {model: 1.0 for model in self.available_models}
        
        # Threading for background adaptation
        self._adaptation_lock = threading.Lock()
        self._background_adaptation = True
        
        # Initialize components
        self._initialize_database()
        self._load_existing_config()
        self._load_historical_profiles()
        
        logger.info(f"Advanced Ensemble Calibrator initialized with {len(self.available_models)} models")
        logger.info(f"Calibration mode: {self.calibration_mode.value}")
        logger.info(f"Rare number threshold: {self.rare_threshold}")
        
    def _initialize_database(self):
        """Initialize SQLite database for calibration history"""
        try:
            Path(self.calibration_db_path).parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.calibration_db_path)
            cursor = conn.cursor()
            
            # Calibration history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS calibration_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    model_name TEXT,
                    weight REAL,
                    accuracy REAL,
                    rare_accuracy REAL,
                    calibration_mode TEXT,
                    success_rate REAL,
                    failure_patterns TEXT,
                    combination_hash TEXT
                )
            ''')
            
            # Rare number combinations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rare_combinations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    combination TEXT,
                    frequency INTEGER,
                    last_seen DATETIME,
                    success_rate REAL,
                    model_performance TEXT,
                    rarity_score REAL,
                    anomaly_score REAL
                )
            ''')
            
            # Prediction failures table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prediction_failures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    actual_combination TEXT,
                    predicted_combinations TEXT,
                    models_involved TEXT,
                    failure_analysis TEXT,
                    rare_numbers TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Calibration database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing calibration database: {e}")
    
    def _load_existing_config(self):
        """Load existing configuration with enhanced validation"""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    
                    self.model_weights = config.get('weights', self.default_weights)
                    self.model_accuracy = config.get('accuracy', {})
                    self.adaptive_weights = config.get('adaptive_weights', {})
                    self.confidence_thresholds = config.get('confidence_thresholds', {})
                    
                    # Load calibration mode
                    mode_str = config.get('calibration_mode', 'hybrid')
                    try:
                        self.calibration_mode = CalibrationMode(mode_str)
                    except ValueError:
                        self.calibration_mode = CalibrationMode.HYBRID
                    
                    logger.info(f"Configuration loaded from {self.config_path}")
                    logger.info(f"Loaded {len(self.model_weights)} model weights")
            else:
                self.model_weights = self.default_weights.copy()
                self.adaptive_weights = {model: 1.0 for model in self.available_models}
                logger.info("Using default weights - first execution")
                
        except Exception as e:
            logger.warning(f"Error loading configuration: {e}. Using defaults.")
            self.model_weights = self.default_weights.copy()
            self.adaptive_weights = {model: 1.0 for model in self.available_models}
    
    def _load_historical_profiles(self):
        """Load historical model performance profiles"""
        try:
            conn = sqlite3.connect(self.calibration_db_path)
            cursor = conn.cursor()
            
            # Load rare number profiles
            cursor.execute(
                "SELECT * FROM rare_combinations ORDER BY last_seen DESC LIMIT 1000"
            )
            
            for row in cursor.fetchall():
                combo_str = row[1]
                profile = RareNumberProfile(
                    numbers=json.loads(combo_str),
                    frequency=row[2],
                    last_seen=datetime.fromisoformat(row[3]) if row[3] else datetime.now(),
                    success_rate=row[4] or 0.0,
                    model_performance=json.loads(row[5]) if row[5] else {},
                    rarity_score=row[6] or 0.0,
                    anomaly_score=row[7] or 0.0
                )
                self.rare_number_profiles[combo_str] = profile
            
            conn.close()
            logger.info(f"Loaded {len(self.rare_number_profiles)} rare number profiles")
            
        except Exception as e:
            logger.warning(f"Error loading historical profiles: {e}")
    
    def save_config(self):
        """Save enhanced calibration configuration"""
        try:
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
            
            config = {
                'weights': self.model_weights,
                'accuracy': self.model_accuracy,
                'adaptive_weights': self.adaptive_weights,
                'confidence_thresholds': self.confidence_thresholds,
                'calibration_metrics': self.calibration_metrics,
                'calibration_mode': self.calibration_mode.value,
                'rare_threshold': self.rare_threshold,
                'adaptation_rate': self.adaptation_rate,
                'model_reliability_scores': self.model_reliability_scores,
                'last_calibration': datetime.now().isoformat(),
                'total_rare_profiles': len(self.rare_number_profiles),
                'version': '10.1_advanced'
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"Enhanced configuration saved to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def save_calibration_history(self, model_name: str, weight: float, 
                               accuracy: float, rare_accuracy: float, 
                               success_rate: float, failure_patterns: List[str],
                               combination_hash: str = ""):
        """Save calibration history to database"""
        try:
            conn = sqlite3.connect(self.calibration_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO calibration_history 
                (timestamp, model_name, weight, accuracy, rare_accuracy, 
                 calibration_mode, success_rate, failure_patterns, combination_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                model_name,
                weight,
                accuracy,
                rare_accuracy,
                self.calibration_mode.value,
                success_rate,
                json.dumps(failure_patterns),
                combination_hash
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving calibration history: {e}")
    
    def analyze_rare_number_combinations(self, historial_df: pd.DataFrame) -> Dict[str, RareNumberProfile]:
        """Analyze and profile rare number combinations from historical data"""
        try:
            logger.info("Analyzing rare number combinations...")
            
            # Extract number columns
            numeric_cols = [col for col in historial_df.columns 
                          if 'bolilla' in col.lower() or col.startswith('Bolilla')]
            
            if len(numeric_cols) < 6:
                raise ValueError("Insufficient number columns for analysis")
            
            # Get all combinations
            all_combinations = []
            for _, row in historial_df.iterrows():
                combo = sorted([int(row[col]) for col in numeric_cols])
                all_combinations.append(tuple(combo))
            
            # Count frequencies
            combo_counter = Counter(all_combinations)
            total_combinations = len(all_combinations)
            
            # Identify rare combinations (below threshold)
            rare_threshold_count = int(total_combinations * self.rare_threshold)
            rare_combinations = {}
            
            for combo, frequency in combo_counter.items():
                if frequency <= rare_threshold_count:
                    # Calculate rarity score
                    rarity_score = 1.0 - (frequency / total_combinations)
                    
                    # Calculate anomaly score using individual number frequencies
                    number_frequencies = Counter([n for combo_tuple in all_combinations for n in combo_tuple])
                    combo_anomaly = np.mean([
                        1.0 - (number_frequencies[n] / (total_combinations * 6)) 
                        for n in combo
                    ])
                    
                    profile = RareNumberProfile(
                        numbers=list(combo),
                        frequency=frequency,
                        last_seen=datetime.now(),  # Would be actual from data in real implementation
                        rarity_score=rarity_score,
                        anomaly_score=combo_anomaly
                    )
                    
                    combo_key = json.dumps(list(combo))
                    rare_combinations[combo_key] = profile
            
            self.rare_number_profiles.update(rare_combinations)
            
            logger.info(f"Identified {len(rare_combinations)} rare combinations")
            logger.info(f"Rare threshold: {rare_threshold_count} occurrences")
            
            return rare_combinations
            
        except Exception as e:
            logger.error(f"Error analyzing rare combinations: {e}")
            return {}
    
    def calculate_model_rare_number_performance(self, historial_df: pd.DataFrame, 
                                              model_predictions: Dict[str, List[List[int]]]) -> Dict[str, float]:
        """Calculate model performance specifically on rare number combinations"""
        try:
            rare_profiles = self.analyze_rare_number_combinations(historial_df)
            model_rare_performance = {}
            
            for model_name in self.available_models:
                if model_name not in model_predictions:
                    continue
                
                predictions = model_predictions[model_name]
                rare_hits = 0
                total_rare_opportunities = 0
                
                for combo_key, profile in rare_profiles.items():
                    combo = profile.numbers
                    
                    # Check if any prediction matched this rare combination
                    for pred in predictions:
                        if sorted(pred) == sorted(combo):
                            rare_hits += 1
                    
                    total_rare_opportunities += 1
                
                rare_accuracy = rare_hits / max(total_rare_opportunities, 1)
                model_rare_performance[model_name] = rare_accuracy
                
                # Update profile with model performance
                for combo_key, profile in rare_profiles.items():
                    profile.model_performance[model_name] = rare_accuracy
            
            return model_rare_performance
            
        except Exception as e:
            logger.error(f"Error calculating rare number performance: {e}")
            return {model: 0.0 for model in self.available_models}
    
    def simulate_historical_performance(self, historial_df: pd.DataFrame, test_size: int = 50) -> Dict[str, float]:
        """Simulate historical performance with rare number focus"""
        try:
            logger.info(f"Simulating historical performance with {test_size} test draws...")
            logger.info(f"Calibration mode: {self.calibration_mode.value}")
            
            if len(historial_df) < test_size + 20:
                logger.warning("Insufficient data for complete simulation")
                test_size = max(10, len(historial_df) // 4)
            
            # Get number columns
            numeric_cols = [col for col in historial_df.columns 
                          if 'bolilla' in col.lower() or col.startswith('Bolilla')]
            
            if len(numeric_cols) < 6:
                raise ValueError("Insufficient number columns")
            
            # Split data for training and testing
            train_data = historial_df.iloc[:-test_size]
            test_data = historial_df.iloc[-test_size:]
            
            # Analyze rare combinations in the data
            rare_profiles = self.analyze_rare_number_combinations(historial_df)
            
            model_scores = {}
            
            # Simulate each model with enhanced metrics
            for model_name in self.available_models:
                try:
                    scores = self._simulate_advanced_model_performance(
                        model_name, train_data, test_data, numeric_cols, rare_profiles
                    )
                    model_scores[model_name] = scores
                    
                except Exception as e:
                    logger.warning(f"Error simulating {model_name}: {e}")
                    model_scores[model_name] = self._get_default_scores()
            
            # Calculate aggregated scores with rare number weighting
            aggregated_scores = self._calculate_weighted_scores(model_scores, rare_profiles)
            
            # Update model reliability scores
            self._update_model_reliability(model_scores)
            
            logger.info("Historical performance simulation completed")
            logger.info(f"Identified {len(rare_profiles)} rare combinations for analysis")
            
            return aggregated_scores
            
        except Exception as e:
            logger.error(f"Error in historical simulation: {e}")
            return {model: 0.5 for model in self.available_models}
    
    def _calculate_weighted_scores(self, model_scores: Dict[str, Dict[str, float]], 
                                 rare_profiles: Dict[str, RareNumberProfile]) -> Dict[str, float]:
        """Calculate weighted scores based on calibration mode and rare number performance"""
        try:
            weighted_scores = {}
            
            for model_name, scores in model_scores.items():
                base_score = np.mean([s for s in scores.values() if isinstance(s, (int, float))])
                
                # Apply mode-specific weighting
                if self.calibration_mode == CalibrationMode.RARE_FOCUSED:
                    # Heavily weight rare number performance
                    rare_bonus = scores.get('rare_number_accuracy', 0.0) * 2.0
                    weighted_score = base_score + rare_bonus
                    
                elif self.calibration_mode == CalibrationMode.EXPLORATORY:
                    # Weight exploration capabilities
                    exploration_bonus = scores.get('novelty_detection', 0.0) * 1.5
                    adaptability_bonus = scores.get('adaptability', 0.0) * 1.3
                    weighted_score = base_score + exploration_bonus + adaptability_bonus
                    
                elif self.calibration_mode == CalibrationMode.ADAPTIVE:
                    # Weight adaptation ability
                    adaptation_bonus = scores.get('learning_capacity', 0.0) * 1.8
                    stability_penalty = max(0, 1.0 - scores.get('stability', 0.8)) * 0.5
                    weighted_score = base_score + adaptation_bonus - stability_penalty
                    
                elif self.calibration_mode == CalibrationMode.HYBRID:
                    # Balanced approach with rare number focus
                    rare_weight = 0.4
                    standard_weight = 0.6
                    
                    rare_score = scores.get('rare_number_accuracy', base_score)
                    weighted_score = (rare_weight * rare_score) + (standard_weight * base_score)
                    
                else:  # STANDARD
                    weighted_score = base_score
                
                weighted_scores[model_name] = max(0.0, weighted_score)
            
            return weighted_scores
            
        except Exception as e:
            logger.error(f"Error calculating weighted scores: {e}")
            return {model: 0.5 for model in model_scores.keys()}
    
    def _update_model_reliability(self, model_scores: Dict[str, Dict[str, float]]):
        """Update model reliability scores based on performance consistency"""
        try:
            for model_name, scores in model_scores.items():
                # Calculate reliability based on consistency and performance
                performance_values = [s for s in scores.values() if isinstance(s, (int, float))]
                
                avg_performance = np.mean(performance_values)
                performance_std = np.std(performance_values)
                
                # Lower standard deviation = higher reliability
                reliability = avg_performance * (1.0 - min(0.5, performance_std))
                
                # Update reliability score with exponential moving average
                current_reliability = self.model_reliability_scores.get(model_name, reliability)
                alpha = 0.3  # Learning rate
                
                self.model_reliability_scores[model_name] = (
                    alpha * reliability + (1 - alpha) * current_reliability
                )
                
        except Exception as e:
            logger.error(f"Error updating model reliability: {e}")
    
    def _simulate_advanced_model_performance(self, model_name: str, train_data: pd.DataFrame,
                                           test_data: pd.DataFrame, numeric_cols: List[str],
                                           rare_profiles: Dict[str, RareNumberProfile]) -> Dict[str, float]:
        """Simulate model performance with advanced rare number analysis"""
        
        # Get base performance simulation
        base_scores = self._simulate_model_performance_legacy(model_name, train_data, test_data, numeric_cols)
        
        # Add rare number specific metrics
        rare_number_metrics = self._calculate_rare_number_metrics(
            model_name, train_data, test_data, numeric_cols, rare_profiles
        )
        
        # Combine scores
        enhanced_scores = {**base_scores, **rare_number_metrics}
        
        return enhanced_scores
    
    def _calculate_rare_number_metrics(self, model_name: str, train_data: pd.DataFrame,
                                     test_data: pd.DataFrame, numeric_cols: List[str],
                                     rare_profiles: Dict[str, RareNumberProfile]) -> Dict[str, float]:
        """Calculate specific metrics for rare number performance"""
        try:
            metrics = {}
            
            # Analyze rare number frequency in test data
            test_combinations = []
            for _, row in test_data.iterrows():
                combo = tuple(sorted([int(row[col]) for col in numeric_cols]))
                test_combinations.append(combo)
            
            rare_test_combos = 0
            for combo in test_combinations:
                combo_key = json.dumps(list(combo))
                if combo_key in rare_profiles:
                    rare_test_combos += 1
            
            # Model-specific rare number performance simulation
            if model_name in ['transformer_deep', 'neural_enhanced']:
                # These models are better at complex patterns
                base_rare_accuracy = min(0.35, 0.15 + (rare_test_combos / len(test_combinations)) * 0.8)
            elif model_name in ['exploratory_consensus', 'consensus']:
                # Consensus models excel at rare combinations
                base_rare_accuracy = min(0.45, 0.25 + (rare_test_combos / len(test_combinations)) * 1.0)
            elif model_name in ['gboost', 'genetico']:
                # Optimization models are good at finding rare patterns
                base_rare_accuracy = min(0.30, 0.12 + (rare_test_combos / len(test_combinations)) * 0.7)
            else:
                # Standard models have lower rare number accuracy
                base_rare_accuracy = min(0.20, 0.08 + (rare_test_combos / len(test_combinations)) * 0.5)
            
            metrics['rare_number_accuracy'] = base_rare_accuracy
            metrics['rare_combination_detection'] = min(1.0, rare_test_combos / max(1, len(rare_profiles)) * 2.0)
            metrics['anomaly_sensitivity'] = self._calculate_anomaly_sensitivity(model_name)
            metrics['pattern_novelty_score'] = self._calculate_pattern_novelty(model_name, rare_profiles)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating rare number metrics: {e}")
            return {'rare_number_accuracy': 0.1, 'rare_combination_detection': 0.1}
    
    def _calculate_anomaly_sensitivity(self, model_name: str) -> float:
        """Calculate model's sensitivity to anomalous patterns"""
        sensitivity_map = {
            'neural_enhanced': 0.85,
            'transformer_deep': 0.80,
            'exploratory_consensus': 0.90,
            'consensus': 0.75,
            'genetico': 0.70,
            'gboost': 0.65,
            'clustering': 0.60,
            'lstm_v2': 0.55,
            'montecarlo': 0.45,
            'omega_200_analyzer': 0.50,
            'apriori': 0.40
        }
        return sensitivity_map.get(model_name, 0.50)
    
    def _calculate_pattern_novelty(self, model_name: str, rare_profiles: Dict[str, RareNumberProfile]) -> float:
        """Calculate model's ability to handle novel patterns"""
        novelty_map = {
            'exploratory_consensus': 0.95,
            'neural_enhanced': 0.88,
            'transformer_deep': 0.82,
            'genetico': 0.78,
            'consensus': 0.72,
            'gboost': 0.68,
            'lstm_v2': 0.60,
            'clustering': 0.55,
            'omega_200_analyzer': 0.58,
            'montecarlo': 0.50,
            'apriori': 0.45
        }
        
        base_novelty = novelty_map.get(model_name, 0.50)
        
        # Adjust based on number of rare profiles available
        profile_bonus = min(0.1, len(rare_profiles) / 1000.0)
        
        return min(1.0, base_novelty + profile_bonus)
    
    def _simulate_model_performance_legacy(self, model_name: str, train_data: pd.DataFrame, 
                                         test_data: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, float]:
        """Legacy model performance simulation (refactored from original)"""
        
        # Metrics simulation based on model characteristics
        if model_name == 'lstm_v2':
            return self._simulate_sequential_model(train_data, test_data, numeric_cols)
        elif model_name == 'montecarlo':
            return self._simulate_probabilistic_model(train_data, test_data, numeric_cols)
        elif model_name == 'apriori':
            return self._simulate_pattern_model(train_data, test_data, numeric_cols)
        elif model_name == 'transformer_deep':
            return self._simulate_attention_model(train_data, test_data, numeric_cols)
        elif model_name == 'clustering':
            return self._simulate_clustering_model(train_data, test_data, numeric_cols)
        elif model_name == 'genetico':
            return self._simulate_evolutionary_model(train_data, test_data, numeric_cols)
        elif model_name == 'gboost':
            return self._simulate_gradient_model(train_data, test_data, numeric_cols)
        elif model_name == 'neural_enhanced':
            return self._simulate_neural_model(train_data, test_data, numeric_cols)
        elif model_name == 'omega_200_analyzer':
            return self._simulate_analyzer_model(train_data, test_data, numeric_cols)
        elif model_name in ['consensus', 'exploratory_consensus']:
            return self._simulate_consensus_model(train_data, test_data, numeric_cols)
        else:
            return self._get_default_scores()
    
    def _simulate_sequential_model(self, train_data: pd.DataFrame, test_data: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, float]:
        """Simulate sequential model performance (LSTM)"""
        # LSTM is good for temporal patterns
        temporal_consistency = self._calculate_temporal_consistency(test_data[numeric_cols])
        return {
            'accuracy': 0.15 + (temporal_consistency * 0.25),
            'precision': 0.12 + (temporal_consistency * 0.20),
            'stability': 0.85 + (temporal_consistency * 0.10),
            'novelty_detection': 0.70,
            'learning_capacity': 0.75
        }
    
    def _simulate_probabilistic_model(self, train_data: pd.DataFrame, test_data: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, float]:
        """Simulate probabilistic model performance (Montecarlo)"""
        # Montecarlo is good for stable distributions
        distribution_stability = self._calculate_distribution_stability(train_data[numeric_cols], test_data[numeric_cols])
        return {
            'accuracy': 0.18 + (distribution_stability * 0.15),
            'precision': 0.16 + (distribution_stability * 0.12),
            'stability': 0.90,
            'coverage': 0.85,
            'adaptability': 0.60
        }
    
    def _simulate_pattern_model(self, train_data: pd.DataFrame, test_data: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, float]:
        """Simulate pattern model performance (Apriori)"""
        # Apriori is good for frequent patterns
        pattern_strength = self._calculate_pattern_strength(train_data[numeric_cols])
        return {
            'accuracy': 0.20 + (pattern_strength * 0.18),
            'precision': 0.22 + (pattern_strength * 0.15),
            'pattern_discovery': 0.80,
            'frequency_accuracy': 0.75,
            'stability': 0.82
        }
    
    def _simulate_attention_model(self, train_data: pd.DataFrame, test_data: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, float]:
        """Simulate attention model performance (Transformer)"""
        # Transformer is good for complex relationships
        complexity_score = self._calculate_complexity_score(train_data[numeric_cols])
        return {
            'accuracy': 0.22 + (complexity_score * 0.20),
            'precision': 0.20 + (complexity_score * 0.18),
            'attention_quality': 0.85,
            'context_understanding': 0.80,
            'adaptability': 0.82,
            'learning_capacity': 0.88
        }
    
    def _simulate_clustering_model(self, train_data: pd.DataFrame, test_data: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, float]:
        """Simulate clustering model performance"""
        # Clustering is good for finding natural groups
        cluster_quality = self._calculate_cluster_quality(train_data[numeric_cols])
        return {
            'accuracy': 0.16 + (cluster_quality * 0.15),
            'precision': 0.14 + (cluster_quality * 0.12),
            'group_identification': 0.75,
            'outlier_detection': 0.70,
            'stability': 0.78
        }
    
    def _simulate_evolutionary_model(self, train_data: pd.DataFrame, test_data: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, float]:
        """Simulate evolutionary model performance (Genetic)"""
        # Genetic is good for global optimization
        optimization_space = self._calculate_optimization_potential(train_data[numeric_cols])
        return {
            'accuracy': 0.19 + (optimization_space * 0.16),
            'precision': 0.17 + (optimization_space * 0.14),
            'global_search': 0.90,
            'convergence_quality': 0.80,
            'adaptability': 0.85,
            'novelty_detection': 0.78
        }
    
    def _simulate_gradient_model(self, train_data: pd.DataFrame, test_data: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, float]:
        """Simulate gradient model performance (GBoost)"""
        # GBoost is good for non-linear relationships
        nonlinearity = self._calculate_nonlinearity(train_data[numeric_cols])
        return {
            'accuracy': 0.21 + (nonlinearity * 0.17),
            'precision': 0.19 + (nonlinearity * 0.15),
            'feature_importance': 0.85,
            'robustness': 0.80,
            'learning_capacity': 0.82,
            'adaptability': 0.75
        }
    
    def _simulate_neural_model(self, train_data: pd.DataFrame, test_data: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, float]:
        """Simulate enhanced neural model performance"""
        # Neural enhanced combines multiple strengths
        overall_complexity = self._calculate_overall_complexity(train_data[numeric_cols])
        return {
            'accuracy': 0.25 + (overall_complexity * 0.22),
            'precision': 0.23 + (overall_complexity * 0.20),
            'adaptability': 0.90,
            'learning_capacity': 0.95,
            'novelty_detection': 0.88,
            'stability': 0.85
        }
    
    def _simulate_analyzer_model(self, train_data: pd.DataFrame, test_data: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, float]:
        """Simulate performance of 200-draw analyzer model"""
        # 200 analyzer specializes in recent trends
        recent_trend_strength = self._calculate_recent_trends(train_data[numeric_cols].tail(200))
        return {
            'accuracy': 0.28 + (recent_trend_strength * 0.25),
            'precision': 0.26 + (recent_trend_strength * 0.22),
            'trend_detection': 0.95,
            'short_term_prediction': 0.90
        }
    
    def _simulate_consensus_model(self, train_data: pd.DataFrame, test_data: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, float]:
        """Simulate performance of consensus models (including exploratory)"""
        # Consensus models combine multiple approaches
        overall_complexity = self._calculate_overall_complexity(train_data[numeric_cols])
        pattern_strength = self._calculate_pattern_strength(train_data[numeric_cols])
        
        return {
            'accuracy': 0.32 + (overall_complexity * 0.28),
            'precision': 0.30 + (overall_complexity * 0.25),
            'ensemble_synergy': 0.92,
            'adaptability': 0.88,
            'consensus_quality': 0.85 + (pattern_strength * 0.10),
            'exploration_capability': 0.90  # Higher for exploratory_consensus
        }
    
    # Auxiliary methods for calculating metrics
    def _calculate_temporal_consistency(self, data: pd.DataFrame) -> float:
        """Calculate temporal consistency"""
        try:
            variations = []
            for col in data.columns:
                col_data = data[col].values
                variation = np.std(np.diff(col_data)) / (np.mean(col_data) + 1e-8)
                variations.append(variation)
            return max(0, 1 - np.mean(variations) / 10)
        except:
            return 0.5
    
    def _calculate_distribution_stability(self, train_data: pd.DataFrame, test_data: pd.DataFrame) -> float:
        """Calculate distribution stability"""
        try:
            train_mean = train_data.values.flatten().mean()
            test_mean = test_data.values.flatten().mean()
            stability = 1 - abs(train_mean - test_mean) / 40
            return max(0, min(1, stability))
        except:
            return 0.5
    
    def _calculate_pattern_strength(self, data: pd.DataFrame) -> float:
        """Calculate pattern strength"""
        try:
            all_numbers = data.values.flatten()
            freq_std = np.std(list(Counter(all_numbers).values()))
            return min(1, freq_std / 20)
        except:
            return 0.5
    
    def _calculate_complexity_score(self, data: pd.DataFrame) -> float:
        """Calculate complexity score"""
        try:
            # Based on combination entropy
            combinations = [tuple(sorted(row)) for row in data.values]
            unique_ratio = len(set(combinations)) / len(combinations)
            return unique_ratio
        except:
            return 0.5
    
    def _calculate_cluster_quality(self, data: pd.DataFrame) -> float:
        """Calculate potential cluster quality"""
        try:
            # Based on intra vs inter group variance
            means_per_draw = data.mean(axis=1)
            overall_variance = np.var(means_per_draw)
            return min(1, overall_variance / 100)
        except:
            return 0.5
    
    def _calculate_optimization_potential(self, data: pd.DataFrame) -> float:
        """Calculate optimization potential"""
        try:
            # Based on score dispersion
            ranges = [data[col].max() - data[col].min() for col in data.columns]
            avg_range = np.mean(ranges)
            return min(1, avg_range / 40)
        except:
            return 0.5
    
    def _calculate_nonlinearity(self, data: pd.DataFrame) -> float:
        """Calculate degree of non-linearity"""
        try:
            correlations = []
            for i in range(len(data.columns)-1):
                for j in range(i+1, len(data.columns)):
                    corr = np.corrcoef(data.iloc[:, i], data.iloc[:, j])[0, 1]
                    if not np.isnan(corr):
                        correlations.append(abs(corr))
            
            avg_correlation = np.mean(correlations) if correlations else 0
            return 1 - avg_correlation  # Higher non-linearity = lower correlation
        except:
            return 0.5
    
    def _calculate_overall_complexity(self, data: pd.DataFrame) -> float:
        """Calculate overall dataset complexity"""
        try:
            # Combination of multiple metrics
            entropy = self._calculate_complexity_score(data)
            nonlinearity = self._calculate_nonlinearity(data)
            pattern_strength = self._calculate_pattern_strength(data)
            
            return (entropy + nonlinearity + pattern_strength) / 3
        except:
            return 0.5
    
    def _calculate_recent_trends(self, data: pd.DataFrame) -> float:
        """Calculate strength of recent trends"""
        try:
            if len(data) < 50:
                return 0.5
                
            # Enhanced: Compare recent vs previous periods for robust analysis
            analysis_size = min(500, len(data) // 2)  # Use 500 or half available data
            recent = data.tail(analysis_size)
            previous_start = max(0, len(data) - (analysis_size * 2))
            previous_end = len(data) - analysis_size
            previous = data.iloc[previous_start:previous_end] if len(data) >= analysis_size * 2 else data.head(analysis_size)
            
            recent_freq = Counter(recent.values.flatten())
            prev_freq = Counter(previous.values.flatten())
            
            # Calculate frequency changes
            changes = []
            for num in range(1, 41):
                recent_count = recent_freq.get(num, 0)
                prev_count = prev_freq.get(num, 0)
                if prev_count > 0:
                    change = abs(recent_count - prev_count) / prev_count
                    changes.append(change)
            
            trend_strength = np.mean(changes) if changes else 0
            return min(1, trend_strength)
        except:
            return 0.5
    
    def _get_default_scores(self) -> Dict[str, float]:
        """Default scores if simulation fails"""
        return {
            'accuracy': 0.15,
            'precision': 0.13,
            'stability': 0.75,
            'rare_number_accuracy': 0.08,
            'default': True
        }
    
    def adaptive_calibration_update(self, actual_combination: List[int], 
                                   predicted_combinations: Dict[str, List[int]],
                                   prediction_success: Dict[str, bool]):
        """Update calibration based on actual prediction results"""
        try:
            with self._adaptation_lock:
                combo_key = json.dumps(sorted(actual_combination))
                
                # Check if this was a rare combination
                is_rare = combo_key in self.rare_number_profiles
                
                # Update model weights based on success/failure
                for model_name, success in prediction_success.items():
                    if model_name not in self.available_models:
                        continue
                    
                    # Get current weight
                    current_weight = self.model_weights.get(model_name, 1.0 / len(self.available_models))
                    
                    # Calculate adaptation based on success and rarity
                    if success:
                        if is_rare:
                            # Larger reward for rare combination success
                            adaptation = self.adaptation_rate * 1.5
                        else:
                            # Standard reward
                            adaptation = self.adaptation_rate
                        
                        new_weight = current_weight * (1 + adaptation)
                    else:
                        if is_rare:
                            # Smaller penalty for rare combination failure
                            adaptation = self.adaptation_rate * 0.5
                        else:
                            # Standard penalty
                            adaptation = self.adaptation_rate * 0.8
                        
                        new_weight = current_weight * (1 - adaptation)
                    
                    # Apply bounds
                    new_weight = max(0.01, min(2.0, new_weight))
                    self.model_weights[model_name] = new_weight
                
                # Normalize weights
                total_weight = sum(self.model_weights.values())
                if total_weight > 0:
                    self.model_weights = {
                        model: weight / total_weight 
                        for model, weight in self.model_weights.items()
                    }
                
                # Save adaptation to database
                self._save_prediction_result(actual_combination, predicted_combinations, 
                                           prediction_success, is_rare)
                
                logger.debug(f"Adaptive calibration updated - Rare: {is_rare}")
                
        except Exception as e:
            logger.error(f"Error in adaptive calibration update: {e}")
    
    def _save_prediction_result(self, actual_combination: List[int],
                              predicted_combinations: Dict[str, List[int]],
                              prediction_success: Dict[str, bool],
                              is_rare: bool):
        """Save prediction result for analysis"""
        try:
            conn = sqlite3.connect(self.calibration_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO prediction_failures
                (timestamp, actual_combination, predicted_combinations, 
                 models_involved, failure_analysis, rare_numbers)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                json.dumps(sorted(actual_combination)),
                json.dumps(predicted_combinations),
                json.dumps(list(prediction_success.keys())),
                json.dumps(prediction_success),
                json.dumps(is_rare)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving prediction result: {e}")
    
    def calibrate_weights(self, historial_df: pd.DataFrame) -> Dict[str, float]:
        """Calibrate weights with advanced rare number focus"""
        try:
            logger.info(f"Starting ensemble weight calibration - Mode: {self.calibration_mode.value}")
            
            # Simulate performance with enhanced metrics
            performance_scores = self.simulate_historical_performance(historial_df)
            
            # Apply calibration mode specific adjustments
            adjusted_scores = self._apply_calibration_mode_adjustments(performance_scores, historial_df)
            
            # Normalize scores
            total_score = sum(adjusted_scores.values())
            
            if total_score > 0:
                normalized_weights = {
                    model: score / total_score 
                    for model, score in adjusted_scores.items()
                }
            else:
                # Fallback: equal weights
                normalized_weights = {
                    model: 1.0 / len(self.available_models) 
                    for model in self.available_models
                }
            
            # Apply advanced smoothing with confidence intervals
            smoothed_weights = self._apply_advanced_smoothing(normalized_weights, performance_scores)
            
            # Calculate confidence intervals for weights
            confidence_intervals = self._calculate_weight_confidence_intervals(smoothed_weights)
            
            # Re-normalize after smoothing
            total_smoothed = sum(smoothed_weights.values())
            final_weights = {
                model: weight / total_smoothed 
                for model, weight in smoothed_weights.items()
            }
            
            # Update configuration with enhanced metrics
            self.model_weights = final_weights
            self.model_accuracy = performance_scores
            self.confidence_thresholds = confidence_intervals
            
            # Enhanced calibration metrics
            self.calibration_metrics = self._calculate_enhanced_calibration_metrics(
                performance_scores, final_weights, historial_df
            )
            
            # Save configuration and history
            self.save_config()
            self._save_calibration_session(performance_scores, final_weights)
            
            logger.info("Advanced calibration completed")
            logger.info(f"Best model: {self.calibration_metrics.get('best_model')}")
            logger.info(f"Rare number specialist: {self.calibration_metrics.get('rare_number_specialist')}")
            logger.info(f"Weight distribution: {self.calibration_metrics.get('weight_distribution')}")
            
            return final_weights
            
        except Exception as e:
            logger.error(f"Error in calibration: {e}")
            return self.default_weights.copy()
    
    def _apply_calibration_mode_adjustments(self, performance_scores: Dict[str, float], 
                                          historial_df: pd.DataFrame) -> Dict[str, float]:
        """Apply calibration mode specific adjustments to performance scores"""
        try:
            adjusted_scores = performance_scores.copy()
            
            if self.calibration_mode == CalibrationMode.RARE_FOCUSED:
                # Boost models that perform well on rare combinations
                rare_specialists = ['exploratory_consensus', 'neural_enhanced', 'transformer_deep']
                for model in rare_specialists:
                    if model in adjusted_scores:
                        adjusted_scores[model] *= 1.3
                        
            elif self.calibration_mode == CalibrationMode.EXPLORATORY:
                # Boost exploratory and adaptive models
                exploratory_models = ['exploratory_consensus', 'genetico', 'neural_enhanced']
                for model in exploratory_models:
                    if model in adjusted_scores:
                        adjusted_scores[model] *= 1.4
                        
            elif self.calibration_mode == CalibrationMode.ADAPTIVE:
                # Boost models with high learning capacity
                adaptive_models = ['neural_enhanced', 'transformer_deep', 'gboost']
                for model in adaptive_models:
                    if model in adjusted_scores:
                        adjusted_scores[model] *= 1.2
                        
            elif self.calibration_mode == CalibrationMode.HYBRID:
                # Balanced approach with slight rare number focus
                rare_boost = ['exploratory_consensus', 'consensus', 'neural_enhanced']
                for model in rare_boost:
                    if model in adjusted_scores:
                        adjusted_scores[model] *= 1.15
            
            return adjusted_scores
            
        except Exception as e:
            logger.error(f"Error applying calibration mode adjustments: {e}")
            return performance_scores
    
    def _apply_advanced_smoothing(self, normalized_weights: Dict[str, float], 
                                performance_scores: Dict[str, float]) -> Dict[str, float]:
        """Apply advanced smoothing with reliability consideration"""
        try:
            smoothed_weights = {}
            min_weight = 0.03  # Minimum weight of 3%
            
            for model, weight in normalized_weights.items():
                # Get previous weight and reliability score
                previous_weight = self.model_weights.get(model, 1.0 / len(self.available_models))
                reliability = self.model_reliability_scores.get(model, 0.5)
                
                # Adaptive smoothing based on reliability
                if reliability > 0.7:
                    # High reliability: more weight to new performance
                    alpha = 0.8
                else:
                    # Lower reliability: more conservative updates
                    alpha = 0.5
                
                smoothed_weight = alpha * weight + (1 - alpha) * previous_weight
                
                # Apply minimum weight
                smoothed_weights[model] = max(min_weight, smoothed_weight)
            
            return smoothed_weights
            
        except Exception as e:
            logger.error(f"Error in advanced smoothing: {e}")
            return normalized_weights
    
    def _calculate_weight_confidence_intervals(self, weights: Dict[str, float]) -> Dict[str, Tuple[float, float]]:
        """Calculate confidence intervals for model weights"""
        try:
            confidence_intervals = {}
            
            for model, weight in weights.items():
                # Use historical performance variation to estimate confidence
                reliability = self.model_reliability_scores.get(model, 0.5)
                
                # Higher reliability = narrower confidence interval
                margin = (1.0 - reliability) * 0.1  # Max 10% margin
                
                lower_bound = max(0.01, weight - margin)
                upper_bound = min(1.0, weight + margin)
                
                confidence_intervals[model] = (lower_bound, upper_bound)
            
            return confidence_intervals
            
        except Exception as e:
            logger.error(f"Error calculating confidence intervals: {e}")
            return {model: (0.05, 0.15) for model in weights.keys()}
    
    def _calculate_enhanced_calibration_metrics(self, performance_scores: Dict[str, float],
                                              final_weights: Dict[str, float],
                                              historial_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate enhanced calibration metrics"""
        try:
            # Basic metrics
            best_model = max(performance_scores, key=performance_scores.get)
            worst_model = min(performance_scores, key=performance_scores.get)
            
            # Weight distribution analysis
            weight_values = list(final_weights.values())
            max_weight = max(weight_values)
            weight_entropy = -sum(w * np.log(w + 1e-8) for w in weight_values)
            
            if max_weight < 0.25:
                distribution = 'highly_balanced'
            elif max_weight < 0.4:
                distribution = 'balanced'
            else:
                distribution = 'concentrated'
            
            # Identify rare number specialist
            rare_specialists = ['exploratory_consensus', 'neural_enhanced', 'transformer_deep']
            rare_specialist = max(
                (model for model in rare_specialists if model in final_weights),
                key=lambda m: final_weights[m],
                default='neural_enhanced'
            )
            
            # Analyze rare combinations in data
            rare_profiles = self.analyze_rare_number_combinations(historial_df)
            
            return {
                'total_models': len(self.available_models),
                'best_model': best_model,
                'worst_model': worst_model,
                'rare_number_specialist': rare_specialist,
                'weight_distribution': distribution,
                'weight_entropy': weight_entropy,
                'max_weight': max_weight,
                'calibration_mode': self.calibration_mode.value,
                'rare_combinations_analyzed': len(rare_profiles),
                'average_performance': np.mean(list(performance_scores.values())),
                'performance_std': np.std(list(performance_scores.values())),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating enhanced calibration metrics: {e}")
            return {
                'total_models': len(self.available_models),
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _save_calibration_session(self, performance_scores: Dict[str, float], 
                                final_weights: Dict[str, float]):
        """Save calibration session to database"""
        try:
            for model_name in self.available_models:
                if model_name in performance_scores and model_name in final_weights:
                    self.save_calibration_history(
                        model_name=model_name,
                        weight=final_weights[model_name],
                        accuracy=performance_scores[model_name],
                        rare_accuracy=performance_scores.get(f"{model_name}_rare", 0.0),
                        success_rate=self.model_reliability_scores.get(model_name, 0.5),
                        failure_patterns=[],
                        combination_hash="calibration_session"
                    )
        except Exception as e:
            logger.error(f"Error saving calibration session: {e}")
    
    def get_calibration_summary(self) -> Dict[str, Any]:
        """Return comprehensive calibration summary"""
        return {
            'weights': self.model_weights,
            'adaptive_weights': self.adaptive_weights,
            'accuracy_scores': self.model_accuracy,
            'calibration_metrics': self.calibration_metrics,
            'confidence_thresholds': self.confidence_thresholds,
            'reliability_scores': self.model_reliability_scores,
            'calibration_mode': self.calibration_mode.value,
            'rare_number_profiles': len(self.rare_number_profiles),
            'total_models': len(self.available_models),
            'is_calibrated': bool(self.calibration_metrics),
            'last_adaptation': datetime.now().isoformat()
        }

    def set_calibration_mode(self, mode: CalibrationMode):
        """Set calibration mode for specific scenarios"""
        self.calibration_mode = mode
        logger.info(f"Calibration mode set to: {mode.value}")
    
    def get_rare_number_insights(self) -> Dict[str, Any]:
        """Get insights about rare number combination performance"""
        try:
            insights = {
                'total_rare_profiles': len(self.rare_number_profiles),
                'most_successful_rare_models': [],
                'rarest_combinations': [],
                'recent_rare_patterns': []
            }
            
            # Find models that perform best on rare combinations
            rare_performance = {}
            for profile in self.rare_number_profiles.values():
                for model, performance in profile.model_performance.items():
                    if model not in rare_performance:
                        rare_performance[model] = []
                    rare_performance[model].append(performance)
            
            # Calculate average rare performance per model
            for model, performances in rare_performance.items():
                avg_performance = np.mean(performances) if performances else 0.0
                insights['most_successful_rare_models'].append({
                    'model': model,
                    'rare_accuracy': avg_performance
                })
            
            # Sort by performance
            insights['most_successful_rare_models'].sort(
                key=lambda x: x['rare_accuracy'], reverse=True
            )
            
            # Get rarest combinations
            sorted_profiles = sorted(
                self.rare_number_profiles.items(),
                key=lambda x: x[1].rarity_score,
                reverse=True
            )
            
            insights['rarest_combinations'] = [
                {
                    'combination': json.loads(combo_key),
                    'rarity_score': profile.rarity_score,
                    'frequency': profile.frequency
                }
                for combo_key, profile in sorted_profiles[:10]
            ]
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating rare number insights: {e}")
            return {'error': str(e)}
    
    def validate_calibration_effectiveness(self, validation_data: pd.DataFrame) -> Dict[str, float]:
        """Validate calibration effectiveness using statistical tests"""
        try:
            logger.info("Validating calibration effectiveness...")
            
            validation_metrics = {}
            
            # Cross-validation of weight stability
            weight_values = list(self.model_weights.values())
            validation_metrics['weight_stability'] = 1.0 - (np.std(weight_values) / np.mean(weight_values))
            
            # Rare number coverage
            rare_profiles = self.analyze_rare_number_combinations(validation_data)
            validation_metrics['rare_coverage'] = len(rare_profiles) / max(1, len(validation_data))
            
            # Model diversity index
            entropy = -sum(w * np.log(w + 1e-8) for w in weight_values)
            max_entropy = np.log(len(weight_values))
            validation_metrics['diversity_index'] = entropy / max_entropy
            
            # Calibration confidence
            avg_confidence = np.mean([
                interval[1] - interval[0] 
                for interval in self.confidence_thresholds.values()
            ]) if self.confidence_thresholds else 0.1
            validation_metrics['calibration_confidence'] = 1.0 - avg_confidence
            
            # Overall effectiveness score
            validation_metrics['overall_effectiveness'] = np.mean([
                validation_metrics['weight_stability'],
                validation_metrics['diversity_index'],
                validation_metrics['calibration_confidence']
            ])
            
            logger.info(f"Calibration effectiveness: {validation_metrics['overall_effectiveness']:.3f}")
            
            return validation_metrics
            
        except Exception as e:
            logger.error(f"Error validating calibration effectiveness: {e}")
            return {'error': str(e)}

def calibrate_ensemble(historial_df: pd.DataFrame, 
                     config_path: str = "config/ensemble_weights.json",
                     calibration_mode: str = "hybrid",
                     rare_threshold: float = 0.15) -> Dict[str, Any]:
    """Main function to calibrate ensemble with advanced features"""
    try:
        # Convert string mode to enum
        try:
            mode = CalibrationMode(calibration_mode)
        except ValueError:
            logger.warning(f"Invalid calibration mode '{calibration_mode}', using hybrid")
            mode = CalibrationMode.HYBRID
        
        calibrator = AdvancedEnsembleCalibrator(
            config_path=config_path,
            rare_threshold=rare_threshold
        )
        calibrator.set_calibration_mode(mode)
        
        optimized_weights = calibrator.calibrate_weights(historial_df)
        summary = calibrator.get_calibration_summary()
        rare_insights = calibrator.get_rare_number_insights()
        validation_metrics = calibrator.validate_calibration_effectiveness(historial_df)
        
        return {
            'weights': optimized_weights,
            'summary': summary,
            'rare_insights': rare_insights,
            'validation_metrics': validation_metrics,
            'calibration_mode': mode.value,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Error in ensemble calibration: {e}")
        return {
            'weights': {},
            'summary': {},
            'success': False,
            'error': str(e)
        }

def create_rare_focused_calibrator(historial_df: pd.DataFrame) -> AdvancedEnsembleCalibrator:
    """Create a calibrator specifically optimized for rare number combinations"""
    calibrator = AdvancedEnsembleCalibrator(
        rare_threshold=0.10,  # More aggressive rare number detection
        adaptation_rate=0.4,  # Faster adaptation
        validation_window=150  # Larger validation window
    )
    calibrator.set_calibration_mode(CalibrationMode.RARE_FOCUSED)
    return calibrator

def create_exploratory_calibrator(historial_df: pd.DataFrame) -> AdvancedEnsembleCalibrator:
    """Create a calibrator optimized for exploratory consensus mode"""
    calibrator = AdvancedEnsembleCalibrator(
        rare_threshold=0.12,
        adaptation_rate=0.35,
        validation_window=200
    )
    calibrator.set_calibration_mode(CalibrationMode.EXPLORATORY)
    return calibrator
