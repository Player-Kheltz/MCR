# Troubleshooting MCR

> Problemas comuns e soluções. Consulte antes de debuggar do zero.

---

## Compilação

### "msbuild não encontrado" / "cl.exe não encontrado"
**Causa:** `vcvars64.bat` não foi executado antes do msbuild.
**Solução:** Use `auto.py compile --client` ou `--server` que já chama o vcvars.

### OTClient: "error MSB4126: configuração inválida"
**Causa:** Usou `otclient.sln` em vez de `otclient.vcxproj` direto.
**Solução:** Compile o `.vcxproj`, não o `.sln`. `auto.py` já faz isso.

### Canary: "fatal error C1083" (arquivo .h não encontrado)
**Causa:** Caminho de include faltando ou vcpkg não configurado.
**Solução:** Verificar se compilou antes com sucesso. Se sim, `git clean -xdf` e recompilar.

---

## LOS / Visão

### Cliente vê sprite mas não nome/HP/projéteis
**Causa provável:** `isSightClear` no cliente retorna `false` para a posição.
**Diagnóstico:**
1. Ativar logs `[MCR-DEBUG-CLIENT]` em `isSightClear` no cliente
2. Verificar qual etapa falhou: origin, ceiling, interpolation, ou same-floor
3. Comparar com servidor: ativar `[MCR-DEBUG-DOWN]` no servidor

**Causas comuns:**
- Ceiling check sem exclusão `hasFloorChange()` no cliente
- Same-floor Bresenham com caminho diferente entre servidor e cliente
- Cache sujo (`clearSightCache()`)

**Soluções:**
- Se o servidor retorna `true` e o cliente `false`, alinhar o DOWN case do cliente com o servidor
- Verificar `DevLog/Sistema Multi-Piso.md` seção 3

### BattleList: criatura aparece no mesmo piso atrás de parede
**Causa:** `isSightClear` retornando `true` incorretamente.
**Diagnóstico:** Verificar se o same-floor trace está ignorando tiles.
**Solução:** O cliente tenta ambos os sentidos do Bresenham. Se passar em um, ok. Se ambos passam, a parede não tem `BLOCK_PROJECTTILE`.

### Projétil não aparece visualmente
**Causa:** O servidor criou mas o cliente não desenha.
**Diagnóstico:** Verificar se a missile está em `g_map.getMissiles()`.
**Solução:** O desenho de projéteis NÃO verifica mais `isSightClear` — se o servidor enviou, o cliente desenha. Se não aparece, pode ser Z errado ou `getCurrentZ()` vs `getCurrentPosition()` inconsistente.

---

## Encoding

### "Não" aparece como "NÃ£o" no jogo
**Causa:** String C++ não passou por `toLatin1()` antes de `msg.addString()`.
**Solução:** Verificar `sendTextMessage` e `sendCancelMessage`.

### "Você" aparece como "Voc�" no console
**Causa:** Console do Windows em cp1252, arquivo salvo como UTF-8.
**Solução:** Normal. O arquivo está correto, o console que não exibe. Use `python` para ler o arquivo e verificar os bytes reais.

---

## SPA / Progressão

### "!testesistema" não retorna nada
**Causa:** Script não registrado ou erro de init.
**Solução:** Verificar `data-canary/scripts/MCR/SPA/core/` se os scripts existem. Verificar logs do servidor no startup.

### "Domínio não encontrado" no !testesistema
**Causa:** Domínio não populado no banco.
**Solução:** Executar INSERT na tabela `dominios` ou rodar `test.py --setup`.

---

## Bridge / Test Bot

### "!assistente" não funciona no jogo
**Causa:** `chat_bridge.lua` não registrado ou não carregado.
**Solução:** Verificar se o arquivo existe em `data-canary/scripts/MCR/core/chat_bridge.lua`. Verificar logs do servidor.

### bridge.py não vê mensagens
**Causa:** Caminho do `chat_in.txt` errado ou servidor não rodando.
**Solução:** Verificar se `data/logs/chat_in.txt` existe. Verificar se `TestChar` está online.
