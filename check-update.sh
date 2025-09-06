#!/bin/bash
# Verifica se há nova versão disponível via GitHub ou URL.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOCAL_VERSION=$(cat "$SCRIPT_DIR/version.txt")
CONFIG="$HOME/.config/chatgpt-cli/config"
[ -f "$CONFIG" ] && source "$CONFIG"

HAS_UPDATE=0
NEW_VERSION=""
NEW_URL=""
HUMAN_MSG=""

if [ -n "$GH_REPO" ]; then
  resp=$(curl -s "https://api.github.com/repos/$GH_REPO/releases/latest")
  tag=$(echo "$resp" | grep -m1 '"tag_name"' | sed -E 's/.*"tag_name":\s*"v?([^\"]+)".*/\1/')
  url=$(echo "$resp" | grep -o '"browser_download_url":[^,]*' | sed -E 's/.*"browser_download_url":\s*"([^\"]+)".*/\1/' | grep 'chatgpt-cli-secure' | head -n1)
  if [ -n "$tag" ]; then
    latest=$(printf '%s\n%s\n' "$tag" "$LOCAL_VERSION" | sort -V | tail -n1)
    if [ "$latest" != "$LOCAL_VERSION" ]; then
      HAS_UPDATE=1
      NEW_VERSION="$tag"
      NEW_URL="$url"
    fi
  fi
  HUMAN_MSG="Verificação via GitHub."
elif [ -n "$UPDATE_URL" ]; then
  tag=$(curl -s "$UPDATE_URL/version.txt" | tr -d ' \t\n\r')
  url="$UPDATE_URL/chatgpt-cli-secure.tar.gz"
  if [ -n "$tag" ]; then
    latest=$(printf '%s\n%s\n' "$tag" "$LOCAL_VERSION" | sort -V | tail -n1)
    if [ "$latest" != "$LOCAL_VERSION" ]; then
      HAS_UPDATE=1
      NEW_VERSION="$tag"
      NEW_URL="$url"
    fi
  fi
  HUMAN_MSG="Verificação via URL."
else
  HUMAN_MSG="Nenhuma origem de atualização configurada."
fi

if [ "$1" == "--machine-read" ]; then
  echo "HAS_UPDATE=$HAS_UPDATE"
  echo "NEW_VERSION=$NEW_VERSION"
  echo "NEW_URL=$NEW_URL"
  echo "__HUMAN__=$HUMAN_MSG"
else
  if [ "$HAS_UPDATE" -eq 1 ]; then
    echo "Nova versão $NEW_VERSION disponível."
    echo "URL: $NEW_URL"
  else
    echo "Você está na versão mais recente ($LOCAL_VERSION)."
  fi
  echo "$HUMAN_MSG"
fi
