"""On-disk storage for run records.

Records are stored as human-readable JSON files named by their record id
(content hash), so the filename is itself a verifiable claim about the contents.
The store is deliberately simple and filesystem-backed: records are portable,
diffable, and easy to publish.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

from verievals.records.schema import RunRecord


class RecordStore:
    """A directory of run records, addressed by record id."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def _path_for(self, record_id: str) -> Path:
        return self.root / f"{record_id}.json"

    def save(self, record: RunRecord) -> Path:
        """Persist ``record`` and return the path it was written to."""
        self.root.mkdir(parents=True, exist_ok=True)
        path = self._path_for(record.record_id)
        text = json.dumps(record.to_dict(), indent=2, ensure_ascii=False, sort_keys=True)
        path.write_text(text + "\n", encoding="utf-8")
        return path

    def load(self, record_id: str) -> RunRecord:
        """Load a record by id."""
        return self.load_path(self._path_for(record_id))

    @staticmethod
    def load_path(path: str | Path) -> RunRecord:
        """Load a record from an explicit path."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return RunRecord.from_dict(data)

    def exists(self, record_id: str) -> bool:
        return self._path_for(record_id).exists()

    def iter_records(self) -> Iterator[RunRecord]:
        """Yield every record in the store, sorted by record id."""
        if not self.root.exists():
            return
        for path in sorted(self.root.glob("*.json")):
            yield self.load_path(path)

    def record_ids(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(p.stem for p in self.root.glob("*.json"))
