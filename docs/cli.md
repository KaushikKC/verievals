# CLI reference

All commands are subcommands of `verievals`. Run `verievals <cmd> --help` for
the authoritative flag list.

## `keygen`

Generate an Ed25519 signing keypair.

```bash
verievals keygen --out ./keys/runner
# writes ./keys/runner.key (private, 0600) and ./keys/runner.pub (public)
```

## `run`

Run a benchmark against a model and emit a signed record.

```bash
verievals run \
    --benchmark benchmarks/arithmetic \
    --model echo \
    --key ./keys/runner.key \
    --out ./records \
    [--limit N] [--scorer ID] [--seed N] [--signer NAME]
```

| Flag | Meaning |
|------|---------|
| `--benchmark` | benchmark directory (with `benchmark.yaml` + `tasks.jsonl`) |
| `--model` | model spec: `echo`, `fixture:<path>`, `anthropic[:<model>]`, `openai[:<model>]` |
| `--key` | signing key file (`.key`) |
| `--out` | record store directory (default `./records`) |
| `--limit` | evaluate only the first N tasks |
| `--scorer` | override the benchmark's default scorer |
| `--seed` | random seed (recorded for reproducibility) |
| `--signer` | optional human-readable signer label |

## `ledger`

Manage the append-only Merkle ledger. `--ledger` precedes the subcommand.

```bash
verievals ledger --ledger ./ledger append ./records/<id>.json
verievals ledger --ledger ./ledger root          # prints the current root
```

`append` verifies the record's signature before committing it, so the ledger
never includes a record that doesn't verify on its own.

## `verify`

Run the verification protocol. Exit code `0` = verified, `1` = not verified.

```bash
verievals verify ./records/<id>.json \
    [--ledger ./ledger] \           # adds Merkle inclusion
    [--benchmark benchmarks/arithmetic --model echo]   # adds reproduction
```

## `leaderboard`

Build a verifiable leaderboard from records committed to a ledger.

```bash
verievals leaderboard --records ./records --ledger ./ledger \
    [--benchmark arithmetic] [--out leaderboard.md]
```

Only records whose signature verifies *and* whose Merkle inclusion checks out
appear on the board, sorted by accuracy descending.
