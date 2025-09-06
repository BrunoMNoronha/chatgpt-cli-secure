from __future__ import annotations

import shutil
import stat
import subprocess
from pathlib import Path


def test_gpt_wrapper_resolves_moved_script(tmp_path: Path) -> None:
    wrapper_src: Path = Path("wrappers/gpt")
    wrapper_dest_dir: Path = tmp_path / "wrappers"
    wrapper_dest_dir.mkdir()
    wrapper_dest: Path = wrapper_dest_dir / "gpt"
    shutil.copy(wrapper_src, wrapper_dest)

    dummy_script: Path = tmp_path / "gpt_cli.py"
    dummy_script.write_text("print('gpt_cli_ok')\n")

    wrapper_dest.chmod(wrapper_dest.stat().st_mode | stat.S_IEXEC)

    result: subprocess.CompletedProcess[str] = subprocess.run(
        [str(wrapper_dest)], capture_output=True, text=True, check=True
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
