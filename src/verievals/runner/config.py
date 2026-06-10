"""Run configuration.

Every field here affects the result and is therefore recorded in the run record
so a verifier can reproduce the exact run.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunConfig:
    """Determinism-affecting configuration for an eval run.

    Attributes:
        seed: random seed recorded for reproducibility (used by samplers; the
            built-in deterministic models ignore it but it is still pinned).
        sample_limit: if set, evaluate only the first N tasks (in benchmark
            order). ``None`` evaluates all tasks.
        scorer: optional scorer id overriding the benchmark's default scorer.
    """

    seed: int = 0
    sample_limit: int | None = None
    scorer: str | None = None
