"""Tests for HTML leaderboard rendering."""

from __future__ import annotations

from pathlib import Path

import pytest

from verievals.benchmarks.base import Benchmark, Task
from verievals.crypto.signing import SigningKey, generate_signing_key
from verievals.leaderboard.builder import build_leaderboard
from verievals.leaderboard.trust import build_trust_leaderboard
from verievals.ledger.merkle_log import MerkleLog
from verievals.models.fixture import FixtureModel
from verievals.records.store import RecordStore
from verievals.runner.engine import run_eval


@pytest.fixture
def key() -> SigningKey:
    return generate_signing_key()


@pytest.fixture
def populated(tmp_path: Path, key: SigningKey):
    benchmark = Benchmark(
        id="arith",
        version="1.0",
        scorer="numeric",
        tasks=[Task(id="t1", prompt="2+2?", expected="4")],
    )
    store = RecordStore(tmp_path / "records")
    ledger = MerkleLog(tmp_path / "ledger")
    rec = run_eval(
        benchmark, FixtureModel({"2+2?": "4"}, name="m"), signing_key=key, signer="kaushik"
    )
    store.save(rec)
    ledger.append(rec)
    return store, ledger


def test_accuracy_board_html_is_wellformed(populated) -> None:
    store, ledger = populated
    html = build_leaderboard(store, ledger).render_html()
    assert html.startswith("<!doctype html>")
    assert "<table>" in html and "</table>" in html
    assert "Verifiable Evals Leaderboard" in html
    assert ledger.root() in html


def test_trust_board_html_has_tier_classes(populated) -> None:
    store, ledger = populated
    html = build_trust_leaderboard(store, ledger).render_html()
    assert "Trust Score Leaderboard" in html
    assert 'class="tier verified"' in html
    assert "Trust tiers:" in html  # legend present


def test_html_escapes_values(tmp_path: Path, key: SigningKey) -> None:
    # A signer containing HTML must be escaped, not injected.
    benchmark = Benchmark(
        id="b",
        version="1.0",
        scorer="numeric",
        tasks=[Task(id="t1", prompt="2+2?", expected="4")],
    )
    store = RecordStore(tmp_path / "records")
    ledger = MerkleLog(tmp_path / "ledger")
    rec = run_eval(
        benchmark,
        FixtureModel({"2+2?": "4"}, name="m"),
        signing_key=key,
        signer="<script>x</script>",
    )
    store.save(rec)
    ledger.append(rec)
    html = build_trust_leaderboard(store, ledger).render_html()
    assert "<script>x</script>" not in html
    assert "&lt;script&gt;" in html
