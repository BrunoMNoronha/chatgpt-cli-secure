import os
import subprocess
from pathlib import Path

def run_check(tmp_path: Path, config_text: str) -> subprocess.CompletedProcess[str]:
    config_dir: Path = tmp_path / '.config/chatgpt-cli'
    config_dir.mkdir(parents=True)
    (config_dir / 'config').write_text(config_text)
    env: dict[str, str] = {**os.environ, 'HOME': str(tmp_path)}
    env.pop('GH_REPO', None)
    env.pop('UPDATE_URL', None)
    return subprocess.run(
        ['bash', 'check-update.sh', '--machine-read'],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
    )

def test_valid_config(tmp_path: Path) -> None:
    result = run_check(tmp_path, '#comentario\nGH_REPO=\nUNSAFE=1\n')
    assert result.returncode == 0
    assert 'HAS_UPDATE=0' in result.stdout

def test_malformed_line(tmp_path: Path) -> None:
    result = run_check(tmp_path, 'BADLINE')
    assert result.returncode != 0
    assert 'Linha malformada' in result.stderr
