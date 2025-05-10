import os
import base64
from cryptography.fernet import Fernet

class EnvKeyEncryptionManager:
    """
    Encryption manager that stores and retrieves keys from environment variables.
    This approach makes keys persistent across program runs while keeping them
    out of your source code.
    """
    
    def __init__(self, env_var_name="SUPREME_BOT_ENCRYPTION_KEY"):
        """
        Initialize encryption manager with an environment variable name.
        
        Args:
            env_var_name: Name of the environment variable to store/retrieve the key
        """
        self.env_var_name = env_var_name
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self):
        """
        Get the key from an environment variable or create a new one if not found.
        
        Returns:
            bytes: Fernet key
        """
        # Try to get the key from environment
        key = os.environ.get(self.env_var_name)
        
        if not key:
            # Generate a new key
            key = Fernet.generate_key().decode()
            
            # Store it in environment variable
            os.environ[self.env_var_name] = key
            
            print(f"Created new encryption key and stored in {self.env_var_name}")
            print(f"To make this key persistent across sessions, add this to your environment:")
            print(f"export {self.env_var_name}='{key}'")
        else:
            print(f"Using existing encryption key from {self.env_var_name}")
        
        # Return bytes for Fernet
        return key.encode() if isinstance(key, str) else key
    
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
        Get the key as a base64 string.
        
        Returns:
            str: Base64-encoded key
        """
        return self.key.decode() if isinstance(self.key, bytes) else self.key


# For managing multiple different keys (e.g., one per service)
class MultiKeyManager:
    """
    Manages multiple encryption keys, each stored in its own environment variable.
    Useful for different encryption needs (webhook, credentials, etc.)
    """
    
    def __init__(self):
        """Initialize the multi-key manager."""
        self.prefix = "SUPREME_BOT_KEY_"
        self.managers = {}
    
    def get_manager(self, service_name):
        """
        Get or create an encryption manager for a specific service.
        
        Args:
            service_name: Service identifier (e.g., 'webhook', 'credentials')
            
        Returns:
            EnvKeyEncryptionManager: Manager for the service
        """
        service_name = service_name.upper()
        env_var = f"{self.prefix}{service_name}"
        
        if service_name not in self.managers:
            self.managers[service_name] = EnvKeyEncryptionManager(env_var)
            
        return self.managers[service_name]
    
    def encrypt(self, service_name, message):
        """
        Encrypt a message for a specific service.
        
        Args:
            service_name: Service identifier
            message: Message to encrypt
            
        Returns:
            str: Encrypted message
        """
        manager = self.get_manager(service_name)
        return manager.encrypt(message)
    
    def decrypt(self, service_name, encrypted_message):
        """
        Decrypt a message for a specific service.
        
        Args:
            service_name: Service identifier
            encrypted_message: Encrypted message
            
        Returns:
            str: Decrypted message
        """
        manager = self.get_manager(service_name)
        return manager.decrypt(encrypted_message)


# Example usage showing both approaches
def example_usage():
    print("===== Example 1: Single Key Manager =====")
    # Basic usage with a single key
    manager = EnvKeyEncryptionManager()
    webhook = "https://discord.com/api/webhooks/1234567890/abcdefghijklmnopqrstuvwxyz"
    
    # Encrypt
    encrypted = manager.encrypt(webhook)
    print(f"Encrypted webhook: {encrypted}")
    
    # Decrypt
    decrypted = manager.decrypt(encrypted)
    print(f"Decrypted webhook: {decrypted}")
    
    print("\n===== Example 2: Multiple Key Manager =====")
    # Using multiple keys for different services
    multi_manager = MultiKeyManager()
    
    # Encrypt webhook with its own key
    webhook_encrypted = multi_manager.encrypt("webhook", webhook)
    print(f"Encrypted webhook with WEBHOOK key: {webhook_encrypted}")
    
    # Encrypt credentials with a different key
    credentials = "username:password123"
    creds_encrypted = multi_manager.encrypt("credentials", credentials)
    print(f"Encrypted credentials with CREDENTIALS key: {creds_encrypted}")
    
    # Decrypt each with their respective keys
    webhook_decrypted = multi_manager.decrypt("webhook", webhook_encrypted)
    creds_decrypted = multi_manager.decrypt("credentials", creds_encrypted)
    
    print(f"Decrypted webhook: {webhook_decrypted}")
    print(f"Decrypted credentials: {creds_decrypted}")
    
    print("\nKeys are now stored in these environment variables:")
    for var in [manager.env_var_name, 
                multi_manager.get_manager("webhook").env_var_name,
                multi_manager.get_manager("credentials").env_var_name]:
        print(f"- {var}")


if __name__ == "__main__":
    example_usage()