"""Signed, reproducible eval records.

A :class:`~verievals.records.schema.RunRecord` is the central artifact of the
whole system. It separates:

* a deterministic **body** -- everything needed to *reproduce* the run
  (benchmark identity, model identity + decoding params, seed, prompts, outputs,
  per-task scores, aggregate metrics). The body's canonical content hash is the
  record's stable identifier and the leaf committed to the Merkle ledger.
* a non-deterministic **envelope** -- metadata that must *not* affect the hash
  (wall-clock timestamp, optional signer label).
* a **signature** -- an Ed25519 signature over the content hash.

This split is what makes a record both signable *and* reproducible: re-running
the body yields the same content hash, while the timestamp/signature live
outside the hashed payload.
"""

from verievals.records.schema import (
    Aggregate,
    BenchmarkSpec,
    Envelope,
    ModelSpec,
    RunBody,
    RunRecord,
    RunnerSpec,
    Signature,
    TaskResult,
)
from verievals.records.store import RecordStore

__all__ = [
    "Aggregate",
    "BenchmarkSpec",
    "Envelope",
    "ModelSpec",
    "RunBody",
    "RunRecord",
    "RunnerSpec",
    "Signature",
    "TaskResult",
    "RecordStore",
]
