"""Tests for the benchmark loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from verievals.benchmarks.loader import load_benchmark


def _write_benchmark(directory: Path, tasks_jsonl: str, meta: str | None = None) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "benchmark.yaml").write_text(
        meta or "id: demo\nversion: '1.0'\nscorer: numeric\ndescription: d\n",
        encoding="utf-8",
    )
    (directory / "tasks.jsonl").write_text(tasks_jsonl, encoding="utf-8")
    return directory


def test_loads_directory(tmp_path: Path) -> None:
    d = _write_benchmark(
        tmp_path / "b",
        '{"id": "t1", "prompt": "q1", "expected": "1"}\n'
        '{"id": "t2", "prompt": "q2", "expected": "2"}\n',
    )
    bench = load_benchmark(d)
    assert bench.id == "demo"
    assert len(bench) == 2
    assert bench.tasks[0].prompt == "q1"


def test_blank_lines_are_skipped(tmp_path: Path) -> None:
    d = _write_benchmark(tmp_path / "b", '{"id": "t1", "prompt": "q"}\n\n')
    assert len(load_benchmark(d)) == 1


def test_missing_meta_key_raises(tmp_path: Path) -> None:
    d = _write_benchmark(
        tmp_path / "b", '{"id": "t1", "prompt": "q"}\n', meta="id: demo\nversion: '1'\n"
    )
    with pytest.raises(ValueError, match="missing required key"):
        load_benchmark(d)


def test_duplicate_task_ids_raise(tmp_path: Path) -> None:
    d = _write_benchmark(
        tmp_path / "b",
        '{"id": "t1", "prompt": "a"}\n{"id": "t1", "prompt": "b"}\n',
    )
    with pytest.raises(ValueError, match="duplicate task id"):
        load_benchmark(d)


def test_invalid_json_line_raises(tmp_path: Path) -> None:
    d = _write_benchmark(tmp_path / "b", "{not json}\n")
    with pytest.raises(ValueError, match="invalid JSON"):
        load_benchmark(d)


def test_loads_bundled_arithmetic_benchmark() -> None:
    root = Path(__file__).resolve().parents[2]
    bench = load_benchmark(root / "benchmarks" / "arithmetic")
    assert bench.id == "arithmetic"
    assert bench.scorer == "numeric"
    assert len(bench) == 15
