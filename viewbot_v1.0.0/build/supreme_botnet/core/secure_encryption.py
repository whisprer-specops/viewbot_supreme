# core/secure_encryption.py

import os
import json
import base64
import platform
import logging
from pathlib import Path
from cryptography.fernet import Fernet

class PersistentKeyManager:
    """
    Encryption manager that handles persisting encryption keys
    between program runs using environment variables and config files.
    """
    
    def __init__(self, service_name="default", config_dir=None):
        """
        Initialize persistent key manager.
        
        Args:
            service_name: Service identifier (will be used in env var names)
            config_dir: Directory to store persisted keys (default: ~/.supremebot)
        """
        self.service_name = service_name.upper()
        self.env_var_name = f"SUPREME_BOT_KEY_{self.service_name}"
        
        # Set up config directory
        if config_dir is None:
            self.config_dir = str(Path.home() / ".supremebot")
        else:
            self.config_dir = config_dir
            
        # Create config directory if it doesn't exist
        Path(self.config_dir).mkdir(parents=True, exist_ok=True)
        self.config_file = Path(self.config_dir) / "keys.json"
        
        # Get or create key
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
        
        logging.debug(f"Initialized PersistentKeyManager for service {self.service_name}")
    
    def _get_or_create_key(self):
        """
        Get key from environment, stored file, or create new one.
        
        Returns:
            bytes: Fernet encryption key
        """
        # First, check environment variable
        key = os.environ.get(self.env_var_name)
        
        if key:
            logging.debug(f"Using encryption key from {self.env_var_name} environment variable")
            return key.encode() if isinstance(key, str) else key
            
        # If not in environment, check config file
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    keys = json.load(f)
                    
                key = keys.get(self.service_name)
                if key:
                    logging.debug(f"Using stored encryption key for {self.service_name} from {self.config_file}")
                    # Also set environment variable for future use
                    os.environ[self.env_var_name] = key
                    return key.encode() if isinstance(key, str) else key
            except Exception as e:
                logging.error(f"Error reading keys file: {e}")
        
        # If no key found, create a new one
        key = Fernet.generate_key().decode()
        
        # Store in environment variable
        os.environ[self.env_var_name] = key
        
        # Save to config file
        self._save_key_to_file(key)
        
        logging.info(f"Created new encryption key for {self.service_name} and saved it")
        return key.encode() if isinstance(key, str) else key
    
    def _save_key_to_file(self, key):
        """
        Save key to config file.
        
        Args:
            key: Encryption key to save
        """
        # Read existing keys if file exists
        keys = {}
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    keys = json.load(f)
            except:
                pass
                
        # Update with new key
        keys[self.service_name] = key
        
        # Write back to file
        with open(self.config_file, 'w') as f:
            json.dump(keys, f, indent=2)
            
        logging.debug(f"Saved {self.service_name} key to {self.config_file}")
    
    def encrypt(self, message):
        """
        Encrypt a message.
        
        Args:
            message: Text to encrypt
            
        Returns:
            str: Encrypted message (base64-encoded)
        """
        if isinstance(message, str):
            message = message.encode()
        return self.cipher.encrypt(message).decode()
    
    def decrypt(self, encrypted_message):
        """
        Decrypt an encrypted message.
        
        Args:
            encrypted_message: Encrypted message to decrypt
            
        Returns:
            str: Decrypted message
        """
        if isinstance(encrypted_message, str):
            encrypted_message = encrypted_message.encode()
        return self.cipher.decrypt(encrypted_message).decode()
    
    def get_key_string(self):
        """
        Get the key as a string.
        
        Returns:
            str: Base64-encoded key
        """
        return self.key.decode() if isinstance(self.key, bytes) else self.key
    
    def create_env_var_script(self, output_file=None):
        """
        Create a script to set environment variables with the current keys.
        This is useful for setting up environments on different machines.
        
        Args:
            output_file: Optional path to save the script
            
        Returns:
            str: Script content
        """
        if platform.system() == "Windows":
            script = f'@echo off\nsetx {self.env_var_name} "{self.get_key_string()}"\n'
            file_ext = ".bat"
        else:  # Linux/Mac
            script = f'#!/bin/bash\nexport {self.env_var_name}="{self.get_key_string()}"\n'
            file_ext = ".sh"
            
        if output_file:
            # If no extension provided, add the appropriate one
            if not Path(output_file).suffix:
                output_file = f"{output_file}{file_ext}"
                
            with open(output_file, 'w') as f:
                f.write(script)
                
            # Make executable on Linux/Mac
            if platform.system() != "Windows":
                os.chmod(output_file, 0o755)
                
            logging.info(f"Created environment setup script: {output_file}")
            
        return script