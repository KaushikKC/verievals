# Verify eval records in CI (GitHub Action)

A reusable composite action that **fails your CI job if an eval record doesn't
verify**. Use it to gate merges/releases on cryptographically-verified results.

## Usage

Add a step to any workflow:

```yaml
name: Verify evals
on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: KaushikKC/verievals/.github/actions/verify@main
        with:
          record: "records/*.json"     # path or glob to your record(s)
          ledger: "ledger"             # optional: checks Merkle inclusion
          benchmark: "benchmarks/gsm8k" # optional: enables reproduction
          model: "echo"                #   (with a deterministic model)
```

Pin to a released version for stability:

```yaml
      - uses: KaushikKC/verievals/.github/actions/verify@v0.1.0
        with:
          record: "records/*.json"
          version: "0.1.0"            # exact verievals version to install
```

## Inputs

| Input | Required | Description |
|-------|:--------:|-------------|
| `record` | ✅ | Path or glob to the record JSON file(s). |
| `ledger` | — | Ledger directory; enables the Merkle inclusion check. |
| `benchmark` | — | Benchmark directory; enables reproduction (with `model`). |
| `model` | — | Model spec (e.g. `echo`); enables reproduction. |
| `version` | — | `verievals` version to install from PyPI (default: latest). |
| `python-version` | — | Python version (default: `3.12`). |

## Behavior

- Installs `verievals` from PyPI, then runs `verievals verify` on each matched
  record. Any non-verifying record (exit code 1) **fails the job**.
- With no `ledger`/`benchmark`/`model`, it still checks **integrity + signature**.
- Add `ledger` to also check **Merkle inclusion**; add `benchmark` + a
  deterministic `model` to also check **reproduction**.

## Typical pattern

1. A job runs your eval and commits/produces the record + ledger root.
2. This action verifies it on every push/PR.
3. A green check means the published number is backed by a verifiable record —
   not a self-reported claim.

This repo dogfoods the action in
[`.github/workflows/verify-demo.yml`](../.github/workflows/verify-demo.yml).
