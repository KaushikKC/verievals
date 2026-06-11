"""Offline reproduction test for the captured gemma3:1b GSM8K run.

Replays the committed fixture (gemma3:1b's real outputs) against the GSM8K
sample benchmark. This makes the captured local-model run independently
re-verifiable in CI with no Ollama server and no model download -- the core
promise of verifiable evals, applied to a locally-run open model.
"""

from __future__ import annotations

from pathlib import Path

from verievals.benchmarks.loader import load_benchmark
from verievals.crypto.signing import generate_signing_key
from verievals.models.fixture import FixtureModel
from verievals.runner.engine import run_eval

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "examples" / "fixtures" / "gsm8k_gemma3_1b.json"


def test_captured_gemma_run_reproduces() -> None:
    benchmark = load_benchmark(ROOT / "benchmarks" / "gsm8k")
    model = FixtureModel.from_file(FIXTURE)
    record = run_eval(benchmark, model, signing_key=generate_signing_key())

    # gemma3:1b solved 11 of 12 sample problems (gsm-06 reasoning error).
    assert record.body.aggregate.metrics["passed"] == 11.0
    assert record.body.aggregate.num_tasks == 12
    assert record.verify_signature()


def test_fixture_covers_every_task() -> None:
    benchmark = load_benchmark(ROOT / "benchmarks" / "gsm8k")
    model = FixtureModel.from_file(FIXTURE)
    # strict=True by default: a missing prompt would raise, so this asserts
    # the fixture has an answer for every task in the benchmark.
    for task in benchmark.tasks:
        assert isinstance(model.generate(task.prompt), str)
