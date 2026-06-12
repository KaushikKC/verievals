---
title: Verifiable Evals
emoji: 🔏
colorFrom: green
colorTo: blue
sdk: gradio
app_file: app.py
pinned: false
license: apache-2.0
---

# Verifiable Evals — verify an eval record

A no-code app: paste a [`verievals`](https://pypi.org/project/verievals/) run
record (JSON) and click **Verify**. It recomputes the content hash and checks the
Ed25519 signature to prove whether the record is authentic and untampered.

Click **Load a sample record** to get a valid one, verify it (✅), then edit any
number and verify again (❌) — that demonstrates tamper-evidence.

- Code & docs: <https://github.com/KaushikKC/verievals>
- Demo video: <https://youtu.be/RoJX8_gD_iI>

## Running locally

```bash
pip install -r requirements.txt
python app.py
```
