"""Canonical (deterministic) JSON encoding.

Two independent parties must be able to hash "the same" record and obtain the
*same bytes*. Ordinary ``json.dumps`` does not guarantee this: key order,
whitespace, and non-ASCII escaping all vary. This module pins those choices so
that the byte serialization of a JSON-compatible value is a pure function of the
value.

The rules (a pragmatic subset of RFC 8785 / JCS):

* object keys are sorted lexicographically by their UTF-8 code units;
* no insignificant whitespace (``", "`` / ``": "`` become ``","`` / ``":"``);
* UTF-8 output, with non-ASCII characters emitted literally (not ``\\uXXXX``);
* ``NaN`` and ``Infinity`` are rejected -- they have no canonical JSON form.

Floats are intentionally discouraged in records (use strings or integers for
anything that must round-trip exactly); we still encode them via Python's
shortest-round-trip ``repr`` for convenience, but callers that need
bit-for-bit determinism across languages should avoid floats entirely.
"""

from __future__ import annotations

import json
from typing import Any


def canonical_dumps(value: Any) -> str:
    """Serialize ``value`` to a canonical JSON *string*.

    Raises:
        ValueError: if the value contains ``NaN``/``Infinity`` or a type that is
            not JSON-serializable.
    """
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except ValueError as exc:  # allow_nan=False raises ValueError on NaN/Infinity
        raise ValueError(f"value is not canonically encodable: {exc}") from exc


def canonical_encode(value: Any) -> bytes:
    """Serialize ``value`` to canonical JSON *bytes* (UTF-8)."""
    return canonical_dumps(value).encode("utf-8")
