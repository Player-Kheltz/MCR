# Lesson: Recuperação de Conversas no OpenCode

## Data: 2026-06-24

## Problema
Usuário fechou a conversa do OpenCode acidentalmente e perdeu o histórico.

## Solução
O OpenCode CLI (versao 1.17.9) possui sistema de sessoes que salva automaticamente todas as conversas.

### Comandos Uteis

```powershell
# Listar todas as sessoes (mais recentes primeiro)
opencode session list

# Continuar a ultima sessao
opencode -c

# Continuar uma sessao especifica
opencode -s ses_<ID>

# Exportar sessao como JSON (para backup/consulta)
opencode export ses_<ID>

# Fork de sessao (cria copia para continuar sem modificar original)
opencode -s ses_<ID> --fork

# Importar sessao salva
opencode import <arquivo.json>
```

### Local de Armazenamento
As sessoes ficam em `~/.config/opencode/` (config) e `~/.local/share/opencode/` (dados).

### Estrutura do Export
O JSON exportado contem:
- `info`: metadados (id, titulo, modelo, tokens, custo, tempo)
- `messages`: array de mensagens, cada uma com:
  - `info.role`: "user" ou "assistant"
  - `info.agent`: "build", "plan", "compaction"
  - `parts[]`: array de partes da mensagem (texto, ferramentas, raciocinio, etc)

### Tipos de Partes
| Part Type | Conteudo |
|-----------|----------|
| `text` | Texto da mensagem |
| `tool` | Chamada de ferramenta (grep, read, write, etc) |
| `reasoning` | Raciocinio interno do modelo |
| `step-start` / `step-finish` | Marcadores de passo |
| `compaction` | Resumo automatico |
| `patch` | Diferenca de codigo |

### Dica Importante
- Sempre atualizar `Pendencias.md` ao final de cada sessao para preservar contexto
- Se estiver chegando no limite de contexto, atualizar Pendencias.md com resumo
- O comando `opencode session list` mostra titulo e horario - ajuda a identificar a sessao correta
