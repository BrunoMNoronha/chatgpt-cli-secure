import stat
from pathlib import Path

import pytest
from cryptography.exceptions import InvalidTag

from chatgpt_cli.secure_storage import (
    AesGcmCipher,
    KeyLocation,
    load_api_key,
    save_api_key,
)


def test_save_and_load_api_key(tmp_path: Path) -> None:
    loc = KeyLocation(base_dir=tmp_path)
    save_api_key("chave-teste", "senha", loc=loc, cipher=AesGcmCipher())
    recovered = load_api_key("senha", loc=loc, cipher=AesGcmCipher())
    assert recovered == "chave-teste"
    mode = stat.S_IMODE(loc.path.stat().st_mode)
    assert mode == 0o600


def test_load_api_key_errors(tmp_path: Path) -> None:
    """Ensure wrong password or corrupted file raises an exception."""
    loc = KeyLocation(base_dir=tmp_path)
    save_api_key("chave-teste", "senha-correta", loc=loc, cipher=AesGcmCipher())

    # Wrong password should not decrypt
    with pytest.raises((ValueError, InvalidTag)):
        load_api_key("senha-errada", loc=loc, cipher=AesGcmCipher())

    # Corrupt stored data and expect failure
    data = bytearray(loc.path.read_bytes())
    data[0] ^= 0xFF
    loc.path.write_bytes(data)

    with pytest.raises((ValueError, InvalidTag)):
        load_api_key("senha-correta", loc=loc, cipher=AesGcmCipher())
