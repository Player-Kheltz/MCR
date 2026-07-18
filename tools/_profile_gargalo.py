import sys, time, cProfile, pstats, io; sys.path.insert(0, 'E:/MCR')
from mcr.coupling import MCRCoupling

# Carregar motor principal (ja tem 68960 obs)
c = MCRCoupling()
c.load("mcr/coupling_MCRCoupling.json")
print(f"Motor: {c._total} obs, {len(c._palavra_acao)} palavras")

# Profile: 20 chamadas _assinatura_frase (gatilho do gargalo)
frases = ["cachorro late forte", "dog runs fast", "agua molha terra",
          "casa abriga pessoa", "amor une coracao", "arvore cresce floresta",
          "vermelho cor fogo", "correr rapido pular", "luz ilumina dia",
          "conhecimento aprende mente"]

print("\nProfiling _assinatura_frase (10 chamadas)...")
pr = cProfile.Profile()
pr.enable()
for f in frases:
    sig = c._assinatura_frase(f)
pr.disable()

s = io.StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
ps.print_stats(20)
print(s.getvalue())
