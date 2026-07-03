# PatternEngine Gatekeeper — Validação Universal de Reparos

**Data**: 2026-06-30
**Status**: Implementado
**Arquivo**: `scripts/mcr_devia/modulos/util.py` (`reparar_com_validacao()`)

---

## Problema

Toda ferramenta de reparo do MCR-DevIA modifica código sem validar se a mudança realmente melhorou ou piorou o código.

## Solução

Wrapper universal `reparar_com_validacao()` que:
1. Antes: calcula fingerprint + eixo do código original
2. Depois: calcula fingerprint + eixo do código gerado
3. Gatekeeper: só aceita se similaridade >= 0.7 E eixo não caiu
4. Caso contrário, REVERTE automaticamente

## Arquivos modificados

| Arquivo | Mudança | Linhas |
|---------|---------|:------:|
| `modulos/util.py` | +`reparar_com_validacao()` wrapper | ~20 |
| `modulos/diagnostic_engine.py` `remediar()` | Usar `reparar_com_validacao()` | ~8 |
| `modulos/master_agent.py` `_gerar_e_aplicar()` | Usar `reparar_com_validacao()` | ~5 |
| `modulos/self_study.py` `_auto_repair()` | Verificar except já tem corpo | ~3 |
| **Total** | | **~36 linhas** |

## Como testar

```bash
mcr diagnosticar
# Deve mostrar 0 erros de compilacao
```
