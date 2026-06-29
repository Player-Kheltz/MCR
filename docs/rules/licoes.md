# Licoes.md — Lições Aprendidas MCR

> Parte do sistema modular `docs/rules/`. Consulte `../AGENTS.md` para visão geral.

## Propósito

Registrar aprendizados para nunca repetir erros. O time de 3 (Cloud + MCR-DevIA + Usuário) aprende constantemente.

## O Sistema (atual)

- Lições são registradas via **KG** (`python MCR_DevIA-Kernel.py ensinar "<erro>" "<causa>" "<solucao>" "<categoria>"`)
- Categorias: `bugfix`, `feature`, `decisao`, `licao`, `api`, `comando`, `weblearn`, `sessao`, `aprendizado`, `auto_review`, `teste_cego`
- As lições mais recentes ficam em `docs/lessons/recentes.md`
- O KG persiste entre sessões (~2MB, 2000+ lessons)
- O **ciclo de aprendizado** funciona:
  1. Mente.think() carrega memórias de ALTO SCORE
  2. Mente.learn() autoavalia e atualiza scores
  3. Pre-check: se < 2 lessons no KG → weblearn pesquisa automaticamente
  4. Auto-web: se FAST disser "resposta nao atende" → weblearn + regenera
- O **auto_revisor** usa heurística (não FAST): classe em código = valida, contextualizada = valida, nome composto 10+ chars = suspeita
- Memória individual por membro do conselho: `sandbox/.mcr_devia/conselho_memoria/{nome}.jsonl`

## Regras

1. **Registre uma lição** sempre que:
   - Resolver um bug complexo
   - Descobrir algo relevante não documentado
   - Tomar decisão arquitetural importante
   - Aprender algo novo da web (web_learn)
   - Alguém do time cometer um erro (para não repetir)

2. **Ao iniciar conversa**, revise as lições recentes em `docs/lessons/recentes.md`

3. **Compartilhe lições com o Hub do Lojista** se aplicáveis ao contexto de varejo (veja `docs/rules/intercambio.md`)
