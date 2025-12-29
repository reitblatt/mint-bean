"""Encryption utilities for sensitive data.

This module provides encryption/decryption for sensitive fields stored in the database,
such as API keys and secrets. It uses Fernet (symmetric encryption) from the cryptography library.

Security Notes:
- The encryption key MUST be stored securely (environment variable, secrets manager, etc.)
- The key should be 32 URL-safe base64-encoded bytes
- Rotating the key requires re-encrypting all encrypted data
- Never commit the encryption key to version control

Usage:
    from app.core.encryption import encrypt_value, decrypt_value

    # Encrypt a secret before storing
    encrypted = encrypt_value("my-secret-api-key")

    # Decrypt when retrieving
    decrypted = decrypt_value(encrypted)
"""

import os

from cryptography.fernet import Fernet


def get_encryption_key() -> bytes:
    """
    Get the encryption key from environment variable.

    The key should be a 32-byte URL-safe base64-encoded string.
    You can generate a new key with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

    Returns:
        Encryption key as bytes

    Raises:
        ValueError: If ENCRYPTION_KEY is not set or invalid
    """
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise ValueError(
            "ENCRYPTION_KEY environment variable not set. "
            'Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        )

    try:
        return key.encode()
    except Exception as e:
        raise ValueError(f"Invalid ENCRYPTION_KEY format: {e}") from e


def get_fernet() -> Fernet:
    """
    Get a Fernet cipher instance.

    Returns:
        Fernet cipher configured with the encryption key
    """
    return Fernet(get_encryption_key())


def encrypt_value(plaintext: str | None) -> str | None:
    """
    Encrypt a string value.

    Args:
        plaintext: The value to encrypt (or None)

    Returns:
        Encrypted value as a string (or None if input was None)
    """
    if plaintext is None:
        return None

    if not plaintext:  # Empty string
        return ""

    try:
        fernet = get_fernet()
        encrypted_bytes = fernet.encrypt(plaintext.encode())
        return encrypted_bytes.decode()
    except Exception as e:
        raise ValueError(f"Encryption failed: {e}") from e


def decrypt_value(ciphertext: str | None) -> str | None:
    """
    Decrypt an encrypted string value.

    Args:
        ciphertext: The encrypted value (or None)

    Returns:
        Decrypted plaintext string (or None if input was None)
    """
    if ciphertext is None:
        return None

    if not ciphertext:  # Empty string
        return ""

    try:
        fernet = get_fernet()
        decrypted_bytes = fernet.decrypt(ciphertext.encode())
        return decrypted_bytes.decode()
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}") from e


def is_encrypted(value: str | None) -> bool:
    """
    Check if a value appears to be encrypted.

    This is a heuristic check based on Fernet token format.
    Fernet tokens start with "gAAAAA" (base64 of timestamp + padding).

    Args:
        value: The value to check

    Returns:
        True if value looks encrypted, False otherwise
    """
    if not value:
        return False

    # Fernet tokens are base64 and typically start with 'gAAAAA'
    # This is not foolproof but good enough for migration detection
    return value.startswith("gAAAAA")
