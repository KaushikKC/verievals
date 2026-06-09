"""The ``RunRecord`` schema and its components.

All dataclasses here are immutable and provide ``to_dict`` / ``from_dict`` so
they can be canonicalized and hashed deterministically. ``to_dict`` produces
plain JSON-compatible structures with sorted-by-construction keys; canonical
encoding (see :mod:`verievals.crypto.canonical`) sorts keys again, so field
order here is irrelevant to the hash.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from verievals.crypto.hashing import content_hash
from verievals.crypto.signing import SigningKey, verify

SCHEMA_VERSION = "verievals/runrecord/v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ModelSpec:
    """Identity and decoding parameters of the evaluated model."""

    provider: str
    name: str
    version: str
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "name": self.name,
            "version": self.version,
            "params": dict(self.params),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ModelSpec:
        return cls(
            provider=d["provider"],
            name=d["name"],
            version=d["version"],
            params=dict(d.get("params", {})),
        )


@dataclass(frozen=True)
class BenchmarkSpec:
    """Identity of the benchmark, including a content hash of its definition."""

    id: str
    version: str
    content_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "version": self.version, "content_hash": self.content_hash}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> BenchmarkSpec:
        return cls(id=d["id"], version=d["version"], content_hash=d["content_hash"])


@dataclass(frozen=True)
class RunnerSpec:
    """Determinism-affecting runner configuration."""

    seed: int
    sample_limit: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"seed": self.seed, "sample_limit": self.sample_limit}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RunnerSpec:
        return cls(seed=int(d["seed"]), sample_limit=d.get("sample_limit"))


@dataclass(frozen=True)
class TaskResult:
    """The full, transparent result for a single task."""

    task_id: str
    prompt: str
    output: str
    expected: str | None
    score: float
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "prompt": self.prompt,
            "output": self.output,
            "expected": self.expected,
            "score": self.score,
            "passed": self.passed,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> TaskResult:
        return cls(
            task_id=d["task_id"],
            prompt=d["prompt"],
            output=d["output"],
            expected=d.get("expected"),
            score=float(d["score"]),
            passed=bool(d["passed"]),
        )


@dataclass(frozen=True)
class Aggregate:
    """Aggregate metrics across all tasks."""

    scorer: str
    num_tasks: int
    metrics: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scorer": self.scorer,
            "num_tasks": self.num_tasks,
            "metrics": dict(self.metrics),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Aggregate:
        return cls(
            scorer=d["scorer"],
            num_tasks=int(d["num_tasks"]),
            metrics={k: float(v) for k, v in d.get("metrics", {}).items()},
        )


@dataclass(frozen=True)
class RunBody:
    """The deterministic, reproducible payload of a run."""

    verievals_version: str
    benchmark: BenchmarkSpec
    model: ModelSpec
    runner: RunnerSpec
    results: list[TaskResult]
    aggregate: Aggregate
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "verievals_version": self.verievals_version,
            "benchmark": self.benchmark.to_dict(),
            "model": self.model.to_dict(),
            "runner": self.runner.to_dict(),
            "results": [r.to_dict() for r in self.results],
            "aggregate": self.aggregate.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RunBody:
        return cls(
            schema_version=d.get("schema_version", SCHEMA_VERSION),
            verievals_version=d["verievals_version"],
            benchmark=BenchmarkSpec.from_dict(d["benchmark"]),
            model=ModelSpec.from_dict(d["model"]),
            runner=RunnerSpec.from_dict(d["runner"]),
            results=[TaskResult.from_dict(r) for r in d["results"]],
            aggregate=Aggregate.from_dict(d["aggregate"]),
        )

    def content_hash(self) -> str:
        """Stable content address of the run body."""
        return content_hash(self.to_dict())


@dataclass(frozen=True)
class Signature:
    """An Ed25519 signature over a record's content hash."""

    algorithm: str
    public_key: str
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "public_key": self.public_key,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Signature:
        return cls(
            algorithm=d["algorithm"],
            public_key=d["public_key"],
            signature=d["signature"],
        )


@dataclass(frozen=True)
class Envelope:
    """Non-deterministic metadata that is intentionally excluded from the hash."""

    created_at: str
    signer: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"created_at": self.created_at, "signer": self.signer}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Envelope:
        return cls(created_at=d["created_at"], signer=d.get("signer"))


@dataclass(frozen=True)
class RunRecord:
    """A signed, reproducible eval record."""

    body: RunBody
    content_hash: str
    signature: Signature
    envelope: Envelope

    @property
    def record_id(self) -> str:
        """The record's stable identifier (its body content hash)."""
        return self.content_hash

    @classmethod
    def create(
        cls,
        body: RunBody,
        signing_key: SigningKey,
        signer: str | None = None,
    ) -> RunRecord:
        """Create a signed record from a body, signing its content hash."""
        digest = body.content_hash()
        sig = Signature(
            algorithm="ed25519",
            public_key=signing_key.verify_key.hex,
            signature=signing_key.sign(digest.encode("utf-8")),
        )
        return cls(
            body=body,
            content_hash=digest,
            signature=sig,
            envelope=Envelope(created_at=_utc_now_iso(), signer=signer),
        )

    def recompute_content_hash(self) -> str:
        return self.body.content_hash()

    def verify_integrity(self) -> bool:
        """Return True iff the stored content hash matches the body."""
        return self.recompute_content_hash() == self.content_hash

    def verify_signature(self) -> bool:
        """Return True iff the signature is valid for the content hash."""
        if not self.verify_integrity():
            return False
        if self.signature.algorithm != "ed25519":
            return False
        return verify(
            self.signature.public_key,
            self.content_hash.encode("utf-8"),
            self.signature.signature,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "body": self.body.to_dict(),
            "content_hash": self.content_hash,
            "signature": self.signature.to_dict(),
            "envelope": self.envelope.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RunRecord:
        return cls(
            body=RunBody.from_dict(d["body"]),
            content_hash=d["content_hash"],
            signature=Signature.from_dict(d["signature"]),
            envelope=Envelope.from_dict(d["envelope"]),
        )
