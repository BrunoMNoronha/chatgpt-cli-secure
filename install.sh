#!/bin/bash
# Instala o chatgpt-cli-secure na pasta do usuário.
set -e

PREFIX_DIR="$HOME/Documentos/chatgpt-cli"
BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"

mkdir -p "$PREFIX_DIR" "$BIN_DIR" "$APP_DIR"
mkdir -p "$HOME/.config/chatgpt-cli" \
         "$HOME/.local/share/chatgpt-cli" \
         "$HOME/.local/state/chatgpt-cli/sessions"

# Copiar scripts principais
cp -f gpt_cli.py gpt-gui.sh gpt-secure-setup.sh update.sh check-update.sh version.txt README.md LICENSE "$PREFIX_DIR/"

# Copiar wrappers e desktop
mkdir -p "$PREFIX_DIR/wrappers" "$PREFIX_DIR/desktop"
cp -f wrappers/gpt wrappers/gpt-gui "$PREFIX_DIR/wrappers/"
cp -f desktop/chatgpt-gui.desktop "$PREFIX_DIR/desktop/"

# Instalar wrappers no PATH
install -m 755 "$PREFIX_DIR/wrappers/gpt" "$BIN_DIR/gpt"
install -m 755 "$PREFIX_DIR/wrappers/gpt-gui" "$BIN_DIR/gpt-gui"

# Instalar atalho de desktop (ajusta o Exec para apontar para bin)
desktop_file="$APP_DIR/chatgpt-gui.desktop"
sed "s|Exec=.*|Exec=$BIN_DIR/gpt-gui|g" "$PREFIX_DIR/desktop/chatgpt-gui.desktop" > "$desktop_file"
chmod 644 "$desktop_file"

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
