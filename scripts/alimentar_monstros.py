#!/usr/bin/env python3
"""Alimenta MCR com monsters reais do Canary (data-otservbr-global/monster)."""

import sys, os, time

os.chdir(r"E:\MCR")
sys.path.insert(0, ".")
__file__ = os.path.join(os.getcwd(), "MCR.py")
with open(__file__, encoding="utf-8") as f:
    _code = f.read().split("def main():")[0]
exec(compile(_code, "MCR.py", "exec"))

RAIZ = r"E:\Projeto MCR\Canary\data-otservbr-global\monster"
BATCH_SIZE = 10

print("=" * 60)
print("  ALIMENTANDO MONSTROS DO CANARY")
print("=" * 60)

c = CerebroAGI()
t0 = time.perf_counter()

arquivos = []
for raiz, dirs, files in os.walk(RAIZ):
    for f in files:
        if not f.endswith('.lua'): continue
        fp = os.path.join(raiz, f)
        tam = os.path.getsize(fp)
        if 50 <= tam <= 200000:
            nome_rel = os.path.relpath(fp, RAIZ)
            arquivos.append((nome_rel, fp, tam))

print(f"  {len(arquivos)} monsters Lua ({sum(a[2] for a in arquivos)/1024:.0f} KB)")

batch_textos = []
n_arqs = 0
n_batches = 0

for nome_rel, fp, tam in arquivos:
    try:
        with open(fp, 'r', encoding='utf-8', errors='replace') as f:
            texto = f.read()
        batch_textos.append(texto)
        
        if len(batch_textos) >= BATCH_SIZE:
            texto_batch = "\n\n--[[ SEP ]]\n\n".join(batch_textos)
            c.alimentar(texto_batch[:40000], f"monster_batch_{n_batches}")
            n_batches += 1
            n_arqs += len(batch_textos)
            
            if n_batches % 5 == 0:
                t = time.perf_counter()
                print(f"  [{n_arqs}/{len(arquivos)}] b={n_batches} "
                      f"ent={c.mk_palavra.entropia_media():.2f} "
                      f"{n_arqs/max(t-t0,0.1):.1f} arqs/s {t-t0:.0f}s")
            
            batch_textos = []
    except: pass

if batch_textos:
    texto_batch = "\n\n--[[ SEP ]]\n\n".join(batch_textos)
    c.alimentar(texto_batch[:40000], f"monster_batch_{n_batches}")
    n_arqs += len(batch_textos)
    n_batches += 1

t1 = time.perf_counter()
print(f"\n{'='*60}")
print(f"  RESUMO")
print(f"{'='*60}")
print(f"  Monstros: {n_arqs}")
print(f"  Batches: {n_batches}")
print(f"  Tempo: {t1-t0:.1f}s ({n_arqs/max(t1-t0,0.01):.1f} arqs/s)")
print(f"  Topicos: {len(c.topicos)}")
print(f"  Transicoes palavra: {c.mk_palavra.total}")
print(f"  Vocabulario: {len(c.mk_palavra.freq)}")
print(f"  Entropia: {c.mk_palavra.entropia_media():.3f}")

for palavra in ['monster', 'type', 'name', 'experience', 'health', 'loot', 'flags', 'voices']:
    if palavra in c.mk_palavra.freq:
        pred, conf = c.mk_palavra.predizer(palavra)
        print(f"  '{palavra}' (freq={c.mk_palavra.freq[palavra]}) → '{pred}' (conf={conf:.2f})")
    else:
        print(f"  '{palavra}' NAO encontrada")

c.salvar()
print(f"\n  Cerebro salvo!")
