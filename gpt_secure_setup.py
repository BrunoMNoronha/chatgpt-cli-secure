#!/usr/bin/env python3
"""Configura a chave API de forma segura usando ``save_api_key``."""

from getpass import getpass

from chatgpt_cli.secure_storage import KeyLocation, save_api_key


def main() -> None:
    print("Configuração segura da chave API OpenAI.")
    api_key: str = getpass("Digite sua OpenAI API key: ")
    if not api_key:
        print("Chave vazia. Abortando.")
        return
    pass1: str = getpass("Crie uma senha mestra: ")
    pass2: str = getpass("Confirme a senha mestra: ")
    if not pass1:
        print("Senha vazia. Abortando.")
        return
    if pass1 != pass2:
        print("As senhas não coincidem.")
        return
    save_api_key(api_key, pass1)
    print(f"Chave criptografada e salva em {KeyLocation().path}")


if __name__ == "__main__":
    main()
