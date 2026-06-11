"""Ollama model adapter for locally-run open models.

Talks to a local Ollama server (default ``http://localhost:11434``) via its HTTP
API, so you can evaluate any model you've pulled (``gemma3:1b``, ``llama3:8b``,
``deepseek-r1:7b``, ...) with no Python ML dependencies -- just stdlib HTTP.

Reproducibility note: even at ``temperature=0`` with a fixed seed, local model
inference is not guaranteed bit-for-bit across hardware/driver versions, so this
adapter reports ``deterministic = False``. The record still pins the model id and
all sampling options. To make a local run independently re-verifiable offline,
capture its prompt->output pairs into a
:class:`~verievals.models.fixture.FixtureModel` (see ``examples/``).
"""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable
from typing import Any

from verievals.models.base import ModelAdapter, ModelInfo

DEFAULT_MODEL = "gemma3:1b"
DEFAULT_HOST = "http://localhost:11434"


class OllamaAdapter(ModelAdapter):
    """Generate text with a locally-served Ollama model."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        *,
        host: str = DEFAULT_HOST,
        temperature: float = 0.0,
        seed: int = 0,
        num_predict: int = 512,
        system: str | None = None,
        timeout: float = 180.0,
        transport: Callable[[dict[str, Any]], str] | None = None,
    ) -> None:
        self.model = model
        self.host = host.rstrip("/")
        self.temperature = temperature
        self.seed = seed
        self.num_predict = num_predict
        self.system = system
        self.timeout = timeout
        self._transport = transport or self._http_transport

    def _http_transport(self, payload: dict[str, Any]) -> str:
        request = urllib.request.Request(
            f"{self.host}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        return str(data.get("response", ""))

    def generate(self, prompt: str) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "seed": self.seed,
                "num_predict": self.num_predict,
            },
        }
        if self.system is not None:
            payload["system"] = self.system
        return self._transport(payload).strip()

    def info(self) -> ModelInfo:
        params: dict[str, Any] = {
            "temperature": self.temperature,
            "seed": self.seed,
            "num_predict": self.num_predict,
        }
        if self.system is not None:
            params["system"] = self.system
        return ModelInfo(
            provider="ollama",
            name=self.model,
            version=self.model,
            params=params,
        )
