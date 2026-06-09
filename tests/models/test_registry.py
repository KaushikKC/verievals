"""Tests for the model registry."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from verievals.models.echo import EchoModel
from verievals.models.fixture import FixtureModel
from verievals.models.registry import load_model


def test_load_echo() -> None:
    assert isinstance(load_model("echo"), EchoModel)


def test_load_fixture(tmp_path: Path) -> None:
    path = tmp_path / "f.json"
    path.write_text(json.dumps({"responses": {"q": "a"}}), encoding="utf-8")
    model = load_model(f"fixture:{path}")
    assert isinstance(model, FixtureModel)
    assert model.generate("q") == "a"


def test_fixture_requires_path() -> None:
    with pytest.raises(ValueError, match="requires a path"):
        load_model("fixture")


def test_unknown_provider_raises() -> None:
    with pytest.raises(ValueError, match="unknown model provider"):
        load_model("frobnicate:xyz")
