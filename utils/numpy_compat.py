"""
NumPy Compatibility Layer
Provides compatibility for deprecated numpy aliases in NumPy 2.0+
"""

import numpy as np
import warnings
import json
from typing import Any

def patch_numpy_deprecated_aliases():
    """
    Patch numpy to restore deprecated aliases for compatibility with older dependencies
    """
    try:
        # Check if np.bool already exists (NumPy < 2.0)
        if hasattr(np, 'bool'):
            return
        
        # Restore deprecated aliases for NumPy 2.0+
        if not hasattr(np, 'bool'):
            np.bool = bool
            np.int = int
            np.float = float
            np.complex = complex
            np.object = object
            np.str = str
            
        # Suppress specific deprecation warnings
        warnings.filterwarnings('ignore', category=DeprecationWarning, 
                              message='.*np.bool.*deprecated.*')
        warnings.filterwarnings('ignore', category=DeprecationWarning,
                              message='.*np.int.*deprecated.*')
        warnings.filterwarnings('ignore', category=DeprecationWarning,
                              message='.*np.float.*deprecated.*')
                              
    except Exception as e:
        print(f"Warning: Could not apply numpy compatibility patch: {e}")

def numpy_to_python(obj: Any) -> Any:
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: numpy_to_python(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [numpy_to_python(item) for item in obj]
    return obj

def safe_json_dump(obj: Any, **kwargs) -> str:
    """Safely serialize object to JSON, converting numpy types"""
    converted_obj = numpy_to_python(obj)
    return json.dumps(converted_obj, **kwargs)

def safe_json_export(obj: Any, filepath: str, **kwargs) -> None:
    """Safely export object to JSON file, converting numpy types"""
    converted_obj = numpy_to_python(obj)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(converted_obj, f, **kwargs)

def safe_slice_list(lst: Any, start: int = None, end: int = None) -> list:
    """Safely slice a list-like object, handling edge cases"""
    if not lst or not hasattr(lst, '__getitem__'):
        return []
    
    try:
        if isinstance(lst, list):
            return lst[start:end] if start is not None or end is not None else lst
        else:
            return list(lst)[start:end] if start is not None or end is not None else list(lst)
    except (TypeError, IndexError):
        return []

# Apply patch on import
patch_numpy_deprecated_aliases()