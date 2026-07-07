"""Auto-calibra thresholds do MarkovDecider e MarkovRouter.
Roda a cada 50 interacoes. Nao depende do MCRAutoEvolution."""
import os, json, time

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(CACHE, exist_ok=True)

def calibrar(decider, router, filter_stats, ultimos_erros):
    """Ajusta thresholds baseado nos erros recentes."""
    path = os.path.join(CACHE, "calibracao.json")
    hist = {}
    if os.path.exists(path):
        try:
            with open(path) as f:
                hist = json.load(f)
        except:
            pass
    
    total = hist.get("total_ciclos", 0) + 1
    hist["total_ciclos"] = total
    hist["ultima_calibracao"] = time.time()
    
    # Ajusta confianca minima do MarkovDecider baseado no FeedbackFilter
    taxa_aceite = filter_stats.get("taxa_aceite", 50)
    if taxa_aceite < 30:
        # Muitas rejeicoes: sobe a confianca minima
        decider.thr.observar(1.0)
    elif taxa_aceite > 90:
        # Muitas aceitacoes: pode baixar
        decider.thr.observar(0.3)
    
    hist["taxa_aceite"] = taxa_aceite
    hist["decider_total"] = decider.total
    hist["router_rotas"] = len(router.SEEDS)
    hist["erros_recentes"] = len(ultimos_erros)
    
    with open(path, "w") as f:
        json.dump(hist, f)
    
    return hist
