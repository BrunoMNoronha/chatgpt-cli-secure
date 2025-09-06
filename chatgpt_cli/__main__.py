from __future__ import annotations

"""Allow module execution via ``python -m chatgpt_cli``.

The design follows the *Facade* pattern by exposing a simple entry point.
Uma alternativa ligeiramente mais performática seria invocar diretamente
``chatgpt_cli.main`` sem importação adicional, porém a diferença é mínima.
"""

from typing import NoReturn

from . import main


def run() -> NoReturn:
    """Execute ``chatgpt_cli.main``.

    Encapsular a chamada em função dedicada permite extensão futura sem
    alterar o ponto de entrada. Um caminho mais rápido seria chamar ``main``
    diretamente, evitando a chamada extra.
    """
    main()
    raise SystemExit(0)


if __name__ == "__main__":
    run()
