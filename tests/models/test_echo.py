"""Tests for the deterministic echo model."""

from __future__ import annotations

from verievals.models.echo import EchoModel


def test_returns_text_after_answer_marker() -> None:
    model = EchoModel()
    assert model.generate("What is 2+2?\nAnswer: 4") == "4"


def test_falls_back_to_last_nonempty_line() -> None:
    model = EchoModel()
    assert model.generate("line one\nline two\n\n") == "line two"


def test_empty_prompt_returns_empty() -> None:
    assert EchoModel().generate("") == ""


def test_is_deterministic() -> None:
    model = EchoModel()
    assert model.deterministic
    assert model.generate("Answer: x") == model.generate("Answer: x")


def test_info_reports_mock_provider() -> None:
    info = EchoModel().info()
    assert info.provider == "mock"
    assert info.name == "echo"
