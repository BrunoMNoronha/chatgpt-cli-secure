import os
import tarfile
import shutil
import io
from pathlib import Path
from typing import Dict
import subprocess
import urllib.request
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent))
from update_strategies import FileStrategy, UrlStrategy, GitHubStrategy, _safe_extract


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


def _sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def test_file_strategy_executes_install(tmp_path: Path) -> None:
    tar_path = _create_package(tmp_path, "#!/bin/bash\necho ok > \"$OUTPUT\"\n")
    out = tmp_path / "out.txt"
    os.environ["OUTPUT"] = str(out)
    try:
        FileStrategy(tar_path).install()
    finally:
        os.environ.pop("OUTPUT")
    assert out.read_text().strip() == "ok"


def test_url_strategy_downloads_and_installs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tar_path = _create_package(tmp_path, "#!/bin/bash\necho ok > \"$OUTPUT\"\n")
    sha = _sha256(tar_path)
    sha_path = tmp_path / "pkg.tar.sha256"
    sha_path.write_text(f"{sha}  pkg.tar")
    url = "https://example.com/pkg.tar"
    files: Dict[str, Path] = {url: tar_path, url + ".sha256": sha_path}

    def fake_urlretrieve(link: str, filename: str, *args, **kwargs):
        shutil.copy(files[link], filename)
        return filename, None

    monkeypatch.setattr(urllib.request, "urlretrieve", fake_urlretrieve)
    out = tmp_path / "out.txt"
    os.environ["OUTPUT"] = str(out)
    try:
        UrlStrategy(url).install()
    finally:
        os.environ.pop("OUTPUT")
    assert out.read_text().strip() == "ok"


def test_github_strategy_uses_check_script(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tar_path = _create_package(tmp_path, "#!/bin/bash\necho ok > \"$OUTPUT\"\n")
    sha = _sha256(tar_path)
    sha_path = tmp_path / "pkg.tar.sha256"
    sha_path.write_text(f"{sha}  pkg.tar")
    url = "https://example.com/pkg.tar"
    files: Dict[str, Path] = {url: tar_path, url + ".sha256": sha_path}

    def fake_urlretrieve(link: str, filename: str, *args, **kwargs):
        shutil.copy(files[link], filename)
        return filename, None

    monkeypatch.setattr(urllib.request, "urlretrieve", fake_urlretrieve)
    real_run = subprocess.run

    def fake_run(cmd, *args, **kwargs):
        if "--machine-read" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout=f"HAS_UPDATE=1\nNEW_URL={url}\n", stderr="")
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", fake_run)
    out = tmp_path / "out.txt"
    os.environ["OUTPUT"] = str(out)
    try:
        GitHubStrategy().install()
    finally:
        os.environ.pop("OUTPUT")
    assert out.read_text().strip() == "ok"


def test_safe_extract_detects_path_traversal(tmp_path: Path) -> None:
    tar_path = tmp_path / "malicious.tar"
    with tarfile.open(tar_path, "w") as tar:
        info = tarfile.TarInfo(name="../evil.txt")
        data = b"malicious"
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    with tarfile.open(tar_path) as tar:
        with pytest.raises(ValueError):
            _safe_extract(tar, tmp_path)
