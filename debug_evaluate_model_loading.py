#!/usr/bin/env python3
"""
Debug script to test the cargar_datos() function in evaluate_model.py
"""

import sys
import os
import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer

# Add the modules directory to Python path to import evaluate_model
sys.path.insert(0, os.path.join(os.getcwd(), 'modules', 'learning'))

def test_cargar_datos():
    try:
        print("🔍 Testing cargar_datos() function from evaluate_model.py...")
        
        # Import the function
        from evaluate_model import cargar_datos
        
        # Call the function
        print("⚙️ Calling cargar_datos()...")
        df = cargar_datos()
        
        print(f"✅ Function returned DataFrame with shape: {df.shape}")
        
        if not df.empty:
            print(f"📊 Columns: {list(df.columns)}")
            print(f"\n📋 First 10 rows:")
            print(df.head(10))
            
            if len(df.columns) > 0:
                first_col = df.columns[0] 
                print(f"\n📊 First 10 values of {first_col}: {df[first_col].head(10).tolist()}")
                print(f"📊 Unique values in {first_col}: {sorted(df[first_col].unique())}")
                
                # Check if all values are 40
                if df[first_col].nunique() == 1 and df[first_col].iloc[0] == 40:
                    print("🚨 FOUND THE ISSUE: All values in first column are 40!")
                else:
                    print("✅ Values look correct - not all 40s")
        else:
            print("⚠️ DataFrame is empty")
            
    except Exception as e:
        print(f"❌ Error testing cargar_datos(): {e}")
        import traceback
        traceback.print_exc()

def test_direct_csv_load():
    print("\n" + "="*60)
    print("🔍 Testing direct CSV loading...")
    
    # Test the exact path used by evaluate_model.py
    DATA_PATH = "data/processed/DataFrame_completo_de_sorteos.csv"
    
    try:
        print(f"⚙️ Loading CSV from: {DATA_PATH}")
        df = pd.read_csv(DATA_PATH)
        
        print(f"✅ Loaded CSV with shape: {df.shape}")
        
        # Filter to bolilla columns
        df_bolillas = df[[col for col in df.columns if col.lower().startswith("bolilla")]]
        print(f"📊 Bolilla columns shape: {df_bolillas.shape}")
        
        if df_bolillas.shape[1] > 0:
            first_col = df_bolillas.columns[0]
            print(f"📊 First 10 values of {first_col}: {df_bolillas[first_col].head(10).tolist()}")
            print(f"📊 Unique values count in {first_col}: {df_bolillas[first_col].nunique()}")
            
        # Test the imputation logic from cargar_datos
        print(f"\n⚙️ Testing imputation logic...")
        if df_bolillas.shape[1] == 6:
            print("✅ Found 6 bolilla columns")
            
            # Check for NaN
            print(f"📊 NaN values per column:")
            for col in df_bolillas.columns:
                nan_count = df_bolillas[col].isna().sum()
                print(f"  {col}: {nan_count} NaNs")
            
            # Apply imputation
            imputer = SimpleImputer(strategy='mean')
            df_imputed = pd.DataFrame(imputer.fit_transform(df_bolillas), columns=df_bolillas.columns)
            df_final = df_imputed.dropna()
            
            print(f"📊 After imputation and dropna: shape {df_final.shape}")
            
            if not df_final.empty and len(df_final.columns) > 0:
                first_col = df_final.columns[0]
                print(f"📊 First 10 values after processing: {df_final[first_col].head(10).tolist()}")
                print(f"📊 Unique values after processing: {df_final[first_col].nunique()}")
                
                # Check clipping
                values_too_low = (df_final < 1).any().any()
                values_too_high = (df_final > 40).any().any()
                print(f"📊 Values too low (<1): {values_too_low}")
                print(f"📊 Values too high (>40): {values_too_high}")
                
                if values_too_low or values_too_high:
                    print("⚙️ Applying clipping...")
                    df_clipped = df_final.clip(1, 40)
                    first_col = df_clipped.columns[0]
                    print(f"📊 After clipping - first 10 values: {df_clipped[first_col].head(10).tolist()}")
        else:
            print(f"❌ Expected 6 bolilla columns, got {df_bolillas.shape[1]}")
            
    except Exception as e:
        print(f"❌ Error in direct CSV test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cargar_datos()
    test_direct_csv_load()