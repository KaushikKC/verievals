"""Cryptographic primitives for verifiable evals.

This package provides the building blocks that make eval results verifiable:

- :mod:`verievals.crypto.canonical` -- deterministic ("canonical") JSON encoding,
  so two parties hashing the same logical object always get the same bytes.
- :mod:`verievals.crypto.hashing` -- SHA-256 content addressing over canonical bytes.
- :mod:`verievals.crypto.merkle` -- an RFC 6962-style Merkle tree with inclusion proofs.
- :mod:`verievals.crypto.signing` -- Ed25519 keypair generation, signing, and verification.
"""

from verievals.crypto.canonical import canonical_dumps, canonical_encode
from verievals.crypto.hashing import content_hash, sha256_hex
from verievals.crypto.merkle import (
    InclusionProof,
    merkle_proof,
    merkle_root,
    verify_inclusion_proof,
)
from verievals.crypto.signing import (
    SigningKey,
    VerifyKey,
    generate_signing_key,
    sign,
    verify,
)

__all__ = [
    "InclusionProof",
    "SigningKey",
    "VerifyKey",
    "canonical_dumps",
    "canonical_encode",
    "content_hash",
    "generate_signing_key",
    "merkle_proof",
    "merkle_root",
    "sha256_hex",
    "sign",
    "verify",
    "verify_inclusion_proof",
]
