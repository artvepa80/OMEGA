# modules/adaptive_learning_system.py
"""
Adaptive Learning System - Continuous improvement and adaptation
"""

import logging
import numpy as np
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class AdaptivePrediction:
    combination: List[int]
    confidence: float
    rank: int
    total_score: float
    components_used: List[str]

class AdaptiveLearningSystem:
    """System that continuously learns and adapts to improve predictions"""
    
    def __init__(self, enable_all: bool = True):
        self.enable_all = enable_all
        self.logger = logging.getLogger(__name__)
        self.components = {
            'pattern_learner': True,
            'frequency_adapter': True,
            'trend_detector': True,
            'outlier_handler': True
        }
        self.adaptation_history = []
    
    def learn_patterns(self, historical_data: List[List[int]]) -> Dict[str, Any]:
        """Learn patterns from historical data"""
        try:
            # Analyze patterns
            patterns = {}
            
            # Pattern 1: Number frequency adaptation
            all_numbers = [num for combo in historical_data for num in combo]
            from collections import Counter
            frequency = Counter(all_numbers)
            
            # Identify trending numbers (last 20% of data)
            recent_size = max(1, len(historical_data) // 5)
            recent_data = historical_data[-recent_size:]
            recent_numbers = [num for combo in recent_data for num in combo]
            recent_frequency = Counter(recent_numbers)
            
            # Calculate trend scores
            trend_scores = {}
            for num in range(1, 41):
                recent_freq = recent_frequency.get(num, 0) / len(recent_numbers) if recent_numbers else 0
                historical_freq = frequency.get(num, 0) / len(all_numbers) if all_numbers else 0
                trend_scores[num] = recent_freq - historical_freq
            
            patterns['trending_numbers'] = sorted(
                [(num, score) for num, score in trend_scores.items() if score > 0.01],
                key=lambda x: x[1], reverse=True
            )[:10]
            
            patterns['declining_numbers'] = sorted(
                [(num, abs(score)) for num, score in trend_scores.items() if score < -0.01],
                key=lambda x: x[1], reverse=True
            )[:10]
            
            return patterns
            
        except Exception as e:
            self.logger.warning(f"Pattern learning failed: {e}")
            return {}
    
    def generate_adaptive_combination(self, patterns: Dict[str, Any], seed: int = 0) -> List[int]:
        """Generate combination based on learned patterns"""
        
        np.random.seed(seed)
        
        # Start with trending numbers
        trending = patterns.get('trending_numbers', [])
        combo = []
        
        # Add 2-3 trending numbers
        if trending:
            trend_count = min(3, len(trending))
            selected_trending = np.random.choice(
                [num for num, _ in trending[:6]], 
                size=trend_count, 
                replace=False
            )
            combo.extend(selected_trending)
        
        # Fill remaining with balanced selection
        remaining_needed = 6 - len(combo)
        available_numbers = [n for n in range(1, 41) if n not in combo]
        
        if remaining_needed > 0:
            # Divide into ranges for balanced selection
            low_range = [n for n in available_numbers if 1 <= n <= 13]
            mid_range = [n for n in available_numbers if 14 <= n <= 27]
            high_range = [n for n in available_numbers if 28 <= n <= 40]
            
            # Try to get at least one from each range
            for range_nums in [low_range, mid_range, high_range]:
                if range_nums and len(combo) < 6:
                    combo.append(np.random.choice(range_nums))
                    available_numbers = [n for n in available_numbers if n not in combo]
            
            # Fill remaining randomly
            while len(combo) < 6 and available_numbers:
                combo.append(np.random.choice(available_numbers))
                available_numbers = [n for n in available_numbers if n not in combo]
        
        return sorted(combo)
    
    async def generate_adaptive_predictions(self, historical_data: List[List[int]], 
                                          count: int) -> Dict[str, Any]:
        """Generate adaptive predictions asynchronously"""
        
        try:
            # Learn patterns
            patterns = self.learn_patterns(historical_data)
            
            # Generate predictions
            predictions = []
            
            for i in range(count):
                combination = self.generate_adaptive_combination(patterns, seed=i)
                
                # Calculate confidence based on trend alignment
                confidence = 0.6  # Base confidence
                
                # Boost confidence if combination includes trending numbers
                trending_nums = {num for num, _ in patterns.get('trending_numbers', [])}
                trend_overlap = len(set(combination) & trending_nums)
                confidence += (trend_overlap / 6) * 0.3
                
                prediction = AdaptivePrediction(
                    combination=combination,
                    confidence=min(0.95, confidence),
                    rank=i + 1,
                    total_score=confidence * 100,
                    components_used=['pattern_learner', 'frequency_adapter', 'trend_detector']
                )
                
                predictions.append({
                    'combination': prediction.combination,
                    'confidence': prediction.confidence,
                    'rank': prediction.rank,
                    'total_score': prediction.total_score,
                    'components_used': prediction.components_used
                })
            
            return {
                'predictions': predictions,
                'patterns_learned': len(patterns),
                'trending_count': len(patterns.get('trending_numbers', [])),
                'declining_count': len(patterns.get('declining_numbers', []))
            }
            
        except Exception as e:
            self.logger.error(f"Adaptive prediction generation failed: {e}")
            return {
                'predictions': [],
                'error': str(e)
            }

def create_adaptive_learning_system(enable_all: bool = True) -> AdaptiveLearningSystem:
    """Create and configure adaptive learning system"""
    return AdaptiveLearningSystem(enable_all=enable_all)