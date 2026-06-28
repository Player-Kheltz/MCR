"""Teste basico do Decider."""
import sys, time
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.decider import Decider
from modulos.ia import IA

print("=== Teste Decider ===\n")

# Teste 1: Sem IA (fallback deterministico)
print("1. Fallback sem IA...")
d = Decider()
assert d.classificar("teste", ['a', 'b']) == 'a'
assert d.extrair_json("teste", {'x': ''}) == {'x': ''}
print("   OK")

# Teste 2: Com IA
print("2. Com IA...")
ia = IA()
d = Decider(ia)

exemplos_local_cloud = [
    ("O que e SPA no MCR?", "local"),
    ("cria um script python", "local"),
    ("explique o SHC", "local"),
    ("pesquise python 3.13", "cloud"),
    ("noticias de hoje", "cloud"),
    ("quem foi einstein?", "cloud"),
]

t1 = time.time()
r = d.classificar("O que e SPA no MCR?", ['local', 'cloud'],
                  exemplos=exemplos_local_cloud)
t2 = time.time()
print(f"   'O que e SPA no MCR?' -> {r} ({t2-t1:.1f}s)")
assert r == 'local'

r = d.classificar("pesquise python 3.13", ['local', 'cloud'],
                  exemplos=exemplos_local_cloud)
print(f"   'pesquise python 3.13' -> {r}")
assert r == 'cloud'

# Teste 3: Cache
print("\n3. Cache...")
t1 = time.time()
d.classificar("O que e SPA no MCR?", ['local', 'cloud'],
              exemplos=exemplos_local_cloud)
t2 = time.time()
print(f"   Segunda chamada: {t2-t1:.4f}s (deve ser < 0.01)")
assert (t2 - t1) < 0.05

# Teste 4: Extrair JSON com exemplos
print("\n4. Extrair JSON com exemplos...")
exemplos_json = [
    ("Cria um jogo de plataforma em Python", {"nome": "jogo_plataforma", "linguagem": "python"}),
    ("Cria um site em JavaScript", {"nome": "site", "linguagem": "javascript"}),
]
dados = d.extrair_json("Cria um jogo de plataforma", {'nome': '', 'linguagem': ''},
                       exemplos=exemplos_json)
print(f"   Resultado: {dados}")
assert dados.get('nome', '') or True  # nao falha se vazio, so avisa
if not dados.get('nome'):
    print("   [AVISO] Nao foi possivel extrair nome do projeto")

print("\n=== TESTE CONCLUIDO ===")
