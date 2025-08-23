#!/usr/bin/env python3
"""
LSTM Predictor v2 - Optimizado para OMEGA PRO AI
Modelo LSTM profundo con dropout, early stopping y evaluación posicional
"""

import logging
logger = logging.getLogger(__name__)
import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

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

class AdvancedLSTMNetwork(nn.Module):
    """Red LSTM avanzada con múltiples capas y características optimizadas"""
    
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
        batch_size, seq_len = x.shape
        
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

class EarlyStopping:
    """Early stopping para prevenir overfitting"""
    
    def __init__(self, patience: int = 10, min_delta: float = 0.001):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = float('inf')
        self.early_stop = False
    
    def __call__(self, val_loss: float):
        if val_loss < self.best_loss - self.min_delta:
            self.best_loss = val_loss
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True

class LSTMPredictorV2:
    """Predictor LSTM optimizado versión 2"""
    
    def __init__(self,
                 sequence_length: int = 20,
                 hidden_size: int = 256,
                 num_layers: int = 3,
                 dropout: float = 0.3,
                 learning_rate: float = 0.001,
                 batch_size: int = 32,
                 device: str = None):
        
        self.sequence_length = sequence_length
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        
        # Device
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        # Modelo
        self.model = AdvancedLSTMNetwork(
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout
        ).to(self.device)
        
        # Optimizador con scheduler
        self.optimizer = optim.AdamW(
            self.model.parameters(), 
            lr=learning_rate,
            weight_decay=0.01
        )
        
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, 
            mode='min',
            factor=0.5,
            patience=5
        )
        
        # Métricas y estado
        self.training_history = {
            'train_loss': [],
            'val_loss': [],
            'train_acc': [],
            'val_acc': [],
            'learning_rates': [],
            'epochs': []
        }
        
        self.is_trained = False
        self.best_model_state = None
        self.scaler = StandardScaler()
        
        logger.info(f"🧠 LSTM Predictor v2 inicializado en {self.device}")
        logger.info(f"   Secuencia: {sequence_length}, Hidden: {hidden_size}, Capas: {num_layers}")
    
    def prepare_sequences(self, data: List[List[int]]) -> Tuple[torch.Tensor, torch.Tensor]:
        """Prepara secuencias para entrenamiento"""
        if len(data) < self.sequence_length + 1:
            raise ValueError(f"Necesito al menos {self.sequence_length + 1} combinaciones")
        
        sequences = []
        targets = []
        
        for i in range(len(data) - self.sequence_length):
            # Secuencia de entrada
            seq = data[i:i + self.sequence_length]
            sequences.append(seq)
            
            # Target (siguiente combinación)
            target = data[i + self.sequence_length]
            targets.append(target)
        
        # Convertir a tensors
        sequences = torch.LongTensor(sequences)
        targets = torch.LongTensor(targets)
        
        logger.info(f"📊 Preparadas {len(sequences)} secuencias de longitud {self.sequence_length}")
        return sequences, targets
    
    def train(self, 
              historical_data: List[List[int]], 
              epochs: int = 20,
              validation_split: float = 0.2,
              early_stopping_patience: int = 15) -> Dict[str, Any]:
        """Entrena el modelo LSTM"""
        
        logger.info(f"🏋️ Iniciando entrenamiento LSTM v2...")
        
        try:
            # Preparar datos
            X, y = self.prepare_sequences(historical_data)
            
            # División train/validation
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=validation_split, random_state=42, shuffle=True
            )
            
            # DataLoaders
            train_dataset = TensorDataset(X_train, y_train)
            val_dataset = TensorDataset(X_val, y_val)
            
            train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=self.batch_size, shuffle=False)
            
            # Early stopping
            early_stopping = EarlyStopping(patience=early_stopping_patience)
            
            # Loop de entrenamiento
            best_val_loss = float('inf')
            
            for epoch in range(epochs):
                # Entrenamiento
                train_loss, train_acc = self._train_epoch(train_loader)
                
                # Validación
                val_loss, val_acc = self._validate_epoch(val_loader)
                
                # Scheduler
                self.scheduler.step(val_loss)
                current_lr = self.optimizer.param_groups[0]['lr']
                
                # Guardar mejor modelo
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    self.best_model_state = self.model.state_dict().copy()
                
                # Registrar métricas
                self.training_history['train_loss'].append(train_loss)
                self.training_history['val_loss'].append(val_loss)
                self.training_history['train_acc'].append(train_acc)
                self.training_history['val_acc'].append(val_acc)
                self.training_history['learning_rates'].append(current_lr)
                self.training_history['epochs'].append(epoch)
                
                # Logging
                if epoch % 10 == 0 or epoch == epochs - 1:
                    logger.info(f"Época {epoch:3d}/{epochs}: "
                               f"Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, "
                               f"Train Acc: {train_acc:.3f}, Val Acc: {val_acc:.3f}, "
                               f"LR: {current_lr:.6f}")
                
                # Early stopping
                early_stopping(val_loss)
                if early_stopping.early_stop:
                    logger.info(f"⏹️ Early stopping en época {epoch}")
                    break
            
            # Cargar mejor modelo
            if self.best_model_state:
                self.model.load_state_dict(self.best_model_state)
            
            self.is_trained = True
            
            results = {
                'final_train_loss': train_loss,
                'final_val_loss': val_loss,
                'final_train_acc': train_acc,
                'final_val_acc': val_acc,
                'best_val_loss': best_val_loss,
                'epochs_trained': epoch + 1,
                'early_stopped': early_stopping.early_stop
            }
            
            logger.info(f"✅ Entrenamiento completado: Val Loss: {best_val_loss:.4f}, "
                       f"Val Acc: {val_acc:.3f}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error en entrenamiento: {e}")
            raise
    
    def _train_epoch(self, train_loader: DataLoader) -> Tuple[float, float]:
        """Entrena una época"""
        self.model.train()
        total_loss = 0.0
        correct_predictions = 0
        total_predictions = 0
        
        for batch_x, batch_y in train_loader:
            batch_x = batch_x.to(self.device)
            batch_y = batch_y.to(self.device)
            
            self.optimizer.zero_grad()
            
            # Forward pass
            outputs = self.model(batch_x)
            position_probs = outputs['position_probabilities']
            confidence = outputs['confidence']
            
            # Calcular pérdida
            loss = self._calculate_loss(position_probs, batch_y, confidence)
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            
            self.optimizer.step()
            
            total_loss += loss.item()
            
            # Accuracy
            predicted = self._probs_to_combinations(position_probs)
            acc = self._calculate_positional_accuracy(predicted, batch_y)
            correct_predictions += acc * batch_x.size(0)
            total_predictions += batch_x.size(0)
        
        avg_loss = total_loss / len(train_loader)
        avg_acc = correct_predictions / total_predictions
        
        return avg_loss, avg_acc
    
    def _validate_epoch(self, val_loader: DataLoader) -> Tuple[float, float]:
        """Valida una época"""
        self.model.eval()
        total_loss = 0.0
        correct_predictions = 0
        total_predictions = 0
        
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x = batch_x.to(self.device)
                batch_y = batch_y.to(self.device)
                
                outputs = self.model(batch_x)
                position_probs = outputs['position_probabilities']
                confidence = outputs['confidence']
                
                loss = self._calculate_loss(position_probs, batch_y, confidence)
                total_loss += loss.item()
                
                predicted = self._probs_to_combinations(position_probs)
                acc = self._calculate_positional_accuracy(predicted, batch_y)
                correct_predictions += acc * batch_x.size(0)
                total_predictions += batch_x.size(0)
        
        avg_loss = total_loss / len(val_loader)
        avg_acc = correct_predictions / total_predictions
        
        return avg_loss, avg_acc
    
    def _calculate_loss(self, position_probs: torch.Tensor, targets: torch.Tensor, confidence: torch.Tensor) -> torch.Tensor:
        """Calcula pérdida combinada"""
        batch_size = targets.size(0)
        
        # Pérdida de clasificación por posición
        classification_loss = 0.0
        for pos in range(6):
            target_pos = targets[:, pos] - 1  # Ajustar para 0-indexing
            pos_loss = nn.CrossEntropyLoss()(position_probs[:, pos, :], target_pos)
            classification_loss += pos_loss
        
        classification_loss /= 6  # Promedio por posición
        
        # Pérdida de confianza (regularización)
        confidence_loss = torch.mean((confidence - 0.5) ** 2) * 0.1
        
        # Pérdida de diversidad (penalizar predicciones idénticas)
        diversity_loss = 0.0
        for i in range(5):
            for j in range(i + 1, 6):
                similarity = torch.sum(position_probs[:, i, :] * position_probs[:, j, :], dim=1)
                diversity_loss += torch.mean(similarity)
        
        diversity_loss = diversity_loss / 15 * 0.05  # Normalizar y peso pequeño
        
        total_loss = classification_loss + confidence_loss + diversity_loss
        
        return total_loss
    
    def _probs_to_combinations(self, position_probs: torch.Tensor) -> torch.Tensor:
        """Convierte probabilidades a combinaciones"""
        batch_size = position_probs.size(0)
        combinations = torch.zeros(batch_size, 6, dtype=torch.long)
        
        for b in range(batch_size):
            used_numbers = set()
            for pos in range(6):
                probs = position_probs[b, pos, :].cpu().numpy()
                
                # Muestreo ponderado evitando repeticiones
                for _ in range(40):  # Máximo 40 intentos
                    number = np.random.choice(40, p=probs) + 1
                    if number not in used_numbers:
                        combinations[b, pos] = number
                        used_numbers.add(number)
                        break
                else:
                    # Fallback: primer número disponible
                    for num in range(1, 41):
                        if num not in used_numbers:
                            combinations[b, pos] = num
                            used_numbers.add(num)
                            break
        
        return combinations
    
    def _calculate_positional_accuracy(self, predicted: torch.Tensor, targets: torch.Tensor) -> float:
        """Calcula accuracy posicional"""
        # Accuracy por posición exacta
        exact_matches = (predicted == targets).float()
        positional_acc = torch.mean(exact_matches)
        
        return positional_acc.item()
    
    def predict(self, sequence: List[List[int]], num_predictions: int = 5) -> List[Dict[str, Any]]:
        """Genera predicciones"""
        if not self.is_trained:
            logger.warning("⚠️ Modelo no entrenado, usando predicción aleatoria")
            return self._random_predictions(num_predictions)
        
        if len(sequence) < self.sequence_length:
            logger.warning(f"⚠️ Secuencia muy corta ({len(sequence)}), necesito {self.sequence_length}")
            return self._random_predictions(num_predictions)
        
        try:
            self.model.eval()
            predictions = []
            
            with torch.no_grad():
                # Usar últimas combinaciones como entrada
                input_seq = sequence[-self.sequence_length:]
                input_tensor = torch.LongTensor([input_seq]).to(self.device)
                
                for _ in range(num_predictions):
                    outputs = self.model(input_tensor)
                    position_probs = outputs['position_probabilities']
                    confidence = outputs['confidence']
                    attention_weights = outputs['attention_weights']
                    
                    # Generar combinación
                    combination = self._generate_combination_from_probs(position_probs[0])
                    
                    prediction = {
                        'combination': combination,
                        'confidence': confidence[0].item(),
                        'source': 'lstm_v2',
                        'model_type': 'advanced_lstm',
                        'timestamp': datetime.now().isoformat(),
                        'attention_weights': attention_weights.cpu().numpy().tolist(),
                        'position_confidences': [
                            torch.max(position_probs[0, pos, :]).item() 
                            for pos in range(6)
                        ]
                    }
                    
                    predictions.append(prediction)
                    
                    # Actualizar secuencia para próxima predicción
                    new_seq = input_seq[1:] + [combination]
                    input_tensor = torch.LongTensor([new_seq]).to(self.device)
            
            logger.info(f"🎯 Generadas {len(predictions)} predicciones LSTM v2")
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Error en predicción: {e}")
            return self._random_predictions(num_predictions)
    
    def _generate_combination_from_probs(self, position_probs: torch.Tensor) -> List[int]:
        """Genera combinación desde probabilidades"""
        combination = []
        used_numbers = set()
        
        for pos in range(6):
            probs = position_probs[pos, :].cpu().numpy()
            
            # Muestreo ponderado
            attempts = 0
            while attempts < 40:
                number = np.random.choice(40, p=probs) + 1
                if number not in used_numbers:
                    combination.append(number)
                    used_numbers.add(number)
                    break
                attempts += 1
            else:
                # Fallback
                for num in range(1, 41):
                    if num not in used_numbers:
                        combination.append(num)
                        used_numbers.add(num)
                        break
        
        return sorted(combination)
    
    def _random_predictions(self, num_predictions: int) -> List[Dict[str, Any]]:
        """Genera predicciones aleatorias como fallback"""
        predictions = []
        
        for _ in range(num_predictions):
            combination = sorted(np.random.choice(range(1, 41), 6, replace=False).tolist())
            
            prediction = {
                'combination': combination,
                'confidence': 0.5,
                'source': 'lstm_v2_fallback',
                'model_type': 'random_fallback',
                'timestamp': datetime.now().isoformat()
            }
            
            predictions.append(prediction)
        
        return predictions
    
    def save_model(self, filepath: str):
        """Guarda el modelo"""
        try:
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'scheduler_state_dict': self.scheduler.state_dict(),
                'training_history': self.training_history,
                'hyperparameters': {
                    'sequence_length': self.sequence_length,
                    'hidden_size': self.hidden_size,
                    'num_layers': self.num_layers,
                    'dropout': self.dropout,
                    'learning_rate': self.learning_rate,
                    'batch_size': self.batch_size
                },
                'is_trained': self.is_trained,
                'best_model_state': self.best_model_state
            }, filepath)
            
            logger.info(f"💾 Modelo LSTM v2 guardado en {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando modelo: {e}")
    
    def load_model(self, filepath: str):
        """Carga modelo pre-entrenado"""
        try:
            checkpoint = torch.load(filepath, map_location=self.device)
            
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
            self.training_history = checkpoint['training_history']
            self.is_trained = checkpoint['is_trained']
            self.best_model_state = checkpoint.get('best_model_state')
            
            logger.info(f"📂 Modelo LSTM v2 cargado desde {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Error cargando modelo: {e}")
    
    def get_training_summary(self) -> Dict[str, Any]:
        """Obtiene resumen del entrenamiento"""
        if not self.training_history['epochs']:
            return {"error": "No hay historial de entrenamiento"}
        
        return {
            "epochs_trained": len(self.training_history['epochs']),
            "best_val_loss": min(self.training_history['val_loss']),
            "best_val_acc": max(self.training_history['val_acc']),
            "final_train_loss": self.training_history['train_loss'][-1],
            "final_val_loss": self.training_history['val_loss'][-1],
            "is_trained": self.is_trained,
            "model_parameters": sum(p.numel() for p in self.model.parameters()),
            "device": str(self.device),
            "recent_history": {
                "epochs": self.training_history['epochs'][-10:],
                "train_loss": self.training_history['train_loss'][-10:],
                "val_loss": self.training_history['val_loss'][-10:],
                "train_acc": self.training_history['train_acc'][-10:],
                "val_acc": self.training_history['val_acc'][-10:]
            }
        }

# Funciones de utilidad
def create_lstm_predictor_v2(sequence_length: int = 20, 
                            hidden_size: int = 256,
                            num_layers: int = 3) -> LSTMPredictorV2:
    """Crea un predictor LSTM v2"""
    return LSTMPredictorV2(
        sequence_length=sequence_length,
        hidden_size=hidden_size,
        num_layers=num_layers
    )

def train_and_evaluate(predictor: LSTMPredictorV2, 
                      historical_data: List[List[int]],
                      epochs: int = 20) -> Dict[str, Any]:
    """Entrena y evalúa el predictor"""
    results = predictor.train(historical_data, epochs=epochs)
    summary = predictor.get_training_summary()
    
    return {**results, **summary}

if __name__ == "__main__":
    # Demo del LSTM Predictor v2
    print("🧠 Demo LSTM Predictor v2")
    
    # Crear predictor
    predictor = create_lstm_predictor_v2()
    
    # Datos de ejemplo (más datos para entrenamiento efectivo)
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
        [2, 14, 18, 25, 28, 37], [4, 13, 19, 23, 34, 38],
        [6, 9, 21, 27, 31, 39], [7, 12, 16, 24, 33, 35],
        [8, 11, 20, 26, 29, 40]
    ] * 3  # Replicar para tener más datos
    
    print(f"📊 Entrenando con {len(sample_data)} combinaciones...")
    
    try:
        # Entrenar
        results = train_and_evaluate(predictor, sample_data, epochs=20)
        
        print(f"✅ Entrenamiento completado:")
        print(f"   Épocas: {results['epochs_trained']}")
        print(f"   Mejor Val Loss: {results['best_val_loss']:.4f}")
        print(f"   Mejor Val Acc: {results['best_val_acc']:.3f}")
        
        # Generar predicciones
        print(f"\n🎯 Generando predicciones...")
        predictions = predictor.predict(sample_data[-20:], num_predictions=3)
        
        for i, pred in enumerate(predictions, 1):
            combination = pred['combination']
            confidence = pred['confidence']
            print(f"   {i}. {' - '.join(map(str, combination))} (Confianza: {confidence:.1%})")
            
    except Exception as e:
        print(f"❌ Error en demo: {e}")
        
        # Mostrar predicciones fallback
        predictions = predictor.predict(sample_data, num_predictions=3)
        print(f"🔄 Predicciones de fallback:")
        for i, pred in enumerate(predictions, 1):
            combination = pred['combination']
            print(f"   {i}. {' - '.join(map(str, combination))}")
