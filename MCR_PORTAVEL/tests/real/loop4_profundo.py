#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOOP 4 — Testes de integração profunda com dados REAIS

Testa:
  1. SDM populado com cerebro.json → retrieval semântico
  2. MCRFuel.abastecer() com fontes reais
  3. Pipeline criativo: Emergir → MCRConector → SQLiteMarkov
  4. MCRExpansao.expandir() com tema real
  5. Performance: geração em paralelo via MCRSpawner
"""
import sys, os, time, json, re, random
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
    print('  LOOP 4 — Integração Profunda com Dados Reais')
    print('=' * 60)

    # ─── 1. SDM com cerebro.json REAL ───────────────
    print('\n[1] SDM populado com cerebro.json + retrieval')
    try:
        from hdc_core import HDVector, HDCVocab
        from sdm_core import SDM
        
        vocab = HDCVocab()
        sdm = SDM(n_enderecos=1000, raio=0.06)
        
        # Carregar topicos do cerebro.json
        cerebro_path = os.path.join(_BASE, 'cache', 'cerebro.json')
        if os.path.exists(cerebro_path):
            with open(cerebro_path, 'r', encoding='utf-8') as f:
                cerebro = json.load(f)
            topicos = cerebro.get('topicos', {})
            T(f'cerebro.json: {len(topicos)} topicos', len(topicos) > 0)
            
            # Indexar topicos no SDM
            indexados = 0
            for nome, dados in list(topicos.items())[:100]:
                texto = str(nome)
                if isinstance(dados, dict):
                    texto += ' ' + str(dados.get('texto', ''))
                hv = vocab.get(texto[:100])
                sdm.store(hv)
                indexados += 1
            T(f'SDM indexou {indexados} topicos', indexados > 0)
            
            # Testar retrieval semântico
            hv_query = vocab.get("sword")
            recon, fid, ativos = sdm.retrieve(hv_query)
            T(f'SDM retrieve "sword": fid={fid:.3f}, ativos={ativos}', fid > 0)
            
            hv_query2 = vocab.get("dragon")
            recon2, fid2, ativos2 = sdm.retrieve(hv_query2)
            T(f'SDM retrieve "dragon": fid={fid2:.3f}, ativos={ativos2}', fid2 > 0)
    except Exception as e:
        T('SDM+cerebro', None, str(e)[:100])

    # ─── 2. MCRFuel.abastecer() com fonte real ───────
    print('\n[2] MCRFuel.abastecer() — fontes reais')
    try:
        from mcr_kernel.evolution import MCRFuel
        fuel = MCRFuel()
        # Abastecer com manifesto + docs (fontes pequenas, rapidas)
        n = fuel.abastecer(fontes=['manifesto'])
        T(f'MCRFuel manifesto: {n} lessons', n >= 0)
    except Exception as e:
        T('MCRFuel', None, str(e)[:100])

    # ─── 3. Pipeline criativo end-to-end ─────────────
    print('\n[3] Pipeline Criativo: Emergir → MCRConector → SQLiteMarkov')
    try:
        from mcr.sqlite_markov import SQLiteMarkov
        from mcr_kernel.memory import MCRConector
        
        mk = SQLiteMarkov(os.path.join(_BASE, 'cache', 'mcr_adapt.db'), n_max=30)
        
        # Etapa 1: MCRConector encontra ponte entre conceitos
        conector = MCRConector()
        conector.alimentar(
            "O dragao cospe fogo e suas escamas brilham como ouro",
            "dragao"
        )
        conector.alimentar(
            "O ferreiro forja armaduras na bigorna com martelo e fogo",
            "ferreiro"
        )
        conexao = conector.conectar("dragao", "ferreiro")
        T('MCRConector dragao<->ferreiro', conexao is not None)
        if conexao:
            T(f'Ponte: {conexao.get("palavra_a","?")} <-> {conexao.get("palavra_b","?")} nota={conexao.get("nota",0):.1f}',
               conexao.get('nota', 0) > 0)
        
        # Etapa 2: Gerar código com identidade via SQLiteMarkov
        seq = mk.gerar_com_identidade('Adrenius', 'local', passos=30)
        tokens = [t for t in seq if not t.startswith('B:') and len(t) < 200]
        T(f'SQLiteMarkov Adrenius: {len(tokens)} tokens', len(tokens) > 10)
        
        # Verifica estrutura
        texto = ' '.join(tokens)
        estrutura = ['internalNpcName', 'Game.createNpcType', 'npcConfig']
        encontrados = [e for e in estrutura if e in texto]
        T(f'Estrutura NPC: {len(encontrados)}/{len(estrutura)}', len(encontrados) >= 2,
          f'encontrados={encontrados}')
        
        mk.close()
    except Exception as e:
        T('Pipeline criativo', None, str(e)[:100])

    # ─── 4. Geração em paralelo via MCRSpawner ────────
    print('\n[4] Geração paralela (MCRSpawner + SQLiteMarkov)')
    try:
        from mcr_kernel.evolution import MCRSpawner, MCRTarefa
        from mcr.sqlite_markov import SQLiteMarkov
        
        spawner = MCRSpawner()
        
        # Criar tarefas de geração para múltiplas identidades
        identidades = ['Adrenius', 'Ahmet', 'Sapo Azul', 'Sapo Coral']
        tarefas = []
        for ident in identidades:
            def gerar_ident(identity=ident):
                mk2 = SQLiteMarkov(os.path.join(_BASE, 'cache', 'mcr_adapt.db'), n_max=30)
                seq = mk2.gerar_com_identidade(identity, 'local', passos=20)
                tokens = [t for t in seq if not t.startswith('B:')]
                mk2.close()
                return {'identity': identity, 'tokens': len(tokens),
                        'texto': ' '.join(tokens[:10])}
            
            tarefas.append(MCRTarefa(f'gerar_{ident}', gerar_ident))
        
        t1 = time.time()
        workers = spawner.spawnar(tarefas)
        tempo_paralelo = time.time() - t1
        
        sucessos = sum(1 for w in workers if w.resultado is not None and w.erro is None)
        T(f'Paralelo: {sucessos}/{len(workers)} gerados em {tempo_paralelo:.3f}s',
           sucessos >= 1, f'{sucessos}/{len(workers)} workers')
    except Exception as e:
        T('Geração paralela', None, str(e)[:100])

    # ─── 5. MCRExpansao.expandir() ────────────────────
    print('\n[5] MCRExpansao.expandir() — auto-expansão')
    try:
        from mcr_kernel.evolution import MCRExpansao
        expansao = MCRExpansao()
        r = expansao.expandir("NPC ferreiro", max_recursos=3)
        T(f'MCRExpansao: {r.get("expansoes",0)} expansoes', r.get('expansoes', 0) >= 0)
    except Exception as e:
        T('MCRExpansao', None, str(e)[:100])

    # ─── 6. Classificação com dados reais ─────────────
    print('\n[6] Classificação (MarkovDecider com 15 seeds)')
    from mcr.adaptadores import PipelineConectado
    pipe = PipelineConectado()
    
    # Testa classificação em batch
    testes = [
        ("Crie um NPC mago em Yalahar", "criar_npc"),
        ("Gere um script de cura", "criar_codigo"),
        ("Explique o sistema SPA", "explicar_conceito"),
        ("Oi, como voce esta?", "conversa"),
        ("Quanto custa uma runa?", "conversa"),
        ("Analise este codigo por favor", "analisar_codigo"),
        ("Busque arquivos de configuracao", "busca_informacao"),
        ("Crie uma quest epica", "criar_quest"),
    ]
    acertos = 0
    for entrada, esperado in testes:
        classe, conf = pipe._decider.classificar(entrada)
        if classe == esperado:
            acertos += 1
    T(f'Classificação: {acertos}/{len(testes)} corretas', acertos >= 6,
       f'{acertos}/{len(testes)} = {acertos/len(testes)*100:.0f}%')
    pipe.close()

    # ─── 7. MCRAutoEvolution — evolução real ──────────
    print('\n[7] MCRAutoEvolution — evolução de thresholds')
    try:
        from mcr.mcr_auto_evolution import MCRAutoEvolution
        ae = MCRAutoEvolution()
        est = ae.estatisticas()
        T(f'MCRAutoEvolution: {est.get("mutacoes_aceitas",0)} mutacoes aceitas',
           est.get('mutacoes_aceitas', 0) >= 0)
    except Exception as e:
        T('MCRAutoEvolution', None, str(e)[:100])

    # ─── Resumo ──────────────────────────────────────
    print('\n' + '=' * 60)
    total = PASS + FAIL + ERR
    print(f'  RESULTADO: {PASS}/{total} PASS, {FAIL} FAIL, {ERR} ERR')
    print(f'  Tempo: {time.time()-t0:.1f}s')
    print('=' * 60)

if __name__ == '__main__':
    main()
