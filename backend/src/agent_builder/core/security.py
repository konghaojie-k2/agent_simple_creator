# -*- coding: utf-8 -*-
"""Security utilities including encryption."""

import base64
from typing import Optional

from cryptography.fernet import Fernet

from agent_builder.core.config import settings


class EncryptionManager:
    """API Key encryption manager using Fernet."""

    def __init__(self, key: Optional[str] = None):
        if key:
            # Use provided key or generate new one
            key_bytes = key.encode() if isinstance(key, str) else key
            # Ensure key is 32 bytes for Fernet (URL-safe base64 encoded)
            if len(key_bytes) < 32:
                key_bytes = key_bytes.ljust(32, b'0')
            # Generate a valid Fernet key from the input
            # Fernet requires a 32-byte key that is URL-safe base64 encoded
            self._key = base64.urlsafe_b64encode(key_bytes[:32])
        else:
            self._key = Fernet.generate_key()

        self._fernet = Fernet(self._key)

    @property
    def key(self) -> str:
        """Get the encryption key as string."""
        return self._key.decode()

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string."""
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a ciphertext string."""
        return self._fernet.decrypt(ciphertext.encode()).decode()

    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key."""
        return Fernet.generate_key().decode()


# Global encryption manager
encryption_manager = EncryptionManager(settings.ENCRYPTION_KEY)


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key."""
    return encryption_manager.encrypt(api_key)


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key."""
    return encryption_manager.decrypt(encrypted_key)
