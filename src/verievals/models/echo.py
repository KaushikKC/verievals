"""A deterministic echo model.

``EchoModel`` extracts the final answer from a prompt that follows the
convention used by the built-in benchmarks: it returns the text after the last
``Answer:`` marker if present, otherwise it echoes the last non-empty line.

It exists to exercise the full pipeline (run -> sign -> ledger -> verify)
offline and bit-for-bit, with no API calls. It is not meant to be *good* at any
benchmark -- it is meant to be *reproducible*.
"""

from __future__ import annotations

from verievals.models.base import ModelAdapter, ModelInfo

_VERSION = "1"


class EchoModel(ModelAdapter):
    """Deterministically reflects the prompt back as the answer."""

    def __init__(self, marker: str = "Answer:") -> None:
        self.marker = marker

    def generate(self, prompt: str) -> str:
        if self.marker in prompt:
            return prompt.rsplit(self.marker, 1)[1].strip()
        lines = [line.strip() for line in prompt.splitlines() if line.strip()]
        return lines[-1] if lines else ""

    def info(self) -> ModelInfo:
        return ModelInfo(
            provider="mock",
            name="echo",
            version=_VERSION,
            params={"marker": self.marker},
        )

    @property
    def deterministic(self) -> bool:
        return True
