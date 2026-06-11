# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project scaffolding: packaging, license, contributor guide, CI.
- `crypto` module: canonical JSON, SHA-256 content addressing, Merkle tree with
  inclusion proofs, Ed25519 signing/verification.
- `records` module: signed `RunRecord` schema and append-only record store.
- `models` module: adapter interface with deterministic `echo`, Anthropic, and
  OpenAI adapters.
- `benchmarks` module: benchmark/task loaders and built-in benchmarks.
- `scoring` module: exact-match, regex, and numeric scorers.
- `runner` module: deterministic evaluation engine.
- `ledger` module: append-only Merkle log and re-run verifier.
- `leaderboard` module: verifiable leaderboard builder.
- `cli`: `keygen`, `run`, `verify`, `ledger`, and `leaderboard` commands.
- Bundled benchmarks: `arithmetic` (numeric scoring) and `capitals`
  (exact-match scoring).
- End-to-end example (`examples/run_arithmetic.py`) and a deterministic solver
  fixture.
- Documentation: architecture, record format, verification protocol, threat
  model, and CLI reference.
- PEP 561 `py.typed` marker so downstream users get the shipped type hints.
- `sdk` module: `EvalRecorder` context manager and `@logged_eval` decorator to
  emit signed records from inside existing eval loops (byte-identical to the
  runner's output for the same data).
- Trust-scored leaderboard (`leaderboard.trust`, `leaderboard --trust`): ranks
  entries by verification strength (reproduced / verified / signed /
  self-reported), making the gap between cryptographically-backed and
  self-reported numbers explicit.

[Unreleased]: https://github.com/kccreations1704/verifiable-evals/commits/main
