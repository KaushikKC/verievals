"""Anthropic Claude model adapter.

Wraps the official ``anthropic`` SDK's Messages API. Install the optional
dependency with ``pip install verievals[anthropic]`` and set ``ANTHROPIC_API_KEY``.

Reproducibility note: hosted models are not bit-for-bit deterministic, so this
adapter reports ``deterministic = False``. The run record still captures the
exact model id and decoding parameters, so a verifier can see precisely what was
requested and flag drift. To make a Claude run independently re-verifiable
offline, capture its prompt->output pairs into a
:class:`~verievals.models.fixture.FixtureModel`.

Decoding parameters: the default model ``claude-opus-4-8`` uses adaptive
thinking and does **not** accept ``temperature`` / ``top_p`` / ``top_k`` (they
return HTTP 400). This adapter therefore forwards only ``max_tokens`` plus any
explicit ``extra_params`` you pass -- it does not inject a temperature.
"""

from __future__ import annotations

from typing import Any

from verievals.models.base import ModelAdapter, ModelInfo

DEFAULT_MODEL = "claude-opus-4-8"
DEFAULT_MAX_TOKENS = 1024


class AnthropicAdapter(ModelAdapter):
    """Generate text with a Claude model via the Anthropic Messages API."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        *,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        system: str | None = None,
        extra_params: dict[str, Any] | None = None,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self.system = system
        self.extra_params = dict(extra_params or {})
        if client is not None:
            self._client = client
        else:
            try:
                import anthropic
            except ImportError as exc:  # pragma: no cover - exercised only without dep
                raise ImportError(
                    "The 'anthropic' package is required for AnthropicAdapter. "
                    "Install it with: pip install verievals[anthropic]"
                ) from exc
            self._client = anthropic.Anthropic()

    def generate(self, prompt: str) -> str:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            **self.extra_params,
        }
        if self.system is not None:
            kwargs["system"] = self.system
        response = self._client.messages.create(**kwargs)
        return _extract_text(response)

    def info(self) -> ModelInfo:
        params: dict[str, Any] = {"max_tokens": self.max_tokens, **self.extra_params}
        if self.system is not None:
            params["system"] = self.system
        return ModelInfo(
            provider="anthropic",
            name=self.model,
            version=self.model,
            params=params,
        )


def _extract_text(response: Any) -> str:
    """Concatenate text blocks from a Messages API response."""
    parts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    return "".join(parts)
