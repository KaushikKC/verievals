"""Sanity test for the full official GSM8K test split (1,319 problems)."""

from __future__ import annotations

from pathlib import Path

from verievals.benchmarks.loader import load_benchmark

ROOT = Path(__file__).resolve().parents[2]


def test_gsm8k_full_loads_all_1319() -> None:
    bench = load_benchmark(ROOT / "benchmarks" / "gsm8k-full")
    assert bench.id == "gsm8k-full"
    assert bench.scorer == "gsm8k"
    assert len(bench) == 1319


def test_gsm8k_full_answers_are_integers() -> None:
    bench = load_benchmark(ROOT / "benchmarks" / "gsm8k-full")
    for task in bench.tasks:
        assert task.expected is not None
        int(task.expected)  # raises if not an integer


def test_gsm8k_full_content_hash_is_stable() -> None:
    bench = load_benchmark(ROOT / "benchmarks" / "gsm8k-full")
    assert bench.content_hash() == load_benchmark(ROOT / "benchmarks" / "gsm8k-full").content_hash()
