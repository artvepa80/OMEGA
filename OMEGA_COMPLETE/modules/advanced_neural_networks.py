#!/usr/bin/env python3
"""
Advanced Neural Networks Module for OMEGA PRO AI
Implementa redes neuronales profundas y avanzadas para predicción
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os
from typing import List, Dict, Any, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AttentionMechanism(nn.Module):
    """Mecanismo de atención para capturar patrones complejos"""
    
    def __init__(self, input_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        
        self.query = nn.Linear(input_dim, hidden_dim)
        self.key = nn.Linear(input_dim, hidden_dim)
        self.value = nn.Linear(input_dim, hidden_dim)
        self.softmax = nn.Softmax(dim=-1)
        
    def forward(self, x):
        batch_size, seq_len, _ = x.shape
        
        Q = self.query(x)  # [batch, seq, hidden]
        K = self.key(x)    # [batch, seq, hidden]
        V = self.value(x)  # [batch, seq, hidden]
        
        # Attention scores
        scores = torch.matmul(Q, K.transpose(-2, -1)) / np.sqrt(self.hidden_dim)
        attention_weights = self.softmax(scores)
        
        # Apply attention
        attended = torch.matmul(attention_weights, V)
        return attended, attention_weights

class OmegaAdvancedNetwork(nn.Module):
    """Red neuronal avanzada con múltiples capas de atención y memoria"""
    
    def __init__(self, input_size: int = 6, hidden_sizes: List[int] = [256, 512, 256, 128]):
        super().__init__()
        self.input_size = input_size
        self.hidden_sizes = hidden_sizes
        
        # Capas de embedding
        self.embedding = nn.Embedding(41, 64)  # 40 números + padding
        
        # Capas LSTM bidireccionales
        self.lstm = nn.LSTM(
            input_size=64,
            hidden_size=256,
            num_layers=3,
            batch_first=True,
            bidirectional=True,
            dropout=0.3
        )
        
        # Mecanismo de atención
        self.attention = AttentionMechanism(512, 256)  # 256*2 por bidireccional
        
        # Capas fully connected con residual connections
        layers = []
        prev_size = 256  # output del attention
        
        for hidden_size in hidden_sizes:
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.BatchNorm1d(hidden_size),
                nn.ReLU(),
                nn.Dropout(0.2)
            ])
            prev_size = hidden_size
        
        self.fc_layers = nn.ModuleList(layers)
        
        # Capas de salida múltiple
        self.combination_head = nn.Linear(hidden_sizes[-1], 6 * 40)  # 6 posiciones x 40 números
        self.probability_head = nn.Linear(hidden_sizes[-1], 1)
        self.confidence_head = nn.Linear(hidden_sizes[-1], 1)
        
        # Capa de meta-learning
        self.meta_network = nn.Sequential(
            nn.Linear(hidden_sizes[-1], 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        batch_size = x.shape[0]
        
        # Embedding
        embedded = self.embedding(x)  # [batch, seq, embed_dim]
        
        # LSTM
        lstm_out, (hidden, cell) = self.lstm(embedded)  # [batch, seq, hidden*2]
        
        # Attention
        attended, attention_weights = self.attention(lstm_out)
        
        # Global pooling (promedio ponderado por atención)
        pooled = torch.mean(attended, dim=1)  # [batch, hidden]
        
        # Fully connected layers con residual connections
        x = pooled
        residual = x
        
        for i in range(0, len(self.fc_layers), 4):
            if i + 3 < len(self.fc_layers):
                x = self.fc_layers[i](x)      # Linear
                x = self.fc_layers[i+1](x)    # BatchNorm
                x = self.fc_layers[i+2](x)    # ReLU
                x = self.fc_layers[i+3](x)    # Dropout
                
                # Residual connection si las dimensiones coinciden
                if x.shape == residual.shape:
                    x = x + residual
                residual = x
        
        # Múltiples cabezas de salida
        combination_logits = self.combination_head(x).reshape(batch_size, 6, 40)
        probability = torch.sigmoid(self.probability_head(x))
        confidence = torch.sigmoid(self.confidence_head(x))
        meta_features = self.meta_network(x)
        
        return {
            'combination_logits': combination_logits,
            'probability': probability,
            'confidence': confidence,
            'meta_features': meta_features,
            'attention_weights': attention_weights
        }

class ReinforcementLearningAgent:
    """Agente de aprendizaje por refuerzo para auto-optimización"""
    
    def __init__(self, state_dim: int = 100, action_dim: int = 50):
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Q-Network para toma de decisiones
        self.q_network = nn.Sequential(
            nn.Linear(state_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, action_dim)
        )
        
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=0.001)
        self.epsilon = 0.1  # Exploración
        self.gamma = 0.95   # Factor de descuento
        
        # Memoria de experiencias
        self.memory = []
        self.memory_size = 10000
        
    def select_action(self, state):
        """Selecciona acción usando epsilon-greedy"""
        if np.random.random() < self.epsilon:
            return np.random.randint(0, self.action_dim)
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            q_values = self.q_network(state_tensor)
            return q_values.argmax().item()
    
    def store_experience(self, state, action, reward, next_state, done):
        """Almacena experiencia en memoria"""
        experience = (state, action, reward, next_state, done)
        
        if len(self.memory) >= self.memory_size:
            self.memory.pop(0)
        
        self.memory.append(experience)
    
    def learn(self, batch_size: int = 32):
        """Entrena el agente con experiencias aleatorias"""
        if len(self.memory) < batch_size:
            return
        
        # Muestreo aleatorio de experiencias
        batch_indices = np.random.choice(len(self.memory), batch_size, replace=False)
        batch = [self.memory[i] for i in batch_indices]
        
        states = torch.FloatTensor([exp[0] for exp in batch])
        actions = torch.LongTensor([exp[1] for exp in batch])
        rewards = torch.FloatTensor([exp[2] for exp in batch])
        next_states = torch.FloatTensor([exp[3] for exp in batch])
        dones = torch.BoolTensor([exp[4] for exp in batch])
        
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        with torch.no_grad():
            next_q_values = self.q_network(next_states).max(1)[0]
            target_q_values = rewards + (self.gamma * next_q_values * ~dones)
        
        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Decaimiento de epsilon
        self.epsilon = max(0.01, self.epsilon * 0.995)

class AdaptiveLearningSystem:
    """Sistema de aprendizaje adaptativo continuo"""
    
    def __init__(self):
        self.model = OmegaAdvancedNetwork()
        self.rl_agent = ReinforcementLearningAgent()
        self.optimizer = optim.AdamW(self.model.parameters(), lr=0.001, weight_decay=0.01)
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(self.optimizer, T_max=100)
        
        # Métricas de rendimiento
        self.performance_history = []
        self.adaptation_rate = 0.1
        
        # Sistema de meta-aprendizaje
        self.meta_optimizer = optim.Adam(self.model.meta_network.parameters(), lr=0.0001)
        
    def adapt_to_new_data(self, new_data: List[List[int]], results: List[bool] = None):
        """Adapta el modelo a nuevos datos en tiempo real"""
        logger.info("🔄 Iniciando adaptación a nuevos datos...")
        
        if not new_data:
            logger.warning("⚠️ No hay nuevos datos para adaptación")
            return
        
        # Validar formato de datos
        try:
            for combo in new_data:
                if len(combo) != 6:
                    raise ValueError(f"Combinación debe tener 6 números, recibida: {len(combo)}")
                if not all(1 <= num <= 40 for num in combo):
                    raise ValueError(f"Números deben estar entre 1-40, recibida: {combo}")
        except Exception as e:
            logger.error(f"❌ Error en validación de datos: {e}")
            return
        
        # Convertir datos a tensores
        X = torch.LongTensor(new_data)
        
        if results is not None:
            y = torch.FloatTensor(results)
            
            # Entrenamiento supervisado
            self.model.train()
            outputs = self.model(X)
            
            # Pérdida combinada
            prob_loss = nn.BCELoss()(outputs['probability'].squeeze(), y)
            confidence_loss = nn.MSELoss()(outputs['confidence'].squeeze(), y)
            
            total_loss = prob_loss + 0.1 * confidence_loss
            
            self.optimizer.zero_grad()
            total_loss.backward()
            self.optimizer.step()
            
            logger.info(f"📈 Modelo adaptado - Pérdida: {total_loss.item():.4f}")
        
        # Meta-aprendizaje: aprender a aprender
        self._meta_learning_update(X)
        
    def _meta_learning_update(self, data):
        """Actualización de meta-aprendizaje"""
        with torch.no_grad():
            outputs = self.model(data)
            meta_features = outputs['meta_features']
            
            # Calcular métricas de diversidad y complejidad
            diversity = torch.std(meta_features, dim=0).mean()
            complexity = torch.norm(meta_features, dim=1).mean()
            
            # Objetivo: maximizar diversidad y controlar complejidad
            meta_target = diversity - 0.1 * complexity
            
        # Actualizar meta-network
        self.meta_optimizer.zero_grad()
        current_meta = self.model.meta_network(outputs['combination_logits'].detach().mean(dim=(1,2)))
        meta_loss = -meta_target  # Maximizar
        meta_loss.backward()
        self.meta_optimizer.step()
    
    def generate_intelligent_combinations(self, num_combinations: int = 10) -> List[Dict[str, Any]]:
        """Genera combinaciones usando IA avanzada"""
        logger.info(f"🤖 Generando {num_combinations} combinaciones con IA avanzada...")
        
        self.model.eval()
        combinations = []
        
        for i in range(num_combinations):
            # Generar entrada aleatoria como semilla
            seed_input = torch.randint(1, 41, (1, 6))
            
            with torch.no_grad():
                outputs = self.model(seed_input)
                
                # Extraer combinación más probable
                combination_probs = torch.softmax(outputs['combination_logits'], dim=-1)
                combination = []
                
                for pos in range(6):
                    # Muestreo ponderado por probabilidades
                    probs = combination_probs[0, pos].numpy()
                    
                    # Normalizar probabilidades para evitar NaN
                    probs = probs / (probs.sum() + 1e-8)
                    
                    number = np.random.choice(40, p=probs) + 1
                    
                    # Evitar duplicados con límite de intentos
                    attempts = 0
                    while number in combination and attempts < 100:
                        number = np.random.choice(40, p=probs) + 1
                        attempts += 1
                    
                    # Si no se pudo evitar duplicado, usar número secuencial disponible
                    if number in combination:
                        for num in range(1, 41):
                            if num not in combination:
                                number = num
                                break
                    
                    combination.append(number)
                
                combination.sort()
                
                result = {
                    'combination': combination,
                    'probability': outputs['probability'].item(),
                    'confidence': outputs['confidence'].item(),
                    'meta_score': outputs['meta_features'].mean().item(),
                    'attention_weights': outputs['attention_weights'].cpu().numpy(),
                    'source': 'advanced_ai',
                    'timestamp': datetime.now().isoformat()
                }
                
                combinations.append(result)
                logger.info(f"🎯 Generada: {combination} (Conf: {result['confidence']:.3f})")
        
        return combinations
    
    def analyze_pattern_intelligence(self, historical_data: List[List[int]]) -> Dict[str, Any]:
        """Análisis inteligente de patrones usando IA"""
        logger.info("🔍 Analizando patrones con IA avanzada...")
        
        if not historical_data:
            return {}
        
        X = torch.LongTensor(historical_data)
        
        with torch.no_grad():
            outputs = self.model(X)
            attention_weights = outputs['attention_weights'].cpu().numpy()
            meta_features = outputs['meta_features'].cpu().numpy()
        
        analysis = {
            'pattern_complexity': np.std(meta_features, axis=0).mean(),
            'attention_focus': attention_weights.mean(axis=0),
            'sequence_importance': np.var(attention_weights, axis=1).mean(),
            'ai_confidence': outputs['confidence'].mean().item(),
            'predicted_trend': 'ascending' if meta_features.mean() > 0.5 else 'descending',
            'intelligence_score': outputs['meta_features'].mean().item(),
            'recommendations': self._generate_recommendations(meta_features)
        }
        
        logger.info(f"📊 Análisis completado - Inteligencia: {analysis['intelligence_score']:.3f}")
        return analysis
    
    def _generate_recommendations(self, meta_features: np.ndarray) -> List[str]:
        """Genera recomendaciones inteligentes basadas en el análisis"""
        recommendations = []
        
        complexity = np.std(meta_features, axis=0).mean()
        avg_feature = meta_features.mean()
        
        if complexity > 0.7:
            recommendations.append("Patrones complejos detectados - considera estrategias diversificadas")
        
        if avg_feature > 0.6:
            recommendations.append("Tendencia al alza detectada - enfócate en números altos")
        elif avg_feature < 0.4:
            recommendations.append("Tendencia a la baja detectada - considera números bajos")
        
        if np.var(meta_features) > 0.5:
            recommendations.append("Alta variabilidad - usa estrategias adaptativas")
        
        return recommendations
    
    def save_model(self, model_path: str = "models/advanced_ai_model.pt"):
        """Guarda el modelo completo"""
        try:
            import os
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            checkpoint = {
                'model_state_dict': self.model.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'scheduler_state_dict': self.scheduler.state_dict(),
                'rl_agent_state_dict': self.rl_agent.q_network.state_dict(),
                'performance_history': self.performance_history,
                'adaptation_rate': self.adaptation_rate
            }
            
            torch.save(checkpoint, model_path)
            logger.info(f"✅ Modelo guardado en: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando modelo: {e}")
            return False
    
    def load_model(self, model_path: str = "models/advanced_ai_model.pt"):
        """Carga el modelo completo"""
        try:
            if not os.path.exists(model_path):
                logger.warning(f"⚠️ Archivo de modelo no encontrado: {model_path}")
                return False
            
            checkpoint = torch.load(model_path, map_location='cpu')
            
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
            self.rl_agent.q_network.load_state_dict(checkpoint['rl_agent_state_dict'])
            self.performance_history = checkpoint.get('performance_history', [])
            self.adaptation_rate = checkpoint.get('adaptation_rate', 0.1)
            
            logger.info(f"✅ Modelo cargado desde: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cargando modelo: {e}")
            return False

# Funciones de utilidad
def create_advanced_ai_system() -> AdaptiveLearningSystem:
    """Crea y configura el sistema de IA avanzado"""
    logger.info("🚀 Inicializando sistema de IA avanzado OMEGA PRO...")
    
    system = AdaptiveLearningSystem()
    
    # Configuración inicial
    logger.info("✅ Sistema de IA avanzado inicializado correctamente")
    return system

def train_with_historical_data(system: AdaptiveLearningSystem, historical_data: List[List[int]]):
    """Entrena el sistema con datos históricos"""
    logger.info("📚 Entrenando sistema con datos históricos...")
    
    if len(historical_data) < 10:
        logger.warning("⚠️ Pocos datos históricos para entrenamiento")
        return
    
    # Dividir datos en lotes para entrenamiento incremental
    batch_size = min(32, len(historical_data) // 4)
    
    for i in range(0, len(historical_data), batch_size):
        batch = historical_data[i:i+batch_size]
        system.adapt_to_new_data(batch)
    
    logger.info("✅ Entrenamiento con datos históricos completado")

if __name__ == "__main__":
    # Ejemplo de uso
    system = create_advanced_ai_system()
    
    # Datos de ejemplo
    sample_data = [
        [1, 15, 23, 31, 35, 40],
        [3, 12, 18, 27, 33, 39],
        [5, 14, 22, 28, 34, 38]
    ]
    
    # Entrenar sistema
    train_with_historical_data(system, sample_data)
    
    # Generar combinaciones inteligentes
    intelligent_combos = system.generate_intelligent_combinations(5)
    
    # Análizar patrones
    pattern_analysis = system.analyze_pattern_intelligence(sample_data)
    
    print("🤖 Sistema de IA Avanzado OMEGA PRO operativo!")
