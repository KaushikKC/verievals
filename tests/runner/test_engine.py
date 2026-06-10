"""Tests for the evaluation engine."""

from __future__ import annotations

import pytest

from verievals.benchmarks.base import Benchmark, Task
from verievals.crypto.signing import SigningKey, generate_signing_key
from verievals.models.fixture import FixtureModel
from verievals.runner.config import RunConfig
from verievals.runner.engine import run_eval


@pytest.fixture
def benchmark() -> Benchmark:
    return Benchmark(
        id="arith",
        version="1.0",
        scorer="numeric",
        tasks=[
            Task(id="t1", prompt="2+2?", expected="4"),
            Task(id="t2", prompt="3+3?", expected="6"),
            Task(id="t3", prompt="9+9?", expected="18"),
        ],
    )


@pytest.fixture
def key() -> SigningKey:
    return generate_signing_key()


def test_run_produces_signed_record(benchmark: Benchmark, key: SigningKey) -> None:
    model = FixtureModel({"2+2?": "4", "3+3?": "6", "9+9?": "18"})
    record = run_eval(benchmark, model, signing_key=key, signer="kaushik")
    assert record.verify_signature()
    assert record.body.aggregate.metrics["accuracy"] == 1.0
    assert record.body.aggregate.num_tasks == 3


def test_partial_accuracy(benchmark: Benchmark, key: SigningKey) -> None:
    model = FixtureModel({"2+2?": "4", "3+3?": "WRONG", "9+9?": "18"})
    record = run_eval(benchmark, model, signing_key=key)
    assert record.body.aggregate.metrics["accuracy"] == pytest.approx(2 / 3)
    assert record.body.aggregate.metrics["passed"] == 2.0


def test_captures_prompts_and_outputs(benchmark: Benchmark, key: SigningKey) -> None:
    model = FixtureModel({"2+2?": "4", "3+3?": "6", "9+9?": "18"})
    record = run_eval(benchmark, model, signing_key=key)
    first = record.body.results[0]
    assert first.task_id == "t1"
    assert first.prompt == "2+2?"
    assert first.output == "4"
    assert first.expected == "4"


def test_sample_limit_takes_first_n(benchmark: Benchmark, key: SigningKey) -> None:
    model = FixtureModel({"2+2?": "4", "3+3?": "6"})
    record = run_eval(benchmark, model, config=RunConfig(sample_limit=2), signing_key=key)
    assert record.body.aggregate.num_tasks == 2
    assert [r.task_id for r in record.body.results] == ["t1", "t2"]


def test_scorer_override(benchmark: Benchmark, key: SigningKey) -> None:
    model = FixtureModel({"2+2?": "4", "3+3?": "6", "9+9?": "18"})
    record = run_eval(benchmark, model, config=RunConfig(scorer="exact_match"), signing_key=key)
    assert record.body.aggregate.scorer == "exact_match"


def test_runs_are_reproducible(benchmark: Benchmark, key: SigningKey) -> None:
    model = FixtureModel({"2+2?": "4", "3+3?": "6", "9+9?": "18"})
    r1 = run_eval(benchmark, model, signing_key=key)
    r2 = run_eval(benchmark, model, signing_key=key)
    # Same body -> same content hash, even though timestamps differ.
    assert r1.content_hash == r2.content_hash


def test_records_benchmark_content_hash(benchmark: Benchmark, key: SigningKey) -> None:
    model = FixtureModel({"2+2?": "4", "3+3?": "6", "9+9?": "18"})
    record = run_eval(benchmark, model, signing_key=key)
    assert record.body.benchmark.content_hash == benchmark.content_hash()
