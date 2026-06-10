"""Regex-match scorer.

The ``expected`` value is treated as a regular expression; the task passes if the
pattern is found anywhere in the output. Useful for answers that allow surface
variation but must contain a specific token or shape.
"""

from __future__ import annotations

import re

from verievals.scoring.base import Score, Scorer


class RegexMatchScorer(Scorer):
    """Pass iff ``expected`` (a regex) matches somewhere in the output."""

    id = "regex_match"

    def __init__(self, *, flags: int = 0) -> None:
        self.flags = flags

    def score(self, output: str, expected: str | None) -> Score:
        if expected is None:
            return Score(value=0.0, passed=False)
        try:
            matched = re.search(expected, output, self.flags) is not None
        except re.error:
            matched = False
        return Score(value=1.0 if matched else 0.0, passed=matched)
