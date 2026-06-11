"""Sanity test for the bundled capitals benchmark."""

from __future__ import annotations

from pathlib import Path

from verievals.benchmarks.loader import load_benchmark
from verievals.crypto.signing import generate_signing_key
from verievals.models.fixture import FixtureModel
from verievals.runner.engine import run_eval


def _capitals_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "benchmarks" / "capitals"


def test_capitals_loads_with_exact_match() -> None:
    bench = load_benchmark(_capitals_dir())
    assert bench.id == "capitals"
    assert bench.scorer == "exact_match"
    assert len(bench) == 10


def test_exact_match_tolerates_case_and_whitespace() -> None:
    bench = load_benchmark(_capitals_dir())
    # Answer with different case / surrounding whitespace; exact_match normalizes.
    responses = {t.prompt: f"  {(t.expected or '').upper()} " for t in bench.tasks}
    model = FixtureModel(responses, name="loud-solver")
    record = run_eval(bench, model, signing_key=generate_signing_key())
    assert record.body.aggregate.metrics["accuracy"] == 1.0
