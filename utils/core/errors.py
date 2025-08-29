from typing import Optional, Dict


class OmegaError(Exception):
    """Base class for OMEGA typed errors."""


class DataLoadError(OmegaError):
    def __init__(self, message: str, *, path: Optional[str] = None):
        super().__init__(message)
        self.path = path


class ModelLoadError(OmegaError):
    def __init__(self, message: str, *, model: Optional[str] = None):
        super().__init__(message)
        self.model = model


class ValidationError(OmegaError):
    def __init__(self, message: str, *, details: Optional[Dict] = None):
        super().__init__(message)
        self.details = details or {}


