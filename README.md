# Verifiable Evals (`verievals`)

> Every eval run produces a signed, reproducible record — model version, prompts,
> outputs, scores, seed, and config — appended to a public Merkle log. Anyone can
> re-run and **cryptographically verify** any leaderboard entry.

[![CI](https://github.com/kccreations1704/verifiable-evals/actions/workflows/ci.yml/badge.svg)](https://github.com/kccreations1704/verifiable-evals/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

---

## Why this exists

AI evaluations today are frequently **not transparent, accessible, or verifiable**.
When labs report benchmark numbers it is often impossible to know the exact prompts,
decoding parameters, model version, or scoring rules that produced them — so results
can't be reproduced and competing labs publish conflicting numbers for the *same*
benchmark.

`verievals` answers that problem directly. It is a benchmark runner where **the
evidence is the artifact**:

- Each run is captured as a **canonical, content-addressed `RunRecord`** containing
  the model identity, every prompt, every raw output, the scorer, per-task scores,
  the random seed, and the full run config.
- Each record is **signed with Ed25519** by the party that ran it.
- Each record's content hash is **appended to an append-only Merkle log**, yielding a
  compact **inclusion proof** and a single root hash that commits to all results.
- A **verifier** can re-run the exact eval and confirm the outputs/scores match the
  signed record, and confirm the record is included under a published root.

> No blockchain required. The Merkle root is small enough to publish anywhere
> (a README, a tweet, a git tag). An optional L2 anchor can be added later.

## Quickstart

```bash
pip install -e ".[dev]"

# 1. Generate a signing keypair (private key stays local)
verievals keygen --out ./keys/runner

# 2. Run a benchmark deterministically and emit a signed record
verievals run \
    --benchmark benchmarks/arithmetic \
    --model echo \
    --key ./keys/runner.key \
    --out ./records

# 3. Append the record to the public Merkle ledger
verievals ledger append ./records/<record-id>.json --ledger ./ledger

# 4. Anyone can verify the record reproduces and is included under the root
verievals verify ./records/<record-id>.json --ledger ./ledger
```

## How verification works

```
prompts + config + seed ──▶ model ──▶ outputs ──▶ scorer ──▶ scores
        │                                                       │
        └──────────────── canonical RunRecord ──────────────────┘
                                  │
                       sha256 (content address)
                                  │
                 Ed25519 signature   +   Merkle leaf
                                  │
                          published root
```

Verification re-derives the content hash from the record, checks the Ed25519
signature against the signer's public key, checks the Merkle inclusion proof against
the published root, and (optionally) **re-runs** the eval to confirm bit-for-bit
reproducibility of outputs and scores.

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — system design and module map
- [`docs/record-format.md`](docs/record-format.md) — the `RunRecord` schema
- [`docs/verification.md`](docs/verification.md) — the verification protocol
- [`docs/sdk.md`](docs/sdk.md) — the logging SDK (`EvalRecorder` / `@logged_eval`)
- [`docs/trust-score.md`](docs/trust-score.md) — the trust-scored leaderboard
- [`docs/threat-model.md`](docs/threat-model.md) — goals and explicit non-goals
- [`docs/cli.md`](docs/cli.md) — command-line reference
- [`examples/`](examples/) — a fully offline end-to-end demo
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to contribute

## Bundled benchmarks

- `benchmarks/arithmetic` — integer arithmetic, numeric scorer (15 tasks)
- `benchmarks/capitals` — world capitals, exact-match scorer (10 tasks)

## License

Apache 2.0 — see [LICENSE](LICENSE).
