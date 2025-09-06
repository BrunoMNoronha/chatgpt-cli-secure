from pathlib import Path
import importlib
import sys
import types


def test_read_config_invalid_file(tmp_path: Path, monkeypatch) -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    dummy_requests = types.ModuleType("requests")
    dummy_requests.Response = object
    exc = types.ModuleType("requests.exceptions")
    exc.RequestException = Exception
    monkeypatch.setitem(sys.modules, "requests", dummy_requests)
    monkeypatch.setitem(sys.modules, "requests.exceptions", exc)
    cli = importlib.import_module("chatgpt_cli")
    config_file: Path = tmp_path / "config"
    config_file.write_text("invalid-line")
    monkeypatch.setattr(cli, "CONFIG_PATH", config_file)
    assert cli.read_config() == {}
