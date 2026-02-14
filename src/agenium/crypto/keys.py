"""
Key generation and management.

Uses Ed25519 for agent identity keys.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)


@dataclass
class KeyPair:
    """Ed25519 key pair."""

    private_key: Ed25519PrivateKey
    public_key: Ed25519PublicKey
    public_key_b64: str

    def sign(self, data: bytes) -> bytes:
        """Sign data with the private key."""
        return self.private_key.sign(data)

    def verify(self, signature: bytes, data: bytes) -> bool:
        """Verify a signature. Returns False if invalid."""
        try:
            self.public_key.verify(signature, data)
            return True
        except Exception:
            return False

    def private_key_pem(self) -> str:
        """Export private key as PEM."""
        return self.private_key.private_bytes(
            Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
        ).decode()

    def public_key_pem(self) -> str:
        """Export public key as PEM."""
        return self.public_key.public_bytes(
            Encoding.PEM, PublicFormat.SubjectPublicKeyInfo
        ).decode()


def generate_keypair() -> KeyPair:
    """Generate a new Ed25519 key pair."""
    private = Ed25519PrivateKey.generate()
    public = private.public_key()
    raw = public.public_bytes(Encoding.Raw, PublicFormat.Raw)
    b64 = base64.b64encode(raw).decode()
    return KeyPair(private_key=private, public_key=public, public_key_b64=b64)
