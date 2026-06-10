"""Load benchmarks from disk.

A benchmark lives in a directory with two files:

* ``benchmark.yaml`` -- metadata: ``id``, ``version``, ``scorer``, ``description``.
* ``tasks.jsonl``    -- one JSON object per line: ``{id, prompt, expected?, metadata?}``.

JSONL keeps task data line-diffable and append-friendly, which matters when the
whole point is that others can audit exactly what was asked.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from verievals.benchmarks.base import Benchmark, Task

_META_FILE = "benchmark.yaml"
_TASKS_FILE = "tasks.jsonl"


def load_benchmark(path: str | Path) -> Benchmark:
    """Load a benchmark from a directory (or its ``benchmark.yaml``)."""
    p = Path(path)
    directory = p.parent if p.is_file() else p
    meta_path = directory / _META_FILE
    tasks_path = directory / _TASKS_FILE

    if not meta_path.exists():
        raise FileNotFoundError(f"missing {_META_FILE} in {directory}")
    if not tasks_path.exists():
        raise FileNotFoundError(f"missing {_TASKS_FILE} in {directory}")

    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
    for key in ("id", "version", "scorer"):
        if key not in meta:
            raise ValueError(f"{_META_FILE} is missing required key: {key!r}")

    tasks = _load_tasks(tasks_path)
    if not tasks:
        raise ValueError(f"benchmark {meta['id']!r} has no tasks")

    _check_unique_ids(tasks)

    return Benchmark(
        id=str(meta["id"]),
        version=str(meta["version"]),
        scorer=str(meta["scorer"]),
        description=str(meta.get("description", "")),
        tasks=tasks,
    )


def _load_tasks(tasks_path: Path) -> list[Task]:
    tasks: list[Task] = []
    with tasks_path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{tasks_path}:{lineno}: invalid JSON: {exc}") from exc
            tasks.append(Task.from_dict(obj))
    return tasks


def _check_unique_ids(tasks: list[Task]) -> None:
    seen: set[str] = set()
    for task in tasks:
        if task.id in seen:
            raise ValueError(f"duplicate task id: {task.id!r}")
        seen.add(task.id)
