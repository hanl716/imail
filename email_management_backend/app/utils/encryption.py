from cryptography.fernet import Fernet, InvalidToken
from app.core.config import FERNET_KEY

_cipher_suite = None

if FERNET_KEY:
    try:
        key_bytes = FERNET_KEY.encode()  # Convert to bytes
        # This also validates the key is correctly formatted for Fernet
        _cipher_suite = Fernet(key_bytes)
        print("Encryption service initialized successfully with FERNET_KEY.")
    except (ValueError, TypeError) as e:
        # This error could occur if FERNET_KEY is not valid base64, for example.
        print(f"CRITICAL: Invalid FERNET_KEY format. Encryption disabled. Error: {e}")
        # _cipher_suite remains None
    except Exception as e:
        print(f"CRITICAL: Error initializing Fernet with key. Encryption disabled. Error: {e}")
        # _cipher_suite remains None
else:
    print("CRITICAL: FERNET_KEY not found in environment. Encryption disabled.")
    # _cipher_suite remains None

def encrypt_data(data: str) -> bytes | None:
    if not _cipher_suite:
        print("CRITICAL ERROR: Attempted to encrypt data but encryption service is not available (missing/invalid FERNET_KEY).")
        # In a strict application, you might raise an exception here to halt operations that require encryption.
        # For now, returning None or raising a less fatal error might be considered if some parts of app can work without it.
        # However, for credentials, this is a critical failure.
        raise ConnectionAbortedError("Encryption service not available due to missing or invalid FERNET_KEY.")

    if data is None: # Handle None input explicitly, though Fernet expects bytes.
        return None
    if not isinstance(data, str): # Ensure input is string before encoding
        raise TypeError("Data to encrypt must be a string.")

    return _cipher_suite.encrypt(data.encode('utf-8'))

def decrypt_data(encrypted_data_bytes: bytes) -> str | None:
    if not _cipher_suite:
        print("CRITICAL ERROR: Attempted to decrypt data but decryption service is not available (missing/invalid FERNET_KEY).")
        raise ConnectionAbortedError("Decryption service not available due to missing or invalid FERNET_KEY.")

    if encrypted_data_bytes is None:
        return None
    if not isinstance(encrypted_data_bytes, bytes):
        raise TypeError("Encrypted data must be bytes.")

    try:
        decrypted_bytes = _cipher_suite.decrypt(encrypted_data_bytes)
        return decrypted_bytes.decode('utf-8')
    except InvalidToken:
        # This occurs if the token is invalid, tampered, or encrypted with a different key.
        print("ERROR: Failed to decrypt data. Invalid token or key.")
        # Depending on policy, you might raise a custom error or return None/empty string.
        # Raising an error is often better for security-sensitive data.
        raise ValueError("Failed to decrypt data. Invalid token or key.")
    except Exception as e: # Catch other potential decryption errors
        print(f"ERROR: An unexpected error occurred during decryption: {e}")
        raise ValueError(f"Decryption failed due to an unexpected error: {e}")
