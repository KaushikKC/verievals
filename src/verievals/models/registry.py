"""Resolve model spec strings to adapters.

Spec grammar::

    echo                          -> deterministic echo model
    fixture:<path>                -> deterministic fixture model from a JSON file
    ollama[:<model>]              -> locally-served model via Ollama
    anthropic[:<model>]           -> Claude via the Anthropic API
    openai[:<model>]              -> OpenAI via the Chat Completions API

The live adapters are imported lazily so that ``echo`` / ``fixture`` work with no
optional dependencies installed.
"""

from __future__ import annotations

from verievals.models.base import ModelAdapter
from verievals.models.echo import EchoModel
from verievals.models.fixture import FixtureModel


def load_model(spec: str) -> ModelAdapter:
    """Resolve a model spec string to a :class:`ModelAdapter`."""
    provider, _, rest = spec.partition(":")
    provider = provider.strip()

    if provider == "echo":
        return EchoModel()

    if provider == "fixture":
        if not rest:
            raise ValueError("fixture model requires a path: 'fixture:<path>'")
        return FixtureModel.from_file(rest)

    if provider == "ollama":
        from verievals.models.ollama_adapter import DEFAULT_MODEL, OllamaAdapter

        return OllamaAdapter(model=rest or DEFAULT_MODEL)

    if provider == "anthropic":
        from verievals.models.anthropic_adapter import DEFAULT_MODEL, AnthropicAdapter

        return AnthropicAdapter(model=rest or DEFAULT_MODEL)

    if provider == "openai":
        from verievals.models.openai_adapter import DEFAULT_MODEL, OpenAIAdapter

        return OpenAIAdapter(model=rest or DEFAULT_MODEL)

    raise ValueError(f"unknown model provider: {provider!r} (in spec {spec!r})")
