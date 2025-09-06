from __future__ import annotations

import stat
from pathlib import Path
from typing import Union


def assert_exec(path: Union[str, Path]) -> None:
    """Assert that a given path exists, is a file and is executable.

    Guard clauses improve readability by failing fast. Using ``Path.stat`` is
    explicit and portable, albeit marginally slower than ``os.access`` which
    checks permissions directly via the C interface.
    """
    p: Path = Path(path)
    assert p.is_file(), f"{p} is not a file"
    mode: int = p.stat().st_mode
    is_exec: bool = bool(mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
    assert is_exec, f"{p} is not executable"
