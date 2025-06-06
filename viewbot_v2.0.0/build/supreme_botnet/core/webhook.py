### core/webhook.py ###

import logging
import requests

class WebhookManager:
    """
    Manages sending notifications to webhooks (e.g., Discord).
    """
    
    def __init__(self, webhook_url, encryption_manager=None):
        """
        Initialize webhook manager.
        
        Args:
            webhook_url: URL to send webhooks to
            encryption_manager: Optional EncryptionManager for encrypting payloads
        """
        self.webhook_url = webhook_url
        self.encryption_manager = encryption_manager
        
    def send_notification(self, message, encrypt=True):
        """
        Send a notification to the webhook.
        
        Args:
            message: Message to send
            encrypt: Whether to encrypt the message
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if encrypt and self.encryption_manager:
                encrypted_message = self.encryption_manager.encrypt(message)
                payload = {"content": f"Encrypted: {encrypted_message}"}
            else:
                payload = {"content": message}
                
            headers = {"Content-Type": "application/json"}
            response = requests.post(self.webhook_url, json=payload, headers=headers)
            
            if response.status_code == 204:
                logging.info("Webhook sent successfully")
                return True
            else:
                logging.error(f"Failed to send webhook: {response.status_code}")
                return False
        except Exception as e:
            logging.error(f"Error sending webhook: {e}")
            return False

