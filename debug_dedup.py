import sys, os, re, sqlite3
os.chdir("E:\\MCR")
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
__file__ = os.path.join(os.getcwd(), "MCR.py")
with open(__file__, encoding="utf-8") as f:
    exec(compile(f.read().split("def main():")[0], "MCR.py", "exec"))

# Replay the exact alimentar logic for Ahmet
def tokenizar(texto):
    tokens = []
    i = 0
    while i < len(texto):
        c = texto[i]
        if c.isspace(): i += 1; continue
        if c in ('"', "'"):
            quote = c; j = i + 1
            while j < len(texto) and texto[j] != quote: j += 1
            tokens.append(texto[i:j+1] if j < len(texto) else texto[i:])
            i = (j + 1) if j < len(texto) else len(texto)
            continue
        if c.isalnum() or c in '_.':
            j = i
            while j < len(texto) and (texto[j].isalnum() or texto[j] in '_.'): j += 1
            tokens.append(texto[i:j]); i = j
            continue
        if c in ',;:+-*/<>~|&#@%^=':
            tokens.append(c); i += 1; continue
        if c in '()[]{}':
            tokens.append(c); i += 1; continue
        tokens.append(c); i += 1
    return tokens

with open(r"E:\Projeto MCR\Canary\data-otservbr-global\npc\ahmet.lua", "r", encoding="utf-8", errors="replace") as f:
    texto = f.read()

nome = "Ahmet"
tokens = tokenizar(texto)
print(f"Tokens: {len(tokens)}")
print(f"First 20: {tokens[:20]}")

# Phase 1: collect counts
n_max = 30
counts = {}
for n in range(1, n_max + 1):
    for i in range(len(tokens) - n):
        chave = (n,) + tuple(tokens[i:i+n])
        prox = tokens[i+n]
        if chave not in counts:
            counts[chave] = {}
        counts[chave][prox] = counts[chave].get(prox, 0) + 1

print(f"Counts entries: {len(counts)}")

# Phase 2: dedup
N_KEEP = 5
kept = {n: 0 for n in range(1, 31)}
total = {n: 0 for n in range(1, 31)}
dedup_removed = {n: 0 for n in range(1, 31)}

for (n, *ctx), nexts in counts.items():
    total[n] = total.get(n, 0) + 1
    keep = n <= N_KEEP
    if not keep:
        sufixo = tuple(ctx[1:])
        parent_key = (n-1,) + sufixo
        parent = counts.get(parent_key)
        if parent is None:
            keep = True  # parent not found in counts
        elif set(nexts.keys()) != set(parent.keys()):
            keep = True
        else:
            keep = False
            dedup_removed[n] = dedup_removed.get(n, 0) + 1
    if keep:
        kept[n] = kept.get(n, 0) + 1

print(f"\nN-level distribution:")
for n in range(1, 31):
    if total.get(n, 0) > 0:
        print(f"  N={n}: total={total[n]}, kept={kept[n]}, removed={dedup_removed.get(n,0)}")

# Check specific N=10 key
key_n10 = (10, 'creatureSayCallback', '(', 'npc', ',', 'creature', ',', 'type', ',', 'message', ')')
key_n9 = (9, '(', 'npc', ',', 'creature', ',', 'type', ',', 'message', ')')
print(f"\nN=10 key: {'FOUND' if key_n10 in counts else 'NOT FOUND'}")
print(f"  Nexts: {counts.get(key_n10, {})}")
print(f"N=9 key: {'FOUND' if key_n9 in counts else 'NOT FOUND'}")
print(f"  Nexts: {counts.get(key_n9, {})}")
