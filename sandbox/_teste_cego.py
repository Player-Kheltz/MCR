#!/usr/bin/env python3
"""Teste Cego: Orquestrador (MCR) vs Cloud direto.
Protocolo:
1. MCR escreve _resposta_mcr.txt (via orquestrador)
2. Cloud escreve _resposta_cloud.txt (sem ler a do MCR)
3. SÓ ENTÃO comparar usando --comparar

Uso: python _teste_cego.py [--comparar]
     python _teste_cego.py  (executa MCR e Cloud, depois compara)
"""
import sys, os, json, time, re, urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

SANDBOX = os.path.dirname(os.path.abspath(__file__))
OLLAMA_URL = "http://localhost:11434/api/generate"

PERGUNTAS = [
    "O que e SPA no projeto MCR? Explique em 3 frases.",
    "Crie uma lore curta sobre a cidade de Eridanus, com 2 personagens.",
    "Qual a diferenca entre SHC e SPA? Responda em 2 frases.",
]

def _ollama(modelo, prompt, temp=0.2, ctx=4096):
    """Chamada direta ao Ollama (simula Cloud sem pipeline)."""
    try:
        d = json.dumps({
            "model": modelo,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temp, "num_ctx": ctx}
        }).encode()
        r = urllib.request.Request(OLLAMA_URL, data=d,
            headers={"Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(r, timeout=120).read())
        return resp.get("response", "")
    except Exception as e:
        return f"[ERRO] {e}"

def _mcr_orquestrador(pergunta):
    """MCR via orquestrador."""
    from modulos.orquestrador import Orquestrador
    from mcr_devia import KnowledgeGraph
    kg = KnowledgeGraph()
    from modulos.ia import IA
    ia = IA()
    import context_crew as cc
    ctx = cc.ContextCrew()
    
    orq = Orquestrador(kg=kg, ia=ia, ctx_crew=ctx)
    r = orq.executar("perguntar", {"pergunta": pergunta}, consulta=pergunta, temp=0.3)
    if r and r.get("sucesso"):
        return r["resposta"]
    return "[FALHA]"

def _cloud_direto(pergunta):
    """Cloud: modelo direto sem pipeline."""
    return _ollama("qwen2.5-coder:7b",
        f"Pergunta: {pergunta}\nResponda de forma util e especifica.", 0.3)

def _extrair_metricas(texto):
    """Extrai metricas objetivas do texto."""
    if not texto or texto.startswith("["):
        return {"chars": 0, "nomes": 0, "palavras": 0, "paragrafos": 0, "tem_tibia": False}
    chars = len(texto)
    palavras = len(texto.split())
    nomes = len(set(re.findall(r'\b[A-Z][a-z]{2,}\b', texto)))
    paragrafos = len([p for p in texto.split('\n') if p.strip()])
    tem_tibia = any(kw in texto.lower() for kw in ["tibia", "mcr", "eridanus", "spa", "shc",
                                                     "servidor", "npc", "aventureiro", "canary"])
    return {"chars": chars, "nomes": nomes, "palavras": palavras,
            "paragrafos": paragrafos, "tem_tibia": tem_tibia}

# ============================================================
# COMPARAR (modo --comparar)
# ============================================================
def modo_comparar():
    print("=" * 70)
    print("TESTE CEGO: ORQUESTRADOR (MCR) vs CLOUD DIRETO")
    print("=" * 70)
    
    resultados = []
    for i in range(len(PERGUNTAS)):
        mcr_path = os.path.join(SANDBOX, f"_resposta_mcr_{i}.txt")
        cloud_path = os.path.join(SANDBOX, f"_resposta_cloud_{i}.txt")
        
        mcr_texto = ""
        cloud_texto = ""
        
        if os.path.exists(mcr_path):
            with open(mcr_path, 'r', encoding='utf-8') as f:
                mcr_texto = f.read()
        if os.path.exists(cloud_path):
            with open(cloud_path, 'r', encoding='utf-8') as f:
                cloud_texto = f.read()
        
        m_met = _extrair_metricas(mcr_texto)
        c_met = _extrair_metricas(cloud_texto)
        
        # Determinacao de vencedor com validacao semantica
        vencedor = "EMPATE"
        criterio = ""
        
        # VALIDACAO SEMANTICA: detecta alucinacoes de siglas MCR
        def _alucinou(texto):
            if not texto: return False
            t = texto.lower()
            if "single page application" in t: return True
            if "sistema hospitalar" in t: return True
            if "subsystem of progress" in t: return True
            if "sistema de controle de acesso" in t: return True
            return False
        
        mcr_alucinou = _alucinou(mcr_texto)
        cloud_alucinou = _alucinou(cloud_texto)
        
        # 0. Alucinacao = derrota automatica
        if mcr_alucinou and not cloud_alucinou:
            vencedor = "Cloud"; criterio = "MCR alucinou"
        elif cloud_alucinou and not mcr_alucinou:
            vencedor = "MCR"; criterio = "Cloud alucinou"
        elif mcr_alucinou and cloud_alucinou:
            vencedor = "EMPATE"; criterio = "Ambos alucinaram"
        # 1. Tem conteudo Tibia?
        elif m_met["tem_tibia"] and not c_met["tem_tibia"]:
            vencedor = "MCR"; criterio = "Conteudo Tibia"
        elif c_met["tem_tibia"] and not m_met["tem_tibia"]:
            vencedor = "Cloud"; criterio = "Conteudo Tibia"
        elif m_met["tem_tibia"] == c_met["tem_tibia"]:
            # 2. Mais nomes proprios = mais especifico
            if m_met["nomes"] > c_met["nomes"]:
                vencedor = "MCR"; criterio = f"Nomes ({m_met['nomes']} vs {c_met['nomes']})"
            elif c_met["nomes"] > m_met["nomes"]:
                vencedor = "Cloud"; criterio = f"Nomes ({c_met['nomes']} vs {m_met['nomes']})"
            else:
                # 3. Mais conteudo (chars)
                if m_met["chars"] > c_met["chars"] and m_met["chars"] > 50:
                    vencedor = "MCR"; criterio = f"Chars ({m_met['chars']} vs {c_met['chars']})"
                elif c_met["chars"] > m_met["chars"] and c_met["chars"] > 50:
                    vencedor = "Cloud"; criterio = f"Chars ({c_met['chars']} vs {m_met['chars']})"
        
        resultados.append((i, PERGUNTAS[i][:60], mcr_texto, cloud_texto, m_met, c_met, vencedor, criterio))
    
    # Tabela
    print()
    print(f"{'#':<3} {'Pergunta':<40} {'MCR':<10} {'Cloud':<10} {'Vencedor':<20}")
    print("-" * 83)
    mcr_score = 0
    cloud_score = 0
    for i, pergunta, mcr_t, cloud_t, m_met, c_met, v, crit in resultados:
        mcr_str = f"[OK]" if m_met["chars"] > 0 else "[ERRO]"
        cloud_str = f"[OK]" if c_met["chars"] > 0 else "[ERRO]"
        if v == "MCR": mcr_score += 1
        elif v == "Cloud": cloud_score += 1
        print(f"{i:<3} {pergunta:<40} {mcr_str:<10} {cloud_str:<10} {v:<10} ({crit})")
    
    print()
    print("=" * 70)
    print("DETALHAMENTO POR PERGUNTA:")
    print("=" * 70)
    for i, pergunta, mcr_t, cloud_t, m_met, c_met, v, crit in resultados:
        print(f"\n--- Pergunta {i}: {PERGUNTAS[i]} ---")
        print(f"  MCR ({m_met['chars']} chars, {m_met['nomes']} nomes, Tibia={m_met['tem_tibia']}):")
        print(f"    {mcr_t[:200]}")
        print(f"  Cloud ({c_met['chars']} chars, {c_met['nomes']} nomes, Tibia={c_met['tem_tibia']}):")
        print(f"    {cloud_t[:200]}")
        print(f"  Vencedor: {v} - {crit}")
    
    print()
    print("=" * 70)
    print(f"PLACAR FINAL: MCR {mcr_score} x {cloud_score} Cloud")
    print(f"Empates: {len(resultados) - mcr_score - cloud_score}")
    print("=" * 70)
    
    return mcr_score, cloud_score

# ============================================================
# EXECUTAR (modo normal)
# ============================================================
def executar():
    print("=" * 70)
    print("EXECUTANDO TESTE CEGO...")
    print("MCR (orquestrador) vs Cloud (modelo direto)")
    print("=" * 70)
    
    for i, pergunta in enumerate(PERGUNTAS):
        print(f"\n--- Pergunta {i}: {pergunta[:60]}... ---")
        
        # 1. MCR escreve _resposta_mcr.txt
        print("  [MCR] Orquestrador gerando resposta...")
        t0 = time.time()
        mcr_resp = _mcr_orquestrador(pergunta)
        t_mcr = time.time() - t0
        mcr_path = os.path.join(SANDBOX, f"_resposta_mcr_{i}.txt")
        with open(mcr_path, 'w', encoding='utf-8') as f:
            f.write(mcr_resp)
        print(f"  [MCR] OK ({t_mcr:.1f}s) - {len(mcr_resp)} chars")
        
        # 2. Cloud escreve _resposta_cloud.txt (sem ler a do MCR)
        print("  [Cloud] Modelo direto respondendo...")
        t0 = time.time()
        cloud_resp = _cloud_direto(pergunta)
        t_cloud = time.time() - t0
        cloud_path = os.path.join(SANDBOX, f"_resposta_cloud_{i}.txt")
        with open(cloud_path, 'w', encoding='utf-8') as f:
            f.write(cloud_resp)
        print(f"  [Cloud] OK ({t_cloud:.1f}s) - {len(cloud_resp)} chars")
    
    print("\nExecucao concluida. Comparando...")
    return modo_comparar()


if __name__ == '__main__':
    if '--comparar' in sys.argv:
        modo_comparar()
    else:
        executar()
