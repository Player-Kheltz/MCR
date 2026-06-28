"""
Listar pendencias em aberto apos sessao de 25/06
"""
pendencias = """
╔══════════════════════════════════════════════════════════════════╗
║        PENDENCIAS EM ABERTO — MCR-DevIA (25/06/2026)           ║
╚══════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────┐
│ ✅ CONCLUÍDO NESTA SESSÃO                                        │
├─────────────────────────────────────────────────────────────────┤

  • Model Router V2: corrigido com modelos reais + ctx por cargo
  • Super Fragmentador: criado (fragmenta/processa/compila/referencia)
  • Context Infinity: orquestrador de contexto com IA-Crew
  • Validador de Gênero V2: aprendizado via KG, 0 chamadas IA
  • Comando 'analisar': AST + linha numerada + router híbrido
  • Filtro de Veracidade: barra nomes compostos inventados
  • AGENTS.md atualizado: regras, comandos, lessons
  • 5 modelos baixados e configurados (1.5B → 8B)
  • KG cresceu para 1020+ lessons
  • Migração E:\ concluída (logs, modelos, config)

┌─────────────────────────────────────────────────────────────────┐
│ ⏳ PENDENTE (nao implementar agora, so listar)                   │
├─────────────────────────────────────────────────────────────────┤

 1. Items.xml — CORREÇÃO (10.701 problemas detectados)
    → 1.231 artigos errados, 13 nao traduzidos, 9.457 nomes
    → Pipeline extract → review → apply pronto
    → Aguardando supervisão para aplicar via --force

 2. Docs — CLASSIFICAÇÃO COMPLETA (51 docs, so 5 classificados)
    → Docs descobertos mas nao categorizados
    → IA alucina com perguntar (contexto acumulado)

 3. Docs — REORGANIZAÇÃO
    → Conforme solicitado pelo usuário
    → MCR-DevIA sabe onde estao os docs (KG)

 4. CÓDIGO — REVISÃO GERAL (C++, Lua, scripts)
    → extract code funciona (416 funcoes de player.cpp)
    → Revisao pendente para depois dos dados

 5. AUTO-CONSCIÊNCIA — MAIS CICLOS
    → 2 toques detectados (reparos monster, licoes repetidas)
    → Precisa de mais dados pra melhorar

 6. ORQUESTRADOR DE CONTEXTO — INTEGRAÇÃO COMPLETA
    → Context Infinity criado mas nao integrado 100% no pipeline
    → Falta conectar Adicionador/Removedor com o perguntar

 7. SUBSTITUIR IA POR V12 — AUDITORIA PARCIAL
    → Identificamos ~60% das chamadas de IA viaveis
    → Falta aplicar as substituicoes

 8. 14B — TESTE CONFIRMADO: NAO CABE NA VRAM
    → Q4_K_M (9GB) e Q3_K_M (7.3GB) testados
    → Nenhum cabe na RTX 3080 10GB
    → Foco mantido em modelos 7B/8B

 9. DEEPSEEK-R1:7B — ALUCINA EM RACIOCINIO
    → Thinking mode gera conclusoes erradas
    → Substituido por coder:7b em varias tarefas
    → Mas ainda é usado em planejador

10. FAST (PT-BR) — AINDA ERRA SEM O V12
    → Validador V12 cobre palavras conhecidas
    → Palavras novas/ambiguas ainda precisam de IA
    → Dicionario do V12 cresce com uso

┌─────────────────────────────────────────────────────────────────┤
│ 📊 STATUS ATUAL                                                  │
├─────────────────────────────────────────────────────────────────┤

  • MCR-DevIA: 46 comandos, 1020+ lessons
  • Modelos: 5 (nomic, coder:1.5b, coder:7b, deepseek-r1:7b, llama3.1:8b)
  • KG: 1020+ lessons, 46 contextos diferentes
  • V12 implementado em: genero, KG response, fast classification
  • Context Infinity: criado, parcialmente integrado
  • AGENTS.md: regra absoluta "USE MCR-DEVIA PRIMEIRO"
  • Tudo salvo em E:\\ (nada em C:)
  • Zero alteracoes fora do sandbox (itens.xml nao foi alterado)
"""
print(pendencias)
