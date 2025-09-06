#!/bin/bash
# Baixa e instala atualizações do chatgpt-cli-secure.
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

usage() {
  echo "Uso: $0 --from-github | --from-url <URL> | --from-file <arquivo>"
  exit 1
}

if [ "$1" == "--from-github" ]; then
  info=$("$SCRIPT_DIR/check-update.sh" --machine-read)
  has=$(echo "$info" | grep '^HAS_UPDATE=' | cut -d= -f2)
  url=$(echo "$info" | grep '^NEW_URL=' | cut -d= -f2)
  if [ "$has" != "1" ]; then
    echo "Nenhuma atualização disponível."
    exit 0
  fi
  tmp=$(mktemp -d)
  file="$tmp/package.tar.gz"
  echo "Baixando pacote de atualização..."
  curl -L -o "$file" "$url"
  tar -xf "$file" -C "$tmp"
  dir=$(find "$tmp" -maxdepth 1 -mindepth 1 -type d | head -n1)
  if [ ! -f "$dir/install.sh" ]; then
    echo "Pacote inválido."
    exit 1
  fi
  bash "$dir/install.sh"
  echo "Atualização concluída."
elif [ "$1" == "--from-url" ]; then
  url="$2"
  [ -z "$url" ] && usage
  tmp=$(mktemp -d)
  file="$tmp/package.tar.gz"
  echo "Baixando pacote..."
  curl -L -o "$file" "$url"
  tar -xf "$file" -C "$tmp"
  dir=$(find "$tmp" -maxdepth 1 -mindepth 1 -type d | head -n1)
  bash "$dir/install.sh"
  echo "Atualização concluída."
elif [ "$1" == "--from-file" ]; then
  file="$2"
  [ -z "$file" ] && usage
  tmp=$(mktemp -d)
  tar -xf "$file" -C "$tmp"
  dir=$(find "$tmp" -maxdepth 1 -mindepth 1 -type d | head -n1)
  bash "$dir/install.sh"
  echo "Atualização concluída."
else
  usage
fi
