import sys, time
sys.path.insert(0, r'E:\MCR')
from mcr_devia import processar, _memoria

# Teste 1: criar NPC com itens
pergunta = "Crie um NPC chamado Mercador de Fogo que vende Ultimate Healing Rune (clientId 2273) por 100 gold e compra Demon Armor (clientId 12345) por 500 gold"

print('[TESTE] Criar NPC com itens...')
t0 = time.time()
r = processar(pergunta)
t = time.time() - t0

resp = r.get('resposta', '')
cl = r.get('classe', '?')
sv = r.get('sintaxe_valida')
print(f'Tempo: {t:.1f}s')
print(f'Classe: {cl}')
print(f'Sintaxe: {sv}')
print(f'Tamanho: {len(resp)}')
print()
print(resp[:500])

if '12345' in resp:
    print('\n[ITEM CHECK] ID 12345 presente (item database validation)')
else:
    print('\n[ITEM CHECK] ID 12345 removido - nao existe no items.xml')

# Teste 2: memoria episodica
if _memoria:
    print('\n[MEMORIA] Buscando episodio...')
    t0 = time.time()
    r2 = processar('crie um npc de fogo chamado Aprendiz mercador')
    t = time.time() - t0
    resp2 = r2.get('resposta', '')
    print(f'Tempo: {t:.1f}s')
    print(f'Resposta: {resp2[:100]}')
