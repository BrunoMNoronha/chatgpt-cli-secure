import stat
from pathlib import Path

import pytest

from chatgpt_cli.secure_storage import KeyLocation, load_api_key, save_api_key


def test_save_and_load_api_key(tmp_path: Path) -> None:
    loc = KeyLocation(base_dir=tmp_path)
    save_api_key("chave-teste", loc=loc)
    recovered = load_api_key(loc=loc)
    assert recovered == "chave-teste"
    mode = stat.S_IMODE(loc.path.stat().st_mode)
    assert mode == 0o600


def test_load_api_key_missing_file(tmp_path: Path) -> None:
    loc = KeyLocation(base_dir=tmp_path)
    with pytest.raises(FileNotFoundError):
        load_api_key(loc=loc)
