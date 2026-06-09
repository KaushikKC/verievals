"""OpenAI model adapter.

Wraps the official ``openai`` SDK's Chat Completions API so that the benchmark
runner is lab-neutral -- the whole point of verifiable evals is letting anyone
compare and re-verify results *across* providers. Install with
``pip install verievals[openai]`` and set ``OPENAI_API_KEY``.

Like the Anthropic adapter, hosted OpenAI models are not bit-for-bit
deterministic; the record captures the model id and decoding params.
"""

from __future__ import annotations

from typing import Any

from verievals.models.base import ModelAdapter, ModelInfo

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_MAX_TOKENS = 1024


class OpenAIAdapter(ModelAdapter):
    """Generate text with an OpenAI model via the Chat Completions API."""

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
                import openai
            except ImportError as exc:  # pragma: no cover - exercised only without dep
                raise ImportError(
                    "The 'openai' package is required for OpenAIAdapter. "
                    "Install it with: pip install verievals[openai]"
                ) from exc
            self._client = openai.OpenAI()

    def generate(self, prompt: str) -> str:
        messages: list[dict[str, str]] = []
        if self.system is not None:
            messages.append({"role": "system", "content": self.system})
        messages.append({"role": "user", "content": prompt})
        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=messages,
            **self.extra_params,
        )
        return response.choices[0].message.content or ""

    def info(self) -> ModelInfo:
        params: dict[str, Any] = {"max_tokens": self.max_tokens, **self.extra_params}
        if self.system is not None:
            params["system"] = self.system
        return ModelInfo(
            provider="openai",
            name=self.model,
            version=self.model,
            params=params,
        )
