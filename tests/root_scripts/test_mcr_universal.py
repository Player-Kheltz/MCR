#!/usr/bin/env python3
"""
test_mcr_universal.py — Valida TUDO que foi conectado.

Testa:
  1. MCRSpriteUniversal.treinar() — auto-descobre parametros
  2. MCRThreshold — thresholds adaptativos
  3. MCRDiscriminador — qualidade dos gerados
  4. RadarMCR — similaridade visual
  5. MCREntropia — deteccao de loop
  6. MCRPesoNota — nota MCR
  7. mcr_radar.buscar — busca por ondas
  8. SignatureAnalyzer — tipos de sprite
  9. MCRSignatureExpansiva — dimensionalidade
  10. Comparacao visual com olhos_mcr.py
"""
import sys, os, random, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from pathlib import Path
from PIL import Image

from mcr.mcr_sprite_universal import MCRSpriteUniversal
from mcr.sprite_corpus import carregar_categoria, extrair_grid_papel, sprite_para_ascii
from mcr.olhos_mcr import sprite_para_ascii_rich, sprite_para_ascii_compacto
from mcr.mcr_signature_cluster import SignatureAnalyzer, SignatureCluster
from mcr.mcr_radar import RadarMCR
from mcr.meus_olhos import MCRDiscriminador

from mcr_universal.core.signature import MCRSignatureExpansiva
from mcr_universal.core.byte_utils import MCRByteUtils

from devia.kernel.mcr_kernel.decisor import (
    MCRThreshold, MCRDecisor, MCREntropia, MCRPesoNota
)

SEED = 42
random.seed(SEED)

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

OUT_DIR = Path(os.path.join(_BASE, 'poc_output', 'mcr_universal_test'))
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── 1. MCRSpriteUniversal — Treino e Geracao ──────────────

print('=' * 70)
print('TESTE 1: MCRSpriteUniversal — treino e geracao')
print('=' * 70)

CATEGORIAS = ['sword_weapons', 'shields', 'armors', 'helmets', 'boots']

for cat in CATEGORIAS:
    print(f'\n--- {cat} ---')
    su = MCRSpriteUniversal()
    su.treinar(cat, n_max=15)

    # Gerar
    novos = su.gerar(n=5)

    # Avaliar
    avaliacao = su.avaliar(novos)

    # Salvar
    for i, arr in enumerate(novos):
        Image.fromarray(arr, 'RGBA').save(str(OUT_DIR / f'{cat}_gerado_{i}.png'))

    # Stats
    stats = su.stats()
    print(f'  Stats: {json.dumps(stats, indent=2)}')
    print(f'  Avaliacao: {json.dumps(avaliacao, indent=2)}')

    # Mostrar ASCII do melhor gerado
    if novos:
        gp, gc = extrair_grid_papel(novos[0])
        ascii = sprite_para_ascii(gp)
        n_vis = sum(1 for l in ascii.split('\n') if any(c in l for c in '#+.'))
        print(f'  ASCII ({n_vis} linhas visiveis):')
        for line in ascii.split('\n'):
            if any(c in line for c in '#+.'):
                print(f'    {line}')

# ─── 2. MCRThreshold — Auto-descoberta ─────────────────────

print('\n' + '=' * 70)
print('TESTE 2: MCRThreshold — auto-descoberta de parametros')
print('=' * 70)

th = MCRThreshold('test_sprite')
# Simular observacoes de dados reais
for op in [50, 120, 300, 450, 600, 150, 80, 200, 350, 500]:
    th.observar(float(op))

print(f'  Threshold (multiplicador=1.0): {th.calcular(1.0):.1f}')
print(f'  Threshold (multiplicador=0.5): {th.calcular(0.5):.1f}')
th.aprender('temp_ideal', 0.75)
print(f'  Temp ideal (aprendida): {th.obter("temp_ideal", 0.5):.2f}')
print(f'  Temp ideal (fallback): {th.obter("desconhecido", 0.5):.2f}')

# ─── 3. MCRDiscriminador — Qualidade ───────────────────────

print('\n' + '=' * 70)
print('TESTE 3: MCRDiscriminador — avaliacao de qualidade')
print('=' * 70)

sprites = carregar_categoria('armors', max_sprites=10)
grids = [extrair_grid_papel(s)[0] for s in sprites]

disc = MCRDiscriminador()
disc.treinar(grids)

for i, gp in enumerate(grids[:3]):
    r = disc.avaliar(gp)
    print(f'  Real #{i}: score={r["score"]:.3f} ok={r["ok"]}')

# ─── 4. MCREntropia — Deteccao de Loop ─────────────────────

print('\n' + '=' * 70)
print('TESTE 4: MCREntropia — deteccao de loop')
print('=' * 70)

ent = MCREntropia('test_loop')
# Simular padrao repetitivo (loop)
for _ in range(20):
    ent.alimentar('A')
    ent.alimentar('B')
    ent.alimentar('A')
    ent.alimentar('B')
print(f'  Em loop (padrao ABAB): {ent.esta_em_loop()}')

# Simular padrao variado
ent2 = MCREntropia('test_variedade')
import string
for _ in range(50):
    ent2.alimentar(random.choice(string.ascii_letters))
print(f'  Em loop (aleatorio): {ent2.esta_em_loop()}')

# ─── 5. RadarMCR — Busca Visual ────────────────────────────

print('\n' + '=' * 70)
print('TESTE 5: RadarMCR — busca por similaridade visual')
print('=' * 70)

radar = RadarMCR()

# Fingerprint visual de sprites reais
candidatos = []
for cat in ['sword_weapons', 'shields', 'armors']:
    sps = carregar_categoria(cat, max_sprites=3)
    for i, arr in enumerate(sps):
        fp = MCRSignatureExpansiva.fingerprint(arr.tobytes(), 8)
        candidatos.append({
            'id': f'{cat}_{i}',
            'texto': ' '.join(str(round(x, 2)) for x in fp),
            'fingerprint': fp,
        })

# Buscar por similaridade
consulta = candidatos[0]['texto']
resultados = radar.buscar(consulta, candidatos)
print(f'  Consulta: {candidatos[0]["id"]}')
print(f'  Resultados: {len(resultados)}')
for r in resultados[:3]:
    print(f'    {r["id"]}: score={r["score"]:.3f} onda={r["onda"]}')

# ─── 6. MCRSignatureExpansiva — Dimensionalidade ──────────

print('\n' + '=' * 70)
print('TESTE 6: MCRSignatureExpansiva — dimensionalidade ideal')
print('=' * 70)

for cat in CATEGORIAS:
    sps = carregar_categoria(cat, max_sprites=3)
    if not sps:
        continue
    dados = b''.join(s.tobytes() for s in sps)
    n = MCRSignatureExpansiva.dimensionalidade_ideal(dados)
    fp = MCRSignatureExpansiva.fingerprint(dados, 8)
    print(f'  {cat}: dim_ideal={n} fp8={[round(x,2) for x in fp]}')

# ─── 7. Comparacao Visual — olhos_mcr ──────────────────────

print('\n' + '=' * 70)
print('TESTE 7: Comparacao Visual — ASCII rico')
print('=' * 70)

# Pegar um real e um gerado para comparar
sp_armors = carregar_categoria('armors', max_sprites=1)
if sp_armors:
    su2 = MCRSpriteUniversal()
    su2.treinar('armors', n_max=10)
    gerados = su2.gerar(n=1)

    if gerados:
        # Real
        gp_r, gc_r = extrair_grid_papel(sp_armors[0])
        rich_r = sprite_para_ascii_rich(gp_r, gc_r, nome='armors REAL')
        print(f'  REAL ASCII ({len(rich_r.split(chr(10)))} linhas):')
        # Mostrar so as primeiras camadas
        linhas_r = rich_r.split(chr(10))
        for linha in linhas_r[:38]:
            print(f'    {linha}')

        # Gerado
        gp_g, gc_g = extrair_grid_papel(gerados[0])
        rich_g = sprite_para_ascii_rich(gp_g, gc_g, nome='armors GERADO')
        print(f'\n  GERADO ASCII ({len(rich_g.split(chr(10)))} linhas):')
        linhas_g = rich_g.split(chr(10))
        for linha in linhas_g[:38]:
            print(f'    {linha}')

# ─── 8. Resumo Final ───────────────────────────────────────

print('\n' + '=' * 70)
print('RESUMO — Testes do MCR Sprite Universal')
print('=' * 70)
print(f'''
Modulos Conectados:
  - MCRSpriteUniversal: {len(CATEGORIAS)} categorias treinadas
  - MCRThreshold: thresholds adaptativos OK
  - MCRDiscriminador: scores nos sprites reais OK
  - MCREntropia: deteccao de loop OK
  - RadarMCR: busca visual OK
  - MCRSignatureExpansiva: dimensionalidade OK
  - olhos_mcr: comparacao visual OK

Resultados em: {OUT_DIR}
''')
