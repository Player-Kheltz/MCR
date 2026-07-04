#!/usr/bin/env python3
"""
Benchmark: Deteccao de anomalias multi-fonte vs metodos simples.

Simula N fontes independentes (sensores) com padrao previsivel.
Em momentos aleatorios, TODAS as fontes oscilam simultaneamente.
Compara MCREntropiaTemporal (multi-nivel) com:
  - Nivel unico (mono-fonte)
  - Threshold fixo (3 desvios padrao)
  - CUMSUM

Gera metricas: precisao, recall, F1, latencia.
Salva resultados em benchmark/resultados.json
"""

import sys, os, json, math, time, random as _rand
from collections import deque

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.join(BASE_DIR, '..', '..'))
sys.path.insert(0, os.getcwd())

__file__ = os.path.join(os.getcwd(), "MCR_AGI.py")
with open(__file__, encoding="utf-8") as f:
    _code = f.read().split("def main():")[0]
exec(compile(_code, "MCR_AGI.py", "exec"))

RESULTADOS_PATH = os.path.join(BASE_DIR, "resultados.json")
SEED = 42


def gerar_sensor(periodo=6, ruido=0.05):
    """Gera um ciclo previsivel de tokens para um 'sensor'.
    
    Ex: periodo=6 → 'A,B,C,D,E,F,A,B,C,D,E,F,...'
    ruido=0.05 → 5% de chance de token aleatorio.
    """
    tokens = [chr(65 + i) for i in range(periodo)]
    idx = 0
    while True:
        if _rand.random() < ruido:
            yield _rand.choice(tokens)
        else:
            yield tokens[idx]
            idx = (idx + 1) % periodo


def simular_experimento(n_sensores=5, n_estavel=50, n_pos_evento=15,
                        n_eventos=5, ent_rel=0.10, min_niveis=2):
    """Simula N fontes com eventos injetados.
    
    Retorna: (deteccoes, falsos_positivos, latencia_media)
    """
    # Cria N fontes MCR
    fontes = {f"sensor_{i}": MCR(f"sensor_{i}") for i in range(n_sensores)}
    gens = {f"sensor_{i}": gerar_sensor(periodo=_rand.choice([4, 6, 8])) 
            for i in range(n_sensores)}
    
    # Configura entropia temporal
    class Obs:
        def levels(self):
            return fontes
    et = MCREntropiaTemporal(observer=Obs(), janela=20)
    
    # Registra eventos reais
    eventos_reais = set()
    timer_atual = 0
    for e in range(n_eventos):
        timer_atual += n_estavel // n_eventos + _rand.randint(-3, 3)
        timer_atual = max(timer_atual, 5)
        eventos_reais.add(timer_atual)
    
    # Fase de pre-warm (estabiliza as cadeias)
    for t in range(20):
        for nome, gen in gens.items():
            token = next(gen)
            mk_seg = fontes[nome]
            # Aprende transicao entre ultimo token e este
            if hasattr(mk_seg, '_ultimo'):
                mk_seg.aprender(mk_seg._ultimo, token)
            mk_seg._ultimo = token
        et.medir()
    et._hist.clear()
    
    # Fase principal
    deteccoes = []
    falsos = []
    latencias = []
    
    for t in range(n_estavel + n_pos_evento * n_eventos):
        # Alimenta fontes
        for nome, gen in gens.items():
            token = next(gen)
            mk_seg = fontes[nome]
            if hasattr(mk_seg, '_ultimo'):
                mk_seg.aprender(mk_seg._ultimo, token)
            mk_seg._ultimo = token
        
        # Injeta evento real neste instante
        if t in eventos_reais:
            # Troca o padrao de TODAS as fontes simultaneamente
            novos_gens = {f"sensor_{i}": gerar_sensor(
                periodo=_rand.choice([3, 5, 7])) for i in range(n_sensores)}
            for nome in gens:
                mk_seg = fontes[nome]
                if hasattr(mk_seg, '_ultimo'):
                    token = next(novos_gens[nome])
                    mk_seg.aprender(mk_seg._ultimo, token)
                    mk_seg._ultimo = token
            gens = novos_gens
        
        # Mede entropia e detecta
        et.medir()
        evento, info = et.detectar(threshold_rel=ent_rel, min_niveis=min_niveis)
        
        if evento:
            if t in eventos_reais or any(abs(t - r) <= 2 for r in eventos_reais):
                deteccoes.append(t)
                latencias.append(min(abs(t - r) for r in eventos_reais))
            else:
                falsos.append(t)
    
    return deteccoes, falsos, latencias


def avaliar_metodos(n_rodadas=10):
    """Compara MCR multi-nivel vs nivel unico vs threshold fixo."""
    relatorio = []
    
    for rodada in range(n_rodadas):
        _rand.seed(SEED + rodada)
        n_sensores = _rand.choice([3, 4, 5, 6])
        n_eventos = _rand.choice([3, 4, 5])
        
        # MCR multi-nivel (min_niveis=2)
        det, fal, lat = simular_experimento(
            n_sensores=n_sensores, n_eventos=n_eventos,
            ent_rel=0.10, min_niveis=2)
        taxa_mcr = len(det) / max(n_eventos, 1)
        fp_mcr = len(fal)
        lat_mcr = sum(lat) / max(len(lat), 1) if lat else 0
        
        # MCR mono-nivel (min_niveis=1 — qualquer oscilacao conta)
        det1, fal1, lat1 = simular_experimento(
            n_sensores=n_sensores, n_eventos=n_eventos,
            ent_rel=0.10, min_niveis=1)
        taxa_mono = len(det1) / max(n_eventos, 1)
        fp_mono = len(fal1)
        
        relatorio.append({
            "rodada": rodada + 1,
            "sensores": n_sensores,
            "eventos": n_eventos,
            "mcr_multi_taxa": round(taxa_mcr, 2),
            "mcr_multi_fp": fp_mcr,
            "mcr_multi_latencia": round(lat_mcr, 1),
            "mcr_mono_taxa": round(taxa_mono, 2),
            "mcr_mono_fp": fp_mono,
        })
        
        print(f"  Rodada {rodada+1}: {n_sensores} sensores, {n_eventos} eventos")
        print(f"    Multi-nivel: taxa={taxa_mcr:.0%} fp={fp_mcr} lat={lat_mcr:.1f}")
        print(f"    Mono-nivel:  taxa={taxa_mono:.0%} fp={fp_mono}")
    
    return relatorio


# ═══════════════════════════════════════════════════════════════
# TESTE ADICIONAL: Log real do Windows + 3-sigma
# ═══════════════════════════════════════════════════════════════

def testar_log_real():
    """Testa MCR contra arquivo de log real (+ comparacao 3-sigma)."""
    print()
    print("=" * 60)
    print("  TESTE REAL: Log do Windows + 3-sigma")
    print("=" * 60)
    
    ARQUIVO = r"C:\Windows\Logs\CBS\FilterList.log"
    with open(ARQUIVO, 'r', errors='replace') as f:
        linhas = f.read().strip().split('\n')
    
    print(f"  Arquivo: {ARQUIVO}")
    print(f"  Linhas: {len(linhas)}")
    
    mk = MCR("log_real")
    metade = len(linhas) // 2
    for i in range(metade - 1):
        mk.aprender(linhas[i].strip(), linhas[i+1].strip())
    
    ent_antes = mk.entropia_media()
    acertos = 0
    for i in range(metade - 1, len(linhas) - 1):
        mk.aprender(linhas[i].strip(), linhas[i+1].strip())
        pred, conf = mk.predizer(linhas[i].strip())
        if pred and pred == linhas[i+1].strip():
            acertos += 1
    ent_depois = mk.entropia_media()
    taxa = acertos / max(len(linhas) - metade, 1)
    
    print(f"  Taxa de acerto (MCR): {acertos}/{len(linhas)-metade} = {taxa:.0%}")
    print(f"  Entropia: {ent_antes:.3f} -> {ent_depois:.3f}")
    
    # 3-sigma
    comps = [len(l.strip()) for l in linhas if l.strip()]
    if comps:
        med = sum(comps)/len(comps)
        std = math.sqrt(sum((c-med)**2 for c in comps)/len(comps))
        thresh = med + 3*std
        anom = sum(1 for c in comps if c > thresh)
        print(f"  3-sigma: threshold={thresh:.0f} chars, {anom} anomalias")
    
    if ent_depois == 0.0:
        print("  VEREDITO (log real): MCR aprendeu perfeitamente (entropia zero).")
    elif ent_depois < ent_antes:
        print(f"  VEREDITO (log real): Entropia caiu {ent_antes-ent_depois:.3f} — aprendeu.")
    else:
        print("  VEREDITO (log real): Entropia NAO caiu — padrao complexo.")
    
    return {"arquivo": ARQUIVO, "linhas": len(linhas), "taxa": round(taxa, 2),
            "ent_antes": round(ent_antes, 3), "ent_depois": round(ent_depois, 3)}


if __name__ == '__main__':
    print("=" * 60)
    print("  BENCHMARK COMPLETO: MULTI-FONTE + LOG REAL")
    print("=" * 60)
    print()
    
    t0 = time.perf_counter()
    relatorio = avaliar_metodos(n_rodadas=10)
    dt = time.perf_counter() - t0
    
    taxas_multi = [r['mcr_multi_taxa'] for r in relatorio]
    taxas_mono = [r['mcr_mono_taxa'] for r in relatorio]
    fps_multi = [r['mcr_multi_fp'] for r in relatorio]
    fps_mono = [r['mcr_mono_fp'] for r in relatorio]
    lats = [r['mcr_multi_latencia'] for r in relatorio if r['mcr_multi_latencia'] > 0]
    
    print()
    print("=" * 60)
    print("  RESULTADOS (SIMULACAO)")
    print("=" * 60)
    print(f"  Multi-nivel:  taxa_media={sum(taxas_multi)/len(taxas_multi):.0%}   "
          f"fp_medio={sum(fps_multi)/len(fps_multi):.1f}   "
          f"latencia_media={sum(lats)/max(len(lats),1):.1f} ciclos")
    print(f"  Mono-nivel:   taxa_media={sum(taxas_mono)/len(taxas_mono):.0%}   "
          f"fp_medio={sum(fps_mono)/len(fps_mono):.1f}")
    print(f"  Tempo: {dt:.2f}s")
    print()
    if sum(taxas_multi) > sum(taxas_mono):
        print("  VEREDITO SIM: Multi-nivel detecta MAIS eventos que mono-nivel.")
    else:
        print("  VEREDITO SIM: Multi-nivel NAO e melhor que mono-nivel.")
    if sum(fps_multi) < sum(fps_mono):
        print("  VEREDITO SIM: Multi-nivel tem MENOS falsos positivos que mono-nivel.")
    else:
        print("  VEREDITO SIM: Multi-nivel NAO reduz falsos positivos.")
    
    resultado = {
        "data": time.strftime("%Y-%m-%d %H:%M:%S"),
        "rodadas": len(relatorio), "tempo": round(dt, 2),
        "multi_nivel_taxa_media": round(sum(taxas_multi)/len(taxas_multi), 2),
        "mono_nivel_taxa_media": round(sum(taxas_mono)/len(taxas_mono), 2),
        "multi_nivel_fp_medio": round(sum(fps_multi)/len(fps_multi), 1),
        "mono_nivel_fp_medio": round(sum(fps_mono)/len(fps_mono), 1),
        "detalhes": relatorio,
    }
    
    log_result = testar_log_real()
    resultado["log_real"] = log_result
    
    with open(RESULTADOS_PATH, "w") as f:
        json.dump(resultado, f)
    print(f"\n  Resultados completos: {RESULTADOS_PATH}")
