#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import os
import sys
import json
import argparse
import subprocess
import getpass
import time
from pathlib import Path

CONFIG_PATH = Path.home() / '.config/chatgpt-cli/config'
SECRET_PATH = Path.home() / '.local/share/chatgpt-cli/secret.enc'
STATE_DIR = Path.home() / '.local/state/chatgpt-cli'
HISTORY_FILE = STATE_DIR / 'history.jsonl'
SESSIONS_DIR = STATE_DIR / 'sessions'

def read_config():
    config = {}
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    key, val = line.split('=',1)
                    val = val.strip().strip('"')
                    config[key] = val
        except Exception:
            pass
    return config

def get_api_key():
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        return api_key
    if not SECRET_PATH.exists():
        sys.stderr.write("Erro: chave API não configurada. Rode gpt-secure-setup.sh\n")
        sys.exit(1)
    try:
        password = os.environ.get('OPENAI_MASTER_PASSWORD')
        if not password:
            password = getpass.getpass("Senha mestra: ")
    except Exception:
        sys.stderr.write("Erro ao ler senha.\n")
        sys.exit(1)
    if not password:
        sys.stderr.write("Senha vazia.\n")
        sys.exit(1)
    try:
        result = subprocess.run(['openssl','enc','-d','-aes-256-cbc','-pbkdf2',
                                 '-iter','200000','-md','sha256','-salt',
                                 '-in', str(SECRET_PATH),
                                 '-pass', f'pass:{password}'],
                                check=True, capture_output=True)
        api_key = result.stdout.decode('utf-8').strip()
        if not api_key:
            raise RuntimeError
        return api_key
    except Exception:
        sys.stderr.write("Erro: falha ao descriptografar a chave. Senha incorreta?\n")
        sys.exit(1)

def load_session(name):
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    session_file = SESSIONS_DIR / f'{name}.json'
    if session_file.exists():
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                messages = json.load(f)
                if isinstance(messages, list):
                    return messages
        except Exception:
            pass
    return []

def save_session(name, messages):
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    session_file = SESSIONS_DIR / f'{name}.json'
    try:
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(messages, f)
    except Exception as e:
        sys.stderr.write(f"Não foi possível salvar a sessão: {e}\n")

def append_history(session, prompt, response):
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

def main():
    parser = argparse.ArgumentParser(description="CLI para ChatGPT com suporte a anexos e sessões.")
    parser.add_argument('prompt', nargs='?', help="Pergunta para o ChatGPT.")
    parser.add_argument('-f','--file', action='append', help="Adicionar anexo (PDF/TXT/IMG/Áudio).", default=[])
    parser.add_argument('--session', help="Nome da sessão para manter contexto.")
    parser.add_argument('--clear-session', help="Limpa a sessão especificada e sai.", default=None)
    parser.add_argument('--delete-files', action='store_true', help="Apagar arquivos enviados após resposta.")
    parser.add_argument('--model', help="Modelo a ser utilizado (sobrescreve config).")
    parser.add_argument('--temp', type=float, help="Temperatura (sobrescreve config).")
    args = parser.parse_args()

    config = read_config()
    model = args.model or os.environ.get('OPENAI_MODEL') or config.get('MODEL', 'gpt-4o-mini')
    temperature = args.temp or float(os.environ.get('OPENAI_TEMP') or config.get('TEMP', '0.7'))
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
    uploaded_ids = {}
    uploaded_file_ids_list = []
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
                    resp = requests.post('https://api.openai.com/v1/files', headers={'Authorization':'Bearer '+api_key}, data=data, files=files)
                if resp.status_code not in (200,201):
                    print(f"Falha ao enviar {path}: {resp.text}", file=sys.stderr)
                    sys.exit(1)
                file_id = resp.json().get('id')
                if not file_id:
                    print(f"Resposta inesperada ao enviar {path}", file=sys.stderr)
                    sys.exit(1)
                uploaded_ids[key] = file_id
                uploaded_file_ids_list.append(file_id)
            except Exception as e:
                print(f"Erro ao fazer upload de {path}: {e}", file=sys.stderr)
                sys.exit(1)

    response_text = ""
    try:
        if not attachments:
            messages = list(session_messages) if session_messages else []
            messages.append({"role":"user", "content":prompt})
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": True
            }
            headers = {'Authorization':'Bearer '+api_key, 'Content-Type':'application/json'}
            with requests.post('https://api.openai.com/v1/chat/completions', headers=headers, data=json.dumps(payload), stream=True) as r:
                if r.status_code != 200:
                    print(f"Erro {r.status_code}: {r.text}", file=sys.stderr)
                    sys.exit(1)
                for line in r.iter_lines():
                    if not line:
                        continue
                    decoded = line.decode('utf-8')
                    if decoded.startswith('data:'):
                        content = decoded[len('data:'):].strip()
                        if content == '[DONE]':
                            break
                        try:
                            event = json.loads(content)
                            delta = event['choices'][0].get('delta',{})
                            c = delta.get('content')
                            if c:
                                print(c, end='', flush=True)
                                response_text += c
                        except Exception:
                            pass
            print()
        else:
            input_obj = {"input_text": prompt}
            input_obj.update(uploaded_ids)
            payload = {
                "model": model,
                "input": input_obj,
                "temperature": temperature
            }
            headers = {'Authorization':'Bearer '+api_key, 'Content-Type':'application/json'}
            resp = requests.post('https://api.openai.com/v1/responses', headers=headers, data=json.dumps(payload))
            if resp.status_code not in (200,201):
                print(f"Erro {resp.status_code}: {resp.text}", file=sys.stderr)
                sys.exit(1)
            data = resp.json()
            if isinstance(data, dict):
                if 'output' in data:
                    response_text = data['output']
                elif 'choices' in data and len(data['choices']) > 0:
                    response_text = data['choices'][0].get('message','').get('content','')
                else:
                    response_text = str(data)
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
        for fid in uploaded_file_ids_list:
            try:
                requests.delete(f'https://api.openai.com/v1/files/{fid}', headers={'Authorization':'Bearer '+api_key})
            except Exception:
                pass

if __name__ == '__main__':
    main()
