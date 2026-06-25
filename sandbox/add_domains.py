"""Add arcos and lutador domains to mcr_crew.py"""
with open(r'E:\Projeto MCR\sandbox\mcr_crew.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Find the DOMINIOS dict and add new entries after clavas_leves
old = """    DOMINIOS = {
        'clavas_leves': {"""
new = """    DOMINIOS = {
        'arcos': {
            'id': 120, 'nome': 'ARCOS', 'parent': 'Precisao 13 - Combate 1',
            'elemento': 'COMBAT_PHYSICALDAMAGE', 'ids': (12001, 12020),
            'sinergia_doms': {23: 'Fogo', 24: 'Gelo', 26: 'Energia'},
            'descricao': 'arco e flecha, ataques precisos a distancia, perfuracao',
            'pool_tematico': ['flecha', 'tiro', 'arco', 'mira', 'precisao', 'disparo', 'chuva', 'perfurante', 'buscador', 'aguia', 'certeiro', 'rapido', 'triplo', 'barragem', 'sniper'],
            'palavras_proibidas': ['punho', 'soco', 'chute', 'espada', 'clava', 'machado', 'magia', 'arcano', 'bastao', 'cajado'],
        },
        'lutador': {
            'id': 130, 'nome': 'LUTADOR', 'parent': 'Artes Marciais 14 - Combate 1',
            'elemento': 'COMBAT_PHYSICALDAMAGE', 'ids': (13001, 13020),
            'sinergia_doms': {132: 'Armas de Punho', 14: 'Artes Marciais', 1: 'Combate'},
            'descricao': 'luta corpo-a-corpo, socos, chutes e quedas',
            'pool_tematico': ['soco', 'punho', 'jab', 'cruzado', 'gancho', 'chute', 'joelhada', 'combate', 'lutador', 'esquiva', 'furia', 'combo', 'quebra', 'ossos', 'impacto'],
            'palavras_proibidas': ['flecha', 'arco', 'espada', 'clava', 'magia', 'arcano', 'bastao'],
        },
        'clavas_leves': {"""

c = c.replace(old, new)

with open(r'E:\Projeto MCR\sandbox\mcr_crew.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'mcr_crew.py', 'exec')
    print('OK! Domains added: arcos, lutador, clavas_leves')
except SyntaxError as e:
    print(f'Error: {e}')
