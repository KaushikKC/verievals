"""The logging-SDK recorder.

``EvalRecorder`` accumulates per-item results logged from inside an existing
loop, then builds and signs a :class:`~verievals.records.schema.RunRecord` that
is byte-identical in structure to one produced by :func:`verievals.runner.run_eval`.
The benchmark content hash is derived from the logged tasks, so the record stays
verifiable even though the loop -- not the runner -- drove evaluation.

Each item can be scored automatically (pass ``expected`` and let the recorder's
scorer judge it) or with your own grader (pass ``score``/``passed`` directly).
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any

from verievals.benchmarks.base import Benchmark, Task
from verievals.crypto.signing import SigningKey
from verievals.models.base import ModelInfo
from verievals.records.schema import (
    Aggregate,
    BenchmarkSpec,
    ModelSpec,
    RunBody,
    RunnerSpec,
    RunRecord,
    TaskResult,
)
from verievals.scoring.base import Scorer
from verievals.scoring.registry import get_scorer
from verievals.version import __version__


class EvalRecorder:
    """Accumulates logged results and produces a signed record on finalize."""

    def __init__(
        self,
        benchmark_id: str,
        benchmark_version: str,
        model_info: ModelInfo,
        signing_key: SigningKey,
        *,
        scorer: str | Scorer = "exact_match",
        seed: int = 0,
        sample_limit: int | None = None,
        signer: str | None = None,
    ) -> None:
        self.benchmark_id = benchmark_id
        self.benchmark_version = benchmark_version
        self.model_info = model_info
        self.signing_key = signing_key
        self.seed = seed
        self.sample_limit = sample_limit
        self.signer = signer

        self._scorer: Scorer = scorer if isinstance(scorer, Scorer) else get_scorer(scorer)
        self.scorer_id = self._scorer.id

        self._tasks: list[Task] = []
        self._results: list[TaskResult] = []
        self._passed = 0
        self.record: RunRecord | None = None

    def log(
        self,
        task_id: str,
        prompt: str,
        output: str,
        expected: str | None = None,
        *,
        score: float | None = None,
        passed: bool | None = None,
    ) -> bool:
        """Log one evaluated item; return whether it passed.

        If ``score`` is omitted, the recorder's scorer judges ``output`` against
        ``expected``. If ``score`` is provided, your grading is used verbatim
        (``passed`` defaults to ``score >= 1.0``).
        """
        if self.record is not None:
            raise RuntimeError("recorder already finalized; create a new EvalRecorder")
        if any(t.id == task_id for t in self._tasks):
            raise ValueError(f"duplicate task id: {task_id!r}")

        if score is None:
            result = self._scorer.score(output, expected)
            value, ok = result.value, result.passed
        else:
            value = float(score)
            ok = bool(passed) if passed is not None else value >= 1.0

        self._tasks.append(Task(id=task_id, prompt=prompt, expected=expected))
        self._results.append(
            TaskResult(
                task_id=task_id,
                prompt=prompt,
                output=output,
                expected=expected,
                score=value,
                passed=ok,
            )
        )
        self._passed += int(ok)
        return ok

    def finalize(self) -> RunRecord:
        """Build and sign the record from everything logged so far."""
        if self.record is not None:
            return self.record
        if not self._results:
            raise RuntimeError("nothing logged; cannot finalize an empty record")

        benchmark = Benchmark(
            id=self.benchmark_id,
            version=self.benchmark_version,
            scorer=self.scorer_id,
            tasks=self._tasks,
        )
        num_tasks = len(self._results)
        accuracy = self._passed / num_tasks if num_tasks else 0.0

        body = RunBody(
            verievals_version=__version__,
            benchmark=BenchmarkSpec(
                id=benchmark.id,
                version=benchmark.version,
                content_hash=benchmark.content_hash(),
            ),
            model=ModelSpec(
                provider=self.model_info.provider,
                name=self.model_info.name,
                version=self.model_info.version,
                params=self.model_info.params,
            ),
            runner=RunnerSpec(seed=self.seed, sample_limit=self.sample_limit),
            results=self._results,
            aggregate=Aggregate(
                scorer=self.scorer_id,
                num_tasks=num_tasks,
                metrics={"accuracy": accuracy, "passed": float(self._passed)},
            ),
        )
        self.record = RunRecord.create(body, self.signing_key, signer=self.signer)
        return self.record

    def __enter__(self) -> EvalRecorder:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        # Only finalize on clean exit; a raised exception leaves the record None
        # and propagates (we never return True, so exceptions are not swallowed).
        if exc_type is None:
            self.finalize()


def logged_eval(
    benchmark_id: str,
    benchmark_version: str,
    model_info: ModelInfo,
    signing_key: SigningKey,
    **recorder_kwargs: Any,
) -> Callable[[Callable[..., None]], Callable[..., RunRecord]]:
    """Decorator turning a logging function into one that returns a signed record.

    The decorated function receives an :class:`EvalRecorder` as its first
    argument and logs items into it; the wrapper finalizes and returns the record::

        @logged_eval("gsm8k", "1.0", model_info, key, scorer="numeric")
        def evaluate(rec):
            for task in dataset:
                rec.log(task.id, task.prompt, model(task.prompt), expected=task.answer)

        record = evaluate()
    """

    def decorator(fn: Callable[..., None]) -> Callable[..., RunRecord]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> RunRecord:
            recorder = EvalRecorder(
                benchmark_id, benchmark_version, model_info, signing_key, **recorder_kwargs
            )
            fn(recorder, *args, **kwargs)
            return recorder.finalize()

        return wrapper

    return decorator
