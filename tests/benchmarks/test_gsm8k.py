"""Sanity test for the bundled GSM8K sample benchmark."""

from __future__ import annotations

from pathlib import Path

from verievals.benchmarks.loader import load_benchmark
from verievals.crypto.signing import generate_signing_key
from verievals.models.fixture import FixtureModel
from verievals.runner.engine import run_eval


def _gsm8k_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "benchmarks" / "gsm8k"


def test_gsm8k_loads_with_gsm8k_scorer() -> None:
    bench = load_benchmark(_gsm8k_dir())
    assert bench.id == "gsm8k"
    assert bench.scorer == "gsm8k"
    assert len(bench) == 12
    # Every task has an integer answer.
    for task in bench.tasks:
        assert task.expected is not None
        int(task.expected)


def test_perfect_solver_scores_full_with_reasoning() -> None:
    bench = load_benchmark(_gsm8k_dir())
    # Simulate chain-of-thought: prepend a distractor number, end with the answer.
    responses = {
        t.prompt: f"Let me think... 999 ... the answer is {t.expected}." for t in bench.tasks
    }
    model = FixtureModel(responses, name="cot-solver")
    record = run_eval(bench, model, signing_key=generate_signing_key())
    assert record.body.aggregate.metrics["accuracy"] == 1.0
