from __future__ import annotations

import hashlib
import subprocess
import tarfile
import tempfile
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class UpdateStrategy(ABC):
    """Interface for update strategies."""

    @abstractmethod
    def install(self) -> None:
        """Execute the update process."""


@dataclass
class FileStrategy(UpdateStrategy):
    """Install update from a local archive file."""

    path: Path
    sha256: Optional[str] = None

    def _verify_hash(self) -> None:
        expected: Optional[str] = self.sha256
        if expected is None:
            hash_path = self.path.with_suffix(self.path.suffix + ".sha256")
            if hash_path.exists():
                expected = hash_path.read_text().strip().split()[0]
        if expected is None:
            return
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        if digest != expected:
            raise ValueError("SHA256 mismatch")

    def install(self) -> None:  # type: ignore[override]
        self._verify_hash()
        with tempfile.TemporaryDirectory() as tmp:
            with tarfile.open(self.path) as tar:
                tar.extractall(tmp)
            dir_path = next(p for p in Path(tmp).iterdir() if p.is_dir())
            install_script = dir_path / "install.sh"
            subprocess.run(["bash", str(install_script)], check=True)


@dataclass
class UrlStrategy(UpdateStrategy):
    """Download update package from URL and install it."""

    url: str

    def _download(self, dest: Path) -> Optional[str]:
        urllib.request.urlretrieve(self.url, dest)
        hash_dest = dest.with_suffix(dest.suffix + ".sha256")
        try:
            urllib.request.urlretrieve(self.url + ".sha256", hash_dest)
            return hash_dest.read_text().strip().split()[0]
        except Exception:
            return None

    def install(self) -> None:  # type: ignore[override]
        with tempfile.TemporaryDirectory() as tmp:
            file_path = Path(tmp) / "package.tar"
            sha256 = self._download(file_path)
            FileStrategy(file_path, sha256).install()


@dataclass
class GitHubStrategy(UpdateStrategy):
    """Check GitHub for updates and install if available."""

    check_script: Path = Path("check-update.sh")

    def install(self) -> None:  # type: ignore[override]
        result = subprocess.run(
            [str(self.check_script), "--machine-read"],
            capture_output=True,
            text=True,
            check=True,
        )
        info = dict(
            line.strip().split("=", 1)
            for line in result.stdout.splitlines()
            if "=" in line
        )
        if info.get("HAS_UPDATE") != "1":
            return
        url = info.get("NEW_URL")
        if not url:
            raise RuntimeError("Missing NEW_URL from check-update output")
        UrlStrategy(url).install()
