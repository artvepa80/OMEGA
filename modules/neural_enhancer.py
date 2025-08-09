# OMEGA_PRO_AI_v10.1/modules/neural_enhancer.py
"""
Potenciador de Redes Neuronales para OMEGA PRO AI
Integra análisis de 200 sorteos con redes neuronales avanzadas
"""

import logging
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from typing import List, Dict, Any, Tuple, Optional
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class EnhancedNeuralPredictor(nn.Module):
    """Red neuronal mejorada con atención y memoria LSTM"""
    
    def __init__(self, input_size: int = 60, hidden_size: int = 128, num_layers: int = 3):
        super().__init__()
        
        # LSTM bidireccional para capturar patrones temporales
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=0.3
        )
        
        # Mecanismo de atención
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size * 2,  # bidirectional
            num_heads=8,
            dropout=0.2
        )
        
        # Capas densas con normalización
        self.fc_layers = nn.Sequential(
            nn.Linear(hidden_size * 2, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.4),
            
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.3),
            
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.2),
            
            # Salida: 40 probabilidades para números 1-40
            nn.Linear(64, 40),
            nn.Softmax(dim=1)
        )
        
        # Inicialización de pesos
        self._init_weights()
    
    def _init_weights(self):
        """Inicialización optimizada de pesos"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.kaiming_normal_(module.weight, mode='fan_out', nonlinearity='relu')
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)
            elif isinstance(module, nn.LSTM):
                for name, param in module.named_parameters():
                    if 'weight' in name:
                        nn.init.orthogonal_(param)
                    elif 'bias' in name:
                        nn.init.constant_(param, 0)
    
    def forward(self, x):
        # LSTM processing
        lstm_out, (hidden, cell) = self.lstm(x)
        
        # Attention mechanism
        # Reshape for attention: (seq_len, batch, feature)
        lstm_out = lstm_out.transpose(0, 1)
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        
        # Use the last attention output
        final_output = attn_out[-1]  # (batch, feature)
        
        # Dense layers
        predictions = self.fc_layers(final_output)
        
        return predictions

class NeuralEnhancer:
    """Potenciador neuronal que integra análisis histórico"""
    
    def __init__(self, device: str = None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.training_history = []
        
        logger.info(f"🧠 NeuralEnhancer inicializado en device: {self.device}")
    
    def prepare_training_data(self, historial_df: pd.DataFrame, lookback: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """Prepara datos de entrenamiento con ventana deslizante"""
        try:
            # Obtener columnas de bolillas
            numeric_cols = [col for col in historial_df.columns 
                          if 'bolilla' in col.lower() or col.startswith('Bolilla')]
            
            if len(numeric_cols) < 6:
                raise ValueError("Insuficientes columnas de bolillas")
            
            data = historial_df[numeric_cols[:6]].values.astype(float)
            
            # Crear ventanas deslizantes
            X, y = [], []
            
            for i in range(lookback, len(data)):
                # Ventana de lookback sorteos anteriores
                window = data[i-lookback:i]
                # Próximo sorteo como target
                target = data[i]
                
                # Flatten window para crear features
                window_flat = window.flatten()
                
                # Crear vector de probabilidades target (one-hot style)
                target_probs = np.zeros(40)
                for num in target:
                    if 1 <= num <= 40:
                        target_probs[int(num-1)] = 1.0 / 6  # Distribuir probabilidad
                
                X.append(window_flat)
                y.append(target_probs)
            
            X = np.array(X)
            y = np.array(y)
            
            # Normalizar features
            X = self.scaler.fit_transform(X)
            
            logger.info(f"🔢 Datos preparados: {X.shape[0]} muestras, {X.shape[1]} features")
            return X, y
            
        except Exception as e:
            logger.error(f"❌ Error preparando datos: {e}")
            raise
    
    def train_enhanced_model(self, historial_df: pd.DataFrame, epochs: int = 100, learning_rate: float = 0.001, batch_size: int | None = None):
        """Entrena el modelo neuronal mejorado"""
        try:
            logger.info("🚀 Iniciando entrenamiento del modelo neuronal mejorado...")
            
            # Preparar datos
            X, y = self.prepare_training_data(historial_df)
            
            if len(X) < 50:
                logger.warning("⚠️ Pocos datos para entrenamiento, usando configuración simplificada")
                epochs = min(epochs, 50)
            
            # Split datos
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=False
            )
            
            # Reshape para LSTM (batch, seq_len, features)
            X_train = X_train.reshape(X_train.shape[0], 1, X_train.shape[1])
            X_val = X_val.reshape(X_val.shape[0], 1, X_val.shape[1])
            
            # Convertir a tensores
            X_train = torch.FloatTensor(X_train).to(self.device)
            y_train = torch.FloatTensor(y_train).to(self.device)
            X_val = torch.FloatTensor(X_val).to(self.device)
            y_val = torch.FloatTensor(y_val).to(self.device)
            
            # Inicializar modelo
            input_size = X_train.shape[2]
            self.model = EnhancedNeuralPredictor(input_size=input_size).to(self.device)
            
            # Optimizador y loss
            optimizer = optim.AdamW(self.model.parameters(), lr=learning_rate, weight_decay=1e-5)
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)
            criterion = nn.MSELoss()
            
            # Entrenamiento (batch_size opcional; si no se usa, se procesa todo el batch junto)
            best_val_loss = float('inf')
            patience_counter = 0
            
            for epoch in range(epochs):
                # Training (sin minibatching real para simplicidad; batch_size aceptado pero no obligatorio)
                self.model.train()
                optimizer.zero_grad()
                
                train_pred = self.model(X_train)
                train_loss = criterion(train_pred, y_train)
                
                train_loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()
                
                # Validation
                self.model.eval()
                with torch.no_grad():
                    val_pred = self.model(X_val)
                    val_loss = criterion(val_pred, y_val)
                
                scheduler.step(val_loss)
                
                # Early stopping
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                if patience_counter >= 15:
                    logger.info(f"🛑 Early stopping en época {epoch}")
                    break
                
                # Log progreso
                if epoch % 20 == 0 or epoch == epochs - 1:
                    logger.info(f"Época {epoch}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")
                
                self.training_history.append({
                    'epoch': epoch,
                    'train_loss': train_loss.item(),
                    'val_loss': val_loss.item()
                })
            
            self.is_trained = True
            logger.info(f"✅ Entrenamiento completado. Mejor val_loss: {best_val_loss:.4f}")
            
        except Exception as e:
            logger.error(f"❌ Error en entrenamiento: {e}")
            self.is_trained = False
            raise
    
    def predict_combinations(self, historial_df: pd.DataFrame, num_combinations: int = 5, focus_high_numbers: bool = True) -> List[Dict[str, Any]]:
        """Genera predicciones usando el modelo entrenado con enfoque optimizado en números altos"""
        if not self.is_trained or self.model is None:
            logger.warning("⚠️ Modelo no entrenado, usando predicciones aleatorias")
            return self._generate_random_predictions(num_combinations)
        
        try:
            # Preparar último contexto
            numeric_cols = [col for col in historial_df.columns 
                          if 'bolilla' in col.lower() or col.startswith('Bolilla')]
            
            last_data = historial_df[numeric_cols[:6]].tail(10).values.astype(float)
            
            # Normalizar
            last_flat = last_data.flatten().reshape(1, -1)
            last_normalized = self.scaler.transform(last_flat)
            
            # Reshape para modelo
            last_input = last_normalized.reshape(1, 1, -1)
            last_tensor = torch.FloatTensor(last_input).to(self.device)
            
            # Predicción
            self.model.eval()
            with torch.no_grad():
                predictions = self.model(last_tensor)
                probabilities = predictions.cpu().numpy()[0]
            
            # Generar combinaciones basadas en probabilidades con optimización
            combinations = []
            for i in range(num_combinations):
                # Sampling probabilístico con temperatura y boost para números altos
                temperature = 0.8 + (i * 0.1)  # Aumentar temperatura para variedad
                adjusted_probs = np.power(probabilities, 1/temperature)
                
                # MEJORA: Boost para números altos (30-40) basado en análisis del 5/08/2025
                if focus_high_numbers:
                    high_numbers_boost = np.zeros(40)
                    high_numbers_boost[29:40] = 0.3  # Boost del 30% para números 30-40
                    high_numbers_boost[13] = 0.2     # Boost especial para 14 (único bajo que salió)
                    adjusted_probs = adjusted_probs + high_numbers_boost
                
                adjusted_probs = adjusted_probs / np.sum(adjusted_probs)
                
                # Seleccionar 6 números únicos
                selected_indices = np.random.choice(
                    40, size=6, replace=False, p=adjusted_probs
                )
                
                # Convertir a números (1-40)
                combination = sorted([int(idx + 1) for idx in selected_indices])
                
                # Calcular confianza
                confidence = np.mean([probabilities[idx] for idx in selected_indices])
                
                combinations.append({
                    'combination': combination,
                    'confidence': float(confidence),
                    'source': 'neural_enhanced',
                    'temperature': temperature,
                    'score': 0.5 + (confidence * 0.5)  # Score base + bonus de confianza
                })
            
            logger.info(f"🧠 Generadas {len(combinations)} predicciones neuronales")
            return combinations
            
        except Exception as e:
            logger.error(f"❌ Error en predicción: {e}")
            return self._generate_random_predictions(num_combinations)
    
    def _generate_random_predictions(self, num_combinations: int) -> List[Dict[str, Any]]:
        """Fallback: genera predicciones aleatorias"""
        combinations = []
        for i in range(num_combinations):
            combination = sorted(np.random.choice(range(1, 41), size=6, replace=False))
            combinations.append({
                'combination': combination.tolist(),
                'confidence': 0.5,
                'source': 'neural_fallback',
                'score': 0.5
            })
        return combinations
    
    def get_training_summary(self) -> Dict[str, Any]:
        """Retorna resumen del entrenamiento"""
        if not self.training_history:
            return {'trained': False}
        
        best_epoch = min(self.training_history, key=lambda x: x['val_loss'])
        final_epoch = self.training_history[-1]
        
        return {
            'trained': self.is_trained,
            'total_epochs': len(self.training_history),
            'best_epoch': best_epoch['epoch'],
            'best_val_loss': best_epoch['val_loss'],
            'final_train_loss': final_epoch['train_loss'],
            'final_val_loss': final_epoch['val_loss'],
            'device': self.device
        }

def enhance_neural_predictions(historial_df: pd.DataFrame, num_combinations: int = 5) -> Dict[str, Any]:
    """Función principal para predicciones neuronales mejoradas"""
    try:
        enhancer = NeuralEnhancer()
        
        # Entrenar modelo
        enhancer.train_enhanced_model(historial_df, epochs=80)
        
        # Generar predicciones
        predictions = enhancer.predict_combinations(historial_df, num_combinations)
        
        # Resumen
        summary = enhancer.get_training_summary()
        
        return {
            'predictions': predictions,
            'training_summary': summary,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"❌ Error en predicciones neuronales: {e}")
        return {
            'predictions': [],
            'training_summary': {'trained': False, 'error': str(e)},
            'success': False
        }
