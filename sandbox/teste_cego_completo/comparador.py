#!/usr/bin/env python3
"""Comparador do Teste Cego: avalia respostas Cloud vs MCR com criterios UNIVERSALS.
Nao favorece nenhum dominio especifico. Mede capacidade tecnica generica."""
import os, json, re, sys

BASE = os.path.dirname(os.path.abspath(__file__))
CLOUD_DIR = os.path.join(BASE, "respostas_cloud")
MCR_DIR = os.path.join(BASE, "respostas_mcr")
BATERIA_PATH = os.path.join(BASE, "bateria.json")

# Palavras de baixa qualidade (respostas genericas, "encher linguica")
GENERICAS = [
    "em suma", "em resumo", "de forma geral", "basicamente",
    "como mencionado", "como dito anteriormente", "vale ressaltar",
    "e importante notar", "e fundamental", "e crucial",
]

def _carregar_bateria():
    with open(BATERIA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def _detectar_generico(texto):
    """Detecta se resposta e muito generica (pouco valor informativo)."""
    if not texto: return True
    t = texto.lower()
    # Frases muito curtas
    if len(texto.split()) < 10: return True
    # Muitas palavras de enchimento
    count = sum(1 for g in GENERICAS if g in t)
    return count >= 2

def _contar_palavras_unicas(texto):
    """Conta palavras significativas (sem stopwords basicas)."""
    if not texto: return 0
    stopwords = set("a o e de do da em para com um uma os as no na dos das pelo pela por".split())
    palavras = re.findall(r'\b[a-záéíóúãõç]{4,}\b', texto.lower())
    return len([p for p in palavras if p not in stopwords])

def _extrair_metricas(texto):
    """Extrai metricas universais de qualidade."""
    if not texto or texto.startswith("[MCR") or texto.startswith("[ERRO"):
        return {"valido": False, "generico": True, "unicas": 0, "palavras": 0, "chars": 0}
    
    palavras = len(texto.split())
    chars = len(texto)
    unicas = _contar_palavras_unicas(texto)
    generico = _detectar_generico(texto)
    
    return {
        "valido": palavras >= 5,
        "generico": generico,
        "unicas": unicas,
        "palavras": palavras,
        "chars": chars,
    }

def _determinar_vencedor(av_mcr, av_cloud):
    """Determina vencedor com criterios universais."""
    # Criterio 1: Validade basica
    if not av_mcr["valido"] and av_cloud["valido"]:
        return "Cloud", "MCR invalido/vazio"
    if not av_cloud["valido"] and av_mcr["valido"]:
        return "MCR", "Cloud invalido/vazio"
    if not av_mcr["valido"] and not av_cloud["valido"]:
        return "EMPATE", "Ambos invalidos"
    
    # Criterio 2: Nao ser generico (importante)
    if av_mcr["generico"] and not av_cloud["generico"]:
        return "Cloud", "MCR generico"
    if av_cloud["generico"] and not av_mcr["generico"]:
        return "MCR", "Cloud generico"
    
    # Criterio 3: Riqueza de vocabulario (palavras unicas significativas)
    if av_mcr["unicas"] > av_cloud["unicas"] * 1.5:
        return "MCR", f"voc+ ({av_mcr['unicas']} vs {av_cloud['unicas']})"
    if av_cloud["unicas"] > av_mcr["unicas"] * 1.5:
        return "Cloud", f"voc+ ({av_cloud['unicas']} vs {av_mcr['unicas']})"
    
    # Criterio 4: Completude (chars sem ser generico)
    if av_mcr["chars"] > av_cloud["chars"] * 1.3 and not av_mcr["generico"]:
        return "MCR", f"chars ({av_mcr['chars']} vs {av_cloud['chars']})"
    if av_cloud["chars"] > av_mcr["chars"] * 1.3 and not av_cloud["generico"]:
        return "Cloud", f"chars ({av_cloud['chars']} vs {av_mcr['chars']})"
    
    return "EMPATE", "Empate tecnico"

def comparar():
    bateria = _carregar_bateria()
    testes = bateria["testes"]
    
    print("=" * 80)
    print("  TESTE CEGO: ORQUESTRADOR (MCR) vs CLOUD DIRETO")
    print("  Criterio: CAPACIDADE TECNICA UNIVERSAL (sem favorecimento de dominio)")
    print("=" * 80)
    
    resultados = []
    
    for t in testes:
        tid = t["id"]
        mcr_path = os.path.join(MCR_DIR, f"test_{tid}.txt")
        cloud_path = os.path.join(CLOUD_DIR, f"test_{tid}.txt")
        
        mcr_txt = ""
        cloud_txt = ""
        if os.path.exists(mcr_path):
            with open(mcr_path, 'r', encoding='utf-8-sig', errors='replace') as f:
                mcr_txt = f.read()
        if os.path.exists(cloud_path):
            with open(cloud_path, 'r', encoding='utf-8-sig', errors='replace') as f:
                cloud_txt = f.read()
        
        av_mcr = _extrair_metricas(mcr_txt)
        av_cloud = _extrair_metricas(cloud_txt)
        vencedor, motivo = _determinar_vencedor(av_mcr, av_cloud)
        
        resultados.append({
            "id": tid,
            "categoria": t["categoria"],
            "titulo": t["titulo"],
            "vencedor": vencedor,
            "motivo": motivo,
            "mcr": av_mcr,
            "cloud": av_cloud,
        })
    
    # Tabela
    print()
    cab = f"{'#':<3} {'Categoria':<20} {'Vencedor':<10} {'Motivo':<30} {'MCR':<20} {'Cloud':<20}"
    print(cab)
    print("-" * len(cab))
    
    score_mcr = 0
    score_cloud = 0
    empates = 0
    
    for r in resultados:
        if r["vencedor"] == "MCR":
            score_mcr += 1
        elif r["vencedor"] == "Cloud":
            score_cloud += 1
        else:
            empates += 1
        
        mcr_info = f"voc={r['mcr']['unicas']} chars={r['mcr']['chars']}"
        cloud_info = f"voc={r['cloud']['unicas']} chars={r['cloud']['chars']}"
        if r["mcr"]["generico"]: mcr_info += " GENERICO"
        if r["cloud"]["generico"]: cloud_info += " GENERICO"
        
        print(f"{r['id']:<3} {r['categoria']:<20} {r['vencedor']:<10} {r['motivo']:<30} {mcr_info:<20} {cloud_info:<20}")
    
    print()
    print("=" * 80)
    print(f"  PLACAR FINAL: MCR {score_mcr} x {score_cloud} Cloud | Empates: {empates}")
    print("=" * 80)
    
    # Detalhamento
    print()
    print("DETALHAMENTO:")
    for r in resultados:
        print(f"\n--- Teste {r['id']}: {r['titulo']} ---")
        print(f"  Vencedor: {r['vencedor']} | {r['motivo']}")
        
        mcr_path = os.path.join(MCR_DIR, f"test_{r['id']}.txt")
        cloud_path = os.path.join(CLOUD_DIR, f"test_{r['id']}.txt")
        
        with open(mcr_path, 'r', encoding='utf-8-sig', errors='replace') as f:
            mcr_txt = f.read()
        with open(cloud_path, 'r', encoding='utf-8-sig', errors='replace') as f:
            cloud_txt = f.read()
        
        print(f"  MCR ({r['mcr']['chars']} chars):")
        print(f"    {mcr_txt[:200]}")
        print(f"  Cloud ({r['cloud']['chars']} chars):")
        print(f"    {cloud_txt[:200]}")
    
    return score_mcr, score_cloud, empates

if __name__ == "__main__":
    comparar()
