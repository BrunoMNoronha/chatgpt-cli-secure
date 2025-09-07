#!/usr/bin/env python3
"""Configura a chave API de forma simples usando ``save_api_key``."""

from getpass import getpass

from chatgpt_cli.secure_storage import KeyLocation, save_api_key


def main() -> None:
    print("Configuração da chave API OpenAI.")
    api_key: str = getpass("Digite sua OpenAI API key: ")
    if not api_key:
        print("Chave vazia. Abortando.")
        return
    save_api_key(api_key)
    print(f"Chave salva em {KeyLocation().path}")


if __name__ == "__main__":
    main()
