"""Construct and render verifiable leaderboards."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from verievals.crypto.merkle import verify_inclusion_proof
from verievals.ledger.merkle_log import MerkleLog
from verievals.records.schema import RunRecord
from verievals.records.store import RecordStore


@dataclass(frozen=True)
class LeaderboardEntry:
    """One verified leaderboard row."""

    record_id: str
    benchmark_id: str
    benchmark_version: str
    model_provider: str
    model_name: str
    accuracy: float
    num_tasks: int
    signer: str | None
    public_key: str
    inclusion_verified: bool

    @classmethod
    def from_record(cls, record: RunRecord, *, inclusion_verified: bool) -> LeaderboardEntry:
        body = record.body
        return cls(
            record_id=record.record_id,
            benchmark_id=body.benchmark.id,
            benchmark_version=body.benchmark.version,
            model_provider=body.model.provider,
            model_name=body.model.name,
            accuracy=float(body.aggregate.metrics.get("accuracy", 0.0)),
            num_tasks=body.aggregate.num_tasks,
            signer=record.envelope.signer,
            public_key=record.signature.public_key,
            inclusion_verified=inclusion_verified,
        )


@dataclass(frozen=True)
class Leaderboard:
    """A ranked, verifiable set of entries committed under ``root``."""

    root: str
    entries: list[LeaderboardEntry]
    generated_at: str

    def render_markdown(self) -> str:
        lines = [
            "# Verifiable Evals Leaderboard",
            "",
            f"- Merkle root: `{self.root}`",
            f"- Generated: {self.generated_at}",
            f"- Entries: {len(self.entries)}",
            "",
            "| # | Benchmark | Model | Accuracy | Tasks | Signer | Included | Record |",
            "|---|-----------|-------|----------|-------|--------|----------|--------|",
        ]
        for i, e in enumerate(self.entries, start=1):
            included = "✅" if e.inclusion_verified else "❌"
            lines.append(
                f"| {i} | {e.benchmark_id}@{e.benchmark_version} "
                f"| {e.model_provider}:{e.model_name} "
                f"| {e.accuracy:.3f} | {e.num_tasks} "
                f"| {e.signer or '—'} | {included} | `{e.record_id[:12]}…` |"
            )
        return "\n".join(lines) + "\n"


def build_leaderboard(
    store: RecordStore,
    ledger: MerkleLog,
    *,
    benchmark_id: str | None = None,
) -> Leaderboard:
    """Build a leaderboard from every verifying record in ``store``.

    A record is included only if its signature verifies and it is committed under
    the ledger root (inclusion proof checks out). Rows are sorted by accuracy
    (descending), then by record id for a stable tie-break.
    """
    root = ledger.root()
    entries: list[LeaderboardEntry] = []

    for record in store.iter_records():
        if benchmark_id is not None and record.body.benchmark.id != benchmark_id:
            continue
        if not record.verify_signature():
            continue
        included = False
        if ledger.contains(record.record_id):
            proof = ledger.proof_for(record.record_id)
            included = verify_inclusion_proof(record.content_hash, proof, root)
        if not included:
            continue
        entries.append(LeaderboardEntry.from_record(record, inclusion_verified=included))

    entries.sort(key=lambda e: (-e.accuracy, e.record_id))
    return Leaderboard(
        root=root,
        entries=entries,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
