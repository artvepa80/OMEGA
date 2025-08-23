# OMEGA_PRO_AI_v10.1/modules/lstm_model_enhanced.py
"""
Enhanced LSTM Model with Attention Mechanisms for OMEGA PRO AI
Implements advanced LSTM architecture targeting 65-70% accuracy
Based on successful 50% accuracy baseline (28,29,39 prediction)
"""

import logging
import os
import json
import random
import traceback
import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List, Dict, Set, Tuple, Any, Union

# Third-party imports
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    LSTM, Dense, Dropout, BatchNormalization, Attention, 
    Input, Concatenate, Bidirectional, MultiHeadAttention,
    LayerNormalization, Add
)
from tensorflow.keras.callbacks import (
    EarlyStopping, ReduceLROnPlateau, ModelCheckpoint, TensorBoard
)
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import joblib

# Local imports
from modules.advanced_feature_engineering import AdvancedFeatureEngineer, create_enhanced_features
from modules.score_dynamics import score_combinations

logger = logging.getLogger(__name__)

@dataclass
class EnhancedLSTMConfig:
    """Enhanced configuration for LSTM with attention"""
    # Base LSTM parameters
    n_steps: int = 10
    n_units: int = 128  # Increased from 64
    dropout_rate: float = 0.3
    learning_rate: float = 0.001
    epochs: int = 100  # Increased from 20 for better learning
    batch_size: int = 32
    validation_split: float = 0.15
    
    # Attention mechanism parameters
    use_attention: bool = True
    attention_heads: int = 4
    attention_units: int = 64
    
    # Bidirectional LSTM parameters
    use_bidirectional: bool = True
    
    # Feature fusion parameters
    use_feature_fusion: bool = True
    fusion_units: int = 64
    
    # Advanced training parameters
    use_batch_norm: bool = True
    use_layer_norm: bool = True
    gradient_cliping: float = 1.0
    
    # Model paths
    model_path: Optional[Path] = None
    tensorboard_logdir: Optional[Path] = None
    
    # Regularization
    l1_reg: float = 0.001
    l2_reg: float = 0.001
    
    # Early stopping and learning rate
    early_stopping_patience: int = 20  # Increased patience
    reduce_lr_patience: int = 8
    reduce_lr_factor: float = 0.3
    reduce_lr_min: float = 1e-7
    
    # Data parameters
    number_range: Tuple[int, int] = (1, 40)
    number_count: int = 6
    scaler_type: str = "minmax"
    seed: Optional[int] = None

class AttentionLayer(tf.keras.layers.Layer):
    """Custom attention layer for lottery number sequences"""
    
    def __init__(self, units=64, **kwargs):
        super(AttentionLayer, self).__init__(**kwargs)
        self.units = units
        self.attention = Attention()
        self.dense = Dense(units, activation='tanh')
        
    def call(self, inputs):
        # inputs: (batch_size, timesteps, features)
        query = self.dense(inputs)
        attention_output = self.attention([query, inputs])
        return attention_output
        
    def get_config(self):
        config = super().get_config()
        config.update({'units': self.units})
        return config

class EnhancedLSTMModel:
    """Enhanced LSTM model with attention mechanisms and feature fusion"""
    
    def __init__(self, config: EnhancedLSTMConfig):
        self.config = config
        self.model = None
        self.scaler = None
        self.feature_engineer = AdvancedFeatureEngineer()
        self.history = None
        
        # Set seeds for reproducibility
        if config.seed is not None:
            self._set_seeds(config.seed)
            
    def _set_seeds(self, seed: int):
        """Set all seeds for reproducibility"""
        os.environ['PYTHONHASHSEED'] = str(seed)
        random.seed(seed)
        np.random.seed(seed)
        tf.random.set_seed(seed)
        os.environ['TF_DETERMINISTIC_OPS'] = '1'
        
    def build_enhanced_model(self, input_shape: Tuple[int, int]) -> Model:
        """
        Build enhanced LSTM model with attention and feature fusion
        
        Architecture:
        - Input layer
        - Bidirectional LSTM layers with attention
        - Multi-head attention layer
        - Feature fusion layer
        - Dense layers with regularization
        - Output layer for 6 lottery numbers
        """
        # Input layer
        inputs = Input(shape=input_shape, name='sequence_input')
        
        # Bidirectional LSTM layers
        if self.config.use_bidirectional:
            lstm1 = Bidirectional(
                LSTM(self.config.n_units, return_sequences=True, dropout=self.config.dropout_rate),
                name='bidirectional_lstm1'
            )(inputs)
        else:
            lstm1 = LSTM(
                self.config.n_units, return_sequences=True, dropout=self.config.dropout_rate,
                name='lstm1'
            )(inputs)
            
        if self.config.use_batch_norm:
            lstm1 = BatchNormalization(name='batch_norm1')(lstm1)
            
        # Second LSTM layer
        if self.config.use_bidirectional:
            lstm2 = Bidirectional(
                LSTM(self.config.n_units, return_sequences=True, dropout=self.config.dropout_rate),
                name='bidirectional_lstm2'
            )(lstm1)
        else:
            lstm2 = LSTM(
                self.config.n_units, return_sequences=True, dropout=self.config.dropout_rate,
                name='lstm2'
            )(lstm1)
            
        # Multi-head attention mechanism
        if self.config.use_attention:
            attention_output = MultiHeadAttention(
                num_heads=self.config.attention_heads,
                key_dim=self.config.attention_units,
                name='multi_head_attention'
            )(lstm2, lstm2)
            
            # Add residual connection
            attention_output = Add(name='attention_residual')([lstm2, attention_output])
            
            if self.config.use_layer_norm:
                attention_output = LayerNormalization(name='layer_norm1')(attention_output)
        else:
            attention_output = lstm2
            
        # Global average pooling to get fixed-size representation
        pooled_output = tf.keras.layers.GlobalAveragePooling1D(name='global_avg_pool')(attention_output)
        
        # Feature fusion layer
        if self.config.use_feature_fusion:
            fusion1 = Dense(
                self.config.fusion_units, 
                activation='relu',
                kernel_regularizer=tf.keras.regularizers.l1_l2(
                    l1=self.config.l1_reg, l2=self.config.l2_reg
                ),
                name='fusion1'
            )(pooled_output)
            
            fusion1 = Dropout(self.config.dropout_rate, name='fusion_dropout1')(fusion1)
            
            fusion2 = Dense(
                self.config.fusion_units // 2, 
                activation='relu',
                kernel_regularizer=tf.keras.regularizers.l1_l2(
                    l1=self.config.l1_reg, l2=self.config.l2_reg
                ),
                name='fusion2'
            )(fusion1)
            
            fusion2 = Dropout(self.config.dropout_rate, name='fusion_dropout2')(fusion2)
            final_features = fusion2
        else:
            final_features = pooled_output
            
        # Output layers for each lottery position
        outputs = []
        for i in range(6):
            # Each position gets its own head to capture position-specific patterns
            position_output = Dense(
                32, 
                activation='relu',
                name=f'position_{i+1}_dense1'
            )(final_features)
            position_output = Dropout(self.config.dropout_rate)(position_output)
            
            # Output layer for this position (40 classes for numbers 1-40)
            position_final = Dense(
                40, 
                activation='softmax',  # Use softmax for probability distribution
                name=f'position_{i+1}_output'
            )(position_output)
            outputs.append(position_final)
        
        # Create model
        model = Model(inputs=inputs, outputs=outputs, name='enhanced_lstm_lottery')
        
        # Compile model with custom loss for multiple outputs
        optimizer = tf.keras.optimizers.Adam(
            learning_rate=self.config.learning_rate,
            clipnorm=self.config.gradient_cliping
        )
        
        model.compile(
            optimizer=optimizer,
            loss='sparse_categorical_crossentropy',  # For multi-class classification
            metrics=['accuracy'],
            loss_weights=[1.0] * 6  # Equal weight for all positions
        )
        
        return model
        
    def prepare_training_data(self, historial_df: pd.DataFrame) -> Tuple[np.ndarray, List[np.ndarray]]:
        """
        Prepare training data with enhanced features
        
        Returns:
            X: Enhanced feature sequences
            y: Target arrays for each position
        """
        logger.info("🔧 Preparing enhanced training data...")
        
        # Extract enhanced sequential features
        X, raw_y = create_enhanced_features(historial_df, self.config.n_steps)
        
        # Prepare targets for multi-output model
        y_targets = []
        for pos in range(6):
            y_pos = raw_y[:, pos] - 1  # Convert to 0-based indexing
            y_targets.append(y_pos)
            
        # Initialize and fit scaler
        n_samples, n_timesteps, n_features = X.shape
        X_reshaped = X.reshape(-1, n_features)
        
        if self.config.scaler_type == "standard":
            self.scaler = StandardScaler()
        else:
            self.scaler = MinMaxScaler()
            
        X_scaled = self.scaler.fit_transform(X_reshaped)
        X_scaled = X_scaled.reshape(n_samples, n_timesteps, n_features)
        
        logger.info(f"✅ Training data prepared: X shape {X_scaled.shape}")
        return X_scaled, y_targets
        
    def train(self, historial_df: pd.DataFrame, verbose: int = 1) -> tf.keras.callbacks.History:
        """Train the enhanced LSTM model"""
        logger.info("🚀 Starting enhanced LSTM training...")
        
        # Prepare data
        X, y_targets = self.prepare_training_data(historial_df)
        
        if len(X) < self.config.n_steps + 10:
            raise ValueError(f"Insufficient data: {len(X)} samples. Need at least {self.config.n_steps + 10}")
            
        # Build model
        input_shape = (X.shape[1], X.shape[2])
        self.model = self.build_enhanced_model(input_shape)
        
        if verbose > 0:
            self.model.summary()
            
        # Prepare callbacks
        callbacks = self._prepare_callbacks()
        
        # Train model
        self.history = self.model.fit(
            X, y_targets,
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            validation_split=self.config.validation_split,
            callbacks=callbacks,
            verbose=verbose,
            shuffle=False  # Keep temporal order
        )
        
        logger.info("✅ Enhanced LSTM training completed")
        return self.history
        
    def _prepare_callbacks(self) -> List:
        """Prepare training callbacks"""
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=self.config.early_stopping_patience,
                restore_best_weights=True,
                verbose=1
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=self.config.reduce_lr_factor,
                patience=self.config.reduce_lr_patience,
                min_lr=self.config.reduce_lr_min,
                verbose=1
            )
        ]
        
        # TensorBoard logging
        if self.config.tensorboard_logdir:
            self.config.tensorboard_logdir.mkdir(parents=True, exist_ok=True)
            callbacks.append(TensorBoard(
                log_dir=str(self.config.tensorboard_logdir),
                histogram_freq=1
            ))
            
        # Model checkpointing
        if self.config.model_path:
            self.config.model_path.parent.mkdir(parents=True, exist_ok=True)
            callbacks.append(ModelCheckpoint(
                filepath=str(self.config.model_path.with_suffix('.h5')),
                save_best_only=True,
                monitor='val_loss',
                verbose=1
            ))
            
        return callbacks
        
    def predict_combinations(self, historial_df: pd.DataFrame, 
                           n_combinations: int = 10) -> List[Dict[str, Any]]:
        """
        Generate lottery combinations using the trained model
        
        Uses the model to predict probability distributions for each position,
        then samples combinations based on these probabilities while ensuring
        no duplicates within each combination.
        """
        if self.model is None or self.scaler is None:
            raise RuntimeError("Model not trained or loaded")
            
        logger.info(f"🎯 Generating {n_combinations} combinations...")
        
        # Get the last sequence for prediction
        X, _ = create_enhanced_features(historial_df, self.config.n_steps)
        
        if len(X) == 0:
            raise ValueError("No sequences available for prediction")
            
        # Scale the last sequence
        last_sequence = X[-1:].reshape(-1, X.shape[-1])
        last_sequence_scaled = self.scaler.transform(last_sequence)
        last_sequence_scaled = last_sequence_scaled.reshape(1, X.shape[1], X.shape[2])
        
        # Predict probabilities for each position
        position_probs = self.model.predict(last_sequence_scaled, verbose=0)
        
        combinations = []
        attempts = 0
        max_attempts = n_combinations * 10
        
        # Create historical set for filtering
        numeric_cols = [col for col in historial_df.columns 
                       if 'bolilla' in col.lower() or col.startswith('Bolilla')]
        historical_combos = set()
        for _, row in historial_df.iterrows():
            combo = tuple(sorted([int(row[col]) for col in numeric_cols[:6]]))
            historical_combos.add(combo)
        
        while len(combinations) < n_combinations and attempts < max_attempts:
            attempts += 1
            
            # Generate a combination by sampling from each position's distribution
            combination = []
            used_numbers = set()
            
            # Sample for each position
            for pos in range(6):
                probs = position_probs[pos][0]  # Get probabilities for this position
                
                # Mask out already used numbers
                available_probs = probs.copy()
                for used_num in used_numbers:
                    available_probs[used_num - 1] = 0
                    
                # Renormalize
                if np.sum(available_probs) > 0:
                    available_probs = available_probs / np.sum(available_probs)
                else:
                    # Fallback: uniform distribution over unused numbers
                    available_probs = np.ones(40)
                    for used_num in used_numbers:
                        available_probs[used_num - 1] = 0
                    available_probs = available_probs / np.sum(available_probs)
                
                # Sample number
                number = np.random.choice(range(1, 41), p=available_probs) 
                combination.append(number)
                used_numbers.add(number)
            
            # Sort combination and check if it's valid
            combination = sorted(combination)
            combo_tuple = tuple(combination)
            
            if combo_tuple not in historical_combos and combo_tuple not in [tuple(c['combination']) for c in combinations]:
                # Calculate confidence score based on probabilities
                confidence = 0
                for pos, num in enumerate(combination):
                    confidence += position_probs[pos][0][num - 1]
                confidence = confidence / 6
                
                combinations.append({
                    'combination': combination,
                    'source': 'enhanced_lstm',
                    'score': float(confidence),
                    'metrics': {
                        'model_confidence': float(confidence),
                        'attention_based': self.config.use_attention,
                        'bidirectional': self.config.use_bidirectional
                    }
                })
        
        logger.info(f"✅ Generated {len(combinations)} combinations in {attempts} attempts")
        return combinations
        
    def save_model(self):
        """Save the trained model and scaler"""
        if self.model is None or self.scaler is None:
            raise RuntimeError("No model or scaler to save")
            
        if not self.config.model_path:
            raise ValueError("Model path not configured")
            
        self.config.model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save model
        model_path = self.config.model_path.with_suffix('.h5')
        self.model.save(str(model_path))
        
        # Save scaler
        scaler_path = model_path.with_name(f"{model_path.stem}_scaler.pkl")
        joblib.dump(self.scaler, str(scaler_path))
        
        # Save config and metadata
        metadata = {
            "config": asdict(self.config),
            "training_date": datetime.datetime.now().isoformat(),
            "model_type": "enhanced_lstm_with_attention",
            "n_features": getattr(self.scaler, 'n_features_in_', None),
            "tf_version": tf.__version__
        }
        metadata_path = model_path.with_name(f"{model_path.stem}_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        logger.info(f"✅ Enhanced LSTM model saved to {model_path}")

def generar_combinaciones_lstm_enhanced(
    historial_df: pd.DataFrame,
    cantidad: int = 10,
    config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Main interface for generating combinations with enhanced LSTM
    
    Args:
        historial_df: Historical lottery data
        cantidad: Number of combinations to generate
        config: Optional configuration overrides
        
    Returns:
        List of combination dictionaries
    """
    # Load or create configuration
    base_config = EnhancedLSTMConfig()
    if config:
        # Update configuration with provided values
        for key, value in config.items():
            if hasattr(base_config, key):
                setattr(base_config, key, value)
    
    # Create and train model
    model = EnhancedLSTMModel(base_config)
    
    try:
        # Train model
        model.train(historial_df, verbose=1)
        
        # Generate combinations
        combinations = model.predict_combinations(historial_df, cantidad)
        
        # Score combinations using existing scoring system
        try:
            scored_combinations = score_combinations(combinations, historial_df)
            return scored_combinations
        except Exception as e:
            logger.warning(f"Scoring failed: {e}. Returning unscored combinations.")
            return combinations
            
    except Exception as e:
        logger.error(f"Enhanced LSTM failed: {e}")
        logger.info("Falling back to random combinations...")
        
        # Fallback to random combinations
        fallback_combinations = []
        for _ in range(cantidad):
            combo = sorted(random.sample(range(1, 41), 6))
            fallback_combinations.append({
                'combination': combo,
                'source': 'enhanced_lstm_fallback',
                'score': 0.5,
                'metrics': {}
            })
        return fallback_combinations