#!/usr/bin/env python3
"""Fetch the official GSM8K test split and convert it to a verievals benchmark.

Source: https://github.com/openai/grade-school-math (MIT License).
Writes ``benchmarks/gsm8k-full/{benchmark.yaml, tasks.jsonl}`` with all 1,319
test problems, scored by the ``gsm8k`` scorer (final-number extraction).

Usage:
    python scripts/fetch_gsm8k.py                 # download from the source URL
    python scripts/fetch_gsm8k.py path/to/test.jsonl   # convert a local copy
                                                       # (e.g. fetched via curl)
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

SOURCE_URL = (
    "https://raw.githubusercontent.com/openai/grade-school-math/"
    "master/grade_school_math/data/test.jsonl"
)
OUT_DIR = Path(__file__).resolve().parents[1] / "benchmarks" / "gsm8k-full"

BENCHMARK_YAML = """\
id: gsm8k-full
version: "test-1.0.0"
scorer: gsm8k
description: >
  The official GSM8K test split (1,319 grade-school math word problems), fetched
  from https://github.com/openai/grade-school-math (MIT License) and converted by
  scripts/fetch_gsm8k.py. The prompt is the original question verbatim; the
  expected value is the final number after the "####" marker. Scored by the gsm8k
  scorer. Regenerate with: python scripts/fetch_gsm8k.py
"""


def final_answer(answer: str) -> str:
    """GSM8K answers end with '#### <number>'; return that number (no commas)."""
    return answer.split("####")[-1].strip().replace(",", "")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 1:
        print(f"reading local file {sys.argv[1]} ...")
        raw = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        print(f"downloading {SOURCE_URL} ...")
        raw = urllib.request.urlopen(SOURCE_URL, timeout=60).read().decode("utf-8")  # noqa: S310
    lines = [line for line in raw.splitlines() if line.strip()]

    tasks_path = OUT_DIR / "tasks.jsonl"
    with tasks_path.open("w", encoding="utf-8") as fh:
        for i, line in enumerate(lines, start=1):
            item = json.loads(line)
            task = {
                "id": f"gsm8k-test-{i:04d}",
                "prompt": item["question"],
                "expected": final_answer(item["answer"]),
            }
            fh.write(json.dumps(task, ensure_ascii=False) + "\n")

    (OUT_DIR / "benchmark.yaml").write_text(BENCHMARK_YAML, encoding="utf-8")
    print(f"wrote {len(lines)} tasks to {tasks_path}")


if __name__ == "__main__":
    main()
