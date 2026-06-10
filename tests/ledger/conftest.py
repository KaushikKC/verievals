"""Fixtures for ledger tests."""

from __future__ import annotations

import pytest

from verievals.benchmarks.base import Benchmark, Task
from verievals.crypto.signing import SigningKey, generate_signing_key
from verievals.models.fixture import FixtureModel
from verievals.records.schema import RunRecord
from verievals.runner.engine import run_eval


@pytest.fixture
def key() -> SigningKey:
    return generate_signing_key()


@pytest.fixture
def benchmark() -> Benchmark:
    return Benchmark(
        id="arith",
        version="1.0",
        scorer="numeric",
        tasks=[
            Task(id="t1", prompt="2+2?", expected="4"),
            Task(id="t2", prompt="3+3?", expected="6"),
        ],
    )


@pytest.fixture
def model() -> FixtureModel:
    return FixtureModel({"2+2?": "4", "3+3?": "6"})


@pytest.fixture
def record(benchmark: Benchmark, model: FixtureModel, key: SigningKey) -> RunRecord:
    return run_eval(benchmark, model, signing_key=key, signer="kaushik")
