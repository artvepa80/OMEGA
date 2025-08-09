#!/usr/bin/env python3
"""
Reinforcement Learning Trainer for OMEGA PRO AI
Sistema de aprendizaje por refuerzo para optimización a largo plazo
"""

import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from collections import deque, namedtuple
import random
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

# Estructura para experiencias
Experience = namedtuple('Experience', ['state', 'action', 'reward', 'next_state', 'done'])

class ActionType(Enum):
    """Tipos de acciones que puede tomar el agente"""
    INCREASE_MODEL_WEIGHT = 0
    DECREASE_MODEL_WEIGHT = 1
    CHANGE_STRATEGY = 2
    ADJUST_THRESHOLD = 3
    COMBINE_MODELS = 4

@dataclass
class RLState:
    """Estado del entorno para RL"""
    model_performances: List[float]  # Performance reciente de cada modelo
    context_features: List[float]    # Features del contexto actual
    recent_rewards: List[float]      # Recompensas recientes
    current_weights: List[float]     # Pesos actuales de modelos
    time_features: List[float]       # Features temporales

@dataclass
class RLAction:
    """Acción del agente RL"""
    action_type: ActionType
    model_index: int
    adjustment_value: float

class DQNNetwork(nn.Module):
    """Red neuronal profunda para Q-Learning"""
    
    def __init__(self, state_size: int, action_size: int, hidden_sizes: List[int] = [256, 128, 64]):
        super(DQNNetwork, self).__init__()
        
        self.state_size = state_size
        self.action_size = action_size
        
        # Capas de entrada
        layers = []
        prev_size = state_size
        
        for hidden_size in hidden_sizes:
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.BatchNorm1d(hidden_size)
            ])
            prev_size = hidden_size
        
        # Capa de salida
        layers.append(nn.Linear(prev_size, action_size))
        
        self.network = nn.Sequential(*layers)
        
        # Inicialización Xavier
        for layer in self.network:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight)
    
    def forward(self, state):
        return self.network(state)

class ReplayBuffer:
    """Buffer de replay para almacenar experiencias"""
    
    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)
        self.capacity = capacity
    
    def push(self, experience: Experience):
        self.buffer.append(experience)
    
    def sample(self, batch_size: int) -> List[Experience]:
        return random.sample(self.buffer, min(batch_size, len(self.buffer)))
    
    def __len__(self):
        return len(self.buffer)

class ReinforcementTrainer:
    """Entrenador de aprendizaje por refuerzo para OMEGA PRO AI"""
    
    def __init__(self, 
                 state_size: int = 30,
                 action_size: int = 50,
                 learning_rate: float = 0.001,
                 gamma: float = 0.95,
                 epsilon: float = 1.0,
                 epsilon_decay: float = 0.995,
                 epsilon_min: float = 0.01,
                 memory_size: int = 10000,
                 batch_size: int = 32):
        
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.batch_size = batch_size
        
        # Redes neuronales (Double DQN)
        self.q_network = DQNNetwork(state_size, action_size)
        self.target_network = DQNNetwork(state_size, action_size)
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
        
        # Copiar pesos iniciales
        self.update_target_network()
        
        # Memoria de replay
        self.memory = ReplayBuffer(memory_size)
        
        # Historial de entrenamiento
        self.training_history = {
            'episodes': [],
            'rewards': [],
            'losses': [],
            'epsilon_history': [],
            'q_values': []
        }
        
        # Métricas de performance
        self.episode_count = 0
        self.total_steps = 0
        self.best_reward = -float('inf')
        
        # Configuración de modelos disponibles
        self.model_names = [
            'lstm_v2', 'transformer', 'clustering', 'montecarlo',
            'genetic', 'gboost', 'ensemble_ai'
        ]
        
        logger.info("🎮 Reinforcement Learning Trainer inicializado")
        logger.info(f"   Estado: {state_size}D, Acciones: {action_size}, LR: {learning_rate}")
    
    def state_to_tensor(self, state: RLState) -> torch.Tensor:
        """Convierte estado a tensor de PyTorch"""
        # Concatenar todas las features del estado
        state_vector = (
            state.model_performances +
            state.context_features +
            state.recent_rewards +
            state.current_weights +
            state.time_features
        )
        
        # Padding o truncamiento para tamaño fijo
        if len(state_vector) < self.state_size:
            state_vector.extend([0.0] * (self.state_size - len(state_vector)))
        elif len(state_vector) > self.state_size:
            state_vector = state_vector[:self.state_size]
        
        return torch.FloatTensor(state_vector).unsqueeze(0)
    
    def choose_action(self, state: RLState) -> RLAction:
        """Selecciona acción usando epsilon-greedy"""
        if np.random.random() <= self.epsilon:
            # Exploración: acción aleatoria
            action_type = random.choice(list(ActionType))
            model_index = random.randint(0, len(self.model_names) - 1)
            adjustment_value = np.random.uniform(-0.2, 0.2)
        else:
            # Explotación: mejor acción según Q-network
            state_tensor = self.state_to_tensor(state)
            
            with torch.no_grad():
                q_values = self.q_network(state_tensor)
                action_index = torch.argmax(q_values).item()
            
            # Decodificar acción
            action_type = ActionType(action_index % len(ActionType))
            model_index = (action_index // len(ActionType)) % len(self.model_names)
            
            # Valor de ajuste basado en Q-values
            adjustment_value = (q_values[0][action_index].item() - 0.5) * 0.4
            adjustment_value = np.clip(adjustment_value, -0.2, 0.2)
        
        return RLAction(action_type, model_index, adjustment_value)
    
    def calculate_reward(self, 
                        old_performance: Dict[str, float],
                        new_performance: Dict[str, float],
                        action: RLAction) -> float:
        """Calcula la recompensa basada en mejora de performance"""
        
        # Recompensa base por mejora de accuracy
        old_acc = old_performance.get('accuracy', 0.5)
        new_acc = new_performance.get('accuracy', 0.5)
        accuracy_improvement = new_acc - old_acc
        
        # Recompensa por mejora de F1-score
        old_f1 = old_performance.get('f1_score', 0.5)
        new_f1 = new_performance.get('f1_score', 0.5)
        f1_improvement = new_f1 - old_f1
        
        # Recompensa por consistencia (menor varianza)
        old_std = old_performance.get('std_dev', 0.2)
        new_std = new_performance.get('std_dev', 0.2)
        consistency_improvement = old_std - new_std
        
        # Recompensa combinada
        reward = (
            accuracy_improvement * 10.0 +      # Peso alto para accuracy
            f1_improvement * 8.0 +             # Peso alto para F1
            consistency_improvement * 5.0       # Peso moderado para consistencia
        )
        
        # Bonus por superar thresholds
        if new_acc > 0.8:
            reward += 2.0
        if new_f1 > 0.8:
            reward += 2.0
        
        # Penalización por overfitting (performance muy alta pero inconsistente)
        if new_acc > 0.95 and new_std > 0.3:
            reward -= 3.0
        
        # Penalización por acciones extremas
        if abs(action.adjustment_value) > 0.15:
            reward -= 1.0
        
        # Normalizar reward
        reward = np.clip(reward, -10.0, 10.0)
        
        logger.debug(f"💰 Recompensa calculada: {reward:.3f} (Acc: {accuracy_improvement:.3f}, F1: {f1_improvement:.3f})")
        return reward
    
    def remember(self, state: RLState, action: RLAction, reward: float, 
                next_state: RLState, done: bool):
        """Almacena experiencia en memoria de replay"""
        
        state_tensor = self.state_to_tensor(state).squeeze(0)
        next_state_tensor = self.state_to_tensor(next_state).squeeze(0)
        
        # Codificar acción como índice
        action_index = (action.action_type.value * len(self.model_names) + 
                       action.model_index)
        
        experience = Experience(
            state=state_tensor,
            action=action_index,
            reward=reward,
            next_state=next_state_tensor,
            done=done
        )
        
        self.memory.push(experience)
    
    def replay_learning(self) -> float:
        """Realiza aprendizaje desde memoria de replay"""
        if len(self.memory) < self.batch_size:
            return 0.0
        
        # Muestrear batch de experiencias
        experiences = self.memory.sample(self.batch_size)
        
        # Preparar tensors
        states = torch.stack([exp.state for exp in experiences])
        actions = torch.LongTensor([exp.action for exp in experiences])
        rewards = torch.FloatTensor([exp.reward for exp in experiences])
        next_states = torch.stack([exp.next_state for exp in experiences])
        dones = torch.BoolTensor([exp.done for exp in experiences])
        
        # Q-values actuales
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        # Q-values objetivo (Double DQN)
        with torch.no_grad():
            # Seleccionar acciones con red principal
            next_actions = self.q_network(next_states).argmax(1)
            # Evaluar con red objetivo
            next_q_values = self.target_network(next_states).gather(1, next_actions.unsqueeze(1)).squeeze(1)
            target_q_values = rewards + (self.gamma * next_q_values * ~dones)
        
        # Calcular pérdida
        loss = F.mse_loss(current_q_values.squeeze(), target_q_values)
        
        # Optimización
        self.optimizer.zero_grad()
        loss.backward()
        
        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 1.0)
        
        self.optimizer.step()
        
        # Decaimiento de epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        self.total_steps += 1
        
        return loss.item()
    
    def update_target_network(self):
        """Actualiza la red objetivo con pesos de la red principal"""
        self.target_network.load_state_dict(self.q_network.state_dict())
    
    def train_episode(self, 
                     initial_state: RLState,
                     environment_step_fn,
                     max_steps: int = 100) -> Dict[str, float]:
        """Entrena un episodio completo"""
        
        state = initial_state
        total_reward = 0.0
        total_loss = 0.0
        step_count = 0
        
        episode_history = {
            'states': [],
            'actions': [],
            'rewards': [],
            'q_values': []
        }
        
        for step in range(max_steps):
            # Seleccionar acción
            action = self.choose_action(state)
            
            # Ejecutar acción en el entorno
            next_state, reward, done = environment_step_fn(state, action)
            
            # Almacenar experiencia
            self.remember(state, action, reward, next_state, done)
            
            # Aprender de experiencias
            if len(self.memory) >= self.batch_size:
                loss = self.replay_learning()
                total_loss += loss
            
            # Registrar para historial
            episode_history['states'].append(state)
            episode_history['actions'].append(action)
            episode_history['rewards'].append(reward)
            
            # Q-value para análisis
            state_tensor = self.state_to_tensor(state)
            with torch.no_grad():
                q_vals = self.q_network(state_tensor)
                max_q = torch.max(q_vals).item()
                episode_history['q_values'].append(max_q)
            
            total_reward += reward
            step_count += 1
            state = next_state
            
            if done:
                break
        
        # Actualizar red objetivo periódicamente
        if self.episode_count % 10 == 0:
            self.update_target_network()
        
        # Registrar episodio
        avg_loss = total_loss / step_count if step_count > 0 else 0
        
        self.training_history['episodes'].append(self.episode_count)
        self.training_history['rewards'].append(total_reward)
        self.training_history['losses'].append(avg_loss)
        self.training_history['epsilon_history'].append(self.epsilon)
        self.training_history['q_values'].append(np.mean(episode_history['q_values']))
        
        # Actualizar mejor recompensa
        if total_reward > self.best_reward:
            self.best_reward = total_reward
            logger.info(f"🏆 Nueva mejor recompensa: {total_reward:.3f}")
        
        self.episode_count += 1
        
        results = {
            'total_reward': total_reward,
            'avg_loss': avg_loss,
            'steps': step_count,
            'epsilon': self.epsilon,
            'avg_q_value': np.mean(episode_history['q_values'])
        }
        
        logger.info(f"📈 Episodio {self.episode_count}: Recompensa={total_reward:.2f}, "
                   f"Pérdida={avg_loss:.4f}, Pasos={step_count}, ε={self.epsilon:.3f}")
        
        return results
    
    def create_state_from_context(self, 
                                 model_performances: Dict[str, float],
                                 context_features: List[float],
                                 current_weights: Dict[str, float]) -> RLState:
        """Crea estado RL desde contexto del sistema"""
        
        # Performance de modelos (en orden fijo)
        perf_list = [model_performances.get(name, 0.5) for name in self.model_names]
        
        # Pesos actuales (en orden fijo)
        weights_list = [current_weights.get(name, 1.0) for name in self.model_names]
        
        # Features temporales
        now = datetime.now()
        time_features = [
            now.hour / 24.0,           # Hora del día
            now.weekday() / 7.0,       # Día de la semana
            now.month / 12.0,          # Mes del año
            (now.timetuple().tm_yday) / 365.0  # Día del año
        ]
        
        # Recompensas recientes (simuladas o desde historial)
        recent_rewards = getattr(self, '_recent_rewards', [0.0] * 5)
        
        return RLState(
            model_performances=perf_list,
            context_features=context_features[:10],  # Limitar a 10
            recent_rewards=recent_rewards[-5:],       # Últimas 5
            current_weights=weights_list,
            time_features=time_features
        )
    
    def apply_action_to_weights(self, 
                               action: RLAction,
                               current_weights: Dict[str, float]) -> Dict[str, float]:
        """Aplica acción RL a los pesos de modelos"""
        
        new_weights = current_weights.copy()
        model_name = self.model_names[action.model_index]
        
        if action.action_type == ActionType.INCREASE_MODEL_WEIGHT:
            new_weights[model_name] = min(3.0, new_weights[model_name] + abs(action.adjustment_value))
            
        elif action.action_type == ActionType.DECREASE_MODEL_WEIGHT:
            new_weights[model_name] = max(0.1, new_weights[model_name] - abs(action.adjustment_value))
            
        elif action.action_type == ActionType.CHANGE_STRATEGY:
            # Cambio de estrategia: redistribuir pesos
            total_weight = sum(new_weights.values())
            redistribution = action.adjustment_value * total_weight
            
            for name in self.model_names:
                if name != model_name:
                    new_weights[name] = max(0.1, new_weights[name] - redistribution / (len(self.model_names) - 1))
            
            new_weights[model_name] = min(3.0, new_weights[model_name] + redistribution)
            
        elif action.action_type == ActionType.ADJUST_THRESHOLD:
            # Ajuste proporcional de todos los pesos
            factor = 1.0 + action.adjustment_value
            for name in new_weights:
                new_weights[name] = max(0.1, min(3.0, new_weights[name] * factor))
                
        elif action.action_type == ActionType.COMBINE_MODELS:
            # Combinación: promedio ponderado con otro modelo
            other_index = (action.model_index + 1) % len(self.model_names)
            other_name = self.model_names[other_index]
            
            alpha = abs(action.adjustment_value)
            new_weights[model_name] = (1 - alpha) * new_weights[model_name] + alpha * new_weights[other_name]
            new_weights[other_name] = (1 - alpha) * new_weights[other_name] + alpha * new_weights[model_name]
        
        logger.debug(f"🎯 Acción aplicada: {action.action_type.name} en {model_name} "
                    f"(ajuste: {action.adjustment_value:.3f})")
        
        return new_weights
    
    def save_model(self, filepath: str):
        """Guarda el modelo entrenado"""
        try:
            torch.save({
                'q_network_state_dict': self.q_network.state_dict(),
                'target_network_state_dict': self.target_network.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'training_history': self.training_history,
                'episode_count': self.episode_count,
                'epsilon': self.epsilon,
                'best_reward': self.best_reward,
                'hyperparameters': {
                    'state_size': self.state_size,
                    'action_size': self.action_size,
                    'learning_rate': self.learning_rate,
                    'gamma': self.gamma,
                    'epsilon_decay': self.epsilon_decay,
                    'epsilon_min': self.epsilon_min
                }
            }, filepath)
            
            logger.info(f"💾 Modelo RL guardado en {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando modelo: {e}")
    
    def load_model(self, filepath: str):
        """Carga modelo pre-entrenado"""
        try:
            checkpoint = torch.load(filepath, map_location='cpu')
            
            self.q_network.load_state_dict(checkpoint['q_network_state_dict'])
            self.target_network.load_state_dict(checkpoint['target_network_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.training_history = checkpoint['training_history']
            self.episode_count = checkpoint['episode_count']
            self.epsilon = checkpoint['epsilon']
            self.best_reward = checkpoint['best_reward']
            
            logger.info(f"📂 Modelo RL cargado desde {filepath}")
            logger.info(f"   Episodios: {self.episode_count}, Mejor recompensa: {self.best_reward:.3f}")
            
        except Exception as e:
            logger.error(f"❌ Error cargando modelo: {e}")
    
    def get_training_summary(self) -> Dict[str, Any]:
        """Obtiene resumen del entrenamiento"""
        if not self.training_history['episodes']:
            return {"error": "No hay historial de entrenamiento"}
        
        recent_rewards = self.training_history['rewards'][-10:] if len(self.training_history['rewards']) >= 10 else self.training_history['rewards']
        
        return {
            "total_episodes": self.episode_count,
            "best_reward": self.best_reward,
            "avg_recent_reward": np.mean(recent_rewards),
            "current_epsilon": self.epsilon,
            "memory_size": len(self.memory),
            "avg_q_value": np.mean(self.training_history['q_values'][-10:]) if self.training_history['q_values'] else 0,
            "training_progress": {
                "episodes": self.training_history['episodes'][-20:],
                "rewards": self.training_history['rewards'][-20:],
                "losses": self.training_history['losses'][-20:]
            }
        }

# Funciones de utilidad
def create_rl_trainer(state_size: int = 30, action_size: int = 50) -> ReinforcementTrainer:
    """Crea un entrenador de RL"""
    return ReinforcementTrainer(state_size, action_size)

def simulate_environment_step(state: RLState, action: RLAction) -> Tuple[RLState, float, bool]:
    """Simula un paso del entorno (para testing)"""
    # Simular cambio de estado
    new_performances = [max(0.1, min(0.9, perf + np.random.normal(0, 0.05))) 
                       for perf in state.model_performances]
    
    new_state = RLState(
        model_performances=new_performances,
        context_features=state.context_features,
        recent_rewards=state.recent_rewards[1:] + [0.0],  # Rotar rewards
        current_weights=state.current_weights,
        time_features=state.time_features
    )
    
    # Recompensa simulada
    improvement = np.mean(new_performances) - np.mean(state.model_performances)
    reward = improvement * 10.0 + np.random.normal(0, 0.5)
    
    # Done si alcanzamos muy buen performance
    done = np.mean(new_performances) > 0.85
    
    return new_state, reward, done

if __name__ == "__main__":
    # Demo del RL trainer
    print("🎮 Demo Reinforcement Learning Trainer")
    
    # Crear trainer
    trainer = create_rl_trainer()
    
    # Estado inicial simulado
    initial_state = RLState(
        model_performances=[0.6, 0.5, 0.7, 0.55, 0.65, 0.6, 0.7],
        context_features=[0.5, 0.3, 0.8, 0.4, 0.6] + [0.0] * 5,
        recent_rewards=[1.0, -0.5, 2.0, 0.5, 1.5],
        current_weights=[1.0, 1.2, 0.8, 1.1, 0.9, 1.0, 1.3],
        time_features=[0.5, 0.3, 0.7, 0.8]
    )
    
    print("🏋️ Entrenando 5 episodios de demostración...")
    
    for episode in range(5):
        results = trainer.train_episode(
            initial_state, 
            simulate_environment_step,
            max_steps=20
        )
        
        print(f"   Episodio {episode + 1}: Recompensa = {results['total_reward']:.2f}")
    
    # Mostrar resumen
    summary = trainer.get_training_summary()
    print(f"\n📊 Resumen del entrenamiento:")
    print(f"   Episodios totales: {summary['total_episodes']}")
    print(f"   Mejor recompensa: {summary['best_reward']:.3f}")
    print(f"   Epsilon actual: {summary['current_epsilon']:.3f}")
    print(f"   Memoria: {summary['memory_size']} experiencias")
