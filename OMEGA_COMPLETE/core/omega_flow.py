"""
OMEGA Flow Manager
Core lottery prediction system integration with ensemble learning and advanced pattern recognition
"""

import asyncio
import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pickle
import hashlib

logger = logging.getLogger(__name__)

class LotteryType(str, Enum):
    KABALA = "kabala"
    POWERBALL = "powerball"
    MEGA_MILLIONS = "mega_millions"
    EUROMILLIONS = "euromillions"
    LOTTO_6_49 = "lotto_649"

class PredictionMode(str, Enum):
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"
    EXPERIMENTAL = "experimental"

@dataclass
class LotterySeries:
    numbers: List[int]
    confidence: float
    pattern_score: float
    frequency_score: float
    statistical_score: float
    meta_data: Dict[str, Any]

@dataclass
class PredictionResult:
    series: List[LotterySeries]
    analysis: Dict[str, Any]
    recommendations: List[str]
    generated_at: datetime
    expires_at: datetime

class OmegaFlowManager:
    """Main OMEGA flow manager for lottery predictions"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.models = {}
        self.historical_data = {}
        self.pattern_cache = {}
        
        # Configuration
        self.lottery_configs = {
            LotteryType.KABALA: {
                "number_range": (1, 36),
                "series_length": 6,
                "draws_per_week": 2,
                "jackpot_frequency": 0.02
            },
            LotteryType.POWERBALL: {
                "main_range": (1, 69),
                "power_range": (1, 26),
                "series_length": 5,
                "powerball": True
            }
        }
    
    async def initialize(self):
        """Initialize OMEGA flow system"""
        try:
            # Load historical data
            await self._load_historical_data()
            
            # Initialize ML models
            await self._initialize_models()
            
            # Load pattern cache
            await self._load_pattern_cache()
            
            logger.info("OMEGA Flow Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OMEGA Flow: {e}")
            raise
    
    async def generate_series(self, 
                            lottery_type: str, 
                            series_count: int = 5,
                            filters: Dict[str, Any] = None,
                            user_preferences: Dict[str, Any] = None) -> PredictionResult:
        """Generate lottery series predictions"""
        
        try:
            lottery_enum = LotteryType(lottery_type)
            config = self.lottery_configs.get(lottery_enum)
            
            if not config:
                raise ValueError(f"Unsupported lottery type: {lottery_type}")
            
            # Generate predictions using ensemble approach
            series_predictions = []
            
            for i in range(series_count):
                # Generate base prediction
                base_numbers = await self._generate_base_prediction(lottery_enum, config)
                
                # Apply filters and adjustments
                adjusted_numbers = await self._apply_filters(base_numbers, filters, config)
                
                # Calculate scores
                confidence = await self._calculate_confidence(adjusted_numbers, lottery_enum)
                pattern_score = await self._calculate_pattern_score(adjusted_numbers, lottery_enum)
                frequency_score = await self._calculate_frequency_score(adjusted_numbers, lottery_enum)
                statistical_score = await self._calculate_statistical_score(adjusted_numbers, lottery_enum)
                
                # Create series object
                series = LotterySeries(
                    numbers=adjusted_numbers,
                    confidence=confidence,
                    pattern_score=pattern_score,
                    frequency_score=frequency_score,
                    statistical_score=statistical_score,
                    meta_data={
                        "generation_method": "ensemble_ml",
                        "model_version": "4.0.1",
                        "filters_applied": filters or {},
                        "series_index": i
                    }
                )
                
                series_predictions.append(series)
            
            # Sort by confidence
            series_predictions.sort(key=lambda x: x.confidence, reverse=True)
            
            # Generate analysis
            analysis = await self._generate_analysis(series_predictions, lottery_enum)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(series_predictions, analysis)
            
            # Create result
            result = PredictionResult(
                series=series_predictions,
                analysis=analysis,
                recommendations=recommendations,
                generated_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=24)
            )
            
            # Cache result
            await self._cache_prediction_result(result, lottery_type)
            
            return result
            
        except Exception as e:
            logger.error(f"Series generation failed: {e}")
            raise
    
    async def _generate_base_prediction(self, lottery_type: LotteryType, config: Dict[str, Any]) -> List[int]:
        """Generate base prediction using ML ensemble"""
        
        try:
            # Get model predictions
            transformer_pred = await self._get_transformer_prediction(lottery_type)
            statistical_pred = await self._get_statistical_prediction(lottery_type)
            pattern_pred = await self._get_pattern_prediction(lottery_type)
            frequency_pred = await self._get_frequency_prediction(lottery_type)
            
            # Ensemble combination with weights
            ensemble_weights = {
                "transformer": 0.4,
                "statistical": 0.25,
                "pattern": 0.20,
                "frequency": 0.15
            }
            
            # Combine predictions
            combined_scores = {}
            number_range = config["number_range"]
            
            for num in range(number_range[0], number_range[1] + 1):
                score = (
                    transformer_pred.get(num, 0) * ensemble_weights["transformer"] +
                    statistical_pred.get(num, 0) * ensemble_weights["statistical"] +
                    pattern_pred.get(num, 0) * ensemble_weights["pattern"] +
                    frequency_pred.get(num, 0) * ensemble_weights["frequency"]
                )
                combined_scores[num] = score
            
            # Select top numbers
            series_length = config["series_length"]
            sorted_numbers = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Add some randomness to avoid identical predictions
            top_candidates = [num for num, score in sorted_numbers[:series_length * 2]]
            
            # Smart selection with diversity
            selected_numbers = await self._smart_number_selection(
                top_candidates, series_length, lottery_type
            )
            
            return sorted(selected_numbers)
            
        except Exception as e:
            logger.error(f"Base prediction generation failed: {e}")
            # Fallback to random selection
            return await self._fallback_prediction(config)
    
    async def _get_transformer_prediction(self, lottery_type: LotteryType) -> Dict[int, float]:
        """Get prediction from transformer model"""
        
        # Mock transformer prediction - in production, load actual model
        mock_predictions = {}
        
        if lottery_type == LotteryType.KABALA:
            # Generate realistic probability distribution
            for i in range(1, 37):
                # Simulate learned patterns
                base_prob = np.random.beta(2, 5)  # Skewed distribution
                if i in [7, 14, 21, 28]:  # "Lucky" numbers
                    base_prob *= 1.2
                mock_predictions[i] = base_prob
        
        return mock_predictions
    
    async def _get_statistical_prediction(self, lottery_type: LotteryType) -> Dict[int, float]:
        """Get statistical analysis prediction"""
        
        # Mock statistical analysis
        historical_draws = await self._get_historical_draws(lottery_type)
        
        if not historical_draws:
            return {}
        
        # Calculate frequency-based probabilities
        frequency_count = {}
        total_draws = len(historical_draws)
        
        for draw in historical_draws:
            for number in draw:
                frequency_count[number] = frequency_count.get(number, 0) + 1
        
        # Convert to probabilities with regression to mean
        predictions = {}
        for number, count in frequency_count.items():
            freq_prob = count / (total_draws * 6)  # 6 numbers per draw
            # Apply regression to mean
            predictions[number] = 0.7 * freq_prob + 0.3 * (1/36)  # 1/36 is random probability
        
        return predictions
    
    async def _get_pattern_prediction(self, lottery_type: LotteryType) -> Dict[int, float]:
        """Get pattern-based prediction"""
        
        # Mock pattern analysis
        patterns = await self._analyze_patterns(lottery_type)
        
        # Generate predictions based on identified patterns
        predictions = {}
        
        # Sum patterns (consecutive numbers)
        consecutive_boost = patterns.get("consecutive_tendency", 1.0)
        
        # Odd/even balance
        odd_even_balance = patterns.get("odd_even_balance", 0.5)
        
        # Number range distribution
        range_preferences = patterns.get("range_distribution", {})
        
        for i in range(1, 37):
            score = 0.5  # Base score
            
            # Apply pattern adjustments
            if i % 2 == 1:  # Odd numbers
                score *= (1 + odd_even_balance * 0.2)
            else:  # Even numbers
                score *= (1 + (1 - odd_even_balance) * 0.2)
            
            # Range distribution
            if 1 <= i <= 12:
                score *= range_preferences.get("low", 1.0)
            elif 13 <= i <= 24:
                score *= range_preferences.get("mid", 1.0)
            else:
                score *= range_preferences.get("high", 1.0)
            
            predictions[i] = score
        
        return predictions
    
    async def _get_frequency_prediction(self, lottery_type: LotteryType) -> Dict[int, float]:
        """Get frequency-based prediction with hot/cold analysis"""
        
        historical_draws = await self._get_historical_draws(lottery_type)
        
        if not historical_draws:
            return {}
        
        recent_draws = historical_draws[-20:]  # Last 20 draws
        older_draws = historical_draws[-100:-20]  # 20-100 draws back
        
        # Calculate recent vs historical frequency
        recent_freq = {}
        older_freq = {}
        
        for draw in recent_draws:
            for num in draw:
                recent_freq[num] = recent_freq.get(num, 0) + 1
        
        for draw in older_draws:
            for num in draw:
                older_freq[num] = older_freq.get(num, 0) + 1
        
        # Generate predictions based on hot/cold analysis
        predictions = {}
        
        for i in range(1, 37):
            recent_count = recent_freq.get(i, 0)
            older_count = older_freq.get(i, 0)
            
            # Hot number logic (recently drawn frequently)
            if recent_count > 2:
                hot_score = min(recent_count / 20, 0.3)
            else:
                hot_score = 0
            
            # Cold number logic (overdue)
            if recent_count == 0 and older_count > 0:
                cold_score = min((len(recent_draws) - recent_count) / 40, 0.2)
            else:
                cold_score = 0
            
            # Combine hot and cold analysis
            predictions[i] = 0.5 + hot_score + cold_score
        
        return predictions
    
    async def _smart_number_selection(self, candidates: List[int], count: int, lottery_type: LotteryType) -> List[int]:
        """Smart selection with diversity and pattern awareness"""
        
        selected = []
        remaining_candidates = candidates.copy()
        
        # First selection - highest scoring
        selected.append(remaining_candidates[0])
        remaining_candidates.remove(selected[0])
        
        # Subsequent selections with diversity
        for _ in range(count - 1):
            best_candidate = None
            best_diversity_score = -1
            
            for candidate in remaining_candidates[:10]:  # Consider top 10
                # Calculate diversity score
                diversity_score = self._calculate_diversity_score(candidate, selected)
                
                if diversity_score > best_diversity_score:
                    best_diversity_score = diversity_score
                    best_candidate = candidate
            
            if best_candidate:
                selected.append(best_candidate)
                remaining_candidates.remove(best_candidate)
        
        return selected
    
    def _calculate_diversity_score(self, candidate: int, selected: List[int]) -> float:
        """Calculate diversity score for number selection"""
        
        if not selected:
            return 1.0
        
        # Distance-based diversity
        min_distance = min(abs(candidate - num) for num in selected)
        distance_score = min(min_distance / 10, 1.0)
        
        # Range diversity (avoid clustering)
        ranges = {"low": 0, "mid": 0, "high": 0}
        
        for num in selected:
            if 1 <= num <= 12:
                ranges["low"] += 1
            elif 13 <= num <= 24:
                ranges["mid"] += 1
            else:
                ranges["high"] += 1
        
        # Determine candidate range
        if 1 <= candidate <= 12:
            range_diversity = 1 - (ranges["low"] / len(selected))
        elif 13 <= candidate <= 24:
            range_diversity = 1 - (ranges["mid"] / len(selected))
        else:
            range_diversity = 1 - (ranges["high"] / len(selected))
        
        # Combine scores
        return distance_score * 0.6 + range_diversity * 0.4
    
    async def _apply_filters(self, numbers: List[int], filters: Dict[str, Any], config: Dict[str, Any]) -> List[int]:
        """Apply user-defined filters to predictions"""
        
        if not filters:
            return numbers
        
        filtered_numbers = numbers.copy()
        
        # Exclude specific numbers
        if "exclude_numbers" in filters:
            exclude = filters["exclude_numbers"]
            filtered_numbers = [n for n in filtered_numbers if n not in exclude]
        
        # Include specific numbers
        if "include_numbers" in filters:
            include = filters["include_numbers"]
            for num in include:
                if num not in filtered_numbers:
                    filtered_numbers.append(num)
        
        # Odd/even ratio filter
        if "odd_even_ratio" in filters:
            target_ratio = filters["odd_even_ratio"]  # e.g., 0.5 for 50% odd
            await self._adjust_odd_even_ratio(filtered_numbers, target_ratio)
        
        # Sum range filter
        if "sum_range" in filters:
            min_sum, max_sum = filters["sum_range"]
            current_sum = sum(filtered_numbers)
            
            if current_sum < min_sum or current_sum > max_sum:
                # Adjust numbers to fit sum range
                filtered_numbers = await self._adjust_sum_range(filtered_numbers, min_sum, max_sum)
        
        # Ensure correct series length
        series_length = config["series_length"]
        if len(filtered_numbers) > series_length:
            filtered_numbers = filtered_numbers[:series_length]
        elif len(filtered_numbers) < series_length:
            # Add random numbers to complete series
            number_range = config["number_range"]
            available = [n for n in range(number_range[0], number_range[1] + 1) 
                        if n not in filtered_numbers]
            needed = series_length - len(filtered_numbers)
            filtered_numbers.extend(np.random.choice(available, needed, replace=False))
        
        return sorted(filtered_numbers)
    
    async def _calculate_confidence(self, numbers: List[int], lottery_type: LotteryType) -> float:
        """Calculate prediction confidence"""
        
        # Base confidence
        confidence = 0.7
        
        # Pattern consistency
        pattern_score = await self._calculate_pattern_score(numbers, lottery_type)
        confidence += pattern_score * 0.1
        
        # Historical performance
        historical_performance = await self._get_historical_performance(lottery_type)
        confidence += historical_performance * 0.15
        
        # Ensemble agreement
        ensemble_agreement = await self._calculate_ensemble_agreement(numbers, lottery_type)
        confidence += ensemble_agreement * 0.05
        
        return min(confidence, 0.95)
    
    async def _calculate_pattern_score(self, numbers: List[int], lottery_type: LotteryType) -> float:
        """Calculate pattern matching score"""
        
        patterns = await self._analyze_patterns(lottery_type)
        score = 0.5  # Base score
        
        # Check consecutive numbers
        consecutive_count = sum(1 for i in range(len(numbers)-1) if numbers[i+1] == numbers[i] + 1)
        expected_consecutive = patterns.get("avg_consecutive", 1)
        if abs(consecutive_count - expected_consecutive) <= 1:
            score += 0.1
        
        # Check odd/even balance
        odd_count = sum(1 for n in numbers if n % 2 == 1)
        odd_ratio = odd_count / len(numbers)
        expected_ratio = patterns.get("odd_even_balance", 0.5)
        if abs(odd_ratio - expected_ratio) <= 0.2:
            score += 0.1
        
        # Check sum range
        numbers_sum = sum(numbers)
        expected_sum = patterns.get("avg_sum", 105)  # For Kabala
        sum_deviation = abs(numbers_sum - expected_sum) / expected_sum
        if sum_deviation <= 0.2:
            score += 0.15
        
        return min(score, 1.0)
    
    async def _calculate_frequency_score(self, numbers: List[int], lottery_type: LotteryType) -> float:
        """Calculate frequency-based score"""
        
        frequency_data = await self._get_frequency_data(lottery_type)
        
        if not frequency_data:
            return 0.5
        
        # Calculate average frequency percentile
        total_score = 0
        for number in numbers:
            freq_percentile = frequency_data.get(number, 0.5)
            total_score += freq_percentile
        
        return total_score / len(numbers)
    
    async def _calculate_statistical_score(self, numbers: List[int], lottery_type: LotteryType) -> float:
        """Calculate statistical significance score"""
        
        # Mock statistical analysis
        score = 0.5
        
        # Check for statistical patterns
        mean_number = sum(numbers) / len(numbers)
        expected_mean = 18.5  # For Kabala (1-36 range)
        
        if abs(mean_number - expected_mean) <= 3:
            score += 0.2
        
        # Check standard deviation
        std_dev = np.std(numbers)
        expected_std = 10.5  # Expected for random selection
        
        if abs(std_dev - expected_std) <= 2:
            score += 0.15
        
        return min(score, 1.0)
    
    async def _generate_analysis(self, series: List[LotterySeries], lottery_type: LotteryType) -> Dict[str, Any]:
        """Generate comprehensive analysis"""
        
        analysis = {
            "prediction_quality": {
                "avg_confidence": sum(s.confidence for s in series) / len(series),
                "confidence_range": [min(s.confidence for s in series), max(s.confidence for s in series)],
                "pattern_consistency": sum(s.pattern_score for s in series) / len(series)
            },
            "number_analysis": {
                "most_frequent": await self._get_most_frequent_numbers(series),
                "least_frequent": await self._get_least_frequent_numbers(series),
                "hot_numbers": await self._identify_hot_numbers(lottery_type),
                "cold_numbers": await self._identify_cold_numbers(lottery_type)
            },
            "statistical_summary": {
                "avg_sum": sum(sum(s.numbers) for s in series) / len(series),
                "sum_range": [min(sum(s.numbers) for s in series), max(sum(s.numbers) for s in series)],
                "odd_even_distribution": await self._analyze_odd_even_distribution(series)
            },
            "historical_context": await self._get_historical_context(lottery_type),
            "market_insights": await self._get_market_insights(lottery_type)
        }
        
        return analysis
    
    async def _generate_recommendations(self, series: List[LotterySeries], analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Confidence-based recommendations
        avg_confidence = analysis["prediction_quality"]["avg_confidence"]
        if avg_confidence > 0.8:
            recommendations.append("High confidence predictions - consider playing multiple series")
        elif avg_confidence < 0.6:
            recommendations.append("Lower confidence - recommend conservative play or wait for better predictions")
        
        # Pattern-based recommendations
        pattern_consistency = analysis["prediction_quality"]["pattern_consistency"]
        if pattern_consistency > 0.7:
            recommendations.append("Strong pattern matching detected - predictions align well with historical trends")
        
        # Statistical recommendations
        hot_numbers = analysis["number_analysis"]["hot_numbers"]
        if hot_numbers:
            recommendations.append(f"Consider including hot numbers: {', '.join(map(str, hot_numbers[:3]))}")
        
        cold_numbers = analysis["number_analysis"]["cold_numbers"]
        if cold_numbers:
            recommendations.append(f"Overdue numbers to watch: {', '.join(map(str, cold_numbers[:3]))}")
        
        # Sum analysis
        avg_sum = analysis["statistical_summary"]["avg_sum"]
        if avg_sum < 90:
            recommendations.append("Predictions favor lower number ranges")
        elif avg_sum > 120:
            recommendations.append("Predictions favor higher number ranges")
        
        return recommendations
    
    # Helper methods for data retrieval and caching
    
    async def _get_historical_draws(self, lottery_type: LotteryType) -> List[List[int]]:
        """Get historical lottery draws"""
        # Mock historical data
        return [
            [1, 7, 14, 21, 28, 35],
            [3, 9, 16, 23, 30, 36],
            [2, 8, 15, 22, 29, 34],
            # ... more historical draws
        ]
    
    async def _analyze_patterns(self, lottery_type: LotteryType) -> Dict[str, Any]:
        """Analyze historical patterns"""
        return {
            "consecutive_tendency": 0.3,
            "odd_even_balance": 0.52,
            "avg_consecutive": 1.2,
            "avg_sum": 105.5,
            "range_distribution": {"low": 0.35, "mid": 0.35, "high": 0.30}
        }
    
    async def _get_frequency_data(self, lottery_type: LotteryType) -> Dict[int, float]:
        """Get number frequency data"""
        # Mock frequency data (percentiles)
        return {i: np.random.beta(2, 2) for i in range(1, 37)}
    
    async def _load_historical_data(self):
        """Load historical lottery data"""
        self.historical_data = {
            LotteryType.KABALA: []  # Would load from database/files
        }
    
    async def _initialize_models(self):
        """Initialize ML models"""
        self.models = {
            "transformer": None,  # Would load actual models
            "statistical": None,
            "pattern": None
        }
    
    async def _load_pattern_cache(self):
        """Load pattern analysis cache"""
        self.pattern_cache = {}
    
    async def _cache_prediction_result(self, result: PredictionResult, lottery_type: str):
        """Cache prediction result"""
        if self.redis:
            try:
                cache_key = f"prediction:{lottery_type}:{datetime.now().strftime('%Y%m%d_%H')}"
                cache_data = {
                    "series": [s.__dict__ for s in result.series],
                    "analysis": result.analysis,
                    "recommendations": result.recommendations,
                    "generated_at": result.generated_at.isoformat()
                }
                
                await self.redis.setex(cache_key, 3600, json.dumps(cache_data, default=str))
                
            except Exception as e:
                logger.warning(f"Failed to cache prediction result: {e}")
    
    async def _fallback_prediction(self, config: Dict[str, Any]) -> List[int]:
        """Fallback prediction using random selection"""
        number_range = config["number_range"]
        series_length = config["series_length"]
        
        available_numbers = list(range(number_range[0], number_range[1] + 1))
        return sorted(np.random.choice(available_numbers, series_length, replace=False))
    
    # Additional helper methods would be implemented here...
    
    async def get_prediction_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user prediction history"""
        try:
            if self.redis:
                history_key = f"user_predictions:{user_id}"
                history = await self.redis.lrange(history_key, 0, limit-1)
                return [json.loads(item) for item in history]
            return []
        except Exception as e:
            logger.warning(f"Failed to get prediction history: {e}")
            return []
    
    async def update_prediction_result(self, prediction_id: str, actual_results: List[int]):
        """Update prediction with actual lottery results for learning"""
        try:
            # This would update the models with actual results for continuous learning
            logger.info(f"Updating prediction {prediction_id} with results: {actual_results}")
            
            # Calculate accuracy
            # Update model weights
            # Store performance metrics
            
        except Exception as e:
            logger.error(f"Failed to update prediction result: {e}")