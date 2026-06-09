"""Benchmark and task data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from verievals.crypto.hashing import content_hash


@dataclass(frozen=True)
class Task:
    """A single benchmark item.

    Attributes:
        id: stable identifier, unique within the benchmark.
        prompt: the exact prompt presented to the model.
        expected: the reference answer (may be ``None`` for open-ended tasks).
        metadata: optional task-level metadata (category, difficulty, ...).
    """

    id: str
    prompt: str
    expected: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "prompt": self.prompt,
            "expected": self.expected,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Task:
        return cls(
            id=str(d["id"]),
            prompt=d["prompt"],
            expected=d.get("expected"),
            metadata=dict(d.get("metadata", {})),
        )


@dataclass(frozen=True)
class Benchmark:
    """An identified, versioned set of tasks with a default scorer."""

    id: str
    version: str
    scorer: str
    tasks: list[Task]
    description: str = ""

    def __len__(self) -> int:
        return len(self.tasks)

    def content_hash(self) -> str:
        """Content hash over the *testable* definition.

        Includes id, version, scorer, and every task (id/prompt/expected/metadata).
        ``description`` is documentation and is intentionally excluded, so editing
        prose does not change the benchmark's verifiable identity -- bump
        ``version`` for any change to the tasks themselves.
        """
        payload = {
            "id": self.id,
            "version": self.version,
            "scorer": self.scorer,
            "tasks": [t.to_dict() for t in self.tasks],
        }
        return content_hash(payload)
