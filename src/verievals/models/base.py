"""The model adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModelInfo:
    """Identity and decoding parameters of a model, for the run record.

    Attributes:
        provider: e.g. ``"anthropic"``, ``"openai"``, ``"mock"``.
        name: the model identifier (e.g. ``"claude-opus-4-8"``).
        version: the resolved version/snapshot if known, else the same as ``name``.
        params: decoding parameters that affect output (e.g. ``max_tokens``).
    """

    provider: str
    name: str
    version: str
    params: dict[str, Any] = field(default_factory=dict)


class ModelAdapter(ABC):
    """Turns a prompt into model output text."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Return the model's text output for ``prompt``."""

    @abstractmethod
    def info(self) -> ModelInfo:
        """Return identity + decoding params for inclusion in a run record."""

    @property
    def deterministic(self) -> bool:
        """Whether identical inputs always yield identical outputs.

        Deterministic models can be re-run by a verifier to reproduce a record
        bit-for-bit; non-deterministic ones cannot.
        """
        return False
