"""An append-only Merkle log of signed run records.

On-disk layout (a single directory)::

    <ledger>/entries.jsonl   # one line per appended record, in append order

Each entry records the leaf (the record's content hash), the signer's public
key, and an append timestamp. The Merkle tree is built over the leaves in append
order; the root is recomputed on demand from ``entries.jsonl``, so the log is
just an auditable, line-diffable text file -- publish it anywhere.

Only records that pass integrity + signature verification are appended, so the
log never commits to a record that doesn't verify on its own.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from verievals.crypto.merkle import InclusionProof, merkle_proof, merkle_root
from verievals.records.schema import RunRecord

_ENTRIES_FILE = "entries.jsonl"


class LedgerError(RuntimeError):
    """Raised for invalid ledger operations (e.g. appending an unverified record)."""


class MerkleLog:
    """An append-only, content-addressed Merkle log."""

    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self._entries_path = self.root_dir / _ENTRIES_FILE

    # -- reading -------------------------------------------------------------

    def _read_entries(self) -> list[dict[str, object]]:
        if not self._entries_path.exists():
            return []
        entries: list[dict[str, object]] = []
        with self._entries_path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries

    def leaves(self) -> list[str]:
        """Return the leaf content hashes, in append order."""
        return [str(e["leaf"]) for e in self._read_entries()]

    def size(self) -> int:
        return len(self._read_entries())

    def record_ids(self) -> list[str]:
        return [str(e["record_id"]) for e in self._read_entries()]

    def index_of(self, record_id: str) -> int | None:
        for i, e in enumerate(self._read_entries()):
            if e["record_id"] == record_id:
                return i
        return None

    def contains(self, record_id: str) -> bool:
        return self.index_of(record_id) is not None

    def root(self) -> str:
        """Return the current Merkle root (hex)."""
        return merkle_root(self.leaves())

    # -- proofs --------------------------------------------------------------

    def proof_for_index(self, index: int) -> InclusionProof:
        return merkle_proof(self.leaves(), index)

    def proof_for(self, record_id: str) -> InclusionProof:
        index = self.index_of(record_id)
        if index is None:
            raise LedgerError(f"record {record_id} is not in the ledger")
        return self.proof_for_index(index)

    # -- writing -------------------------------------------------------------

    def append(self, record: RunRecord) -> InclusionProof:
        """Verify and append ``record``; return its inclusion proof.

        Raises:
            LedgerError: if the record fails verification or is already present.
        """
        if not record.verify_signature():
            raise LedgerError("refusing to append: record signature does not verify")
        if self.contains(record.record_id):
            raise LedgerError(f"record {record.record_id} is already in the ledger")

        self.root_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "index": self.size(),
            "record_id": record.record_id,
            "leaf": record.content_hash,
            "public_key": record.signature.public_key,
            "appended_at": datetime.now(timezone.utc).isoformat(),
        }
        with self._entries_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, sort_keys=True) + "\n")

        return self.proof_for(record.record_id)
