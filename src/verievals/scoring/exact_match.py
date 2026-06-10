"""Exact-match scorer with light normalization."""

from __future__ import annotations

from verievals.scoring.base import Score, Scorer


class ExactMatchScorer(Scorer):
    """Pass iff the normalized output equals the normalized expected answer.

    Normalization strips leading/trailing whitespace and, by default, lowercases
    both sides. This is intentionally simple and fully specified so it is
    reproducible across machines.
    """

    id = "exact_match"

    def __init__(self, *, case_sensitive: bool = False) -> None:
        self.case_sensitive = case_sensitive

    def _normalize(self, text: str) -> str:
        text = text.strip()
        return text if self.case_sensitive else text.casefold()

    def score(self, output: str, expected: str | None) -> Score:
        if expected is None:
            return Score(value=0.0, passed=False)
        passed = self._normalize(output) == self._normalize(expected)
        return Score(value=1.0 if passed else 0.0, passed=passed)
