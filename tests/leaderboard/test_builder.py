"""Tests for leaderboard construction."""

from __future__ import annotations

from pathlib import Path

import pytest

from verievals.benchmarks.base import Benchmark, Task
from verievals.crypto.signing import SigningKey, generate_signing_key
from verievals.leaderboard.builder import build_leaderboard
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
        tasks=[Task(id="t1", prompt="2+2?", expected="4"), Task(id="t2", prompt="3+3?", expected="6")],
    )


def _run(benchmark: Benchmark, key: SigningKey, name: str, responses: dict[str, str]):
    model = FixtureModel(responses, name=name, strict=False)
    return run_eval(benchmark, model, signing_key=key, signer=name)


def test_entries_sorted_by_accuracy(tmp_path: Path, benchmark: Benchmark, key: SigningKey) -> None:
    store = RecordStore(tmp_path / "records")
    ledger = MerkleLog(tmp_path / "ledger")

    perfect = _run(benchmark, key, "good", {"2+2?": "4", "3+3?": "6"})
    half = _run(benchmark, key, "ok", {"2+2?": "4", "3+3?": "0"})
    for rec in (half, perfect):
        store.save(rec)
        ledger.append(rec)

    board = build_leaderboard(store, ledger)
    assert [e.model_name for e in board.entries] == ["good", "ok"]
    assert board.entries[0].accuracy == 1.0
    assert all(e.inclusion_verified for e in board.entries)
    assert board.root == ledger.root()


def test_excludes_records_not_in_ledger(tmp_path: Path, benchmark: Benchmark, key: SigningKey) -> None:
    store = RecordStore(tmp_path / "records")
    ledger = MerkleLog(tmp_path / "ledger")
    rec = _run(benchmark, key, "good", {"2+2?": "4", "3+3?": "6"})
    store.save(rec)  # saved but NOT appended to the ledger
    board = build_leaderboard(store, ledger)
    assert board.entries == []


def test_benchmark_filter(tmp_path: Path, key: SigningKey) -> None:
    b1 = Benchmark(id="arith", version="1.0", scorer="numeric", tasks=[Task(id="t", prompt="2+2?", expected="4")])
    b2 = Benchmark(id="other", version="1.0", scorer="numeric", tasks=[Task(id="t", prompt="2+2?", expected="4")])
    store = RecordStore(tmp_path / "records")
    ledger = MerkleLog(tmp_path / "ledger")
    for b in (b1, b2):
        rec = run_eval(b, FixtureModel({"2+2?": "4"}, name="m"), signing_key=key)
        store.save(rec)
        ledger.append(rec)
    board = build_leaderboard(store, ledger, benchmark_id="arith")
    assert len(board.entries) == 1
    assert board.entries[0].benchmark_id == "arith"


def test_render_markdown_includes_root(tmp_path: Path, benchmark: Benchmark, key: SigningKey) -> None:
    store = RecordStore(tmp_path / "records")
    ledger = MerkleLog(tmp_path / "ledger")
    rec = _run(benchmark, key, "good", {"2+2?": "4", "3+3?": "6"})
    store.save(rec)
    ledger.append(rec)
    md = build_leaderboard(store, ledger).render_markdown()
    assert "Verifiable Evals Leaderboard" in md
    assert ledger.root() in md
    assert "Accuracy" in md
