# core/encryption.py

from cryptography.fernet import Fernet

def generate_key():
    return Fernet.generate_key()

def encrypt(data: str, key: bytes) -> bytes:
    f = Fernet(key)
    return f.encrypt(data.encode())

def decrypt(token: bytes, key: bytes) -> str:
    f = Fernet(key)
    return f.decrypt(token).decode()
