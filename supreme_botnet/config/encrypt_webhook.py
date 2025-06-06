import os
import sys
from cryptography.fernet import Fernet

KEY_FILE = os.path.join(os.path.dirname(__file__), "bot_key.txt")
ENC_FILE = os.path.join(os.path.dirname(__file__), "webhook.enc")


def generate_key():
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    print(f"[+] New key generated and saved to {KEY_FILE}")
    return key


def load_or_generate_key():
    if not os.path.exists(KEY_FILE):
        return generate_key()
    with open(KEY_FILE, "rb") as f:
        return f.read()


def encrypt_webhook(url: str):
    key = load_or_generate_key()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(url.encode())
    with open(ENC_FILE, "wb") as f:
        f.write(encrypted)
    print(f"[+] Encrypted webhook saved to {ENC_FILE}")


if __name__ == "__main__":
    try:
        webhook = input("Enter your webhook URL to encrypt:\n> ").strip()
        if webhook:
            encrypt_webhook(webhook)
        else:
            print("[-] No URL provided. Aborting.")
    except Exception as e:
        print(f"[!] Error: {e}")
        sys.exit(1)
