# Threat model

What verifiable evals defends against, and what it explicitly does not.

## Goals

| # | Property | Mechanism |
|---|----------|-----------|
| G1 | A published result cannot be silently altered | Content-addressing: any change to the body changes the record id |
| G2 | A result is attributable to a key | Ed25519 signature over the content hash |
| G3 | A result cannot be back-dated into a published set | Merkle inclusion under a published root |
| G4 | Reported outputs/scores follow from the inputs | Re-run reproduction (deterministic models) |
| G5 | The benchmark itself is pinned | `BenchmarkSpec.content_hash` over tasks + scorer |

## In scope (attacks defended)

- **Result tampering.** Editing any score, output, prompt, or metric changes the
  content hash, breaking both integrity and the signature (G1, G2).
- **Benchmark swap.** Claiming a score on benchmark X while having run an easier
  variant: the body pins the benchmark content hash, and reproduction requires
  the matching benchmark (G5, G4).
- **Cherry-picked configs.** Decoding params, seed, sample limit, and scorer are
  all in the hashed body, so "we used a different temperature" is visible.
- **Ledger back-dating.** Once a root is published, a record not committed under
  it fails the inclusion check (G3).
- **Forged authorship.** A result can only be signed by the holder of the
  private key (G2).

## Out of scope (explicit non-goals)

- **Key trust / identity binding.** We prove a result was signed by *a* key, not
  that the key belongs to a specific lab. Distribute and trust public keys out of
  band, as with any PKI.
- **Hosted-model non-determinism.** API models aren't bit-reproducible. The record
  pins what was requested; bit-for-bit reproduction needs a deterministic model or
  a captured fixture. Drift between a re-run and the record is surfaced, not hidden.
- **Prompt/benchmark quality.** Verifiability says nothing about whether a
  benchmark measures something meaningful — only that the reported run is faithful
  to its stated inputs.
- **Private-key custody.** Generating, storing, and rotating signing keys is the
  operator's responsibility. Private keys are git-ignored and written `0600`, but
  the system cannot prevent a leaked key from signing.
- **Availability of the ledger.** This is an append-only log, not a consensus
  system. Publishing and preserving the root (and optionally anchoring it to an
  external timestamp/L2) is an operational concern.

## Notes on the Merkle construction

The RFC 6962 leaf/node domain separation (`0x00` / `0x01` prefixes) prevents
second-preimage attacks where an internal node is presented as a leaf. The tree
shape (split at the largest power of two) is fully specified, so independent
implementations compute identical roots and proofs.
