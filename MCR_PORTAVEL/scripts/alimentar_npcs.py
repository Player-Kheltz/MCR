#!/usr/bin/env python3
"""Alimenta MCR com 1034 NPCs reais do Canary (data-otservbr-global/npc)."""

import sys, os, time

os.chdir(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ".")
try:
    from MCR import CerebroAGI
except ImportError:
    CerebroAGI = None

RAIZ = os.path.join(os.path.dirname(__file__), '..', 'server', 'data-otservbr-global', 'npc')
BATCH_SIZE = 10

print("=" * 60)
print("  ALIMENTANDO 1034 NPCs REAIS DO CANARY")
print("=" * 60)

c = CerebroAGI()
t0 = time.perf_counter()

# Coleta arquivos
arquivos = []
for raiz, dirs, files in os.walk(RAIZ):
    for f in files:
        if not f.endswith('.lua'): continue
        fp = os.path.join(raiz, f)
        tam = os.path.getsize(fp)
        if 50 <= tam <= 200000:
            nome_rel = os.path.relpath(fp, RAIZ)
            arquivos.append((nome_rel, fp, tam))

print(f"  {len(arquivos)} NPCs Lua ({sum(a[2] for a in arquivos)/1024:.0f} KB)")

# Processa em batches
batch_textos = []
batch_nomes = []
n_arqs = 0
n_batches = 0

for nome_rel, fp, tam in arquivos:
    try:
        with open(fp, 'r', encoding='utf-8', errors='replace') as f:
            texto = f.read()
        batch_textos.append(texto)
        batch_nomes.append(nome_rel)
        
        if len(batch_textos) >= BATCH_SIZE:
            texto_batch = "\n\n--[[ SEPARADOR ]]\n\n".join(batch_textos)
            c.alimentar(texto_batch[:40000], f"npc_batch_{n_batches}")
            n_batches += 1
            n_arqs += len(batch_textos)
            
            if n_batches % 5 == 0:
                t = time.perf_counter()
                print(f"  [{n_arqs}/{len(arquivos)}] batches={n_batches} "
                      f"p_ent={c.mk_palavra.entropia_media():.2f} "
                      f"{n_arqs/max(t-t0,0.1):.1f} arqs/s {t-t0:.0f}s")
            
            batch_textos = []
    except Exception: pass

# Ultimo batch
if batch_textos:
    texto_batch = "\n\n--[[ SEPARADOR ]]\n\n".join(batch_textos)
    c.alimentar(texto_batch[:40000], f"npc_batch_{n_batches}")
    n_arqs += len(batch_textos)
    n_batches += 1

t1 = time.perf_counter()
print(f"\n{'='*60}")
print(f"  RESUMO")
print(f"{'='*60}")
print(f"  NPCs processados: {n_arqs}")
print(f"  Batches: {n_batches}")
print(f"  Tempo: {t1-t0:.1f}s ({n_arqs/max(t1-t0,0.01):.1f} arqs/s)")
print(f"  Topicos: {len(c.topicos)}")
print(f"  Transicoes palavra: {c.mk_palavra.total}")
print(f"  Vocabulario: {len(c.mk_palavra.freq)} palavras")
print(f"  Entropia palavra: {c.mk_palavra.entropia_media():.3f}")

# Palavras-chave NPC
for palavra in ['npcConfig', 'onSay', 'onGreet', 'shop', 'greet', 'name', 'local']:
    if palavra in c.mk_palavra.freq:
        pred, conf = c.mk_palavra.predizer(palavra)
        print(f"  '{palavra}' (freq={c.mk_palavra.freq[palavra]}) → '{pred}' (conf={conf:.2f})")
    else:
        print(f"  '{palavra}' NAO encontrada no vocabulario")

c.salvar()
print(f"\n  Cerebro salvo!")
