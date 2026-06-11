# Examples

## `run_arithmetic.py`

A fully offline, deterministic walkthrough of the whole system:

```bash
python examples/run_arithmetic.py
```

It runs the bundled `arithmetic` benchmark with two deterministic models, signs
each run, appends both to a Merkle ledger, verifies one with full reproduction,
and prints a leaderboard — no API keys required.

## `fixtures/arithmetic_solver.json`

A `FixtureModel` definition mapping each arithmetic prompt to its correct
answer. It demonstrates the pattern for making any model's run **reproducible**:
capture its prompt → output pairs into a fixture so anyone can re-run and verify
the eval offline, even for a non-deterministic hosted model.

## Running a real Claude model

```bash
pip install "verievals[anthropic]"
export ANTHROPIC_API_KEY=sk-ant-...
verievals keygen --out ./keys/runner
verievals run \
    --benchmark benchmarks/arithmetic \
    --model anthropic:claude-opus-4-8 \
    --key ./keys/runner.key \
    --out ./records \
    --signer "your-name"
```

The resulting record captures the exact model id, prompts, outputs, and scores.
Append it to a ledger and publish the root so others can verify the entry.
