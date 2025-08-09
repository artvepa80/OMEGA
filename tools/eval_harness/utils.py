from __future__ import annotations

import json
import os
import platform
import random
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, Optional


def set_all_seeds(seed: int) -> None:
    """Set seeds across os, random, numpy and, if available, torch and tf.

    This aims for determinism where possible without adding heavy deps.
    """
    try:
        os.environ["PYTHONHASHSEED"] = str(seed)
    except Exception:
        pass

    random.seed(seed)

    try:
        import numpy as np  # type: ignore

        np.random.seed(seed)
    except Exception:
        pass

    # Optional hooks
    try:
        import torch  # type: ignore

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except Exception:
        pass

    try:
        import tensorflow as tf  # type: ignore

        tf.random.set_seed(seed)
    except Exception:
        pass


def ensure_dir(path: str) -> None:
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def timestamped_run_dir(base_dir: str) -> str:
    """Create a timestamped run directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(base_dir, f"run_{timestamp}")
    ensure_dir(run_dir)
    return run_dir


def save_json(data: Dict[str, Any], path: str) -> None:
    """Save data as JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def collect_env_manifest() -> Dict[str, Any]:
    """Collect environment information for reproducibility."""
    manifest = {
        "timestamp": datetime.now().isoformat(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
        },
        "packages": {},
        "git": {},
    }

    # Try to collect package versions
    try:
        import pkg_resources

        installed_packages = [d for d in pkg_resources.working_set]
        manifest["packages"] = {pkg.project_name: pkg.version for pkg in installed_packages}
    except Exception:
        pass

    # Try to collect git info
    try:
        git_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
        manifest["git"]["commit"] = git_hash
    except Exception:
        pass

    try:
        git_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
        manifest["git"]["branch"] = git_branch
    except Exception:
        pass

    try:
        git_status = subprocess.check_output(["git", "status", "--porcelain"], stderr=subprocess.DEVNULL).decode().strip()
        manifest["git"]["dirty"] = bool(git_status)
    except Exception:
        pass

    return manifest