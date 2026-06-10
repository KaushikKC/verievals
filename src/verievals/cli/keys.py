"""Signing-key file helpers for the CLI.

A keypair is stored as two files next to ``<out>``:

* ``<out>.key`` -- the private signing key (hex of the 32-byte seed). Written
  with ``0600`` permissions and ignored by git via ``.gitignore``.
* ``<out>.pub`` -- the public verify key (hex). Safe to publish.
"""

from __future__ import annotations

import os
from pathlib import Path

from verievals.crypto.signing import SigningKey, generate_signing_key


def key_paths(out: str | Path) -> tuple[Path, Path]:
    """Return the ``(private, public)`` paths for an ``out`` prefix."""
    base = Path(out)
    return base.with_suffix(".key"), base.with_suffix(".pub")


def save_keypair(key: SigningKey, out: str | Path) -> tuple[Path, Path]:
    """Write ``<out>.key`` (private, 0600) and ``<out>.pub`` (public)."""
    private_path, public_path = key_paths(out)
    private_path.parent.mkdir(parents=True, exist_ok=True)

    # Create the private key file with restrictive permissions from the start.
    fd = os.open(private_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(key.hex + "\n")

    public_path.write_text(key.verify_key.hex + "\n", encoding="utf-8")
    return private_path, public_path


def generate_and_save(out: str | Path) -> tuple[SigningKey, Path, Path]:
    """Generate a fresh keypair and persist it."""
    key = generate_signing_key()
    private_path, public_path = save_keypair(key, out)
    return key, private_path, public_path


def load_signing_key(path: str | Path) -> SigningKey:
    """Load a signing key from a ``.key`` file (hex)."""
    text = Path(path).read_text(encoding="utf-8").strip()
    return SigningKey.from_hex(text)
