from __future__ import annotations

from pathlib import Path
import stat


def ensure_exec(path: Path) -> None:
    """Ensure that a file is executable by owner, group, and others."""
    mode = path.stat().st_mode
    if not mode & stat.S_IXUSR:
        path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
