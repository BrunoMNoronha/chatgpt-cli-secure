# -*- coding: utf-8 -*-

import argparse
import getpass
import json
import os
import sys
import time
from functools import lru_cache
from configparser import ConfigParser, MissingSectionHeaderError, ParsingError
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from io import StringIO

import requests
from requests import Response
from requests.exceptions import RequestException
from .secure_storage import KeyLocation, load_api_key

CONFIG_PATH = Path.home() / '.config/chatgpt-cli/config'
STATE_DIR = Path.home() / '.local/state/chatgpt-cli'
HISTORY_FILE = STATE_DIR / 'history.jsonl'
SESSIONS_DIR = STATE_DIR / 'sessions'
DEFAULT_REQUEST_TIMEOUT: float = 30.0


@dataclass
class Config:
    """Configuração tipada para o cliente.

    Utiliza *dataclass* para reduzir boilerplate e tornar os campos explícitos.
    Uma alternativa ainda mais performática seria empregar ``__slots__`` no
    dataclass, porém à custa de menor flexibilidade.
    """

    model: str
    temperature: float


def read_config() -> Dict[str, str]:
    """Lê arquivo de configuração do usuário usando ``ConfigParser``.

    Utiliza o padrão *EAFP* ("Easier to Ask Forgiveness than Permission") para
    tentativa de leitura e converte o conteúdo em ``dict``. Uma alternativa mais
    performática seria o parse manual linha a linha, como antes, porém menos
    robusta.
    """
    parser = ConfigParser()
    parser.optionxform = str  # preserva capitalização das chaves
    if not CONFIG_PATH.exists():
        return {}
    try:
        content: str = CONFIG_PATH.read_text(encoding="utf-8")
        parser.read_string("[DEFAULT]\n" + content)
    except (OSError, MissingSectionHeaderError, ParsingError):
        return {}
    return {k: v.strip().strip('"') for k, v in parser["DEFAULT"].items()}


def load_env_config(config_dict: Optional[Dict[str, str]] = None) -> Config:
    """Constrói ``Config`` a partir de variáveis de ambiente.

    Aplica o padrão *Factory Method* para isolar a lógica de conversão e
    validação. Uma alternativa mais performática seria acessar ``os.environ``
    diretamente com chaves obrigatórias, evitando lookups repetidos.
    """
    cfg = config_dict or read_config()
    model: str = os.environ.get("OPENAI_MODEL") or cfg.get("MODEL", "gpt-4o-mini")
    temp_raw = os.environ.get("OPENAI_TEMP") or cfg.get("TEMP", "0.7")
    try:
        temperature = float(temp_raw)
    except ValueError as exc:
        raise ValueError("Temperatura inválida") from exc
    if not 0.0 <= temperature <= 2.0:
        raise ValueError("Temperatura deve estar entre 0 e 2")
    return Config(model=model, temperature=temperature)

@lru_cache(maxsize=1)
def get_api_key() -> str:
    """Obtém a chave da API OpenAI.

    Emprega o padrão *Singleton* via ``lru_cache`` para armazenar a chave
    após a primeira descriptografia, evitando invocações repetidas da rotina
    de segurança. Uma alternativa ainda mais performática seria utilizar uma
    variável global para cache manual, eliminando a sobrecarga do decorator,
    porém dificultaria a limpeza em testes.

    Aplica também o padrão *Strategy* ao delegar a descriptografia para
    ``load_api_key``.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return api_key
    location: KeyLocation = KeyLocation()
    if not location.path.exists():
        sys.stderr.write(
            "Erro: chave API não configurada. Rode gpt-secure-setup.py\n"
        )
        sys.exit(1)
    try:
        password = os.environ.pop("OPENAI_MASTER_PASSWORD", None)
        if not password:
            password = getpass.getpass("Senha mestra: " )
    except Exception:
        sys.stderr.write("Erro ao ler senha.\n")
        sys.exit(1)
    if not password:
        sys.stderr.write("Senha vazia.\n")
        sys.exit(1)
    try:
        return load_api_key(password, loc=location)
    except Exception:
        sys.stderr.write(
            "Erro: falha ao descriptografar a chave. Senha incorreta?\n"
        )
        sys.exit(1)

def extract_text_from_data(data: Dict[str, Any]) -> str:
    """Extrai texto da resposta de acordo com a especificação mais recente."""
    if "output" in data and isinstance(data["output"], list):
        parts: List[str] = []
        for item in data["output"]:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        parts.append(part.get("text", ""))
            elif isinstance(content, str):
                parts.append(content)
        return "".join(parts)
    if "choices" in data and data["choices"]:
        choice = data["choices"][0]
        if isinstance(choice, dict):
            return (
                choice.get("message", {})
                .get("content", "")
            )
    return data.get("output_text", "")


def stream_chat_completion(
    api_key: str,
    messages: List[Dict[str, Any]],
    config: Config,
    timeout: float,
) -> str:
    """Realiza streaming de tokens SSE para chat completions.

    Emprega o padrão *Context Manager* para garantir o fechamento seguro da
    requisição e utiliza ``StringIO`` para evitar concatenações repetidas de
    strings. Uma alternativa igualmente performática seria acumular tokens em
    uma lista e aplicar ``"".join`` ao final.
    """
    payload: Dict[str, Any] = {
        "model": config.model,
        "messages": messages,
        "temperature": config.temperature,
        "stream": True,
    }
    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
    }
    buffer: StringIO = StringIO()
    try:
        with requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            stream=True,
            timeout=timeout,
        ) as r:
            if r.status_code != 200:
                sys.stderr.write(f"Erro {r.status_code}: {r.text}\n")
                sys.exit(1)
            for line in r.iter_lines():
                if not line:
                    continue
                decoded = line.decode("utf-8")
                if decoded.startswith("data:"):
                    content = decoded[len("data:") :].strip()
                    if content == "[DONE]":
                        break
                    try:
                        event = json.loads(content)
                    except Exception:
                        continue
                    delta = event.get("choices", [{}])[0].get("delta", {})
                    c = delta.get("content")
                    if c:
                        print(c, end="", flush=True)
                        buffer.write(c)
            print()
    except RequestException as e:
        sys.stderr.write(f"Erro de conexão: {e}\n")
        sys.exit(1)
    return buffer.getvalue()


def delete_uploaded_files(
    file_ids: List[str], api_key: str, timeout: float
) -> None:
    """Remove arquivos enviados aguardando resposta do servidor."""
    for fid in file_ids:
        try:
            resp: Response = requests.delete(
                f"https://api.openai.com/v1/files/{fid}",
                headers={"Authorization": "Bearer " + api_key},
                timeout=timeout,
            )
            if resp.status_code not in (200, 202, 204):
                sys.stderr.write(
                    f"Erro ao remover arquivo {fid}: {resp.status_code} {resp.text}\n"
                )
        except RequestException as e:
            sys.stderr.write(f"Erro ao remover arquivo {fid}: {e}\n")
        time.sleep(0.5)

def load_session(name: str) -> List[Dict[str, Any]]:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    session_file = SESSIONS_DIR / f'{name}.json'
    if session_file.exists():
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                messages = json.load(f)
                if isinstance(messages, list):
                    return messages  # type: ignore[return-value]
        except Exception:
            pass
    return []

def save_session(name: str, messages: List[Dict[str, Any]]) -> None:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    session_file = SESSIONS_DIR / f'{name}.json'
    try:
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(messages, f)
    except Exception as e:
        sys.stderr.write(f"Não foi possível salvar a sessão: {e}\n")

def append_history(session: Optional[str], prompt: str, response: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
            record = {
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S'),
                "session": session,
                "prompt": prompt,
                "response": response
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        sys.stderr.write(f"Não foi possível gravar histórico: {e}\n")

def main() -> None:
    parser = argparse.ArgumentParser(description="CLI para ChatGPT com suporte a anexos e sessões.")
    parser.add_argument('prompt', nargs='?', help="Pergunta para o ChatGPT.")
    parser.add_argument('-f','--file', action='append', help="Adicionar anexo (PDF/TXT/IMG/Áudio).", default=[])
    parser.add_argument('--session', help="Nome da sessão para manter contexto.")
    parser.add_argument('--clear-session', help="Limpa a sessão especificada e sai.", default=None)
    parser.add_argument('--delete-files', action='store_true', help="Apagar arquivos enviados após resposta.")
    parser.add_argument('--model', help="Modelo a ser utilizado (sobrescreve config).")
    parser.add_argument('--temp', type=float, help="Temperatura (sobrescreve config).")
    args = parser.parse_args()

    config_raw = read_config()
    config = load_env_config(config_raw)
    if args.model or args.temp is not None:
        config = Config(
            model=args.model or config.model,
            temperature=args.temp if args.temp is not None else config.temperature,
        )
    try:
        request_timeout: float = float(
            config_raw.get('REQUEST_TIMEOUT', DEFAULT_REQUEST_TIMEOUT)
        )
    except ValueError:
        request_timeout = DEFAULT_REQUEST_TIMEOUT
    prompt = args.prompt

    if args.clear-session:
        name = args.clear-session
        session_file = SESSIONS_DIR / f'{name}.json'
        if session_file.exists():
            try:
                os.remove(session_file)
                print(f"Sessão '{name}' removida.")
            except Exception as e:
                print(f"Falha ao remover sessão: {e}")
        else:
            print(f"Sessão '{name}' não encontrada.")
        sys.exit(0)

    if not prompt and not args.file:
        parser.print_help()
        sys.exit(1)

    api_key = get_api_key()

    session_messages = []
    if args.session:
        session_messages = load_session(args.session)

    attachments = args.file or []
    uploaded_ids: Dict[str, str] = {}
    uploaded_file_ids_list: List[str] = []
    if attachments:
        for path in attachments:
            p = Path(path)
            if not p.exists():
                print(f"Arquivo não encontrado: {path}", file=sys.stderr)
                sys.exit(1)
            ext = p.suffix.lower()
            if ext in ['.png','.jpg','.jpeg','.gif','.bmp','.webp']:
                key = 'input_image'
            elif ext in ['.mp3','.wav','.ogg','.flac','.m4a']:
                key = 'input_audio'
            else:
                key = 'input_file'
            if key in uploaded_ids:
                print(f"Aviso: mais de um arquivo para {key}. Apenas o primeiro será usado.", file=sys.stderr)
                continue
            try:
                with open(p, 'rb') as f:
                    files = {'file': (p.name, f)}
                    data = {'purpose': 'assistants'}
                    resp = requests.post(
                        'https://api.openai.com/v1/files',
                        headers={'Authorization': 'Bearer ' + api_key},
                        data=data,
                        files=files,
                        timeout=request_timeout,
                    )
            except RequestException as e:
                print(f"Erro de conexão ao enviar {path}: {e}", file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                print(f"Erro ao fazer upload de {path}: {e}", file=sys.stderr)
                sys.exit(1)
            if resp.status_code not in (200, 201):
                print(f"Falha ao enviar {path}: {resp.text}", file=sys.stderr)
                sys.exit(1)
            file_id = resp.json().get('id')
            if not file_id:
                print(f"Resposta inesperada ao enviar {path}", file=sys.stderr)
                sys.exit(1)
            uploaded_ids[key] = file_id
            uploaded_file_ids_list.append(file_id)

    response_text = ""
    try:
        if not attachments:
            messages = list(session_messages) if session_messages else []
            messages.append({"role": "user", "content": prompt})
            response_text = stream_chat_completion(
                api_key, messages, config, request_timeout
            )
        else:
            input_obj = {"input_text": prompt}
            input_obj.update(uploaded_ids)
            payload = {
                "model": config.model,
                "input": input_obj,
                "temperature": config.temperature,
            }
            headers = {
                "Authorization": "Bearer " + api_key,
                "Content-Type": "application/json",
            }
            try:
                resp = requests.post(
                    "https://api.openai.com/v1/responses",
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=request_timeout,
                )
            except RequestException as e:
                print(f"Erro de conexão: {e}", file=sys.stderr)
                sys.exit(1)
            if resp.status_code not in (200, 201):
                print(f"Erro {resp.status_code}: {resp.text}", file=sys.stderr)
                sys.exit(1)
            data = resp.json()
            if isinstance(data, dict):
                response_text = extract_text_from_data(data)
            print(response_text)
    except KeyboardInterrupt:
        print("\nInterrompido.")
        sys.exit(1)

    if args.session:
        session_messages.append({"role":"user","content": prompt})
        session_messages.append({"role":"assistant","content": response_text})
        save_session(args.session, session_messages)
    append_history(args.session, prompt, response_text)

    if attachments and args.delete_files:
        delete_uploaded_files(uploaded_file_ids_list, api_key, request_timeout)

if __name__ == '__main__':
    main()
