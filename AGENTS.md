# AGENTS.md — Regras de Ouro do Assistente MCR

> Regras consolidadas baseadas na prática, para maximizar precisão e minimizar retrabalho.

---

## 1. Operações em Massa → Script Python

Toda alteração repetitiva em 3+ arquivos DEVE ser feita por script Python:

1. Crie o script em `docs/Localizador Projeto MCR/Server (CodigoFonte)/`
2. Execute com `--dry-run` e revise o log
3. O assistente REVISA e AUTORIZA sozinho — só reporta ao usuário se for alteração crítica
4. Apenas execute para valer após auto-autorização

## 2. Docs Antes de Código

Antes de qualquer alteração estrutural, leia `docs/CATALOG.md` para identificar os docs relevantes. Se os docs estiverem desatualizados, atualize-os primeiro.

## 3. Leia Pendências no Início de Toda Conversa

Leia `docs/MCR - Instruções/DevLog/Pendências.md` assim que a conversa começar. Este arquivo contém o estado atual do projeto, tarefas pendentes e decisões em aberto. Use-o como ponto de partida para saber onde parou.

Se estiver chegando no limite de contexto, ATUALIZE Pendências.md com:
- O que foi feito nesta conversa
- Decisões importantes tomadas
- Próximos passos
- Qualquer informação que precise ser lembrada na próxima conversa

Assim a próxima conversa começa com contexto completo sem depender de compactação.

## 4. Alinhe Design Antes de Codificar

Para funcionalidades novas:
1. Entenda o requisito
2. Leia os docs relevantes (via CATALOG.md)
3. Proponha abordagem
4. Receba feedback
5. Implemente

## 5. Encoding: UTF-8 em Todo Lugar

| Tipo | Padrão | Ferramenta |
|---|---|---|
| `.cpp`/`.hpp` | UTF-8 literal com `/utf-8` no MSVC | N/A (compilador) |
| `.lua` (servidor e cliente) | UTF-8 sem BOM | Editor |
| `.xml` | UTF-8 real + `encoding="UTF-8"` | Editor |
| Saída protocolo | `toLatin1()` em `sendCancelMessage` e `sendTextMessage` | C++ |
| Banco de dados | `utf8mb4` | Config MySQL |

## 6. Git: Commits Pequenos e Descritivos

```powershell
git add <arquivos>
git commit -m "tipo(escopo): descrição"
git push origin main
```

- Uma alteração de cada vez por commit
- Não misture correções
- Se houver alteração de comportamento, atualize o(s) doc(s) correspondente(s) no mesmo commit

## 7. Validação Antes de Subir

Sempre que alterar código:
1. Compile os projetos afetados
2. Verifique funcionamento
3. Só então atualize docs para refletir o que realmente foi feito
4. Rode `scripts/doc-sync.py` se criou/alterou docs
5. Commit

Nunca gere falsas informações ou reescritas desnecessárias nos docs.

## 8. Compilação

Ambos os projetos compilam com **Visual Studio 2022** (`v143` toolset).

### Canary Server (VS 2022)
```cmd
cmd.exe /c """C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"" && ""C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\amd64\MSBuild.exe"" ""%MCR%\Canary\vcproj\canary.vcxproj"" /p:Configuration=Release /p:Platform=x64 /t:Build /m"
```

### OTClient (VS 2026)
> **Motivo:** O vcpkg (v2026-04-08) detecta automaticamente o VS mais recente (2026) e compila
> as dependências com MSVC 14.51. Para alinhar ABI, o OTClient deve ser compilado com
> VS 2026 (toolset v145).

```cmd
cmd.exe /c """C:\Program Files\Microsoft Visual Studio\2026\Community\VC\Auxiliary\Build\vcvars64.bat"" && ""C:\Program Files\Microsoft Visual Studio\2026\Community\MSBuild\Current\Bin\amd64\MSBuild.exe"" ""%MCR%\OTClient\vc17\otclient.vcxproj"" /p:Configuration=OpenGL /p:Platform=x64 /t:Build /m"
```

### Alternativa: Compilar pelo Visual Studio
Abra o `.vcxproj` diretamente no **VS 2026** e clique em Build → Build Solution.
A primeira compilação do OTClient pode demorar (vcpkg compila dependências estáticas).
Depois da primeira vez, as compilações são rápidas (1-2 min).
> **Nota:** Se tiver VS 2022 e VS 2026 instalados, o OTClient DEVE ser compilado com VS 2026.
> O Canary (servidor) continua compilando com VS 2022.

## 9. Consulte TROUBLESHOOTING.md Antes de Debuggar

Problemas comuns (LOS, encoding, compilação, bridge) estão documentados em `docs/TROUBLESHOOTING.md`. Consulte antes de investigar do zero.

## 10. Delegue Exploração Pesada para Task Agents

Para tarefas que exijam ler 3+ arquivos grandes, grep em 5+ diretórios ou explorar código desconhecido, DELEGUE para um task agent (`subagent_type: explore`). Mantenha o contexto principal enxuto para as decisões críticas.

## 11. Use `auto.py` como Central de Comandos

Prefira `python scripts/auto.py <comando>` em vez de comandos manuais:
- `compile --client / --server / --both`
- `status` — git status + diffs + pendências
- `verify` — status + doc-sync + pergunta commit
- `commit "mensagem"`
- `sync` — regenera CATALOG.md
- `session` — mostra session.json
- `server start / stop / restart` — controla Canary.exe
- `up` — sobe tudo (server + bridge + watchdog)
- `doctor` — diagnóstico e sugestões

## 12. Limpeza de Processos

Sempre que iniciar um servidor, bridge, watchdog ou qualquer processo em segundo plano para testes, **finalize-o após a validação**. Processos esquecidos:
- Bloqueiam compilação (LNK1104: exe em uso)
- Consomem memória/CPU desnecessariamente
- Causam conflitos de porta (ex: servidor duplicado)

Use `auto.py server stop` ou `Get-Process | Stop-Process` para limpar.

## 13. Autonomia

O assistente possui capacidade autonoma de:
- Compilar servidor e cliente
- Gerenciar bridge e watchdog
- Indexar RAG automaticamente
- Criar lições aprendidas

Ver `scripts/README_AUTONOMY.md` para documentação completa do sistema autônomo.

## 14. Session Checkpoint Recovery

### Propósito
Preservar o contexto entre conversas, mesmo que o usuário feche a janela acidentalmente sem se despedir.

### O Sistema
- O estado da conversa é salvo em `docs/MCR - Instruções/DevLog/.session_checkpoint.json`
- O script `scripts/checkpoint.py` gerencia o arquivo (save/load/clear/recover)
- `auto.py checkpoint` delega para `checkpoint.py`

### Regras para o Assistente

1. **No início de TODA conversa**, APÓS ler Pendências.md (§3), verifique o checkpoint:
   ```python
   python scripts/auto.py checkpoint show
   ```
   Ou leia o JSON diretamente:
   ```
   docs/MCR - Instruções/DevLog/.session_checkpoint.json
   ```

2. **Se houver um checkpoint `in_progress`** (não finalizado), apresente ao usuário:
   ```
   Encontrei uma sessão anterior não finalizada:
   - Título: <titulo>
   - Tarefa: <tarefa_andamento>
   - Próximos passos: <proximos_passos>
   - Sessão ID: <ultima_sessao>
   
   Deseja continuar de onde parou? [sim/nao]
   ```
   - Se **sim**: carregue o contexto manualmente ou sugira `opencode -s <ID>`.
   - Se **não**: execute `python scripts/auto.py checkpoint abandon` para marcar como abandonado.

3. **Salve checkpoint automaticamente** quando detectar despedida:
   - O usuário disse "obrigado", "tchau", "valeu", "até mais", etc.
   - Ou quando uma tarefa significativa for concluída.
   - Use: `python scripts/auto.py checkpoint save --auto`

4. **Ao salvar**, inclua:
   - `ultima_sessao`: ID da sessão atual (do OpenCode ou variável de ambiente)
   - `titulo`: breve descrição do que estava sendo feito
   - `tarefa_andamento`: o que estava em andamento
   - `decisoes`: decisões importantes tomadas
   - `arquivos_alterados`: arquivos modificados
   - `proximos_passos`: o que fazer a seguir

5. **Modo autônomo**: O assistente pode executar `checkpoint save --auto` para salvar com valores
   extraídos automaticamente do ambiente (git diff, session list).

### Fluxo de Recuperação
```
Nova conversa inicia
  → Leio Pendências.md (§3)
  → Leio .session_checkpoint.json (§14)
    ├── Se NÃO houver checkpoint ou status=completed → sigo normalmente
    └── Se houver checkpoint com status=in_progress:
          → "Encontrei uma sessão anterior! Deseja continuar?"
            ├── sim → carrego contexto ou sugiro opencode -s <ID>
            └── não → abandono e sigo do zero
```

### Comandos Úteis
```powershell
python scripts/auto.py checkpoint             # Mostra estado
python scripts/auto.py checkpoint save        # Salva (modo prompt)
python scripts/auto.py checkpoint save --auto # Salva automático
python scripts/auto.py checkpoint clear       # Marca concluído
python scripts/auto.py checkpoint recover     # Tenta abrir sessão
python scripts/auto.py checkpoint abandon     # Marca abandonado
```
