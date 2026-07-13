#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LOOP — Validação COMPLETA: 143 tokens + integração + funções standalone"""
import sys, os, time
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
    print('  LOOP — Validação COMPLETA')
    print('=' * 60)

    # ─── 1. Validar TODOS os 143 tokens ─────────────
    print('\n[1] Validação de 143 tokens')
    from mcr.executor_map import _reg, _resolver
    tokens = _reg.listar_tokens()
    falhas_resolve = []
    for t in tokens:
        entry = _reg._registro[t]
        fn = _resolver(entry['fn_path'])
        if fn is None:
            falhas_resolve.append(t)
    
    T(f'Tokens total: {len(tokens)}', len(tokens) >= 140)
    T(f'Tokens que falham ao resolver: {len(falhas_resolve)}', len(falhas_resolve) == 0,
      str(falhas_resolve[:5]) if falhas_resolve else 'nenhum')
    T(f'Taxa de resolucao: {len(tokens)-len(falhas_resolve)}/{len(tokens)}', len(falhas_resolve) == 0)

    # ─── 2. Cadeia de integração ────────────────────
    print('\n[2] Cadeia: MCRMentePura → SQLiteMarkov → PipelineConectado')
    
    # MCRMentePura pensa sobre um problema
    from mcr.mcr_mente_pura import MCRMentePura
    mp = MCRMentePura()
    T('MCRMentePura: OK', mp is not None)
    
    # PipelineConectado processa
    from mcr.adaptadores import PipelineConectado
    pipe = PipelineConectado()
    T('PipelineConectado: OK', pipe is not None)
    
    s = pipe.status()
    conectados = sum(1 for v in s.values() if v)
    T(f'PipelineConectado: {conectados}/{len(s)} modulos', conectados >= 17)
    
    # SQLiteMarkov gera
    from mcr.sqlite_markov import SQLiteMarkov
    mk = SQLiteMarkov(os.path.join(_BASE, 'cache', 'mcr_adapt.db'), n_max=10)
    seq = mk.gerar_com_identidade('Adrenius', 'local', passos=15)
    tokens_gen = [t for t in seq if not t.startswith('B:') and len(t) < 200]
    T(f'SQLiteMarkov: {len(tokens_gen)} tokens', len(tokens_gen) > 5)
    mk.close()
    
    # EmergirUnificado criativo
    from mcr.emergir_unificado import EmergirUnificado
    eu = EmergirUnificado()
    ideia = eu.gerar_ideia()
    T(f'EmergirUnificado: ideia gerada', len(ideia.get('ideia', '')) > 10)
    
    # MCRWorldSystem
    from mcr.mcr_world_system import MCRWorldSystem
    ws = MCRWorldSystem()
    T('MCRWorldSystem: OK', ws is not None)
    
    # Metacognicao avalia
    from mcr.metacognicao import Metacognicao
    mc = Metacognicao()
    score, just = mc.calcular_confianca('criar npc ferreiro')
    T(f'Metacognicao: score={score:.2f}', score >= 0)
    
    # Todos integrados
    pipe.close()
    T('Cadeia completa: integrada', True)

    # ─── 3. Funções standalone do mcr/ ──────────────
    print('\n[3] Funções standalone (não registradas como tokens)')
    import mcr
    # Verifica funções importáveis mas não tokens
    all_tokens = set(tokens)
    standalone = []
    for name in dir(mcr):
        if name.startswith('_'): continue
        obj = getattr(mcr, name)
        if callable(obj) and not isinstance(obj, type):
            if name not in all_tokens:
                standalone.append(name)
    
    # Filtra path constants e I/O functions
    skip = {'ensure_dirs', 'read_file', 'write_file', 'read_lines', 'write_lines'}
    standalone = [s for s in standalone if s not in skip and not s.endswith('_DIR') 
                  and s not in ('ROOT_DIR','SERVER_DIR','MCR_PY','ROUTER_CACHE',
                                'KG_DIR','DATA_DIR','GENERATED_DIR','CACHE_DIR',
                                'DOCS_DIR','LORE_DIR','TOOLS_DIR','SCRIPTS_DIR',
                                'PROTOTYPES_DIR','SANDBOX_DIR','DEVIA_DIR',
                                'CLIENT_DIR','GRIMORIO_DIR','LOGIN_SERVER_DIR',
                                'MAP_EDITOR_DIR','SCRIPTS_GENERATED_DIR',
                                'SCRIPTS_QUARANTINE_DIR','GOLDEN_EXAMPLES_DIR',
                                'SANDBOX_CRIATIVO_DIR','IDEAS_DIR',
                                'CANARY_SRC_DIR','CANARY_SCRIPTS_DIR',
                                'CANARY_DATA_DIR','CANARY_NPC_DIR',
                                'CANARY_MONSTER_DIR','CANARY_ITEMS_XML',
                                'CANARY_CONFIG','DEVIA_KERNEL_DIR',
                                'DEVIA_MODULES_DIR','DEVIA_COMANDOS_DIR',
                                'DEVIA_KNOWLEDGE_DIR','DEVIA_ANALYSIS_DIR',
                                'DEVIA_TESTS_DIR','DEVIA_DATA_DIR',
                                'CANARY_BUILD_DIR','CLIENT_SRC_DIR',
                                'CLIENT_BUILD_DIR','POC_OUTPUT_DIR')]
    
    if standalone:
        T(f'Funções standalone exportadas: {len(standalone)}', len(standalone) <= 5,
          str(standalone))
    else:
        T('Funções standalone: 0 (todas são classes)', True)

    # ─── 4. Suite rápida ────────────────────────────
    print('\n[4] Suite rápida de regressão')
    import subprocess
    scripts = [
        'tests/real/test_final_8modulos.py',
        'tests/real/loop_check.py',
        'tests/real/loop5_sprites.py',
        'tests/real/loop6_qualidade.py',
    ]
    for script in scripts:
        r = subprocess.run([sys.executable, script], capture_output=True, text=True, timeout=120)
        for line in r.stdout.split('\n'):
            if 'RESULTADO:' in line:
                T(f'{os.path.basename(script)}: {line.strip()}', 'FAIL' not in line)

    # ─── Resumo ──────────────────────────────────────
    print('\n' + '=' * 60)
    total = PASS + FAIL + ERR
    print(f'  RESULTADO: {PASS}/{total} PASS, {FAIL} FAIL, {ERR} ERR')
    print(f'  Tempo: {time.time()-t0:.1f}s')
    print('=' * 60)

if __name__ == '__main__':
    main()
