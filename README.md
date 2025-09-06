# chatgpt-cli-secure v1.2.1

**chatgpt-cli-secure** é uma interface leve para ChatGPT sem navegador, oferecendo tanto linha de comando (CLI) quanto interface gráfica com Zenity (GUI). O foco está em usabilidade e segurança, armazenando a chave de API criptografada e proporcionando histórico, sessões e suporte a anexos.

## Recursos principais

- **CLI (`gpt`)**: 
  - Envia perguntas simples ou com anexos (PDF/TXT/IMG/Áudio).
  - Suporta streaming SSE quando não há anexos.
  - Possibilidade de manter contexto através de sessões (`--session` e `--clear-session`).
  - Remoção opcional de anexos após a resposta (`--delete-files`).
  - Configuração de modelo e temperatura via arquivo de configuração ou variáveis de ambiente.

- **GUI (`gpt-gui`)**:
  - Interface simples com Zenity para perguntas ao ChatGPT.
  - Seleção de modelo (pré-definidos ou personalizado) e opção de salvá-lo como padrão.
  - Seleção de arquivos anexos.
  - Botão para copiar a resposta ao clipboard (usa `xclip` ou `wl-clipboard` se disponíveis).
  - Gerenciamento de sessões (ativar/desativar e limpar).
  - Verificação e aplicação de atualizações (GitHub Releases ou URL configurada).
  - Configuração segura da chave API.

- **Segurança**:
  - A chave da API é armazenada criptografada em `~/.local/share/chatgpt-cli/secret.enc` usando AES‑256‑CBC, PBKDF2 com 200 000 iterações e SHA‑256.
  - Nunca é gravada em texto claro; é exportada para processos filhos via variável de ambiente apenas durante a execução.
  - O histórico e as sessões são armazenados respeitando os padrões XDG (em `~/.local/state/chatgpt-cli/`).

- **Sistema de atualização**:
  - `check-update.sh` verifica se há nova versão em GitHub ou em URL configurada, usando `curl -fI` para obter `ETag` ou `Last-Modified`. O token retornado é armazenado em `~/.local/state/chatgpt-cli/` e reutilizado em execuções futuras, baixando detalhes completos apenas quando houver mudança.
  - `update.sh` baixa e instala a atualização a partir de GitHub, URL ou arquivo local.
  - A GUI integra o fluxo de verificação/instalação de atualização.

## Dependências

- **Obrigatórias**: `bash`, `python3` com biblioteca `requests`, `openssl`, `curl`, `zenity`.
- **Opcionais** (para copiar texto no clipboard): `xclip` (Xorg) ou `wl-clipboard` (Wayland).
- Testado em sistemas Linux (Arch e derivados, mas compatível com qualquer distribuição que possua os utilitários acima).

## Instalação

1. Clone ou extraia este repositório e entre na pasta `chatgpt-cli-secure`.
2. (Opcional) exporte `PREFIX_DIR` para escolher outro destino de instalação. O padrão é `~/.local/share/chatgpt-cli`:
    ```bash
    export PREFIX_DIR=/caminho/desejado
    ```
3. Execute o script de instalação:
    ```bash
    bash install.sh
    ```
    O instalador copia os arquivos para `$PREFIX_DIR` (padrão `~/.local/share/chatgpt-cli/`), instala wrappers (`gpt` e `gpt-gui`) em `~/.local/bin/` e cria um atalho de desktop em `~/.local/share/applications/`. Também cria, caso não exista, o arquivo de configuração em `~/.config/chatgpt-cli/config`.

4. Configure a chave da OpenAI de forma segura executando:
    ```bash
    bash "$PREFIX_DIR/gpt-secure-setup.sh"
    ```
   Você informará sua API key e uma senha mestra. A chave ficará criptografada em `~/.local/share/chatgpt-cli/secret.enc`.

> **Nota:** Após a instalação, talvez seja necessário reindexar o menu de aplicativos (ou reiniciar o ambiente gráfico) para que o atalho apareça.

## Uso da CLI

### Envio básico
```bash
gpt "Quem descobriu o Brasil?"
```

### Com anexos
```bash
gpt -f resumo.pdf -f imagem.png "Faça um resumo com base nos arquivos"
```

### Sessões
- Criar/continuar uma sessão:
  ```bash
  gpt --session MinhaSessao "Pergunta inicial"
  ```
  As mensagens ficarão encadeadas dentro dessa sessão. Na GUI, ative/desative a sessão pelo menu.

- Limpar uma sessão:
  ```bash
  gpt --clear-session MinhaSessao
  ```

### Outras opções

- `--delete-files`: remove os arquivos enviados após a resposta.
- `--model` e `--temp`: sobrescrevem o modelo e a temperatura (caso não queira usar as definições do arquivo de configuração).
- `OPENAI_MODEL` e `OPENAI_TEMP`: variáveis de ambiente que também podem ser usadas para sobrescrever temporariamente as definições.

O histórico de interações (pergunta e resposta) é salvo em `~/.local/state/chatgpt-cli/history.jsonl`. Cada linha contém um JSON com `timestamp`, `session`, `prompt` e `response`.

## Uso da GUI

Execute:
```bash
gpt-gui
```

Na primeira execução, a interface pedirá sua senha mestra para descriptografar a chave. O menu inicial oferece:

1. **Perguntar ao ChatGPT** – abre um formulário para digitar a pergunta, selecionar o modelo e os anexos. Após a resposta, você pode copiá-la para o clipboard ou fazer outra pergunta.
2. **Checar atualização** – verifica se há nova versão disponível e oferece instalá-la.
3. **Ativar/Desativar contexto** – define ou remove o nome da sessão atual.
4. **Limpar sessão atual** – apaga a sessão ativa do disco.
5. **Configurar chave** – executa o script de configuração segura para alterar sua API key.
6. **Sair** – encerra a GUI.

A GUI utiliza `zenity --password` para a senha mestra, `zenity --list`/`--entry` para formulários e `zenity --info` para mostrar a resposta.

## Configuração

O arquivo `~/.config/chatgpt-cli/config` armazena variáveis:

```bash
MODEL="gpt-4o-mini"
TEMP="0.7"
UPDATE_URL=""   # Ex.: "https://meuservidor.com/updates"
GH_REPO=""      # Ex.: "usuario/repositorio" para releases do GitHub
```

- Cada linha deve seguir o formato `CHAVE=valor` e linhas iniciadas por `#` são ignoradas.
- Para o script `check-update.sh`, somente `UPDATE_URL` e `GH_REPO` são interpretadas; variáveis não reconhecidas são ignoradas.
- Entradas malformadas fazem o script abortar, evitando execução acidental de comandos.

- **MODEL**: modelo padrão usado pela CLI/GUI (pode ser alterado no menu da GUI ou manualmente).
- **TEMP**: temperatura padrão (0 a 1).
- **UPDATE_URL**: URL onde deve existir um `version.txt` e um pacote `chatgpt-cli-secure.tar.gz`.
- **GH_REPO**: repositório do GitHub para verificar releases. Se ambos forem preenchidos, o GitHub tem prioridade.

Edite esse arquivo para apontar para sua fonte de atualização preferida.

## Atualização

- Verifique manualmente com:
  ```bash
  bash "$PREFIX_DIR/check-update.sh"
  ```
- Atualize via linha de comando:
  ```bash
  # A partir do GitHub
  bash "$PREFIX_DIR/update.sh" --from-github

  # A partir de uma URL
  bash "$PREFIX_DIR/update.sh" --from-url https://meuservidor.com/chatgpt-cli-secure.tar.gz

  # Usando um arquivo local
  bash "$PREFIX_DIR/update.sh" --from-file /caminho/para/pacote.tar.gz
  ```

A GUI automatiza esse processo quando seleciona **Checar atualização**.

## Desinstalação

Para remover os wrappers e o atalho de desktop:
```bash
bash uninstall.sh
```

Para remover completamente também os arquivos em `$PREFIX_DIR`, histórico, configuração e a chave, use a opção `--purge`:
```bash
bash uninstall.sh --purge
```

## Observações de segurança

- A chave da API é criptografada via `openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -md sha256 -salt` e nunca é salva em texto plano.
- A GUI exporta a chave para os processos `gpt` usando uma variável de ambiente apenas no momento da execução (`env OPENAI_API_KEY=... command`). Após a chamada, o script remove (`unset`) a variável de seu próprio ambiente.
- Para maior segurança, **não compartilhe sua senha mestra** e proteja seu diretório pessoal.
- Outros processos rodando com o mesmo usuário podem, em teoria, listar variáveis de ambiente de processos filhos enquanto eles estão ativos. Evite executar múltiplas instâncias simultâneas e mantenha o sistema atualizado.
- Se desejar trocar de modelo ou temperatura temporariamente, defina `OPENAI_MODEL` e/ou `OPENAI_TEMP` somente no momento da execução e não deixe essas variáveis permanentemente expostas.

## Teste funcional

1. **Instalação**:
   ```bash
   git clone <repositório> chatgpt-cli-secure
   cd chatgpt-cli-secure
   bash install.sh
   ```
2. **Configurar chave**:
   ```bash
   bash "$PREFIX_DIR/gpt-secure-setup.sh"
   ```
   Siga as instruções para inserir a API key e a senha mestra.

3. **Testar CLI**:
   ```bash
   gpt "Diga olá"
   ```
   Deve exibir a resposta do ChatGPT.

4. **Testar anexos**:
   ```bash
   gpt -f /caminho/exemplo.pdf -f /caminho/figura.png "Resuma o conteúdo e descreva a imagem" --delete-files
   ```
   O comando deve enviar os arquivos, mostrar a resposta e remover os arquivos enviados após a conclusão.

5. **Testar sessão**:
   ```bash
   gpt --session teste "Quem foi Albert Einstein?"
   gpt --session teste "E quais foram suas principais contribuições?"
   gpt --clear-session teste
   ```
   As duas primeiras perguntas compartilham contexto, e a última remove a sessão.

6. **Testar GUI**:
   - Execute `gpt-gui` e insira a senha mestra.
   - Selecione **Perguntar ao ChatGPT**, digite uma pergunta e escolha o modelo.
   - Anexe arquivos se desejar, copie a resposta e faça outra pergunta.
   - Teste ativar uma sessão pelo menu, depois limpar a sessão.
   - Teste **Checar atualização** (configure `UPDATE_URL` ou `GH_REPO` com URLs fictícias para verificar a mensagem).

7. **Teste de atualização via terminal**:
   - Edite `~/.config/chatgpt-cli/config` definindo `GH_REPO="usuario/repositorio-falso"` ou `UPDATE_URL="https://exemplo.com/update"` e execute:
     ```bash
     bash "$PREFIX_DIR/check-update.sh"
     ```
     Observe a saída. Para testar o fluxo de instalação sem internet, baixe ou crie um tarball falso contendo este projeto, depois use:
     ```bash
     bash "$PREFIX_DIR/update.sh" --from-file chatgpt-cli-secure.tar.gz
     ```

Siga estes passos para validar todas as funcionalidades.
