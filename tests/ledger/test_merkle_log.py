"""Tests for the append-only Merkle log."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from verievals.benchmarks.base import Benchmark
from verievals.crypto.merkle import verify_inclusion_proof
from verievals.crypto.signing import SigningKey
from verievals.ledger.merkle_log import LedgerError, MerkleLog
from verievals.models.fixture import FixtureModel
from verievals.records.schema import RunRecord
from verievals.runner.engine import run_eval


def test_append_then_verify_inclusion(tmp_path: Path, record: RunRecord) -> None:
    log = MerkleLog(tmp_path / "ledger")
    proof = log.append(record)
    assert log.size() == 1
    assert log.contains(record.record_id)
    assert verify_inclusion_proof(record.content_hash, proof, log.root())


def test_multiple_records_all_included(
    tmp_path: Path, benchmark: Benchmark, key: SigningKey
) -> None:
    log = MerkleLog(tmp_path / "ledger")
    records = []
    # Distinct runs via distinct fixture model names -> distinct content hashes.
    for i in range(5):
        model = FixtureModel({"2+2?": "4", "3+3?": "6"}, name=f"snap-{i}")
        rec = run_eval(benchmark, model, signing_key=key)
        records.append(rec)
        log.append(rec)
    root = log.root()
    for rec in records:
        assert verify_inclusion_proof(rec.content_hash, log.proof_for(rec.record_id), root)


def test_append_is_persisted_across_instances(tmp_path: Path, record: RunRecord) -> None:
    MerkleLog(tmp_path / "ledger").append(record)
    reopened = MerkleLog(tmp_path / "ledger")
    assert reopened.contains(record.record_id)
    assert reopened.size() == 1


def test_duplicate_append_raises(tmp_path: Path, record: RunRecord) -> None:
    log = MerkleLog(tmp_path / "ledger")
    log.append(record)
    with pytest.raises(LedgerError, match="already in the ledger"):
        log.append(record)


def test_refuses_record_with_bad_signature(tmp_path: Path, record: RunRecord) -> None:
    bad_sig = dataclasses.replace(record.signature, signature="00" * 64)
    bad = dataclasses.replace(record, signature=bad_sig)
    log = MerkleLog(tmp_path / "ledger")
    with pytest.raises(LedgerError, match="signature does not verify"):
        log.append(bad)


def test_proof_for_missing_record_raises(tmp_path: Path) -> None:
    log = MerkleLog(tmp_path / "ledger")
    with pytest.raises(LedgerError, match="not in the ledger"):
        log.proof_for("deadbeef")


def test_empty_ledger(tmp_path: Path) -> None:
    log = MerkleLog(tmp_path / "ledger")
    assert log.size() == 0
    assert log.leaves() == []
