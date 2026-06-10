"""Tests for the exact-match scorer."""

from __future__ import annotations

from verievals.scoring.exact_match import ExactMatchScorer


def test_passes_on_identical() -> None:
    assert ExactMatchScorer().score("yes", "yes").passed


def test_ignores_surrounding_whitespace() -> None:
    assert ExactMatchScorer().score("  yes\n", "yes").passed


def test_case_insensitive_by_default() -> None:
    assert ExactMatchScorer().score("YES", "yes").passed


def test_case_sensitive_mode() -> None:
    assert not ExactMatchScorer(case_sensitive=True).score("YES", "yes").passed


def test_mismatch_fails() -> None:
    s = ExactMatchScorer().score("no", "yes")
    assert not s.passed
    assert s.value == 0.0


def test_none_expected_fails() -> None:
    assert not ExactMatchScorer().score("anything", None).passed
