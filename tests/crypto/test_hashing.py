"""Tests for content-addressed hashing."""

from __future__ import annotations

import hashlib

from verievals.crypto.hashing import content_hash, sha256_hex


def test_sha256_hex_matches_hashlib() -> None:
    assert sha256_hex(b"abc") == hashlib.sha256(b"abc").hexdigest()


def test_content_hash_is_stable_across_key_order() -> None:
    assert content_hash({"a": 1, "b": 2}) == content_hash({"b": 2, "a": 1})


def test_content_hash_changes_with_value() -> None:
    assert content_hash({"a": 1}) != content_hash({"a": 2})


def test_content_hash_is_lowercase_hex_of_len_64() -> None:
    h = content_hash({"hello": "world"})
    assert len(h) == 64
    assert h == h.lower()
    int(h, 16)  # parses as hex
