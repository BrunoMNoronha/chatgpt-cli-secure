#!/bin/bash
# Script para configurar chave da API OpenAI de forma segura.
set -e
SECRET_DIR="$HOME/.local/share/chatgpt-cli"
CONFIG_DIR="$HOME/.config/chatgpt-cli"
mkdir -p "$SECRET_DIR"
mkdir -p "$CONFIG_DIR"

echo "Configuração segura da chave API OpenAI."
read -rp "Digite sua OpenAI API key: " api_key
if [ -z "$api_key" ]; then
    echo "Chave vazia. Abortando."
    exit 1
fi

read -rsp "Crie uma senha mestra: " pass1; echo
read -rsp "Confirme a senha mestra: " pass2; echo
if [ "$pass1" != "$pass2" ]; then
    echo "As senhas não coincidem."
    exit 1
fi

echo -n "$api_key" | openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -md sha256 -salt -out "$SECRET_DIR/secret.enc" -pass pass:"$pass1"
chmod 600 "$SECRET_DIR/secret.enc"
echo "Chave criptografada e salva em $SECRET_DIR/secret.enc"
