"""Verifiable Evals (``verievals``).

An open-source benchmark runner where every eval run produces a signed,
reproducible record that is appended to a public Merkle log, so that anyone can
re-run and cryptographically verify a leaderboard entry.
"""

from verievals.version import __version__

__all__ = ["__version__"]
