# scripts/decryptor_bot.py

import logging
from core.encryption import decrypt
from core.secure_webhook import BOT_KEY_FILE, WEBHOOK_FILE

def main():
    try:
        with open(BOT_KEY_FILE, "rb") as f:
            key = f.read()
        with open(WEBHOOK_FILE, "rb") as f:
            encrypted = f.read()
        url = decrypt(encrypted, key)
        print(f"[decryptor_bot] Webhook URL:\n{url}")
    except Exception as e:
        logging.error(f"[decryptor_bot] Failed: {e}")

if __name__ == "__main__":
    main()
