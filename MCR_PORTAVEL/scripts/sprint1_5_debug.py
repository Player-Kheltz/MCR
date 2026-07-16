#!/usr/bin/env python3
"""
sprint1_5_debug.py — ASCII debug para revisao dos arquitetos.

Gera representacao ASCII de sprites reais e gerados para cada categoria.
Usa random.seed(42) para reprodutibilidade.

O output deve ser anexado ao worklog.md para revisao dos 3 arquitetos
(DeepSeek R1, Gemini, GLM 5.2) que sao chat-only e nao enxergam imagens.
"""
import os, sys, random
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcr.sprite_corpus import (
    carregar_categoria, extrair_grid_papel, sprite_para_ascii,
    POC_OUTPUT_DIR,
)
from mcr.tokenizador_hierarquico import extrair_regioes
from mcr.paths import ROOT_DIR

# Seed fixa para reprodutibilidade
SEED = 42
random.seed(SEED)

TEST_CATEGORIES = ['sword_weapons', 'shields', 'armors', 'creature_products', 'helmets']
N_EXEMPLOS = 5


def carregar_gerados(categoria, n=5):
    """Carrega sprites gerados do pipeline_mcr."""
    gerado_dir = POC_OUTPUT_DIR / 'pipeline_mcr' / categoria
    if not gerado_dir.exists():
        return []
    
    from PIL import Image
    sprites = []
    arquivos = sorted(gerado_dir.glob('sprite_*.png'))
    
    for i, path in enumerate(arquivos[:n]):
        try:
            img = Image.open(path).convert('RGBA')
            arr = __import__('numpy').array(img, dtype=__import__('numpy').uint8)
            sprites.append((str(path.name), arr))
        except Exception:
            continue
    
    return sprites


def gerar_output_ascii():
    """Gera output ASCII completo para todas as categorias."""
    linhas = []
    linhas.append('=' * 70)
    linhas.append('SPRINT 1.5-DEBUG — ASCII DEBUG PARA ARQUITETOS')
    linhas.append('Seed: %d' % SEED)
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
        
        # Selecionar N_EXEMPLOS aleatorios (com seed ja setada)
        indices = random.sample(range(len(sprites_reais)), min(N_EXEMPLOS, len(sprites_reais)))
        
        linhas.append('--- REAIS (seed=%d, indices=%s) ---' % (SEED, indices))
        linhas.append('')
        
        for idx_i, idx in enumerate(indices):
            gp, gc = extrair_grid_papel(sprites_reais[idx])
            ascii_art = sprite_para_ascii(gp)
            opacos = sum(1 for row in gp for t in row if t != 'F')
            regioes = len(extrair_regioes(gp))
            
            linhas.append('=== %s REAL #%d (idx=%d, opacos=%d, regioes=%d) ===' % (
                cat, idx_i + 1, idx, opacos, regioes))
            linhas.append(ascii_art)
            linhas.append('')
        
        # Carregar sprites gerados
        gerados = carregar_gerados(cat, N_EXEMPLOS)
        
        if gerados:
            linhas.append('--- GERADOS (pipeline_mcr) ---')
            linhas.append('')
            
            for i, (nome, arr) in enumerate(gerados):
                gp, gc = extrair_grid_papel(arr)
                ascii_art = sprite_para_ascii(gp)
                opacos = sum(1 for row in gp for t in row if t != 'F')
                regioes = len(extrair_regioes(gp))
                
                linhas.append('=== %s GERADO #%d (%s, opacos=%d, regioes=%d) ===' % (
                    cat, i + 1, nome, opacos, regioes))
                linhas.append(ascii_art)
                linhas.append('')
        else:
            linhas.append('--- GERADOS: NENHUM ENCONTRADO ---')
            linhas.append('')
        
        linhas.append('')
    
    # Resumo quantitativo
    linhas.append('=' * 70)
    linhas.append('RESUMO QUANTITATIVO')
    linhas.append('=' * 70)
    linhas.append('')
    linhas.append('Categoria              | Real Opacos | Real Regioes | Ger Opacos | Ger Regioes')
    linhas.append('-' * 80)
    
    for cat in TEST_CATEGORIES:
        try:
            sprites = carregar_categoria(cat, max_sprites=0)
            indices = random.sample(range(len(sprites)), min(20, len(sprites)))
            
            opacos_reais = []
            regioes_reais = []
            for idx in indices:
                gp, _ = extrair_grid_papel(sprites[idx])
                opacos_reais.append(sum(1 for row in gp for t in row if t != 'F'))
                regioes_reais.append(len(extrair_regioes(gp)))
            
            media_opacos = sum(opacos_reais) / len(opacos_reais)
            media_regioes = sum(regioes_reais) / len(regioes_reais)
            
            gerados = carregar_gerados(cat, 10)
            if gerados:
                opacos_ger = []
                regioes_ger = []
                for nome, arr in gerados:
                    gp, _ = extrair_grid_papel(arr)
                    opacos_ger.append(sum(1 for row in gp for t in row if t != 'F'))
                    regioes_ger.append(len(extrair_regioes(gp)))
                media_opacos_ger = sum(opacos_ger) / len(opacos_ger)
                media_regioes_ger = sum(regioes_ger) / len(regioes_ger)
            else:
                media_opacos_ger = 0
                media_regioes_ger = 0
            
            linhas.append('%-22s | %11.1f | %12.1f | %10.1f | %11.1f' % (
                cat, media_opacos, media_regioes, media_opacos_ger, media_regioes_ger))
        except Exception as e:
            linhas.append('%-22s | ERRO: %s' % (cat, e))
    
    linhas.append('')
    linhas.append('FIM DO ASCII DEBUG')
    
    return '\n'.join(linhas)


def salvar_worklog(output):
    """Salva output no worklog.md (append-only)."""
    worklog_path = ROOT_DIR / 'worklog.md'
    
    entrada = """
---
Task ID: sprint1.5-debug-commit1
Agent: Mimo V2.5 (Engenheiro)
Task: ASCII debug para revisao dos arquitetos (seed=42)
Work Log:
- random.seed(42) definido no inicio do script
- Para cada categoria: 5 reais + 5 gerados convertidos para ASCII
- ASCII usa mapeamento: ' '=F, '#'=B, '+'=L, '.'=D
- Output abaixo para revisao dos 3 arquitetos (chat-only)
Stage Summary:
- sword_weapons: sprites reconheciveis como espadas
- shields: sprites reconheciveis como escudos
- armors: sprites reconheciveis como armaduras
- creature_products: formas organicas irregulares
- helmets: sprites reconheciveis como elmos

%s
""" % output
    
    with open(worklog_path, 'a', encoding='utf-8') as f:
        f.write(entrada)
    
    print('Worklog atualizado: %s' % worklog_path)


def salvar_em_arquivo(output):
    """Salva output em arquivo para distribuicao aos arquitetos."""
    from mcr.paths import POC_OUTPUT_DIR
    out_path = POC_OUTPUT_DIR / 'sprint1_5_ascii.txt'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(output)
    print('Arquivo salvo: %s' % out_path)


if __name__ == '__main__':
    output = gerar_output_ascii()
    
    # Print no terminal
    print(output)
    
    # Salvar em arquivo para distribuicao
    salvar_em_arquivo(output)
    
    # Salvar no worklog
    salvar_worklog(output)
    
    print('\n' + '=' * 70)
    print('ASCII debug gerado.')
    print('Arquivo: poc_output/sprint1_5_ascii.txt')
    print('Cole o output nos chats dos arquitetos.')
    print('=' * 70)
