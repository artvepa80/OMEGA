"""
OMEGA Flow Manager - Integrated with Real OMEGA Prediction Models
Core lottery prediction system using actual HybridOmegaPredictor and consensus engine
"""

import asyncio
import logging
import json
import numpy as np
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

# Add the OMEGA core modules to path
omega_path = Path(__file__).parent.parent
sys.path.insert(0, str(omega_path))

# Import real OMEGA prediction engines
from core.predictor import HybridOmegaPredictor
from core.consensus_engine import generar_combinaciones_consenso
from utils.validation import clean_historial_df

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

@dataclass
class LotterySeries:
    numbers: List[int]
    confidence: float
    pattern_score: float
    frequency_score: float
    statistical_score: float
    source: str
    svi_score: float
    meta_data: Dict[str, Any]

@dataclass
class PredictionResult:
    series: List[LotterySeries]
    analysis: Dict[str, Any]
    recommendations: List[str]
    generated_at: datetime
    expires_at: datetime
    disclaimer: str

class OmegaFlowIntegrated:
    """OMEGA flow manager using real prediction models"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.predictor = None
        self.historical_data = None
        
        # Statistical analysis disclaimer
        self.disclaimer = """
        OMEGA AI Statistical Analysis System
        
        IMPORTANT DISCLAIMER:
        This system performs statistical analysis based on historical lottery data.
        It presents mathematical patterns and probabilities, NOT recommendations.
        
        - Results are based on data analysis and mathematical modeling
        - Past performance does not guarantee future results
        - This is NOT gambling advice or recommendations
        - Users must make their own informed decisions
        - Lottery outcomes are random and unpredictable
        - Play responsibly and within your means
        
        OMEGA presents FACTS and STATISTICAL ANALYSIS only.
        """
        
        # Configuration for different lottery types
        self.lottery_configs = {
            LotteryType.KABALA: {
                "number_range": (1, 40),
                "series_length": 6,
                "draws_per_week": 2,
                "data_file": "data/historial_kabala_github.csv"
            },
            LotteryType.POWERBALL: {
                "main_range": (1, 69),
                "power_range": (1, 26),
                "series_length": 5,
                "powerball": True
            }
        }
    
    async def initialize(self):
        """Initialize OMEGA integrated system"""
        try:
            # Load historical data for Kabala lottery
            data_path = os.path.join(str(omega_path), "data", "historial_kabala_github.csv")
            
            if os.path.exists(data_path):
                self.historical_data = pd.read_csv(data_path)
                logger.info(f"Loaded historical data: {self.historical_data.shape[0]} records")
            else:
                logger.warning(f"Historical data file not found: {data_path}")
                # Create dummy data for testing
                self.historical_data = pd.DataFrame({
                    'fecha': pd.date_range('2020-01-01', periods=1000, freq='3D'),
                    'Bolilla 1': np.random.randint(1, 41, 1000),
                    'Bolilla 2': np.random.randint(1, 41, 1000),
                    'Bolilla 3': np.random.randint(1, 41, 1000),
                    'Bolilla 4': np.random.randint(1, 41, 1000),
                    'Bolilla 5': np.random.randint(1, 41, 1000),
                    'Bolilla 6': np.random.randint(1, 41, 1000)
                })
                # Ensure no duplicates within rows
                for i in range(len(self.historical_data)):
                    row_numbers = list(range(1, 41))
                    selected = np.random.choice(row_numbers, 6, replace=False)
                    self.historical_data.iloc[i, 1:7] = sorted(selected)
            
            # Clean historical data
            self.historical_data = clean_historial_df(self.historical_data)
            
            # Initialize the real OMEGA predictor
            self.predictor = HybridOmegaPredictor(
                historial_df=self.historical_data,
                cantidad_final=30,
                perfil_svi='default',
                logger=logger,
                seed=42
            )
            
            logger.info("OMEGA Integrated Flow Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OMEGA Integrated Flow: {e}")
            raise
    
    async def generate_series(self, 
                            lottery_type: str, 
                            series_count: int = 5,
                            filters: Dict[str, Any] = None,
                            user_preferences: Dict[str, Any] = None) -> PredictionResult:
        """Generate lottery series using real OMEGA prediction models"""
        
        try:
            lottery_enum = LotteryType(lottery_type)
            config = self.lottery_configs.get(lottery_enum)
            
            if not config:
                raise ValueError(f"Unsupported lottery type: {lottery_type}")
            
            if not self.predictor:
                raise RuntimeError("OMEGA predictor not initialized")
            
            # Map user preferences to OMEGA parameters
            mode = user_preferences.get('mode', 'default') if user_preferences else 'default'
            perfil_svi = self._map_prediction_mode(mode)
            
            # Update predictor configuration
            self.predictor.perfil_svi = perfil_svi
            self.predictor.cantidad_final = max(series_count, 10)
            
            logger.info(f"Generating {series_count} series using OMEGA prediction engine")
            
            # Run the real OMEGA prediction models
            omega_results = await self._run_omega_prediction()
            
            if not omega_results:
                raise RuntimeError("OMEGA prediction engine returned no results")
            
            # Convert OMEGA results to our format
            series_predictions = await self._convert_omega_results(
                omega_results, series_count, filters, config
            )
            
            # Generate comprehensive analysis
            analysis = await self._generate_analysis(series_predictions, lottery_enum)
            
            # Generate recommendations with disclaimer
            recommendations = await self._generate_statistical_recommendations(
                series_predictions, analysis
            )
            
            # Create result with disclaimer
            result = PredictionResult(
                series=series_predictions,
                analysis=analysis,
                recommendations=recommendations,
                generated_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=24),
                disclaimer=self.disclaimer
            )
            
            # Cache result
            await self._cache_prediction_result(result, lottery_type)
            
            logger.info(f"Generated {len(series_predictions)} statistical predictions")
            return result
            
        except Exception as e:
            logger.error(f"Statistical analysis generation failed: {e}")
            raise
    
    async def _run_omega_prediction(self) -> List[Dict[str, Any]]:
        """Run the real OMEGA prediction engine"""
        try:
            # Run OMEGA prediction models in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            omega_results = await loop.run_in_executor(
                None, 
                self.predictor.run_all_models
            )
            
            logger.info(f"OMEGA engine generated {len(omega_results)} predictions")
            return omega_results
            
        except Exception as e:
            logger.error(f"OMEGA prediction engine error: {e}")
            return []
    
    async def _convert_omega_results(self, 
                                   omega_results: List[Dict[str, Any]], 
                                   series_count: int,
                                   filters: Dict[str, Any],
                                   config: Dict[str, Any]) -> List[LotterySeries]:
        """Convert OMEGA prediction results to API format"""
        
        series_predictions = []
        
        # Take the top predictions from OMEGA
        top_results = omega_results[:series_count]
        
        for i, result in enumerate(top_results):
            try:
                # Extract OMEGA prediction data
                numbers = result.get('combination', [])
                source = result.get('source', 'omega_ensemble')
                score = result.get('score', 0.0)
                normalized_score = result.get('normalized', score)
                svi_score = result.get('svi_score', score)
                metrics = result.get('metrics', {})
                
                # Apply user filters if specified
                if filters:
                    numbers = await self._apply_user_filters(numbers, filters, config)
                
                # Ensure numbers are in valid range and format
                numbers = [int(n) for n in numbers if 1 <= int(n) <= config["number_range"][1]]
                numbers = sorted(list(set(numbers)))  # Remove duplicates and sort
                
                # Ensure we have the right number count
                if len(numbers) != config["series_length"]:
                    # Fill or trim to correct length
                    if len(numbers) < config["series_length"]:
                        available = [n for n in range(1, config["number_range"][1] + 1) 
                                   if n not in numbers]
                        needed = config["series_length"] - len(numbers)
                        additional = np.random.choice(available, needed, replace=False)
                        numbers.extend(additional)
                        numbers = sorted(numbers)
                    else:
                        numbers = numbers[:config["series_length"]]
                
                # Calculate confidence based on OMEGA scores
                confidence = min(0.95, max(0.3, normalized_score))
                pattern_score = metrics.get('pattern_score', svi_score)
                frequency_score = metrics.get('frequency_score', score * 0.8)
                statistical_score = metrics.get('statistical_score', score * 0.9)
                
                # Create series object
                series = LotterySeries(
                    numbers=numbers,
                    confidence=confidence,
                    pattern_score=pattern_score,
                    frequency_score=frequency_score,
                    statistical_score=statistical_score,
                    source=f"omega_{source}",
                    svi_score=svi_score,
                    meta_data={
                        "omega_metrics": metrics,
                        "generation_method": "omega_hybrid_predictor",
                        "model_version": "10.1",
                        "series_index": i,
                        "original_omega_score": score,
                        "analysis_type": "statistical_pattern_recognition"
                    }
                )
                
                series_predictions.append(series)
                
            except Exception as e:
                logger.warning(f"Error converting OMEGA result {i}: {e}")
                continue
        
        # Sort by confidence
        series_predictions.sort(key=lambda x: x.confidence, reverse=True)
        
        return series_predictions
    
    async def _apply_user_filters(self, 
                                numbers: List[int], 
                                filters: Dict[str, Any], 
                                config: Dict[str, Any]) -> List[int]:
        """Apply user-defined filters to predictions"""
        
        if not filters:
            return numbers
        
        filtered_numbers = list(numbers)
        
        # Exclude specific numbers
        if "exclude_numbers" in filters:
            exclude = filters["exclude_numbers"]
            filtered_numbers = [n for n in filtered_numbers if n not in exclude]
        
        # Include specific numbers (add if not present)
        if "include_numbers" in filters:
            include = filters["include_numbers"]
            for num in include:
                if num not in filtered_numbers and 1 <= num <= config["number_range"][1]:
                    filtered_numbers.append(num)
        
        # Odd/even ratio filter
        if "odd_even_ratio" in filters:
            target_ratio = filters["odd_even_ratio"]  # e.g., 0.5 for 50% odd
            filtered_numbers = await self._adjust_odd_even_ratio(filtered_numbers, target_ratio, config)
        
        return sorted(list(set(filtered_numbers)))
    
    async def _adjust_odd_even_ratio(self, 
                                   numbers: List[int], 
                                   target_ratio: float,
                                   config: Dict[str, Any]) -> List[int]:
        """Adjust numbers to meet odd/even ratio"""
        
        if not numbers:
            return numbers
        
        current_odd = sum(1 for n in numbers if n % 2 == 1)
        current_ratio = current_odd / len(numbers)
        series_length = config["series_length"]
        
        if abs(current_ratio - target_ratio) <= 0.1:  # Close enough
            return numbers
        
        # Adjust towards target ratio
        target_odd_count = int(series_length * target_ratio)
        
        if current_odd < target_odd_count:
            # Need more odd numbers
            even_nums = [n for n in numbers if n % 2 == 0]
            if even_nums:
                # Replace some even with odd
                available_odd = [n for n in range(1, config["number_range"][1] + 1, 2) 
                               if n not in numbers]
                if available_odd:
                    to_replace = min(len(even_nums), target_odd_count - current_odd, len(available_odd))
                    for i in range(to_replace):
                        numbers.remove(even_nums[i])
                        numbers.append(available_odd[i])
        
        elif current_odd > target_odd_count:
            # Need fewer odd numbers
            odd_nums = [n for n in numbers if n % 2 == 1]
            if odd_nums:
                # Replace some odd with even
                available_even = [n for n in range(2, config["number_range"][1] + 1, 2) 
                                if n not in numbers]
                if available_even:
                    to_replace = min(len(odd_nums), current_odd - target_odd_count, len(available_even))
                    for i in range(to_replace):
                        numbers.remove(odd_nums[i])
                        numbers.append(available_even[i])
        
        return sorted(numbers)
    
    def _map_prediction_mode(self, mode: str) -> str:
        """Map API prediction mode to OMEGA SVI profile"""
        mapping = {
            'balanced': 'default',
            'conservative': 'conservative',
            'aggressive': 'aggressive',
            'default': 'default'
        }
        return mapping.get(mode, 'default')
    
    async def _generate_analysis(self, 
                               series: List[LotterySeries], 
                               lottery_type: LotteryType) -> Dict[str, Any]:
        """Generate comprehensive statistical analysis"""
        
        if not series:
            return {"error": "No series to analyze"}
        
        # Extract all numbers from all series
        all_numbers = []
        for s in series:
            all_numbers.extend(s.numbers)
        
        # Statistical analysis
        analysis = {
            "prediction_quality": {
                "avg_confidence": sum(s.confidence for s in series) / len(series),
                "confidence_range": [min(s.confidence for s in series), max(s.confidence for s in series)],
                "pattern_consistency": sum(s.pattern_score for s in series) / len(series),
                "avg_svi_score": sum(s.svi_score for s in series) / len(series)
            },
            "number_analysis": {
                "most_frequent": await self._get_most_frequent_numbers(all_numbers),
                "least_frequent": await self._get_least_frequent_numbers(all_numbers),
                "number_distribution": await self._analyze_number_distribution(all_numbers),
                "range_coverage": await self._analyze_range_coverage(all_numbers)
            },
            "statistical_summary": {
                "avg_sum": sum(sum(s.numbers) for s in series) / len(series),
                "sum_range": [min(sum(s.numbers) for s in series), max(sum(s.numbers) for s in series)],
                "odd_even_distribution": await self._analyze_odd_even_distribution(series),
                "consecutive_numbers": await self._analyze_consecutive_patterns(series)
            },
            "model_sources": await self._analyze_model_sources(series),
            "disclaimer_info": {
                "analysis_type": "statistical_pattern_recognition",
                "data_based": True,
                "recommendation_type": "statistical_facts_only"
            }
        }
        
        return analysis
    
    async def _generate_statistical_recommendations(self, 
                                                  series: List[LotterySeries], 
                                                  analysis: Dict[str, Any]) -> List[str]:
        """Generate statistical analysis recommendations (not gambling advice)"""
        
        recommendations = [
            "📊 STATISTICAL ANALYSIS RESULTS:",
            "",
            "⚠️  IMPORTANT: These are statistical patterns, not recommendations.",
            "🎲 Lottery outcomes remain random regardless of historical patterns.",
            ""
        ]
        
        # Confidence analysis
        avg_confidence = analysis["prediction_quality"]["avg_confidence"]
        if avg_confidence > 0.8:
            recommendations.append("📈 High statistical confidence detected in pattern analysis")
        elif avg_confidence > 0.6:
            recommendations.append("📊 Moderate statistical confidence in identified patterns") 
        else:
            recommendations.append("📉 Lower statistical confidence - patterns less defined")
        
        # Pattern analysis
        pattern_consistency = analysis["prediction_quality"]["pattern_consistency"]
        if pattern_consistency > 0.7:
            recommendations.append("🔍 Strong historical pattern consistency observed")
        
        # Statistical observations
        most_frequent = analysis["number_analysis"]["most_frequent"]
        if most_frequent:
            recommendations.append(f"🔢 Most frequent numbers in analysis: {', '.join(map(str, most_frequent[:5]))}")
        
        # Sum analysis
        avg_sum = analysis["statistical_summary"]["avg_sum"]
        if avg_sum < 90:
            recommendations.append("📊 Statistical analysis indicates lower number range bias")
        elif avg_sum > 140:
            recommendations.append("📊 Statistical analysis indicates higher number range bias")
        
        # Model sources
        model_info = analysis.get("model_sources", {})
        if model_info:
            recommendations.append("🤖 Predictions generated using:")
            for source, count in list(model_info.items())[:3]:
                recommendations.append(f"   • {source}: {count} predictions")
        
        recommendations.extend([
            "",
            "🎯 REMEMBER:",
            "• This analysis shows statistical patterns only",
            "• Past performance does not predict future results", 
            "• All lottery draws are independent random events",
            "• Use this information for educational purposes only",
            "• Make your own informed decisions"
        ])
        
        return recommendations
    
    async def _analyze_model_sources(self, series: List[LotterySeries]) -> Dict[str, int]:
        """Analyze which OMEGA models contributed to predictions"""
        source_count = {}
        for s in series:
            source = s.source
            source_count[source] = source_count.get(source, 0) + 1
        return dict(sorted(source_count.items(), key=lambda x: x[1], reverse=True))
    
    async def _get_most_frequent_numbers(self, numbers: List[int]) -> List[int]:
        """Get most frequently appearing numbers"""
        from collections import Counter
        counter = Counter(numbers)
        return [num for num, count in counter.most_common(10)]
    
    async def _get_least_frequent_numbers(self, numbers: List[int]) -> List[int]:
        """Get least frequently appearing numbers"""
        from collections import Counter
        counter = Counter(numbers)
        return [num for num, count in counter.most_common()[-5:]][::-1]
    
    async def _analyze_number_distribution(self, numbers: List[int]) -> Dict[str, Any]:
        """Analyze distribution of numbers across ranges"""
        low = sum(1 for n in numbers if 1 <= n <= 13)
        mid = sum(1 for n in numbers if 14 <= n <= 26) 
        high = sum(1 for n in numbers if 27 <= n <= 40)
        total = len(numbers)
        
        return {
            "low_range": {"count": low, "percentage": low/total * 100 if total > 0 else 0},
            "mid_range": {"count": mid, "percentage": mid/total * 100 if total > 0 else 0}, 
            "high_range": {"count": high, "percentage": high/total * 100 if total > 0 else 0}
        }
    
    async def _analyze_range_coverage(self, numbers: List[int]) -> Dict[str, Any]:
        """Analyze how well numbers cover the full range"""
        unique_numbers = set(numbers)
        coverage_percentage = len(unique_numbers) / 40 * 100  # For 1-40 range
        
        return {
            "unique_numbers": len(unique_numbers),
            "total_predictions": len(numbers),
            "coverage_percentage": coverage_percentage,
            "gaps": await self._find_number_gaps(unique_numbers)
        }
    
    async def _find_number_gaps(self, numbers: set) -> List[int]:
        """Find gaps in number coverage"""
        all_numbers = set(range(1, 41))
        gaps = sorted(list(all_numbers - numbers))
        return gaps[:10]  # Return first 10 gaps
    
    async def _analyze_odd_even_distribution(self, series: List[LotterySeries]) -> Dict[str, Any]:
        """Analyze odd/even distribution across series"""
        total_odd = 0
        total_even = 0
        
        for s in series:
            odd_count = sum(1 for n in s.numbers if n % 2 == 1)
            even_count = len(s.numbers) - odd_count
            total_odd += odd_count
            total_even += even_count
        
        total = total_odd + total_even
        return {
            "odd_count": total_odd,
            "even_count": total_even,
            "odd_percentage": total_odd/total * 100 if total > 0 else 0,
            "even_percentage": total_even/total * 100 if total > 0 else 0
        }
    
    async def _analyze_consecutive_patterns(self, series: List[LotterySeries]) -> Dict[str, Any]:
        """Analyze consecutive number patterns"""
        consecutive_counts = []
        
        for s in series:
            consecutive = 0
            for i in range(len(s.numbers) - 1):
                if s.numbers[i+1] == s.numbers[i] + 1:
                    consecutive += 1
            consecutive_counts.append(consecutive)
        
        return {
            "avg_consecutive": sum(consecutive_counts) / len(consecutive_counts) if consecutive_counts else 0,
            "max_consecutive": max(consecutive_counts) if consecutive_counts else 0,
            "series_with_consecutive": sum(1 for c in consecutive_counts if c > 0)
        }
    
    async def _cache_prediction_result(self, result: PredictionResult, lottery_type: str):
        """Cache prediction result"""
        if self.redis:
            try:
                cache_key = f"omega_prediction:{lottery_type}:{datetime.now().strftime('%Y%m%d_%H')}"
                
                # Convert dataclasses to dict for JSON serialization
                cache_data = {
                    "series": [asdict(s) for s in result.series],
                    "analysis": result.analysis,
                    "recommendations": result.recommendations,
                    "generated_at": result.generated_at.isoformat(),
                    "disclaimer": result.disclaimer
                }
                
                await self.redis.setex(cache_key, 3600, json.dumps(cache_data, default=str))
                logger.info(f"Cached prediction result: {cache_key}")
                
            except Exception as e:
                logger.warning(f"Failed to cache prediction result: {e}")