#!/usr/bin/env python3
"""
PyTorch LSTM Adapter for OMEGA PRO AI v10.1
Integrates pre-trained PyTorch LSTM models with OMEGA's Keras-based infrastructure
"""

import os
import logging
import numpy as np
import torch
import torch.nn as nn
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import glob

logger = logging.getLogger(__name__)

@dataclass
class PyTorchModelInfo:
    """Information about a PyTorch model checkpoint"""
    path: Path
    timestamp: str
    hyperparameters: Dict[str, Any]
    training_history: Dict[str, List[float]]
    is_trained: bool

class AdvancedLSTMNetwork(nn.Module):
    """
    Replica of the PyTorch LSTM network architecture for loading pre-trained models
    This must match exactly with the architecture in lstm_predictor_v2.py
    """
    
    def __init__(self, 
                 input_size: int = 64,
                 hidden_size: int = 256,
                 num_layers: int = 3,
                 output_size: int = 6,
                 dropout: float = 0.3,
                 bidirectional: bool = True):
        
        super(AdvancedLSTMNetwork, self).__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_size = output_size
        self.bidirectional = bidirectional
        
        # Embedding para números (1-40)
        self.number_embedding = nn.Embedding(41, input_size)  # +1 para padding
        
        # Codificador posicional
        self.positional_encoder = PositionalEncoder(input_size)
        
        # Capas LSTM con dropout
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=bidirectional
        )
        
        # Normalización
        lstm_output_size = hidden_size * 2 if bidirectional else hidden_size
        self.layer_norm = nn.LayerNorm(lstm_output_size)
        
        # Capas de atención
        self.attention = nn.MultiheadAttention(
            embed_dim=lstm_output_size,
            num_heads=8,
            dropout=dropout,
            batch_first=True
        )
        
        # Capas fully connected
        self.fc_layers = nn.Sequential(
            nn.Linear(lstm_output_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.BatchNorm1d(hidden_size),
            
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.BatchNorm1d(hidden_size // 2),
            
            nn.Linear(hidden_size // 2, output_size * 40)  # 6 posiciones x 40 números
        )
        
        # Capas de salida especializadas
        self.position_heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(lstm_output_size, hidden_size // 4),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_size // 4, 40),
                nn.Softmax(dim=-1)
            )
            for _ in range(6)  # Una cabeza por posición
        ])
        
        # Predictor de confianza
        self.confidence_head = nn.Sequential(
            nn.Linear(lstm_output_size, hidden_size // 4),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 4, 1),
            nn.Sigmoid()
        )
        
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x):
        # Handle different input shapes robustly
        if len(x.shape) == 2:
            batch_size, seq_len = x.shape
        elif len(x.shape) == 3:
            batch_size, seq_len, _ = x.shape
            x = x[:, :, 0] if x.shape[2] > 1 else x.squeeze(-1)
        else:
            raise ValueError(f"Expected 2D or 3D input, got shape {x.shape}")
        
        # Ensure x is 2D [batch_size, seq_len] with valid indices
        if x.dim() != 2:
            x = x.view(batch_size, -1)
        
        # Clamp values to valid range for embedding (0-40, where 0 is padding)
        x = torch.clamp(x, 0, 40)
        
        # Embedding de números
        embedded = self.number_embedding(x)  # [batch, seq, embed_dim]
        
        # Añadir codificación posicional
        embedded = self.positional_encoder(embedded.transpose(0, 1)).transpose(0, 1)
        
        # LSTM
        lstm_out, (hidden, cell) = self.lstm(embedded)
        lstm_out = self.layer_norm(lstm_out)
        
        # Atención
        attended, attention_weights = self.attention(lstm_out, lstm_out, lstm_out)
        
        # Pooling global (promedio ponderado por atención)
        pooled = torch.mean(attended, dim=1)  # [batch, hidden_size]
        pooled = self.dropout(pooled)
        
        # Predicciones por posición
        position_outputs = []
        for head in self.position_heads:
            pos_output = head(pooled)  # [batch, 40]
            position_outputs.append(pos_output)
        
        # Confianza
        confidence = self.confidence_head(pooled)  # [batch, 1]
        
        # Combinar salidas
        position_probs = torch.stack(position_outputs, dim=1)  # [batch, 6, 40]
        
        return {
            'position_probabilities': position_probs,
            'confidence': confidence,
            'attention_weights': attention_weights,
            'lstm_output': lstm_out
        }

class PositionalEncoder(nn.Module):
    """Codificador posicional para secuencias de números"""
    
    def __init__(self, d_model: int, max_len: int = 100):
        super(PositionalEncoder, self).__init__()
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * 
                           (-np.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        
        self.register_buffer('pe', pe)
    
    def forward(self, x):
        # Asegurar que x es un tensor
        if not isinstance(x, torch.Tensor):
            x = torch.tensor(x)
        return x + self.pe[:x.size(0), :]

class PyTorchLSTMAdapter:
    """
    Adapter that integrates pre-trained PyTorch LSTM models with OMEGA's infrastructure
    Provides a Keras-compatible interface while using PyTorch models internally
    """
    
    def __init__(self, models_directory: str = "models/"):
        self.models_directory = Path(models_directory)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.model_info = None
        self.sequence_length = 20  # Default from training
        
        logger.info(f"🔧 PyTorch LSTM Adapter initialized on {self.device}")
    
    def find_best_model(self) -> Optional[PyTorchModelInfo]:
        """
        Find the best available pre-trained PyTorch LSTM model
        Prioritizes by timestamp (newest first)
        """
        pattern = str(self.models_directory / "meta_learning_state_*_lstm_v2.pt")
        model_files = glob.glob(pattern)
        
        if not model_files:
            logger.warning("⚠️ No pre-trained PyTorch LSTM models found")
            return None
        
        # Sort by timestamp (newest first)
        model_files.sort(reverse=True)
        
        for model_path in model_files:
            try:
                model_path = Path(model_path)
                checkpoint = torch.load(model_path, map_location='cpu')
                
                # Validate checkpoint structure
                required_keys = ['model_state_dict', 'hyperparameters', 'is_trained']
                if all(key in checkpoint for key in required_keys):
                    if checkpoint['is_trained']:
                        # Extract timestamp from filename
                        timestamp = model_path.stem.split('_')[3] + '_' + model_path.stem.split('_')[4]
                        
                        model_info = PyTorchModelInfo(
                            path=model_path,
                            timestamp=timestamp,
                            hyperparameters=checkpoint['hyperparameters'],
                            training_history=checkpoint.get('training_history', {}),
                            is_trained=checkpoint['is_trained']
                        )
                        
                        logger.info(f"✅ Found valid PyTorch model: {model_path.name}")
                        return model_info
                        
            except Exception as e:
                logger.warning(f"⚠️ Error loading {model_path}: {e}")
                continue
        
        logger.error("❌ No valid trained PyTorch models found")
        return None
    
    def load_model(self, model_info: Optional[PyTorchModelInfo] = None) -> bool:
        """
        Load a pre-trained PyTorch LSTM model
        """
        if model_info is None:
            model_info = self.find_best_model()
            
        if model_info is None:
            return False
        
        try:
            # Load checkpoint
            checkpoint = torch.load(model_info.path, map_location=self.device)
            
            # Get hyperparameters
            hyperparams = model_info.hyperparameters
            self.sequence_length = hyperparams.get('sequence_length', 20)
            
            # Create model with correct architecture
            self.model = AdvancedLSTMNetwork(
                input_size=64,  # From architecture analysis
                hidden_size=hyperparams.get('hidden_size', 256),
                num_layers=hyperparams.get('num_layers', 3),
                dropout=hyperparams.get('dropout', 0.3),
                bidirectional=True
            ).to(self.device)
            
            # Load trained weights
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.eval()
            
            self.model_info = model_info
            
            logger.info(f"🎯 PyTorch model loaded successfully: {model_info.path.name}")
            logger.info(f"   Sequence length: {self.sequence_length}")
            logger.info(f"   Hidden size: {hyperparams.get('hidden_size', 256)}")
            logger.info(f"   Layers: {hyperparams.get('num_layers', 3)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading PyTorch model: {e}")
            return False
    
    def predict_combinations(self, 
                           historical_data: List[List[int]], 
                           num_predictions: int = 10,
                           min_confidence: float = 0.3) -> List[Dict[str, Any]]:
        """
        Generate lottery combinations using the pre-trained PyTorch model
        Returns predictions in OMEGA's expected format
        """
        if self.model is None:
            logger.error("❌ No model loaded for prediction")
            return []
        
        if len(historical_data) < self.sequence_length:
            logger.warning(f"⚠️ Insufficient historical data: {len(historical_data)} < {self.sequence_length}")
            return []
        
        try:
            self.model.eval()
            predictions = []
            
            with torch.no_grad():
                # Use the most recent sequence as input
                input_sequence = historical_data[-self.sequence_length:]
                
                # Convert to tensor and move to device
                input_tensor = torch.LongTensor([input_sequence]).to(self.device)
                
                # Generate multiple predictions
                for prediction_idx in range(num_predictions):
                    outputs = self.model(input_tensor)
                    
                    position_probs = outputs['position_probabilities']
                    confidence = outputs['confidence'].item()
                    
                    # Skip low-confidence predictions
                    if confidence < min_confidence:
                        continue
                    
                    # Generate combination from probabilities
                    combination = self._generate_combination_from_probs(position_probs[0])
                    
                    # Create OMEGA-compatible prediction
                    prediction = {
                        'numbers': combination,
                        'combination': combination,
                        'source': 'pytorch_lstm_v2',
                        'score': confidence,
                        'confidence': confidence,
                        'normalized': confidence,
                        'metrics': {
                            'model_type': 'pytorch_advanced_lstm',
                            'model_timestamp': self.model_info.timestamp,
                            'sequence_length': self.sequence_length,
                            'prediction_index': prediction_idx,
                            'position_confidences': [
                                torch.max(position_probs[0, pos, :]).item() 
                                for pos in range(6)
                            ]
                        }
                    }
                    
                    predictions.append(prediction)
                    
                    # Update input for next prediction (sliding window)
                    new_sequence = input_sequence[1:] + [combination]
                    input_tensor = torch.LongTensor([new_sequence]).to(self.device)
            
            # Sort by confidence/score
            predictions.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(f"🎯 Generated {len(predictions)} PyTorch predictions with confidence >= {min_confidence}")
            
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Error during PyTorch prediction: {e}")
            return []
    
    def _generate_combination_from_probs(self, position_probs: torch.Tensor) -> List[int]:
        """
        Generate a valid lottery combination from position probabilities
        Ensures no duplicates and valid range (1-40)
        """
        combination = []
        used_numbers = set()
        
        for pos in range(6):
            probs = position_probs[pos, :].detach().cpu().numpy()
            
            # Sample from probability distribution, avoiding duplicates
            attempts = 0
            while attempts < 40:
                number = np.random.choice(40, p=probs) + 1  # Convert to 1-40 range
                if number not in used_numbers:
                    combination.append(number)
                    used_numbers.add(number)
                    break
                attempts += 1
            else:
                # Fallback: find first available number
                for num in range(1, 41):
                    if num not in used_numbers:
                        combination.append(num)
                        used_numbers.add(num)
                        break
        
        return sorted(combination)
    
    def is_available(self) -> bool:
        """Check if PyTorch models are available and can be loaded"""
        return self.find_best_model() is not None
    
    def get_model_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the currently loaded model"""
        if self.model_info is None:
            return None
        
        return {
            'model_path': str(self.model_info.path),
            'timestamp': self.model_info.timestamp,
            'hyperparameters': self.model_info.hyperparameters,
            'is_trained': self.model_info.is_trained,
            'device': str(self.device),
            'sequence_length': self.sequence_length,
            'available': True,
            'model_type': 'pytorch_advanced_lstm_v2'
        }

# Singleton instance for global access
pytorch_adapter = PyTorchLSTMAdapter()

def get_pytorch_lstm_predictions(historical_data: List[List[int]], 
                                num_predictions: int = 10) -> List[Dict[str, Any]]:
    """
    Convenience function to get predictions from PyTorch models
    This is the main interface for OMEGA integration
    """
    # Try to load model if not already loaded
    if pytorch_adapter.model is None:
        success = pytorch_adapter.load_model()
        if not success:
            logger.warning("⚠️ No PyTorch models available, falling back to Keras training")
            return []
    
    return pytorch_adapter.predict_combinations(historical_data, num_predictions)

def is_pytorch_model_available() -> bool:
    """Check if pre-trained PyTorch models are available"""
    return pytorch_adapter.is_available()

if __name__ == "__main__":
    # Test the adapter
    print("🧠 Testing PyTorch LSTM Adapter")
    
    adapter = PyTorchLSTMAdapter()
    
    # Check available models
    model_info = adapter.find_best_model()
    if model_info:
        print(f"📂 Found model: {model_info.path.name}")
        print(f"   Timestamp: {model_info.timestamp}")
        print(f"   Hyperparameters: {model_info.hyperparameters}")
        
        # Load and test
        if adapter.load_model(model_info):
            # Create sample historical data
            sample_data = [
                [1, 15, 23, 31, 35, 40], [3, 12, 18, 27, 33, 39],
                [5, 14, 22, 28, 34, 38], [2, 11, 19, 25, 32, 37],
                [7, 16, 24, 29, 36, 38], [4, 13, 21, 26, 34, 39],
                [6, 17, 25, 30, 37, 40], [8, 10, 20, 24, 31, 35],
                [9, 18, 26, 32, 38, 40], [1, 12, 20, 28, 33, 36],
                [3, 14, 19, 27, 35, 39], [5, 11, 17, 23, 29, 34],
                [2, 16, 22, 30, 36, 40], [4, 9, 15, 25, 31, 37],
                [6, 13, 21, 26, 32, 38], [7, 18, 24, 28, 34, 39],
                [8, 12, 19, 27, 33, 35], [1, 10, 16, 22, 29, 31],
                [3, 11, 17, 24, 30, 36], [5, 15, 20, 26, 32, 40],
                [2, 14, 18, 25, 28, 37], [4, 13, 19, 23, 34, 38]
            ]
            
            print(f"🎯 Testing predictions with {len(sample_data)} historical combinations...")
            
            predictions = adapter.predict_combinations(sample_data, num_predictions=5)
            
            if predictions:
                print(f"✅ Generated {len(predictions)} predictions:")
                for i, pred in enumerate(predictions, 1):
                    combo = pred['combination']
                    confidence = pred['confidence']
                    print(f"   {i}. {combo} (confidence: {confidence:.3f})")
            else:
                print("❌ No predictions generated")
    else:
        print("❌ No PyTorch models found")