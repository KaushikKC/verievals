"""The record verification protocol.

Verification answers, in increasing order of strength:

1. **Integrity** -- does the record's stored content hash match its body?
2. **Signature** -- is the Ed25519 signature valid for that content hash?
3. **Inclusion** -- is the record committed under the ledger's published root?
4. **Reproduction** -- re-running the eval yields the same body content hash
   (only possible with a deterministic model).

Each check is independent; callers run as many as they have inputs for.
"""

from __future__ import annotations

from dataclasses import dataclass

from verievals.benchmarks.base import Benchmark
from verievals.crypto.merkle import verify_inclusion_proof
from verievals.crypto.signing import generate_signing_key
from verievals.ledger.merkle_log import MerkleLog
from verievals.models.base import ModelAdapter
from verievals.records.schema import RunRecord
from verievals.runner.config import RunConfig
from verievals.runner.engine import run_eval


@dataclass(frozen=True)
class VerificationResult:
    """Outcome of verifying a record. ``None`` means a check was not performed."""

    record_id: str
    integrity_ok: bool
    signature_ok: bool
    inclusion_ok: bool | None = None
    reproduced_ok: bool | None = None
    notes: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        """True iff every *performed* check passed."""
        checks = [self.integrity_ok, self.signature_ok, self.inclusion_ok, self.reproduced_ok]
        return all(c for c in checks if c is not None)


def reproduce_record(
    record: RunRecord,
    benchmark: Benchmark,
    model: ModelAdapter,
) -> bool:
    """Re-run the eval described by ``record`` and check the body hash matches.

    The run config (seed, sample limit, scorer) is taken from the record itself,
    so reproduction uses exactly the recorded settings. Signing is irrelevant to
    the body hash, so an ephemeral key is used.
    """
    if benchmark.content_hash() != record.body.benchmark.content_hash:
        return False
    config = RunConfig(
        seed=record.body.runner.seed,
        sample_limit=record.body.runner.sample_limit,
        scorer=record.body.aggregate.scorer,
    )
    rerun = run_eval(benchmark, model, config=config, signing_key=generate_signing_key())
    return rerun.content_hash == record.content_hash


def verify_record(
    record: RunRecord,
    *,
    ledger: MerkleLog | None = None,
    root: str | None = None,
    benchmark: Benchmark | None = None,
    model: ModelAdapter | None = None,
) -> VerificationResult:
    """Run the verification protocol over ``record``.

    Args:
        ledger: if given, check Merkle inclusion against its current root
            (or against ``root`` if that is also supplied).
        root: an explicit published root to check inclusion against (requires
            ``ledger`` to source the inclusion proof).
        benchmark, model: if both given and the model is deterministic, re-run
            the eval and check reproduction.
    """
    notes: list[str] = []
    integrity_ok = record.verify_integrity()
    signature_ok = record.verify_signature()

    inclusion_ok: bool | None = None
    if ledger is not None:
        target_root = root if root is not None else ledger.root()
        if not ledger.contains(record.record_id):
            inclusion_ok = False
            notes.append("record is not present in the ledger")
        else:
            proof = ledger.proof_for(record.record_id)
            inclusion_ok = verify_inclusion_proof(record.content_hash, proof, target_root)

    reproduced_ok: bool | None = None
    if benchmark is not None and model is not None:
        if not model.deterministic:
            notes.append("model is non-deterministic; skipping reproduction")
        else:
            reproduced_ok = reproduce_record(record, benchmark, model)

    return VerificationResult(
        record_id=record.record_id,
        integrity_ok=integrity_ok,
        signature_ok=signature_ok,
        inclusion_ok=inclusion_ok,
        reproduced_ok=reproduced_ok,
        notes=tuple(notes),
    )
