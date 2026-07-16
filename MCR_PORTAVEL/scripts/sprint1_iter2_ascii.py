#!/usr/bin/env python3
"""
sprint1_iter2_ascii.py — ASCII debug da iteracao 2 (template refatorado).

Gera sprites com template_regiao.py refatorado e compara com reais.
Salva output em poc_output/refatoracao_iter2_ascii.txt.
"""
import os, sys, random
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcr.sprite_corpus import (
    carregar_categoria, extrair_grid_papel, sprite_para_ascii,
    POC_OUTPUT_DIR,
)
from mcr.template_regiao import treinar_templates, gerar_sprite, resumir_treino
from mcr.tokenizador_hierarquico import extrair_regioes
from mcr.paths import ROOT_DIR

SEED = 42
random.seed(SEED)

TEST_CATEGORIES = ['sword_weapons', 'shields', 'armors', 'helmets', 'food', 'boots']
N_EXEMPLOS = 5
N_TREINO = 20


def gerar_output_ascii():
    """Gera output ASCII completo para todas as categorias."""
    linhas = []
    linhas.append('=' * 70)
    linhas.append('SPRINT 1 REFATORACAO — ASCII DEBUG ITERACAO 2')
    linhas.append('Seed: %d' % SEED)
    linhas.append('Template: temperatura por posicao (H<0.2=0.1, 0.2-0.5=0.6, >=0.5=1.0)')
    linhas.append('Deslocamento: 0.8x delta centroid')
    linhas.append('=' * 70)
    linhas.append('')
    
    for cat in TEST_CATEGORIES:
        linhas.append('#' * 70)
        linhas.append('# CATEGORIA: %s' % cat)
        linhas.append('#' * 70)
        linhas.append('')
        
        # Carregar sprites reais
        try:
            sprites_reais = carregar_categoria(cat, max_sprites=0)
        except Exception as e:
            linhas.append('ERRO ao carregar %s: %s' % (cat, e))
            linhas.append('')
            continue
        
        # Extrair grids
        grids_reais = []
        for s in sprites_reais[:N_TREINO]:
            gp, _ = extrair_grid_papel(s)
            grids_reais.append(gp)
        
        # Treinar template refatorado
        treino = treinar_templates(grids_reais)
        linhas.append('TREINO: %s' % resumir_treino(treino))
        linhas.append('')
        
        # Selecionar N_EXEMPLOS reais aleatorios (com seed ja setada)
        indices = random.sample(range(len(grids_reais)), min(N_EXEMPLOS, len(grids_reais)))
        
        linhas.append('--- REAIS (seed=%d, indices=%s) ---' % (SEED, indices))
        linhas.append('')
        
        for idx_i, idx in enumerate(indices):
            gp = grids_reais[idx]
            ascii_art = sprite_para_ascii(gp)
            opacos = sum(1 for row in gp for t in row if t != 'F')
            regioes = len(extrair_regioes(gp))
            
            linhas.append('=== %s REAL #%d (idx=%d, opacos=%d, regioes=%d) ===' % (
                cat, idx_i + 1, idx, opacos, regioes))
            linhas.append(ascii_art)
            linhas.append('')
        
        # Gerar sprites
        linhas.append('--- GERADOS (template refatorado iteracao 2) ---')
        linhas.append('')
        
        for i in range(N_EXEMPLOS):
            gp, info = gerar_sprite(treino)
            ascii_art = sprite_para_ascii(gp)
            opacos = sum(1 for row in gp for t in row if t != 'F')
            regioes = len(extrair_regioes(gp))
            
            linhas.append('=== %s GERADO #%d (opacos=%d, regioes=%d) ===' % (
                cat, i + 1, opacos, regioes))
            linhas.append(ascii_art)
            linhas.append('')
        
        linhas.append('')
    
    # Resumo quantitativo
    from mcr.sprite_corpus import jaccard_silhueta, jaccard_gerados_vs_reais
    
    linhas.append('=' * 70)
    linhas.append('RESUMO QUANTITATIVO — ITERACAO 2')
    linhas.append('=' * 70)
    linhas.append('')
    linhas.append('Categoria              | J Real  | J Ger   | J vs R  | Opacos R (media±dp) | Opacos G (media±dp)')
    linhas.append('-' * 95)
    
    for cat in TEST_CATEGORIES:
        try:
            sprites = carregar_categoria(cat, max_sprites=0)
            grids_r = [extrair_grid_papel(s)[0] for s in sprites[:N_TREINO]]
            grids_g = []
            for _ in range(20):
                gp, _ = gerar_sprite(treino)
                grids_g.append(gp)
            
            jr = jaccard_silhueta(grids_r)
            jg = jaccard_silhueta(grids_g)
            jvr = jaccard_gerados_vs_reais(grids_g, grids_r)
            
            opacos_r_vals = [sum(1 for row in g for t in row if t != 'F') for g in grids_r]
            opacos_g_vals = [sum(1 for row in g for t in row if t != 'F') for g in grids_g]
            media_r = sum(opacos_r_vals) / len(opacos_r_vals) if opacos_r_vals else 0
            media_g = sum(opacos_g_vals) / len(opacos_g_vals) if opacos_g_vals else 0
            dp_r = (sum((x - media_r)**2 for x in opacos_r_vals) / max(len(opacos_r_vals), 1)) ** 0.5
            dp_g = (sum((x - media_g)**2 for x in opacos_g_vals) / max(len(opacos_g_vals), 1)) ** 0.5
            
            linhas.append('%-22s | %7.3f | %7.3f | %7.3f | %8.0f ± %5.0f | %8.0f ± %5.0f' % (
                cat, jr, jg, jvr, media_r, dp_r, media_g, dp_g))
        except Exception as e:
            linhas.append('%-22s | ERRO: %s' % (cat, e))
    
    linhas.append('')
    linhas.append('FIM DO ASCII DEBUG — ITERACAO 2')
    
    return '\n'.join(linhas)


def salvar_em_arquivo(output):
    """Salva output em arquivo para distribuicao aos arquitetos."""
    out_path = POC_OUTPUT_DIR / 'refatoracao_iter2_ascii.txt'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(output)
    print('Arquivo salvo: %s' % out_path)


def salvar_worklog(output):
    """Salva output no worklog.md (append-only)."""
    worklog_path = ROOT_DIR / 'worklog.md'
    
    entrada = """
---
Task ID: sprint1-refatoracao-commit5
Agent: Mimo V2.5 (Engenheiro)
Task: ASCII debug da iteracao 2 da refatoracao para revisao dos arquitetos
Work Log:
- Rodado sprint1_iter2_ascii.py com template_regiao.py refatorado (iteracao 2)
- 5 reais + 5 gerados por categoria, seed 42, 6 categorias
- Output salvo em poc_output/refatoracao_iter2_ascii.txt
Stage Summary:
- ASCII completo disponivel para revisao visual dos 2 arquitetos
- Aguardando parecer antes de decidir Caminho D (multi-template), C (HDC), ou A revisitado

%s
""" % output
    
    with open(worklog_path, 'a', encoding='utf-8') as f:
        f.write(entrada)
    
    print('Worklog atualizado: %s' % worklog_path)


if __name__ == '__main__':
    output = gerar_output_ascii()
    
    # Print no terminal
    print(output)
    
    # Salvar em arquivo
    salvar_em_arquivo(output)
    
    # Salvar no worklog
    salvar_worklog(output)
    
    print('\n' + '=' * 70)
    print('ASCII debug iteracao 2 gerado.')
    print('Arquivo: poc_output/refatoracao_iter2_ascii.txt')
    print('=' * 70)
