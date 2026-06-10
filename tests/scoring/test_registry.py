"""Tests for the scorer registry."""

from __future__ import annotations

import pytest

from verievals.scoring.exact_match import ExactMatchScorer
from verievals.scoring.numeric import NumericScorer
from verievals.scoring.registry import available_scorers, get_scorer


def test_resolves_known_scorers() -> None:
    assert isinstance(get_scorer("exact_match"), ExactMatchScorer)
    assert isinstance(get_scorer("numeric"), NumericScorer)


def test_unknown_scorer_lists_known() -> None:
    with pytest.raises(ValueError, match="unknown scorer"):
        get_scorer("nope")


def test_available_scorers_is_sorted() -> None:
    scorers = available_scorers()
    assert scorers == sorted(scorers)
    assert "numeric" in scorers
