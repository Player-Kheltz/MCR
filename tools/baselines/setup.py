"""00_setup.py — Carrega MCR com corpus para os testes de baseline.

Uso:
    python tools/baselines/00_setup.py

Tambem pode ser importado:
    from tools.baselines import setup
    c, info = setup.carregar_mcr(leve=True)   # matematico + dataset_500
    c, info = setup.carregar_mcr(leve=False)  # + Wikipedia 80K (se JSON disponivel)
"""
import sys, os, time, json
sys.path.insert(0, r"E:\MCR")

from mcr.coupling import MCRCoupling

RAIZ = r"E:\MCR"
DATASET_500 = os.path.join(RAIZ, "tests", "experimento_rigoroso", "dataset_500.json")
WIKI_JSON = os.path.join(RAIZ, "cache", "coupling_wiki_teste.json")
WIKI_CACHE = os.path.join(RAIZ, "cache", "wiki")

# Importa corpus matematico
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from corpus_matematico import alimentar_corpus_matematico, validar_corpus_matematico


def carregar_mcr(leve=True):
    """Carrega MCR com corpus.

    leve=True: corpus matematico + dataset_500 (rapido, ~2s)
    leve=False: + Wikipedia 80K (lento se treinar, rapido se JSON existe)

    Returns:
        (coupling, info_dict)
    """
    c = MCRCoupling()
    info = {"leve": leve, "fontes": []}

    # 1. Corpus matematico (sempre)
    t0 = time.time()
    acoes = alimentar_corpus_matematico(c)
    dt = time.time() - t0
    info["fontes"].append({"nome": "matematico", "tempo": dt, "acoes": dict(acoes)})
    print(f"[setup] Corpus matematico: {sum(acoes.values())} obs em {dt:.2f}s")

    # 2. Dataset_500 (sempre — para testes antigos)
    if os.path.exists(DATASET_500):
        t0 = time.time()
        with open(DATASET_500, "r", encoding="utf-8") as f:
            ds = json.load(f)
        pares = [(d["input"], d["expected_action"]) for d in ds]
        c.alimentar_lote(pares)
        dt = time.time() - t0
        info["fontes"].append({"nome": "dataset_500", "tempo": dt, "n": len(pares)})
        print(f"[setup] Dataset_500: {len(pares)} obs em {dt:.2f}s")

    # 3. Wikipedia (apenas se !leve)
    if not leve:
        if os.path.exists(WIKI_JSON):
            t0 = time.time()
            ok = c.load(WIKI_JSON)
            dt = time.time() - t0
            if ok:
                info["fontes"].append({"nome": "wiki_load", "tempo": dt})
                print(f"[setup] Wikipedia (JSON): carregado em {dt:.2f}s")
            else:
                info["fontes"].append({"nome": "wiki_load_fail", "tempo": dt})
                print(f"[setup] Wikipedia JSON falhou — vazio")
        else:
            # Treinar do zero se cache wiki existe
            if os.path.isdir(WIKI_CACHE):
                t0 = time.time()
                n = _treinar_wikipedia(c, WIKI_CACHE)
                dt = time.time() - t0
                info["fontes"].append({"nome": "wiki_train", "tempo": dt, "n": n})
                print(f"[setup] Wikipedia (treino): {n} frases em {dt:.2f}s")
            else:
                info["fontes"].append({"nome": "wiki_skip"})
                print(f"[setup] Wikipedia: cache ausente, pulando")

    # Stats finais
    info["total_obs"] = c._total
    info["vocab"] = len(c._palavra_acao)
    info["acoes"] = list(c._freq_acao.keys())
    info["n_acoes"] = len(c._freq_acao)
    print(f"[setup] OK: {info['total_obs']} obs, {info['vocab']} pal, {info['n_acoes']} acoes")
    return c, info


def _treinar_wikipedia(c, wiki_cache_dir):
    """Treina MCR com corpus Wikipedia do cache."""
    # Procura arquivos JSON no cache
    arqs = []
    for f in os.listdir(wiki_cache_dir):
        if f.endswith(".json"):
            arqs.append(os.path.join(wiki_cache_dir, f))
    if not arqs:
        return 0

    n = 0
    for arq in arqs:
        try:
            with open(arq, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if isinstance(dados, list):
                pares = [(d.get("texto", d.get("input", "")), d.get("acao", d.get("cid", "descrever")))
                         for d in dados if isinstance(d, dict)]
                c.alimentar_lote(pares)
                n += len(pares)
            elif isinstance(dados, dict):
                # Formato dict — tenta um campo
                for k, v in dados.items():
                    if isinstance(v, list):
                        pares = [(x.get("texto", x.get("input", "")), x.get("acao", x.get("cid", k)))
                                 for x in v if isinstance(x, dict)]
                        c.alimentar_lote(pares)
                        n += len(pares)
        except Exception:
            continue
    return n


def mcr_decidir(c, texto):
    """Wrapper para decidir() que retorna (acao, conf)."""
    return c.decidir(texto, (None, 0.0))


def mcr_features_top(c, texto, n=3):
    """Retorna top-n acoes por _dist_features."""
    r = c._dist_features(texto)
    if not r:
        return []
    return sorted(r.items(), key=lambda x: -x[1])[:n]


def mcr_nmi(c, a, b):
    """Calcula NMI semantico entre dois termos."""
    if hasattr(c, "_nmi_semantico"):
        ass_a = c._assinatura_palavra(a)
        ass_b = c._assinatura_palavra(b)
        if not ass_a or not ass_b:
            return 0.0
        return c._nmi_semantico(ass_a, ass_b)
    return 0.0


if __name__ == "__main__":
    print("=== Setup leve ===")
    c_leve, info_leve = carregar_mcr(leve=True)
    print()
    print("=== Setup pesado (com Wikipedia) ===")
    c_pes, info_pes = carregar_mcr(leve=False)
    print()
    print("=== Info ===")
    print(f"Leve:    {info_leve['total_obs']} obs, {info_leve['vocab']} pal, {info_leve['n_acoes']} acoes")
    print(f"Pesado:  {info_pes['total_obs']} obs, {info_pes['vocab']} pal, {info_pes['n_acoes']} acoes")
