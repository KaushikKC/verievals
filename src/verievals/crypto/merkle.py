"""An RFC 6962-style Merkle tree with inclusion (audit) proofs.

We use the same construction as Certificate Transparency (RFC 6962) because it
is well specified, widely reviewed, and -- crucially -- uses domain separation
between leaf and internal nodes to prevent second-preimage attacks that affect
naive "duplicate the last node" Merkle trees:

    leaf hash:      SHA-256(0x00 || data)
    internal hash:  SHA-256(0x01 || left || right)
    empty tree:     SHA-256("")

For a list of ``n`` leaves the tree is defined recursively. Let ``k`` be the
largest power of two strictly less than ``n``::

    MTH([])      = SHA-256("")
    MTH([d0])    = SHA-256(0x00 || d0)
    MTH(D[0:n])  = SHA-256(0x01 || MTH(D[0:k]) || MTH(D[k:n]))   for n > 1

An inclusion proof (audit path) for leaf ``m`` is the ordered list of sibling
hashes, bottom-up, needed to recompute the root from leaf ``m``.

All hashes in the public API are lowercase hex strings; raw ``bytes`` are used
internally.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

_LEAF_PREFIX = b"\x00"
_NODE_PREFIX = b"\x01"


def _hash_leaf(data: bytes) -> bytes:
    return hashlib.sha256(_LEAF_PREFIX + data).digest()


def _hash_children(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(_NODE_PREFIX + left + right).digest()


def _largest_power_of_two_below(n: int) -> int:
    """Largest power of two strictly less than ``n`` (requires ``n >= 2``)."""
    k = 1
    while k * 2 < n:
        k *= 2
    return k


def _to_leaf_bytes(leaf: bytes | str) -> bytes:
    """Accept either raw bytes or a hex string as leaf input."""
    if isinstance(leaf, str):
        return bytes.fromhex(leaf)
    return leaf


def _merkle_root_bytes(leaves: Sequence[bytes]) -> bytes:
    n = len(leaves)
    if n == 0:
        return hashlib.sha256(b"").digest()
    if n == 1:
        return _hash_leaf(leaves[0])
    k = _largest_power_of_two_below(n)
    return _hash_children(_merkle_root_bytes(leaves[:k]), _merkle_root_bytes(leaves[k:]))


def _merkle_path_bytes(leaves: Sequence[bytes], index: int) -> list[bytes]:
    n = len(leaves)
    if n == 1:
        return []
    k = _largest_power_of_two_below(n)
    if index < k:
        return [*_merkle_path_bytes(leaves[:k], index), _merkle_root_bytes(leaves[k:])]
    return [*_merkle_path_bytes(leaves[k:], index - k), _merkle_root_bytes(leaves[:k])]


def merkle_root(leaves: Sequence[bytes | str]) -> str:
    """Return the Merkle Tree Hash (root) of ``leaves`` as a hex string.

    Leaves may be given as raw ``bytes`` or as hex strings.
    """
    raw = [_to_leaf_bytes(leaf) for leaf in leaves]
    return _merkle_root_bytes(raw).hex()


@dataclass(frozen=True)
class InclusionProof:
    """A proof that a leaf is included in a Merkle tree of a given size.

    Attributes:
        leaf_index: zero-based position of the leaf in the tree.
        tree_size: total number of leaves in the tree the proof is against.
        audit_path: sibling hashes (hex), ordered bottom-up.
    """

    leaf_index: int
    tree_size: int
    audit_path: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "leaf_index": self.leaf_index,
            "tree_size": self.tree_size,
            "audit_path": list(self.audit_path),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InclusionProof:
        return cls(
            leaf_index=int(data["leaf_index"]),
            tree_size=int(data["tree_size"]),
            audit_path=[str(h) for h in data["audit_path"]],
        )


def merkle_proof(leaves: Sequence[bytes | str], index: int) -> InclusionProof:
    """Build an :class:`InclusionProof` for ``leaves[index]``."""
    n = len(leaves)
    if not 0 <= index < n:
        raise IndexError(f"leaf index {index} out of range for tree of size {n}")
    raw = [_to_leaf_bytes(leaf) for leaf in leaves]
    path = _merkle_path_bytes(raw, index)
    return InclusionProof(leaf_index=index, tree_size=n, audit_path=[h.hex() for h in path])


def verify_inclusion_proof(leaf: bytes | str, proof: InclusionProof, root: str) -> bool:
    """Verify ``proof`` shows ``leaf`` is included in a tree with the given ``root``.

    Implements the RFC 6962 audit-path verification algorithm.
    """
    if not 0 <= proof.leaf_index < proof.tree_size:
        return False

    r = _hash_leaf(_to_leaf_bytes(leaf))
    fn = proof.leaf_index
    sn = proof.tree_size - 1

    for sibling_hex in proof.audit_path:
        if sn == 0:
            # More path entries than the tree size allows.
            return False
        sibling = bytes.fromhex(sibling_hex)
        if (fn & 1) == 1 or fn == sn:
            r = _hash_children(sibling, r)
            if (fn & 1) == 0:
                while (fn & 1) == 0 and fn != 0:
                    fn >>= 1
                    sn >>= 1
        else:
            r = _hash_children(r, sibling)
        fn >>= 1
        sn >>= 1

    return fn == 0 and r.hex() == root
