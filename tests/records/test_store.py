"""Tests for the on-disk record store."""

from __future__ import annotations

from pathlib import Path

from verievals.crypto.signing import SigningKey
from verievals.records.schema import RunBody, RunRecord
from verievals.records.store import RecordStore


def test_save_and_load_roundtrip(
    tmp_path: Path, sample_body: RunBody, signing_key: SigningKey
) -> None:
    store = RecordStore(tmp_path)
    record = RunRecord.create(sample_body, signing_key)
    path = store.save(record)
    assert path.exists()
    assert path.name == f"{record.record_id}.json"
    loaded = store.load(record.record_id)
    assert loaded == record
    assert loaded.verify_signature()


def test_exists(tmp_path: Path, sample_body: RunBody, signing_key: SigningKey) -> None:
    store = RecordStore(tmp_path)
    record = RunRecord.create(sample_body, signing_key)
    assert not store.exists(record.record_id)
    store.save(record)
    assert store.exists(record.record_id)


def test_iter_records_is_sorted(
    tmp_path: Path, sample_body: RunBody, signing_key: SigningKey
) -> None:
    store = RecordStore(tmp_path)
    record = RunRecord.create(sample_body, signing_key)
    store.save(record)
    ids = store.record_ids()
    assert ids == [record.record_id]
    assert [r.record_id for r in store.iter_records()] == ids


def test_empty_store_returns_no_records(tmp_path: Path) -> None:
    store = RecordStore(tmp_path / "does-not-exist")
    assert store.record_ids() == []
    assert list(store.iter_records()) == []


def test_saved_file_is_human_readable_json(
    tmp_path: Path, sample_body: RunBody, signing_key: SigningKey
) -> None:
    store = RecordStore(tmp_path)
    record = RunRecord.create(sample_body, signing_key)
    path = store.save(record)
    text = path.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert '"content_hash"' in text
