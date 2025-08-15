import hashlib
import pandas as pd
import numpy as np
from typing import Union, List, Dict
from cryptography.fernet import Fernet
from differential_privacy import PrivacyEngine

class DataSecurity:
    def __init__(self, encryption_key: bytes = None):
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)

    def anonymize_data(self, data: Union[pd.DataFrame, np.ndarray], 
                       columns_to_anonymize: List[str] = None) -> Union[pd.DataFrame, np.ndarray]:
        """
        Anonymize sensitive data columns using hashing
        
        Args:
            data (DataFrame or ndarray): Input data
            columns_to_anonymize (List[str]): Columns to anonymize
        
        Returns:
            Anonymized data
        """
        if isinstance(data, pd.DataFrame):
            anonymized_data = data.copy()
            
            if columns_to_anonymize is None:
                columns_to_anonymize = [
                    col for col in data.columns 
                    if any(sensitive in col.lower() for sensitive in ['id', 'name', 'email', 'phone'])
                ]
            
            for col in columns_to_anonymize:
                anonymized_data[col] = anonymized_data[col].apply(
                    lambda x: hashlib.sha256(str(x).encode()).hexdigest()
                )
            
            return anonymized_data
        
        # For numpy arrays, hash based on index
        return np.array([hashlib.sha256(str(val).encode()).hexdigest() for val in data])

    def encrypt_dataset(self, data: Union[pd.DataFrame, Dict]) -> bytes:
        """
        Encrypt entire dataset
        
        Args:
            data (DataFrame or Dict): Data to encrypt
        
        Returns:
            Encrypted bytes
        """
        # Convert to JSON for consistent serialization
        if isinstance(data, pd.DataFrame):
            data_json = data.to_json()
        else:
            data_json = json.dumps(data)
        
        return self.cipher_suite.encrypt(data_json.encode())

    def decrypt_dataset(self, encrypted_data: bytes) -> Union[pd.DataFrame, Dict]:
        """
        Decrypt dataset
        
        Args:
            encrypted_data (bytes): Encrypted data
        
        Returns:
            Decrypted data
        """
        decrypted_json = self.cipher_suite.decrypt(encrypted_data).decode()
        
        try:
            return pd.read_json(decrypted_json)
        except:
            return json.loads(decrypted_json)

    def apply_differential_privacy(self, data: np.ndarray, epsilon: float = 1.0) -> np.ndarray:
        """
        Apply differential privacy to numerical data
        
        Args:
            data (ndarray): Numerical data
            epsilon (float): Privacy budget (lower = more privacy)
        
        Returns:
            Privatized data
        """
        privacy_engine = PrivacyEngine()
        
        # Add Laplace noise to preserve differential privacy
        sensitivity = np.max(data) - np.min(data)
        noise = np.random.laplace(0, sensitivity / epsilon, data.shape)
        
        return data + noise

    def data_masking(self, data: Union[pd.DataFrame, np.ndarray], 
                     mask_percentage: float = 0.5) -> Union[pd.DataFrame, np.ndarray]:
        """
        Mask sensitive data for development environments
        
        Args:
            data (DataFrame or ndarray): Input data
            mask_percentage (float): Percentage of data to mask
        
        Returns:
            Masked data
        """
        if isinstance(data, pd.DataFrame):
            masked_data = data.copy()
            for col in masked_data.columns:
                mask_indices = np.random.choice(
                    masked_data.index, 
                    int(len(masked_data) * mask_percentage), 
                    replace=False
                )
                masked_data.loc[mask_indices, col] = '[MASKED]'
            return masked_data
        
        # For numpy arrays
        mask_indices = np.random.choice(
            range(len(data)), 
            int(len(data) * mask_percentage), 
            replace=False
        )
        masked_data = data.copy()
        masked_data[mask_indices] = '[MASKED]'
        return masked_data

    def audit_data_access(self, user: str, action: str, data_id: str):
        """
        Log data access for audit trail
        
        Args:
            user (str): User accessing data
            action (str): Type of data access
            data_id (str): Identifier for accessed data
        """
        audit_log = {
            "timestamp": datetime.now().isoformat(),
            "user": hashlib.sha256(user.encode()).hexdigest(),
            "action": action,
            "data_id": hashlib.sha256(data_id.encode()).hexdigest()
        }
        
        with open("/var/log/omega_data_access.log", "a") as log_file:
            json.dump(audit_log, log_file)
            log_file.write("\n")

    def right_to_be_forgotten(self, data: Union[pd.DataFrame, Dict], user_id: str) -> Union[pd.DataFrame, Dict]:
        """
        Remove all data associated with a specific user
        
        Args:
            data (DataFrame or Dict): Input data
            user_id (str): User identifier to remove
        
        Returns:
            Data with user's information removed
        """
        if isinstance(data, pd.DataFrame):
            # Remove rows containing user's hashed ID
            user_hash = hashlib.sha256(user_id.encode()).hexdigest()
            return data[~data.apply(lambda row: user_hash in row.values, axis=1)]
        
        # For dictionaries, remove user-specific entries
        return {k: v for k, v in data.items() if user_hash not in str(v)}