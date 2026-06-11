"""Tests for the Ollama adapter using an injected transport (no server needed)."""

from __future__ import annotations

from typing import Any

from verievals.models.ollama_adapter import DEFAULT_MODEL, OllamaAdapter
from verievals.models.registry import load_model


def test_generate_uses_transport_and_strips() -> None:
    captured: dict[str, Any] = {}

    def transport(payload: dict[str, Any]) -> str:
        captured.update(payload)
        return "  72\n"

    adapter = OllamaAdapter(transport=transport)
    assert adapter.generate("2+2?") == "72"
    assert captured["model"] == DEFAULT_MODEL
    assert captured["stream"] is False
    assert captured["options"]["temperature"] == 0.0
    assert captured["options"]["seed"] == 0


def test_system_prompt_included_when_set() -> None:
    captured: dict[str, Any] = {}

    def transport(payload: dict[str, Any]) -> str:
        captured.update(payload)
        return "ok"

    OllamaAdapter(system="be terse", transport=transport).generate("hi")
    assert captured["system"] == "be terse"


def test_info_reports_ollama_provider() -> None:
    info = OllamaAdapter(model="llama3:8b", transport=lambda _p: "").info()
    assert info.provider == "ollama"
    assert info.name == "llama3:8b"
    assert info.params["num_predict"] == 512


def test_not_deterministic() -> None:
    assert not OllamaAdapter(transport=lambda _p: "").deterministic


def test_registry_resolves_ollama_with_colon_in_tag() -> None:
    model = load_model("ollama:llama3:8b")
    assert isinstance(model, OllamaAdapter)
    assert model.model == "llama3:8b"


def test_registry_default_model() -> None:
    model = load_model("ollama")
    assert isinstance(model, OllamaAdapter)
    assert model.model == DEFAULT_MODEL
