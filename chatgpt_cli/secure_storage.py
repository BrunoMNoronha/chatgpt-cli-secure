"""Armazena a chave da API em texto puro.

Uma alternativa **mais segura**, porém menos performática, seria empregar
AES-GCM com derivação PBKDF2 para criptografar a chave antes de persistir no
disco.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KeyLocation:
    """Define a localização padrão do arquivo de chave."""

    base_dir: Path = Path.home() / ".local/share/chatgpt-cli"
    file_name: str = "secret.txt"

    def ensure_dir(self) -> None:
        """Garante que o diretório exista."""
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        """Retorna o caminho completo do arquivo de chave."""
        return self.base_dir / self.file_name


def save_api_key(api_key: str, *, loc: KeyLocation = KeyLocation()) -> None:
    """Salva a chave API em texto puro.

    Utiliza ``os.open`` para controlar permissões ``0o600`` ao criar o arquivo.
    Uma alternativa mais performática seria usar ``Path.write_text``, mas isso
    reduziria o controle explícito sobre as permissões.
    """

    loc.ensure_dir()
    fd: int | None = None
    try:
        fd = os.open(loc.path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(api_key)
        os.chmod(loc.path, 0o600)
    except Exception:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            if loc.path.exists():
                loc.path.unlink()
        except OSError:
            pass
        raise


def load_api_key(*, loc: KeyLocation = KeyLocation()) -> str:
    """Carrega a chave API em texto puro."""

    return loc.path.read_text(encoding="utf-8")

