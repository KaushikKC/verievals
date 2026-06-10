"""Scorers turn a model output + reference answer into a numeric score.

Scoring must be deterministic and fully specified by the scorer id stored in the
run record -- two parties scoring the same output against the same expected
value must get the same number. Use :func:`~verievals.scoring.registry.get_scorer`
to resolve a scorer id (e.g. ``"exact_match"``, ``"numeric"``).
"""

from verievals.scoring.base import Score, Scorer
from verievals.scoring.exact_match import ExactMatchScorer
from verievals.scoring.numeric import NumericScorer
from verievals.scoring.regex_match import RegexMatchScorer
from verievals.scoring.registry import get_scorer

__all__ = [
    "Score",
    "Scorer",
    "ExactMatchScorer",
    "NumericScorer",
    "RegexMatchScorer",
    "get_scorer",
]
