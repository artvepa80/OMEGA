from __future__ import annotations

import os
import random
from typing import Dict, List, Any, Sequence

import pandas as pd

from .utils import ensure_dir, set_all_seeds, save_json, collect_env_manifest
from .splits import rolling_windows
from .metrics import calculate_all_metrics


def load_data(path: str) -> pd.DataFrame:
    """Load lottery data from CSV file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")
    df = pd.read_csv(path)
    return df


def extract_truth_from_row(row: pd.Series) -> List[int]:
    """Extract truth numbers from a data row."""
    # Try common column patterns
    num_cols = [col for col in row.index if col.lower().startswith(('num', 'n')) and col[-1].isdigit()]
    if num_cols:
        nums = []
        for col in sorted(num_cols):
            try:
                nums.append(int(row[col]))
            except (ValueError, TypeError):
                continue
        if len(nums) >= 6:
            return nums[:6]
    
    # Fallback: look for columns with numeric names
    numeric_cols = [col for col in row.index if str(col).isdigit()]
    if numeric_cols:
        nums = []
        for col in sorted(numeric_cols, key=int):
            try:
                nums.append(int(row[col]))
            except (ValueError, TypeError):
                continue
        if len(nums) >= 6:
            return nums[:6]
    
    # Last resort: generate dummy truth
    return list(range(1, 7))


# Import OMEGA wrappers
try:
    from .omega_wrappers import OMEGA_MODEL_REGISTRY
except ImportError:
    OMEGA_MODEL_REGISTRY = {}

# MODEL REGISTRY - Replace with your actual model wrappers
MODEL_REGISTRY = {
    # Dummy models for testing
    "consensus": lambda train_df, top_n: dummy_predict_consensus(train_df, top_n),
    "transformer_deep": lambda train_df, top_n: dummy_predict_transformer(train_df, top_n),
    "lstm_v2": lambda train_df, top_n: dummy_predict_lstm(train_df, top_n),
    "genetico": lambda train_df, top_n: dummy_predict_genetic(train_df, top_n),
    "montecarlo": lambda train_df, top_n: dummy_predict_montecarlo(train_df, top_n),
    "apriori": lambda train_df, top_n: dummy_predict_apriori(train_df, top_n),
}

# Add OMEGA models
MODEL_REGISTRY.update(OMEGA_MODEL_REGISTRY)


def dummy_predict_consensus(train_df: pd.DataFrame, top_n: int) -> List[List[int]]:
    """Dummy consensus predictor - replace with real implementation."""
    random.seed(42)
    preds = []
    for i in range(min(top_n, 10)):
        pred = sorted(random.sample(range(1, 41), 6))
        preds.append(pred)
    return preds


def dummy_predict_transformer(train_df: pd.DataFrame, top_n: int) -> List[List[int]]:
    """Dummy transformer predictor - replace with real implementation."""
    random.seed(123)
    preds = []
    for i in range(min(top_n, 8)):
        # Simulate transformer bias towards recent patterns
        pred = sorted(random.sample(range(5, 40), 6))
        preds.append(pred)
    return preds


def dummy_predict_lstm(train_df: pd.DataFrame, top_n: int) -> List[List[int]]:
    """Dummy LSTM predictor - replace with real implementation."""
    random.seed(456)
    preds = []
    for i in range(min(top_n, 6)):
        # Simulate LSTM sequence patterns
        base = random.randint(1, 10)
        pred = sorted([base + j*5 + random.randint(-2, 2) for j in range(6)])
        pred = [max(1, min(40, x)) for x in pred]  # Clamp to valid range
        if len(set(pred)) == 6:  # Ensure uniqueness
            preds.append(pred)
    return preds


def dummy_predict_genetic(train_df: pd.DataFrame, top_n: int) -> List[List[int]]:
    """Dummy genetic algorithm predictor - replace with real implementation."""
    random.seed(789)
    preds = []
    for i in range(min(top_n, 12)):
        # Simulate genetic diversity
        pred = sorted(random.sample(range(1, 41), 6))
        preds.append(pred)
    return preds


def dummy_predict_montecarlo(train_df: pd.DataFrame, top_n: int) -> List[List[int]]:
    """Dummy Monte Carlo predictor - replace with real implementation."""
    random.seed(101112)
    preds = []
    for i in range(min(top_n, 15)):
        # Pure random sampling
        pred = sorted(random.sample(range(1, 41), 6))
        preds.append(pred)
    return preds


def dummy_predict_apriori(train_df: pd.DataFrame, top_n: int) -> List[List[int]]:
    """Dummy Apriori predictor - replace with real implementation."""
    random.seed(131415)
    preds = []
    # Simulate frequent patterns
    frequent_nums = [7, 14, 21, 28, 35]  # Common lottery patterns
    for i in range(min(top_n, 8)):
        pred = random.sample(frequent_nums, 3) + random.sample(range(1, 41), 3)
        pred = sorted(list(set(pred))[:6])  # Remove duplicates and limit
        if len(pred) == 6:
            preds.append(pred)
    return preds


def run_backtest(data_path: str, models: List[str], windows: str, top_n: int, seed: int, out_dir: str) -> Dict[str, Any]:
    """Run the backtest evaluation."""
    # Set deterministic seed
    set_all_seeds(seed)
    
    # Create output directory
    ensure_dir(out_dir)
    
    # Save run arguments
    args = {
        "data_path": data_path,
        "models": models,
        "windows": windows,
        "top_n": top_n,
        "seed": seed,
        "out_dir": out_dir,
    }
    save_json(args, os.path.join(out_dir, "args.json"))
    
    # Save environment manifest
    env_manifest = collect_env_manifest()
    save_json(env_manifest, os.path.join(out_dir, "env_manifest.json"))
    
    # Load data
    df = load_data(data_path)
    print(f"📊 Loaded {len(df)} rows from {data_path}")
    
    # Parse window configuration
    if windows.startswith("rolling_"):
        train_size = int(windows.split("_")[1])
    else:
        train_size = 200  # Default
    
    # Initialize results
    results = []
    window_count = 0
    
    # Run rolling window backtest
    print(f"🔄 Starting rolling window backtest (train_size={train_size})...")
    
    try:
        for train_df, test_df in rolling_windows(df, train_size=train_size, step=1):
            window_count += 1
            if window_count > 100:  # Limit for demo
                break
                
            # Extract truth from test row
            test_row = test_df.iloc[0]
            truth = extract_truth_from_row(test_row)
            
            print(f"  Window {window_count}: train={len(train_df)}, test=1, truth={truth}")
            
            # Test each model
            for model_name in models:
                if model_name not in MODEL_REGISTRY:
                    print(f"  ⚠️  Unknown model: {model_name}, skipping")
                    continue
                
                try:
                    # Get model predictions
                    model_func = MODEL_REGISTRY[model_name]
                    preds = model_func(train_df, top_n)
                    
                    if not preds:
                        print(f"  ⚠️  Model {model_name} returned no predictions")
                        continue
                    
                    # Calculate metrics
                    metrics = calculate_all_metrics(preds, truth)
                    
                    # Store results
                    result = {
                        "window": window_count,
                        "model": model_name,
                        "truth": truth,
                        "predictions": preds[:3],  # Store top 3 for space
                        **metrics
                    }
                    results.append(result)
                    
                    print(f"    {model_name}: best={metrics['best']}, compound={metrics['compound']:.3f}")
                    
                except Exception as e:
                    print(f"  ❌ Error with model {model_name}: {e}")
                    continue
    
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        return {"error": str(e)}
    
    # Save detailed results
    results_df = pd.DataFrame(results)
    results_path = os.path.join(out_dir, "backtest_results.csv")
    results_df.to_csv(results_path, index=False)
    
    # Calculate summary statistics
    summary_stats = []
    for model_name in models:
        model_results = results_df[results_df["model"] == model_name]
        if len(model_results) > 0:
            stats = {
                "model": model_name,
                "windows": len(model_results),
                "mean_compound": model_results["compound"].mean(),
                "std_compound": model_results["compound"].std(),
                "mean_best": model_results["best"].mean(),
                "hit6_count": model_results["hit6"].sum(),
                "hit5_count": model_results["hit5"].sum(),
                "hit4_count": model_results["hit4"].sum(),
                "total_points": model_results["points"].sum(),
            }
            summary_stats.append(stats)
    
    summary_df = pd.DataFrame(summary_stats)
    summary_path = os.path.join(out_dir, "summary.csv")
    summary_df.to_csv(summary_path, index=False)
    
    print(f"✅ Backtest completed: {len(results)} results across {window_count} windows")
    print(f"📁 Results saved to: {out_dir}")
    
    return {
        "success": True,
        "windows_processed": window_count,
        "total_results": len(results),
        "results_path": results_path,
        "summary_path": summary_path,
        "summary_stats": summary_stats,
    }