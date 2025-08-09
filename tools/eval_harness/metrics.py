from __future__ import annotations

from typing import Iterable, List, Sequence
import itertools
import math


def matches_per_combo(pred: Sequence[int], truth: Sequence[int]) -> int:
    """Count matching numbers between prediction and truth."""
    return len(set(map(int, pred)) & set(map(int, truth)))


def hit_at_k(preds: Sequence[Sequence[int]], truth: Sequence[int], k: int, r: int = 6) -> bool:
    """Check if any of top-k predictions has at least r matches with truth."""
    topk = list(itertools.islice(preds, k))
    truth_set = set(map(int, truth))
    return any(len(set(map(int, p)) & truth_set) >= r for p in topk)


def hit_top1(preds: Sequence[Sequence[int]], truth: Sequence[int], r: int = 6) -> bool:
    """Check if top-1 prediction has at least r matches."""
    return hit_at_k(preds, truth, k=1, r=r)


def best_at_n(preds: Sequence[Sequence[int]], truth: Sequence[int], n: int = 10) -> int:
    """Find best number of matches among top-n predictions."""
    topn = list(itertools.islice(preds, n))
    truth_set = set(map(int, truth))
    return max((len(set(map(int, p)) & truth_set) for p in topn), default=0)


def jaccard_mean(preds: Sequence[Sequence[int]]) -> float:
    """Calculate mean Jaccard similarity between all prediction pairs."""
    preds = list(preds)
    if len(preds) < 2:
        return 0.0
    
    total = 0.0
    count = 0
    for i in range(len(preds)):
        for j in range(i + 1, len(preds)):
            a = set(map(int, preds[i]))
            b = set(map(int, preds[j]))
            jaccard = len(a & b) / len(a | b) if (a | b) else 0.0
            total += jaccard
            count += 1
    
    return total / count if count > 0 else 0.0


def coverage(preds: Sequence[Sequence[int]], num_range: int = 40) -> float:
    """Calculate how many unique numbers are covered by predictions."""
    all_nums = set()
    for pred in preds:
        all_nums.update(map(int, pred))
    return len(all_nums) / num_range


def diversity(preds: Sequence[Sequence[int]]) -> float:
    """Calculate diversity as 1 - mean_jaccard (higher = more diverse)."""
    return 1.0 - jaccard_mean(preds)


def compound_score(params: dict) -> float:
    """Calculate compound score with configurable weights."""
    # Default weights
    weights = {
        "w_hit6": params.get("w_hit6", 0.3),
        "w_hit5": params.get("w_hit5", 0.25), 
        "w_hit4": params.get("w_hit4", 0.2),
        "w_best": params.get("w_best", 0.15),
        "w_div": params.get("w_div", 0.1),
    }
    
    # Extract metrics from params
    hit6 = params.get("hit6", 0)
    hit5 = params.get("hit5", 0) 
    hit4 = params.get("hit4", 0)
    best = params.get("best", 0) / 6.0  # Normalize to [0,1]
    diversity_score = params.get("diversity", 0)
    
    # Calculate weighted sum
    score = (
        weights["w_hit6"] * hit6 +
        weights["w_hit5"] * hit5 +
        weights["w_hit4"] * hit4 +
        weights["w_best"] * best +
        weights["w_div"] * diversity_score
    )
    
    return score


def points_weighted(matches: int) -> float:
    """Convert matches to weighted points for visualization."""
    if matches >= 6:
        return 100.0  # Jackpot
    elif matches == 5:
        return 50.0
    elif matches == 4:
        return 10.0
    elif matches == 3:
        return 2.0
    else:
        return 0.0


def calculate_all_metrics(preds: Sequence[Sequence[int]], truth: Sequence[int]) -> dict:
    """Calculate all metrics for a given prediction set and truth."""
    truth_set = set(map(int, truth))
    
    # Hit metrics
    hit6 = hit_at_k(preds, truth, k=1, r=6)
    hit5 = hit_at_k(preds, truth, k=1, r=5) 
    hit4 = hit_at_k(preds, truth, k=1, r=4)
    
    # Best matches
    best = best_at_n(preds, truth, n=10)
    
    # Diversity metrics
    div = diversity(preds)
    cov = coverage(preds)
    
    # Points for top prediction
    top_matches = matches_per_combo(list(preds)[0] if preds else [], truth) if preds else 0
    points = points_weighted(top_matches)
    
    # Compound score
    compound = compound_score({
        "hit6": int(hit6),
        "hit5": int(hit5), 
        "hit4": int(hit4),
        "best": best,
        "diversity": div,
    })
    
    return {
        "hit6": hit6,
        "hit5": hit5,
        "hit4": hit4,
        "best": best,
        "diversity": div,
        "coverage": cov,
        "points": points,
        "compound": compound,
        "top_matches": top_matches,
    }