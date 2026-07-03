"""Teste rapido do GeradorDeTestes."""
import sys, os
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
sys.path.insert(0, 'E:/Projeto MCR')

# Importa direto do sandbox
sys.path.insert(0, 'E:/Projeto MCR/sandbox')
from _test_bateria import GeradorDeTestes, extrair_contexto, extrair_linguagem
from modulos.ia import IA

ia = IA()
gerador = GeradorDeTestes(ia)

print("=== Teste GeradorDeTestes ===\n")

# Teste 1: Gerar request sem historico
print("1. Gerar request cenario 1 (sem historico)...")
req = gerador.gerar_request(1)
print(f"   Request: {req[:100]}...")
assert req and len(req) > 15
print("   OK")

# Teste 2: Gerar request com historico (deve evitar repeticoes)
print("\n2. Gerar request cenario 2 (com historico)...")
projetos = [{'id': 1, 'contexto': 'jogo', 'linguagem': 'python'}]
req2 = gerador.gerar_request(2, projetos)
print(f"   Request: {req2[:100]}...")
assert req2 and len(req2) > 15
print("   OK")

# Teste 3: Gerar multiplos e verificar diversidade
print("\n3. Gerar 3 requests cenario 3...")
requests = set()
for i in range(3):
    req = gerador.gerar_request(3, projetos)
    requests.add(req[:50])  # primeiros 50 chars
    print(f"   [{i+1}] {req[:80]}...")
print(f"   Variacao: {len(requests)}/3 unicos")
# Pode repetir se FAST falhar, mas idealmente sao diferentes

# Teste 4: extrair_contexto
print("\n4. extrair_contexto()...")
assert extrair_contexto("Cria um jogo de plataforma") == 'jogo'
assert extrair_contexto("Cria uma API REST em Flask") == 'api'
assert extrair_contexto("Cria uma CLI tool") == 'cli'
print("   OK")

# Teste 5: extrair_linguagem
print("\n5. extrair_linguagem()...")
assert extrair_linguagem("Cria um jogo em Python com Pygame") == 'python'
assert extrair_linguagem("Cria um site em HTML e JavaScript") == 'javascript'
assert extrair_linguagem("Cria um jogo em Lua com Love2D") == 'lua'
print("   OK")

print("\n=== TODOS OS TESTES OK ===")
