"""SHA-256 content addressing over canonical JSON.

A *content hash* is the SHA-256 of the canonical encoding of a value, returned
as lowercase hex. Because the encoding is deterministic (see
:mod:`verievals.crypto.canonical`), the content hash is a stable identifier for
a logical object: anyone who has the object can recompute it and get the same
value.
"""

from __future__ import annotations

import hashlib
from typing import Any

from verievals.crypto.canonical import canonical_encode


def sha256_hex(data: bytes) -> str:
    """Return the lowercase hex SHA-256 digest of raw ``data``."""
    return hashlib.sha256(data).hexdigest()


def content_hash(value: Any) -> str:
    """Return the content hash (hex SHA-256 of canonical JSON) of ``value``."""
    return sha256_hex(canonical_encode(value))
