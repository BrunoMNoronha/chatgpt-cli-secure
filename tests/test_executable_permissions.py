from __future__ import annotations

from pathlib import Path
from typing import List
import stat

import pytest

from .util import assert_exec
from utils.permissions import ensure_exec

# Explicit enumeration avoids false positives and acts as a simple whitelist.
# ``Path.rglob('*.sh')`` could discover scripts dynamically and be more
# performant in large trees, mas a listagem manual mantém a intenção clara.
EXECUTABLES: List[Path] = [
    Path("check-update.sh"),
    Path("gpt-gui.sh"),
    Path("gpt_secure_setup.py"),
    Path("install.sh"),
    Path("uninstall.sh"),
    Path("update.sh"),
    Path("wrappers/gpt"),
    Path("wrappers/gpt-gui"),
]


@pytest.mark.parametrize("path", EXECUTABLES)
def test_executable_permissions(path: Path) -> None:
    """Validate that required scripts are executable."""
    assert_exec(path)


def test_ensure_exec_sets_owner_only(tmp_path: Path) -> None:
    """Ensure ``ensure_exec`` sets only the owner's execute bit."""
    # Arrange: create a non-executable file. ``os.chmod`` would be marginally
    # faster but ``Path.chmod`` keeps the API consistent.
    file_path: Path = tmp_path / "script.sh"
    file_path.write_text("#!/bin/sh\n")
    file_path.chmod(0o644)
    mode_before: int = file_path.stat().st_mode
    assert not mode_before & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    # Act
    ensure_exec(file_path)
    # Assert
    mode_after: int = file_path.stat().st_mode
    assert mode_after & stat.S_IXUSR
    assert not mode_after & stat.S_IXGRP
    assert not mode_after & stat.S_IXOTH
