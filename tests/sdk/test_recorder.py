"""Tests for the logging SDK recorder."""

from __future__ import annotations

import pytest

from verievals.benchmarks.base import Benchmark, Task
from verievals.crypto.signing import SigningKey, generate_signing_key
from verievals.ledger.merkle_log import MerkleLog
from verievals.ledger.verifier import verify_record
from verievals.models.base import ModelInfo
from verievals.models.fixture import FixtureModel
from verievals.runner.engine import run_eval
from verievals.sdk.recorder import EvalRecorder, logged_eval


@pytest.fixture
def key() -> SigningKey:
    return generate_signing_key()


@pytest.fixture
def model_info() -> ModelInfo:
    return ModelInfo(provider="mock", name="solver", version="1", params={})


def test_context_manager_produces_signed_record(key: SigningKey, model_info: ModelInfo) -> None:
    with EvalRecorder("arith", "1.0", model_info, key, scorer="numeric", signer="kaushik") as rec:
        rec.log("t1", "2+2?", "4", expected="4")
        rec.log("t2", "3+3?", "6", expected="6")
    assert rec.record is not None
    assert rec.record.verify_signature()
    assert rec.record.body.aggregate.metrics["accuracy"] == 1.0
    assert rec.record.envelope.signer == "kaushik"


def test_custom_score_is_used(key: SigningKey, model_info: ModelInfo) -> None:
    rec = EvalRecorder("b", "1.0", model_info, key)
    rec.log("t1", "p", "out", score=0.5, passed=False)
    record = rec.finalize()
    assert record.body.results[0].score == 0.5
    assert record.body.results[0].passed is False
    assert record.body.aggregate.metrics["accuracy"] == 0.0


def test_record_matches_runner_for_same_data(key: SigningKey) -> None:
    # A recorder driven by the same prompts/outputs as run_eval must produce the
    # same body content hash -- proving the SDK and runner agree byte-for-byte.
    benchmark = Benchmark(
        id="arith",
        version="1.0",
        scorer="numeric",
        tasks=[
            Task(id="t1", prompt="2+2?", expected="4"),
            Task(id="t2", prompt="3+3?", expected="6"),
        ],
    )
    model = FixtureModel({"2+2?": "4", "3+3?": "6"}, name="solver")
    runner_record = run_eval(benchmark, model, signing_key=key)

    with EvalRecorder("arith", "1.0", model.info(), key, scorer="numeric") as rec:
        for task in benchmark.tasks:
            rec.log(task.id, task.prompt, model.generate(task.prompt), expected=task.expected)

    assert rec.record is not None
    assert rec.record.content_hash == runner_record.content_hash


def test_decorator_returns_record(key: SigningKey, model_info: ModelInfo) -> None:
    @logged_eval("arith", "1.0", model_info, key, scorer="numeric")
    def evaluate(rec: EvalRecorder) -> None:
        rec.log("t1", "2+2?", "4", expected="4")

    record = evaluate()
    assert record.verify_signature()
    assert record.body.aggregate.num_tasks == 1


def test_exception_in_context_leaves_record_unfinalized(
    key: SigningKey, model_info: ModelInfo
) -> None:
    rec = EvalRecorder("b", "1.0", model_info, key)
    with pytest.raises(RuntimeError, match="boom"), rec:
        rec.log("t1", "p", "o", expected="o")
        raise RuntimeError("boom")
    assert rec.record is None


def test_duplicate_task_id_rejected(key: SigningKey, model_info: ModelInfo) -> None:
    rec = EvalRecorder("b", "1.0", model_info, key)
    rec.log("t1", "p", "o")
    with pytest.raises(ValueError, match="duplicate task id"):
        rec.log("t1", "p2", "o2")


def test_log_after_finalize_rejected(key: SigningKey, model_info: ModelInfo) -> None:
    rec = EvalRecorder("b", "1.0", model_info, key)
    rec.log("t1", "p", "o")
    rec.finalize()
    with pytest.raises(RuntimeError, match="already finalized"):
        rec.log("t2", "p2", "o2")


def test_empty_finalize_raises(key: SigningKey, model_info: ModelInfo) -> None:
    rec = EvalRecorder("b", "1.0", model_info, key)
    with pytest.raises(RuntimeError, match="nothing logged"):
        rec.finalize()


def test_sdk_record_appends_to_ledger_and_verifies(
    key: SigningKey, model_info: ModelInfo, tmp_path
) -> None:
    with EvalRecorder("arith", "1.0", model_info, key, scorer="numeric") as rec:
        rec.log("t1", "2+2?", "4", expected="4")
    ledger = MerkleLog(tmp_path / "ledger")
    ledger.append(rec.record)
    result = verify_record(rec.record, ledger=ledger)
    assert result.ok
    assert result.inclusion_ok
