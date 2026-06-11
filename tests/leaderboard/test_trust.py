"""Tests for the trust-scored leaderboard."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from verievals.benchmarks.base import Benchmark, Task
from verievals.crypto.signing import SigningKey, generate_signing_key
from verievals.leaderboard.trust import TrustTier, build_trust_leaderboard
from verievals.ledger.merkle_log import MerkleLog
from verievals.models.fixture import FixtureModel
from verievals.records.store import RecordStore
from verievals.runner.engine import run_eval


@pytest.fixture
def key() -> SigningKey:
    return generate_signing_key()


@pytest.fixture
def benchmark() -> Benchmark:
    return Benchmark(
        id="arith",
        version="1.0",
        scorer="numeric",
        tasks=[Task(id="t1", prompt="2+2?", expected="4")],
    )


@pytest.fixture
def model() -> FixtureModel:
    return FixtureModel({"2+2?": "4"}, name="solver")


def test_verified_tier_for_signed_and_included(
    tmp_path: Path, benchmark: Benchmark, model: FixtureModel, key: SigningKey
) -> None:
    store = RecordStore(tmp_path / "records")
    ledger = MerkleLog(tmp_path / "ledger")
    rec = run_eval(benchmark, model, signing_key=key)
    store.save(rec)
    ledger.append(rec)
    board = build_trust_leaderboard(store, ledger)
    assert board.entries[0].tier == TrustTier.VERIFIED
    assert board.entries[0].trust_score == 0.80


def test_signed_tier_when_not_in_ledger(
    tmp_path: Path, benchmark: Benchmark, model: FixtureModel, key: SigningKey
) -> None:
    store = RecordStore(tmp_path / "records")
    ledger = MerkleLog(tmp_path / "ledger")  # empty
    rec = run_eval(benchmark, model, signing_key=key)
    store.save(rec)
    board = build_trust_leaderboard(store, ledger)
    assert board.entries[0].tier == TrustTier.SIGNED
    assert board.entries[0].trust_score == 0.50


def test_self_reported_tier_for_broken_signature(
    tmp_path: Path, benchmark: Benchmark, model: FixtureModel, key: SigningKey
) -> None:
    store = RecordStore(tmp_path / "records")
    ledger = MerkleLog(tmp_path / "ledger")
    rec = run_eval(benchmark, model, signing_key=key)
    broken = dataclasses.replace(
        rec, signature=dataclasses.replace(rec.signature, signature="00" * 64)
    )
    store.save(broken)
    board = build_trust_leaderboard(store, ledger)
    assert board.entries[0].tier == TrustTier.SELF_REPORTED
    assert board.entries[0].trust_score == 0.20


def test_reproduced_tier_with_reproducers(
    tmp_path: Path, benchmark: Benchmark, model: FixtureModel, key: SigningKey
) -> None:
    store = RecordStore(tmp_path / "records")
    ledger = MerkleLog(tmp_path / "ledger")
    rec = run_eval(benchmark, model, signing_key=key)
    store.save(rec)
    ledger.append(rec)
    board = build_trust_leaderboard(store, ledger, reproducers={"arith": (benchmark, model)})
    assert board.entries[0].tier == TrustTier.REPRODUCED
    assert board.entries[0].trust_score == 1.0


def test_sorted_by_trust_then_accuracy(
    tmp_path: Path, benchmark: Benchmark, key: SigningKey
) -> None:
    store = RecordStore(tmp_path / "records")
    ledger = MerkleLog(tmp_path / "ledger")

    # Verified entry (lower accuracy) should still outrank a self-reported one.
    verified = run_eval(benchmark, FixtureModel({"2+2?": "5"}, name="wrong"), signing_key=key)
    store.save(verified)
    ledger.append(verified)

    self_reported = run_eval(
        benchmark, FixtureModel({"2+2?": "4"}, name="claimed"), signing_key=key
    )
    broken = dataclasses.replace(
        self_reported,
        signature=dataclasses.replace(self_reported.signature, signature="00" * 64),
    )
    store.save(broken)

    board = build_trust_leaderboard(store, ledger)
    assert board.entries[0].tier == TrustTier.VERIFIED
    assert board.entries[1].tier == TrustTier.SELF_REPORTED


def test_render_markdown_shows_tiers(
    tmp_path: Path, benchmark: Benchmark, model: FixtureModel, key: SigningKey
) -> None:
    store = RecordStore(tmp_path / "records")
    ledger = MerkleLog(tmp_path / "ledger")
    rec = run_eval(benchmark, model, signing_key=key)
    store.save(rec)
    ledger.append(rec)
    md = build_trust_leaderboard(store, ledger).render_markdown()
    assert "Trust Score Leaderboard" in md
    assert "self-reported" in md
    assert ledger.root() in md
