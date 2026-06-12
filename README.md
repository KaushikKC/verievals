# Verifiable Evals (`verievals`)

> **Every eval run produces a signed, reproducible record — model version, prompts,
> outputs, scores, seed, and config — appended to a public Merkle log. Anyone can
> re-run and *cryptographically verify* any leaderboard entry.**

[![CI](https://github.com/kccreations1704/verifiable-evals/actions/workflows/ci.yml/badge.svg)](https://github.com/kccreations1704/verifiable-evals/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-204_passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-97%25-brightgreen.svg)](pyproject.toml)
[![Typed](https://img.shields.io/badge/typed-mypy_strict-blue.svg)](pyproject.toml)

---

## Table of contents

- [The problem](#the-problem)
- [The idea: the evidence is the artifact](#the-idea-the-evidence-is-the-artifact)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Integrate your own model & benchmark](#integrate-your-own-model--benchmark)
- [Architecture](#architecture)
- [The `RunRecord`](#the-runrecord)
- [Cryptographic design](#cryptographic-design)
- [The verification protocol](#the-verification-protocol)
- [Trust Score leaderboard](#trust-score-leaderboard)
- [Determinism & the reproducibility model](#determinism--the-reproducibility-model)
- [The logging SDK](#the-logging-sdk)
- [Models, benchmarks, and scorers](#models-benchmarks-and-scorers)
- [GSM8K MVP: a locally-run open model, end to end](#gsm8k-mvp-a-locally-run-open-model-end-to-end)
- [Command-line interface](#command-line-interface)
- [Threat model](#threat-model)
- [Project layout](#project-layout)
- [Development](#development)
- [Project status](#project-status)
- [Roadmap](#roadmap)
- [License](#license)

---

## The problem

AI evaluations today are frequently **not transparent, accessible, or verifiable**.
When a lab reports a benchmark number, it is often impossible to recover the exact
prompts, decoding parameters, model snapshot, or scoring rules that produced it.
The consequences are well documented:

- **Irreproducibility.** The same benchmark, run by two parties, yields different
  numbers because the setup differed in ways nobody recorded.
- **Conflicting claims.** Different labs publish different scores for the *same*
  benchmark and the same model, with no way to adjudicate.
- **Self-reported trust.** A leaderboard entry is, in practice, a claim backed by
  a PDF — there is no mechanism for a third party to confirm it.

This project takes the position that a benchmark result should be an **auditable
artifact**, not a claim. It implements the machinery to make that true.

## The idea: the evidence *is* the artifact

`verievals` is a benchmark runner in which the output of a run is a
**canonical, content-addressed, Ed25519-signed, Merkle-anchored record** that
contains everything needed to understand and reproduce the result:

- the model identity (provider, name, resolved version) and **every decoding
  parameter**;
- the benchmark identity **plus a content hash of its exact tasks and scorer**;
- the random seed and sampling configuration;
- **every prompt, every raw output, and every per-task score**, verbatim;
- the aggregate metrics.

That record is signed and its content hash is appended to an append-only
**Merkle ledger**. The ledger's single root hash commits to every result it
contains, and a compact inclusion proof lets anyone confirm a specific record is
committed under a published root. No blockchain is required — the root is 32 bytes
and can be published in a README, a git tag, or a tweet (an optional L2 anchor can
be layered on later).

A verifier can then, with only the public artifacts:

1. confirm the record has not been altered (content hash matches the body),
2. confirm who signed it (Ed25519 signature),
3. confirm it is committed under the published root (Merkle inclusion proof), and
4. for a deterministic model, **re-run the eval and confirm the outputs and scores
   reproduce bit-for-bit**.

```
prompts + config + seed ──▶ model ──▶ outputs ──▶ scorer ──▶ scores
        │                                                       │
        └──────────────── canonical RunRecord (body) ───────────┘
                                  │
                       sha256 (content address = record id)
                                  │
                 Ed25519 signature   +   Merkle leaf
                                  │
                          published root ◀── inclusion proof ──▶ anyone verifies
```

## Installation

```bash
pip install verievals
```

Optional model backends and dev tooling:

```bash
pip install "verievals[anthropic]"   # Claude adapter
pip install "verievals[openai]"      # OpenAI adapter
pip install "verievals[dev]"         # tests, lint, types, build/publish tools
```

From source (for contributing, or before the PyPI release):

```bash
git clone https://github.com/KaushikKC/verievals && cd verievals
pip install -e ".[dev]"
```

## Quickstart

```bash
# 1. Generate a signing keypair (the private key stays local, chmod 0600)
verievals keygen --out ./keys/runner

# 2. Run a benchmark deterministically and emit a signed record
verievals run \
    --benchmark benchmarks/arithmetic \
    --model echo \
    --key ./keys/runner.key \
    --out ./records \
    --signer "your-name"

# 3. Append the record to the public Merkle ledger
verievals ledger --ledger ./ledger append ./records/<record-id>.json

# 4. Anyone can verify the record reproduces and is included under the root
verievals verify ./records/<record-id>.json \
    --ledger ./ledger --benchmark benchmarks/arithmetic --model echo

# 5. Build a trust-scored leaderboard
verievals leaderboard --records ./records --ledger ./ledger --trust
```

A fully offline, deterministic walkthrough of the whole pipeline:

```bash
python examples/run_arithmetic.py     # run → sign → ledger → verify → leaderboard
python examples/run_gsm8k.py          # the local-model MVP, replayed from a fixture
```

## Integrate your own model & benchmark

You **install `verievals` as a dependency** in your own project — you don't fork
or edit its source. Then you plug in two things: your model and your benchmark.

**Your model** — three options, easiest first:

- **Already supported** (no code): a spec string — `ollama:llama3:8b`,
  `anthropic:claude-opus-4-8`, `openai:gpt-4o`.
- **Your own / proprietary model** — wrap it in a ~15-line adapter:

  ```python
  from verievals.models.base import ModelAdapter, ModelInfo

  class MyModelAdapter(ModelAdapter):
      def generate(self, prompt: str) -> str:
          return my_model(prompt)          # your transformers pipeline / API call
      def info(self) -> ModelInfo:
          return ModelInfo("my-org", "my-model", "v1.0", {})
  ```

- **You already have an eval loop** — use the SDK (`EvalRecorder`) and just
  `rec.log(...)` inside your existing loop.

**Your benchmark** — a folder with `benchmark.yaml` (`id`, `version`, `scorer`)
and `tasks.jsonl` (`{id, prompt, expected}` per line). Drop in the full GSM8K
split, or your own tasks, in the same format.

Then run it to get a signed, verifiable record:

```python
from verievals.benchmarks.loader import load_benchmark
from verievals.crypto.signing import generate_signing_key
from verievals.runner.engine import run_eval

record = run_eval(load_benchmark("./my-benchmark"), MyModelAdapter(),
                  signing_key=generate_signing_key(), signer="my-org")
print(record.body.aggregate.metrics["accuracy"])
```

**Full walkthrough:** [`docs/INTEGRATION.md`](docs/INTEGRATION.md) ·
**runnable template:** [`examples/custom_model.py`](examples/custom_model.py).

## Architecture

The package is a set of small, single-responsibility modules with a strictly
downward dependency flow (no cycles):

```
verievals
├── crypto       canonical JSON · SHA-256 content addressing · RFC 6962 Merkle · Ed25519
├── records      RunRecord schema (body / envelope / signature) · filesystem store
├── models       adapter interface · echo + fixture (deterministic)
│                                  · ollama (local) · anthropic + openai (hosted)
├── benchmarks   Benchmark/Task models (+ content hash) · yaml+jsonl loader
├── scoring      exact-match · regex · numeric · gsm8k · registry
├── runner       deterministic eval engine → signed RunRecord
├── sdk          EvalRecorder context manager + @logged_eval decorator
├── ledger       append-only Merkle log · 4-stage verification protocol
├── leaderboard  accuracy board · trust-scored board (verification tiers)
└── cli          keygen · run · ledger · verify · leaderboard
```

Dependency direction: `crypto` depends on nothing internal → `records` →
`runner` (also uses `benchmarks`, `models`, `scoring`) → `ledger` → `leaderboard`
/ `cli` / `sdk` on top.

| Module | Responsibility |
|--------|----------------|
| `crypto` | Deterministic JSON encoding, content hashing, Merkle tree + inclusion proofs, signing/verification — the trust primitives. |
| `records` | The `RunRecord` schema and a content-addressed filesystem store. |
| `models` | A uniform `ModelAdapter` interface and concrete adapters (deterministic, local, hosted). |
| `benchmarks` | Immutable, versioned benchmark/task definitions with a verifiable content hash, and a yaml+jsonl loader. |
| `scoring` | Deterministic scorers behind an id registry, so the scorer is pinned by the record. |
| `runner` | The deterministic engine that runs a benchmark against a model with a scorer and produces a signed record. |
| `sdk` | Drop-in instrumentation that emits the same signed record from inside an existing eval loop. |
| `ledger` | The append-only Merkle log and the verification protocol. |
| `leaderboard` | Ranked boards built only from verifying, ledger-included records. |
| `cli` | The `verievals` command-line entry point. |

## The `RunRecord`

The record is the central artifact. It splits cleanly into three parts:

| Part | Hashed? | Contents |
|------|:-------:|----------|
| **body** | ✅ | Everything deterministic and reproducible: benchmark spec (with content hash), model spec + params, runner config (seed, sample limit), per-task results (prompt / output / expected / score / passed), aggregate metrics. |
| **envelope** | ❌ | Non-deterministic metadata: wall-clock `created_at`, optional signer label. |
| **signature** | — | Ed25519 signature over the content hash, plus the signer's public key. |

The body's canonical SHA-256 is both the **record id** and the **Merkle leaf**.
This split is what lets a record be *both signable and reproducible*: re-running
the body yields the same content hash regardless of *when* or *by whom* it was run,
while the timestamp and signature live outside the hashed payload. Records are
stored as human-readable JSON named `<record-id>.json` — the filename is itself a
verifiable claim about the contents.

Schema version: `verievals/runrecord/v1`. Full reference:
[`docs/record-format.md`](docs/record-format.md).

## Cryptographic design

- **Canonical JSON** (`crypto/canonical.py`). A pragmatic subset of RFC 8785: keys
  sorted, no insignificant whitespace, UTF-8, `NaN`/`Infinity` rejected. This makes
  the byte serialization of a logical value a pure function of that value, so two
  parties hashing "the same" record get identical bytes.
- **Content addressing** (`crypto/hashing.py`). `content_hash(x) =
  sha256(canonical_json(x))`, lowercase hex. A stable identifier for any logical
  object.
- **Merkle tree** (`crypto/merkle.py`). The **RFC 6962 (Certificate Transparency)**
  construction: domain-separated leaf (`0x00`) and internal-node (`0x01`) hashing,
  and the split-at-largest-power-of-two tree shape. This is widely reviewed and
  avoids the second-preimage weakness of naive "duplicate the last leaf" trees.
  Inclusion proofs use the RFC 6962 audit-path verification algorithm. Verified by
  property tests across tree sizes 1–24, plus hand-computed known-answer vectors.
- **Signatures** (`crypto/signing.py`). Ed25519 via the `cryptography` library:
  deterministic signatures, 32-byte public keys. Keys are hex-encoded; private keys
  are git-ignored and written with `0600` permissions.

## The verification protocol

Four independent checks, in increasing order of strength. A verifier runs as many
as it has inputs for; the result is "verified" iff every *performed* check passes.

| # | Check | Proves | Inputs needed |
|---|-------|--------|---------------|
| 1 | **Integrity** | the body has not been altered | the record alone |
| 2 | **Signature** | the result is attributable to a key | the record alone |
| 3 | **Inclusion** | the record is committed under a published root | the ledger + root |
| 4 | **Reproduction** | the outputs/scores follow from the inputs | the benchmark + a deterministic model |

```
$ verievals verify <record>.json --ledger ./ledger --benchmark benchmarks/arithmetic --model echo
Record:       56c7984e…
Integrity:    ok
Signature:    ok
Inclusion:    ok
Reproduction: ok
Overall:      VERIFIED          # exit code 0 (1 if not verified) — CI-gateable
```

Details: [`docs/verification.md`](docs/verification.md).

## Trust Score leaderboard

A plain leaderboard ranks by accuracy. A **trust-scored** leaderboard answers the
question the project exists for — *how much should you believe this number?* — by
assigning each entry the strongest verification tier that holds for it:

| Tier | Score | Earned when |
|------|:-----:|-------------|
| 🟢 `reproduced` | 1.00 | re-running the eval reproduced the exact signed body hash |
| 🔵 `verified` | 0.80 | valid signature **and** committed under the ledger root |
| 🟡 `signed` | 0.50 | valid signature, but not in the ledger |
| 🔴 `self_reported` | 0.20 | no valid signature — a bare claim |

Entries sort by **tier first**, then accuracy — a *verified* result with lower
accuracy outranks a *self-reported* one with a higher claimed number, by design.
This makes the gap between cryptographically-backed and self-reported results
explicit and rankable.

```
| # | Trust         | Score | Benchmark           | Model              | Accuracy | Tasks | Signer  |
|---|---------------|-------|---------------------|--------------------|----------|-------|---------|
| 1 | 🟢 reproduced | 1.00  | arithmetic@1.0.0    | mock:solver        | 1.000    | 15    | solver  |
| 2 | 🔵 verified   | 0.80  | gsm8k@sample-1.0.0  | ollama:gemma3:1b   | 0.917    | 12    | kaushik |
```

Details: [`docs/trust-score.md`](docs/trust-score.md).

## Determinism & the reproducibility model

Everything that can change a result lives in the hashed body: the benchmark tasks
(via their content hash), the model identity and decoding params, the scorer id,
the seed, and the sample limit.

- **Deterministic models** (`echo`, `fixture`) re-run bit-for-bit and earn the
  `reproduced` tier directly.
- **Non-deterministic models** (hosted APIs, local GPU inference) are *not*
  bit-reproducible across hardware/driver versions; the adapters report
  `deterministic = False`. The record still pins exactly what was requested, and the
  recommended pattern is to **capture a run's prompt→output pairs into a
  `FixtureModel`**, which makes that exact run replayable and verifiable offline by
  anyone, with no API key, server, or model download.

This capture-to-fixture pattern is what turns "we ran gemma3:1b and got 0.917" into
a claim a CI job can re-check (see the GSM8K MVP below).

## The logging SDK

For teams that already have an evaluation loop, the SDK provides verifiable
provenance without handing control to the runner. You wrap your loop and log each
item; on clean exit you get a signed `RunRecord` that is **byte-identical in
structure** to one the runner would produce for the same data (enforced by a test).

```python
from verievals.sdk import EvalRecorder

with EvalRecorder("gsm8k", "1.0", model_info, signing_key, scorer="gsm8k") as rec:
    for task in dataset:
        output = my_model(task.prompt)
        rec.log(task.id, task.prompt, output, expected=task.answer)
        # or, with your own grader:  rec.log(..., score=0.5, passed=False)

record = rec.record          # signed, ready to append to a ledger
```

A `@logged_eval(...)` decorator wraps a logging function and returns the finished
record. If the loop raises, the record is **not** finalized — partial runs never
produce a misleading signed artifact. Details: [`docs/sdk.md`](docs/sdk.md).

## Models, benchmarks, and scorers

**Model adapters** resolve from a spec string via `verievals.models.load_model`:

| Spec | Adapter | Notes |
|------|---------|-------|
| `echo` | `EchoModel` | deterministic; extracts the answer from the prompt — for plumbing/repro |
| `fixture:<path>` | `FixtureModel` | deterministic; replays recorded prompt→output pairs |
| `ollama[:<tag>]` | `OllamaAdapter` | local open models via Ollama; stdlib-only, no ML deps |
| `anthropic[:<model>]` | `AnthropicAdapter` | Claude via the Anthropic SDK (default `claude-opus-4-8`) |
| `openai[:<model>]` | `OpenAIAdapter` | OpenAI Chat Completions — lab-neutral by design |

**Bundled benchmarks** (each a directory of `benchmark.yaml` + `tasks.jsonl`):

| Benchmark | Scorer | Tasks | Demonstrates |
|-----------|--------|:-----:|--------------|
| `arithmetic` | `numeric` | 15 | numeric answer extraction |
| `capitals` | `exact_match` | 10 | normalized non-numeric matching |
| `gsm8k` | `gsm8k` | 12 | chain-of-thought, final-number extraction (sample subset) |

**Scorers** (deterministic, resolved by id so they are pinned in the record):
`exact_match` (case/whitespace-normalized), `regex_match`, `numeric` (first number,
tolerance), and `gsm8k` (final number — the chain-of-thought convention).

## GSM8K MVP: a locally-run open model, end to end

The milestone-1 MVP evaluates a small open-source model on grade-school math
**entirely on your own machine**, then makes the run independently re-verifiable.

- **Model:** any Ollama model via `--model ollama:<tag>`; defaults to **`gemma3:1b`**
  (~815 MB, runs in seconds on Apple Silicon, no download if pulled). Point it at
  `ollama:llama3:8b` or `ollama:deepseek-r1:7b` for stronger models.
- **Benchmark:** `benchmarks/gsm8k` — a 12-item GSM8K-style sample with integer
  answers (drop-in replaceable with the official split).
- **Scorer:** `gsm8k` (final-number extraction), tolerant of full chain-of-thought.

**Measured result (Apple M3, 16 GB):** `gemma3:1b` scored **11/12 (0.917)** on the
sample. The single miss is a genuine reasoning error by the 1B model, not a harness
issue. The exact outputs are captured into
`examples/fixtures/gsm8k_gemma3_1b.json`, and a CI test replays them offline to the
same 11/12 — so the local-model result is reproducible by anyone with no server and
no download.

```bash
ollama pull gemma3:1b
verievals run --benchmark benchmarks/gsm8k --model ollama:gemma3:1b \
    --key ./keys/runner.key --out ./records --signer me
python examples/run_gsm8k.py          # offline replay of the captured run
```

Details: [`docs/gsm8k-mvp.md`](docs/gsm8k-mvp.md).

## Command-line interface

| Command | Purpose |
|---------|---------|
| `verievals keygen --out <prefix>` | generate an Ed25519 keypair (`.key` private 0600, `.pub` public) |
| `verievals run --benchmark <dir> --model <spec> --key <file> --out <dir>` | run + emit a signed record |
| `verievals ledger --ledger <dir> append <record>` | verify & append a record to the Merkle log |
| `verievals ledger --ledger <dir> root` | print the current Merkle root |
| `verievals verify <record> [--ledger <dir>] [--benchmark <dir> --model <spec>]` | run the verification protocol |
| `verievals leaderboard --records <dir> --ledger <dir> [--trust]` | build an accuracy or trust-scored board |

Full reference: [`docs/cli.md`](docs/cli.md).

## Threat model

**Defends against:** result tampering (any edit changes the content hash and breaks
the signature), benchmark swapping (the tasks are content-hashed and reproduction
requires the matching benchmark), cherry-picked configs (decoding params, seed,
sampler, scorer are all in the hashed body), ledger back-dating (a record not under
the published root fails inclusion), and forged authorship (only the key holder can
sign).

**Explicit non-goals:** key-to-identity binding (we prove *a key* signed it, not
*who* owns the key — distribute trusted public keys out of band), hosted/GPU model
bit-reproducibility (use a captured fixture), benchmark *quality* (verifiability is
not validity), private-key custody, and ledger availability/consensus. Full
analysis: [`docs/threat-model.md`](docs/threat-model.md).

## Project layout

```
verifiable-evals/
├── src/verievals/              # the package (9 modules, see Architecture)
├── benchmarks/                 # bundled benchmark data (arithmetic, capitals, gsm8k)
├── examples/                   # end-to-end demos + captured fixtures
├── docs/                       # architecture, record-format, verification, sdk,
│                               #   trust-score, gsm8k-mvp, integration, releasing,
│                               #   threat-model, cli
├── tests/                      # mirrors the package; 204 tests, 97% coverage
├── .github/workflows/ci.yml    # lint + mypy + pytest matrix (py3.10–3.12)
├── pyproject.toml  Makefile  CHANGELOG.md  CONTRIBUTING.md  LICENSE
```

## Development

```bash
make install     # pip install -e ".[dev]"
make lint        # ruff check + format check
make type        # mypy (disallow_untyped_defs)
make test        # pytest
make cov         # pytest with coverage
make check       # lint + type + test
```

Standards enforced in CI (Python 3.10/3.11/3.12 matrix): `ruff` lint + format,
`mypy` with `disallow_untyped_defs`, and the full test suite. The package ships a
PEP 561 `py.typed` marker.

Publishing to PyPI (so `pip install verievals` works for everyone) is documented
step-by-step in [`docs/RELEASING.md`](docs/RELEASING.md).

## Project status

- **Stage:** working v0.1.0 — the cryptographic core, runner, ledger, verifier,
  SDK, trust leaderboard, CLI, and the GSM8K local-model MVP are complete and tested.
- **Tests:** 204 passing · **coverage:** 97% · `mypy` and `ruff` clean · wheel builds.
- **Three foundational milestones delivered:**
  1. **MVP for a single open-source model** — `gemma3:1b` on a GSM8K sample via
     Ollama, with a fixture for offline reproduction (`llama3:8b` is one flag away).
  2. **Open-source logging SDK** — `EvalRecorder` / `@logged_eval`, byte-identical to
     the runner's output.
  3. **Public Trust Score leaderboard** — verification-tiered ranking distinguishing
     cryptographically-backed from self-reported numbers.

## Roadmap

- Wire the **official full GSM8K split** (1,319 problems) behind the existing loader.
- A `transformers`/HuggingFace adapter for offline weights without a server.
- Publish a hosted, continuously-updated Trust Score board from a public ledger.
- Optional **L2 anchoring** of the Merkle root for external timestamping.
- Witness/co-signing and multi-party attestation of records.

## License

Apache 2.0 — see [LICENSE](LICENSE).
