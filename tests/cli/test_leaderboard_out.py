"""Tests for `verievals leaderboard --out`."""

from __future__ import annotations

from pathlib import Path

import pytest

from verievals.cli.main import main
from verievals.records.store import RecordStore


@pytest.fixture
def arithmetic_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "benchmarks" / "arithmetic"


def test_leaderboard_writes_markdown_file(
    tmp_path: Path, arithmetic_dir: Path, capsys: pytest.CaptureFixture
) -> None:
    key = tmp_path / "k.key"
    assert main(["keygen", "--out", str(tmp_path / "k")]) == 0
    records = tmp_path / "records"
    ledger = tmp_path / "ledger"
    assert (
        main(
            [
                "run",
                "--benchmark",
                str(arithmetic_dir),
                "--model",
                "echo",
                "--key",
                str(key),
                "--out",
                str(records),
            ]
        )
        == 0
    )
    rid = RecordStore(records).record_ids()[0]
    main(["ledger", "--ledger", str(ledger), "append", str(records / f"{rid}.json")])

    out_file = tmp_path / "board.md"
    capsys.readouterr()
    rc = main(
        [
            "leaderboard",
            "--records",
            str(records),
            "--ledger",
            str(ledger),
            "--out",
            str(out_file),
        ]
    )
    assert rc == 0
    assert "Wrote leaderboard" in capsys.readouterr().out
    assert "Verifiable Evals Leaderboard" in out_file.read_text()
