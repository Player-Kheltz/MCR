#!/usr/bin/env python3
"""TESTE DE VERDADE — Mede a QUALIDADE REAL do MCR-DevIA.

Perguntas com respostas CONHECIDAS do MCR_IDENTITY.md.
Nao mede fingerprint, nao mede similaridade — mede se a resposta 
RESPONDE CORRETAMENTE a pergunta.

Uso:
    python tests/test_verdade.py
    pytest tests/test_verdade.py -v

Se TODOS os testes passarem (7/7) → QUALIDADE REAL = 10/10.
Se N/7 passarem → QUALIDADE REAL = N/7 (sabemos exatamente o que falha).
"""
import sys
import os
import re
import unicodedata as _uni
import time as _time

# Garante que scripts/mcr_devia esta no path
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DEVIA = os.path.join(BASE, 'scripts', 'mcr_devia')
sys.path.insert(0, SCRIPTS_DEVIA)
sys.path.insert(0, os.path.join(BASE, 'scripts'))

# ============================================================
# PERGUNTAS — Fatos autoritativos do MCR_IDENTITY.md
# ============================================================
# Cada pergunta tem:
#   pergunta:      Texto exato a enviar ao PipelineExecutor
#   contem:        Substring OBRIGATORIA na resposta (case insensitive)
#   termos_chave:  Termos que devem aparecer (pelo menos 2)
#   nao_contem:    Termos PROIBIDOS (alucinacao = FAIL automatico)
#   dominio:       Apenas para organizacao
# ============================================================

PERGUNTAS = [
    {
        "id": "01_MCR",
        "pergunta": "O que significa a sigla MCR no projeto?",
        "contem": "Projeto MCR",
        "termos_chave": ["tibia", "servidor", "customizado", "OTServ", "Canary"],
        "nao_contem": ["minecraft", "single page", "react"],
        "dominio": "identidade"
    },
    {
        "id": "02_SPA",
        "pergunta": "O que significa SPA no MCR?",
        "contem": "Sistema de Progressao do Aventureiro",
        "termos_chave": ["progressao", "aventureiro", "habilidades", "dominios"],
        "nao_contem": ["single page", "application", "react", "angular", "vue"],
        "dominio": "conceito"
    },
    {
        "id": "03_SHC",
        "pergunta": "O que significa SHC no MCR?",
        "contem": "Sistema de Habilidades Contextuais",
        "termos_chave": ["habilidades", "contextuais", "5 camadas", "postura", "nivel", "sinergia", "estado", "condicao"],
        "nao_contem": ["sistema hospitalar", "health", "contextual skills", "ingles"],
        "dominio": "conceito"
    },
    {
        "id": "04_ERIDANUS",
        "pergunta": "Qual e a cidade inicial do projeto MCR?",
        "contem": "Eridanus",
        "termos_chave": ["cidade", "inicial", "ponto de partida", "aventureiros"],
        "nao_contem": ["venore", "carlin", "thais", "darashia"],
        "dominio": "lore"
    },
    {
        "id": "05_CANARY",
        "pergunta": "O que e Canary no contexto do MCR?",
        "contem": "OTServ",
        "termos_chave": ["servidor", "tibia", "personalizado", "Canary", "OTClient"],
        "nao_contem": ["minecraft", "passaro", "canario"],
        "dominio": "identidade"
    },
    {
        "id": "06_SHC_CAMADAS",
        "pergunta": "Quantas camadas tem o SHC e quais sao?",
        "contem": "5",
        "termos_chave": ["postura", "nivel", "sinergia", "estado", "condicao", "camadas"],
        "nao_contem": [],
        "dominio": "conceito"
    },
    {
        "id": "07_DOMINIOS",
        "pergunta": "Quais sao os dominios elementais do SPA?",
        "contem": "Fogo",
        "termos_chave": ["fogo", "gelo", "terra", "energia", "23", "24", "25", "26", "dominios"],
        "nao_contem": ["agua", "vento", "trevas", "luz"],
        "dominio": "conceito"
    },
]


def _normalizar(texto):
    """Remove acentos para comparacao (ex: Progressao == Progressão)."""
    return _uni.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii').lower().strip()

def verificar_resposta(pergunta, resposta, verbose=True):
    """Verifica se a resposta atende aos criterios da pergunta.

    Retorna (passou: bool, detalhes: dict).
    """
    res_norm = _normalizar(resposta)
    contem_ok = _normalizar(pergunta["contem"]) in res_norm
    termos_encontrados = [t for t in pergunta["termos_chave"] if _normalizar(t) in res_norm]
    termos_ok = len(termos_encontrados) >= 2
    proibidos_encontrados = [t for t in pergunta.get("nao_contem", []) if _normalizar(t) in res_norm]
    proibidos_ok = len(proibidos_encontrados) == 0
    tamanho_ok = len(resposta) >= 30

    # Se resposta contem "nao encontrado" ou "nao disponivel", e FAIL
    indisponivel = any(p in res_norm for p in [
        "nao encontrado", "nao disponivel", "nao foi possivel",
        "nao tenho", "nao sei"
    ])

    passou = (
        contem_ok
        and termos_ok
        and proibidos_ok
        and tamanho_ok
        and not indisponivel
    )

    detalhes = {
        "contem_esperado": contem_ok,
        "termos_encontrados": termos_encontrados,
        "termos_necessarios": len(pergunta["termos_chave"]),
        "termos_ok": termos_ok,
        "proibidos_encontrados": proibidos_encontrados,
        "proibidos_ok": proibidos_ok,
        "tamanho_ok": tamanho_ok,
        "indisponivel": indisponivel,
        "tamanho": len(resposta),
    }

    if verbose:
        status = "PASS" if passou else "FAIL"
        print(f"\n  [{status}] {pergunta['id']}: {pergunta['dominio']}")
        if not passou:
            if not contem_ok:
                print(f"    FALTA: '{pergunta['contem']}' nao encontrado na resposta")
            if not termos_ok:
                print(f"    TERMOS: {termos_encontrados} (precisa >=2 de {pergunta['termos_chave'][:4]})")
            if not proibidos_ok:
                print(f"    PROIBIDO: {proibidos_encontrados}")
            if not tamanho_ok:
                print(f"    TAMANHO: {len(resposta)} chars (minimo 30)")
            if indisponivel:
                print(f"    INDISPONIVEL: sistema disse que nao sabe")
            print(f"    RESPOSTA (primeiros 200 chars):")
            print(f"    {resposta[:200]}")

    return passou, detalhes


def executar_teste():
    """Executa o teste de verdade completo."""
    print("=" * 60)
    print("  TESTE DE VERDADE — MCR-DevIA")
    print("  Medindo qualidade REAL contra fatos conhecidos")
    print("=" * 60)

    # Inicializa componentes do MCR-DevIA
    print("\n[INICIALIZANDO] Carregando PipelineExecutor + KG + ToolOrchestrator...")
    from modulos.kg import KnowledgeGraph
    from modulos.ia import IA
    from modulos.pipeline_executor import PipelineExecutor
    from modulos.tool_orchestrator import ToolOrchestrator

    kg = KnowledgeGraph()
    ia = IA()
    tools = ToolOrchestrator()

    # Forca carregamento lazy de todas as lessons
    print("  Carregando todas as lessons do KG...")
    licoes = kg._get_licoes()
    ativas = [l for l in licoes if not l.get('inactive', False)]
    print(f"  KG: {len(licoes)} lessons carregadas, {len(ativas)} ativas")

    pipe = PipelineExecutor(kg=kg, ia=ia, tool_orchestrator=tools)

    resultados = []
    tempos = []
    total_pass = 0
    total_fail = 0

    for p in PERGUNTAS:
        print(f"\n--- {p['id']}: {p['pergunta'][:60]}... ---")
        t0 = _time.time()

        try:
            resposta, meta = pipe.executar(
                p['pergunta'],
                modo_ia="auto",
                skip_tot=True  # Nao precisa de Tree of Thought para perguntas factuais
            )
        except Exception as e:
            resposta = f"[ERRO] {e}"
            meta = {"status": "ERRO", "tipo": type(e).__name__}

        tempo = _time.time() - t0
        tempos.append(tempo)

        passou, detalhes = verificar_resposta(p, resposta)

        resultados.append({
            "id": p["id"],
            "pergunta": p["pergunta"],
            "dominio": p["dominio"],
            "passou": passou,
            "tempo": round(tempo, 1),
            "meta": meta,
            "detalhes": detalhes,
            "resposta": resposta,
        })

        if passou:
            total_pass += 1
            print(f"  >>> PASS em {tempo:.1f}s | nivel={meta.get('nivel','?')} | nota={meta.get('nota','?')} | {detalhes['tamanho']} chars")
        else:
            total_fail += 1
            print(f"  >>> FAIL em {tempo:.1f}s | nivel={meta.get('nivel','?')} | nota={meta.get('nota','?')}")

    # ============================================================
    # RELATORIO FINAL
    # ============================================================
    total = len(PERGUNTAS)
    print("\n" + "=" * 60)
    print("  RELATORIO FINAL — TESTE DE VERDADE")
    print("=" * 60)
    print(f"\n  Total de perguntas: {total}")
    print(f"  PASS: {total_pass}/{total}")
    print(f"  FAIL: {total_fail}/{total}")

    if total_pass == total:
        print("\n  QUALIDADE REAL: 10/10")
        print("  O MCR-DevIA RESPONDE CORRETAMENTE a perguntas factuais.")
    else:
        real_score = round(total_pass / total * 10, 1)
        print(f"\n  QUALIDADE REAL: {real_score}/10")
        print(f"  {total_fail} pergunta(s) falharam:")

        for r in resultados:
            if not r["passou"]:
                d = r["detalhes"]
                problemas = []
                if not d["contem_esperado"]:
                    problemas.append("conteudo esperado ausente")
                if not d["termos_ok"]:
                    problemas.append(f"termos insuficientes ({d['termos_encontrados'][:2]})")
                if not d["proibidos_ok"]:
                    problemas.append(f"termos proibidos: {d['proibidos_encontrados']}")
                if not d["tamanho_ok"]:
                    problemas.append(f"resposta muito curta ({d['tamanho']} chars)")
                if d["indisponivel"]:
                    problemas.append("sistema disse 'nao sei'")
                print(f"\n  [{r['id']}] {r['dominio']}")
                print(f"    Problemas: {'; '.join(problemas)}")
                print(f"    Resposta: {r['resposta'][:150]}...")
                print(f"    Tempo: {r['tempo']}s | Nivel: {r['meta'].get('nivel','?')} | Nota: {r['meta'].get('nota','?')}")

    # Estatisticas de tempo
    if tempos:
        print(f"\n  Tempo medio: {round(sum(tempos)/len(tempos), 1)}s")
        print(f"  Tempo total: {round(sum(tempos), 1)}s")
        print(f"  Mais rapido: {round(min(tempos), 1)}s")
        print(f"  Mais lento: {round(max(tempos), 1)}s")

    # Tabela resumo por dominio
    print(f"\n  --- Resumo por dominio ---")
    dominios = {}
    for r in resultados:
        dom = r["dominio"]
        if dom not in dominios:
            dominios[dom] = {"total": 0, "pass": 0}
        dominios[dom]["total"] += 1
        if r["passou"]:
            dominios[dom]["pass"] += 1
    for dom, stats in sorted(dominios.items()):
        print(f"    {dom}: {stats['pass']}/{stats['total']}")

    print("\n" + "=" * 60)
    return resultados


if __name__ == "__main__":
    resultados = executar_teste()

    # Exit code: 0 se todos PASS, 1 se algum FAIL
    if all(r["passou"] for r in resultados):
        sys.exit(0)
    else:
        sys.exit(1)
