from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_install_writes_config_example(tmp_path: Path) -> None:
    """Executa ``install.sh`` e verifica se o config gerado segue o exemplo.

    Usa ``subprocess.run`` para integração real. Uma alternativa mais
    performática seria chamar diretamente funções internas, mas perderíamos a
    validação ponta a ponta."""
    repo_root: Path = Path(__file__).resolve().parents[1]
    env: dict[str, str] = {**os.environ, "HOME": str(tmp_path), "PREFIX_DIR": str(tmp_path / "prefix")}
    subprocess.run(["bash", str(repo_root / "install.sh")], check=True, cwd=repo_root, env=env)
    config_file: Path = tmp_path / ".config/chatgpt-cli/config"
    example_file: Path = repo_root / "chatgpt_cli/config.example"
    assert config_file.read_text(encoding="utf-8") == example_file.read_text(encoding="utf-8")
