from __future__ import annotations

from pathlib import Path
from typing import List

import pytest

from .util import assert_exec

# Explicit enumeration avoids false positives and acts as a simple whitelist.
# ``Path.rglob('*.sh')`` could discover scripts dynamically and be more
# performant in large trees, but manual listing keeps intent clear.
EXECUTABLES: List[Path] = [
    Path("check-update.sh"),
    Path("gpt-gui.sh"),
    Path("gpt-secure-setup.sh"),
    Path("gpt_cli.py"),
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
