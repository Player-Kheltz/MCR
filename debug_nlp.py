import sys; sys.path.insert(0, '.')
from MCR_AGI import *

print("Exemplos registrados:")
for acao, exs in MCRNLP._ex.items():
    print(f"  {acao}: {exs[:2]}")
print()

for t in ["ataque", "ataque o monstro", "go north", "north"]:
    r = MCRNLP.entender(t)
    h = MCRByteUtils.entropia_bytes(t)
    limiar = 0.5 - (h / 8.0) * 0.4
    print(f'entender("{t}"): {r}')
    scores = {}
    for acao, exs in MCRNLP._ex.items():
        melhor = max((MCRByteUtils.jaccard_bytes(t.lower(), ex) for ex in exs), default=0)
        if melhor > 0: scores[acao] = melhor
    print(f'    scores: {scores}')
    print(f'    threshold: {max(0.1, limiar):.3f} (entropy={h:.2f})')
