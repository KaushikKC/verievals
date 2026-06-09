"""Tests for the Anthropic adapter using an injected fake client."""

from __future__ import annotations

from dataclasses import dataclass

from verievals.models.anthropic_adapter import DEFAULT_MODEL, AnthropicAdapter


@dataclass
class _Block:
    type: str
    text: str = ""


class _FakeMessages:
    def __init__(self) -> None:
        self.last_kwargs: dict = {}

    def create(self, **kwargs: object) -> object:
        self.last_kwargs = kwargs
        return type("Resp", (), {"content": [_Block("text", "hello"), _Block("thinking")]})


class _FakeClient:
    def __init__(self) -> None:
        self.messages = _FakeMessages()


def test_generate_extracts_text_blocks_only() -> None:
    client = _FakeClient()
    adapter = AnthropicAdapter(client=client)
    assert adapter.generate("hi") == "hello"


def test_does_not_inject_temperature() -> None:
    client = _FakeClient()
    AnthropicAdapter(client=client).generate("hi")
    assert "temperature" not in client.messages.last_kwargs


def test_forwards_max_tokens_and_messages() -> None:
    client = _FakeClient()
    AnthropicAdapter(client=client, max_tokens=512).generate("hi")
    assert client.messages.last_kwargs["max_tokens"] == 512
    assert client.messages.last_kwargs["messages"] == [{"role": "user", "content": "hi"}]


def test_info_records_model_and_params() -> None:
    adapter = AnthropicAdapter(client=_FakeClient(), max_tokens=256)
    info = adapter.info()
    assert info.provider == "anthropic"
    assert info.name == DEFAULT_MODEL
    assert info.params["max_tokens"] == 256


def test_not_deterministic() -> None:
    assert not AnthropicAdapter(client=_FakeClient()).deterministic
