"""33_llm_pertencimento.py — Os 'erros' do MCR sao pertencimento real?

Kheltz: "voce precisa verificar se o que o MCR 'errou' de fato e
um erro, e nao 'outro caso collatz'"

Hipotese: os 'erros' do Teste 32 sao pertencimento parcial REAL.
- BERT -> arch_gpt: BERT e GPT sao ambos transformer com LayerNorm.
  A unica diferenca e o attention mask (nao e peso!). Nos PESOS,
  sao estatisticamente identicos.
- attention_k -> attention_v: ambos N(0, 0.01-0.02). IDENTICOS.
- embedding -> bias: ambos N(0, 0.01). Mesma distribuicao.

Verificar:
1. Divergencia estatistica (KS test) entre camadas 'confundidas'
2. Se divergencia < threshold, sao pertencimento real (nao erro)
3. Aplicar formigueiro (pertencimento multiplo) aos pesos
4. Ver N niveis: byte -> float -> camada -> arquitetura
"""
import sys, os, struct, random, json, math
from collections import defaultdict, Counter
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding="utf-8")

from mcr.coupling import MCRCoupling
from mcr.formigueiro import Formigueiro
from tools.baselines._llm_pesos_helpers import gerar_pesos, pesos_para_bytes, bytes_para_texto, gerar_arquitetura


def ks_divergence(amostra1, amostra2):
    """Kolmogorov-Smirnov: divergencia maxima entre CDFs.
    
    KS = 0.0 => distribuicoes identicas
    KS = 1.0 => completamente diferentes
    """
    n1, n2 = len(amostra1), len(amostra2)
    if n1 == 0 or n2 == 0:
        return 1.0
    
    combined = sorted(set(amostra1 + amostra2))
    cdf1 = [sum(1 for x in amostra1 if x <= c) / n1 for c in combined]
    cdf2 = [sum(1 for x in amostra2 if x <= c) / n2 for c in combined]
    
    return max(abs(a - b) for a, b in zip(cdf1, cdf2))


def estatisticas_pesos(pesos):
    """Estatisticas basicas de uma lista de pesos."""
    n = len(pesos)
    if n == 0:
        return {"media": 0, "std": 0, "min": 0, "max": 0}
    media = sum(pesos) / n
    var = sum((p - media) ** 2 for p in pesos) / n
    std = math.sqrt(var)
    return {
        "media": round(media, 6),
        "std": round(std, 6),
        "min": round(min(pesos), 6),
        "max": round(max(pesos), 6),
    }


def main():
    print("=" * 70)
    print("  TESTE 33 — Os 'erros' do MCR sao pertencimento real?")
    print("  (Caso Collatz nos pesos de LLM)")
    print("=" * 70)

    # === Fase 1: Divergencia estatistica entre camadas ===
    print("\n[1] Divergencia KS entre tipos de camada...")
    
    tipos_camada = [
        "embedding", "attention_q", "attention_k", "attention_v",
        "attention_o", "ffn_up", "ffn_down",
        "layernorm_gamma", "layernorm_beta",
        "output_proj", "positional", "bias",
    ]
    
    # Gerar amostras de cada tipo
    amostras = {}
    for tipo in tipos_camada:
        amostras[tipo] = gerar_pesos(tipo, 512, seed=42)
    
    # Matriz de divergencia KS
    print(f"\n  {'':22s}", end="")
    for t in tipos_camada[:6]:
        print(f" {t[:8]:>10s}", end="")
    print()
    
    divergencias = {}
    for t1 in tipos_camada:
        print(f"  {t1[:22]:<22s}", end="")
        for t2 in tipos_camada[:6]:
            ks = ks_divergence(amostras[t1], amostras[t2])
            divergencias[(t1, t2)] = ks
            if t1 == t2:
                print(f" {'---':>10s}", end="")
            elif ks < 0.05:
                print(f" {ks:.3f}==", end="")
            elif ks < 0.15:
                print(f" {ks:.3f}~", end="")
            else:
                print(f" {ks:.3f} ", end="")
        print()
    
    # === Fase 2: Identificar clusters de camadas identicas ===
    print("\n[2] Clusters de camadas com distribuicoes identicas (KS < 0.05)...")
    clusters = defaultdict(list)
    ja_visto = set()
    
    for t1 in tipos_camada:
        if t1 in ja_visto:
            continue
        cluster = [t1]
        for t2 in tipos_camada:
            if t2 == t1 or t2 in ja_visto:
                continue
            ks = ks_divergence(amostras[t1], amostras[t2])
            if ks < 0.05:
                cluster.append(t2)
                ja_visto.add(t2)
        ja_visto.add(t1)
        clusters[tuple(cluster)] = cluster
    
    for i, (key, cluster) in enumerate(clusters.items()):
        stats = estatisticas_pesos(amostras[cluster[0]])
        print(f"  Cluster {i+1}: {cluster}")
        print(f"    stats: media={stats['media']}, std={stats['std']}")
    
    # === Fase 3: Os 'erros' do Teste 32 sao pertencimento real? ===
    print("\n[3] Analisando os 'erros' do Teste 32...")
    
    erros_teste32 = [
        ("embedding", "cam_bias", "embedding -> bias"),
        ("attention_q", "cam_ffn_up", "attention_q -> ffn_up"),
        ("attention_k", "cam_attention_v", "attention_k -> attention_v"),
        ("attention_v", "cam_attention_k", "attention_v -> attention_k"),
        ("ffn_up", "cam_attention_k", "ffn_up -> attention_k"),
        ("ffn_down", "cam_attention_v", "ffn_down -> attention_v"),
        ("output_proj", "cam_layernorm_gamma", "output_proj -> layernorm_gamma"),
        ("bias", "cam_attention_o", "bias -> attention_o"),
    ]
    
    print(f"\n  {'Erro':<35s} {'KS':>6s} {'Veredito':<30s}")
    print("  " + "-" * 75)
    
    erros_reais = 0
    pertencimento_real = 0
    
    for tipo_real, acao_predita, descricao in erros_teste32:
        tipo_predito = acao_predita.replace("cam_", "")
        if tipo_predito in amostras:
            ks = ks_divergence(amostras[tipo_real], amostras[tipo_predito])
            if ks < 0.05:
                veredito = "PERTENCIMENTO REAL (==)"
                pertencimento_real += 1
            elif ks < 0.15:
                veredito = "SIMILAR (~)"
                pertencimento_real += 1
            else:
                veredito = "ERRO GENUINO"
                erros_reais += 1
            print(f"  {descricao:<35s} {ks:>6.3f} {veredito}")
        else:
            print(f"  {descricao:<35s} {'N/A':>6s} N/A")
    
    print(f"\n  Pertencimento real: {pertencimento_real}/{len(erros_teste32)}")
    print(f"  Erros genuinos: {erros_reais}/{len(erros_teste32)}")
    
    # === Fase 4: BERT vs GPT — pertencimento real? ===
    print("\n[4] BERT vs GPT — pertencimento real nos pesos?")
    
    # Gerar pesos de cada camada de BERT e GPT
    _, camadas_gpt = gerar_arquitetura("gpt", n_layers=2, n_pesos=256, seed=1)
    _, camadas_bert = gerar_arquitetura("bert", n_layers=2, n_pesos=256, seed=1)
    _, camadas_llama = gerar_arquitetura("llama", n_layers=2, n_pesos=256, seed=1)
    
    # Comparar tipos de camadas entre arquiteturas
    tipos_unicos_gpt = set(camadas_gpt)
    tipos_unicos_bert = set(camadas_bert)
    tipos_unicos_llama = set(camadas_llama)
    
    print(f"  GPT camadas: {sorted(tipos_unicos_gpt)}")
    print(f"  BERT camadas: {sorted(tipos_unicos_bert)}")
    print(f"  LLAMA camadas: {sorted(tipos_unicos_llama)}")
    
    # Camadas compartilhadas entre GPT e BERT
    compartilhadas = tipos_unicos_gpt & tipos_unicos_bert
    so_gpt = tipos_unicos_gpt - tipos_unicos_bert
    so_bert = tipos_unicos_bert - tipos_unicos_gpt
    
    print(f"\n  Compartilhadas GPT/BERT: {sorted(compartilhadas)}")
    print(f"  So GPT: {sorted(so_gpt)}")
    print(f"  So BERT: {sorted(so_bert)}")
    
    # Divergencia entre GPT e BERT (camada por camada)
    ks_gpt_bert = []
    for tipo in sorted(compartilhadas):
        pesos_gpt = gerar_pesos(tipo, 256, seed=1)
        pesos_bert = gerar_pesos(tipo, 256, seed=1)
        ks = ks_divergence(pesos_gpt, pesos_bert)
        ks_gpt_bert.append((tipo, ks))
    
    ks_medio = sum(ks for _, ks in ks_gpt_bert) / len(ks_gpt_bert) if ks_gpt_bert else 0
    print(f"\n  KS medio GPT vs BERT (camada por camada): {ks_medio:.4f}")
    if ks_medio < 0.05:
        print(f"  >>> GPT e BERT sao PERTENCIMENTO REAL nos pesos!")
        print(f"  >>> A diferenca (attention mask) NAO esta nos pesos.")
        print(f"  >>> O MCR 'errou' dizendo BERT=GPT — estava CERTO!")
    
    # === Fase 5: Formigueiro — pertencimento multiplo dos pesos ===
    print("\n[5] Formigueiro: pertencimento multiplo dos pesos de LLM...")
    
    c = MCRCoupling()
    n_treino = 15
    n_pesos = 128
    
    for tipo in tipos_camada:
        for i in range(n_treino):
            pesos = gerar_pesos(tipo, n_pesos + i * 16, seed=i)
            blob = pesos_para_bytes(pesos)
            texto = bytes_para_texto(blob)
            c.alimentar(texto, "cam_" + tipo)
    
    # Construir formigueiro
    f = Formigueiro(c)
    resultado_form = f.construir()
    print(f"  Clusters: {resultado_form['n_clusters']}")
    print(f"  Threshold: {resultado_form['threshold']}")
    print(f"  Pertencimento medio: {resultado_form['pertencimento_medio']}")
    print(f"  Acoes por cluster:")
    for nome, acoes in resultado_form['clusters'].items():
        print(f"    {nome}: {sorted(acoes)}")
    
    # === Fase 6: Pertencimento de cada camada ===
    print("\n[6] Pertencimento de cada camada (zero-shot)...")
    for tipo in tipos_camada:
        pesos = gerar_pesos(tipo, n_pesos * 2, seed=999)
        blob = pesos_para_bytes(pesos)
        texto = bytes_para_texto(blob)
        pert = f.pertencimento(texto)
        if pert:
            top3 = list(pert.items())[:3]
            pert_str = ", ".join(f"{n}:{g:.2f}" for n, g in top3)
            print(f"  {tipo:<22s} -> {pert_str}")
        else:
            print(f"  {tipo:<22s} -> (sem pertencimento)")
    
    # === Fase 7: Arquiteturas como pertencimento multiplo ===
    print("\n[7] Arquiteturas como pertencimento multiplo...")
    
    c2 = MCRCoupling()
    arquiteturas = ["gpt", "bert", "llama"]
    
    for arch in arquiteturas:
        for i in range(20):
            blob, _ = gerar_arquitetura(arch, n_layers=4 + i % 3, n_pesos=64, seed=i)
            texto = bytes_para_texto(blob)
            c2.alimentar(texto, "arch_" + arch)
    
    f2 = Formigueiro(c2)
    resultado_arch = f2.construir()
    print(f"  Clusters: {resultado_arch['n_clusters']}")
    print(f"  Pertencimento medio: {resultado_arch['pertencimento_medio']}")
    print(f"  Acoes por cluster:")
    for nome, acoes in resultado_arch['clusters'].items():
        print(f"    {nome}: {sorted(acoes)}")
    
    # Pertencimento de cada arquitetura
    print("\n  Pertencimento de cada arquitetura (zero-shot):")
    for arch in arquiteturas:
        blob, _ = gerar_arquitetura(arch, n_layers=6, n_pesos=128, seed=888)
        texto = bytes_para_texto(blob)
        pert = f2.pertencimento(texto)
        if pert:
            top3 = list(pert.items())[:3]
            pert_str = ", ".join(f"{n}:{g:.2f}" for n, g in top3)
            print(f"    {arch.upper():<8s} -> {pert_str}")
    
    # === Resumo ===
    print("\n" + "=" * 70)
    print("  RESUMO: Pertencimento nos pesos de LLM")
    print("=" * 70)
    print(f"\n  'Erros' do Teste 32 que sao pertencimento real: {pertencimento_real}/{len(erros_teste32)}")
    print(f"  Erros genuinos: {erros_reais}/{len(erros_teste32)}")
    print(f"  KS medio GPT vs BERT: {ks_medio:.4f} ({'PERTENCIMENTO' if ks_medio < 0.05 else 'DIFERENTES'})")
    print(f"  Clusters de camadas (formigueiro): {resultado_form['n_clusters']}")
    print(f"  Clusters de arquiteturas: {resultado_arch['n_clusters']}")
    
    # Salvar
    resultado = {
        "teste": "llm_pertencimento",
        "pertencimento_real": pertencimento_real,
        "erros_genuinos": erros_reais,
        "ks_gpt_vs_bert": ks_medio,
        "clusters_camadas": resultado_form['n_clusters'],
        "clusters_arquiteturas": resultado_arch['n_clusters'],
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "33_llm_pertencimento.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
