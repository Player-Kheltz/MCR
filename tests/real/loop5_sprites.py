#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOOP 5 — Testes com dados REAIS: sprites, grids, pipeline completo

Valida:
  1. MCRSpawner com 2+ workers paralelos
  2. MCRSpriteMotor com sprites PNG reais do corpus
  3. MCRDiscriminador com grids B/L/F
  4. Pipeline criativo: Emergir → MCRConector → SQLiteMarkov → validação
  5. Qualidade real do output (estrutural, sintático)
"""
import sys, os, time, json, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'devia', 'kernel'))

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
    print('  LOOP 5 — Sprites Reais + Pipeline Completo')
    print('=' * 60)

    # ─── 1. MCRSpawner com múltiplos workers ─────────
    print('\n[1] MCRSpawner — múltiplos workers paralelos')
    from mcr_kernel.evolution import MCRSpawner, MCRTarefa
    spawner = MCRSpawner()
    
    # Adiciona seeds para 4 tarefas
    spawner.mk_nworkers.aprender("n:0", "2")
    spawner.mk_nworkers.aprender("n:4", "2")
    
    def tarefa_rapida(val):
        return {'id': val, 'soma': val * 2}
    
    def make_fn(val):
        return lambda: tarefa_rapida(val)
    
    tarefas = [MCRTarefa(f't{val}', make_fn(val)) for val in range(4)]
    t1 = time.time()
    workers = spawner.spawnar(tarefas)
    tempo = time.time() - t1
    
    sucessos = sum(1 for w in workers if w.erro is None)
    n_workers = len(workers)
    T(f'Spawner: {n_workers} workers para 4 tarefas', n_workers >= 2,
       f'{n_workers} workers, {sucessos} OK, {tempo:.3f}s')

    # ─── 2. MCRSpriteMotor com sprites REAIS ──────────
    print('\n[2] MCRSpriteMotor com sprites PNG reais')
    try:
        from mcr.mcr_sprite_motor import MCRSpriteMotor
        from mcr.sprite_corpus import carregar_categoria, extrair_grid_papel
        
        motor = MCRSpriteMotor()
        T('MCRSpriteMotor instanciado', True)
        
        # Carregar sprites de uma categoria pequena
        try:
            sprites = carregar_categoria('boots', max_sprites=10)
            T(f'carregar_categoria("boots"): {len(sprites)} sprites', len(sprites) > 0)
        except Exception:
            sprites = carregar_categoria('food', max_sprites=10)
            T(f'carregar_categoria("food"): {len(sprites)} sprites', len(sprites) > 0)
        
        if sprites and len(sprites) > 0:
            # Extrair grid B/L/F do primeiro sprite
            sprite = sprites[0]
            if isinstance(sprite, dict) and 'rgba' in sprite:
                grid = extrair_grid_papel(sprite['rgba'])
                T(f'Grid B/L/F: {len(grid)}x{len(grid[0]) if grid else 0}',
                   len(grid) == 32 and len(grid[0]) == 32)
                
                # Treinar motor com os sprites
                try:
                    motor.treinar(sprites, 'test_boots')
                    stats = motor.stats()
                    T(f'MCRSpriteMotor treinado: {stats}', stats is not None)
                except Exception as e:
                    T(f'MCRSpriteMotor.treinar()', None, str(e)[:80])
    except Exception as e:
        T('MCRSpriteMotor', None, str(e)[:100])

    # ─── 3. MCRDiscriminador com grids B/L/F ──────────
    print('\n[3] MCRDiscriminador com grids reais')
    try:
        from mcr.meus_olhos import MCRDiscriminador
        disc = MCRDiscriminador()
        
        if sprites and len(sprites) >= 3:
            # Extrair grids B/L/F de 3 sprites
            grids = []
            for s in sprites[:3]:
                if isinstance(s, dict) and 'rgba' in s:
                    g = extrair_grid_papel(s['rgba'])
                    grids.append(g)
            
            if len(grids) >= 3:
                disc.treinar(grids)
                score = disc.avaliar(grids[0])
                T(f'MCRDiscriminador avaliou: score={score:.3f}',
                   isinstance(score, (int, float)) and score >= 0)
    except Exception as e:
        T('MCRDiscriminador', None, str(e)[:80])

    # ─── 4. Pipeline criativo completo ────────────────
    print('\n[4] Pipeline Criativo: Ideia → Código → Validação')
    try:
        from mcr.sqlite_markov import SQLiteMarkov
        from mcr_kernel.memory import MCRConector
        
        mk = SQLiteMarkov(os.path.join(_BASE, 'cache', 'mcr_adapt.db'), n_max=30)
        
        # Etapa 1: Conectar conceitos
        conector = MCRConector()
        conector.alimentar(
            "O dragao cospe fogo e suas escamas sao impenetraveis",
            "dragao"
        )
        conector.alimentar(
            "O ferreiro forja armaduras de aco na bigorna ardente",
            "ferreiro"
        )
        conexao = conector.conectar("dragao", "ferreiro")
        
        # Etapa 2: Gerar código baseado na conexão
        identidades_npc = ['Adrenius', 'Ahmet']
        resultados_geracao = []
        
        for ident in identidades_npc:
            seq = mk.gerar_com_identidade(ident, 'local', passos=20)
            tokens = [t for t in seq if not t.startswith('B:') and len(t) < 200]
            texto = ' '.join(tokens)
            
            # Validar estrutura (Ahmet usa estrutura de quest, diferente de Adrenius)
            if ident == 'Ahmet':
                estrutura = ['Storage.Quest', 'Player', 'npcHandler']
            else:
                estrutura = ['internalNpcName', 'Game.createNpcType', 'npcConfig']
            encontrados = [e for e in estrutura if e in texto]
            
            resultados_geracao.append({
                'identidade': ident,
                'tokens': len(tokens),
                'estrutura': f'{len(encontrados)}/{len(estrutura)}',
                'preview': texto[:80],
                'encontrados': len(encontrados),
                'total_estrutura': len(estrutura),
            })
        
        for r in resultados_geracao:
            T(f'{r["identidade"]}: {r["tokens"]} tokens, {r["estrutura"]} estrutura',
               r['encontrados'] >= 2)
        
        # Etapa 3: Validar sintaxe Lua (usa Adrenius)
        codigo_lua = resultados_geracao[0]['preview']
        tem_npcType = 'Game.createNpcType' in codigo_lua
        T(f'Sintaxe Lua: Game.createNpcType={"OK" if tem_npcType else "FAIL"}',
           tem_npcType)
        
        mk.close()
    except Exception as e:
        T('Pipeline criativo', None, str(e)[:100])

    # ─── 5. Qualidade real do output ──────────────────
    print('\n[5] Qualidade REAL do output (métricas objetivas)')
    try:
        mk = SQLiteMarkov(os.path.join(_BASE, 'cache', 'mcr_adapt.db'), n_max=30)
        
        # Gerar para múltiplas identidades e medir
        identidades = ['Adrenius', 'Ahmet', 'Sapo Azul']
        metricas = []
        
        for ident in identidades:
            t_ini = time.time()
            seq = mk.gerar_com_identidade(ident, 'local', passos=30)
            t_fim = time.time()
            
            tokens = [t for t in seq if not t.startswith('B:') and len(t) < 200]
            texto = ' '.join(tokens)
            
            # Métricas objetivas
            palavras = texto.split()
            unicidade = len(set(palavras)) / max(len(palavras), 1)
            
            # Estrutura esperada por tipo
            if ident == 'Ahmet':  # Quest NPC
                estrutura = ['Storage.Quest', 'Player', 'npcHandler', 'creatureSayCallback']
            elif ident in ['Adrenius']:  # NPC generico
                estrutura = ['internalNpcName', 'Game.createNpcType', 'npcConfig',
                           'npcHandler', 'npcType:register']
            else:  # Monster
                estrutura = ['Game.createMonsterType', 'monster.description',
                           'monster.experience', 'monster.health',
                           'monster.outfit', 'mType:register']
            
            encontrados = [e for e in estrutura if e in texto]
            taxa_estrutural = len(encontrados) / len(estrutura)
            
            metricas.append({
                'identidade': ident,
                'tokens': len(tokens),
                'tempo_ms': round((t_fim - t_ini) * 1000, 2),
                'unicidade': round(unicidade, 2),
                'estrutura': f'{len(encontrados)}/{len(estrutura)}',
                'taxa_estrutural': round(taxa_estrutural * 100),
            })
        
        for m in metricas:
            T(f'{m["identidade"]}: {m["tokens"]} tokens, {m["estrutura"]} estrutura, '
              f'{m["tempo_ms"]}ms, unicidade={m["unicidade"]}',
              m['taxa_estrutural'] >= 40,
              f'taxa={m["taxa_estrutural"]}%')
        
        mk.close()
    except Exception as e:
        T('Qualidade output', None, str(e)[:100])

    # ─── Resumo ──────────────────────────────────────
    print('\n' + '=' * 60)
    total = PASS + FAIL + ERR
    print(f'  RESULTADO: {PASS}/{total} PASS, {FAIL} FAIL, {ERR} ERR')
    print(f'  Tempo: {time.time()-t0:.1f}s')
    print('=' * 60)

if __name__ == '__main__':
    main()
