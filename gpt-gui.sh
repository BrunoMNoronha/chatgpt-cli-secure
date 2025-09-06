#!/bin/bash
# GUI para ChatGPT usando Zenity.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.config/chatgpt-cli"
SECRET_FILE="$HOME/.local/share/chatgpt-cli/secret.enc"

if [ ! -f "$SECRET_FILE" ]; then
    zenity --error --title="Erro" --text="Chave da API não encontrada. Execute gpt-secure-setup.sh primeiro."
    exit 1
fi

MASTER_PASS=$(zenity --password --title="ChatGPT CLI Secure" --text="Digite a senha mestra para desbloquear a chave:")
if [ $? -ne 0 ]; then exit 0; fi
if [ -z "$MASTER_PASS" ]; then
    zenity --error --text="Senha vazia."
    exit 1
fi

OPENAI_API_KEY=$(printf '%s' "$MASTER_PASS" | openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -md sha256 -salt -in "$SECRET_FILE" -pass stdin 2>/dev/null || true)
unset MASTER_PASS
if [ -z "$OPENAI_API_KEY" ]; then
    zenity --error --text="Falha ao descriptografar a chave. Senha incorreta?"
    exit 1
fi

if [ -f "$CONFIG_DIR/config" ]; then
    . "$CONFIG_DIR/config"
fi
MODEL=${MODEL:-gpt-4o-mini}
TEMP=${TEMP:-0.7}

SESSION_ACTIVE=0
SESSION_NAME=""

while true; do
    selection=$(zenity --list --radiolist --title="ChatGPT CLI Secure" --text="Selecione uma ação:" \
        --column="" --column="Ação" \
        TRUE "Perguntar ao ChatGPT" \
        FALSE "Checar atualização" \
        FALSE "Ativar/Desativar contexto" \
        FALSE "Limpar sessão atual" \
        FALSE "Configurar chave" \
        FALSE "Sair" \
        --height=300 --width=450)

    if [ $? -ne 0 ]; then break; fi

    case "$selection" in
        "Perguntar ao ChatGPT")
            prompt=$(zenity --entry --title="Pergunta" --text="Digite sua pergunta:")
            if [ $? -ne 0 ] || [ -z "$prompt" ]; then continue; fi
            model_select=$(zenity --list --radiolist --title="Escolher Modelo" --text="Selecione o modelo:" \
                --column="" --column="Modelo" \
                TRUE "$MODEL" \
                FALSE "gpt-4o-mini" \
                FALSE "gpt-4o" \
                FALSE "o3-mini" \
                FALSE "gpt-4.1-mini" \
                FALSE "gpt-4.1" \
                FALSE "Personalizado..." \
                --height=350 --width=500)
            if [ $? -ne 0 ]; then continue; fi
            if [ "$model_select" = "Personalizado..." ]; then
                model_select=$(zenity --entry --title="Modelo Personalizado" --text="Digite o identificador do modelo:")
                if [ $? -ne 0 ] || [ -z "$model_select" ]; then continue; fi
            fi
            if zenity --question --title="Salvar Modelo" --text="Salvar $model_select como padrão?"; then
                mkdir -p "$CONFIG_DIR"
                if [ -f "$CONFIG_DIR/config" ]; then
                    if grep -q '^MODEL=' "$CONFIG_DIR/config"; then
                        sed -i "s/^MODEL=.*/MODEL=\"$model_select\"/" "$CONFIG_DIR/config"
                    else
                        echo "MODEL=\"$model_select\"" >> "$CONFIG_DIR/config"
                    fi
                else
                    echo "MODEL=\"$model_select\"" > "$CONFIG_DIR/config"
                fi
                MODEL="$model_select"
            fi
            attachments=$(zenity --file-selection --multiple --separator="|" --title="Selecionar anexos (opcional)" 2>/dev/null || true)
            cmd=(env OPENAI_API_KEY="$OPENAI_API_KEY" OPENAI_MODEL="$model_select" OPENAI_TEMP="$TEMP" "$SCRIPT_DIR/wrappers/gpt")
            if [ "$SESSION_ACTIVE" -eq 1 ] && [ -n "$SESSION_NAME" ]; then
                cmd+=( --session "$SESSION_NAME" )
            fi
            if [ -n "$attachments" ]; then
                IFS='|' read -ra files <<< "$attachments"
                for f in "${files[@]}"; do
                    cmd+=( -f "$f" )
                done
            fi
            cmd+=( "$prompt" )
            response="$(${cmd[@]} 2>&1)"
            if [ $? -ne 0 ]; then
                zenity --error --title="Erro" --text="$response"
                continue
            fi
            zenity --info --title="Resposta" --width=600 --height=400 --text="$response"
            if zenity --question --title="Copiar" --text="Deseja copiar a resposta para o clipboard?"; then
                if command -v xclip >/dev/null 2>&1; then
                    printf "%s" "$response" | xclip -selection clipboard
                elif command -v wl-copy >/dev/null 2>&1; then
                    printf "%s" "$response" | wl-copy
                else
                    zenity --warning --title="Aviso" --text="Nenhum utilitário de clipboard encontrado (xclip ou wl-clipboard)."
                fi
            fi
            if zenity --question --title="Outra pergunta" --text="Deseja fazer outra pergunta?"; then
                continue
            fi
            ;;
        "Checar atualização")
            out=$("$SCRIPT_DIR/check-update.sh" --machine-read 2>/dev/null || true)
            HAS=$(echo "$out" | grep '^HAS_UPDATE=' | cut -d= -f2)
            NEW_VERSION=$(echo "$out" | grep '^NEW_VERSION=' | cut -d= -f2)
            NEW_URL=$(echo "$out" | grep '^NEW_URL=' | cut -d= -f2)
            HUMAN=$(echo "$out" | grep '^__HUMAN__' | cut -d= -f2-)
            if [ "$HAS" = "1" ]; then
                if zenity --question --title="Atualização Disponível" --text="Nova versão $NEW_VERSION disponível.\nDeseja atualizar agora?"; then
                    "$SCRIPT_DIR/update.sh" --from-url "$NEW_URL"
                fi
            else
                zenity --info --title="Atualização" --text="Nenhuma atualização disponível.\n$HUMAN"
            fi
            ;;
        "Ativar/Desativar contexto")
            if [ "$SESSION_ACTIVE" -eq 1 ]; then
                if zenity --question --title="Desativar contexto" --text="Desativar a sessão '$SESSION_NAME'?"; then
                    SESSION_ACTIVE=0
                    SESSION_NAME=""
                fi
            else
                sess=$(zenity --entry --title="Ativar contexto" --text="Nome da sessão:")
                if [ $? -eq 0 ] && [ -n "$sess" ]; then
                    SESSION_NAME="$sess"
                    SESSION_ACTIVE=1
                fi
            fi
            ;;
        "Limpar sessão atual")
            if [ "$SESSION_ACTIVE" -eq 1 ]; then
                if zenity --question --title="Limpar sessão" --text="Deseja limpar a sessão '$SESSION_NAME'?"; then
                    "$SCRIPT_DIR/wrappers/gpt" --clear-session "$SESSION_NAME"
                    SESSION_ACTIVE=0
                    SESSION_NAME=""
                fi
            else
                zenity --warning --title="Aviso" --text="Nenhuma sessão ativa."
            fi
            ;;
        "Configurar chave")
            "$SCRIPT_DIR/gpt-secure-setup.sh"
            MASTER_PASS=$(zenity --password --title="ChatGPT CLI Secure" --text="Digite a senha mestra para desbloquear a chave:")
            if [ $? -ne 0 ] || [ -z "$MASTER_PASS" ]; then
                zenity --error --text="Senha vazia."
                continue
            fi
            OPENAI_API_KEY=$(printf '%s' "$MASTER_PASS" | openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -md sha256 -salt -in "$SECRET_FILE" -pass stdin 2>/dev/null || true)
            unset MASTER_PASS
            ;;
        "Sair")
            break
            ;;
    esac
 done
 
 unset OPENAI_API_KEY
 exit 0
