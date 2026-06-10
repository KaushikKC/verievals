"""Tests for the numeric scorer."""

from __future__ import annotations

from verievals.scoring.numeric import NumericScorer


def test_matches_plain_number() -> None:
    assert NumericScorer().score("42", "42").passed


def test_extracts_number_from_sentence() -> None:
    assert NumericScorer().score("The answer is 42.", "42").passed


def test_handles_negative() -> None:
    assert NumericScorer().score("-7", "-7").passed


def test_handles_thousands_separator() -> None:
    assert NumericScorer().score("1,000", "1000").passed


def test_decimal_within_relative_tolerance() -> None:
    assert NumericScorer(rel_tol=0.01).score("3.14", "3.1415").passed


def test_wrong_number_fails() -> None:
    assert not NumericScorer().score("43", "42").passed


def test_no_number_in_output_fails() -> None:
    assert not NumericScorer().score("forty-two", "42").passed


def test_none_expected_fails() -> None:
    assert not NumericScorer().score("42", None).passed
