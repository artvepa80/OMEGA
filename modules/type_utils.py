import numpy as np
from typing import Union, List, Any

def safe_int_conversion(value: Any) -> int:
    """
    Safely convert various numeric types to Python int with robust handling.
    
    Args:
        value (Any): Input value to convert to integer
    
    Returns:
        int: Converted integer value
    
    Examples:
        >>> safe_int_conversion(4.7)  # 5
        >>> safe_int_conversion(np.int64(10))  # 10
        >>> safe_int_conversion("12")  # 12
    """
    try:
        # Handle numpy numeric types first
        if isinstance(value, (np.integer, np.floating)):
            return int(round(float(value)))
        
        # Handle other numeric and string types
        if isinstance(value, (int, float, str)):
            return int(round(float(value)))
        
        # Fallback for unexpected types
        raise ValueError(f"Cannot convert type {type(value)} to integer")
    
    except (TypeError, ValueError) as e:
        # Log the error or handle it appropriately
        print(f"Error converting {value} to integer: {e}")
        raise

def safe_int_list_conversion(values: List[Any]) -> List[int]:
    """
    Safely convert a list of values to integers.
    
    Args:
        values (List[Any]): List of values to convert
    
    Returns:
        List[int]: List of converted integers
    """
    return [safe_int_conversion(x) for x in values]

def convert_numpy_list(input_list: List[Any]) -> List[int]:
    """
    Robust conversion for lists that might contain numpy types.
    
    Args:
        input_list (List[Any]): Input list with potential numpy types
    
    Returns:
        List[int]: List of pure Python integers
    """
    return [safe_int_conversion(x) for x in input_list]