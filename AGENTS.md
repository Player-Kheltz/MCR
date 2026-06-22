# AGENTS.md — Regras de Ouro do Assistente MCR

> Regras consolidadas baseadas na prática, para maximizar precisão e minimizar retrabalho.

---

## 1. Operações em Massa → Script Python

Toda alteração repetitiva em 3+ arquivos DEVE ser feita por script Python:

1. Crie o script em `docs/Localizador Projeto MCR/Server (CodigoFonte)/`
2. Execute com `--dry-run` e revise o log
3. O assistente REVISA e AUTORIZA sozinho — só reporta ao usuário se for alteração crítica
4. Apenas execute para valer após auto-autorização

## 2. Docs Primeiro, Código Depois

Antes de qualquer alteração estrutural, leia `docs/MCR - Instruções/`. Se os docs estiverem desatualizados, atualize-os primeiro.

## 3. Alinhe Design Antes de Codificar

Para funcionalidades novas:
1. Entenda o requisito → 2. Proponha abordagem → 3. Receba feedback → 4. Implemente

## 4. Encoding: UTF-8 em Todo Lugar

| Tipo | Padrão | Ferramenta |
|---|---|---|
| `.cpp`/`.hpp` | UTF-8 literal com `/utf-8` no MSVC | N/A (compilador) |
| `.lua` (servidor e cliente) | UTF-8 sem BOM | Editor |
| `.xml` | UTF-8 real + `encoding="UTF-8"` | Editor |
| Saída protocolo | `toLatin1()` em `sendCancelMessage` e `sendTextMessage` | C++ |
| Banco de dados | `utf8mb4` | Config MySQL |

## 5. Reutilize Antes de Criar

Verifique se o projeto já tem:
- TalkAction similar (ex: `!escudeiro` para inventário)
- API C++ existente (ex: `player:addMount`, `Mount:getClientId`)
- Sistema de parcel/transferência de itens

## 6. Git: Commits Pequenos e Descritivos

Após cada alteração funcional completa:
```powershell
git add <arquivos>
git commit -m "tipo(escopo): descrição"
git push origin main
```

## 7. Uma Alteração de Cada Vez por Commit

Não misture correções. Cada commit tem um propósito claro.

## 8. Documentação é Código

Mantenha `docs/MCR - Instruções/` atualizado. Se você alterou o comportamento, atualize o doc correspondente no mesmo commit.
