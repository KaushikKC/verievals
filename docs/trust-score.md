# Trust Score leaderboard

A normal leaderboard ranks by accuracy. A **trust-scored** leaderboard answers
the question this whole project exists for: *how much should you believe this
number?* It makes the gap between cryptographically-backed and self-reported
results explicit and rankable.

## Tiers

Each entry is assigned the strongest tier that holds for it:

| Tier | Score | Earned when |
|------|-------|-------------|
| 🟢 `reproduced` | 1.00 | Re-running the eval reproduced the exact signed body hash |
| 🔵 `verified` | 0.80 | Valid signature **and** committed under the ledger root |
| 🟡 `signed` | 0.50 | Valid signature, but not in the ledger |
| 🔴 `self_reported` | 0.20 | No valid signature — a bare claim |

Entries are sorted by tier first, then accuracy, then record id. A *verified*
result with lower accuracy outranks a *self-reported* one with higher claimed
accuracy — trust dominates the headline number, by design.

## CLI

```bash
# Trust board (reproduction tier not attempted):
verievals leaderboard --records ./records --ledger ./ledger --trust

# Enable the 'reproduced' tier for a deterministic benchmark/model:
verievals leaderboard --records ./records --ledger ./ledger --trust \
    --reproduce-benchmark benchmarks/arithmetic \
    --reproduce-model fixture:examples/fixtures/arithmetic_solver.json
```

Example output:

```
| # | Trust | Score | Benchmark | Model | Accuracy | Tasks | Signer | Record |
|---|-------|-------|-----------|-------|----------|-------|--------|--------|
| 1 | 🟢 reproduced | 1.00 | arithmetic@1.0.0 | mock:arithmetic-solver | 1.000 | 15 | solver | `276d38cff88c…` |
| 2 | 🔵 verified    | 0.80 | arithmetic@1.0.0 | mock:echo              | 0.000 | 15 | echo   | `56c7984e5b5a…` |
```

## Programmatic

```python
from verievals.leaderboard.trust import build_trust_leaderboard

board = build_trust_leaderboard(
    store, ledger,
    reproducers={"arithmetic": (benchmark, model)},  # optional, enables 🟢
)
print(board.render_markdown())
```
