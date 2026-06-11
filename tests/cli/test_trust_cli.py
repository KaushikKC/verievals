"""Tests for `verievals leaderboard --trust`."""

from __future__ import annotations

from pathlib import Path

import pytest

from verievals.cli.main import main
from verievals.records.store import RecordStore


@pytest.fixture
def arithmetic_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "benchmarks" / "arithmetic"


def _setup(tmp_path: Path, arithmetic_dir: Path) -> tuple[Path, Path]:
    main(["keygen", "--out", str(tmp_path / "k")])
    records, ledger = tmp_path / "records", tmp_path / "ledger"
    main(
        [
            "run",
            "--benchmark",
            str(arithmetic_dir),
            "--model",
            "echo",
            "--key",
            str(tmp_path / "k.key"),
            "--out",
            str(records),
        ]
    )
    rid = RecordStore(records).record_ids()[0]
    main(["ledger", "--ledger", str(ledger), "append", str(records / f"{rid}.json")])
    return records, ledger


def test_trust_board_shows_verified(
    tmp_path: Path, arithmetic_dir: Path, capsys: pytest.CaptureFixture
) -> None:
    records, ledger = _setup(tmp_path, arithmetic_dir)
    capsys.readouterr()
    rc = main(["leaderboard", "--records", str(records), "--ledger", str(ledger), "--trust"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Trust Score Leaderboard" in out
    assert "verified" in out


def test_trust_board_reproduced_tier(
    tmp_path: Path, arithmetic_dir: Path, capsys: pytest.CaptureFixture
) -> None:
    records, ledger = _setup(tmp_path, arithmetic_dir)
    capsys.readouterr()
    rc = main(
        [
            "leaderboard",
            "--records",
            str(records),
            "--ledger",
            str(ledger),
            "--trust",
            "--reproduce-benchmark",
            str(arithmetic_dir),
            "--reproduce-model",
            "echo",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "reproduced" in out
