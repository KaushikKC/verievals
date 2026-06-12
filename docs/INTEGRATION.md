# Integrate your own model & benchmark

`verievals` is a library you **install and depend on** — you do not fork or edit
its source. In your own project you (1) point it at a model and (2) point it at a
benchmark, and it gives you a signed, reproducible, verifiable record of the run.

This guide takes you from zero to a **verified result** in three steps.

```
pip install verievals          # (until published to PyPI:)
# pip install "git+https://github.com/KaushikKC/verievals.git"
```

---

## Step 1 — Bring your model

A model in verievals is anything that turns a prompt into text. You have three
options, easiest first.

### Option A — a model that's already supported (no code)

Reference it by a spec string:

| Spec | Model |
|------|-------|
| `ollama:llama3:8b` | any local open model served by Ollama |
| `anthropic:claude-opus-4-8` | Claude via the Anthropic API |
| `openai:gpt-4o` | OpenAI via the Chat Completions API |

```bash
verievals run --benchmark ./my-benchmark --model ollama:llama3:8b \
    --key ./keys/runner.key --out ./records --signer my-org
```

### Option B — your own / proprietary model (≈15 lines)

This is the real integration point. Wrap your model behind one method —
`generate(prompt) -> str` — and describe it in `info()`:

```python
from verievals.models.base import ModelAdapter, ModelInfo

class MyModelAdapter(ModelAdapter):
    def __init__(self):
        # load your model once (HF pipeline, API client, local weights, ...)
        from transformers import pipeline
        self.pipe = pipeline("text-generation", model="my-org/my-model")

    def generate(self, prompt: str) -> str:
        out = self.pipe(prompt, max_new_tokens=64, do_sample=False)
        return out[0]["generated_text"][len(prompt):].strip()

    def info(self) -> ModelInfo:
        # everything here is recorded so others know exactly what you ran
        return ModelInfo(
            provider="my-org",
            name="my-model",
            version="v1.0",
            params={"max_new_tokens": 64, "do_sample": False},
        )
```

A model behind an HTTP API is the same shape:

```python
    def generate(self, prompt: str) -> str:
        r = requests.post(MY_ENDPOINT, json={"prompt": prompt}, timeout=60)
        return r.json()["text"]
```

Then run it from Python (see Step 3) — no CLI spec needed for custom adapters.

### Option C — you already have an eval loop (use the SDK)

If you have an existing evaluation/training loop, don't adopt the runner at all.
Log each result inside your loop and get the same signed record out:

```python
from verievals.sdk import EvalRecorder

with EvalRecorder("my-bench", "1.0", model_info, signing_key, scorer="numeric") as rec:
    for task in my_dataset:
        output = my_model(task.prompt)
        rec.log(task.id, task.prompt, output, expected=task.answer)

record = rec.record   # signed, verifiable — ready for a ledger
```

---

## Step 2 — Bring your benchmark

A benchmark is a folder with two files. No code required.

```
my-benchmark/
├── benchmark.yaml
└── tasks.jsonl
```

`benchmark.yaml`:

```yaml
id: my-bench
version: "1.0.0"
scorer: numeric        # exact_match | regex_match | numeric | gsm8k
description: What this benchmark measures.
```

`tasks.jsonl` (one JSON object per line):

```json
{"id": "q1", "prompt": "What is 7 + 5? Reply with only the number.", "expected": "12"}
{"id": "q2", "prompt": "What is 6 * 7? Reply with only the number.", "expected": "42"}
```

Pick the scorer that matches your answers: `exact_match` (text), `numeric`
(a number anywhere), `gsm8k` (the final number after reasoning), or `regex_match`.
To evaluate on a standard benchmark like the full GSM8K, just put its problems
into `tasks.jsonl` in this format.

---

## Step 3 — Run, sign, and verify

### From the CLI (built-in model specs)

```bash
verievals keygen --out ./keys/runner
verievals run --benchmark ./my-benchmark --model ollama:llama3:8b \
    --key ./keys/runner.key --out ./records --signer my-org
verievals ledger --ledger ./ledger append ./records/<id>.json
verievals verify ./records/<id>.json --ledger ./ledger
```

### From Python (any custom adapter)

```python
from verievals.benchmarks.loader import load_benchmark
from verievals.crypto.signing import generate_signing_key
from verievals.runner.engine import run_eval

benchmark = load_benchmark("./my-benchmark")
key = generate_signing_key()
record = run_eval(benchmark, MyModelAdapter(), signing_key=key, signer="my-org")
print(record.body.aggregate.metrics["accuracy"])
```

A complete, runnable version is in
[`examples/custom_model.py`](../examples/custom_model.py) — copy it and replace
the model body with your own.

---

## Publishing your result (so others can trust it)

1. Publish your **public key** (`*.pub`) once — this is your identity.
2. Append your record to a ledger and publish the **Merkle root**.
3. Share the **record JSON** (e.g. in your repo, release, or paper).

Anyone can then verify it:

```bash
verievals verify your-record.json --ledger ./ledger
```

Exit code `0` = verified, `1` = not — so it gates CI and badges cleanly.

---

## A note on non-deterministic models

GPU and hosted models are not bit-for-bit reproducible, so a custom adapter for
one should leave `deterministic = False` (the default). The record still pins
exactly what you ran. To make such a run independently re-verifiable offline,
**capture its prompt→output pairs into a fixture** and ship that alongside the
record (see `examples/fixtures/gsm8k_gemma3_1b.json` and `docs/gsm8k-mvp.md`).
Deterministic adapters can override `deterministic` to return `True` and earn the
`reproduced` trust tier directly.
