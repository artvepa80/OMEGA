import os
import random
from typing import Optional

from utils.logging import get_logger

logger = get_logger(__name__)


def maybe_seed_from_env(env_var: str = "OMEGA_SEED") -> Optional[int]:
    """
    If env var is set, seed Python, NumPy, and Torch (if available).
    Returns the seed used, or None if not set/invalid.
    """
    value = os.getenv(env_var)
    if not value:
        return None
    try:
        seed = int(value)
    except Exception:
        logger.warning(f"Invalid seed value in {env_var}: {value}")
        return None

    try:
        random.seed(seed)
        try:
            import numpy as np
            np.random.seed(seed)
        except Exception:
            logger.debug("NumPy not available for seeding")
        try:
            import torch
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
        except Exception:
            logger.debug("Torch not available for seeding")
        logger.info(f"Deterministic seed initialized from env: {env_var}={seed}")
    except Exception:
        logger.error("Seeding failed", exc_info=True)
        return None

    return seed


