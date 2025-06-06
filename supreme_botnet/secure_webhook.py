# core/secure_webhook.py

import logging
import base64
from cryptography.fernet import Fernet
import requests
from pathlib import Path

BOT_KEY_FILE = Path("config/bot_key.txt")
WEBHOOK_FILE = Path("config/webhook.enc")

class PersistentKeyManager:
    def __init__(self, config_dir="config"):
        self.key_path = Path(config_dir) / "bot_key.txt"
        self.key = None
        self._load_key()

    def _load_key(self):
        try:
            with open(self.key_path, "r") as f:
                self.key = f.read().strip()
            self.fernet = Fernet(self.key)
        except Exception as e:
            logging.warning(f"[PersistentKeyManager] Failed to load key: {e}")

    def decrypt(self, path=WEBHOOK_FILE):
        try:
            with open(path, "rb") as f:
                encrypted = f.read()
            return self.fernet.decrypt(encrypted).decode()
        except Exception as e:
            logging.error(f"[PersistentKeyManager] Decryption error: {e}")
            return None


class SecureWebhookManager:
    def __init__(self, override_url=None, key_manager=None):
        self.key_manager = key_manager or PersistentKeyManager()
        self.url = override_url or self.key_manager.decrypt()

    def send_notification(self, message):
        if not self.url:
            logging.warning("[SecureWebhookManager] No webhook URL configured.")
            return
        try:
            requests.post(self.url, json={"content": message})
        except Exception as e:
            logging.warning(f"[SecureWebhookManager] Failed to post: {e}")
