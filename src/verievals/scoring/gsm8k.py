"""GSM8K-style scorer.

Grade-school math answers are integers, and models typically reason step by step
before stating the result. The conventional extraction is therefore the **last**
number in the output, compared to the expected answer's number. This tolerates
chain-of-thought ("...so 48 + 24 = 72") as well as terse ("72") outputs.
"""

from __future__ import annotations

from verievals.scoring._numbers import last_number
from verievals.scoring.base import Score, Scorer


class GSM8KScorer(Scorer):
    """Pass iff the last number in the output equals the expected answer."""

    id = "gsm8k"

    def __init__(self, *, abs_tol: float = 1e-9) -> None:
        self.abs_tol = abs_tol

    def score(self, output: str, expected: str | None) -> Score:
        if expected is None:
            return Score(value=0.0, passed=False)
        target = last_number(expected)
        got = last_number(output)
        if target is None or got is None:
            return Score(value=0.0, passed=False)
        passed = abs(got - target) <= self.abs_tol
        return Score(value=1.0 if passed else 0.0, passed=passed)
