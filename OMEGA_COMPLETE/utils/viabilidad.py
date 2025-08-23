"""
SVI (Sistema de Viabilidad Inteligente) utilities
"""

import random
from typing import List, Union

def calcular_svi(
    combinacion: Union[str, List[int]], 
    perfil_rng: str = "moderado",
    validacion_ghost: bool = False,
    score_historico: float = 1.0
) -> float:
    """
    Calculate SVI (Sistema de Viabilidad Inteligente) score
    
    Args:
        combinacion: The lottery combination
        perfil_rng: Profile type (moderado, conservador, agresivo)
        validacion_ghost: Whether ghost RNG validation passed
        score_historico: Historical score
    
    Returns:
        SVI score between 0 and 1
    """
    
    try:
        # Parse combination
        if isinstance(combinacion, str):
            # Try to parse string representation
            nums = [int(x) for x in combinacion.strip('[]').split(',')]
        else:
            nums = list(combinacion)
        
        # Basic validation
        if len(nums) != 6 or not all(1 <= n <= 40 for n in nums):
            return 0.3  # Low score for invalid combination
        
        # Base SVI score
        base_score = 0.5
        
        # Pattern analysis
        odd_count = sum(1 for n in nums if n % 2 == 1)
        odd_ratio = odd_count / 6
        
        # Favor balanced odd/even ratio
        if 0.4 <= odd_ratio <= 0.6:
            base_score += 0.1
        
        # Range analysis
        low_count = sum(1 for n in nums if n <= 13)
        mid_count = sum(1 for n in nums if 14 <= n <= 26)
        high_count = sum(1 for n in nums if n >= 27)
        
        # Favor balanced range distribution
        if min(low_count, mid_count, high_count) >= 1:
            base_score += 0.1
        
        # Sum analysis
        total_sum = sum(nums)
        if 90 <= total_sum <= 150:  # Reasonable sum range
            base_score += 0.1
        
        # Consecutive numbers penalty
        consecutive = 0
        sorted_nums = sorted(nums)
        for i in range(len(sorted_nums) - 1):
            if sorted_nums[i+1] == sorted_nums[i] + 1:
                consecutive += 1
        
        if consecutive <= 2:  # Not too many consecutive
            base_score += 0.05
        
        # Ghost RNG bonus
        if validacion_ghost:
            base_score += 0.1
        
        # Historical score influence
        base_score += (score_historico - 1.0) * 0.1
        
        # Profile adjustments
        if perfil_rng == "conservador":
            base_score *= 0.9  # More conservative scoring
        elif perfil_rng == "agresivo":
            base_score *= 1.1  # More aggressive scoring
        
        # Clamp to valid range
        return max(0.1, min(1.0, base_score))
        
    except Exception as e:
        # Return neutral score on error
        return 0.5

def calcular_svi_individual(combinacion: List[int], perfil: str = "default") -> float:
    """Calculate individual SVI score for a combination"""
    return calcular_svi(combinacion, perfil_rng=perfil)