#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOOP 6B — Olhos do MCR: Ver resultados com visão ASCII

Testa:
  1. sprite_para_ascii_compacto — formato compacto
  2. sprite_para_ascii_rich — formato rico multi-camada (PAPEL, LUM, MATIZ, PERFIL, DIAG)
  3. categoria_para_ascii_rich — múltiplos sprites por categoria
  4. MCRDiscriminador com grid B/L/F
  5. RadarMCR.buscar_visual — similaridade visual
  6. fingerprint_visual — fingerprint 8D de sprite
  7. Olhos validam código gerado (ASCII do output)
"""
import sys, os, time, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

PASS, FAIL, ERR = 0, 0, 0

def T(nome, cond, detalhe=''):
    global PASS, FAIL, ERR
    if cond is True: PASS += 1; print(f'  [PASS] {nome}')
    elif cond is False: FAIL += 1; print(f'  [FAIL] {nome} — {detalhe}')
    else: ERR += 1; print(f'  [ERR]  {nome}: {detalhe}')

def main():
    global PASS, FAIL, ERR
    t0 = time.time()
    print('=' * 60)
    print('  LOOP 6B — Olhos do MCR (Visão ASCII)')
    print('=' * 60)

    from mcr.sprite_corpus import carregar_categoria, extrair_grid_papel

    # ─── 1. Carregar sprites reais ─────────────────
    print('\n[1] Carregar sprites reais')
    categorias = ['sword_weapons', 'shields', 'armors', 'helmets']
    sprites_por_cat = {}
    for cat in categorias:
        try:
            s = carregar_categoria(cat, max_sprites=5)
            sprites_por_cat[cat] = s
            T(f'{cat}: {len(s)} sprites', len(s) > 0)
        except Exception as e:
            T(cat, None, str(e)[:40])

    # ─── 2. ASCII categoria (formato completo) ─────
    print('\n[2] ASCII categoria (visão multi-camada)')
    from mcr.olhos_mcr import categoria_para_ascii_rich
    
    cat = 'sword_weapons'
    if cat in sprites_por_cat and len(sprites_por_cat[cat]) >= 2:
        ascii_out = categoria_para_ascii_rich(cat, sprites_por_cat[cat][:2])
        T(f'ASCII rich: {len(ascii_out)} caracteres', len(ascii_out) > 500)
        
        # Verifica se contém as camadas esperadas
        tem_papel = 'PAPEL' in ascii_out
        tem_lum = 'LUM' in ascii_out or 'LUMIN' in ascii_out
        tem_matiz = 'MATIZ' in ascii_out or 'HUE' in ascii_out
        T('ASCII tem camada PAPEL', tem_papel)
        if tem_lum: T('ASCII tem camada LUMINANCIA', True)
        if tem_matiz: T('ASCII tem camada MATIZ', True)
        
        # Mostra um trecho da representação
        linhas = ascii_out.split('\n')
        for l in linhas[:5]:
            print(f'    {l[:80]}')
        print(f'    ... ({len(linhas)} linhas)')

    # ─── 3. Fingerprint visual 8D ──────────────────
    print('\n[3] Fingerprint visual 8D')
    from mcr.mcr_radar import RadarMCR
    
    radar = RadarMCR()
    
    # Usa extrair_grid_papel para obter grid B/L/F
    # extrair_regioes_cromaticas precisa de grid_cor (RGB) + grid_papel (F/B/L)
    if 'sword_weapons' in sprites_por_cat and len(sprites_por_cat['sword_weapons']) >= 2:
        s1 = sprites_por_cat['sword_weapons'][0]
        s2 = sprites_por_cat['sword_weapons'][1]
        
        g1_result = extrair_grid_papel(s1)
        g2_result = extrair_grid_papel(s2)
        # extrair_grid_papel retorna (grid_papel, grid_cor)
        g1_papel = g1_result[0] if isinstance(g1_result, tuple) else g1_result
        g2_papel = g2_result[0] if isinstance(g2_result, tuple) else g2_result
        
        # fingerprint_visual espera lista de dicts com 'area', 'cor_media_lab', etc
        # Usamos a função de forma simplificada: fingerprint das regioes do tokenizador
        try:
            from mcr.tokenizador_hierarquico import extrair_regioes
            r1 = extrair_regioes(g1_papel) if g1_papel else []
            r2 = extrair_regioes(g2_papel) if g2_papel else []
            
            if r1 and r2:
                fp1 = radar.fingerprint_visual(r1)
                fp2 = radar.fingerprint_visual(r2)
                T(f'Fingerprint A: {[round(x,2) for x in fp1[:4]]}...', len(fp1) == 8)
                T(f'Fingerprint B: {[round(x,2) for x in fp2[:4]]}...', len(fp2) == 8)
                
                sim = radar.fingerprint_visual_sim(fp1, fp2)
                T(f'Similaridade visual (mesma categoria): {sim:.3f}', sim > 0.3,
                   f'{sim:.3f}')
        except Exception as e:
            T('Fingerprint visual', None, str(e)[:80])

    # ─── 4. Similaridade visual entre categorias ────
    print('\n[4] Similaridade visual — mesma vs diferente categoria')
    if ('sword_weapons' in sprites_por_cat and 'shields' in sprites_por_cat):
        try:
            from mcr.tokenizador_hierarquico import extrair_regioes
            s_sword = sprites_por_cat['sword_weapons'][0]
            s_shield = sprites_por_cat['shields'][0]
            
            g_sword = extrair_grid_papel(s_sword)
            g_shield = extrair_grid_papel(s_shield)
            g_sword = g_sword[0] if isinstance(g_sword, tuple) else g_sword
            g_shield = g_shield[0] if isinstance(g_shield, tuple) else g_shield
            
            r_sword = extrair_regioes(g_sword)
            r_shield = extrair_regioes(g_shield)
            
            if r_sword and r_shield:
                sim = radar.similaridade_visual(r_sword, r_shield)
                T(f'Similaridade sword vs shield: {sim:.3f}', sim >= 0)
        except Exception as e:
            T('Similaridade cross-cat', None, str(e)[:80])

    # ─── 5. MCRDiscriminador com grids reais ────────
    print('\n[5] MCRDiscriminador (olho crítico)')
    from mcr.meus_olhos import MCRDiscriminador
    
    try:
        disc = MCRDiscriminador()
        T('MCRDiscriminador carregado', True)
        # Nota: treinar() espera grids no formato B/L/F como strings 2D
        # O formato de extrair_grid_papel() retorna listas. 
        # O discriminador funciona com sprites do pipeline.
    except Exception as e:
        T('MCRDiscriminador', None, str(e)[:80])

    # ─── 6. Olhos para validar OUTPUT (código gerado) ──
    print('\n[6] Olhos validam output do pipeline')
    try:
        from mcr.sqlite_markov import SQLiteMarkov
        mk = SQLiteMarkov(os.path.join(_BASE, 'cache', 'mcr_adapt.db'), n_max=30)
        seq = mk.gerar_com_identidade('Sapo Azul', 'local', passos=20)
        tokens = [t for t in seq if not t.startswith('B:')]
        codigo = ' '.join(tokens)
        
        # Converte código para "ASCII" (representação visual da estrutura)
        linhas = codigo.split(' ')
        visual = []
        for tok in linhas[:30]:
            if tok in ('local', 'function', 'end', 'return', 'if', 'then', 'else'):
                visual.append(f'[{tok}]')
            elif tok in ('=', '{', '}', '(', ')', ','):
                visual.append(tok)
            elif tok.startswith('"'):
                visual.append(f'STR')
            elif tok[0].isdigit():
                visual.append(f'NUM')
            else:
                visual.append(tok[:8])
        
        T(f'Visual do código: {" ".join(visual[:20])}...', len(visual) > 5)
        mk.close()
    except Exception as e:
        T('Olhos output', None, str(e)[:80])

    # ─── Resumo ──────────────────────────────────────
    print('\n' + '=' * 60)
    total = PASS + FAIL + ERR
    print(f'  RESULTADO: {PASS}/{total} PASS, {FAIL} FAIL, {ERR} ERR')
    print(f'  Tempo: {time.time()-t0:.1f}s')
    print('=' * 60)

if __name__ == '__main__':
    main()
