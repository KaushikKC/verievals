"""End-to-end tests driving the full pipeline through the CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from verievals.cli.main import main
from verievals.records.store import RecordStore


@pytest.fixture
def arithmetic_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "benchmarks" / "arithmetic"


def _keygen(tmp_path: Path) -> Path:
    assert main(["keygen", "--out", str(tmp_path / "k")]) == 0
    return tmp_path / "k.key"


def _run(tmp_path: Path, key: Path, arithmetic_dir: Path, records: Path) -> str:
    rc = main(
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
            "--signer",
            "kaushik",
        ]
    )
    assert rc == 0
    ids = RecordStore(records).record_ids()
    assert len(ids) == 1
    return ids[0]


def test_full_pipeline(tmp_path: Path, arithmetic_dir: Path, capsys: pytest.CaptureFixture) -> None:
    key = _keygen(tmp_path)
    records = tmp_path / "records"
    ledger = tmp_path / "ledger"

    record_id = _run(tmp_path, key, arithmetic_dir, records)
    record_path = records / f"{record_id}.json"

    # Append to the ledger.
    assert main(["ledger", "--ledger", str(ledger), "append", str(record_path)]) == 0

    # Verify with inclusion + reproduction (echo is deterministic).
    capsys.readouterr()
    rc = main(
        [
            "verify",
            str(record_path),
            "--ledger",
            str(ledger),
            "--benchmark",
            str(arithmetic_dir),
            "--model",
            "echo",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "VERIFIED" in out
    assert "Integrity:    ok" in out
    assert "Inclusion:    ok" in out
    assert "Reproduction: ok" in out


def test_verify_detects_tampering(
    tmp_path: Path, arithmetic_dir: Path, capsys: pytest.CaptureFixture
) -> None:
    key = _keygen(tmp_path)
    records = tmp_path / "records"
    record_id = _run(tmp_path, key, arithmetic_dir, records)
    record_path = records / f"{record_id}.json"

    # Tamper with the stored record: inflate accuracy.
    data = json.loads(record_path.read_text())
    data["body"]["aggregate"]["metrics"]["accuracy"] = 1.0
    record_path.write_text(json.dumps(data))

    capsys.readouterr()
    rc = main(["verify", str(record_path)])
    out = capsys.readouterr().out
    assert rc == 1
    assert "NOT VERIFIED" in out
    assert "Integrity:    FAIL" in out


def test_ledger_root_command(
    tmp_path: Path, arithmetic_dir: Path, capsys: pytest.CaptureFixture
) -> None:
    key = _keygen(tmp_path)
    records = tmp_path / "records"
    ledger = tmp_path / "ledger"
    record_id = _run(tmp_path, key, arithmetic_dir, records)
    main(["ledger", "--ledger", str(ledger), "append", str(records / f"{record_id}.json")])

    capsys.readouterr()
    assert main(["ledger", "--ledger", str(ledger), "root"]) == 0
    root = capsys.readouterr().out.strip()
    assert len(root) == 64  # sha256 hex


def test_leaderboard_command(
    tmp_path: Path, arithmetic_dir: Path, capsys: pytest.CaptureFixture
) -> None:
    key = _keygen(tmp_path)
    records = tmp_path / "records"
    ledger = tmp_path / "ledger"
    record_id = _run(tmp_path, key, arithmetic_dir, records)
    main(["ledger", "--ledger", str(ledger), "append", str(records / f"{record_id}.json")])

    capsys.readouterr()
    rc = main(["leaderboard", "--records", str(records), "--ledger", str(ledger)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Verifiable Evals Leaderboard" in out


def test_version_flag(capsys: pytest.CaptureFixture) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "verievals" in capsys.readouterr().out
