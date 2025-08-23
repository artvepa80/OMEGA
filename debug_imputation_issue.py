#!/usr/bin/env python3
"""
Debug script to investigate the imputation issue causing bolilla_1 values to be corrupted to 40
"""

import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer

# Load the data the same way consensus_engine does
def test_imputation_process():
    print("🔍 Loading data from CSV...")
    
    # Load the CSV that consensus_engine would be using
    csv_path = "data/historial_kabala_github_emergency_clean.csv"
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ Loaded CSV with shape: {df.shape}")
        print(f"📊 Columns: {list(df.columns)}")
        
        # Show first few rows
        print(f"\n📋 First 5 rows of original data:")
        print(df.head())
        
        # Focus on bolilla columns 
        bolilla_cols = [col for col in df.columns if 'bolilla' in col.lower()]
        print(f"\n🎯 Bolilla columns: {bolilla_cols}")
        
        if bolilla_cols:
            print(f"\n📊 First 10 bolilla_1 values: {df[bolilla_cols[0]].head(10).tolist()}")
            
            # Now simulate what consensus_engine does
            print(f"\n🔬 Simulating consensus_engine imputation process...")
            
            # Step 1: Select numeric columns
            num_cols = df.select_dtypes(include='number').columns[:6]
            print(f"🔢 Selected numeric columns: {list(num_cols)}")
            
            # Step 2: Check for missing values before imputation
            print(f"\n📊 Missing values per column before imputation:")
            for col in num_cols:
                missing_count = df[col].isna().sum()
                print(f"  {col}: {missing_count} missing values")
            
            # Step 3: Show data before imputation  
            print(f"\n📋 Data before imputation (first 10 rows):")
            print(df[num_cols].head(10))
            
            # Step 4: Apply imputation
            imputer = SimpleImputer(strategy="mean")
            df_before_imputation = df[num_cols].copy()
            
            print(f"\n⚙️ Applying imputation...")
            imputed_data = imputer.fit_transform(df[num_cols])
            
            print(f"📊 Imputed data shape: {imputed_data.shape}")
            print(f"📊 First 10 values of first column after imputation:")
            print(imputed_data[:10, 0])
            
            # Step 5: Apply clipping and rounding
            print(f"\n⚙️ Applying clipping (1, 40) and rounding...")
            final_data = np.clip(imputed_data, 1, 40).round().astype(int)
            
            print(f"📊 Final data shape: {final_data.shape}")  
            print(f"📊 First 10 values of first column after clipping:")
            print(final_data[:10, 0])
            
            # Step 6: Check if all values became 40
            unique_values = np.unique(final_data[:, 0])
            print(f"\n📊 Unique values in first column after processing: {unique_values}")
            
            if len(unique_values) == 1 and unique_values[0] == 40:
                print("🚨 FOUND THE ISSUE: All values in first column became 40!")
                
                # Investigate why
                print(f"\n🔍 Investigating the cause...")
                print(f"📊 Mean of original first column: {df_before_imputation.iloc[:, 0].mean()}")
                print(f"📊 Data type of original first column: {df_before_imputation.iloc[:, 0].dtype}")
                print(f"📊 Sample of original values: {df_before_imputation.iloc[:, 0].head(20).tolist()}")
                
                # Check what SimpleImputer calculated as mean
                print(f"📊 Imputer statistics: {imputer.statistics_}")
                
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")

if __name__ == "__main__":
    test_imputation_process()