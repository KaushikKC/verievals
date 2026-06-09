"""Tests for the RunRecord schema."""

from __future__ import annotations

import dataclasses

from verievals.crypto.signing import SigningKey
from verievals.records.schema import RunBody, RunRecord


def test_content_hash_is_stable(sample_body: RunBody) -> None:
    assert sample_body.content_hash() == sample_body.content_hash()


def test_content_hash_ignores_field_construction_order(sample_body: RunBody) -> None:
    rebuilt = RunBody.from_dict(sample_body.to_dict())
    assert rebuilt.content_hash() == sample_body.content_hash()


def test_create_produces_valid_signature(sample_body: RunBody, signing_key: SigningKey) -> None:
    record = RunRecord.create(sample_body, signing_key, signer="kaushik")
    assert record.verify_integrity()
    assert record.verify_signature()
    assert record.record_id == sample_body.content_hash()
    assert record.envelope.signer == "kaushik"


def test_signature_uses_correct_public_key(
    sample_body: RunBody, signing_key: SigningKey
) -> None:
    record = RunRecord.create(sample_body, signing_key)
    assert record.signature.public_key == signing_key.verify_key.hex
    assert record.signature.algorithm == "ed25519"


def test_tampering_with_body_breaks_integrity(
    sample_body: RunBody, signing_key: SigningKey
) -> None:
    record = RunRecord.create(sample_body, signing_key)
    tampered_results = list(record.body.results)
    tampered_results[1] = dataclasses.replace(tampered_results[1], score=1.0, passed=True)
    tampered_body = dataclasses.replace(record.body, results=tampered_results)
    tampered = dataclasses.replace(record, body=tampered_body)
    # Content hash no longer matches the (unchanged) stored hash.
    assert not tampered.verify_integrity()
    # And the signature must therefore not verify either.
    assert not tampered.verify_signature()


def test_envelope_does_not_affect_content_hash(
    sample_body: RunBody, signing_key: SigningKey
) -> None:
    record = RunRecord.create(sample_body, signing_key)
    moved = dataclasses.replace(
        record, envelope=dataclasses.replace(record.envelope, created_at="2000-01-01T00:00:00+00:00")
    )
    # Changing the timestamp must not change the content hash or break the signature.
    assert moved.content_hash == record.content_hash
    assert moved.verify_signature()


def test_record_dict_roundtrip(sample_body: RunBody, signing_key: SigningKey) -> None:
    record = RunRecord.create(sample_body, signing_key)
    restored = RunRecord.from_dict(record.to_dict())
    assert restored == record
    assert restored.verify_signature()


def test_wrong_signature_does_not_verify(sample_body: RunBody, signing_key: SigningKey) -> None:
    record = RunRecord.create(sample_body, signing_key)
    bad_sig = dataclasses.replace(record.signature, signature="00" * 64)
    bad = dataclasses.replace(record, signature=bad_sig)
    assert not bad.verify_signature()
