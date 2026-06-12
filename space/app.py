"""Verifiable Evals — a no-code 'verify a record' app for Hugging Face Spaces.

Paste a verievals run record (JSON) and click Verify. The app recomputes the
content hash and checks the Ed25519 signature — proving whether the record is
authentic and untampered. Edit any number in a valid record and re-verify to see
it fail: that is the whole point of verifiable evals.
"""

from __future__ import annotations

import json

import gradio as gr

from verievals.benchmarks.base import Benchmark, Task
from verievals.crypto.signing import generate_signing_key
from verievals.models.echo import EchoModel
from verievals.records.schema import RunRecord
from verievals.runner.engine import run_eval


def make_example() -> str:
    """Generate a fresh, valid signed record to paste into the box."""
    benchmark = Benchmark(
        id="demo",
        version="1.0",
        scorer="numeric",
        tasks=[Task(id="t1", prompt="What is 2 + 2? Answer: 4", expected="4")],
    )
    record = run_eval(benchmark, EchoModel(), signing_key=generate_signing_key(), signer="demo")
    return json.dumps(record.to_dict(), indent=2)


def verify(text: str) -> str:
    if not text.strip():
        return "Paste a record JSON, or click **Load a sample record**."
    try:
        record = RunRecord.from_dict(json.loads(text))
    except Exception as exc:  # noqa: BLE001 - surface any parse error to the user
        return f"❌ Could not parse this as a verievals record:\n\n{exc}"

    integrity = record.verify_integrity()
    signature = record.verify_signature()
    ok = integrity and signature

    body = record.body
    verdict = (
        "## ✅ VERIFIED\nThis record is authentic and untampered."
        if ok
        else "## ❌ NOT VERIFIED\nThe record was altered, or the signature is invalid."
    )
    return "\n".join(
        [
            verdict,
            "",
            f"- **Record id:** `{record.record_id[:24]}…`",
            f"- **Benchmark:** {body.benchmark.id}@{body.benchmark.version}",
            f"- **Model:** {body.model.provider}:{body.model.name}",
            f"- **Accuracy:** {body.aggregate.metrics.get('accuracy', 0.0):.3f}",
            "",
            f"- Integrity (content hash matches body): {'✅ ok' if integrity else '❌ FAIL'}",
            f"- Signature (Ed25519): {'✅ ok' if signature else '❌ FAIL'}",
        ]
    )


with gr.Blocks(title="Verifiable Evals") as demo:
    gr.Markdown(
        "# 🔏 Verifiable Evals — verify an eval record\n"
        "Paste a `verievals` run record below and click **Verify**. "
        "Try editing a score in a valid record and re-verifying — it will fail. "
        "Learn more: [GitHub](https://github.com/KaushikKC/verievals) · "
        "[PyPI](https://pypi.org/project/verievals/)."
    )
    with gr.Row():
        with gr.Column():
            record_box = gr.Code(label="Record JSON", language="json", lines=20)
            with gr.Row():
                load_btn = gr.Button("Load a sample record")
                verify_btn = gr.Button("Verify", variant="primary")
        result = gr.Markdown(label="Result")

    load_btn.click(make_example, outputs=record_box)
    verify_btn.click(verify, inputs=record_box, outputs=result)


if __name__ == "__main__":
    demo.launch()
