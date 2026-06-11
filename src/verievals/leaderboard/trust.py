"""Trust-scored leaderboard.

The plain leaderboard shows accuracy. A *trust-scored* leaderboard answers the
question the project exists for: **how much should you believe this number?**

Each entry is assigned a trust tier based on the strongest verification that
holds for it:

| Tier            | Score | Meaning                                                      |
|-----------------|-------|--------------------------------------------------------------|
| ``reproduced``  | 1.00  | Re-running the eval reproduced the exact signed result       |
| ``verified``    | 0.80  | Valid signature **and** committed under the ledger root      |
| ``signed``      | 0.50  | Valid signature, but not committed to the ledger             |
| ``self_reported`` | 0.20 | No valid signature -- a bare claim                          |

This makes the gap between "cryptographically backed" and "self-reported"
numbers explicit and rankable, which is the whole pitch.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from verievals.benchmarks.base import Benchmark
from verievals.crypto.merkle import verify_inclusion_proof
from verievals.ledger.merkle_log import MerkleLog
from verievals.ledger.verifier import reproduce_record
from verievals.models.base import ModelAdapter
from verievals.records.schema import RunRecord
from verievals.records.store import RecordStore


class TrustTier(str, Enum):
    """How strongly an entry's number is backed, strongest first."""

    REPRODUCED = "reproduced"
    VERIFIED = "verified"
    SIGNED = "signed"
    SELF_REPORTED = "self_reported"


TRUST_SCORES: dict[TrustTier, float] = {
    TrustTier.REPRODUCED: 1.00,
    TrustTier.VERIFIED: 0.80,
    TrustTier.SIGNED: 0.50,
    TrustTier.SELF_REPORTED: 0.20,
}

_TIER_RANK = {tier: i for i, tier in enumerate(TrustTier)}  # 0 = strongest


@dataclass(frozen=True)
class TrustEntry:
    """A leaderboard row with a trust tier and score."""

    record_id: str
    benchmark_id: str
    benchmark_version: str
    model_provider: str
    model_name: str
    accuracy: float
    num_tasks: int
    signer: str | None
    tier: TrustTier
    trust_score: float


@dataclass(frozen=True)
class TrustLeaderboard:
    """A trust-ranked leaderboard committed under ``root``."""

    root: str
    entries: list[TrustEntry]
    generated_at: str

    def render_markdown(self) -> str:
        emoji = {
            TrustTier.REPRODUCED: "🟢 reproduced",
            TrustTier.VERIFIED: "🔵 verified",
            TrustTier.SIGNED: "🟡 signed",
            TrustTier.SELF_REPORTED: "🔴 self-reported",
        }
        lines = [
            "# Verifiable Evals — Trust Score Leaderboard",
            "",
            f"- Merkle root: `{self.root}`",
            f"- Generated: {self.generated_at}",
            f"- Entries: {len(self.entries)}",
            "",
            "Trust tiers: 🟢 reproduced (1.00) · 🔵 verified (0.80) · "
            "🟡 signed (0.50) · 🔴 self-reported (0.20)",
            "",
            "| # | Trust | Score | Benchmark | Model | Accuracy | Tasks | Signer | Record |",
            "|---|-------|-------|-----------|-------|----------|-------|--------|--------|",
        ]
        for i, e in enumerate(self.entries, start=1):
            lines.append(
                f"| {i} | {emoji[e.tier]} | {e.trust_score:.2f} "
                f"| {e.benchmark_id}@{e.benchmark_version} "
                f"| {e.model_provider}:{e.model_name} "
                f"| {e.accuracy:.3f} | {e.num_tasks} "
                f"| {e.signer or '—'} | `{e.record_id[:12]}…` |"
            )
        return "\n".join(lines) + "\n"


def build_trust_leaderboard(
    store: RecordStore,
    ledger: MerkleLog,
    *,
    reproducers: dict[str, tuple[Benchmark, ModelAdapter]] | None = None,
    benchmark_id: str | None = None,
) -> TrustLeaderboard:
    """Build a trust-ranked leaderboard from every record in ``store``.

    Args:
        reproducers: optional map of ``benchmark_id -> (benchmark, model)``. When
            a record's benchmark id is present and the model is deterministic, the
            eval is re-run; a matching body hash earns the ``reproduced`` tier.
        benchmark_id: if set, only include records for this benchmark.

    Every record is included (even unsigned/self-reported ones) so the board can
    show the trust gap. Rows are sorted by trust tier, then accuracy, then id.
    """
    reproducers = reproducers or {}
    root = ledger.root()
    entries: list[TrustEntry] = []

    for record in store.iter_records():
        if benchmark_id is not None and record.body.benchmark.id != benchmark_id:
            continue
        tier = _classify(record, ledger, root, reproducers)
        entries.append(
            TrustEntry(
                record_id=record.record_id,
                benchmark_id=record.body.benchmark.id,
                benchmark_version=record.body.benchmark.version,
                model_provider=record.body.model.provider,
                model_name=record.body.model.name,
                accuracy=float(record.body.aggregate.metrics.get("accuracy", 0.0)),
                num_tasks=record.body.aggregate.num_tasks,
                signer=record.envelope.signer,
                tier=tier,
                trust_score=TRUST_SCORES[tier],
            )
        )

    entries.sort(key=lambda e: (_TIER_RANK[e.tier], -e.accuracy, e.record_id))
    return TrustLeaderboard(
        root=root,
        entries=entries,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def _classify(
    record: RunRecord,
    ledger: MerkleLog,
    root: str,
    reproducers: dict[str, tuple[Benchmark, ModelAdapter]],
) -> TrustTier:
    if not record.verify_signature():
        return TrustTier.SELF_REPORTED

    included = False
    if ledger.contains(record.record_id):
        proof = ledger.proof_for(record.record_id)
        included = verify_inclusion_proof(record.content_hash, proof, root)

    if not included:
        return TrustTier.SIGNED

    bench_model = reproducers.get(record.body.benchmark.id)
    if bench_model is not None:
        benchmark, model = bench_model
        if model.deterministic and reproduce_record(record, benchmark, model):
            return TrustTier.REPRODUCED

    return TrustTier.VERIFIED
