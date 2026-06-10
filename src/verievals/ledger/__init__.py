"""The public Merkle ledger and the record verifier.

:class:`~verievals.ledger.merkle_log.MerkleLog` is an append-only log of signed
records. Appending a record commits its content hash as a Merkle leaf; the log's
single root hash commits to every record it contains. A compact inclusion proof
lets anyone confirm a specific record is committed under a published root.

:func:`~verievals.ledger.verifier.verify_record` performs the full verification
protocol: integrity, signature, Merkle inclusion, and (optionally) bit-for-bit
re-run reproduction.
"""

from verievals.ledger.merkle_log import MerkleLog
from verievals.ledger.verifier import VerificationResult, reproduce_record, verify_record

__all__ = ["MerkleLog", "VerificationResult", "reproduce_record", "verify_record"]
