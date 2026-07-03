# Pendências MCR-DevIA (26/06/2026)

> Estado atual do projeto após revisão do fluxo da equipe (time de 3).

---

## ✅ ESTADO ATUAL DO SISTEMA

### MCR-DevIA — Núcleo
- **Versão:** V2556
- **Comandos:** ~50 (32 diretos + 18 atalhos)
- **KG:** ~185KB, 446 lessons (após compactação e limpeza)
- **Testes:** 67/67 PASS, V12 coverage 62%
- **Health Score:** 78/100 (auto_diagnostico)

### WebLearn v2
- Pipeline completo: smart query → classificação → GitHub explorer → deep crawl → safety scan → fragmentação → narrativa → KG
- 9 tipos de classificação: tutorial, documentacao, wiki, github_repo, forum, blog, ecommerce, garbage, social
- Filtro inteligente elimina e-commerce e garbage automaticamente
- ContextGuard evita desvio de tópico no deep crawl (threshold ≥ 40)
- Safety scan duplo: V1 (HTML) + V2 (texto)

### YouTube Transcript
- Módulo `youtube_transcript.py` integrado ao web_learn
- `youtube_transcript_api` v1.2.4 (API: `fetch(video_id)` retorna objetos com `.text`)
- Detecta YouTube URLs e extrai transcrição em vez de baixar HTML

### KG (Knowledge Graph)
- Auto-diagnóstico a cada 5 ciclos (monitora saúde)
- Auto-melhoria a cada 10 ciclos (dedup, remove lixo)
- Compactado: 243KB → 185KB (-22%)
- Educação continuada: toda ação relevante vira lesson

### Loop OODA (mcr_loop.py)
- Auto-diagnóstico integrado a cada 5 ciclos
- Auto-melhoria a cada 10 ciclos (--aplicar se health < 80, dry-run se ≥ 80)
- Ciclo contínuo de: INICIAR → PENSAR → EXECUTAR → APRENDER → CONSOLIDAR

### Docs / Regras
- `AGENTS.md` revisado (26/06) — 3 seções, enxuto, time de 3
- `docs/rules/equipe.md` — fluxo oficial do time de 3 (NOVO)
- `docs/rules/autonomia.md` — atualizado com capacidades atuais
- `docs/rules/workflow.md` — atualizado com MCR-DevIA + time de 3
- `docs/rules/licoes.md` — atualizado com fluxo KG
- Demais regras: checkpoint, compilacao, encoding — OK

---

## ⏳ EM ANDAMENTO / PENDENTE

### 1. Items.xml (10.701 problemas)
- Detectados, aprendidos, mas não corrigidos
- Comparação PT vs EN: 1.231 artigos errados, 13 não traduzidos, 9.457 nomes diferentes
- Aguardando supervisão para aplicar correções

### 2. YouTube sem legendas
- Cerca de 15% dos vídeos não têm transcrição disponível
- Possível melhoria: fallback para OCR/ASM ou ignorar vídeos sem legenda

### 3. Gargalos de performance (Ollama-bound)
- `build`: ~153s, `plan`: ~158s, `debate`: ~32s
- Sem modelo mais rápido no Ollama, sem otimização possível

### 4. Melhoria futura: SearXNG
- Descartado por enquanto (requer Docker + configuração complexa)
- DuckDuckGo via `ddgs` é suficiente

---

## 🎯 PRÓXIMOS PASSOS SUGERIDOS

1. Continuar ciclo de melhorias (KG mais enxuto, mais V12 coverage)
2. Explorar integração com mais fontes de busca
3. Corrigir items.xml quando houver supervisão
4. Manter docs sincronizados com o estado real do sistema

---

## 📊 MÉTRICAS ATUAIS

| Métrica | Valor |
|---------|-------|
| Comandos MCR-DevIA | ~50 |
| Lessons no KG | 446 (ativas) |
| Tamanho do KG | 185KB |
| Testes passando | 67/67 (100%) |
| V12 coverage | 62% |
| Health Score | 78/100 |
| Fragmentos weblearn | 1000+ em 50+ diretórios |
| Loops OODA configurados | auto_diagnostico (5) + auto_melhoria (10) |
