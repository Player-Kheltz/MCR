# Plano: Sistema EMERGIR — Reconhecimento Automático de Padrões Emergentes

> **Conceito:** Máquinas são boas em reconhecer padrões. Padrões existem em absolutamente TUDO.
> Às vezes X + Y não dá XY. Dá Z — algo NOVO que não estava nem em X nem em Y.
> O sistema só precisa IDENTIFICAR que Z emergiu.

## Fluxo

```
executar() → ... → APRENDER → FLUSH → EMERGIR → return
                                          │
                                     ┌────┴────┐
                                     │ a cada 5│
                                     │ execuções│
                                     └────┬────┘
                                          ▼
 ┌──────────────────────────────────────────────┐
 │  EMERGIR                                     │
 │                                              │
 │  1. _amostrar_topicos_distantes()            │
 │     → 2-3 lessons de ctxs DIFERENTES         │
 │                                              │
 │  2. _gerar_fingerprint_combinacao()          │
 │     → já tentamos essa combinação? SKIP      │
 │                                              │
 │  3. _gerar_pergunta_emergente()              │
 │     → Decider: "E se X + Y?"                │
 │                                              │
 │  4. IA pensa (temp=0.8)                      │
 │     → sistema responde criativamente         │
 │                                              │
 │  5. _autoavaliar_padrao_novo()               │
 │     → "Isso é um padrão novo ou ruído?"      │
 │       ┌────┴────┐                            │
 │     SIM        NÃO                           │
 │       │          │                           │
 │   Aprende Z   descarta (mas                  │
 │   no KG       guarda fingerprint             │
 │   ctx=        pra não repetir)               │
 │   'emergente'                                │
 └──────────────────────────────────────────────┘
```

## Métodos

### `_amostrar_topicos_distantes(n=3)`
Amostra N lessons de contextos DIFERENTES no KG.

### `_gerar_fingerprint_combinacao(topicos)`
Gera hash MD5 único para uma combinação de tópicos (ordem-independente).

### `_gerar_pergunta_emergente(topicos)`
Decider.extrair_json() gera "E se X com Y?" combinando topicos de forma surpreendente.

### `_processar_emergencia()`
Método principal. Chamado automaticamente a cada 5 execuções.
Orquestra: amostrar → fingerprint → pergunta → pensar → avaliar → aprender.

### `_autoavaliar_padrao_novo(pergunta, resposta, topicos)`
FAST decide se o insight é genuinamente novo ou ruído.
Qualquer resposta pode ser válida — o que importa é se REVELA conexão não-óbvia.

## Arquivos Modificados

- `master_agent.py`: +5 imports, +1 campo __init__, +1 chamada, +5 métodos (~137 linhas)
- `conselho.py` (opcional): +1 arquétipo "criativo" (~10 linhas)

## Contexto: Sessão 6 (2026-06-28)

Este plano foi concebido durante a Sessão 6 do Projeto MCR, após a implementação do
sistema de Identidade Dinâmica (AGENT_IDENTITY.md + V12 + FAST).

A ideia central veio do usuário: "a máquina pensar por si só" — reconhecer padrões
automaticamente, combinando conceitos distantes do KG, e aprendendo os resultados
emergentes (Z) sem supervisão externa.

Difere de um comando "criar_conceito" porque é um MECANISMO INTERNO que roda
silenciosamente em background, não uma resposta a uma solicitação do usuário.
