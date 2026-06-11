"""Shared number extraction used by the numeric and GSM8K scorers."""

from __future__ import annotations

import re

# Optional sign, digits with optional thousands separators, optional decimal.
NUMBER_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")


def _parse(token: str) -> float | None:
    try:
        return float(token.replace(",", ""))
    except ValueError:
        return None


def first_number(text: str) -> float | None:
    """Return the first number in ``text``, or ``None``."""
    match = NUMBER_RE.search(text)
    return _parse(match.group(0)) if match else None


def last_number(text: str) -> float | None:
    """Return the last number in ``text``, or ``None``.

    The last number is the conventional answer extraction for chain-of-thought
    math output (the model reasons, then states the final figure).
    """
    matches = NUMBER_RE.findall(text)
    return _parse(matches[-1]) if matches else None
