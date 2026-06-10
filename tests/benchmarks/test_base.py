"""Tests for benchmark/task data models."""

from __future__ import annotations

from verievals.benchmarks.base import Benchmark, Task


def _bench(**overrides: object) -> Benchmark:
    base = {
        "id": "demo",
        "version": "1.0",
        "scorer": "exact_match",
        "tasks": [Task(id="t1", prompt="p", expected="a")],
        "description": "docs",
    }
    base.update(overrides)
    return Benchmark(**base)  # type: ignore[arg-type]


def test_len_counts_tasks() -> None:
    assert len(_bench()) == 1


def test_content_hash_is_stable() -> None:
    assert _bench().content_hash() == _bench().content_hash()


def test_description_does_not_affect_hash() -> None:
    assert _bench(description="A").content_hash() == _bench(description="B").content_hash()


def test_changing_a_task_changes_hash() -> None:
    other = _bench(tasks=[Task(id="t1", prompt="p", expected="DIFFERENT")])
    assert other.content_hash() != _bench().content_hash()


def test_changing_version_changes_hash() -> None:
    assert _bench(version="2.0").content_hash() != _bench().content_hash()


def test_task_dict_roundtrip() -> None:
    task = Task(id="t", prompt="q", expected="a", metadata={"k": "v"})
    assert Task.from_dict(task.to_dict()) == task
