"""The verievals logging SDK.

Drop-in instrumentation for *existing* training/testing loops. Instead of
handing control to :func:`verievals.runner.run_eval`, you wrap your own loop and
log each item; on exit you get a signed, reproducible
:class:`~verievals.records.schema.RunRecord` ready to append to a ledger.

Two surfaces:

* :class:`~verievals.sdk.recorder.EvalRecorder` -- a context manager you call
  ``.log(...)`` on inside your loop.
* :func:`~verievals.sdk.recorder.logged_eval` -- a decorator that runs your
  logging function and returns the finished record.
"""

from verievals.sdk.recorder import EvalRecorder, logged_eval

__all__ = ["EvalRecorder", "logged_eval"]
