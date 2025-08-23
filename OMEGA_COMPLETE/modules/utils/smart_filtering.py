"""Smart filtering para prevenir combinaciones vacías"""
import numpy as np
import random
import logging

logger = logging.getLogger(__name__)


def smart_filtering_with_fallback(combinations, filters, min_required=3):
    """
    Filtrado inteligente con fallback automático para evitar listas vacías
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    if not combinations:
        logger.warning("⚠️ No hay combinaciones para filtrar")
        return generate_fallback_combinations(min_required)
    
    # Aplicar filtros progresivamente
    filtered = apply_progressive_filters(combinations, filters)
    
    # Si quedan muy pocas, relajar filtros
    if len(filtered) < min_required:
        logger.warning(f"⚠️ Solo {len(filtered)} combinaciones tras filtros. Relajando...")
        filtered = apply_relaxed_filters(combinations, filters, min_required)
    
    # Si aún no hay suficientes, usar combinaciones originales + nuevas
    if len(filtered) < min_required:
        logger.warning("⚠️ Usando combinaciones originales + fallbacks")
        fallback_needed = min_required - len(filtered)
        fallbacks = generate_fallback_combinations(fallback_needed)
        filtered.extend(fallbacks)
    
    return filtered[:min_required * 2]  # Retornar hasta el doble para tener opciones

def apply_progressive_filters(combinations, filters):
    """Aplica filtros progresivamente, manteniendo siempre algunas combinaciones"""
    if not filters:
        return combinations
    
    results = combinations.copy()
    
    # Orden de filtros por severidad (menos restrictivo a más restrictivo)
    filter_order = ['basic_validation', 'range_filters', 'pattern_filters', 'advanced_filters']
    
    for filter_name in filter_order:
        if filter_name in filters and results:
            temp_filtered = apply_single_filter(results, filters[filter_name])
            
            # Solo aplicar el filtro si deja al menos 1 combinación
            if temp_filtered:
                results = temp_filtered
            else:
                logger.warning(f"⚠️ Filtro {filter_name} demasiado restrictivo, omitiendo")
    
    return results

def apply_relaxed_filters(combinations, filters, min_required):
    """Aplica versiones relajadas de los filtros"""
    relaxed_combinations = []
    
    for combo in combinations:
        passes_relaxed = True
        
        # Aplicar solo filtros básicos críticos
        if not basic_combination_validation(combo):
            passes_relaxed = False
        
        if passes_relaxed:
            relaxed_combinations.append(combo)
        
        if len(relaxed_combinations) >= min_required:
            break
    
    return relaxed_combinations

def basic_combination_validation(combination):
    """Validación básica que toda combinación debe pasar"""
    try:
        if not combination or 'combination' not in combination:
            return False
        
        numbers = combination['combination']
        
        # Debe tener exactamente 6 números
        if len(numbers) != 6:
            return False
        
        # Números deben estar en rango válido (1-40)
        if not all(1 <= n <= 40 for n in numbers):
            return False
        
        # No debe tener duplicados
        if len(set(numbers)) != 6:
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error en validación básica: {e}")
        return False

def apply_single_filter(combinations, filter_config):
    """Aplica un filtro específico"""
    try:
        filtered = []
        for combo in combinations:
            if evaluate_filter_condition(combo, filter_config):
                filtered.append(combo)
        return filtered
    except Exception as e:
        logger.error(f"Error aplicando filtro: {e}")
        return combinations  # Return original on error

def evaluate_filter_condition(combination, filter_config):
    """Evalúa si una combinación pasa un filtro específico"""
    try:
        # Implementación básica - expandir según necesidades
        numbers = combination.get('combination', [])
        
        # Filtro por suma
        if 'sum_range' in filter_config:
            combo_sum = sum(numbers)
            min_sum, max_sum = filter_config['sum_range']
            if not (min_sum <= combo_sum <= max_sum):
                return False
        
        # Filtro por números pares/impares
        if 'odd_even_ratio' in filter_config:
            odd_count = sum(1 for n in numbers if n % 2 == 1)
            ratio = odd_count / len(numbers)
            target_ratio = filter_config['odd_even_ratio']
            if abs(ratio - target_ratio) > 0.3:  # Tolerancia del 30%
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error evaluando condición de filtro: {e}")
        return True  # Pass by default on error

def generate_fallback_combinations(count):
    """Genera combinaciones de fallback cuando el filtrado es demasiado restrictivo"""
    import random
    
    fallback_combinations = []
    
    for i in range(count):
        # Generar combinación balanceada
        numbers = sorted(random.sample(range(1, 41), 6))
        
        combination = {
            'combination': numbers,
            'source': 'fallback_filter',
            'score': 0.6,  # Score moderado
            'svi_score': 0.5,
            'metrics': {'fallback_reason': 'filters_too_restrictive'},
            'normalized': 0.0
        }
        
        fallback_combinations.append(combination)
    
    return fallback_combinations

def optimize_filter_thresholds(combinations, target_count=10):
    """Optimiza automáticamente los umbrales de filtros para mantener combinaciones suficientes"""
    import numpy as np
    
    if len(combinations) <= target_count:
        return combinations
    
    # Calcular percentiles para establecer umbrales dinámicos
    scores = [c.get('score', 0.5) for c in combinations]
    svi_scores = [c.get('svi_score', 0.5) for c in combinations]
    
    # Usar percentil dinámico basado en target_count
    percentile = max(50, 100 - (target_count * 100 / len(combinations)))
    
    score_threshold = np.percentile(scores, percentile)
    svi_threshold = np.percentile(svi_scores, percentile)
    
    # Filtrar usando umbrales dinámicos
    filtered = [
        c for c in combinations 
        if c.get('score', 0) >= score_threshold or c.get('svi_score', 0) >= svi_threshold
    ]
    
    # Si aún son muchas, tomar las mejores
    if len(filtered) > target_count * 2:
        filtered.sort(key=lambda x: x.get('score', 0) + x.get('svi_score', 0), reverse=True)
        filtered = filtered[:target_count * 2]
    
    return filtered
