import stat
from pathlib import Path

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
