#!/bin/bash
# Script para configurar chave da API OpenAI de forma segura.
set -e

# Resolve HOME para o usuário correto (suporta sudo)
REAL_USER="${SUDO_USER:-$(id -un)}"
USER_HOME="$(getent passwd "$REAL_USER" | cut -d: -f6)"

SECRET_DIR="$USER_HOME/.local/share/chatgpt-cli"
CONFIG_DIR="$USER_HOME/.config/chatgpt-cli"
mkdir -p "$SECRET_DIR"
mkdir -p "$CONFIG_DIR"

echo "Configuração segura da chave API OpenAI."
read -rsp "Digite sua OpenAI API key: " api_key; echo
if [ -z "$api_key" ]; then
    echo "Chave vazia. Abortando."
    exit 1
fi

read -rsp "Crie uma senha mestra: " pass1; echo
read -rsp "Confirme a senha mestra: " pass2; echo
if [ -z "$pass1" ]; then
    echo "Senha vazia. Abortando."
    exit 1
fi
if [ "$pass1" != "$pass2" ]; then
    echo "As senhas não coincidem."
    exit 1
fi

if ! command -v openssl >/dev/null 2>&1; then
    echo "openssl não encontrado. Instale-o e tente novamente."
    exit 1
fi

if ! echo -n "$api_key" | openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -md sha256 -salt -out "$SECRET_DIR/secret.enc" -pass pass:"$pass1"; then
    echo "Falha ao criptografar."
    exit 1
fi
chmod 600 "$SECRET_DIR/secret.enc"
unset api_key pass1 pass2
echo "Chave criptografada e salva em $SECRET_DIR/secret.enc"
