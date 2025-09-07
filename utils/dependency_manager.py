from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable
import tomllib

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _read_dependencies(pyproject_path: Path = PYPROJECT) -> list[str]:
    """Read project dependencies from pyproject.toml."""
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)
    project = data.get("project", {})
    return [dep.split(";")[0].strip() for dep in project.get("dependencies", [])]

def dependency_in_use(package: str) -> bool:
    """Return True if *package* is required by another installed package."""
    result = subprocess.run(
        ["pip", "show", package],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False
    for line in result.stdout.splitlines():
        if line.startswith("Required-by:"):
            required_by = line.split(":", 1)[1].strip()
            return bool(required_by and required_by != "None")
    return False

def remove_dependencies(packages: Iterable[str]) -> None:
    """Uninstall packages that are not required by others."""
    for package in packages:
        if not dependency_in_use(package):
            subprocess.run(
                ["pip", "uninstall", "--yes", package],
                check=False,
            )

def main() -> None:
    remove_dependencies(_read_dependencies())

if __name__ == "__main__":  # pragma: no cover
    main()
