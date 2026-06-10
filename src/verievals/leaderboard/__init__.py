"""Build verifiable leaderboards from records committed to a ledger.

Every leaderboard entry is backed by a signed record whose Merkle inclusion under
the ledger's published root has been checked. The rendered table includes the
root and each record id so a reader can independently re-verify any row.
"""

from verievals.leaderboard.builder import (
    Leaderboard,
    LeaderboardEntry,
    build_leaderboard,
)

__all__ = ["Leaderboard", "LeaderboardEntry", "build_leaderboard"]
