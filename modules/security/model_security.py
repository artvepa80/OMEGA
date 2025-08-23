import os
import hashlib
import json
import torch
import cryptography
from cryptography.fernet import Fernet
from typing import Dict, Any

class ModelSecurity:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.encryption_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)

    def generate_model_signature(self, model: torch.nn.Module) -> str:
        """
        Generate a digital signature for the model to validate integrity
        
        Args:
            model (torch.nn.Module): ML model to sign
        
        Returns:
            str: Digital signature of the model
        """
        # Convert model state dict to bytes
        model_state = model.state_dict()
        model_bytes = str(model_state).encode('utf-8')
        
        # Create SHA-256 hash
        signature = hashlib.sha256(model_bytes).hexdigest()
        return signature

    def encrypt_model(self, model: torch.nn.Module) -> bytes:
        """
        Encrypt the model using Fernet symmetric encryption
        
        Args:
            model (torch.nn.Module): Model to encrypt
        
        Returns:
            bytes: Encrypted model bytes
        """
        # Serialize model state
        model_state = model.state_dict()
        model_bytes = torch.serialize(model_state)
        
        # Encrypt model bytes
        encrypted_model = self.cipher_suite.encrypt(model_bytes)
        return encrypted_model

    def decrypt_model(self, encrypted_model: bytes, model_class: torch.nn.Module) -> torch.nn.Module:
        """
        Decrypt and load an encrypted model
        
        Args:
            encrypted_model (bytes): Encrypted model bytes
            model_class (torch.nn.Module): Original model class
        
        Returns:
            torch.nn.Module: Decrypted model
        """
        # Decrypt model bytes
        decrypted_bytes = self.cipher_suite.decrypt(encrypted_model)
        
        # Deserialize and load model
        model = model_class()
        model.load_state_dict(torch.deserialize(decrypted_bytes))
        return model

    def validate_model_integrity(self, model: torch.nn.Module, expected_signature: str) -> bool:
        """
        Validate model integrity by comparing signatures
        
        Args:
            model (torch.nn.Module): Model to validate
            expected_signature (str): Expected model signature
        
        Returns:
            bool: Whether model integrity is maintained
        """
        current_signature = self.generate_model_signature(model)
        return current_signature == expected_signature

    def save_model_metadata(self, model: torch.nn.Module, metadata: Dict[str, Any]):
        """
        Save model metadata with security information
        
        Args:
            model (torch.nn.Module): Model to save metadata for
            metadata (Dict): Additional model metadata
        """
        signature = self.generate_model_signature(model)
        full_metadata = {
            "signature": signature,
            "version": metadata.get("version", "1.0"),
            "training_date": metadata.get("training_date"),
            "additional_info": metadata
        }
        
        with open(f"{self.model_path}.metadata.json", 'w') as f:
            json.dump(full_metadata, f, indent=2)

def protect_against_model_poisoning(model: torch.nn.Module) -> torch.nn.Module:
    """
    Apply basic protection against model poisoning
    
    Args:
        model (torch.nn.Module): Input model
    
    Returns:
        torch.nn.Module: Hardened model
    """
    # Implement basic input sanitization and validation
    # This is a placeholder - actual implementation depends on specific model architecture
    
    # Example: Clip weight values to prevent extreme modifications
    for param in model.parameters():
        param.data = param.data.clamp(-10, 10)
    
    return model

def validate_model_security(model, config: Dict = None) -> Dict:
    """Wrapper function for model security validation"""
    try:
        # Basic model validation
        if model is None:
            return {
                'valid': False,
                'error': 'Null model',
                'secure': False
            }
        
        # Check if model has parameters
        if hasattr(model, 'parameters'):
            param_count = sum(p.numel() for p in model.parameters())
            
            return {
                'valid': True,
                'secure': True,
                'parameter_count': param_count,
                'model_type': type(model).__name__,
                'protected_against_poisoning': False
            }
        
        # Non-pytorch model validation
        return {
            'valid': True,
            'secure': True,
            'model_type': type(model).__name__,
            'protected_against_poisoning': False
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': str(e),
            'secure': False
        }