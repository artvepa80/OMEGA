# OMEGA_PRO_AI_v10.1/modules/model_optimization_suite.py
"""
Model Optimization Suite for OMEGA PRO AI
Fixes and enhances Transformer, GBoost, and other models for optimal performance
Implements hyperparameter optimization and model coordination
"""

import logging
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import json
import traceback
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import optuna
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
import warnings

# Set reproducibility seeds
np.random.seed(42)
torch.manual_seed(42)
if torch.cuda.is_available():
    torch.cuda.manual_seed(42)
    torch.cuda.manual_seed_all(42)

# Local imports
from modules.lottery_transformer import LotteryTransformer
from modules.learning.gboost_jackpot_classifier import GBoostJackpotClassifier
from modules.advanced_feature_engineering import AdvancedFeatureEngineer, create_enhanced_features

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

# Optuna logging control
optuna.logging.set_verbosity(optuna.logging.WARNING)

class TransformerModelOptimizer:
    """
    Optimized Transformer model with fixed architecture and enhanced training
    Addresses the issues found in the original transformer_model.py
    """
    
    def __init__(self, num_numbers: int = 40, max_sequence_length: int = 10):
        self.num_numbers = num_numbers
        self.max_sequence_length = max_sequence_length
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.feature_engineer = AdvancedFeatureEngineer()
        
    def create_optimized_transformer(self, d_model: int = 256, nhead: int = 8, 
                                   num_layers: int = 4, dropout: float = 0.1) -> nn.Module:
        """
        Create optimized transformer with proper error handling
        """
        class OptimizedLotteryTransformer(nn.Module):
            def __init__(self, num_numbers, d_model, nhead, num_layers, dropout):
                super().__init__()
                self.num_numbers = num_numbers
                self.d_model = d_model
                
                # Embedding layers
                self.number_embedding = nn.Embedding(num_numbers + 1, d_model, padding_idx=0)
                self.position_embedding = nn.Embedding(100, d_model)  # Max 100 positions
                
                # Transformer encoder
                encoder_layer = nn.TransformerEncoderLayer(
                    d_model=d_model,
                    nhead=nhead,
                    dim_feedforward=d_model * 4,
                    dropout=dropout,
                    batch_first=True
                )
                self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
                
                # Output layers for each position (6 lottery positions)
                self.output_heads = nn.ModuleList([
                    nn.Linear(d_model, num_numbers) for _ in range(6)
                ])
                
                # Dropout
                self.dropout = nn.Dropout(dropout)
                
            def forward(self, numbers, temporal_features=None, positions=None):
                batch_size, seq_len = numbers.shape
                
                # Create embeddings
                number_emb = self.number_embedding(numbers)
                
                # Position embeddings
                if positions is None:
                    positions = torch.arange(seq_len, device=numbers.device).unsqueeze(0).expand(batch_size, -1)
                pos_emb = self.position_embedding(positions)
                
                # Combine embeddings
                embeddings = number_emb + pos_emb
                embeddings = self.dropout(embeddings)
                
                # Transformer forward pass
                transformer_output = self.transformer(embeddings)
                
                # Get final representation (use last timestep)
                final_repr = transformer_output[:, -1, :]  # (batch_size, d_model)
                
                # Generate outputs for each position
                position_outputs = []
                for head in self.output_heads:
                    position_outputs.append(head(final_repr))
                
                return position_outputs
        
        return OptimizedLotteryTransformer(num_numbers, d_model, nhead, num_layers, dropout)
    
    def prepare_transformer_data(self, historial_df: pd.DataFrame) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Prepare data for transformer training with proper error handling
        """
        try:
            # Get numeric columns
            numeric_cols = [col for col in historial_df.columns 
                           if 'bolilla' in col.lower() or col.startswith('Bolilla')]
            
            if len(numeric_cols) < 6:
                raise ValueError(f"Need at least 6 ball columns, found {len(numeric_cols)}")
            
            # Extract sequences
            data = historial_df[numeric_cols[:6]].values.astype(int)
            
            # Validate data range
            if np.any((data < 1) | (data > 40)):
                logger.warning("Data contains invalid numbers, clipping to valid range")
                data = np.clip(data, 1, 40)
            
            # Create sequences
            sequences = []
            targets = []
            
            for i in range(self.max_sequence_length, len(data)):
                seq = data[i-self.max_sequence_length:i]  # Input sequence
                target = data[i]  # Target to predict
                
                sequences.append(seq)
                targets.append(target)
            
            if len(sequences) == 0:
                raise ValueError("No sequences could be created from the data")
            
            # Convert to tensors
            X = torch.tensor(sequences, dtype=torch.long, device=self.device)
            y = torch.tensor(targets, dtype=torch.long, device=self.device)
            
            logger.info(f"✅ Transformer data prepared: {X.shape} -> {y.shape}")
            return X, y
            
        except Exception as e:
            logger.error(f"❌ Error preparing transformer data: {e}")
            raise
    
    def train_optimized_transformer(self, historial_df: pd.DataFrame, 
                                  epochs: int = 50, learning_rate: float = 0.001) -> Dict[str, Any]:
        """
        Train the optimized transformer model
        """
        try:
            logger.info("🚀 Training optimized transformer...")
            
            # Prepare data
            X, y = self.prepare_transformer_data(historial_df)
            
            # Create model
            self.model = self.create_optimized_transformer()
            self.model.to(self.device)
            
            # Loss and optimizer
            criterion = nn.CrossEntropyLoss(ignore_index=0)
            optimizer = torch.optim.AdamW(self.model.parameters(), lr=learning_rate, weight_decay=0.01)
            scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
            
            # Training loop
            self.model.train()
            training_losses = []
            
            for epoch in range(epochs):
                total_loss = 0
                num_batches = 0
                
                # Simple batch processing (process all data as one batch if small enough)
                optimizer.zero_grad()
                
                # Forward pass
                position_outputs = self.model(X)
                
                # Calculate loss for each position
                losses = []
                for pos in range(6):
                    target_pos = y[:, pos] - 1  # Convert to 0-based indexing
                    loss_pos = criterion(position_outputs[pos], target_pos)
                    losses.append(loss_pos)
                
                # Total loss
                total_batch_loss = sum(losses)
                total_loss += total_batch_loss.item()
                num_batches += 1
                
                # Backward pass
                total_batch_loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()
                scheduler.step()
                
                avg_loss = total_loss / num_batches
                training_losses.append(avg_loss)
                
                if epoch % 10 == 0:
                    logger.info(f"Epoch {epoch}/{epochs}, Loss: {avg_loss:.4f}")
            
            self.model.eval()
            logger.info("✅ Transformer training completed")
            
            return {
                'success': True,
                'final_loss': training_losses[-1],
                'training_losses': training_losses
            }
            
        except Exception as e:
            logger.error(f"❌ Transformer training failed: {e}")
            logger.error(traceback.format_exc())
            return {'success': False, 'error': str(e)}
    
    def generate_transformer_combinations(self, historial_df: pd.DataFrame, 
                                        cantidad: int = 10) -> List[Dict[str, Any]]:
        """
        Generate combinations using the optimized transformer
        """
        if self.model is None:
            logger.warning("Model not trained, training now...")
            result = self.train_optimized_transformer(historial_df)
            if not result.get('success', False):
                return self._generate_fallback_combinations(cantidad)
        
        try:
            # Prepare input sequence
            X, _ = self.prepare_transformer_data(historial_df)
            if len(X) == 0:
                return self._generate_fallback_combinations(cantidad)
            
            # Use the last sequence for prediction
            last_sequence = X[-1:].to(self.device)
            
            combinations = []
            self.model.eval()
            
            with torch.no_grad():
                for _ in range(cantidad * 2):  # Generate extra to filter
                    # Forward pass
                    position_outputs = self.model(last_sequence)
                    
                    # Sample from probability distributions
                    combination = []
                    used_numbers = set()
                    
                    for pos in range(6):
                        logits = position_outputs[pos][0]  # Get first (and only) batch item
                        probs = torch.softmax(logits, dim=-1)
                        
                        # Mask used numbers
                        for used_num in used_numbers:
                            probs[used_num - 1] = 0
                        
                        # Renormalize
                        probs = probs / probs.sum()
                        
                        # Sample
                        if torch.sum(probs) > 0:
                            sampled_idx = torch.multinomial(probs, 1).item()
                            number = sampled_idx + 1  # Convert back to 1-based
                        else:
                            # Fallback to random unused number
                            available = [i for i in range(1, 41) if i not in used_numbers]
                            number = np.random.choice(available) if available else np.random.randint(1, 41)
                        
                        combination.append(number)
                        used_numbers.add(number)
                    
                    # Validate and add combination
                    combination = sorted(list(set(combination)))
                    if len(combination) == 6 and all(1 <= n <= 40 for n in combination):
                        confidence = float(torch.mean(torch.stack([
                            torch.softmax(position_outputs[pos][0], dim=-1)[combination[pos] - 1]
                            for pos in range(6)
                        ])))
                        
                        combinations.append({
                            'combination': combination,
                            'source': 'optimized_transformer',
                            'score': confidence,
                            'metrics': {'transformer_confidence': confidence}
                        })
                        
                        if len(combinations) >= cantidad:
                            break
            
            # Fill with fallbacks if needed
            while len(combinations) < cantidad:
                fallback = self._generate_fallback_combinations(1)[0]
                fallback['source'] = 'optimized_transformer_fallback'
                combinations.append(fallback)
            
            logger.info(f"✅ Generated {len(combinations)} transformer combinations")
            return combinations[:cantidad]
            
        except Exception as e:
            logger.error(f"❌ Transformer generation failed: {e}")
            return self._generate_fallback_combinations(cantidad)
    
    def _generate_fallback_combinations(self, cantidad: int) -> List[Dict[str, Any]]:
        """Generate fallback combinations"""
        combinations = []
        for _ in range(cantidad):
            combo = sorted(np.random.choice(range(1, 41), 6, replace=False))
            combinations.append({
                'combination': combo.tolist(),
                'source': 'transformer_fallback',
                'score': 0.4,
                'metrics': {'is_fallback': True}
            })
        return combinations

class GBoostOptimizer:
    """
    Optimized GBoost classifier with enhanced feature matching and training
    """
    
    def __init__(self):
        self.model = None
        self.feature_engineer = AdvancedFeatureEngineer()
        self.label_encoders = {}
        self.is_trained = False
    
    def prepare_gboost_features(self, historial_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare enhanced features for GBoost training
        """
        try:
            # Extract comprehensive features
            X = self.feature_engineer.extract_comprehensive_features(historial_df)
            
            # Create binary classification targets for jackpot prediction
            # Target: 1 if combination contains consecutive pairs (high-value pattern), 0 otherwise
            y = []
            
            numeric_cols = [col for col in historial_df.columns 
                           if 'bolilla' in col.lower() or col.startswith('Bolilla')]
            
            for _, row in historial_df.iterrows():
                numbers = sorted([int(row[col]) for col in numeric_cols[:6]])
                
                # Check for consecutive pairs (74.5% success pattern from analysis)
                has_consecutive = any(numbers[i+1] - numbers[i] == 1 for i in range(5))
                
                # Check for hot numbers (39, 28, 29 from successful prediction)
                has_hot_numbers = any(num in [39, 28, 29] for num in numbers)
                
                # Combine criteria for positive classification
                is_jackpot_pattern = has_consecutive or has_hot_numbers
                y.append(1 if is_jackpot_pattern else 0)
            
            y = np.array(y)
            
            logger.info(f"✅ GBoost features prepared: {X.shape}, positive samples: {np.sum(y)}/{len(y)}")
            return X, y
            
        except Exception as e:
            logger.error(f"❌ GBoost feature preparation failed: {e}")
            raise
    
    def train_optimized_gboost(self, historial_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Train optimized GBoost model with hyperparameter optimization
        """
        try:
            logger.info("🚀 Training optimized GBoost...")
            
            # Prepare features
            X, y = self.prepare_gboost_features(historial_df)
            
            if len(np.unique(y)) < 2:
                logger.warning("Insufficient target diversity for classification")
                return {'success': False, 'error': 'Insufficient target diversity'}
            
            # Hyperparameter optimization with Optuna
            def objective(trial):
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                    'max_depth': trial.suggest_int('max_depth', 3, 10),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                    'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                    'max_features': trial.suggest_float('max_features', 0.6, 1.0),
                    'random_state': 42
                }
                
                model = GradientBoostingClassifier(**params)
                
                # Cross-validation score
                cv_scores = cross_val_score(model, X, y, cv=5, scoring='roc_auc', n_jobs=-1)
                return cv_scores.mean()
            
            # Optimize hyperparameters
            study = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler())
            study.optimize(objective, n_trials=20, timeout=300)  # 5 minutes max
            
            # Train final model with best parameters
            best_params = study.best_params
            self.model = GradientBoostingClassifier(**best_params)
            self.model.fit(X, y)
            
            # Calculate feature importance
            feature_importance = self.model.feature_importances_
            
            self.is_trained = True
            
            logger.info("✅ GBoost training completed")
            logger.info(f"📊 Best ROC-AUC: {study.best_value:.4f}")
            
            return {
                'success': True,
                'best_score': study.best_value,
                'best_params': best_params,
                'feature_importance': feature_importance.tolist()
            }
            
        except Exception as e:
            logger.error(f"❌ GBoost training failed: {e}")
            logger.error(traceback.format_exc())
            return {'success': False, 'error': str(e)}
    
    def generate_gboost_combinations(self, historial_df: pd.DataFrame, 
                                   cantidad: int = 10) -> List[Dict[str, Any]]:
        """
        Generate combinations using optimized GBoost
        """
        if not self.is_trained:
            logger.info("Training GBoost model...")
            result = self.train_optimized_gboost(historial_df)
            if not result.get('success', False):
                return self._generate_fallback_combinations(cantidad)
        
        try:
            combinations = []
            
            # Generate candidate combinations
            for _ in range(cantidad * 10):  # Generate many candidates
                # Create random combination
                candidate = sorted(np.random.choice(range(1, 41), 6, replace=False))
                
                # Create feature vector for this combination
                # Use the last draw's context with this candidate
                temp_df = historial_df.copy()
                
                # Add candidate as new row
                numeric_cols = [col for col in historial_df.columns 
                               if 'bolilla' in col.lower() or col.startswith('Bolilla')]
                
                new_row = historial_df.iloc[-1].copy()
                for i, col in enumerate(numeric_cols[:6]):
                    new_row[col] = candidate[i]
                
                temp_df = pd.concat([temp_df, new_row.to_frame().T], ignore_index=True)
                
                # Extract features for the candidate
                features = self.feature_engineer.extract_comprehensive_features(temp_df)
                candidate_features = features[-1:].reshape(1, -1)
                
                # Predict probability
                prob = self.model.predict_proba(candidate_features)[0, 1]  # Probability of positive class
                
                combinations.append({
                    'combination': candidate,
                    'source': 'optimized_gboost',
                    'score': float(prob),
                    'metrics': {
                        'gboost_probability': float(prob),
                        'jackpot_pattern_score': float(prob)
                    }
                })
            
            # Sort by probability and return top combinations
            combinations.sort(key=lambda x: x['score'], reverse=True)
            selected = combinations[:cantidad]
            
            logger.info(f"✅ Generated {len(selected)} GBoost combinations")
            return selected
            
        except Exception as e:
            logger.error(f"❌ GBoost generation failed: {e}")
            return self._generate_fallback_combinations(cantidad)
    
    def _generate_fallback_combinations(self, cantidad: int) -> List[Dict[str, Any]]:
        """Generate fallback combinations"""
        combinations = []
        for _ in range(cantidad):
            combo = sorted(np.random.choice(range(1, 41), 6, replace=False))
            combinations.append({
                'combination': combo.tolist(),
                'source': 'gboost_fallback',
                'score': 0.4,
                'metrics': {'is_fallback': True}
            })
        return combinations

class HyperparameterOptimizer:
    """
    Hyperparameter optimization for all OMEGA models
    """
    
    def __init__(self):
        self.optimization_results = {}
    
    def optimize_lstm_hyperparameters(self, historial_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Optimize LSTM hyperparameters using Optuna
        """
        def objective(trial):
            from modules.lstm_model_enhanced import EnhancedLSTMConfig, EnhancedLSTMModel
            
            # Suggest hyperparameters
            config = EnhancedLSTMConfig(
                n_units=trial.suggest_int('n_units', 64, 256),
                dropout_rate=trial.suggest_float('dropout_rate', 0.1, 0.5),
                learning_rate=trial.suggest_float('learning_rate', 0.0001, 0.01, log=True),
                attention_heads=trial.suggest_int('attention_heads', 2, 8),
                epochs=20,  # Reduced for optimization
                use_attention=trial.suggest_categorical('use_attention', [True, False]),
                use_bidirectional=trial.suggest_categorical('use_bidirectional', [True, False])
            )
            
            try:
                model = EnhancedLSTMModel(config)
                history = model.train(historial_df, verbose=0)
                
                # Return validation loss (lower is better)
                val_loss = history.history.get('val_loss', [float('inf')])
                return min(val_loss) if val_loss else float('inf')
                
            except Exception:
                return float('inf')
        
        try:
            study = optuna.create_study(direction='minimize')
            study.optimize(objective, n_trials=10, timeout=1800)  # 30 minutes max
            
            return {
                'success': True,
                'best_params': study.best_params,
                'best_score': study.best_value
            }
        except Exception as e:
            logger.error(f"LSTM hyperparameter optimization failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_optimized_parameters(self, model_type: str) -> Dict[str, Any]:
        """
        Get optimized parameters for a specific model type
        """
        # Default optimized parameters based on analysis
        defaults = {
            'enhanced_lstm': {
                'n_units': 128,
                'dropout_rate': 0.3,
                'learning_rate': 0.001,
                'epochs': 100,
                'use_attention': True,
                'use_bidirectional': True,
                'attention_heads': 4
            },
            'transformer': {
                'd_model': 256,
                'nhead': 8,
                'num_layers': 4,
                'dropout': 0.1,
                'learning_rate': 0.001
            },
            'gboost': {
                'n_estimators': 300,
                'max_depth': 6,
                'learning_rate': 0.1,
                'subsample': 0.8,
                'max_features': 0.8
            }
        }
        
        return defaults.get(model_type, {})

# Main interface functions
def generar_combinaciones_transformer_optimized(historial_df: pd.DataFrame, 
                                              cantidad: int = 10) -> List[Dict[str, Any]]:
    """Generate combinations using optimized Transformer"""
    optimizer = TransformerModelOptimizer()
    return optimizer.generate_transformer_combinations(historial_df, cantidad)

def generar_combinaciones_gboost_optimized(historial_df: pd.DataFrame, 
                                         cantidad: int = 10) -> List[Dict[str, Any]]:
    """Generate combinations using optimized GBoost"""
    optimizer = GBoostOptimizer()
    return optimizer.generate_gboost_combinations(historial_df, cantidad)