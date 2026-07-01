"""Debug dos patterns do léxico v2 — importa do módulo real."""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.lexico_v2 import tokenizar_v2, _LEXICO

# Testa patterns de INTENT
print("=== INTENT PATTERNS ===")
for cat, pattern, conf in _LEXICO:
    if cat.startswith("INTENT_"):
        print(f"\n{cat} (conf={conf}):")
        for teste in [
            "busque algo", "Busque", "buscar", "o que e", "O que e Canary",
            "explique", "Explique", "crie", "Crie um", "adicione",
            "revise", "implemente", "como funciona"
        ]:
            try:
                m = re.search(pattern, teste.lower())
                if m:
                    print(f"  ✅ '{teste}' -> match('{m.group()}')")
            except Exception as e:
                print(f"  ❌ '{teste}' -> ERROR: {e}")

# Testa tokenizer real
print("\n\n=== TOKENIZER V2 (MÓDULO REAL) ===")
for frase in [
    "Busque a definicao de SPA no codigo",
    "O que e Canary no contexto do MCR",
    "Explique o sistema SPA do MCR",
    "Crie um NPC Ferreiro em Eridanus",
    "Adicione 'Eridanus = Cidade Inicial' ao arquivo TESTE.md",
]:
    tokens = tokenizar_v2(frase)
    print(f"\n  '{frase[:50]}'")
    for t, p, c in tokens:
        inicio = "→" if t.startswith("INTENT_") or t.startswith("DOM_") or t == "PROPER_NOUN" else " "
        print(f"    {inicio} {t:20s} | '{p}' | conf={c:.2f}")
