"""Tests for the deterministic fixture model."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from verievals.models.fixture import FixtureModel


def test_returns_canned_response() -> None:
    model = FixtureModel({"What is 2+2?": "4"})
    assert model.generate("What is 2+2?") == "4"


def test_strict_raises_on_unknown_prompt() -> None:
    model = FixtureModel({"known": "yes"}, strict=True)
    with pytest.raises(KeyError):
        model.generate("unknown")


def test_non_strict_returns_default() -> None:
    model = FixtureModel({"known": "yes"}, strict=False, default="N/A")
    assert model.generate("unknown") == "N/A"


def test_is_deterministic() -> None:
    assert FixtureModel({"a": "b"}).deterministic


def test_from_file(tmp_path: Path) -> None:
    path = tmp_path / "fix.json"
    path.write_text(
        json.dumps({"name": "claude-snapshot", "responses": {"q": "a"}}),
        encoding="utf-8",
    )
    model = FixtureModel.from_file(path)
    assert model.generate("q") == "a"
    assert model.info().name == "claude-snapshot"
