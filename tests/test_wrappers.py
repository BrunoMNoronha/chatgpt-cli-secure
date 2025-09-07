from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path


def test_gpt_wrapper_resolves_moved_package(tmp_path: Path) -> None:
    wrapper_src: Path = Path("wrappers/gpt")
    wrapper_dest_dir: Path = tmp_path / "wrappers"
    wrapper_dest_dir.mkdir()
    wrapper_dest: Path = wrapper_dest_dir / "gpt"
    shutil.copy(wrapper_src, wrapper_dest)

    pkg_dir: Path = tmp_path / "chatgpt_cli"
    pkg_dir.mkdir()
    init: Path = pkg_dir / "__init__.py"
    init.write_text("def main() -> None:\n    print('gpt_cli_ok')\n")
    main_file: Path = pkg_dir / "__main__.py"
    main_file.write_text("from . import main\nmain()\n")

    wrapper_dest.chmod(wrapper_dest.stat().st_mode | stat.S_IEXEC)

    env: dict[str, str] = os.environ.copy()
    env["OPENAI_API_KEY"] = "test"
    env["PREFIX_DIR"] = str(tmp_path)
    result: subprocess.CompletedProcess[str] = subprocess.run(
        [str(wrapper_dest)], capture_output=True, text=True, check=True, env=env
    )
    assert result.stdout.strip() == "gpt_cli_ok"


def test_gpt_gui_wrapper_resolves_moved_script(tmp_path: Path) -> None:
    wrapper_src: Path = Path("wrappers/gpt-gui")
    wrapper_dest_dir: Path = tmp_path / "wrappers"
    wrapper_dest_dir.mkdir()
    wrapper_dest: Path = wrapper_dest_dir / "gpt-gui"
    shutil.copy(wrapper_src, wrapper_dest)

    dummy_script: Path = tmp_path / "gpt-gui.sh"
    dummy_script.write_text("#!/bin/sh\necho gpt_gui_ok\n")
    dummy_script.chmod(dummy_script.stat().st_mode | stat.S_IEXEC)

    wrapper_dest.chmod(wrapper_dest.stat().st_mode | stat.S_IEXEC)

    result: subprocess.CompletedProcess[str] = subprocess.run(
        [str(wrapper_dest)], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == "gpt_gui_ok"
