# Record format

A `RunRecord` is stored as a single JSON file named `<record_id>.json`, where
`record_id` is the body's content hash. The schema version is
`verievals/runrecord/v1`.

## Top-level shape

```json
{
  "body": { ... },          // deterministic, reproducible — hashed
  "content_hash": "<hex>",  // sha256 of canonical(body); also the record id
  "signature": { ... },     // Ed25519 over content_hash
  "envelope": { ... }       // timestamp + signer — NOT hashed
}
```

## `body`

```json
{
  "schema_version": "verievals/runrecord/v1",
  "verievals_version": "0.1.0",
  "benchmark": {
    "id": "arithmetic",
    "version": "1.0.0",
    "content_hash": "<hex of the benchmark's tasks+scorer>"
  },
  "model": {
    "provider": "anthropic",
    "name": "claude-opus-4-8",
    "version": "claude-opus-4-8",
    "params": {"max_tokens": 1024}
  },
  "runner": {"seed": 0, "sample_limit": null},
  "results": [
    {
      "task_id": "add-01",
      "prompt": "What is 7 + 5? Reply with only the number.",
      "output": "12",
      "expected": "12",
      "score": 1.0,
      "passed": true
    }
  ],
  "aggregate": {
    "scorer": "numeric",
    "num_tasks": 15,
    "metrics": {"accuracy": 1.0, "passed": 15.0}
  }
}
```

Every field in `body` affects the content hash. The full prompt and raw output
are stored verbatim for each task — this is the transparency the format exists
to provide.

## `content_hash`

`content_hash = sha256(canonical_json(body))`, lowercase hex. Canonical JSON
(see `verievals.crypto.canonical`) sorts object keys, omits insignificant
whitespace, emits UTF-8, and rejects `NaN`/`Infinity`, so the hash is a pure
function of the logical body.

## `signature`

```json
{
  "algorithm": "ed25519",
  "public_key": "<hex 32 bytes>",
  "signature": "<hex 64 bytes>"
}
```

The signature is over the **UTF-8 bytes of the `content_hash` hex string**.

## `envelope`

```json
{"created_at": "2026-06-10T13:46:00.157615+00:00", "signer": "kaushik"}
```

Changing the envelope never changes the content hash or invalidates the
signature — this is what allows the same logical run to be re-derived later with
a fresh timestamp.
