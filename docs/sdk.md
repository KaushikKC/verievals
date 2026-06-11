# Logging SDK

The SDK instruments an **existing** evaluation loop so it emits a signed,
reproducible `RunRecord` — without handing control to `run_eval`. Use it when you
already have a training/testing loop and just want verifiable provenance for the
numbers it produces.

## `EvalRecorder` (context manager)

```python
from verievals.crypto.signing import generate_signing_key
from verievals.models.base import ModelInfo
from verievals.sdk import EvalRecorder

key = generate_signing_key()
info = ModelInfo(provider="local", name="my-model", version="1", params={})

with EvalRecorder("gsm8k", "1.0", info, key, scorer="numeric", signer="kaushik") as rec:
    for task in dataset:
        output = my_model(task.prompt)
        rec.log(task.id, task.prompt, output, expected=task.answer)

# On clean exit the record is built + signed:
record = rec.record            # ready to append to a ledger
```

- `log(...)` with `expected` lets the recorder's scorer judge the item.
- `log(..., score=..., passed=...)` records your **own** grader's verdict verbatim
  (use this when you have a custom or model-graded metric).
- If the `with` block raises, the record is **not** finalized (`rec.record is None`) —
  partial runs never produce a misleading signed artifact.

## `@logged_eval` (decorator)

```python
from verievals.sdk import logged_eval

@logged_eval("gsm8k", "1.0", info, key, scorer="numeric")
def evaluate(rec):
    for task in dataset:
        rec.log(task.id, task.prompt, my_model(task.prompt), expected=task.answer)

record = evaluate()            # returns the signed RunRecord
```

## Parity with the runner

A record produced by the SDK is **byte-identical in structure** to one produced
by `run_eval` for the same prompts/outputs — same body schema, same benchmark
content hash derived from the logged tasks, same signature scheme. It verifies,
appends to a ledger, and appears on a (trust) leaderboard exactly the same way.
This is enforced by a test (`test_record_matches_runner_for_same_data`).
