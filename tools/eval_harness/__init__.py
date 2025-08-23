"""Evaluation Harness for OMEGA_PRO_AI_v10.1

This package provides a deterministic evaluation harness with:
- CLI entry points for backtesting and benchmarking
- Rolling window splits
- Metrics and reporting utilities

Phases are implemented incrementally. Initial skeleton focuses on a
stable CLI with reproducible seeds and environment manifests.
"""

__all__ = [
    "utils",
    "splits",
    "metrics", 
    "report",
    "backtest",
    "cli",
]