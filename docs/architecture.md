# Architecture

Verifiable Evals turns an eval run into a **signed, content-addressed,
Merkle-anchored artifact**. The design goal is singular: anyone, with only the
published artifacts, can independently confirm a leaderboard entry — and re-run
it when the model is deterministic.

## Module map

```
verievals
├── crypto      canonical JSON · sha256 content addressing · RFC 6962 Merkle · Ed25519
├── records     RunRecord schema (body / envelope / signature) · filesystem store
├── models      adapter interface · echo + fixture (deterministic) · Anthropic + OpenAI (live)
├── benchmarks  Benchmark/Task models (+ content hash) · yaml+jsonl loader
├── scoring     exact-match · regex · numeric · registry
├── runner      deterministic eval engine -> signed RunRecord
├── ledger      append-only Merkle log · verification protocol
├── leaderboard ranked board from ledger-included, signature-checked records
└── cli         keygen · run · ledger · verify · leaderboard
```

Dependencies flow downward only: `crypto` depends on nothing internal;
`records` depends on `crypto`; `runner` depends on `benchmarks`, `models`,
`scoring`, `records`; `ledger` depends on `runner` + `records` + `crypto`;
`leaderboard` and `cli` sit on top. There are no cycles.

## The central artifact: `RunRecord`

A record splits cleanly into:

- **body** — the deterministic, reproducible payload: benchmark identity (with
  content hash), model identity + decoding params, runner config (seed, sample
  limit), every task's prompt/output/expected/score, and aggregate metrics. The
  body's canonical SHA-256 is the record id and the Merkle leaf.
- **envelope** — non-deterministic metadata (wall-clock timestamp, optional
  signer label) deliberately excluded from the hash.
- **signature** — an Ed25519 signature over the content hash.

This split is what lets a record be both *signable* and *reproducible*:
re-running the body yields the same content hash regardless of when or by whom.

See [record-format.md](record-format.md) for the full schema and
[verification.md](verification.md) for the protocol.

## Determinism contract

Anything that can change a result lives in the body and is hashed:

- benchmark tasks (via `BenchmarkSpec.content_hash`),
- model identity and decoding params,
- the scorer id,
- the seed and sample limit.

Deterministic models (`echo`, `fixture`) re-run bit-for-bit. Live API models
(`anthropic`, `openai`) are not bit-reproducible; the record still pins exactly
what was requested, and the recommended pattern is to capture a live run's
prompt→output pairs into a `FixtureModel` so the eval becomes offline-verifiable.

## Why RFC 6962 Merkle

The ledger uses the Certificate Transparency Merkle construction: domain-
separated leaf (`0x00`) and node (`0x01`) hashing, and the split-at-largest-
power-of-two tree shape. This is widely reviewed and avoids the second-preimage
weakness of naive "duplicate the last leaf" trees. The root is a single 32-byte
hash that commits to every record; publish it anywhere (README, tag, tweet, or
an L2 anchor) and inclusion proofs do the rest.
