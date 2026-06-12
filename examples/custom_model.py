#!/usr/bin/env python3
"""Evaluate YOUR OWN model with verifiable evals — a complete, runnable example.

This is the template a new user copies into their own project. Replace the body
of ``my_model`` with a call to your real model (a HuggingFace transformers
pipeline, a local checkpoint, or an HTTP API) and everything else stays the same.

Run it as-is (it ships with a tiny stand-in model so it works out of the box):

    python examples/custom_model.py
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

from verievals.benchmarks.loader import load_benchmark
from verievals.crypto.signing import generate_signing_key
from verievals.ledger.merkle_log import MerkleLog
from verievals.ledger.verifier import verify_record
from verievals.models.base import ModelAdapter, ModelInfo
from verievals.records.store import RecordStore
from verievals.runner.engine import run_eval

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------- #
# 1. YOUR MODEL.  Replace this function body with your real model.
# --------------------------------------------------------------------------- #
def my_model(prompt: str) -> str:
    """Return your model's text answer for a prompt.

    Replace this with, for example:

        # HuggingFace transformers:
        out = pipe(prompt, max_new_tokens=64, do_sample=False)
        return out[0]["generated_text"][len(prompt):].strip()

        # A hosted API:
        return requests.post(MY_ENDPOINT, json={"prompt": prompt}).json()["text"]

    The toy implementation below just solves "a OP b" so the example runs with no
    dependencies; it is intentionally simple, so it gets the harder items wrong.
    """
    match = re.search(r"(-?\d+)\s*([-+*/])\s*(-?\d+)", prompt)
    if not match:
        return ""
    a, op, b = int(match.group(1)), match.group(2), int(match.group(3))
    result = {"+": a + b, "-": a - b, "*": a * b, "/": (a // b if b else 0)}[op]
    return str(result)


# --------------------------------------------------------------------------- #
# 2. WRAP IT IN AN ADAPTER.  This is the only integration code you write.
# --------------------------------------------------------------------------- #
class CustomModelAdapter(ModelAdapter):
    def generate(self, prompt: str) -> str:
        return my_model(prompt)

    def info(self) -> ModelInfo:
        # Everything here is recorded so others know exactly what you ran.
        return ModelInfo(provider="my-org", name="my-model", version="v1.0", params={})

    @property
    def deterministic(self) -> bool:
        # This toy model is deterministic, so it can earn the 'reproduced' tier.
        # A real GPU/API model should leave this False and ship a captured fixture.
        return True


# --------------------------------------------------------------------------- #
# 3. RUN -> SIGN -> LEDGER -> VERIFY.  Standard for every model.
# --------------------------------------------------------------------------- #
def main() -> None:
    benchmark = load_benchmark(PROJECT_ROOT / "benchmarks" / "arithmetic")
    key = generate_signing_key()

    record = run_eval(benchmark, CustomModelAdapter(), signing_key=key, signer="my-org")
    acc = record.body.aggregate.metrics["accuracy"]
    passed = int(record.body.aggregate.metrics["passed"])
    print(f"model: {record.body.model.provider}:{record.body.model.name}")
    print(f"accuracy: {acc:.3f}  ({passed}/{record.body.aggregate.num_tasks})")
    print(f"record id: {record.record_id[:16]}…")

    with tempfile.TemporaryDirectory() as tmp:
        store = RecordStore(Path(tmp) / "records")
        ledger = MerkleLog(Path(tmp) / "ledger")
        store.save(record)
        ledger.append(record)

        result = verify_record(
            record, ledger=ledger, benchmark=benchmark, model=CustomModelAdapter()
        )
        print(
            f"verified: {result.ok}  "
            f"(integrity={result.integrity_ok}, signature={result.signature_ok}, "
            f"inclusion={result.inclusion_ok}, reproduced={result.reproduced_ok})"
        )


if __name__ == "__main__":
    main()
