"""OMEGA Model Wrappers for Evaluation Harness

This module provides wrappers to integrate OMEGA prediction models
with the evaluation harness framework.
"""

from __future__ import annotations

import os
import sys
import subprocess
import tempfile
from typing import List, Dict, Any
import pandas as pd
import json

# Add project root to path so we can import OMEGA modules
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)


def omega_production_wrapper(train_df: pd.DataFrame, top_n: int) -> List[List[int]]:
    """Wrapper for omega_production_v4.py"""
    try:
        # Save training data to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            train_df.to_csv(f.name, index=False)
            temp_data_path = f.name
        
        # Run omega_production_v4.py in single-prediction mode
        script_path = os.path.join(PROJECT_ROOT, "omega_production_v4.py")
        cmd = [
            sys.executable, script_path,
            "--mode", "single-prediction",
            "--export-formats", "json", "csv"
        ]
        
        # Clean environment to avoid argument conflicts
        env = os.environ.copy()
        env.pop('ARGV', None)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, 
                              env=env, cwd=PROJECT_ROOT)
        
        # Cleanup temp file
        os.unlink(temp_data_path)
        
        if result.returncode == 0:
            # Parse output to extract predictions
            predictions = parse_production_output_enhanced(result.stdout)
            return predictions[:top_n] if predictions else fallback_predictions(top_n)
        else:
            print(f"⚠️ omega_production_v4 failed: {result.stderr}")
            # Try to parse any partial output
            if result.stdout:
                predictions = parse_production_output_enhanced(result.stdout)
                if predictions:
                    return predictions[:top_n]
            return fallback_predictions(top_n)
            
    except Exception as e:
        print(f"⚠️ Error in omega_production_wrapper: {e}")
        return fallback_predictions(top_n)


def omega_hybrid_wrapper(train_df: pd.DataFrame, top_n: int) -> List[List[int]]:
    """Wrapper for omega_hybrid_integration.py"""
    try:
        # Run omega_hybrid_integration.py without data argument (uses internal data)
        script_path = os.path.join(PROJECT_ROOT, "omega_hybrid_integration.py")
        cmd = [
            sys.executable, script_path,
            "--mode", "hybrid",
            "--export-formats", "json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            # Parse hybrid output
            predictions = parse_hybrid_output(result.stdout)
            return predictions[:top_n] if predictions else fallback_predictions(top_n)
        else:
            print(f"⚠️ omega_hybrid failed: {result.stderr}")
            return fallback_predictions(top_n)
            
    except Exception as e:
        print(f"⚠️ Error in omega_hybrid_wrapper: {e}")
        return fallback_predictions(top_n)


def omega_pipeline_wrapper(train_df: pd.DataFrame, top_n: int) -> List[List[int]]:
    """Wrapper for pipeline mode only"""
    try:
        script_path = os.path.join(PROJECT_ROOT, "omega_hybrid_integration.py")
        cmd = [
            sys.executable, script_path,
            "--mode", "pipeline",
            "--export-formats", "json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        
        if result.returncode == 0:
            predictions = parse_hybrid_output(result.stdout)
            return predictions[:top_n] if predictions else fallback_predictions(top_n)
        else:
            return fallback_predictions(top_n)
            
    except Exception as e:
        print(f"⚠️ Error in omega_pipeline_wrapper: {e}")
        return fallback_predictions(top_n)


def omega_agentic_wrapper(train_df: pd.DataFrame, top_n: int) -> List[List[int]]:
    """Wrapper for agentic mode only"""
    try:
        script_path = os.path.join(PROJECT_ROOT, "omega_hybrid_integration.py")
        cmd = [
            sys.executable, script_path,
            "--mode", "agentic",
            "--export-formats", "json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        
        if result.returncode == 0:
            predictions = parse_hybrid_output(result.stdout)
            return predictions[:top_n] if predictions else fallback_predictions(top_n)
        else:
            return fallback_predictions(top_n)
            
    except Exception as e:
        print(f"⚠️ Error in omega_agentic_wrapper: {e}")
        return fallback_predictions(top_n)


def main_py_wrapper(train_df: pd.DataFrame, top_n: int) -> List[List[int]]:
    """Wrapper for main.py"""
    try:
        # Save training data to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            train_df.to_csv(f.name, index=False)
            temp_data_path = f.name
        
        # Run main.py
        script_path = os.path.join(PROJECT_ROOT, "main.py")
        cmd = [
            sys.executable, script_path,
            "--data", temp_data_path,
            "--export", "json",
            "--quiet"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        
        # Cleanup temp file
        os.unlink(temp_data_path)
        
        if result.returncode == 0:
            predictions = parse_main_output(result.stdout)
            return predictions[:top_n]
        else:
            return fallback_predictions(top_n)
            
    except Exception as e:
        print(f"⚠️ Error in main_py_wrapper: {e}")
        return fallback_predictions(top_n)


def parse_omega_output(output: str) -> List[List[int]]:
    """Parse output from omega_production_v4.py"""
    predictions = []
    
    try:
        # Look for combination patterns in output
        lines = output.split('\n')
        for line in lines:
            if 'combinación' in line.lower() or 'combination' in line.lower():
                # Extract numbers from line
                import re
                numbers = re.findall(r'\b([1-4]?\d)\b', line)
                if numbers:
                    combo = [int(n) for n in numbers if 1 <= int(n) <= 40]
                    if len(combo) >= 6:
                        predictions.append(sorted(combo[:6]))
        
        # If no patterns found, try to find JSON output
        if not predictions:
            predictions = parse_json_output(output)
            
    except Exception as e:
        print(f"⚠️ Error parsing omega output: {e}")
    
    return predictions if predictions else fallback_predictions(3)


def parse_hybrid_output(output: str) -> List[List[int]]:
    """Parse output from omega_hybrid_integration.py"""
    predictions = []
    
    try:
        # Look for JSON output files mentioned in stdout
        lines = output.split('\n')
        json_files = []
        
        for line in lines:
            if '.json' in line and 'outputs/' in line:
                # Extract JSON file path
                import re
                match = re.search(r'outputs/[^\s]+\.json', line)
                if match:
                    json_file = match.group(0)
                    full_path = os.path.join(PROJECT_ROOT, json_file)
                    if os.path.exists(full_path):
                        json_files.append(full_path)
        
        # Parse the most recent JSON file
        if json_files:
            with open(json_files[-1], 'r') as f:
                data = json.load(f)
                
            if 'combinations' in data:
                for combo_data in data['combinations']:
                    if 'numbers' in combo_data:
                        numbers = combo_data['numbers']
                        if len(numbers) == 6:
                            predictions.append(numbers)
        
        # Fallback: parse text output
        if not predictions:
            predictions = parse_omega_output(output)
            
    except Exception as e:
        print(f"⚠️ Error parsing hybrid output: {e}")
    
    return predictions if predictions else fallback_predictions(3)


def parse_main_output(output: str) -> List[List[int]]:
    """Parse output from main.py"""
    return parse_omega_output(output)  # Similar format


def parse_json_output(text: str) -> List[List[int]]:
    """Try to extract JSON from text output"""
    predictions = []
    
    try:
        # Look for JSON-like structures
        import re
        import json
        
        # Find JSON objects in the text
        json_pattern = r'\{[^{}]*"numbers"[^{}]*\}'
        matches = re.findall(json_pattern, text)
        
        for match in matches:
            try:
                obj = json.loads(match)
                if 'numbers' in obj:
                    numbers = obj['numbers']
                    if isinstance(numbers, list) and len(numbers) == 6:
                        predictions.append(numbers)
            except:
                continue
                
    except Exception:
        pass
    
    return predictions


def fallback_predictions(top_n: int) -> List[List[int]]:
    """Generate fallback predictions when model fails"""
    import random
    random.seed(42)  # Deterministic fallback
    
    predictions = []
    for i in range(min(top_n, 5)):
        pred = sorted(random.sample(range(1, 41), 6))
        predictions.append(pred)
    
    return predictions


def omega_ultimate_v3_wrapper(train_df: pd.DataFrame, top_n: int) -> List[List[int]]:
    """Wrapper for omega_ultimate_v3.py"""
    try:
        script_path = os.path.join(PROJECT_ROOT, "omega_ultimate_v3.py")
        cmd = [sys.executable, script_path]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            predictions = parse_ultimate_v3_output(result.stdout)
            return predictions[:top_n] if predictions else fallback_predictions(top_n)
        else:
            print(f"⚠️ omega_ultimate_v3 failed: {result.stderr}")
            return fallback_predictions(top_n)
            
    except Exception as e:
        print(f"⚠️ Error in omega_ultimate_v3_wrapper: {e}")
        return fallback_predictions(top_n)


def parse_ultimate_v3_output(output: str) -> List[List[int]]:
    """Parse output from omega_ultimate_v3.py"""
    predictions = []
    
    try:
        # Look for combination patterns in output
        lines = output.split('\n')
        for line in lines:
            # Look for patterns like "01 - 07 - 15 - 28 - 30 - 36"
            if ' - ' in line and any(char.isdigit() for char in line):
                import re
                # Extract number sequences separated by dashes
                number_match = re.search(r'(\d{2}\s*-\s*\d{2}\s*-\s*\d{2}\s*-\s*\d{2}\s*-\s*\d{2}\s*-\s*\d{2})', line)
                if number_match:
                    number_str = number_match.group(1)
                    numbers = [int(n.strip()) for n in number_str.split('-')]
                    if len(numbers) == 6 and all(1 <= n <= 40 for n in numbers):
                        predictions.append(sorted(numbers))
            
            # Also look for JSON-like structures in results files
            elif 'ultimate_v3' in line and '.json' in line:
                # Try to read the JSON file mentioned
                try:
                    import re
                    match = re.search(r'results/ultimate_v3/[^\s]+\.json', line)
                    if match:
                        json_file = match.group(0)
                        full_path = os.path.join(PROJECT_ROOT, json_file)
                        if os.path.exists(full_path):
                            with open(full_path, 'r') as f:
                                data = json.load(f)
                            
                            if 'final_combinations' in data:
                                for combo_data in data['final_combinations']:
                                    if 'combination' in combo_data:
                                        numbers = combo_data['combination']
                                        if len(numbers) == 6:
                                            predictions.append(numbers)
                except Exception:
                    continue
        
        # If no patterns found, try to find CSV files
        if not predictions:
            import glob
            csv_files = glob.glob(os.path.join(PROJECT_ROOT, "results/ultimate_v3/*.csv"))
            if csv_files:
                latest_csv = max(csv_files, key=os.path.getctime)
                try:
                    df = pd.read_csv(latest_csv)
                    if 'combination' in df.columns:
                        for combo_str in df['combination'].head(top_n):
                            numbers = [int(n) for n in combo_str.split('-')]
                            if len(numbers) == 6:
                                predictions.append(numbers)
                except Exception:
                    pass
                    
    except Exception as e:
        print(f"⚠️ Error parsing ultimate v3 output: {e}")
    
    return predictions if predictions else fallback_predictions(5)


def parse_production_output_enhanced(output: str) -> List[List[int]]:
    """Enhanced parser for omega_production_v4.py output"""
    predictions = []
    
    try:
        # 1. Look for JSON file exports mentioned in output
        lines = output.split('\n')
        json_files = []
        csv_files = []
        
        for line in lines:
            if 'JSON:' in line or '.json' in line:
                import re
                match = re.search(r'outputs/[^\s]+\.json', line)
                if match:
                    json_files.append(match.group(0))
            elif 'CSV:' in line or '.csv' in line:
                match = re.search(r'outputs/[^\s]+\.csv', line)
                if match:
                    csv_files.append(match.group(0))
        
        # 2. Try to read from JSON exports
        for json_file in json_files:
            try:
                full_path = os.path.join(PROJECT_ROOT, json_file)
                if os.path.exists(full_path):
                    with open(full_path, 'r') as f:
                        data = json.load(f)
                    
                    # Look for combinations in different structures
                    if 'ensemble_result' in data and 'final_combinations' in data['ensemble_result']:
                        for combo in data['ensemble_result']['final_combinations']:
                            if isinstance(combo, list) and len(combo) == 6:
                                predictions.append(combo)
                    elif 'traditional_omega' in data and 'combinations' in data['traditional_omega']:
                        for combo in data['traditional_omega']['combinations']:
                            if isinstance(combo, list) and len(combo) == 6:
                                predictions.append(combo)
                    elif 'combinations' in data:
                        for combo in data['combinations']:
                            if isinstance(combo, list) and len(combo) == 6:
                                predictions.append(combo)
                    
                    if predictions:
                        break
            except Exception:
                continue
        
        # 3. Try to read from CSV exports
        if not predictions and csv_files:
            for csv_file in csv_files:
                try:
                    full_path = os.path.join(PROJECT_ROOT, csv_file)
                    if os.path.exists(full_path):
                        import pandas as pd
                        df = pd.read_csv(full_path)
                        
                        # Look for combination columns
                        if 'combination' in df.columns:
                            for combo_str in df['combination']:
                                if isinstance(combo_str, str):
                                    numbers = [int(x.strip()) for x in combo_str.split(',')]
                                    if len(numbers) == 6:
                                        predictions.append(numbers)
                        
                        if predictions:
                            break
                except Exception:
                    continue
        
        # 4. Parse combinations directly from output text
        if not predictions:
            for line in lines:
                # Look for patterns like [1, 15, 23, 28, 35, 40]
                if '[' in line and ']' in line and any(char.isdigit() for char in line):
                    import re
                    matches = re.findall(r'\[([0-9, ]+)\]', line)
                    for match in matches:
                        try:
                            numbers = [int(x.strip()) for x in match.split(',')]
                            if len(numbers) == 6 and all(1 <= n <= 40 for n in numbers):
                                predictions.append(numbers)
                        except ValueError:
                            continue
        
        # 5. Fallback: look for any number sequences
        if not predictions:
            import re
            for line in lines:
                # Look for 6 numbers separated by various delimiters
                number_patterns = [
                    r'(\d+)[,\s-]+(\d+)[,\s-]+(\d+)[,\s-]+(\d+)[,\s-]+(\d+)[,\s-]+(\d+)',
                    r'(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})'
                ]
                
                for pattern in number_patterns:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        try:
                            numbers = [int(x) for x in match]
                            if len(numbers) == 6 and all(1 <= n <= 40 for n in numbers):
                                predictions.append(sorted(numbers))
                        except ValueError:
                            continue
                    
                    if predictions:
                        break
                
                if predictions:
                    break
        
    except Exception as e:
        print(f"⚠️ Error in enhanced production parser: {e}")
    
    return predictions if predictions else []


def heuristic_enhanced_wrapper(train_df: pd.DataFrame, top_n: int) -> List[List[int]]:
    """Wrapper for HeuristicOptimizerEnhanced to generate predictions from training window.

    This avoids heavy training; uses train_df to build a minimal historical DataFrame
    and leverages the heuristic fallback when needed.
    """
    try:
        # Import locally to avoid hard dependency during harness import
        from modules.heuristic_optimizer_enhanced import HeuristicOptimizerEnhanced
        import numpy as np
        import pandas as pd

        # Build a minimal historical dataframe with 6 numeric columns -> 'combination'
        numeric_cols = [c for c in train_df.columns if pd.api.types.is_numeric_dtype(train_df[c])]
        if len(numeric_cols) >= 6:
            use_cols = numeric_cols[:6]
            combos = train_df[use_cols].astype(int).values.tolist()
        else:
            # Fallback: generate a few random combinations from data-driven seed
            rng = np.random.default_rng(42)
            combos = [sorted(rng.choice(range(1, 41), size=6, replace=False).tolist()) for _ in range(min(100, len(train_df) or 100))]

        hist_df = pd.DataFrame({"combination": combos})
        if "fecha" not in hist_df.columns:
            hist_df["fecha"] = pd.date_range("2020-01-01", periods=len(hist_df))

        # Initialize optimizer without reading files
        optimizer = HeuristicOptimizerEnhanced()
        optimizer.historical_data = hist_df

        # Fast pipeline: analyze + generate predictions (no heavy training)
        try:
            optimizer.analyze_historical_patterns(hist_df)
        except Exception:
            pass

        preds = optimizer.generate_predictions(n_predictions=top_n)

        # Ensure proper shape
        cleaned: List[List[int]] = []
        for combo in preds[:top_n]:
            try:
                combo = [int(x) for x in combo]
                combo = sorted(list(dict.fromkeys(combo)))  # unique + sorted
                if len(combo) == 6 and all(1 <= v <= 40 for v in combo):
                    cleaned.append(combo)
            except Exception:
                continue

        # If no valid predictions, synthesize from training window frequency
        if not cleaned:
            # Build frequency of numbers 1..40 from train_df numeric content
            freq = {i: 0 for i in range(1, 41)}
            numeric_cols = [c for c in train_df.columns if pd.api.types.is_numeric_dtype(train_df[c])]
            for c in numeric_cols:
                col_vals = pd.to_numeric(train_df[c], errors='coerce').dropna().astype(int)
                for v, count in col_vals.value_counts().items():
                    if 1 <= v <= 40:
                        freq[v] += int(count)
            # Top-6 by frequency for first combo
            top6 = sorted(sorted(freq.keys(), key=lambda k: (-freq[k], k))[:6])
            if len(set(top6)) == 6 and all(1 <= x <= 40 for x in top6):
                cleaned.append(top6)
            # Add diversity combos sampling around frequencies
            import random
            random.seed(42)
            pool = [n for n in range(1, 41) if n not in set(top6)]
            while len(cleaned) < max(2, min(top_n, 5)):
                # Bias sample: mix half from top-12, half random
                top12 = sorted(freq.keys(), key=lambda k: (-freq[k], k))[:12]
                pick = sorted(list(set(random.sample(top12, k=3) + random.sample(pool or list(range(1, 41)), k=3)))[:6])
                if len(pick) == 6 and pick not in cleaned:
                    cleaned.append(pick)

        # Fallback if still none
        return cleaned if cleaned else fallback_predictions(top_n)

    except Exception as e:
        print(f"⚠️ Error in heuristic_enhanced_wrapper: {e}")
        return fallback_predictions(top_n)

# Register OMEGA model wrappers
OMEGA_MODEL_REGISTRY = {
    "omega_production": omega_production_wrapper,
    "omega_hybrid": omega_hybrid_wrapper,
    "omega_pipeline": omega_pipeline_wrapper,
    "omega_agentic": omega_agentic_wrapper,
    "omega_main": main_py_wrapper,
    "omega_ultimate_v3": omega_ultimate_v3_wrapper,
    "heuristic_enhanced": heuristic_enhanced_wrapper,
}
