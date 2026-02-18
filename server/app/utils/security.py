from cryptography.fernet import Fernet
import os

# Generate this once and store in your .env file on the server
# key = Fernet.generate_key() 
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key()) 

cipher = Fernet(ENCRYPTION_KEY)

def encrypt_api_key(raw_key: str) -> str:
    return cipher.encrypt(raw_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    return cipher.decrypt(encrypted_key.encode()).decode()