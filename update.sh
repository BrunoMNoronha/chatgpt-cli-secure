#!/bin/bash
# Baixa e instala atualizações do chatgpt-cli-secure.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

# download_and_verify(url: string, dest: string) -> None
download_and_verify() {
  local url="$1"
  local dest="$2"
  local hash_file="${dest}.sha256"

  curl -fL --retry 3 --show-error -o "$dest" "$url"
  curl -fL --retry 3 --show-error -o "$hash_file" "${url}.sha256"
  if ! echo "$(cat "$hash_file")  $dest" | sha256sum -c -; then
    echo "Falha na verificação do hash SHA256." >&2
    exit 1
  fi
}

usage() {
  echo "Uso: $0 --from-github | --from-url <URL> | --from-file <arquivo> [hash]"
  exit 1
}

action="${1:-}"
if [ "$action" == "--from-github" ]; then
  info=$("$SCRIPT_DIR/check-update.sh" --machine-read)
  has=$(echo "$info" | grep '^HAS_UPDATE=' | cut -d= -f2)
  url=$(echo "$info" | grep '^NEW_URL=' | cut -d= -f2)
  if [ "$has" != "1" ]; then
    echo "Nenhuma atualização disponível."
    exit 0
  fi
  file="$tmp/package.tar.gz"
  echo "Baixando pacote de atualização..."
  download_and_verify "$url" "$file"
  tar -xf "$file" -C "$tmp"
  dir=$(find "$tmp" -maxdepth 1 -mindepth 1 -type d | head -n1)
  if [ ! -f "$dir/install.sh" ]; then
    echo "Pacote inválido."
    exit 1
  fi
  bash "$dir/install.sh"
  echo "Atualização concluída."
elif [ "$action" == "--from-url" ]; then
  url="${2:-}"
  [ -z "$url" ] && usage
  file="$tmp/package.tar.gz"
  echo "Baixando pacote..."
  download_and_verify "$url" "$file"
  tar -xf "$file" -C "$tmp"
  dir=$(find "$tmp" -maxdepth 1 -mindepth 1 -type d | head -n1)
  bash "$dir/install.sh"
  echo "Atualização concluída."
elif [ "$action" == "--from-file" ]; then
  file="${2:-}"
  hash="${3:-}"
  [ -z "$file" ] && usage
  if [ -n "${hash:-}" ]; then
    if ! echo "$hash  $file" | sha256sum -c -; then
      echo "Falha na verificação do hash SHA256." >&2
      exit 1
    fi
  elif [ -f "${file}.sha256" ]; then
    if ! echo "$(cat "${file}.sha256")  $file" | sha256sum -c -; then
      echo "Falha na verificação do hash SHA256." >&2
      exit 1
    fi
  else
    echo "Aviso: hash SHA256 não fornecido; prosseguindo sem verificação." >&2
  fi
  tar -xf "$file" -C "$tmp"
  dir=$(find "$tmp" -maxdepth 1 -mindepth 1 -type d | head -n1)
  bash "$dir/install.sh"
  echo "Atualização concluída."
else
  usage
fi
