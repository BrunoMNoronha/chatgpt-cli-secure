import importlib
import sys
import types
from pathlib import Path

import pytest


def load_module(monkeypatch: pytest.MonkeyPatch):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    dummy_requests = types.ModuleType("requests")
    dummy_requests.Response = object
    exc = types.ModuleType("requests.exceptions")
    exc.RequestException = Exception
    monkeypatch.setitem(sys.modules, "requests", dummy_requests)
    monkeypatch.setitem(sys.modules, "requests.exceptions", exc)
    return importlib.import_module("chatgpt_cli")


def test_load_env_config_default(monkeypatch: pytest.MonkeyPatch) -> None:
    cli = load_module(monkeypatch)
    monkeypatch.delenv('OPENAI_MODEL', raising=False)
    monkeypatch.delenv('OPENAI_TEMP', raising=False)
    cfg = cli.load_env_config({})
    assert cfg.model == 'gpt-4o-mini'
    assert cfg.temperature == 0.7


def test_load_env_config_invalid_temp(monkeypatch: pytest.MonkeyPatch) -> None:
    cli = load_module(monkeypatch)
    monkeypatch.setenv('OPENAI_TEMP', '5')
    with pytest.raises(ValueError):
        cli.load_env_config({})
