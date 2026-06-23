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

### OTClient (VS 2026)
```cmd
"${VS2026}\\VC\\Auxiliary\\Build\\vcvars64.bat" && msbuild "${MCR}\\OTClient\\vc17\\otclient.vcxproj" /p:Configuration=OpenGL /p:Platform=x64 /t:Build /m"
```

### Canary Server (VS 2022)
```cmd
"${VS2022}\\VC\\Auxiliary\\Build\\vcvars64.bat" && msbuild "${MCR}\\Canary\\vcproj\\canary.vcxproj" /p:Configuration=Release /p:Platform=x64 /t:Build /m"
```

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
