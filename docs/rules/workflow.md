# Workflow.md — Fluxo de Trabalho MCR

> Parte do sistema modular `docs/rules/`. Consulte `../AGENTS.md` para visão geral.

## Central de Comandos: `auto.py`

| Comando | Descrição |
|---|---|
| `compile --client / --server / --both` | Compila OTClient e/ou Canary |
| `status` | Git status + diffs + pendências |
| `verify` | Status + doc-sync + pergunta commit |
| `commit "mensagem"` | Git commit com mensagem |
| `sync` | Regenera CATALOG.md |
| `session` | Mostra session.json |
| `server start / stop / restart` | Controla Canary.exe |
| `up` | Sobe tudo (server + bridge + watchdog) |
| `doctor` | Diagnóstico e sugestões |

## Operações em Massa → Script Python

Toda alteração repetitiva em 3+ arquivos DEVE ser feita por script Python:
1. Crie o script em `docs/Localizador Projeto MCR/Server (CodigoFonte)/`
2. Execute com `--dry-run` e revise o log
3. O assistente REVISA e AUTORIZA sozinho — só reporta ao usuário se for alteração crítica
4. Apenas execute para valer após auto-autorização

## Docs Antes de Código

Antes de qualquer alteração estrutural, leia `docs/CATALOG.md` para identificar os docs relevantes. Se os docs estiverem desatualizados, atualize-os primeiro.

## Alinhe Design Antes de Codificar

Para funcionalidades novas:
1. Entenda o requisito
2. Leia os docs relevantes (via CATALOG.md)
3. Proponha abordagem
4. Receba feedback
5. Implemente

## Validação Antes de Subir

Sempre que alterar código:
1. Compile os projetos afetados
2. Verifique funcionamento
3. Só então atualize docs para refletir o que realmente foi feito
4. Rode `scripts/doc-sync.py` se criou/alterou docs
5. Commit

Nunca gere falsas informações ou reescritas desnecessárias nos docs.

## Commits Pequenos e Descritivos

```
git add <arquivos>
git commit -m "tipo(escopo): descrição"
git push origin main
```

- Uma alteração de cada vez por commit
- Não misture correções
- Se houver alteração de comportamento, atualize o(s) doc(s) correspondente(s) no mesmo commit

## Delegue Exploração Pesada

Para tarefas que exijam ler 3+ arquivos grandes, grep em 5+ diretórios ou explorar código desconhecido, DELEGUE para um task agent (`subagent_type: explore`). Mantenha o contexto principal enxuto.

## Limpeza de Processos — REGRA ABSOLUTA

### ⚠️ Problema
Processos do servidor (`canary-sln.exe`) e bridge (`python.exe`) ficam rodando em segundo
plano entre sessões SEM o assistente ou o usuário saberem. Isso já causou:
- Crash do OpenCode/Bun por acúmulo de memória
- Servidor rodando por 1h+ sem necessidade
- Bridge consumindo recursos do modelo Ollama
- Portas 7171-7173 ocupadas (bloqueia restart limpo)
- Usuário logar no OTClient por engano (servidor ainda vivo)

### ✅ Checklist Obrigatório

**No INÍCIO de toda resposta (antes de QUALQUER outra ação):**
```python
import subprocess, os
subprocess.run(["taskkill", "/f", "/im", "canary-sln.exe"], capture_output=True)
subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True)
for f in [".bridge_pid", ".watchdog_pid"]:
    if os.path.exists(f): os.remove(f)
```

**Ao FINAL de toda resposta:**
1. Verificar se servidor foi desligado (`python scripts/server_manager.py status`)
2. Verificar se bridge foi desligado
3. Remover arquivos PID órfãos

### Regra de Ouro
> Se o assistente iniciou um processo, ele DEVE matá-lo antes de encerrar.
> Se o assistente encontrou um processo rodando, ele DEVE matá-lo ao terminar.
> O servidor e bridge SÓ devem rodar quando explicitamente solicitado pelo usuário
> para TESTE. Fora isso, TUDO desligado.

### Uso durante a sessão
- `auto.py server stop` para limpar
- `server_manager.py kill` como alternativa
- NUNCA usar `Start-Process` do PowerShell (sempre Python `subprocess.Popen` com PID tracking)

## Troubleshooting

Problemas comuns (LOS, encoding, compilação, bridge) estão em `docs/TROUBLESHOOTING.md`. Consulte antes de investigar do zero.
