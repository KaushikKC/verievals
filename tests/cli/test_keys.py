"""Tests for CLI key file helpers."""

from __future__ import annotations

import stat
import sys
from pathlib import Path

import pytest

from verievals.cli import keys


def test_generate_and_load_roundtrip(tmp_path: Path) -> None:
    key, private_path, public_path = keys.generate_and_save(tmp_path / "runner")
    assert private_path.name == "runner.key"
    assert public_path.name == "runner.pub"
    loaded = keys.load_signing_key(private_path)
    assert loaded.hex == key.hex
    assert public_path.read_text().strip() == key.verify_key.hex


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permissions only")
def test_private_key_is_not_world_readable(tmp_path: Path) -> None:
    _key, private_path, _public = keys.generate_and_save(tmp_path / "runner")
    mode = stat.S_IMODE(private_path.stat().st_mode)
    assert mode & 0o077 == 0  # no group/other permissions
