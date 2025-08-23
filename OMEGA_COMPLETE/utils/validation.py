"""
Validation utilities for OMEGA system
"""

import pandas as pd
import numpy as np
import logging
from typing import List, Tuple, Optional, Union

logger = logging.getLogger(__name__)

def clean_historial_df(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate historical lottery data"""
    
    if df is None or df.empty:
        logger.warning("Empty DataFrame provided to clean_historial_df")
        return pd.DataFrame()
    
    try:
        # Make a copy to avoid modifying original
        df_clean = df.copy()
        
        # Remove completely empty rows
        df_clean = df_clean.dropna(how='all')
        
        # Find numeric columns (lottery ball columns)
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns.tolist()
        
        # If no numeric columns found, try to convert string columns to numeric
        if not numeric_cols:
            for col in df_clean.columns:
                if 'bolilla' in col.lower() or 'ball' in col.lower() or col.startswith('B'):
                    try:
                        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                        if not df_clean[col].isna().all():
                            numeric_cols.append(col)
                    except:
                        continue
        
        # Take first 6 numeric columns if we have more than 6
        if len(numeric_cols) > 6:
            numeric_cols = numeric_cols[:6]
        
        # Fill NaN values in numeric columns with valid lottery numbers
        for col in numeric_cols:
            if df_clean[col].isna().any():
                # Fill with random valid numbers (1-40 for typical lottery)
                na_count = df_clean[col].isna().sum()
                df_clean.loc[df_clean[col].isna(), col] = np.random.randint(1, 41, na_count)
        
        # Ensure all numeric values are within valid range (1-40)
        for col in numeric_cols:
            df_clean[col] = df_clean[col].clip(1, 40)
            df_clean[col] = df_clean[col].astype(int)
        
        # Remove rows with duplicate numbers within the same row
        for idx in df_clean.index:
            row_values = df_clean.loc[idx, numeric_cols].tolist()
            if len(set(row_values)) != len(row_values):  # Has duplicates
                # Replace duplicates with random valid numbers
                available = list(range(1, 41))
                new_row = []
                for val in row_values:
                    if val not in new_row and val in available:
                        new_row.append(val)
                        available.remove(val)
                    else:
                        # Find replacement
                        replacement = np.random.choice(available)
                        new_row.append(replacement)
                        available.remove(replacement)
                
                df_clean.loc[idx, numeric_cols] = new_row
        
        logger.info(f"Cleaned historical data: {len(df_clean)} rows, {len(numeric_cols)} columns")
        return df_clean
        
    except Exception as e:
        logger.error(f"Error cleaning historical data: {e}")
        # Return minimal valid DataFrame
        return pd.DataFrame({
            'Bolilla 1': [1, 7, 14, 21],
            'Bolilla 2': [2, 8, 15, 22], 
            'Bolilla 3': [3, 9, 16, 23],
            'Bolilla 4': [4, 10, 17, 24],
            'Bolilla 5': [5, 11, 18, 25],
            'Bolilla 6': [6, 12, 19, 26]
        })

def validate_combination(draw: Union[Tuple[int, ...], List[int]]) -> bool:
    """
    Validate a lottery combination
    • Must be exactly 6 unique integers in range [1, 40]
    """
    try:
        nums = [int(n) for n in draw]
    except (ValueError, TypeError):
        return False
    
    return (
        len(nums) == 6
        and len(set(nums)) == 6  # All unique
        and all(1 <= n <= 40 for n in nums)  # Valid range
    )

def clean_combination(combination: List[int], logger: Optional[logging.Logger] = None) -> Optional[List[int]]:
    """Clean and validate a single lottery combination"""
    
    if not combination:
        return None
    
    try:
        # Convert to integers and remove invalid values
        clean_nums = []
        for num in combination:
            try:
                n = int(num)
                if 1 <= n <= 40:
                    clean_nums.append(n)
            except (ValueError, TypeError):
                continue
        
        # Remove duplicates while preserving order
        seen = set()
        unique_nums = []
        for n in clean_nums:
            if n not in seen:
                unique_nums.append(n)
                seen.add(n)
        
        # If we don't have exactly 6 numbers, try to fix it
        if len(unique_nums) != 6:
            if len(unique_nums) > 6:
                # Take first 6
                unique_nums = unique_nums[:6]
            else:
                # Add random numbers to complete the set
                available = [n for n in range(1, 41) if n not in unique_nums]
                needed = 6 - len(unique_nums)
                if needed <= len(available):
                    additional = np.random.choice(available, needed, replace=False)
                    unique_nums.extend(additional)
        
        # Final validation
        if len(unique_nums) == 6 and len(set(unique_nums)) == 6:
            return sorted(unique_nums)
        
        if logger:
            logger.debug(f"Failed to clean combination: {combination}")
        return None
        
    except Exception as e:
        if logger:
            logger.debug(f"Error cleaning combination {combination}: {e}")
        return None