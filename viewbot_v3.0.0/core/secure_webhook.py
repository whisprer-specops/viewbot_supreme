# core/secure_webhook.py

import requests
import logging
from pathlib import Path

class SecureWebhookManager:
    """
    Enhanced webhook manager with secure storage of webhook URLs.
    """
    
    def __init__(self, webhook_url=None, key_manager=None):
        """
        Initialize secure webhook manager.
        
        Args:
            webhook_url: Discord webhook URL
            key_manager: PersistentKeyManager instance
        """
        self.key_manager = key_manager
        
        # Store webhook URL if provided
        if webhook_url:
            self.set_webhook_url(webhook_url)
    
    def set_webhook_url(self, webhook_url):
        """
        Encrypt and store webhook URL.
        
        Args:
            webhook_url: Discord webhook URL
        """
        if not self.key_manager:
            logging.error("No key manager available for webhook encryption")
            return False
            
        # Encrypt webhook URL
        encrypted_webhook = self.key_manager.encrypt(webhook_url)
        
        # Store encrypted webhook
        webhook_file = Path(self.key_manager.config_dir) / "webhook.enc"
        with open(webhook_file, 'w') as f:
            f.write(encrypted_webhook)
            
        logging.info(f"Webhook URL encrypted and stored at {webhook_file}")
        return True
    
    def get_webhook_url(self):
        """
        Retrieve and decrypt webhook URL.
        
        Returns:
            str: Decrypted webhook URL or None if not available
        """
        if not self.key_manager:
            logging.error("No key manager available for webhook decryption")
            return None
            
        # Try to load encrypted webhook from file
        webhook_file = Path(self.key_manager.config_dir) / "webhook.enc"
        if not webhook_file.exists():
            logging.warning(f"No stored webhook found at {webhook_file}")
            return None
            
        try:
            with open(webhook_file, 'r') as f:
                encrypted_webhook = f.read().strip()
                
            # Decrypt webhook URL
            return self.key_manager.decrypt(encrypted_webhook)
        except Exception as e:
            logging.error(f"Error decrypting webhook URL: {e}")
            return None
    
    def send_notification(self, message):
        """
        Send a notification to the webhook.
        
        Args:
            message: Message to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        webhook_url = self.get_webhook_url()
        if not webhook_url:
            logging.warning("Cannot send notification: No webhook URL available")
            return False
            
        try:
            # Prepare payload
            payload = {
                "content": message
            }
            
            # Send request
            response = requests.post(webhook_url, json=payload)
            
            # Check response
            if response.status_code == 204:
                return True
            else:
                logging.warning(f"Webhook notification failed with status code {response.status_code}")
                return False
        except Exception as e:
            logging.error(f"Error sending webhook notification: {e}")
            return False