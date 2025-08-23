#!/usr/bin/env python3
"""Debug script to understand the data structure"""

import sys
sys.path.append('.')

from modules.data_manager import OmegaDataManager

def debug_data_structure():
    """Debug the actual data structure being used"""
    
    dm = OmegaDataManager()
    data = dm.load_historical_data()
    
    print("=" * 60)
    print("DATA STRUCTURE ANALYSIS")
    print("=" * 60)
    
    print(f"Shape: {data.shape}")
    print(f"Columns: {list(data.columns)}")
    print()
    
    print("Column Details:")
    for i, col in enumerate(data.columns):
        dtype = data[col].dtype
        sample_val = data[col].iloc[0] if len(data) > 0 else "N/A"
        print(f"  {i:2}: {col:20} | {str(dtype):15} | Sample: {sample_val}")
    print()
    
    # Look for lottery number columns
    lottery_cols = []
    for col in data.columns:
        if 'bolilla' in col.lower() or col.lower().startswith('b'):
            lottery_cols.append(col)
    
    print(f"Likely lottery columns: {lottery_cols}")
    
    if lottery_cols:
        print("\nSample lottery data (first 3 rows):")
        for i in range(min(3, len(data))):
            row_data = [data[col].iloc[i] for col in lottery_cols[:6]]  # Take first 6
            print(f"  Row {i}: {row_data}")
    
    print()
    
    # Test extracting just lottery columns
    if len(lottery_cols) >= 6:
        lottery_data = data[lottery_cols[:6]]
        print(f"Extracted lottery data shape: {lottery_data.shape}")
        print(f"Lottery data types: {lottery_data.dtypes.tolist()}")
        
        # Convert to list format that montecarlo expects
        lottery_list = lottery_data.values.tolist()
        print(f"First combo as list: {lottery_list[0]}")
        print(f"Data types in first combo: {[type(x) for x in lottery_list[0]]}")

if __name__ == "__main__":
    debug_data_structure()