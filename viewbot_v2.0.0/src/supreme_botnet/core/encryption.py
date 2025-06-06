### core/encryption.py ###

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class EncryptionManager:
    """
    Manages encryption and decryption of sensitive data.
    """
    
    def __init__(self, password=None):
        """
        Initialize encryption manager with optional password.
        
        Args:
            password: Optional password for encryption (default: random value)
        """
        self.password = password or "supreme_botnet_secure"
        self.cipher = self._generate_cipher()
        
    def _generate_cipher(self):
        """
        Generate a Fernet cipher for encryption.
        
        Returns:
            Fernet: Cipher for encryption/decryption
        """
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
        return Fernet(key)
        
    def encrypt(self, message):
        """
        Encrypt a message.
        
        Args:
            message: Message to encrypt
            
        Returns:
            str: Encrypted message (base64-encoded)
        """
        return self.cipher.encrypt(message.encode()).decode()
        
    def decrypt(self, encrypted_message):
        """
        Decrypt an encrypted message.
        
        Args:
            encrypted_message: Encrypted message to decrypt
            
        Returns:
            str: Decrypted message
        """
        return self.cipher.decrypt(encrypted_message.encode()).decode()
