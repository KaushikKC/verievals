"""Tests for the RFC 6962-style Merkle tree."""

from __future__ import annotations

import hashlib
import os

import pytest

from verievals.crypto.merkle import (
    InclusionProof,
    merkle_proof,
    merkle_root,
    verify_inclusion_proof,
)


def _leaf(data: bytes) -> bytes:
    return hashlib.sha256(b"\x00" + data).digest()


def _node(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(b"\x01" + left + right).digest()


# --- Known-answer tests (hand-computed against the spec) -----------------------


def test_empty_tree_is_sha256_of_empty_string() -> None:
    assert merkle_root([]) == hashlib.sha256(b"").hexdigest()


def test_single_leaf_root() -> None:
    assert merkle_root([b""]) == _leaf(b"").hex()


def test_two_leaf_root() -> None:
    d0, d1 = b"a", b"b"
    expected = _node(_leaf(d0), _leaf(d1)).hex()
    assert merkle_root([d0, d1]) == expected


def test_three_leaf_root_splits_at_power_of_two() -> None:
    d0, d1, d2 = b"a", b"b", b"c"
    # k = 2  ->  node( node(L0,L1), L2 )
    expected = _node(_node(_leaf(d0), _leaf(d1)), _leaf(d2)).hex()
    assert merkle_root([d0, d1, d2]) == expected


# --- Property tests ------------------------------------------------------------


@pytest.mark.parametrize("n", list(range(1, 25)))
def test_every_leaf_has_a_valid_inclusion_proof(n: int) -> None:
    leaves = [os.urandom(16) for _ in range(n)]
    root = merkle_root(leaves)
    for i in range(n):
        proof = merkle_proof(leaves, i)
        assert proof.leaf_index == i
        assert proof.tree_size == n
        assert verify_inclusion_proof(leaves[i], proof, root)


@pytest.mark.parametrize("n", [1, 2, 5, 8, 13])
def test_tampered_leaf_fails_verification(n: int) -> None:
    leaves = [os.urandom(16) for _ in range(n)]
    root = merkle_root(leaves)
    proof = merkle_proof(leaves, 0)
    tampered = bytes([leaves[0][0] ^ 0xFF]) + leaves[0][1:]
    assert not verify_inclusion_proof(tampered, proof, root)


def test_wrong_root_fails_verification() -> None:
    leaves = [os.urandom(16) for _ in range(7)]
    proof = merkle_proof(leaves, 3)
    assert not verify_inclusion_proof(leaves[3], proof, "00" * 32)


def test_proof_against_wrong_index_fails() -> None:
    leaves = [os.urandom(16) for _ in range(6)]
    root = merkle_root(leaves)
    proof = merkle_proof(leaves, 2)
    # Verifying leaf at index 4 with a proof built for index 2 must fail.
    assert not verify_inclusion_proof(leaves[4], proof, root)


def test_out_of_range_index_raises() -> None:
    leaves = [os.urandom(16) for _ in range(3)]
    with pytest.raises(IndexError):
        merkle_proof(leaves, 3)


def test_root_is_deterministic() -> None:
    leaves = [os.urandom(16) for _ in range(10)]
    assert merkle_root(leaves) == merkle_root(leaves)


def test_hex_string_leaves_match_bytes_leaves() -> None:
    raw = [os.urandom(32) for _ in range(5)]
    hexed = [b.hex() for b in raw]
    assert merkle_root(raw) == merkle_root(hexed)


def test_inclusion_proof_dict_roundtrip() -> None:
    leaves = [os.urandom(16) for _ in range(9)]
    proof = merkle_proof(leaves, 4)
    restored = InclusionProof.from_dict(proof.to_dict())
    assert restored == proof
    assert verify_inclusion_proof(leaves[4], restored, merkle_root(leaves))
