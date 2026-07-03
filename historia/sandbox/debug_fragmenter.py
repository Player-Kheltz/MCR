"""Debug: por que o Fragmenter nao quebra perguntas?"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from analysis.fragmenter import SuperFragmentador

frag = SuperFragmentador()
texto = "Explique o sistema SPA do MCR. Crie um NPC guia em Eridanus."

print(f"Texto: {texto}")
print()

fragmentos = frag.fragmentar(texto)
print(f"Fragmentos retornados: {len(fragmentos)}")
for f in fragmentos:
    print(f"  Tipo: {type(f).__name__}")
    if hasattr(f, 'conteudo'):
        print(f"  Conteudo: '{f.conteudo[:80]}'")
    elif isinstance(f, dict):
        print(f"  Dict: {list(f.keys())}")
    else:
        print(f"  Str: {str(f)[:80]}")
    print()

# Testa fallback de divisao por pontuacao
import re
print("Fallback divisao por pontuacao:")
frases = re.split(r'[.!?\n]+(?:\s+|$)', texto)
for f in frases:
    if f.strip():
        print(f"  - {f.strip()[:60]}")
