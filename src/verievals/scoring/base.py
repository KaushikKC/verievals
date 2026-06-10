"""The scorer interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Score:
    """The result of scoring one output.

    Attributes:
        value: a score in ``[0.0, 1.0]``.
        passed: whether the task is considered passed (typically ``value == 1.0``).
    """

    value: float
    passed: bool


class Scorer(ABC):
    """Deterministically scores a model output against a reference answer."""

    #: Stable identifier recorded in the run record.
    id: str

    @abstractmethod
    def score(self, output: str, expected: str | None) -> Score:
        """Score ``output`` against ``expected`` and return a :class:`Score`."""
