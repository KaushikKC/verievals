# Verification protocol

Verification has four independent checks, in increasing order of strength. A
verifier runs as many as it has inputs for; `VerificationResult.ok` is true iff
every check that *was performed* passed.

## 1. Integrity

Recompute `sha256(canonical_json(body))` and compare to the stored
`content_hash`. This catches any tampering with the body (a flipped score, an
edited output, an added task).

```python
record.verify_integrity()
```

## 2. Signature

Verify the Ed25519 signature over the content hash against the embedded public
key. Integrity is checked first, so a valid signature attests to the exact body.

```python
record.verify_signature()
```

> The signature binds the *result* to a *key*, not to an identity. Trust in the
> public key itself is out of scope: publish keys you trust (a lab's key, a
> reviewer's key) the way you'd publish any other public key.

## 3. Merkle inclusion

Given a ledger and a published root, fetch the record's inclusion proof and
verify it reconstructs the root (RFC 6962 audit-path verification). This proves
the record is one of the set the root commits to — it can't be silently swapped
or back-dated after the root is published.

```python
verify_inclusion_proof(record.content_hash, proof, published_root)
```

## 4. Reproduction (deterministic models only)

Re-run the eval using the config recorded in the body (seed, sample limit,
scorer) and the same benchmark, and confirm the re-run's body content hash
matches. This is the strongest check: it proves the reported outputs and scores
actually follow from running the model on the prompts.

```python
reproduce_record(record, benchmark, model)  # True iff body hash matches
```

Reproduction requires a deterministic model. For a hosted model, capture its
prompt→output pairs into a `FixtureModel` and reproduce against that.

## One command

```bash
verievals verify <record>.json \
    --ledger ./ledger \          # enables inclusion
    --benchmark benchmarks/arithmetic \  # } enable
    --model echo                 #          } reproduction
```

Output:

```
Record:       56c7984e…
Integrity:    ok
Signature:    ok
Inclusion:    ok
Reproduction: ok
Overall:      VERIFIED
```

Exit code is `0` when verified, `1` otherwise — suitable for CI gating.
