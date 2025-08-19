import numpy as np
import pytest
from modules.type_utils import safe_int_conversion, safe_int_list_conversion

def test_safe_int_conversion():
    # Test numpy types
    assert safe_int_conversion(np.int64(4)) == 4
    assert safe_int_conversion(np.float64(4.7)) == 5
    assert safe_int_conversion(np.float32(4.2)) == 4

    # Test Python types
    assert safe_int_conversion(4) == 4
    assert safe_int_conversion(4.7) == 5
    assert safe_int_conversion("12") == 12

    # Test rounding behavior
    assert safe_int_conversion(4.3) == 4
    assert safe_int_conversion(4.6) == 5

def test_safe_int_list_conversion():
    # Mixed type list
    mixed_list = [1, 2.5, np.int64(3), "4", np.float64(4.7)]
    result = safe_int_list_conversion(mixed_list)
    assert result == [1, 3, 3, 4, 5]

def test_safe_int_conversion_error_handling():
    with pytest.raises(ValueError):
        safe_int_conversion(None)
    with pytest.raises(ValueError):
        safe_int_conversion([1, 2, 3])