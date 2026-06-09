"""Model adapters.

A :class:`~verievals.models.base.ModelAdapter` is anything that turns a prompt
into text. Two kinds ship here:

* **Deterministic** adapters (:class:`~verievals.models.echo.EchoModel`,
  :class:`~verievals.models.fixture.FixtureModel`) always produce the same
  output for the same input. They make eval runs bit-for-bit reproducible and
  are what the verifier uses to re-run records offline.
* **Live API** adapters (:class:`~verievals.models.anthropic_adapter.AnthropicAdapter`,
  :class:`~verievals.models.openai_adapter.OpenAIAdapter`) call a hosted model.
  These are not perfectly reproducible -- the record captures the exact model id
  and decoding params so a verifier can see what was asked, and flag drift.

Use :func:`~verievals.models.registry.load_model` to resolve a model spec string
(e.g. ``"echo"``, ``"anthropic:claude-opus-4-8"``) to an adapter.
"""

from verievals.models.base import ModelAdapter, ModelInfo
from verievals.models.echo import EchoModel
from verievals.models.fixture import FixtureModel
from verievals.models.registry import load_model

__all__ = [
    "ModelAdapter",
    "ModelInfo",
    "EchoModel",
    "FixtureModel",
    "load_model",
]
