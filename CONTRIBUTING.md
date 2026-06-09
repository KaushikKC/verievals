# Contributing to Verifiable Evals

Thanks for your interest in making AI evaluations more verifiable!

## Principles

1. **Determinism first.** Anything that affects an eval result must be captured in
   the `RunRecord`. If a change makes runs less reproducible, it needs a very good
   reason and explicit documentation.
2. **The evidence is the artifact.** Features should make records easier to produce,
   sign, store, and independently verify.
3. **No private keys in the repo.** Signing keys are generated locally and ignored by
   git. Never commit a `*.key` or `*.pem`.

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Workflow

```bash
make lint     # ruff + mypy
make test     # pytest with coverage
make check    # lint + test
```

- Write tests for any new behaviour, especially in `crypto/` and `ledger/` where
  correctness is security-critical.
- Keep functions typed; `mypy` runs in CI with `disallow_untyped_defs`.
- Follow Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`,
  `chore:`) and keep commits small and focused.

## Reporting verification failures

If you can reproduce a leaderboard entry that does **not** verify, please open an
issue with the `RunRecord`, the published Merkle root, and the verifier output. These
reports are the whole point of the project.
