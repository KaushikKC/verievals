"""Tests for the regex-match scorer."""

from __future__ import annotations

import re

from verievals.scoring.regex_match import RegexMatchScorer


def test_matches_pattern_in_output() -> None:
    assert RegexMatchScorer().score("the answer is PARIS", r"\bPARIS\b").passed


def test_no_match_fails() -> None:
    assert not RegexMatchScorer().score("london", r"\bparis\b").passed


def test_flags_are_applied() -> None:
    assert RegexMatchScorer(flags=re.IGNORECASE).score("PARIS", "paris").passed


def test_invalid_regex_fails_gracefully() -> None:
    assert not RegexMatchScorer().score("anything", "(unclosed").passed


def test_none_expected_fails() -> None:
    assert not RegexMatchScorer().score("x", None).passed
