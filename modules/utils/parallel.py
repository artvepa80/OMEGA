from __future__ import annotations

from joblib import Parallel, delayed
import traceback
from typing import Any, Callable, Iterable, List


def safe_parallel_map(func: Callable[[Any], Any], items: Iterable[Any], n_jobs: int = -1, backend: str = "loky") -> List[Any]:
    try:
        return Parallel(n_jobs=n_jobs, backend=backend)(delayed(func)(x) for x in items)
    except Exception:
        try:
            items = list(items)
            return Parallel(n_jobs=min(8, max(1, len(items))), backend="threading")(delayed(func)(x) for x in items)
        except Exception:
            print("[PARALLEL] Fallback sequential:\n", traceback.format_exc())
            return [func(x) for x in items]


