"""Teste rapido do Router Hibrido (Fase 0)."""
import sys
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.ia import IA

ia = IA()

testes = [
    ('O que e SPA no MCR?', 'local'),
    ('pesquise python 3.13', 'cloud'),
    ('pesquisar ollama', 'cloud'),
    ('quem e albert einstein?', 'cloud'),
    ('noticias tecnologia 2026', 'cloud'),
    ('lancamento python 3.13', 'cloud'),
    ('versoes do python', 'cloud'),
    ('diferenca entre ipv4 e ipv6', 'cloud'),
    ('cria npc ferreiro lua', 'local'),
    ('como funciona um loop', 'cloud'),
    ('definicao de algoritmo', 'cloud'),
    ('cria script lua para shop', 'local'),
    ('busque na web sobre ollama', 'cloud'),
]

print("=== Testes Router Hibrido (Fase 0) ===")
all_ok = True
for consulta, esperado in testes:
    resultado = ia.decider(consulta)
    status = 'OK' if resultado == esperado else 'FAIL'
    if status != 'OK':
        all_ok = False
    print(f'  [{status}] "{consulta:40s}" -> {resultado:6s} (esperado: {esperado})')

print(f"\nResultado: {'TODOS OK' if all_ok else 'ALGUNS FALHARAM'}")

# Teste buscar_web (apenas se DDGS disponivel)
if '_HAS_DDGS' in dir(sys.modules['modulos.ia']):
    print("\n=== Teste buscar_web (opcional) ===")
    res = ia.buscar_web("python 3.13 release date", max_resultados=3)
    if res:
        print(f"  Web search funcionou! {len(res)} chars")
        print(f"  Resumo: {res[:200]}...")
    else:
        print("  Web search retornou None (pode ser rede)")
else:
    print("\n  DDGS nao detectado, pulando teste web")
