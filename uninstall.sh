#!/bin/bash
# Remove os wrappers e o atalho de desktop. Use --purge para apagar também os dados e scripts.
set -e

BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"
PREFIX_DIR="${PREFIX_DIR:-$HOME/.local/share/chatgpt-cli}"
STATE_DIR="$HOME/.local/state/chatgpt-cli"
SHARE_DIR="$HOME/.local/share/chatgpt-cli"
CONFIG_DIR="$HOME/.config/chatgpt-cli"

PURGE=false
REMOVE_DEPS=false
for arg in "$@"; do
  case "$arg" in
    --purge)
      PURGE=true
      ;;
    --remove-deps)
      REMOVE_DEPS=true
      ;;
  esac
done

rm -f "$BIN_DIR/gpt" "$BIN_DIR/gpt-gui"
rm -f "$APP_DIR/chatgpt-gui.desktop"

# Remove $BIN_DIR from common shell configuration files
for file in "$HOME/.bashrc" "$HOME/.profile"; do
  if [ -f "$file" ] && grep -q "$BIN_DIR" "$file"; then
    tmp_file="$(mktemp)"
    grep -v "$BIN_DIR" "$file" > "$tmp_file"
    mv "$tmp_file" "$file"
  fi
done

if [ "$PURGE" = true ]; then
  rm -rf "$PREFIX_DIR"
  rm -rf "$STATE_DIR"
  rm -rf "$SHARE_DIR" "$CONFIG_DIR"
  rm -f "$SHARE_DIR/secret.enc"
  rm -f "$CONFIG_DIR/config"
  echo "Todos os dados e scripts foram removidos."
fi

if [ "$PURGE" = true ] || [ "$REMOVE_DEPS" = true ]; then
  python -m utils.dependency_manager
fi

echo "Desinstalação concluída."
echo "Você pode precisar reiniciar a sessão para que as mudanças no PATH tenham efeito."
