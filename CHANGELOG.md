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

[Unreleased]: https://github.com/kccreations1704/verifiable-evals/commits/main
