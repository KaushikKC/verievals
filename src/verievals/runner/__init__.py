"""The evaluation engine.

:func:`~verievals.runner.engine.run_eval` runs a benchmark against a model with a
scorer, captures every prompt/output/score, aggregates metrics, and returns a
signed :class:`~verievals.records.schema.RunRecord`. Task order and selection are
deterministic so the run is reproducible.
"""

from verievals.runner.config import RunConfig
from verievals.runner.engine import run_eval

__all__ = ["RunConfig", "run_eval"]
