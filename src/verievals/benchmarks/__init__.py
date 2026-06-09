"""Benchmark definitions and loaders.

A :class:`~verievals.benchmarks.base.Benchmark` is an identified, versioned set
of :class:`~verievals.benchmarks.base.Task` items plus a default scorer. Its
:meth:`~verievals.benchmarks.base.Benchmark.content_hash` commits to the exact
tasks and scorer used, so a run record can prove *which* benchmark produced a
result -- not just its name.
"""

from verievals.benchmarks.base import Benchmark, Task
from verievals.benchmarks.loader import load_benchmark

__all__ = ["Benchmark", "Task", "load_benchmark"]
