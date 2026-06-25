# Checkpoint.md — Session Checkpoint Recovery MCR

> Parte do sistema modular `docs/rules/`. Consulte `../AGENTS.md` para visão geral.

## Propósito

Preservar o contexto entre conversas, mesmo que o usuário feche a janela acidentalmente.

## O Sistema

- Estado salvo em `docs/MCR - Instruções/DevLog/.session_checkpoint.json`
- `scripts/checkpoint.py` gerencia o arquivo (save/load/clear/recover)
- `auto.py checkpoint` delega para `checkpoint.py`

## Regras

1. **No início de TODA conversa**, APÓS ler Pendências.md, verifique:
   ```
   python scripts/auto.py checkpoint show
   ```

2. **Se houver checkpoint `in_progress`**, apresente:
   ```
   Encontrei uma sessão anterior não finalizada:
   - Título: <titulo>
   - Tarefa: <tarefa_andamento>
   - Próximos passos: <proximos_passos>
   Deseja continuar de onde parou? [sim/nao]
   ```
   - **sim**: carregue contexto ou `opencode -s <ID>`
   - **não**: `python scripts/auto.py checkpoint abandon`

3. **Salve ao detectar despedida** ou tarefa concluída:
   ```powershell
   python scripts/auto.py checkpoint save --auto
   ```

4. **Ao salvar**, inclua: `ultima_sessao`, `titulo`, `tarefa_andamento`, `decisoes`, `arquivos_alterados`, `proximos_passos`

## Fluxo de Recuperação

```
Nova conversa
  → Leio Pendencias.md
  → Leio .session_checkpoint.json
    ├── Sem checkpoint ou completed → sigo
    └── in_progress → "Continuar?"
          ├── sim → carrego contexto
          └── não → abandono
```

## Comandos

```powershell
python scripts/auto.py checkpoint             # Mostra estado
python scripts/auto.py checkpoint save        # Salva (modo prompt)
python scripts/auto.py checkpoint save --auto # Salva automático
python scripts/auto.py checkpoint clear       # Marca concluído
python scripts/auto.py checkpoint recover     # Tenta abrir sessão
python scripts/auto.py checkpoint abandon     # Marca abandonado
```
