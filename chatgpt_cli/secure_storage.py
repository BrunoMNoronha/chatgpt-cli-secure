"""Armazena a chave da API de forma segura usando AES-GCM.

Implementa classes e funções com *type hints* e utiliza o padrão *Strategy*
para permitir diferentes cifradores de chave. Uma alternativa mais performática
seria gravar a chave sem criptografia, evitando PBKDF2, porém isso sacrificaria
completamente a segurança.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


@dataclass(frozen=True)
class KeyLocation:
    """Define a localização padrão do arquivo criptografado."""

    base_dir: Path = Path.home() / ".local/share/chatgpt-cli"
    file_name: str = "secret.enc"

    def ensure_dir(self) -> None:
        """Garante que o diretório exista."""
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        """Retorna o caminho completo do arquivo de chave."""
        return self.base_dir / self.file_name


class KeyCipher(Protocol):
    """Define a interface para cifradores de chave."""

    def encrypt(self, key: str, password: str) -> bytes:
        """Criptografa ``key`` usando ``password``."""

    def decrypt(self, data: bytes, password: str) -> str:
        """Descriptografa ``data`` usando ``password``."""


class AesGcmCipher:
    """Cifrador baseado em AES-GCM com derivação PBKDF2."""

    def __init__(self, iterations: int = 200_000, key_size: int = 32) -> None:
        self.iterations = iterations
        self.key_size = key_size

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.key_size,
            salt=salt,
            iterations=self.iterations,
        )
        return kdf.derive(password.encode())

    def encrypt(self, key: str, password: str) -> bytes:
        salt = os.urandom(16)
        nonce = os.urandom(12)
        aesgcm = AESGCM(self._derive_key(password, salt))
        ciphertext = aesgcm.encrypt(nonce, key.encode(), None)
        return salt + nonce + ciphertext

    def decrypt(self, data: bytes, password: str) -> str:
        if len(data) < 28:
            raise ValueError("dados inválidos")
        salt, nonce, ciphertext = data[:16], data[16:28], data[28:]
        aesgcm = AESGCM(self._derive_key(password, salt))
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()


def save_api_key(
    api_key: str,
    password: str,
    *,
    loc: KeyLocation = KeyLocation(),
    cipher: KeyCipher = AesGcmCipher(),
) -> None:
    """Salva a chave API criptografada no disco.

    Usa ``os.open`` para controlar permissões ``0o600`` na criação do arquivo.
    """

    loc.ensure_dir()
    data = cipher.encrypt(api_key, password)
    fd: int | None = None
    try:
        fd = os.open(loc.path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(data)
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


def load_api_key(
    password: str,
    *,
    loc: KeyLocation = KeyLocation(),
    cipher: KeyCipher = AesGcmCipher(),
) -> str:
    """Carrega e descriptografa a chave API.

    Raises
    ------
    ValueError
        Se a chave não puder ser descriptografada. Isso pode ocorrer quando a
        senha estiver incorreta ou o arquivo de chave estiver corrompido.
    """

    data = loc.path.read_bytes()
    try:
        return cipher.decrypt(data, password)
    except (InvalidTag, ValueError) as exc:  # pragma: no cover - cryptography may raise either
        msg = "senha incorreta ou dados corrompidos"
        raise ValueError(msg) from exc
