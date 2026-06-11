"""Tests for the OpenAI adapter using an injected fake client."""

from __future__ import annotations

from verievals.models.openai_adapter import DEFAULT_MODEL, OpenAIAdapter


class _FakeCompletions:
    def __init__(self) -> None:
        self.last_kwargs: dict = {}

    def create(self, **kwargs: object) -> object:
        self.last_kwargs = kwargs
        message = type("M", (), {"content": "hello"})
        choice = type("C", (), {"message": message})
        return type("R", (), {"choices": [choice]})


class _FakeChat:
    def __init__(self) -> None:
        self.completions = _FakeCompletions()


class _FakeClient:
    def __init__(self) -> None:
        self.chat = _FakeChat()


def test_generate_returns_message_content() -> None:
    adapter = OpenAIAdapter(client=_FakeClient())
    assert adapter.generate("hi") == "hello"


def test_system_prompt_is_prepended() -> None:
    client = _FakeClient()
    OpenAIAdapter(client=client, system="be terse").generate("hi")
    messages = client.chat.completions.last_kwargs["messages"]
    assert messages[0] == {"role": "system", "content": "be terse"}
    assert messages[1] == {"role": "user", "content": "hi"}


def test_info_records_provider_and_model() -> None:
    info = OpenAIAdapter(client=_FakeClient(), max_tokens=128).info()
    assert info.provider == "openai"
    assert info.name == DEFAULT_MODEL
    assert info.params["max_tokens"] == 128


def test_not_deterministic() -> None:
    assert not OpenAIAdapter(client=_FakeClient()).deterministic
