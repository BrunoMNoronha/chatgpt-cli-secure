from __future__ import annotations

from pathlib import Path
import stat


def ensure_exec(path: Path) -> None:
    """Ensure that a file is executable by its owner only."""
    mode: int = path.stat().st_mode
    owner_exec: bool = bool(mode & stat.S_IXUSR)
    group_or_other_exec: bool = bool(mode & (stat.S_IXGRP | stat.S_IXOTH))
    if owner_exec and not group_or_other_exec:
        return
    new_mode: int = (mode | stat.S_IXUSR) & ~(stat.S_IXGRP | stat.S_IXOTH)
    path.chmod(new_mode)
