"""Resolve scorer ids to scorer instances."""

from __future__ import annotations

from verievals.scoring.base import Scorer
from verievals.scoring.exact_match import ExactMatchScorer
from verievals.scoring.numeric import NumericScorer
from verievals.scoring.regex_match import RegexMatchScorer

_SCORERS: dict[str, type[Scorer]] = {
    ExactMatchScorer.id: ExactMatchScorer,
    RegexMatchScorer.id: RegexMatchScorer,
    NumericScorer.id: NumericScorer,
}


def get_scorer(scorer_id: str) -> Scorer:
    """Return a default-configured scorer for ``scorer_id``."""
    try:
        return _SCORERS[scorer_id]()
    except KeyError:
        known = ", ".join(sorted(_SCORERS))
        raise ValueError(f"unknown scorer: {scorer_id!r} (known: {known})") from None


def available_scorers() -> list[str]:
    """Return the sorted list of registered scorer ids."""
    return sorted(_SCORERS)
