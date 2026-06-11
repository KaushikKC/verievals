#!/usr/bin/env python3
"""End-to-end example: run, sign, append, verify, and leaderboard.

Runs the bundled arithmetic benchmark with two deterministic models -- a perfect
``fixture`` solver and the ``echo`` baseline -- signs each run, appends both to a
Merkle ledger, verifies one with full reproduction, and prints a leaderboard.

Usage::

    python examples/run_arithmetic.py

Everything is deterministic and offline -- no API keys required.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from verievals.benchmarks.loader import load_benchmark
from verievals.crypto.signing import generate_signing_key
from verievals.leaderboard.builder import build_leaderboard
from verievals.ledger.merkle_log import MerkleLog
from verievals.ledger.verifier import verify_record
from verievals.models.echo import EchoModel
from verievals.models.fixture import FixtureModel
from verievals.records.store import RecordStore
from verievals.runner.engine import run_eval

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_DIR = PROJECT_ROOT / "benchmarks" / "arithmetic"
SOLVER_FIXTURE = PROJECT_ROOT / "examples" / "fixtures" / "arithmetic_solver.json"


def main() -> None:
    benchmark = load_benchmark(BENCHMARK_DIR)
    key = generate_signing_key()

    solver = FixtureModel.from_file(SOLVER_FIXTURE)
    echo = EchoModel()

    with tempfile.TemporaryDirectory() as tmp:
        store = RecordStore(Path(tmp) / "records")
        ledger = MerkleLog(Path(tmp) / "ledger")

        for model, signer in ((solver, "solver"), (echo, "echo")):
            record = run_eval(benchmark, model, signing_key=key, signer=signer)
            store.save(record)
            ledger.append(record)
            acc = record.body.aggregate.metrics["accuracy"]
            print(f"ran {signer:7s} -> accuracy {acc:.3f}  record {record.record_id[:12]}…")

        # Verify the solver's run end-to-end, including bit-for-bit reproduction.
        solver_record = next(
            r for r in store.iter_records() if r.envelope.signer == "solver"
        )
        result = verify_record(
            solver_record, ledger=ledger, benchmark=benchmark, model=solver
        )
        print(f"\nsolver record verified: {result.ok} "
              f"(integrity={result.integrity_ok}, signature={result.signature_ok}, "
              f"inclusion={result.inclusion_ok}, reproduced={result.reproduced_ok})")

        print()
        print(build_leaderboard(store, ledger).render_markdown())


if __name__ == "__main__":
    main()
