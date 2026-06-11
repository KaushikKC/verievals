# GSM8K MVP — verifiable evals for a locally-run open model

This is the milestone-1 MVP: evaluate a small open-source model on a narrow math
benchmark and produce a signed, ledger-anchored, independently re-verifiable
record — entirely on your own machine.

## What it uses

- **Model:** any model served by [Ollama](https://ollama.com), via the
  `OllamaAdapter` (`--model ollama:<tag>`). The default is **`gemma3:1b`** — tiny
  (~815 MB), runs in seconds on an M-series Mac, no download if already pulled.
  Point it at `ollama:llama3:8b` or `ollama:deepseek-r1:7b` for stronger models.
- **Benchmark:** `benchmarks/gsm8k` — a 12-item GSM8K-style sample (integer
  answers). Replace `tasks.jsonl` with the official GSM8K split to run the full
  benchmark; the format is identical.
- **Scorer:** `gsm8k` — extracts the *final* number from chain-of-thought output
  (e.g. `...so 48 + 24 = 72` → `72`).

## Run it live (your machine)

```bash
ollama pull gemma3:1b          # if not already present
verievals keygen --out ./keys/runner
verievals run \
    --benchmark benchmarks/gsm8k \
    --model ollama:gemma3:1b \
    --key ./keys/runner.key \
    --out ./records --signer me
verievals ledger --ledger ./ledger append ./records/<id>.json
verievals leaderboard --records ./records --ledger ./ledger --trust
```

Measured result on this repo's hardware (Apple M3): **gemma3:1b scored 11/12
(0.917)** on the sample; the single miss (`gsm-06`) is a genuine reasoning error
by the 1B model, not a harness issue.

## Reproduce it offline (anyone)

Local model inference isn't bit-for-bit deterministic across machines, so the
`OllamaAdapter` reports `deterministic = False`. To make a local run independently
re-verifiable, its exact prompt→output pairs are captured into a fixture
(`examples/fixtures/gsm8k_gemma3_1b.json`). Replaying it reproduces the scores
with no server and no download:

```bash
python examples/run_gsm8k.py        # offline, deterministic
```

A CI test (`tests/benchmarks/test_gsm8k_fixture.py`) asserts the captured run
reproduces 11/12 — turning "we ran gemma3:1b and got 0.917" into a checkable claim.

## Why not Llama-3-8B by default?

Llama-3-8B runs fine on 16 GB Apple Silicon, but needs a ~4.7 GB download and is
the slowest option. The adapter is model-agnostic, so the MVP defaults to the
tiny `gemma3:1b` for instant, zero-download runs; use `--model ollama:llama3:8b`
when you want the bigger model.
