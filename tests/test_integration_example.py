"""Guards the public integration example so it can't silently rot."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

from verievals.benchmarks.loader import load_benchmark
from verievals.crypto.signing import generate_signing_key
from verievals.ledger.merkle_log import MerkleLog
from verievals.ledger.verifier import verify_record
from verievals.runner.engine import run_eval

ROOT = Path(__file__).resolve().parents[1]


def _load_example() -> ModuleType:
    path = ROOT / "examples" / "custom_model.py"
    spec = importlib.util.spec_from_file_location("custom_model_example", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_custom_adapter_runs_and_verifies(tmp_path: Path) -> None:
    mod = _load_example()
    benchmark = load_benchmark(ROOT / "benchmarks" / "arithmetic")
    record = run_eval(
        benchmark, mod.CustomModelAdapter(), signing_key=generate_signing_key(), signer="my-org"
    )
    assert 0.0 < record.body.aggregate.metrics["accuracy"] <= 1.0

    ledger = MerkleLog(tmp_path / "ledger")
    ledger.append(record)
    result = verify_record(
        record, ledger=ledger, benchmark=benchmark, model=mod.CustomModelAdapter()
    )
    assert result.ok
    assert result.reproduced_ok


def test_custom_adapter_info_and_determinism() -> None:
    mod = _load_example()
    adapter = mod.CustomModelAdapter()
    info = adapter.info()
    assert info.provider == "my-org"
    assert info.name == "my-model"
    assert adapter.deterministic is True
