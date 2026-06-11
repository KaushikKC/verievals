"""Tests for the GSM8K scorer."""

from __future__ import annotations

from verievals.scoring.gsm8k import GSM8KScorer
from verievals.scoring.registry import get_scorer


def test_matches_terse_answer() -> None:
    assert GSM8KScorer().score("72", "72").passed


def test_takes_last_number_from_reasoning() -> None:
    out = "Natalia sold 48 in April and 24 in May, so 48 + 24 = 72."
    assert GSM8KScorer().score(out, "72").passed


def test_intermediate_numbers_do_not_match() -> None:
    # The first number (48) is wrong; only the final (72) counts.
    out = "She sold 48, then 24, total 70."  # wrong final
    assert not GSM8KScorer().score(out, "72").passed


def test_handles_thousands_separator() -> None:
    assert GSM8KScorer().score("the total is 1,200", "1200").passed


def test_no_number_fails() -> None:
    assert not GSM8KScorer().score("I don't know", "72").passed


def test_none_expected_fails() -> None:
    assert not GSM8KScorer().score("72", None).passed


def test_registered_in_registry() -> None:
    assert isinstance(get_scorer("gsm8k"), GSM8KScorer)
