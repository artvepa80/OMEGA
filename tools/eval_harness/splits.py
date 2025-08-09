from __future__ import annotations

from typing import Generator, Tuple
import pandas as pd


def _ensure_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure DataFrame has a datetime column for ordering."""
    df = df.copy()
    if "fecha" in df.columns:
        try:
            df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        except Exception:
            df["fecha"] = pd.to_datetime(range(len(df)), unit="D", origin="unix")
    else:
        # Create a deterministic dummy date column
        df["fecha_dummy"] = pd.to_datetime(range(len(df)), unit="D", origin="unix")
    
    sort_col = "fecha" if "fecha" in df.columns else "fecha_dummy"
    df = df.sort_values(sort_col).reset_index(drop=True)
    return df


def rolling_windows(df: pd.DataFrame, train_size: int = 200, step: int = 1) -> Generator[Tuple[pd.DataFrame, pd.DataFrame], None, None]:
    """Generate rolling window splits with anti-leakage guards.
    
    Args:
        df: DataFrame with temporal data
        train_size: Size of training window
        step: Step size for rolling (default 1)
        
    Yields:
        Tuple of (train_df, test_df_1row)
        
    Raises:
        ValueError: If leakage is detected
    """
    # Ensure temporal ordering
    df_ord = _ensure_datetime_index(df)
    n = len(df_ord)
    
    if n <= train_size:
        raise ValueError(f"Dataset too small: {n} rows, need at least {train_size + 1}")
    
    for start in range(0, n - train_size, step):
        end = start + train_size
        test_idx = end
        if test_idx >= n:
            break
            
        train_df = df_ord.iloc[start:end].copy()
        test_df = df_ord.iloc[[test_idx]].copy()
        
        # Anti-leakage guards: ensure there is no overlap of indices
        if set(train_df.index) & set(test_df.index):
            raise ValueError("leakage detected: train and test indices overlap")
            
        # Ensure temporal ordering is respected (if date column exists)
        date_col = "fecha" if "fecha" in df_ord.columns else "fecha_dummy"
        if train_df[date_col].max() >= test_df[date_col].min():
            raise ValueError(f"leakage detected: test data ({test_df[date_col].min()}) not after train data ({train_df[date_col].max()})")
        
        yield train_df, test_df


def validate_split_integrity(train_df: pd.DataFrame, test_df: pd.DataFrame) -> None:
    """Additional validation for split integrity."""
    # Check for data leakage in features
    train_cols = set(train_df.columns)
    test_cols = set(test_df.columns)
    
    if train_cols != test_cols:
        raise ValueError(f"Column mismatch between train and test: {train_cols ^ test_cols}")
    
    # Ensure no duplicate indices
    if set(train_df.index) & set(test_df.index):
        raise ValueError("Index overlap detected between train and test sets")