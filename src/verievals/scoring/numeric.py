"""Numeric scorer.

Extracts the first number from the model output and compares it to the expected
value within a tolerance. Handles negatives, decimals, and thousands separators
(``1,000``). This lets a model answer ``"The answer is 42."`` and still match an
expected ``"42"``.

For chain-of-thought math where the answer is the *last* number, use the
``gsm8k`` scorer instead.
"""

from __future__ import annotations

from verievals.scoring._numbers import first_number
from verievals.scoring.base import Score, Scorer


class NumericScorer(Scorer):
    """Pass iff the first number in the output ~= the expected number."""

    id = "numeric"

    def __init__(self, *, rel_tol: float = 0.0, abs_tol: float = 1e-9) -> None:
        self.rel_tol = rel_tol
        self.abs_tol = abs_tol

    def score(self, output: str, expected: str | None) -> Score:
        if expected is None:
            return Score(value=0.0, passed=False)
        target = first_number(expected)
        got = first_number(output)
        if target is None or got is None:
            return Score(value=0.0, passed=False)
        tolerance = max(self.abs_tol, self.rel_tol * abs(target))
        passed = abs(got - target) <= tolerance
        return Score(value=1.0 if passed else 0.0, passed=passed)
