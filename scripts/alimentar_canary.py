#!/usr/bin/env python3
"""Alimenta MCR com scripts .lua do Canary — alimentar() correto, batch."""

import sys, os, time

os.chdir(r"E:\MCR")
sys.path.insert(0, ".")
__file__ = os.path.join(os.getcwd(), "MCR.py")
with open(__file__, encoding="utf-8") as f:
    _code = f.read().split("def main():")[0]
exec(compile(_code, "MCR.py", "exec"))

RAIZ = r"E:\Projeto MCR\Canary\data"
IGNORAR_DIRS = {'.git', '__pycache__', 'vcpkg', 'build', 'bin', 'obj'}
BATCH_SIZE = 15  # arquivos por batch

print("=" * 55)
print("  ALIMENTANDO CANARY — BATCH OTIMIZADO")
print(f"  Raiz: {RAIZ}")
print(f"  Batch: {BATCH_SIZE} arquivos por chamada")
print("=" * 55)

c = CerebroAGI()
t0 = time.perf_counter()
n_arqs = 0
n_batches = 0

# Coleta arquivos
arquivos = []
for raiz, dirs, files in os.walk(RAIZ):
    dirs[:] = [d for d in dirs if d not in IGNORAR_DIRS and not d.startswith('.')]
    for f in files:
        if not f.endswith('.lua'): continue
        fp = os.path.join(raiz, f)
        tam = os.path.getsize(fp)
        if 30 <= tam <= 200000:
            nome_rel = os.path.relpath(fp, RAIZ)
            arquivos.append((nome_rel, fp, tam))

print(f"  {len(arquivos)} arquivos Lua ({sum(a[2] for a in arquivos)/1024:.0f} KB)")

# Processa em batches
batch_textos = []
batch_nomes = []
batch_tamanho = 0

for nome_rel, fp, tam in arquivos:
    try:
        with open(fp, 'r', encoding='utf-8', errors='replace') as f:
            texto = f.read()
        batch_textos.append(texto)
        batch_nomes.append(nome_rel)
        batch_tamanho += len(texto)
        
        if len(batch_textos) >= BATCH_SIZE or batch_tamanho > 80000:
            # Junta batch em 1 texto e alimenta
            texto_batch = "\n\n---\n\n".join(batch_textos)
            c.alimentar(texto_batch[:50000], f"batch_{n_batches}")
            n_batches += 1
            n_arqs += len(batch_textos)
            
            if n_batches % 10 == 0:
                t = time.perf_counter()
                ent_b = c.mk_byte.entropia_media()
                ent_p = c.mk_palavra.entropia_media()
                print(f"  [{n_arqs}/{len(arquivos)}] batches={n_batches} "
                      f"b_ent={ent_b:.2f} p_ent={ent_p:.2f} "
                      f"{n_arqs/max(t-t0,0.1):.1f} arqs/s "
                      f"{t-t0:.0f}s")
            
            batch_textos = []
            batch_tamanho = 0
    except: pass

# Ultimo batch
if batch_textos:
    texto_batch = "\n\n---\n\n".join(batch_textos)
    c.alimentar(texto_batch[:50000], f"batch_{n_batches}")
    n_batches += 1
    n_arqs += len(batch_textos)

t1 = time.perf_counter()
print(f"\n{'='*55}")
print(f"  RESUMO")
print(f"{'='*55}")
print(f"  Arquivos processados: {n_arqs}")
print(f"  Total de batches: {n_batches}")
print(f"  Tempo: {t1-t0:.1f}s")
print(f"  Velocidade: {n_arqs/max(t1-t0,0.01):.1f} arqs/s")
print(f"  Topicos: {len(c.topicos)}")
print(f"  Transicoes byte: {c.mk_byte.total}")
print(f"  Transicoes palavra: {c.mk_palavra.total}")
print(f"  Entropia byte: {c.mk_byte.entropia_media():.3f}")
print(f"  Entropia palavra: {c.mk_palavra.entropia_media():.3f}")

c.salvar()
print(f"\n  Cerebro salvo em: cache/cerebro.json")
print(f"  Pronto para prototipo!")
