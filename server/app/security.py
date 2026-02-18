from cryptography.fernet import Fernet
import os
import base64

# In a real app, load this from .env. For now, we generate/use a static key for dev.
# This key MUST be 32 url-safe base64-encoded bytes.
# We will use a fixed key for this demo so it persists across restarts.
KEY = b'8_5V3d_v4p8p4u7H8d3_843d837d834d834d834d834=' 

def get_cipher():
    # If the key above is invalid, we generate a new one (for safety)
    try:
        return Fernet(KEY)
    except:
        return Fernet(Fernet.generate_key())

def encrypt_value(value: str) -> str:
    if not value: return None
    cipher = get_cipher()
    return cipher.encrypt(value.encode()).decode()

def decrypt_value(encrypted_value: str) -> str:
    if not encrypted_value: return None
    cipher = get_cipher()
    return cipher.decrypt(encrypted_value.encode()).decode()
