# modules/ai_ensemble_system.py
"""
AI Ensemble System - Intelligent model combination system
"""

import logging
import numpy as np
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class SpecialistModel:
    name: str
    expertise: str
    weight: float
    confidence: float
    predictions: List[List[int]]

class AIEnsembleSystem:
    """Intelligent ensemble system that combines multiple AI specialists"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.specialists = []
        self.trained = False
        self.ensemble_weights = {}
    
    def create_specialists(self) -> List[SpecialistModel]:
        """Create specialized models for different aspects"""
        
        specialists = [
            SpecialistModel(
                name="frequency_specialist",
                expertise="number_frequency_analysis",
                weight=1.0,
                confidence=0.75,
                predictions=[]
            ),
            SpecialistModel(
                name="pattern_specialist",
                expertise="sequence_pattern_detection",
                weight=1.0,
                confidence=0.70,
                predictions=[]
            ),
            SpecialistModel(
                name="trend_specialist",
                expertise="trend_analysis",
                weight=1.0,
                confidence=0.65,
                predictions=[]
            ),
            SpecialistModel(
                name="outlier_specialist",
                expertise="outlier_detection",
                weight=0.8,
                confidence=0.60,
                predictions=[]
            ),
            SpecialistModel(
                name="balance_specialist",
                expertise="number_balance_optimization",
                weight=0.9,
                confidence=0.68,
                predictions=[]
            )
        ]
        
        return specialists
    
    def train_ensemble(self, historical_data: List[List[int]]) -> None:
        """Train the ensemble with historical data"""
        try:
            self.logger.info(f"Training AI ensemble with {len(historical_data)} samples")
            
            # Create specialists
            self.specialists = self.create_specialists()
            
            # Train each specialist
            for specialist in self.specialists:
                specialist.predictions = self._train_specialist(specialist, historical_data)
            
            # Calculate ensemble weights based on specialist performance
            self.ensemble_weights = self._calculate_ensemble_weights()
            
            self.trained = True
            self.logger.info(f"AI ensemble trained with {len(self.specialists)} specialists")
            
        except Exception as e:
            self.logger.error(f"Ensemble training failed: {e}")
            self.trained = False
    
    def _train_specialist(self, specialist: SpecialistModel, 
                         historical_data: List[List[int]]) -> List[List[int]]:
        """Train individual specialist based on their expertise"""
        
        predictions = []
        
        try:
            if specialist.expertise == "number_frequency_analysis":
                predictions = self._train_frequency_specialist(historical_data)
            elif specialist.expertise == "sequence_pattern_detection":
                predictions = self._train_pattern_specialist(historical_data)
            elif specialist.expertise == "trend_analysis":
                predictions = self._train_trend_specialist(historical_data)
            elif specialist.expertise == "outlier_detection":
                predictions = self._train_outlier_specialist(historical_data)
            elif specialist.expertise == "number_balance_optimization":
                predictions = self._train_balance_specialist(historical_data)
            else:
                # Generic training
                predictions = self._train_generic_specialist(historical_data)
                
        except Exception as e:
            self.logger.warning(f"Specialist {specialist.name} training failed: {e}")
            predictions = self._generate_fallback_predictions(5)
        
        return predictions[:5]  # Limit predictions per specialist
    
    def _train_frequency_specialist(self, historical_data: List[List[int]]) -> List[List[int]]:
        """Train specialist focused on frequency analysis"""
        from collections import Counter
        
        # Analyze number frequencies
        all_numbers = [num for combo in historical_data for num in combo]
        frequency = Counter(all_numbers)
        
        # Get most and least frequent numbers
        most_frequent = [num for num, _ in frequency.most_common(20)]
        least_frequent = [num for num, _ in frequency.most_common()[-10:]]
        
        predictions = []
        for i in range(5):
            combo = []
            
            # Mix frequent and infrequent numbers
            frequent_count = np.random.randint(3, 5)
            combo.extend(np.random.choice(most_frequent, size=frequent_count, replace=False))
            
            remaining = 6 - len(combo)
            available = [n for n in range(1, 41) if n not in combo]
            combo.extend(np.random.choice(available, size=remaining, replace=False))
            
            predictions.append(sorted(combo))
        
        return predictions
    
    def _train_pattern_specialist(self, historical_data: List[List[int]]) -> List[List[int]]:
        """Train specialist focused on pattern detection"""
        predictions = []
        
        # Analyze consecutive patterns
        consecutive_pairs = defaultdict(int)
        
        for combo in historical_data:
            for i in range(len(combo) - 1):
                pair = (combo[i], combo[i + 1])
                consecutive_pairs[pair] += 1
        
        # Get most common consecutive pairs
        top_pairs = sorted(consecutive_pairs.items(), key=lambda x: x[1], reverse=True)[:10]
        
        for i in range(5):
            combo = []
            
            # Start with a strong consecutive pair
            if top_pairs:
                pair = top_pairs[i % len(top_pairs)][0]
                combo.extend(pair)
            
            # Fill remaining
            while len(combo) < 6:
                available = [n for n in range(1, 41) if n not in combo]
                if available:
                    combo.append(np.random.choice(available))
                else:
                    break
            
            predictions.append(sorted(combo))
        
        return predictions
    
    def _train_trend_specialist(self, historical_data: List[List[int]]) -> List[List[int]]:
        """Train specialist focused on trend analysis"""
        predictions = []
        
        # Analyze recent trends (last 20% of data)
        recent_size = max(1, len(historical_data) // 5)
        recent_data = historical_data[-recent_size:]
        
        from collections import Counter
        recent_frequency = Counter([num for combo in recent_data for num in combo])
        trending_numbers = [num for num, _ in recent_frequency.most_common(15)]
        
        for i in range(5):
            combo = []
            
            # Use trending numbers
            trend_count = np.random.randint(2, 4)
            if len(trending_numbers) >= trend_count:
                combo.extend(np.random.choice(trending_numbers, size=trend_count, replace=False))
            
            # Fill remaining with balanced selection
            while len(combo) < 6:
                available = [n for n in range(1, 41) if n not in combo]
                if available:
                    combo.append(np.random.choice(available))
                else:
                    break
            
            predictions.append(sorted(combo))
        
        return predictions
    
    def _train_outlier_specialist(self, historical_data: List[List[int]]) -> List[List[int]]:
        """Train specialist focused on outlier detection"""
        predictions = []
        
        # Find rarely used numbers
        from collections import Counter
        all_numbers = [num for combo in historical_data for num in combo]
        frequency = Counter(all_numbers)
        rare_numbers = [num for num, count in frequency.items() if count < np.percentile(list(frequency.values()), 25)]
        
        for i in range(5):
            combo = []
            
            # Include some rare numbers
            if rare_numbers:
                rare_count = np.random.randint(1, 3)
                combo.extend(np.random.choice(rare_numbers, size=min(rare_count, len(rare_numbers)), replace=False))
            
            # Fill with regular numbers
            while len(combo) < 6:
                available = [n for n in range(1, 41) if n not in combo]
                if available:
                    combo.append(np.random.choice(available))
                else:
                    break
            
            predictions.append(sorted(combo))
        
        return predictions
    
    def _train_balance_specialist(self, historical_data: List[List[int]]) -> List[List[int]]:
        """Train specialist focused on number balance"""
        predictions = []
        
        for i in range(5):
            combo = []
            
            # Ensure balanced distribution across ranges
            low_range = list(range(1, 14))    # 1-13
            mid_range = list(range(14, 28))   # 14-27
            high_range = list(range(28, 41))  # 28-40
            
            # Get 2 numbers from each range
            combo.extend(np.random.choice(low_range, size=2, replace=False))
            combo.extend(np.random.choice(mid_range, size=2, replace=False))
            combo.extend(np.random.choice(high_range, size=2, replace=False))
            
            predictions.append(sorted(combo))
        
        return predictions
    
    def _train_generic_specialist(self, historical_data: List[List[int]]) -> List[List[int]]:
        """Generic training for unknown specialist types"""
        return self._generate_fallback_predictions(5)
    
    def _generate_fallback_predictions(self, count: int) -> List[List[int]]:
        """Generate fallback predictions"""
        predictions = []
        for i in range(count):
            combo = sorted(np.random.choice(range(1, 41), 6, replace=False))
            predictions.append(combo)
        return predictions
    
    def _calculate_ensemble_weights(self) -> Dict[str, float]:
        """Calculate weights for ensemble based on specialist confidence"""
        weights = {}
        
        total_confidence = sum(specialist.confidence for specialist in self.specialists)
        
        for specialist in self.specialists:
            weights[specialist.name] = specialist.confidence / total_confidence if total_confidence > 0 else 1.0 / len(self.specialists)
        
        return weights
    
    def generate_ensemble_predictions(self, count: int) -> List[Dict[str, Any]]:
        """Generate predictions using ensemble method"""
        
        if not self.trained or not self.specialists:
            self.logger.warning("Ensemble not trained, using fallback")
            return self._generate_fallback_ensemble_predictions(count)
        
        ensemble_predictions = []
        
        try:
            # Collect all specialist predictions
            all_predictions = []
            for specialist in self.specialists:
                for pred in specialist.predictions:
                    weight = self.ensemble_weights.get(specialist.name, 1.0)
                    all_predictions.append({
                        'combination': pred,
                        'specialist': specialist.name,
                        'weight': weight,
                        'confidence': specialist.confidence
                    })
            
            # Sort by weighted confidence
            all_predictions.sort(key=lambda x: x['weight'] * x['confidence'], reverse=True)
            
            # Select top predictions, avoiding duplicates
            selected = []
            seen_combinations = set()
            
            for pred in all_predictions:
                combo_tuple = tuple(pred['combination'])
                if combo_tuple not in seen_combinations and len(selected) < count:
                    selected.append(pred)
                    seen_combinations.add(combo_tuple)
            
            # Convert to final format
            for i, pred in enumerate(selected):
                ensemble_predictions.append({
                    'combination': pred['combination'],
                    'confidence': pred['confidence'],
                    'method': 'ensemble_weighted',
                    'specialists_used': len(self.specialists),
                    'individual_predictions': [pred['specialist']]
                })
            
            # Fill remaining with specialist voting if needed
            # PARCHE: Evitar loop infinito con contador de seguridad
            safety_counter = 0
            max_attempts = count * 10  # Máximo 10 intentos por combinación
            
            while len(ensemble_predictions) < count and safety_counter < max_attempts:
                safety_counter += 1
                combo = self._generate_voted_combination()
                if combo not in [pred['combination'] for pred in ensemble_predictions]:
                    ensemble_predictions.append({
                        'combination': combo,
                        'confidence': 0.6,
                        'method': 'ensemble_voting',
                        'specialists_used': len(self.specialists),
                        'individual_predictions': [s.name for s in self.specialists]
                    })
            
            # Log si se alcanzó el límite de seguridad
            if safety_counter >= max_attempts:
                self.logger.warning(f"⚠️ Límite de seguridad alcanzado en ensemble generation ({max_attempts} intentos)")
                self.logger.info(f"✅ Generadas {len(ensemble_predictions)} predicciones ensemble (solicitadas: {count})")
            
        except Exception as e:
            self.logger.error(f"Ensemble prediction generation failed: {e}")
            return self._generate_fallback_ensemble_predictions(count)
        
        return ensemble_predictions[:count]
    
    def _generate_voted_combination(self) -> List[int]:
        """Generate combination using specialist voting"""
        
        # Count votes for each number across specialists
        votes = defaultdict(int)
        
        for specialist in self.specialists:
            weight = self.ensemble_weights.get(specialist.name, 1.0)
            for pred in specialist.predictions:
                for num in pred:
                    votes[num] += weight
        
        # Select top voted numbers
        top_voted = sorted(votes.items(), key=lambda x: x[1], reverse=True)
        
        combo = []
        for num, _ in top_voted:
            if len(combo) < 6:
                combo.append(num)
        
        # Fill remaining if needed
        while len(combo) < 6:
            available = [n for n in range(1, 41) if n not in combo]
            if available:
                combo.append(np.random.choice(available))
            else:
                break
        
        return sorted(combo)
    
    def _generate_fallback_ensemble_predictions(self, count: int) -> List[Dict[str, Any]]:
        """Generate fallback ensemble predictions"""
        predictions = []
        
        for i in range(count):
            combo = sorted(np.random.choice(range(1, 41), 6, replace=False))
            predictions.append({
                'combination': combo,
                'confidence': 0.4,
                'method': 'fallback',
                'specialists_used': 0,
                'individual_predictions': []
            })
        
        return predictions

def create_ai_ensemble() -> AIEnsembleSystem:
    """Create and configure AI ensemble system"""
    return AIEnsembleSystem()

async def generate_intelligent_predictions(ensemble: AIEnsembleSystem, 
                                         historical_data: List[List[int]], 
                                         count: int) -> List[Dict[str, Any]]:
    """Generate intelligent predictions using the ensemble system"""
    
    try:
        # Train ensemble if not already trained
        if not ensemble.trained:
            ensemble.train_ensemble(historical_data)
        
        # Generate predictions
        predictions = ensemble.generate_ensemble_predictions(count)
        
        return predictions
        
    except Exception as e:
        ensemble.logger.error(f"Intelligent prediction generation failed: {e}")
        
        # Return fallback predictions
        fallback_predictions = []
        for i in range(count):
            combo = sorted(np.random.choice(range(1, 41), 6, replace=False))
            fallback_predictions.append({
                'combination': combo,
                'confidence': 0.4,
                'method': 'fallback_error',
                'specialists_used': 0,
                'individual_predictions': []
            })
        
        return fallback_predictions
