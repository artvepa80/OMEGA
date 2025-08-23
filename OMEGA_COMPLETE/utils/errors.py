"""
Custom error classes for OMEGA system
"""

class OmegaError(Exception):
    """Base exception for OMEGA system"""
    pass

class DataLoadError(OmegaError):
    """Error loading data"""
    pass

class ModelLoadError(OmegaError):
    """Error loading models"""
    pass

class ValidationError(OmegaError):
    """Validation error"""
    pass

class PredictionError(OmegaError):
    """Error during prediction"""
    pass