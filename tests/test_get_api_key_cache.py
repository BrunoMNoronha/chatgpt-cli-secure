from pathlib import Path

import pytest

import chatgpt_cli
from chatgpt_cli import get_api_key


def test_get_api_key_calls_decrypt_once(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: int = 0

    def fake_load_api_key(password: str, loc: object) -> str:
        nonlocal calls
        calls += 1
        return "decrypted"

    secret_file: Path = tmp_path / "secret.enc"
    secret_file.write_text("data")

    class DummyLocation:
        def __init__(self) -> None:
            self.path = secret_file

    monkeypatch.setattr(chatgpt_cli, "load_api_key", fake_load_api_key)
    monkeypatch.setattr(chatgpt_cli, "KeyLocation", DummyLocation)
    monkeypatch.setenv("OPENAI_MASTER_PASSWORD", "pwd")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_api_key.cache_clear()

    assert get_api_key() == "decrypted"
    assert get_api_key() == "decrypted"
    assert calls == 1
    get_api_key.cache_clear()

