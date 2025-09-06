#!/bin/bash
# Remove os wrappers e o atalho de desktop. Use --purge para apagar também os dados e scripts.
set -e

BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"
PREFIX_DIR="${PREFIX_DIR:-$HOME/.local/share/chatgpt-cli}"
STATE_DIR="$HOME/.local/state/chatgpt-cli"
SHARE_DIR="$HOME/.local/share/chatgpt-cli"
CONFIG_DIR="$HOME/.config/chatgpt-cli"

rm -f "$BIN_DIR/gpt" "$BIN_DIR/gpt-gui"
rm -f "$APP_DIR/chatgpt-gui.desktop"

if [ "$1" == "--purge" ]; then
  rm -rf "$PREFIX_DIR"
  rm -rf "$STATE_DIR"
  rm -f "$SHARE_DIR/secret.enc"
  rm -f "$CONFIG_DIR/config"
  echo "Todos os dados e scripts foram removidos."
fi

echo "Desinstalação concluída."
