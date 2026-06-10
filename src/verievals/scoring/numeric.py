"""Numeric scorer.

Extracts the first number from the model output and compares it to the expected
value within a tolerance. Handles negatives, decimals, and thousands separators
(``1,000``). This lets a model answer ``"The answer is 42."`` and still match an
expected ``"42"``.
"""

from __future__ import annotations

import re

from verievals.scoring.base import Score, Scorer

# Matches optional sign, digits with optional thousands separators, optional decimal.
_NUMBER_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")


def _first_number(text: str) -> float | None:
    match = _NUMBER_RE.search(text)
    if match is None:
        return None
    try:
        return float(match.group(0).replace(",", ""))
    except ValueError:
        return None


class NumericScorer(Scorer):
    """Pass iff the first number in the output ~= the expected number."""

    id = "numeric"

    def __init__(self, *, rel_tol: float = 0.0, abs_tol: float = 1e-9) -> None:
        self.rel_tol = rel_tol
        self.abs_tol = abs_tol

    def score(self, output: str, expected: str | None) -> Score:
        if expected is None:
            return Score(value=0.0, passed=False)
        target = _first_number(expected)
        got = _first_number(output)
        if target is None or got is None:
            return Score(value=0.0, passed=False)
        tolerance = max(self.abs_tol, self.rel_tol * abs(target))
        passed = abs(got - target) <= tolerance
        return Score(value=1.0 if passed else 0.0, passed=passed)
