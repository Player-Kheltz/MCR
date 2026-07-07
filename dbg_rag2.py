import sys; sys.path.insert(0, r'E:\MCR')
from rag_mcr import MCRRAG
rag = MCRRAG()
c = rag.collection.count()
print(f'Total: {c} chunks')

# Conta por tipo de fonte
fontes = {}
if c > 0:
    r = rag.collection.get(limit=c)
    for m in r.get('metadatas', []):
        fonte = m.get('fonte', '?') if m else '?'
        # Extrai tipo do path
        if 'PERSONALIDADE' in fonte:
            tipo = 'Personagem'
        elif 'lore_base' in fonte:
            tipo = 'Lore'
        elif '.lua' in fonte:
            tipo = 'Lua Script'
        else:
            tipo = 'Outro'
        fontes[tipo] = fontes.get(tipo, 0) + 1

for t, q in sorted(fontes.items(), key=lambda x: -x[1]):
    print(f'  {t}: {q}')

# Testa busca por termos Tibia
print(f'\n--- Teste de busca ---')
testes = ['criar npc', 'actionid', 'funcao Lua', 'SPA']
for t in testes:
    docs = rag.buscar_hibrido(t, k=2)
    print(f'\n  Busca: {t} -> {len(docs)} resultados')
    for d in docs:
        print(f'    [{d.get("fonte","?")} score={d.get("score",0):.2f}] {d["texto"][:60]}')
