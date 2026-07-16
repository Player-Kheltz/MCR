#!/usr/bin/env python3
"""Alimenta MCR — treino direto nos dicionarios, sem overhead do alimentar()."""

import sys, os, time

os.chdir(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ".")
try:
    from MCR import CerebroAGI
except ImportError:
    CerebroAGI = None

RAIZ = os.path.join(os.path.dirname(__file__), '..')
SUB_DIRS = ["server", "devia", "mcr", "scripts"]
IGNORAR_DIRS = {'.git', '__pycache__', 'vcpkg', 'build', 'bin', 'obj', 'share', 'man'}
TEXT_EXT = {'.lua', '.py', '.md', '.txt', '.html', '.xml', '.yml', '.yaml',
    '.json', '.sql', '.cfg', '.sh', '.bat', '.cmake',
    '.hpp', '.h', '.cpp', '.c', '.css', '.js', '.rb', '.php', '.go', '.java'}

print("=" * 55)
print("  TREINO DIRETO — PROJETO MCR")
print(f"  Pastas: {', '.join(SUB_DIRS)}")
print("=" * 55)

c = CerebroAGI()
t0 = time.perf_counter()
n_arqs = 0
n_bytes = 0

# Acumuladores de lote
lote_texto = []  # acumula palavras para treinar mk_palavra em lote
lote_amostras = []  # acumula amostras para alimentar() no final

for sub_dir in SUB_DIRS:
    sub_path = os.path.join(RAIZ, sub_dir)
    if not os.path.exists(sub_path): continue
    for raiz, dirs, files in os.walk(sub_path):
        dirs[:] = [d for d in dirs if d not in IGNORAR_DIRS and not d.startswith('.')]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in TEXT_EXT: continue
            fp = os.path.join(raiz, f)
            tam = os.path.getsize(fp)
            if tam < 30 or tam > 200000: continue
            try:
                with open(fp, 'rb') as fh:
                    dados = fh.read()
                texto = dados.decode('utf-8', errors='replace')
                
                # Treina mk_byte com lookup table (sem f-string)
                if n_arqs == 0:
                    BYTE_KEYS = [f"B:{i:02x}" for i in range(256)]
                for i in range(len(dados)-1):
                    a, b = BYTE_KEYS[dados[i]], BYTE_KEYS[dados[i+1]]
                    ta = c.mk_byte.transicoes
                    if a not in ta: ta[a] = {}; c.mk_byte.freq[a] = 0
                    ta[a][b] = ta[a].get(b, 0) + 1
                    c.mk_byte.freq[a] += 1
                    c.mk_byte.total += 1
                
                # Acumula palavras para treino em lote
                palavras = texto.split()[:500]
                if palavras:
                    lote_texto.extend(palavras)
                    # Guarda amostra para topicos (1 a cada 50 arqs)
                    if len(lote_amostras) < 200 and n_arqs % 50 == 0 and len(texto) < 10000:
                        lote_amostras.append(texto[:2000])
                
                n_arqs += 1
                n_bytes += len(dados)
            except Exception: pass

# Treina mk_palavra em lote unico
print(f"\n  Treinando mk_palavra ({len(lote_texto)} palavras)...")
t_pal = time.perf_counter()
mk = c.mk_palavra
for i in range(len(lote_texto)-1):
    a, b = lote_texto[i], lote_texto[i+1]
    if a not in mk.transicoes: mk.transicoes[a] = {}; mk.freq[a] = 0
    mk.transicoes[a][b] = mk.transicoes[a].get(b, 0) + 1
    mk.freq[a] += 1
    mk.total += 1
print(f"  mk_palavra: {mk.total} transicoes em {time.perf_counter()-t_pal:.1f}s")

# Cria topicos com amostras (sem parser, so texto)
print(f"  Criando {len(lote_amostras)} topicos de amostra...")
t_top = time.perf_counter()
for i, texto in enumerate(lote_amostras):
    palavras = texto.split()
    c.topicos[f"projeto_{i}"] = {
        'texto': texto, 'bytes': len(texto.encode()),
        'n_palavras': len(palavras),
        'conteudo': list({p.lower() for p in palavras if len(p) >= 2}),
        'tipo': 'projeto',
    }

# Recalcula coupling uma vez
print(f"  Recalculando coupling...")
c.coupling.recalcular()

t1 = time.perf_counter()
print(f"\n{'='*55}")
print(f"  RESUMO")
print(f"{'='*55}")
print(f"  Arquivos texto: {n_arqs}")
print(f"  Bytes processados: {n_bytes/1024:.0f} KB")
print(f"  Tempo total: {t1-t0:.1f}s")
print(f"  Velocidade media: {n_bytes/1024/max(t1-t0,0.01):.0f} KB/s")
print(f"  Topicos: {len(c.topicos)}")
print(f"  Transicoes byte: {c.mk_byte.total}")
print(f"  Transicoes palavra: {c.mk_palavra.total}")
print(f"  Entropia byte: {c.mk_byte.entropia_media():.3f}")
print(f"  Entropia palavra: {c.mk_palavra.entropia_media():.3f}")

c.salvar()
print(f"\n  Cerebro salvo em: cache/cerebro.json")
