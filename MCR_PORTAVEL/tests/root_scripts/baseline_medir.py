#!/usr/bin/env python3
"""
baseline_medir.py — Mede baseline do pipeline_nitido nas 5 categorias de teste.

Gera 20 sprites por categoria usando o approach pipeline_nitido:
  1. Carrega todos os sprites da categoria
  2. Para cada sprite, tokeniza em grid_papel (B/L/F) + grid_cor
  3. Usa o sprite com mediana de opacos como "template" (grid_papel fixo)
  4. Extrai paleta_mediana de TODOS os sprites
  5. Gera 20 variacoes com CIELAB hue rotation (angulos diferentes)
  6. Mede: opacos, B%, L%, transicoes

Salva baseline em poc_output/baseline_pipeline_nitido.json
"""
import os, sys, math, random, json
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcr.sprite_corpus import carregar_categoria, extrair_grid_papel, extrair_paleta_mediana
from mcr.cielab import rgb_para_lab, lab_para_rgb
from mcr.meus_olhos import MCRDiscriminador
from mcr.tokenizador_hierarquico import extrair_regioes, extrair_relacoes, resumir_hierarquico
from mcr.regioes_anatomicas import extrair_regioes_cromaticas, resumir_regioes
from mcr.paths import POC_OUTPUT_DIR

OUT_DIR = str(POC_OUTPUT_DIR / 'baseline_nitido')
os.makedirs(OUT_DIR, exist_ok=True)

TEST_CATEGORIES = ['sword_weapons', 'shields', 'armors', 'creature_products', 'helmets']
N_GERADOS = 20


def medir_grid(grid_papel):
    """Mede propriedades estruturais de um grid B/L/F."""
    h = len(grid_papel)
    w = len(grid_papel[0])
    total = h * w
    contagem = Counter(t for row in grid_papel for t in row)
    opacos = contagem.get('B', 0) + contagem.get('L', 0) + contagem.get('D', 0)
    
    # Transicoes (ctx_esq, ctx_cima, papel)
    transicoes = Counter()
    for y in range(h):
        for x in range(w):
            tok = grid_papel[y][x]
            if tok == 'F':
                continue
            ctx_esq = grid_papel[y][x-1] if x > 0 else 'F'
            ctx_cima = grid_papel[y-1][x] if y > 0 else 'F'
            transicoes[(ctx_esq, ctx_cima, tok)] += 1
    
    return {
        'opacos': opacos,
        'prop_B': contagem.get('B', 0) / max(opacos, 1),
        'prop_L': contagem.get('L', 0) / max(opacos, 1),
        'n_transicoes': len(transicoes),
        'total_transicoes': sum(transicoes.values()),
    }


def gerar_nitido(grid_papel, paleta_media, angulo_hue, variacao=5):
    """Gera sprite nitido: mesma estrutura, cor via CIELAB rotation."""
    h = len(grid_papel)
    w = len(grid_papel[0])
    grid_saida = [['F'] * w for _ in range(h)]
    
    for y in range(h):
        for x in range(w):
            papel = grid_papel[y][x]
            if papel == 'F':
                continue
            
            r, g, b = paleta_media.get(papel, (128, 128, 128))
            L, a, bl = rgb_para_lab(r, g, b)
            raio = math.sqrt(a*a + bl*bl)
            if raio < 3:
                raio = 6
            novo_a = raio * math.cos(angulo_hue)
            novo_b = raio * math.sin(angulo_hue)
            novo_L = L + random.randint(-variacao, variacao)
            cr, cg, cb = lab_para_rgb(novo_L, novo_a, novo_b)
            grid_saida[y][x] = (cr, cg, cb)
    
    return grid_saida


def medir_categoria(nome):
    """Mede baseline de uma categoria completa."""
    print(f'\n=== {nome} ===')
    
    # 1. Carregar sprites
    sprites = carregar_categoria(nome)
    print(f'  Sprites carregados: {len(sprites)}')
    
    # 2. Tokenizar todos
    dados = []
    for arr in sprites:
        gp, gc = extrair_grid_papel(arr)
        m = medir_grid(gp)
        dados.append({'grid_papel': gp, 'grid_cor': gc, 'metricas': m})
    
    # 3. Metricas agregadas da categoria
    opacos_vals = [d['metricas']['opacos'] for d in dados]
    prop_b_vals = [d['metricas']['prop_B'] for d in dados]
    prop_l_vals = [d['metricas']['prop_L'] for d in dados]
    
    media_opacos = sum(opacos_vals) / len(opacos_vals)
    dp_opacos = (sum((x - media_opacos)**2 for x in opacos_vals) / len(opacos_vals)) ** 0.5
    
    # 4. Sprite template = mediana de opacos
    idx_mediana = sorted(range(len(opacos_vals)), key=lambda i: opacos_vals[i])[len(opacos_vals)//2]
    grid_template = dados[idx_mediana]['grid_papel']
    
    # 5. Paleta mediana de TODOS
    todas_cor = []
    todas_papel = []
    for d in dados:
        for y in range(len(d['grid_cor'])):
            for x in range(len(d['grid_cor'][0])):
                if d['grid_papel'][y][x] != 'F':
                    todas_cor.append(d['grid_cor'][y][x])
                    todas_papel.append(d['grid_papel'][y][x])
    
    # Calcular mediana por papel
    por_papel = defaultdict(list)
    for i in range(len(todas_cor)):
        por_papel[todas_papel[i]].append(todas_cor[i])
    
    paleta_mediana = {}
    for papel, cores in por_papel.items():
        rs = sorted(c[0] for c in cores)
        gs = sorted(c[1] for c in cores)
        bs = sorted(c[2] for c in cores)
        n = len(rs)
        paleta_mediana[papel] = (rs[n//2], gs[n//2], bs[n//2])
    
    # 6. Extrair regioes do template (N1)
    regioes_template = extrair_regioes(grid_template)
    relacoes_template = extrair_relacoes(regioes_template)
    
    # 7. Treinar discriminador com TODOS os grids
    disc = MCRDiscriminador()
    disc.treinar([d['grid_papel'] for d in dados])
    
    # 8. Gerar 20 variacoes
    random.seed(42)
    gerados = []
    for g in range(N_GERADOS):
        angulo = random.random() * 2 * math.pi
        var_cor = random.randint(2, 8)
        grid_gerado = gerar_nitido(grid_template, paleta_mediana, angulo, var_cor)
        
        # Converter grid RGB de volta para B/L/F para medir
        grid_blf = [['F'] * 32 for _ in range(32)]
        for y in range(32):
            for x in range(32):
                if grid_gerado[y][x] != 'F':
                    grid_blf[y][x] = 'L'
        
        m_gerado = medir_grid(grid_blf)
        resultado_disc = disc.avaliar(grid_blf)
        
        gerados.append({
            'idx': g,
            'angulo': round(angulo, 4),
            'variacao': var_cor,
            'metricas': m_gerado,
            'disc_score': resultado_disc['score'],
        })
    
    # 9. Salvar imagens de exemplo
    from PIL import Image
    cat_dir = os.path.join(OUT_DIR, nome)
    os.makedirs(cat_dir, exist_ok=True)
    
    # Salvar template
    img_template = Image.new('RGBA', (32, 32))
    pixels = []
    for y in range(32):
        for x in range(32):
            p = grid_template[y][x]
            if p == 'F':
                pixels.append((0, 0, 0, 0))
            else:
                r, g, b = paleta_mediana.get(p, (128, 128, 128))
                pixels.append((r, g, b, 255))
    img_template.putdata(pixels)
    img_template.save(os.path.join(cat_dir, 'template.png'))
    
    # Salvar 5 gerados
    for g in gerados[:5]:
        grid_gerado = gerar_nitido(grid_template, paleta_mediana, g['angulo'], g['variacao'])
        img = Image.new('RGBA', (32, 32))
        pixels = []
        for y in range(32):
            for x in range(32):
                c = grid_gerado[y][x]
                if c == 'F':
                    pixels.append((0, 0, 0, 0))
                else:
                    pixels.append((*c, 255))
        img.putdata(pixels)
        img.save(os.path.join(cat_dir, f'gerado_{g["idx"]:03d}.png'))
    
    # 10. Resumo
    media_disc = sum(g['disc_score'] for g in gerados) / len(gerados)
    media_gerados_opacos = sum(g['metricas']['opacos'] for g in gerados) / len(gerados)
    
    resultado = {
        'categoria': nome,
        'n_sprites': len(sprites),
        'template_idx': idx_mediana,
        'media_opacos_real': round(media_opacos, 1),
        'dp_opacos_real': round(dp_opacos, 1),
        'media_prop_B_real': round(sum(prop_b_vals)/len(prop_b_vals), 3),
        'media_prop_L_real': round(sum(prop_l_vals)/len(prop_l_vals), 3),
        'n_regioes_template': len(regioes_template),
        'n_relacoes_template': len(relacoes_template),
        'paleta_mediana': {k: list(v) for k, v in paleta_mediana.items()},
        'disc_score_medio': round(media_disc, 4),
        'media_opacos_gerados': round(media_gerados_opacos, 1),
        'gerados': gerados,
    }
    
    print(f'  Template: idx={idx_mediana}, opacos={sum(1 for row in grid_template for t in row if t != "F")}')
    print(f'  Regioes N1: {len(regioes_template)}, Relacoes N2: {len(relacoes_template)}')
    print(f'  Paleta: {paleta_mediana}')
    print(f'  Disc score medio: {media_disc:.4f}')
    print(f'  Opacos gerados: {media_gerados_opacos:.1f} (real: {media_opacos:.1f})')
    
    return resultado


if __name__ == '__main__':
    print('=' * 60)
    print('BASELINE PIPELINE NITIDO — 5 Categorias de Teste')
    print('=' * 60)
    
    resultados = {}
    for cat in TEST_CATEGORIES:
        try:
            resultados[cat] = medir_categoria(cat)
        except Exception as e:
            print(f'  ERRO em {cat}: {e}')
            import traceback; traceback.print_exc()
    
    # Salvar
    out_path = os.path.join(OUT_DIR, 'baseline_pipeline_nitido.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False, default=str)
    
    print(f'\n{"=" * 60}')
    print(f'Baseline salva em: {out_path}')
    print(f'{"=" * 60}')
    
    # Resumo
    print('\n=== RESUMO ===')
    for cat, r in resultados.items():
        print(f'  {cat}: real={r["media_opacos_real"]:.0f}op, '
              f'gerados={r["media_opacos_gerados"]:.0f}op, '
              f'disc={r["disc_score_medio"]:.3f}, '
              f'regN1={r["n_regioes_template"]}, relN2={r["n_relacoes_template"]}')
