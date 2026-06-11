"""The ``verievals`` command-line entry point.

Subcommands:

* ``keygen``      -- generate an Ed25519 signing keypair.
* ``run``         -- run a benchmark against a model and emit a signed record.
* ``ledger``      -- ``append`` a record or print the current Merkle ``root``.
* ``verify``      -- verify a record (integrity, signature, inclusion, reproduction).
* ``leaderboard`` -- build a verifiable leaderboard from records + a ledger.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from verievals.benchmarks.loader import load_benchmark
from verievals.cli import keys
from verievals.leaderboard.builder import build_leaderboard
from verievals.leaderboard.trust import build_trust_leaderboard
from verievals.ledger.merkle_log import MerkleLog
from verievals.ledger.verifier import verify_record
from verievals.models.registry import load_model
from verievals.records.store import RecordStore
from verievals.runner.config import RunConfig
from verievals.runner.engine import run_eval
from verievals.version import __version__


def _cmd_keygen(args: argparse.Namespace) -> int:
    key, private_path, public_path = keys.generate_and_save(args.out)
    print(f"Wrote private key: {private_path} (keep secret)")
    print(f"Wrote public key:  {public_path}")
    print(f"Public key: {key.verify_key.hex}")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    benchmark = load_benchmark(args.benchmark)
    model = load_model(args.model)
    signing_key = keys.load_signing_key(args.key)
    config = RunConfig(seed=args.seed, sample_limit=args.limit, scorer=args.scorer)

    record = run_eval(benchmark, model, config=config, signing_key=signing_key, signer=args.signer)
    path = RecordStore(args.out).save(record)

    accuracy = record.body.aggregate.metrics.get("accuracy", 0.0)
    print(f"Record id:  {record.record_id}")
    print(f"Benchmark:  {benchmark.id}@{benchmark.version} ({len(record.body.results)} tasks)")
    print(f"Model:      {record.body.model.provider}:{record.body.model.name}")
    print(f"Accuracy:   {accuracy:.3f}")
    print(f"Saved to:   {path}")
    return 0


def _cmd_ledger(args: argparse.Namespace) -> int:
    ledger = MerkleLog(args.ledger)
    if args.ledger_command == "append":
        record = RecordStore.load_path(args.record)
        proof = ledger.append(record)
        print(f"Appended {record.record_id} at index {proof.leaf_index}")
        print(f"Tree size:   {proof.tree_size}")
        print(f"Merkle root: {ledger.root()}")
        return 0
    if args.ledger_command == "root":
        print(ledger.root())
        print(f"(size: {ledger.size()})", file=sys.stderr)
        return 0
    raise AssertionError("unreachable")  # pragma: no cover


def _cmd_verify(args: argparse.Namespace) -> int:
    record = RecordStore.load_path(args.record)
    ledger = MerkleLog(args.ledger) if args.ledger else None
    benchmark = load_benchmark(args.benchmark) if args.benchmark else None
    model = load_model(args.model) if args.model else None

    result = verify_record(record, ledger=ledger, benchmark=benchmark, model=model)

    def fmt(value: bool | None) -> str:
        if value is None:
            return "skipped"
        return "ok" if value else "FAIL"

    print(f"Record:       {result.record_id}")
    print(f"Integrity:    {fmt(result.integrity_ok)}")
    print(f"Signature:    {fmt(result.signature_ok)}")
    print(f"Inclusion:    {fmt(result.inclusion_ok)}")
    print(f"Reproduction: {fmt(result.reproduced_ok)}")
    for note in result.notes:
        print(f"  note: {note}")
    print(f"Overall:      {'VERIFIED' if result.ok else 'NOT VERIFIED'}")
    return 0 if result.ok else 1


def _cmd_leaderboard(args: argparse.Namespace) -> int:
    store = RecordStore(args.records)
    ledger = MerkleLog(args.ledger)
    if args.trust:
        reproducers = {}
        if args.reproduce_benchmark and args.reproduce_model:
            bench = load_benchmark(args.reproduce_benchmark)
            reproducers[bench.id] = (bench, load_model(args.reproduce_model))
        board: object = build_trust_leaderboard(
            store, ledger, reproducers=reproducers, benchmark_id=args.benchmark
        )
    else:
        board = build_leaderboard(store, ledger, benchmark_id=args.benchmark)
    markdown = board.render_markdown()  # type: ignore[attr-defined]
    entry_count = len(board.entries)  # type: ignore[attr-defined]
    if args.out:
        from pathlib import Path

        Path(args.out).write_text(markdown, encoding="utf-8")
        print(f"Wrote leaderboard ({entry_count} entries) to {args.out}")
    else:
        print(markdown, end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="verievals", description=__doc__)
    parser.add_argument("--version", action="version", version=f"verievals {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_keygen = sub.add_parser("keygen", help="generate an Ed25519 signing keypair")
    p_keygen.add_argument("--out", required=True, help="output path prefix (writes .key and .pub)")
    p_keygen.set_defaults(func=_cmd_keygen)

    p_run = sub.add_parser("run", help="run a benchmark and emit a signed record")
    p_run.add_argument("--benchmark", required=True, help="benchmark directory")
    p_run.add_argument(
        "--model", required=True, help="model spec (e.g. echo, anthropic:claude-opus-4-8)"
    )
    p_run.add_argument("--key", required=True, help="signing key file (.key)")
    p_run.add_argument("--out", default="./records", help="record store directory")
    p_run.add_argument("--limit", type=int, default=None, help="evaluate only the first N tasks")
    p_run.add_argument("--scorer", default=None, help="override the benchmark's default scorer")
    p_run.add_argument("--seed", type=int, default=0, help="random seed (recorded)")
    p_run.add_argument("--signer", default=None, help="optional signer label")
    p_run.set_defaults(func=_cmd_run)

    p_ledger = sub.add_parser("ledger", help="manage the public Merkle ledger")
    p_ledger.add_argument("--ledger", required=True, help="ledger directory")
    ledger_sub = p_ledger.add_subparsers(dest="ledger_command", required=True)
    p_append = ledger_sub.add_parser("append", help="append a record to the ledger")
    p_append.add_argument("record", help="path to a record JSON file")
    ledger_sub.add_parser("root", help="print the current Merkle root")
    p_ledger.set_defaults(func=_cmd_ledger)

    p_verify = sub.add_parser("verify", help="verify a record")
    p_verify.add_argument("record", help="path to a record JSON file")
    p_verify.add_argument("--ledger", default=None, help="ledger directory (checks inclusion)")
    p_verify.add_argument("--benchmark", default=None, help="benchmark dir (enables reproduction)")
    p_verify.add_argument("--model", default=None, help="model spec (enables reproduction)")
    p_verify.set_defaults(func=_cmd_verify)

    p_board = sub.add_parser("leaderboard", help="build a verifiable leaderboard")
    p_board.add_argument("--records", required=True, help="record store directory")
    p_board.add_argument("--ledger", required=True, help="ledger directory")
    p_board.add_argument("--benchmark", default=None, help="filter to a benchmark id")
    p_board.add_argument("--out", default=None, help="write markdown to a file instead of stdout")
    p_board.add_argument(
        "--trust",
        action="store_true",
        help="render the trust-scored board (reproduced/verified/signed/self-reported)",
    )
    p_board.add_argument(
        "--reproduce-benchmark",
        default=None,
        help="benchmark dir to enable the 'reproduced' trust tier (with --trust)",
    )
    p_board.add_argument(
        "--reproduce-model",
        default=None,
        help="model spec to enable the 'reproduced' trust tier (with --trust)",
    )
    p_board.set_defaults(func=_cmd_leaderboard)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
