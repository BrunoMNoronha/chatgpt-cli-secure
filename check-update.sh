#!/bin/bash
# Verifica se há nova versão disponível via GitHub ou URL.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOCAL_VERSION=$(cat "$SCRIPT_DIR/version.txt")
CONFIG="$HOME/.config/chatgpt-cli/config"
ALLOWED_VARS="GH_REPO UPDATE_URL"
STATE_DIR="$HOME/.local/state/chatgpt-cli"
GH_CACHE="$STATE_DIR/github_release.cache"
URL_CACHE="$STATE_DIR/url_release.cache"

mkdir -p "$STATE_DIR"

if [ -f "$CONFIG" ]; then
  # Loop simples; usar `grep` ou `awk` seria mais performático, mas a leitura linha a linha
  # facilita a validação e manutenção.
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      ''|\#*) continue ;;
    esac
    if [[ $line =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      key="${BASH_REMATCH[1]}"
      value="${BASH_REMATCH[2]}"
      if [[ " $ALLOWED_VARS " == *" $key "* ]]; then
        export "$key=$value"
      fi
    else
      echo "Linha malformada em $CONFIG: $line" >&2
      exit 1
    fi
  done < "$CONFIG"
fi

HAS_UPDATE=0
NEW_VERSION=""
NEW_URL=""
HUMAN_MSG=""

if [ -n "$GH_REPO" ]; then
  # `curl -fI` obtém apenas cabeçalhos, economizando dados.
  headers=$(curl -fIsL "https://api.github.com/repos/$GH_REPO/releases/latest" 2>/dev/null)
  if [ -n "$headers" ]; then
    etag=$(grep -i '^ETag:' <<<"$headers" | tr -d '\r' | awk '{print $2}' | tr -d '"')
    last_mod=$(grep -i '^Last-Modified:' <<<"$headers" | cut -d' ' -f2- | tr -d '\r')
    token=${etag:-$last_mod}
    cache_token=""
    if [ -f "$GH_CACHE" ]; then
      cache_token=$(grep '^ETAG=' "$GH_CACHE" | cut -d= -f2-)
    fi
    if [ "$token" != "$cache_token" ] || [ ! -f "$GH_CACHE" ]; then
      resp=$(curl -fsSL "https://api.github.com/repos/$GH_REPO/releases/latest" 2>/dev/null)
      if command -v jq >/dev/null 2>&1; then
        tag=$(jq -r '.tag_name // empty' <<<"$resp")
        url=$(jq -r '.assets[]?.browser_download_url // empty' <<<"$resp" | grep 'chatgpt-cli-secure' | head -n1)
      else
        echo "Aviso: jq não encontrado; a extração será menos robusta. Instale jq para melhor desempenho." >&2
        tag=$(echo "$resp" | grep -m1 '"tag_name"' | sed -E 's/.*"tag_name":\s*"v?([^\"]+)".*/\1/')
        url=$(echo "$resp" | grep -o '"browser_download_url":[^,]*' | sed -E 's/.*"browser_download_url":\s*"([^\"]+)".*/\1/' | grep 'chatgpt-cli-secure' | head -n1)
      fi
      if [ -n "$tag" ] && [ -n "$url" ]; then
        printf 'ETAG=%s\nTAG=%s\nURL=%s\n' "$token" "$tag" "$url" > "$GH_CACHE"
      fi
    else
      tag=$(grep '^TAG=' "$GH_CACHE" | cut -d= -f2-)
      url=$(grep '^URL=' "$GH_CACHE" | cut -d= -f2-)
    fi
    if [ -n "$tag" ] && [ -n "$url" ]; then
      latest=$(printf '%s\n%s\n' "$tag" "$LOCAL_VERSION" | sort -V | tail -n1)
      if [ "$latest" != "$LOCAL_VERSION" ]; then
        HAS_UPDATE=1
        NEW_VERSION="$tag"
        NEW_URL="$url"
      fi
    fi
    HUMAN_MSG="Verificação via GitHub."
  else
    HUMAN_MSG="Erro ao consultar GitHub."
  fi
elif [ -n "$UPDATE_URL" ]; then
  # Padrão semelhante para URL direta usando `Last-Modified`.
  headers=$(curl -fIsL "$UPDATE_URL/version.txt" 2>/dev/null)
  if [ -n "$headers" ]; then
    last_mod=$(grep -i '^Last-Modified:' <<<"$headers" | cut -d' ' -f2- | tr -d '\r')
    token=$last_mod
    cache_token=""
    if [ -f "$URL_CACHE" ]; then
      cache_token=$(grep '^ETAG=' "$URL_CACHE" | cut -d= -f2-)
    fi
    if [ "$token" != "$cache_token" ] || [ ! -f "$URL_CACHE" ]; then
      tag=$(curl -fsSL "$UPDATE_URL/version.txt" 2>/dev/null | tr -d ' \t\n\r')
      url="$UPDATE_URL/chatgpt-cli-secure.tar.gz"
      if [ -n "$tag" ]; then
        printf 'ETAG=%s\nTAG=%s\nURL=%s\n' "$token" "$tag" "$url" > "$URL_CACHE"
      fi
    else
      tag=$(grep '^TAG=' "$URL_CACHE" | cut -d= -f2-)
      url=$(grep '^URL=' "$URL_CACHE" | cut -d= -f2-)
    fi
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
    HUMAN_MSG="Erro ao obter cabeçalhos em URL."
  fi
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
