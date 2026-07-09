# Plano de Integração Final — MCR Universal

## Objetivo
Conectar TUDO que ainda está solto ao `MCR.py`, eliminando 52 comandos externos e 53 módulos separados. Tudo vira MCR.

## Prioridade 🔥 Crítica (5 itens para criar ARQUIVOS)

| # | Componente | O que faz | Como integrar |
|---|-----------|-----------|---------------|
| 1 | **BlankFiller** | Gera esqueleto com @BLANK, preenche cada blank individualmente | Nova classe `MCRBlankFiller` no MCR.py |
| 2 | **NPC Generator** | Templates e geração de NPCs Lua | Nova classe `MCRNPCGerador` no MCR.py |
| 3 | **Lua Validator** | Valida sintaxe Lua, SQL injection, boas práticas | Nova classe `MCRLuaValidator` no MCR.py |
| 4 | **Reconstructor** | Monta resposta final de fragmentos | Nova classe `MCRReconstructor` no MCR.py |
| 5 | **Pos-Processamento** | Extrai código de resposta, salva arquivos | Nova classe `MCRPosProcessamento` no MCR.py |

## Prioridade 📗 Alta (5 itens para ORQUESTRAÇÃO)

| # | Componente | O que faz | Como integrar |
|---|-----------|-----------|---------------|
| 6 | **Orquestrador** | Motor de templates com fragmentação | Expansão do `MCRFerramentas` |
| 7 | **Context Enricher** | Cria contexto novo (não busca) | Método em `MCRMotor` |
| 8 | **Context Reinforcer** | Valida e reforça contexto | Método em `MCRMotor` |
| 9 | **Conselho** | Multi-personalidade | Classe `MCRConselho` |
| 10 | **Tree of Thought** | Raciocínio multi-branch | Classe `MCRToT` |

## O Fluxo Completo (após integração)

```
"crie um NPC ferreiro em Eridanus"
  │
  ├── MCRPiEngine.avaliar_entropia() → decide método
  ├── MCRFerramentas.executar() → orquestra
  │
  ├── 1. MCRFuel + MCRBusca → busca exemplos de NPCs .lua
  ├── 2. MCRMotor.alimentar() → aprende assinatura dos exemplos
  ├── 3. MCRNPCGerador.gerar() → gera nome + diálogo + estrutura
  ├── 4. MCRBlankFiller.preencher() → esqueleto + blanks
  ├── 5. MCRReconstructor.montar() → fragmentos → arquivo
  ├── 6. MCRLuaValidator.validar() → sintaxe + segurança
  ├── 7. MCRPosProcessamento.salvar() → arquivo .lua no disco
  │
  └── MCRSelfHeal.avaliar() → valida resultado final
```

## Arquivos a modificar

| Arquivo | Mudança |
|---------|---------|
| `E:\Projeto MCR\MCR.py` | Adicionar 5 classes novas (~800 linhas) |
| `E:\Projeto MCR\docs\PLANO_INTEGRACAO_FINAL.md` | Este plano |

## Classes novas (adicionar ao MCR.py)

| Classe | Linhas | Dependências |
|--------|--------|-------------|
| `MCRBlankFiller` | ~100 | MCRMotor |
| `MCRNPCGerador` | ~150 | MCRMotor, MCRBlankFiller |
| `MCRLuaValidator` | ~120 | stdlib `re` |
| `MCRReconstructor` | ~100 | MCRMotor, MCRFragmentador |
| `MCRPosProcessamento` | ~80 | stdlib `os` |
| **Total** | **~550** | **0 novas dependências** |
