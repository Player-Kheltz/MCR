#!/usr/bin/env python3
"""Gera monster Lua com MCR + validacao — 1656 monstros reais treinados."""

import sys, os, re, time

_BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

os.chdir(_BASE)
sys.path.insert(0, ".")
__file__ = os.path.join(os.getcwd(), "MCR.py")
with open(__file__, encoding="utf-8") as f:
    _code = f.read().split("def main():")[0]
exec(compile(_code, "MCR.py", "exec"))

BRACKETS = {'{':'}', '[':']', '(':')'}
BRACKETS_REV = {v:k for k,v in BRACKETS.items()}

def brackets_ok(texto):
    pilha = []
    for ch in texto:
        if ch in BRACKETS:
            pilha.append(ch)
        elif ch in BRACKETS_REV:
            if not pilha or pilha[-1] != BRACKETS_REV[ch]:
                return False
            pilha.pop()
    return not pilha

def validar_monstro(texto):
    if not brackets_ok(texto):
        return False, "brackets desbalanceados"
    # Deve ter estrutura de monster
    if 'Game.createMonsterType' not in texto and 'monster.' not in texto:
        return False, "sem estrutura de monster"
    if not any(p in texto for p in ['monster.experience', 'monster.outfit', 'monster.health', 'monster.defense']):
        return False, "sem atributos de monster"
    if len(texto) < 30:
        return False, "texto muito curto"
    # function sem end
    n_func = len(re.findall(r'\bfunction\b', texto))
    n_end = len(re.findall(r'\bend\b', texto))
    if n_func > n_end:
        return False, f"function sem end"
    return True, "OK"

print("=" * 60)
print("  GERADOR VALIDADO DE MONSTER LUA")
print("  Base: 1656 monsters do Canary")
print("=" * 60)

c = CerebroAGI()
c.carregar(os.path.join(CACHE_DIR, "cerebro.json"))
print(f"Topicos: {len(c.topicos)}, Palavras: {c.mk_palavra.total}")

sementes = ['monster', 'local', 'monster.description', 'monster.experience', 'monster.outfit',
            'monster.health', 'monster.defense', 'monster.raceId', 'mType']

resultados = []
for semente in sementes:
    if semente not in c.mk_palavra.freq:
        print(f"  '{semente}' NAO no vocabulario")
        continue
    for tentativa in range(15):
        seq = c.mk_palavra.gerar_com_entropia(semente, passos=18)
        if not seq: continue
        tokens_limpos = [t for t in seq if not t.startswith('B:') and t != '<UNK>']
        texto = " ".join(tokens_limpos)
        if len(texto) < 30: continue
        ok, motivo = validar_monstro(texto)
        if ok:
            resultados.append((texto, semente, tentativa+1))
            print(f"  ✔ '{semente}' (tentativa #{tentativa+1})")
            break

print(f"\nTotal de monsters validos: {len(resultados)}\n")
for i, (texto, semente, t) in enumerate(resultados):
    print(f"{'─'*60}")
    print(f"  MONSTER {i+1} (semente='{semente}', tentativa #{t})")
    print(f"{'─'*60}")
    # Formata identacao basica
    linhas = texto.replace(' = ', '=').replace('{', '{\n\t').replace('}', '\n}').split('\n')
    for linha in linhas[:30]:
        print(f"  {linha.strip()}")
    if len(linhas) > 30:
        print(f"  ... (mais {len(linhas)-30} linhas)")

print(f"\n{'='*60}")
print(f"  FIM")
print(f"{'='*60}")
