from __future__ import annotations

from functools import lru_cache
from typing import Iterable, Tuple

from utils.logging import get_logger


logger = get_logger(__name__)


def _to_tuple(combination: Iterable[int]) -> Tuple[int, ...]:
    try:
        return tuple(sorted(int(x) for x in combination))
    except Exception:
        return tuple()


@lru_cache(maxsize=2048)
def is_suspicious_seed_pattern_cached(comb_tuple: Tuple[int, ...]) -> bool:
    """
    Fast-path cached predicate to detect suspicious RNG-like patterns.
    Heuristics: excessive arithmetic progression, too many extremes, low entropy proxy.
    Note: This is a lightweight guard; heavy checks should live in Ghost RNG modules.
    """
    if len(comb_tuple) != 6:
        return False

    # Arithmetic progression or near-progression
    diffs = [b - a for a, b in zip(comb_tuple, comb_tuple[1:])]
    if len(set(diffs)) <= 2:
        return True

    # Too many extremes (1..3 or 38..40)
    extremes = sum(1 for n in comb_tuple if n <= 3 or n >= 38)
    if extremes >= 4:
        return True

    # Low variety across decades (proxy for structure)
    decades = {n // 10 for n in comb_tuple}
    if len(decades) <= 2:
        return True

    return False


def is_suspicious_seed_pattern(combination: Iterable[int]) -> bool:
    """
    Public API required by spec. Wraps the cached fast-path.
    """
    comb_tuple = _to_tuple(combination)
    if not comb_tuple:
        return False
    try:
        return is_suspicious_seed_pattern_cached(comb_tuple)
    except Exception:
        # Never fail hard here
        logger.error("ghost_rng_observer fast-path failed", exc_info=True)
        return False


