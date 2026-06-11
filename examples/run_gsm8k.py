#!/usr/bin/env python3
"""GSM8K MVP: evaluate a locally-run open model with verifiable provenance.

By default this **replays the committed fixture** of gemma3:1b's real outputs,
so it runs fully offline and deterministically -- signing the record, appending
it to a Merkle ledger, verifying it, and printing a trust-scored leaderboard.

To run a model **live** through Ollama instead (gemma3:1b, llama3:8b, ...):

    python examples/run_gsm8k.py --live --model gemma3:1b

That requires a running Ollama server with the model pulled.

Usage::

    python examples/run_gsm8k.py                 # offline, replays the fixture
    python examples/run_gsm8k.py --live --model gemma3:1b
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from verievals.benchmarks.loader import load_benchmark
from verievals.crypto.signing import generate_signing_key
from verievals.leaderboard.trust import build_trust_leaderboard
from verievals.ledger.merkle_log import MerkleLog
from verievals.models.fixture import FixtureModel
from verievals.models.ollama_adapter import OllamaAdapter
from verievals.records.store import RecordStore
from verievals.runner.engine import run_eval

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GSM8K_DIR = PROJECT_ROOT / "benchmarks" / "gsm8k"
FIXTURE = PROJECT_ROOT / "examples" / "fixtures" / "gsm8k_gemma3_1b.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="GSM8K verifiable-evals MVP")
    parser.add_argument("--live", action="store_true", help="run live via Ollama")
    parser.add_argument("--model", default="gemma3:1b", help="Ollama model tag (with --live)")
    args = parser.parse_args()

    benchmark = load_benchmark(GSM8K_DIR)
    key = generate_signing_key()

    if args.live:
        model = OllamaAdapter(args.model, num_predict=512)
        signer = f"ollama:{args.model}"
        print(f"running {args.model} live via Ollama on {len(benchmark)} GSM8K tasks...")
    else:
        model = FixtureModel.from_file(FIXTURE)
        signer = "gemma3:1b-fixture"
        print(f"replaying committed gemma3:1b fixture on {len(benchmark)} GSM8K tasks (offline)...")

    record = run_eval(benchmark, model, signing_key=key, signer=signer)
    acc = record.body.aggregate.metrics["accuracy"]
    passed = int(record.body.aggregate.metrics["passed"])
    print(f"accuracy: {acc:.3f}  ({passed}/{record.body.aggregate.num_tasks})  "
          f"record {record.record_id[:12]}…")

    with tempfile.TemporaryDirectory() as tmp:
        store = RecordStore(Path(tmp) / "records")
        ledger = MerkleLog(Path(tmp) / "ledger")
        store.save(record)
        ledger.append(record)
        print()
        print(build_trust_leaderboard(store, ledger).render_markdown())


if __name__ == "__main__":
    main()
