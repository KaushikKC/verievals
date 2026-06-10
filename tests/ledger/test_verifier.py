"""Tests for the verification protocol."""

from __future__ import annotations

import dataclasses
from pathlib import Path

from verievals.benchmarks.base import Benchmark, Task
from verievals.ledger.merkle_log import MerkleLog
from verievals.ledger.verifier import reproduce_record, verify_record
from verievals.models.anthropic_adapter import AnthropicAdapter
from verievals.models.fixture import FixtureModel
from verievals.records.schema import RunRecord


def test_verify_integrity_and_signature(record: RunRecord) -> None:
    result = verify_record(record)
    assert result.integrity_ok
    assert result.signature_ok
    assert result.inclusion_ok is None  # no ledger supplied
    assert result.ok


def test_verify_detects_tampering(record: RunRecord) -> None:
    tampered_agg = dataclasses.replace(record.body.aggregate, metrics={"accuracy": 1.0})
    tampered_body = dataclasses.replace(record.body, aggregate=tampered_agg)
    tampered = dataclasses.replace(record, body=tampered_body)
    result = verify_record(tampered)
    assert not result.integrity_ok
    assert not result.ok


def test_verify_inclusion_against_ledger(tmp_path: Path, record: RunRecord) -> None:
    log = MerkleLog(tmp_path / "ledger")
    log.append(record)
    result = verify_record(record, ledger=log)
    assert result.inclusion_ok
    assert result.ok


def test_verify_inclusion_fails_for_absent_record(tmp_path: Path, record: RunRecord) -> None:
    log = MerkleLog(tmp_path / "ledger")  # empty
    result = verify_record(record, ledger=log)
    assert result.inclusion_ok is False
    assert not result.ok


def test_reproduction_succeeds_for_deterministic_model(
    record: RunRecord, benchmark: Benchmark, model: FixtureModel
) -> None:
    assert reproduce_record(record, benchmark, model)
    result = verify_record(record, benchmark=benchmark, model=model)
    assert result.reproduced_ok
    assert result.ok


def test_reproduction_fails_on_different_outputs(
    record: RunRecord, benchmark: Benchmark
) -> None:
    wrong = FixtureModel({"2+2?": "5", "3+3?": "7"})
    assert not reproduce_record(record, benchmark, wrong)


def test_reproduction_fails_on_different_benchmark(record: RunRecord, model: FixtureModel) -> None:
    other = Benchmark(
        id="arith", version="1.0", scorer="numeric",
        tasks=[Task(id="t1", prompt="2+2?", expected="4")],  # fewer tasks -> different hash
    )
    assert not reproduce_record(record, other, model)


def test_reproduction_skipped_for_nondeterministic_model(record: RunRecord, benchmark: Benchmark) -> None:
    class _FakeClient:
        class messages:  # noqa: N801
            @staticmethod
            def create(**_kwargs: object) -> object:
                return type("R", (), {"content": []})

    nondet = AnthropicAdapter(client=_FakeClient())
    result = verify_record(record, benchmark=benchmark, model=nondet)
    assert result.reproduced_ok is None
    assert any("non-deterministic" in n for n in result.notes)
