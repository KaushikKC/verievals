"""Tests for Ed25519 signing and verification."""

from __future__ import annotations

from verievals.crypto.signing import (
    SigningKey,
    VerifyKey,
    generate_signing_key,
    sign,
    verify,
)


def test_sign_and_verify_roundtrip() -> None:
    key = generate_signing_key()
    msg = b"verifiable evals"
    sig = key.sign(msg)
    assert key.verify_key.verify(msg, sig)


def test_module_level_helpers() -> None:
    key = generate_signing_key()
    sig = sign(key, b"payload")
    assert verify(key.verify_key.hex, b"payload", sig)


def test_tampered_message_fails() -> None:
    key = generate_signing_key()
    sig = key.sign(b"original")
    assert not key.verify_key.verify(b"modified", sig)


def test_wrong_key_fails() -> None:
    key_a = generate_signing_key()
    key_b = generate_signing_key()
    sig = key_a.sign(b"msg")
    assert not key_b.verify_key.verify(b"msg", sig)


def test_signing_is_deterministic() -> None:
    # Ed25519 signatures are deterministic for a fixed key/message.
    key = generate_signing_key()
    assert key.sign(b"x") == key.sign(b"x")


def test_private_key_hex_roundtrip() -> None:
    key = generate_signing_key()
    restored = SigningKey.from_hex(key.hex)
    assert restored.hex == key.hex
    assert restored.verify_key.hex == key.verify_key.hex


def test_public_key_hex_roundtrip() -> None:
    key = generate_signing_key()
    vk_hex = key.verify_key.hex
    restored = VerifyKey.from_hex(vk_hex)
    sig = key.sign(b"data")
    assert restored.verify(b"data", sig)


def test_public_key_is_32_bytes_hex() -> None:
    key = generate_signing_key()
    assert len(key.verify_key.hex) == 64


def test_verify_with_malformed_signature_returns_false() -> None:
    key = generate_signing_key()
    assert not verify(key.verify_key.hex, b"msg", "not-hex")
    assert not key.verify_key.verify(b"msg", "abcd")
