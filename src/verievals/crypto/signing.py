"""Ed25519 signing and verification.

Eval runs are signed so that a record can be attributed to the party that
produced it. We use Ed25519: deterministic signatures, small keys (32-byte raw
public key), and a well-reviewed implementation via ``cryptography``.

Key material is represented as lowercase hex of the 32-byte raw seed (private)
or 32-byte raw public key. Private keys must never be committed to a repository
(see ``.gitignore``).
"""

from __future__ import annotations

from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
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

_NO_ENCRYPTION = NoEncryption()


@dataclass(frozen=True)
class VerifyKey:
    """A public key used to verify signatures."""

    _key: Ed25519PublicKey

    @property
    def hex(self) -> str:
        raw = self._key.public_bytes(Encoding.Raw, PublicFormat.Raw)
        return raw.hex()

    @classmethod
    def from_hex(cls, value: str) -> VerifyKey:
        return cls(Ed25519PublicKey.from_public_bytes(bytes.fromhex(value)))

    def verify(self, message: bytes, signature_hex: str) -> bool:
        try:
            self._key.verify(bytes.fromhex(signature_hex), message)
            return True
        except (InvalidSignature, ValueError):
            return False


@dataclass(frozen=True)
class SigningKey:
    """A private key used to sign messages."""

    _key: Ed25519PrivateKey

    @property
    def hex(self) -> str:
        """Hex of the raw 32-byte private seed. Treat as a secret."""
        raw = self._key.private_bytes(
            Encoding.Raw, PrivateFormat.Raw, encryption_algorithm=_NO_ENCRYPTION
        )
        return raw.hex()

    @classmethod
    def from_hex(cls, value: str) -> SigningKey:
        return cls(Ed25519PrivateKey.from_private_bytes(bytes.fromhex(value)))

    @property
    def verify_key(self) -> VerifyKey:
        return VerifyKey(self._key.public_key())

    def sign(self, message: bytes) -> str:
        return self._key.sign(message).hex()


def generate_signing_key() -> SigningKey:
    """Generate a fresh Ed25519 signing key."""
    return SigningKey(Ed25519PrivateKey.generate())


def sign(key: SigningKey, message: bytes) -> str:
    """Sign ``message`` with ``key``; returns a hex signature."""
    return key.sign(message)


def verify(public_key_hex: str, message: bytes, signature_hex: str) -> bool:
    """Verify ``signature_hex`` over ``message`` for the given public key hex."""
    try:
        return VerifyKey.from_hex(public_key_hex).verify(message, signature_hex)
    except ValueError:
        return False
