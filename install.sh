#!/bin/bash
# Instala o chatgpt-cli-secure na pasta do usuário.
set -e

PREFIX_DIR="${PREFIX_DIR:-$HOME/.local/share/chatgpt-cli}"
BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"

mkdir -p "$HOME/.config/chatgpt-cli" \
         "$HOME/.local/state/chatgpt-cli/sessions"

if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete --exclude '.git/' ./ "$PREFIX_DIR/"
else
  mkdir -p "$PREFIX_DIR"
  cp -rf chatgpt_cli gpt-gui.sh gpt-secure-setup.sh update.sh check-update.sh version.txt README.md LICENSE "$PREFIX_DIR/"
  mkdir -p "$PREFIX_DIR/wrappers" "$PREFIX_DIR/desktop"
  cp -f wrappers/gpt wrappers/gpt-gui "$PREFIX_DIR/wrappers/"
  cp -f desktop/chatgpt-gui.desktop "$PREFIX_DIR/desktop/"
fi

# Instalar wrappers no PATH
install -Dm 755 "$PREFIX_DIR/wrappers/gpt" "$BIN_DIR/gpt"
install -Dm 755 "$PREFIX_DIR/wrappers/gpt-gui" "$BIN_DIR/gpt-gui"

# Instalar atalho de desktop (ajusta o Exec para apontar para bin)
desktop_file="$APP_DIR/chatgpt-gui.desktop"
sed "s|Exec=.*|Exec=$BIN_DIR/gpt-gui|g" "$PREFIX_DIR/desktop/chatgpt-gui.desktop" \
  | install -Dm 644 /dev/stdin "$desktop_file"

# Criar config padrão se não existir
CONFIG="$HOME/.config/chatgpt-cli/config"
if [ ! -f "$CONFIG" ]; then
  cp "$PREFIX_DIR/chatgpt_cli/config.example" "$CONFIG"
  # Alternativa mais performática: ``install -Dm 644`` define permissões em
  # um único passo, mas ``cp`` mantém a simplicidade e segue o padrão
  # *Guard Clause* para idempotência.
fi

# Verificar comandos instalados com *Guard Clause* e *type hints*.
# Alternativa mais performática (menos portável): ``command -v gpt >/dev/null``
# diretamente no shell.
python3 - <<'PY'
from __future__ import annotations
import os
import shutil
from pathlib import Path
from typing import List


def finalize(commands: List[str], bin_dir: Path, secret: Path) -> None:
    """
    Verifica comandos e orienta conforme a presença do segredo.

    Possíveis melhorias de desempenho: usar ``next`` com geradores para
    encerrar a busca ao encontrar a primeira ausência ou cachear resultados de
    ``shutil.which`` para listas extensas.
    """
    missing: List[str] = [cmd for cmd in commands if shutil.which(cmd) is None]
    if missing:
        print(
            f"Instalação concluída, mas {', '.join(missing)} não está no PATH."
        )
        print(f"Adicione {bin_dir} ao PATH para usá-los.")
        return
    if secret.exists():  # Guard Clause
        print("Instalação concluída. Use 'gpt' para a CLI e 'gpt-gui' para a GUI.")
        return
    print(
        "Instalação concluída. Execute 'gpt-secure-setup.sh' para configurar a API key."
    )


bin_dir = Path(os.environ.get('BIN_DIR', str(Path.home() / '.local/bin')))
secret_path = (
    Path(os.environ.get('PREFIX_DIR', str(Path.home() / '.local/share/chatgpt-cli')))
    / 'secret.enc'
)
finalize(['gpt', 'gpt-gui'], bin_dir, secret_path)
PY
