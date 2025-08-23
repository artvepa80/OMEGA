# OMEGA_PRO_AI_v10.1/modules/advanced_feature_engineering.py
"""
Advanced Feature Engineering for OMEGA PRO AI
Implements sophisticated feature extraction based on data scientist findings
Targeting 65-70% accuracy improvement from current 50%
"""

import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Tuple, Optional, Any
from collections import Counter, defaultdict
from scipy.stats import entropy
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import datetime

logger = logging.getLogger(__name__)

class AdvancedFeatureEngineer:
    """
    Advanced feature engineering based on data scientist analysis findings:
    - Position-specific preferences (1-20 prefer positions 1-3, 21-40 prefer 4-6)
    - Consecutive pair patterns (74.5% contain consecutive pairs)
    - Hot number momentum tracking (number 39 showing 2.0x frequency)
    - Mathematical relationships and seasonal cycles
    """
    
    def __init__(self, decay_factor: float = 0.95):
        self.decay_factor = decay_factor  # For recency weighting
        self.scaler = StandardScaler()
        self.position_preferences = self._initialize_position_preferences()
        
    def _initialize_position_preferences(self) -> Dict[str, List[int]]:
        """Initialize position preferences based on data scientist findings"""
        return {
            'early_positions': list(range(1, 21)),    # Numbers 1-20 prefer positions 1-3
            'late_positions': list(range(21, 41)),    # Numbers 21-40 prefer positions 4-6
            'hot_momentum': [39, 28, 29, 34, 35],     # Hot numbers from analysis
            'consecutive_pairs': [(28, 29), (39, 40), (34, 35), (27, 28), (3, 4)]
        }
    
    def extract_comprehensive_features(self, historial_df: pd.DataFrame) -> np.ndarray:
        """
        Extract comprehensive feature set for ML models
        
        Returns feature matrix with:
        - Recency-weighted frequencies (40 features)
        - Position-specific preferences (12 features) 
        - Consecutive pair indicators (10 features)
        - Mathematical relationships (8 features)
        - Seasonal/temporal features (6 features)
        - Hot number momentum (5 features)
        Total: 81 features per draw
        """
        logger.info("🔧 Extracting comprehensive feature set...")
        
        # Get numeric columns
        numeric_cols = [col for col in historial_df.columns 
                       if 'bolilla' in col.lower() or col.startswith('Bolilla')]
        
        if len(numeric_cols) < 6:
            raise ValueError(f"Need at least 6 ball columns, found {len(numeric_cols)}")
        
        features_list = []
        
        for idx, row in historial_df.iterrows():
            draw_numbers = [int(row[col]) for col in numeric_cols[:6]]
            
            # Calculate all feature components
            recency_features = self._calculate_recency_weighted_frequency(
                historial_df.iloc[:idx+1], draw_numbers
            )
            
            position_features = self._calculate_position_preferences(draw_numbers)
            consecutive_features = self._calculate_consecutive_patterns(draw_numbers)
            math_features = self._calculate_mathematical_features(draw_numbers)
            temporal_features = self._calculate_temporal_features(row, historial_df)
            momentum_features = self._calculate_hot_momentum(
                historial_df.iloc[max(0, idx-20):idx+1], draw_numbers
            )
            
            # Combine all features
            combined_features = np.concatenate([
                recency_features,
                position_features, 
                consecutive_features,
                math_features,
                temporal_features,
                momentum_features
            ])
            
            features_list.append(combined_features)
        
        feature_matrix = np.array(features_list)
        logger.info(f"✅ Feature extraction complete: {feature_matrix.shape}")
        
        return feature_matrix
    
    def _calculate_recency_weighted_frequency(self, historical_subset: pd.DataFrame, 
                                            current_numbers: List[int]) -> np.ndarray:
        """Calculate recency-weighted frequency scores with exponential decay"""
        frequencies = np.zeros(40)
        
        # Get all historical numbers up to current draw
        numeric_cols = [col for col in historical_subset.columns 
                       if 'bolilla' in col.lower() or col.startswith('Bolilla')]
        
        for idx, row in historical_subset.iterrows():
            # Apply exponential decay based on recency
            weight = self.decay_factor ** (len(historical_subset) - idx - 1)
            
            for col in numeric_cols[:6]:
                if pd.notna(row[col]):
                    number = int(row[col]) - 1  # Convert to 0-based index
                    if 0 <= number < 40:
                        frequencies[number] += weight
        
        # Normalize frequencies
        if np.sum(frequencies) > 0:
            frequencies = frequencies / np.sum(frequencies)
            
        return frequencies
    
    def _calculate_position_preferences(self, numbers: List[int]) -> np.ndarray:
        """Calculate position preference features based on data scientist findings"""
        features = np.zeros(12)
        
        # Position preference violations (numbers in wrong preferred positions)
        early_in_late = sum(1 for i in range(3, 6) if numbers[i] in self.position_preferences['early_positions'])
        late_in_early = sum(1 for i in range(3) if numbers[i] in self.position_preferences['late_positions'])
        
        features[0] = early_in_late / 3  # Early numbers in late positions (normalized)
        features[1] = late_in_early / 3  # Late numbers in early positions (normalized)
        
        # Position-specific number distributions
        for pos in range(6):
            features[2 + pos] = 1 if numbers[pos] in self.position_preferences['early_positions'] else 0
        
        # Hot number positioning
        for i, num in enumerate(self.position_preferences['hot_momentum'][:4]):
            features[8 + i] = 1 if num in numbers else 0
            
        return features
    
    def _calculate_consecutive_patterns(self, numbers: List[int]) -> np.ndarray:
        """Calculate consecutive pair pattern features"""
        features = np.zeros(10)
        sorted_numbers = sorted(numbers)
        
        # Count consecutive pairs
        consecutive_pairs = 0
        for i in range(len(sorted_numbers) - 1):
            if sorted_numbers[i+1] - sorted_numbers[i] == 1:
                consecutive_pairs += 1
        
        features[0] = consecutive_pairs / 5  # Normalize by max possible pairs
        
        # Specific high-value consecutive pair indicators
        known_pairs = [(28, 29), (39, 40), (34, 35), (27, 28), (3, 4)]
        for i, pair in enumerate(known_pairs):
            features[1 + i] = 1 if (pair[0] in numbers and pair[1] in numbers) else 0
        
        # Gap analysis
        gaps = [sorted_numbers[i+1] - sorted_numbers[i] for i in range(5)]
        features[6] = np.mean(gaps) / 40  # Average gap normalized
        features[7] = np.std(gaps) / 20   # Gap variability normalized
        features[8] = min(gaps) / 40      # Minimum gap normalized
        features[9] = max(gaps) / 40      # Maximum gap normalized
        
        return features
    
    def _calculate_mathematical_features(self, numbers: List[int]) -> np.ndarray:
        """Calculate mathematical relationship features"""
        features = np.zeros(8)
        
        # Sum and sum-related features (target: 122.4±24.4)
        total_sum = sum(numbers)
        features[0] = (total_sum - 122.4) / 24.4  # Deviation from expected mean
        
        # Even/odd distribution
        even_count = sum(1 for n in numbers if n % 2 == 0)
        features[1] = even_count / 6  # Proportion of even numbers
        
        # Decade distribution (1-10, 11-20, 21-30, 31-40)
        decade_counts = [0, 0, 0, 0]
        for num in numbers:
            decade = min((num - 1) // 10, 3)
            decade_counts[decade] += 1
        
        features[2:6] = np.array(decade_counts) / 6  # Normalize decade distributions
        
        # Range and spread
        features[6] = (max(numbers) - min(numbers)) / 39  # Range normalized
        features[7] = np.std(numbers) / 20  # Standard deviation normalized
        
        return features
    
    def _calculate_temporal_features(self, current_row: pd.Series, 
                                   historial_df: pd.DataFrame) -> np.ndarray:
        """Calculate seasonal and temporal cycle features"""
        features = np.zeros(6)
        
        # Extract date if available
        date_col = None
        for col in current_row.index:
            if 'fecha' in col.lower() or 'date' in col.lower():
                date_col = col
                break
        
        if date_col and pd.notna(current_row[date_col]):
            try:
                if isinstance(current_row[date_col], str):
                    date = pd.to_datetime(current_row[date_col])
                else:
                    date = current_row[date_col]
                
                # Seasonal features
                quarter = (date.month - 1) // 3
                features[quarter] = 1  # One-hot encode quarter
                
                # Week of year (cyclical encoding)
                week = date.isocalendar()[1]
                features[4] = np.sin(2 * np.pi * week / 52)
                features[5] = np.cos(2 * np.pi * week / 52)
                
            except Exception as e:
                logger.warning(f"Could not parse date {current_row[date_col]}: {e}")
        
        return features
    
    def _calculate_hot_momentum(self, recent_subset: pd.DataFrame, 
                              current_numbers: List[int]) -> np.ndarray:
        """Calculate hot number momentum features"""
        features = np.zeros(5)
        
        if len(recent_subset) == 0:
            return features
        
        # Get numeric columns
        numeric_cols = [col for col in recent_subset.columns 
                       if 'bolilla' in col.lower() or col.startswith('Bolilla')]
        
        # Count recent frequencies
        recent_freq = Counter()
        for _, row in recent_subset.iterrows():
            for col in numeric_cols[:6]:
                if pd.notna(row[col]):
                    recent_freq[int(row[col])] += 1
        
        # Hot number momentum (number 39 analysis: 2.0x expected frequency)
        expected_freq = len(recent_subset) * 6 / 40  # Expected frequency for any number
        
        hot_numbers = [39, 28, 29, 34, 35]  # From data scientist analysis
        for i, hot_num in enumerate(hot_numbers[:4]):
            actual_freq = recent_freq.get(hot_num, 0)
            momentum = actual_freq / max(expected_freq, 1)  # Avoid division by zero
            features[i] = min(momentum / 2.0, 1.0)  # Normalize by 2x factor, cap at 1
        
        # Overall momentum indicator
        total_hot_freq = sum(recent_freq.get(num, 0) for num in hot_numbers)
        total_expected = expected_freq * len(hot_numbers)
        features[4] = min(total_hot_freq / max(total_expected, 1) / 2.0, 1.0)
        
        return features
    
    def create_feature_correlation_matrix(self, numbers_list: List[List[int]]) -> np.ndarray:
        """Create cross-number correlation matrix features"""
        correlation_features = []
        
        # Create a matrix of number occurrences by position
        position_matrix = np.zeros((len(numbers_list), 40, 6))
        
        for draw_idx, numbers in enumerate(numbers_list):
            for pos_idx, number in enumerate(numbers):
                if 1 <= number <= 40:
                    position_matrix[draw_idx, number-1, pos_idx] = 1
        
        # Calculate correlation features
        for pos1 in range(6):
            for pos2 in range(pos1+1, 6):
                pos1_data = position_matrix[:, :, pos1]
                pos2_data = position_matrix[:, :, pos2]
                
                # Calculate correlation between positions
                correlations = []
                for num1 in range(40):
                    for num2 in range(num1+1, 40):
                        if np.var(pos1_data[:, num1]) > 0 and np.var(pos2_data[:, num2]) > 0:
                            corr = np.corrcoef(pos1_data[:, num1], pos2_data[:, num2])[0, 1]
                            if not np.isnan(corr):
                                correlations.append(abs(corr))
                
                correlation_features.append(np.mean(correlations) if correlations else 0)
        
        return np.array(correlation_features)
    
    def extract_sequence_features(self, historial_df: pd.DataFrame, 
                                sequence_length: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract sequential features for LSTM and Transformer models
        
        Returns:
            X: Sequential features (n_sequences, sequence_length, n_features)
            y: Target values (n_sequences, 6)
        """
        logger.info(f"🔧 Extracting sequence features with length {sequence_length}...")
        
        # Get comprehensive features for each draw
        feature_matrix = self.extract_comprehensive_features(historial_df)
        
        # Get numeric columns for targets
        numeric_cols = [col for col in historial_df.columns 
                       if 'bolilla' in col.lower() or col.startswith('Bolilla')]
        
        # Create sequences
        X_sequences = []
        y_targets = []
        
        for i in range(sequence_length, len(feature_matrix)):
            # Input sequence: previous sequence_length draws
            X_seq = feature_matrix[i-sequence_length:i]
            X_sequences.append(X_seq)
            
            # Target: current draw numbers
            y_target = [int(historial_df.iloc[i][col]) for col in numeric_cols[:6]]
            y_targets.append(y_target)
        
        X = np.array(X_sequences)
        y = np.array(y_targets)
        
        logger.info(f"✅ Sequence extraction complete: X shape {X.shape}, y shape {y.shape}")
        
        return X, y
    
    def get_feature_importance_weights(self) -> Dict[str, float]:
        """
        Return feature importance weights based on data scientist analysis
        These weights prioritize features that contributed to 50% accuracy success
        """
        return {
            'recency_weighted_freq': 0.25,    # High importance - recency matters
            'position_preferences': 0.20,     # High importance - strong pattern
            'consecutive_patterns': 0.18,     # High importance - 74.5% contain pairs
            'hot_momentum': 0.15,             # Medium importance - number 39 effect
            'mathematical_features': 0.12,    # Medium importance - sum patterns
            'temporal_features': 0.10         # Lower importance - seasonal effects
        }

def create_enhanced_features(historial_df: pd.DataFrame, 
                           sequence_length: int = 10) -> Tuple[np.ndarray, np.ndarray]:
    """
    Main function to create enhanced features for OMEGA models
    
    Args:
        historial_df: Historical lottery data
        sequence_length: Length of sequences for temporal models
        
    Returns:
        X: Feature sequences
        y: Target values
    """
    engineer = AdvancedFeatureEngineer()
    return engineer.extract_sequence_features(historial_df, sequence_length)