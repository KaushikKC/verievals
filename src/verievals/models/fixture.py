"""A deterministic fixture model backed by canned responses.

``FixtureModel`` maps each prompt to a pre-recorded answer. This is the
mechanism that makes a *non-deterministic* live model's run reproducible: record
a live run's prompt->output pairs once, ship them as a fixture, and anyone can
re-run and verify the eval offline against exactly those outputs.

Fixtures are keyed by the SHA-256 content hash of the prompt, so they are
robust to whitespace-insensitive edits only if the prompt bytes match exactly
(which is the point -- the prompt is part of what's being verified).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from verievals.crypto.hashing import sha256_hex
from verievals.models.base import ModelAdapter, ModelInfo

_VERSION = "1"


class FixtureModel(ModelAdapter):
    """Returns canned outputs for known prompts."""

    def __init__(
        self,
        responses: Mapping[str, str],
        name: str = "fixture",
        *,
        strict: bool = True,
        default: str = "",
    ) -> None:
        # Store keyed by prompt content hash for stable lookup.
        self._by_hash = {sha256_hex(p.encode("utf-8")): out for p, out in responses.items()}
        self._name = name
        self._strict = strict
        self._default = default

    @classmethod
    def from_file(cls, path: str | Path, **kwargs: object) -> FixtureModel:
        """Load a fixture from a JSON file mapping prompt -> output."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        name = str(data.get("name", "fixture"))
        responses = dict(data["responses"])
        return cls(responses, name=name, **kwargs)  # type: ignore[arg-type]

    def generate(self, prompt: str) -> str:
        key = sha256_hex(prompt.encode("utf-8"))
        if key in self._by_hash:
            return self._by_hash[key]
        if self._strict:
            raise KeyError(f"no fixture response for prompt (hash={key[:12]}...)")
        return self._default

    def info(self) -> ModelInfo:
        return ModelInfo(provider="mock", name=self._name, version=_VERSION, params={})

    @property
    def deterministic(self) -> bool:
        return True
