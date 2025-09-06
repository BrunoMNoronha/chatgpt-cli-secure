import os
import tarfile
from pathlib import Path
import subprocess

def _create_package(tmp_dir: Path, script: str) -> Path:
    pkg_dir = tmp_dir / "pkg"
    pkg_dir.mkdir()
    install_script = pkg_dir / "install.sh"
    install_script.write_text(script)
    install_script.chmod(0o755)
    tar_path = tmp_dir / "pkg.tar"
    with tarfile.open(tar_path, "w") as tar:
        tar.add(pkg_dir, arcname="pkg")
    return tar_path

def _run_update(tar_path: Path, base_tmp: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["TMPDIR"] = str(base_tmp)
    return subprocess.run([
        "bash",
        "update.sh",
        "--from-file",
        str(tar_path),
    ], cwd=str(Path(__file__).resolve().parent.parent), capture_output=True, text=True, env=env)

def test_tmp_removed_on_success(tmp_path: Path) -> None:
    base_tmp = tmp_path / "tmp"
    base_tmp.mkdir()
    tar_path = _create_package(tmp_path, "#!/bin/bash\nexit 0\n")
    result = _run_update(tar_path, base_tmp)
    assert result.returncode == 0
    assert list(base_tmp.iterdir()) == []

def test_tmp_removed_on_failure(tmp_path: Path) -> None:
    base_tmp = tmp_path / "tmp"
    base_tmp.mkdir()
    tar_path = _create_package(tmp_path, "#!/bin/bash\nexit 1\n")
    result = _run_update(tar_path, base_tmp)
    assert result.returncode != 0
    assert list(base_tmp.iterdir()) == []
