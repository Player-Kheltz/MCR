# SESSAO 2026-07-20 — AUTO-OBSERVACAO DA COLONIA

## Resumo

Investigamos se uma **colônia de MCRs** pode exibir auto-observação e
autopreservação sem tokens injetados nem random. Três experimentos:

### v4.5: Museu dos Mortos (aprendizado vicário)
- Especialistas vivos consultam `P(morte | features)` de mortos
- **60 modulações** ocorreram, mas **0 mudança de trajetória**
- Modulação passiva (confiança pós-decisão) não altera comportamento
- Conclusão: o fluxo de informação existe, mas a alavanca (delegação) faltava

### v5: Delegação como Ação
- `misto_bib_trol` delegou 59× — aprendeu a "passar a bola"
- **Razão caiu de 2.6x para 1.4x** — delegação virou muleta
- **Trigger `P(morte) > 0.05` hardcoded** — viola Pilar 1
- Insight crítico: **a conexão causal entre delegar e sobreviver NÃO está
  disponível para o coupling individual**. A morte remove o aprendiz.
  Auto-preservação só emerge na **ecologia** (entre couplings), não dentro.

### v6: Heartbeat na Colônia
- Cada especialista auto-alimenta "vivo:<nome>" após cada passo
- **0 delegações, 0 mortes, 0 diferença** vs baseline
- `P(vivo | features)` não competiu com `P(acao_X | features)` porque
  "acao_delegar" nunca foi treinada (ação não existe sem execução prévia)
- Conclusão: heartbeat é token injetado, não auto-observação genuína

### v7: Colônia como Agente com Auto-Observação
- Colônia alimenta `estado_ferreiro=True/False` como feature na própria memória
- **Criação automática** (necessidade), poda automática (vida < 2.0)
- **Resultado: 3 BONS vivos, 0 RUINS, 23 criações, 20 mortes**
- Memória da colônia: 38 palavras, 12 ações
  - `acao_criar_trol: 10`, `acao_podar_trol: 10`
  - `acao_criar_ferreiro: 1`, `acao_feedback_bom: 60`
- **Colônia SABE (nos dados)** que criar trol dá errado
- Mas `decidir()` raw retorna `auto_observacao` pra tudo (freq 500 domina)

## Insights Arquiteturais

1. **P(b|a) bruto não discrimina auto-conhecimento.** A memória da colônia
   tem os dados (criar_trol=10 vs criar_ferreiro=1, feedback_ruim=40),
   mas `decidir()` é dominado por frequência. Precisa de IDF/NMI para
   recuperação discriminativa — exatamente como a BaseConhecimento.

2. **O self da colônia existe nos dados mas não é acessível via raw P(b|a).**
   A colônia precisa de um MECANISMO DE RECUPERAÇÃO (como `_nmi_semantico`)
   para consultar sua própria memória de forma discriminativa.

3. **Auto-observação genuína requer realimentação do estado como input.**
   `estado_ferreiro=True` derivado de `_freq_acao` é auto-observação
   (não token injetado) — a colônia se observa via própria memória.

4. **Criação não é decisão, é necessidade.** Pedir permissão P(b|a) para
   criar especialistas falha porque a ação não existe antes da primeira
   execução. O ciclo correto: criar automaticamente → aprender com
   consequências → podar seletivamente.

## Próximos Passos

1. **Conectar colônia ao `_nmi_semantico`**: usar NMI+IDF para que a
   colônia discrimine `P(feedback_bom | criar_ferreiro)` de
   `P(feedback_ruim | criar_trol)` em vez de raw freq.

2. **Tornar poda uma decisão P(b|a)**: com NMI/IDF, a colônia pode
   decidir podar baseada em `P(feedback_ruim | features_do_especialista)`
   em vez de threshold fixo.

3. **Integrar ao motor principal**: colônia como agente é o passo final
   para cruzar o horizonte do nível 7 — o self populacional.

## Regressões
- `_regressao_fase1.py`: 113/113 = 100%
- `test_fase18_auto_referencia.py`: 64 PASS / 0 FAIL
