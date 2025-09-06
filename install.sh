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
  cp -f gpt_cli.py gpt-gui.sh gpt-secure-setup.sh update.sh check-update.sh version.txt README.md LICENSE "$PREFIX_DIR/"
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
cat > "$CONFIG" <<'EOF2'
MODEL="gpt-4o-mini"
TEMP="0.7"
UPDATE_URL=""
GH_REPO=""
EOF2
fi

echo "Instalação concluída. Use 'gpt' para a CLI e 'gpt-gui' para a GUI."
