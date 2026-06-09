"""Tests for canonical JSON encoding."""

from __future__ import annotations

import math

import pytest

from verievals.crypto.canonical import canonical_dumps, canonical_encode


def test_keys_are_sorted_recursively() -> None:
    value = {"b": 1, "a": {"d": 4, "c": 3}}
    assert canonical_dumps(value) == '{"a":{"c":3,"d":4},"b":1}'


def test_no_insignificant_whitespace() -> None:
    assert canonical_dumps({"a": 1, "b": [1, 2]}) == '{"a":1,"b":[1,2]}'


def test_key_order_does_not_affect_output() -> None:
    assert canonical_encode({"x": 1, "y": 2}) == canonical_encode({"y": 2, "x": 1})


def test_non_ascii_is_emitted_literally() -> None:
    # Not escaped as \uXXXX; encoded as UTF-8 bytes.
    assert canonical_encode({"k": "café"}) == '{"k":"café"}'.encode()


def test_unicode_string_roundtrips_in_bytes() -> None:
    encoded = canonical_encode({"emoji": "🔒"})
    assert "🔒".encode() in encoded


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_nan_and_infinity_are_rejected(bad: float) -> None:
    with pytest.raises(ValueError):
        canonical_dumps({"x": bad})


def test_non_serializable_type_is_rejected() -> None:
    with pytest.raises(ValueError):
        canonical_dumps({"x": object()})


def test_encode_is_utf8_bytes() -> None:
    assert canonical_encode({"a": 1}) == b'{"a":1}'
