"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from verievals.crypto.signing import SigningKey, generate_signing_key
from verievals.records.schema import (
    Aggregate,
    BenchmarkSpec,
    ModelSpec,
    RunBody,
    RunnerSpec,
    TaskResult,
)


@pytest.fixture
def signing_key() -> SigningKey:
    return generate_signing_key()


@pytest.fixture
def sample_body() -> RunBody:
    results = [
        TaskResult(
            task_id="t1",
            prompt="What is 2 + 2?",
            output="4",
            expected="4",
            score=1.0,
            passed=True,
        ),
        TaskResult(
            task_id="t2",
            prompt="What is 3 + 5?",
            output="7",
            expected="8",
            score=0.0,
            passed=False,
        ),
    ]
    return RunBody(
        verievals_version="0.1.0",
        benchmark=BenchmarkSpec(id="arithmetic", version="1.0", content_hash="ab" * 32),
        model=ModelSpec(provider="mock", name="echo", version="1", params={"temperature": 0}),
        runner=RunnerSpec(seed=7, sample_limit=None),
        results=results,
        aggregate=Aggregate(scorer="exact_match", num_tasks=2, metrics={"accuracy": 0.5}),
    )
