# Auto-Avaliacao MCR — Processo de Melhoria Continua do DevIA

## Ciclo de Auto-Aperfeicoamento

Sempre que alguem (voce, eu, ou o proprio DevIA) identificar uma melhoria:

1. **REGISTRE** no Knowledge Graph (`python mcr_devia.py ensinar "problema" "causa" "solucao" "ctx"`)
2. **IMPLEMENTE** se for codigo (via mcr_scriptbuilder.py ou diretamente)
3. **TESTE** no training_ground ou teste_cego
4. **INTEGRE** ao uso real (fora do sandbox)
5. **COMEMORE** (ele aprendeu algo novo)

## Areas de Melhoria Prioritaria

- Detectar indentacao mista (tabs + espacos)
- Detectar IDs duplicados entre arquivos
- Detectar NPCs sem saudacao (ja faz!)
- Detectar monstros sem loot (ja faz!)
- Melhorar auto-reparo (aprender formato antes de editar)

## Regra de Ouro

> Se o MCR-DevIA ja sabe fazer, DELEGUE a ele.
> Se ele nao sabe, ENSINE uma vez. Depois delegue.
> Se ele erra, CORRIJA uma vez. Depois delegue.

O ciclo nunca para. O DevIA so melhora.
