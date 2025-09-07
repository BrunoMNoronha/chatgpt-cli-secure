from __future__ import annotations

from types import SimpleNamespace
from typing import Any, List

import utils.dependency_manager as dependency_manager


def test_remove_dependencies_uninstalls_unused_packages_once(monkeypatch: Any) -> None:
    called: List[List[str]] = []

    def fake_run(cmd: List[str], check: bool = False, **_: Any) -> SimpleNamespace:
        called.append(cmd)
        return SimpleNamespace(returncode=0, stdout="")

    monkeypatch.setattr(dependency_manager, "dependency_in_use", lambda pkg: pkg == "keep")
    monkeypatch.setattr(dependency_manager.subprocess, "run", fake_run)

    dependency_manager.remove_dependencies(["remove1", "keep", "remove2"])

    assert called == [["pip", "uninstall", "--yes", "remove1", "remove2"]]

