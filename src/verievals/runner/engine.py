"""The deterministic evaluation engine."""

from __future__ import annotations

from verievals.benchmarks.base import Benchmark
from verievals.crypto.signing import SigningKey
from verievals.models.base import ModelAdapter
from verievals.records.schema import (
    Aggregate,
    BenchmarkSpec,
    ModelSpec,
    RunBody,
    RunnerSpec,
    RunRecord,
    TaskResult,
)
from verievals.runner.config import RunConfig
from verievals.scoring.registry import get_scorer
from verievals.version import __version__


def run_eval(
    benchmark: Benchmark,
    model: ModelAdapter,
    *,
    config: RunConfig | None = None,
    signing_key: SigningKey,
    signer: str | None = None,
) -> RunRecord:
    """Run ``benchmark`` against ``model`` and return a signed run record.

    Tasks are evaluated in benchmark order; ``config.sample_limit`` takes the
    first N. Each task's prompt, raw output, and score are captured verbatim.
    """
    config = config or RunConfig()
    scorer_id = config.scorer or benchmark.scorer
    scorer = get_scorer(scorer_id)

    tasks = benchmark.tasks
    if config.sample_limit is not None:
        tasks = tasks[: config.sample_limit]

    results: list[TaskResult] = []
    passed_count = 0
    for task in tasks:
        output = model.generate(task.prompt)
        score = scorer.score(output, task.expected)
        passed_count += int(score.passed)
        results.append(
            TaskResult(
                task_id=task.id,
                prompt=task.prompt,
                output=output,
                expected=task.expected,
                score=score.value,
                passed=score.passed,
            )
        )

    num_tasks = len(results)
    accuracy = (passed_count / num_tasks) if num_tasks else 0.0

    info = model.info()
    body = RunBody(
        verievals_version=__version__,
        benchmark=BenchmarkSpec(
            id=benchmark.id,
            version=benchmark.version,
            content_hash=benchmark.content_hash(),
        ),
        model=ModelSpec(
            provider=info.provider,
            name=info.name,
            version=info.version,
            params=info.params,
        ),
        runner=RunnerSpec(seed=config.seed, sample_limit=config.sample_limit),
        results=results,
        aggregate=Aggregate(
            scorer=scorer_id,
            num_tasks=num_tasks,
            metrics={"accuracy": accuracy, "passed": float(passed_count)},
        ),
    )
    return RunRecord.create(body, signing_key, signer=signer)
