"""
TESTE REAL — Pipeline Conectado com SQLiteMarkov

Testa:
  1. MarkovDecider classifica entrada
  2. MarkovRouter escolhe pipeline
  3. MCRSpawner spawna workers
  4. SQLiteMarkov gera código REAL
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from mcr.adaptadores import PipelineConectado

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

def main():
    print('=' * 60)
    print('  TESTE REAL — Pipeline Conectado')
    print('=' * 60)
    
    pipe = PipelineConectado()
    s = pipe.status()
    print(f'  Status: {s}')
    
    if not s['sqlite_markov']:
        print('  SQLiteMarkov não disponível — abortando')
        return
    
    # Teste 1: Gerar NPC com SQLiteMarkov
    print('\n' + '-' * 60)
    print('  TESTE 1: Gerar NPC via SQLiteMarkov')
    print('-' * 60)
    
    from mcr.sqlite_markov import SQLiteMarkov
    mk = SQLiteMarkov(os.path.join(_BASE, 'cache', 'mcr_adapt.db'), n_max=30)
    
    identidades = ['Adrenius', 'Ahmet', 'Ferronius']
    for ident in identidades:
        t0 = time.time()
        seq = mk.gerar_com_identidade(ident, 'local', passos=40)
        tempo = time.time() - t0
        
        # Filtra tokens B: e control
        tokens_limpos = [t for t in seq if not t.startswith('B:') and len(t) < 200]
        
        acertos_npc = ['internalNpcName', 'Game.createNpcType', 'npcConfig', 'npcHandler']
        encontrados = [a for a in acertos_npc if a in ' '.join(tokens_limpos)]
        
        print(f'\n  [{ident}] {len(tokens_limpos)} tokens em {tempo:.3f}s')
        print(f'    Estrutura: {len(encontrados)}/{len(acertos_npc)} acertos')
        if encontrados:
            print(f'    ✓ {", ".join(encontrados)}')
        print(f'    Preview: {" ".join(tokens_limpos[:15])}...')
    
    # Teste 2: Pipeline completo
    print('\n' + '-' * 60)
    print('  TESTE 2: Pipeline Decider → Router → Spawner')
    print('-' * 60)
    
    entradas = [
        'Crie um NPC ferreiro em Thais',
        'Gere um script Lua de teleporte',
        'Explique como funciona o SPA',
    ]
    
    for entrada in entradas:
        print(f'\n  [ENTRADA] {entrada}')
        r = pipe.processar(entrada)
        classe = r['etapas']['classificar']['classe']
        conf = r['etapas']['classificar']['confianca']
        acoes = r['etapas']['rotear']['acoes']
        n_tarefas = r['etapas']['converter']['n_tarefas']
        print(f'    Classe: {classe} (conf={conf:.2f})')
        print(f'    Pipeline: {" → ".join(acoes[:4])}')
        print(f'    Tarefas: {n_tarefas} executadas em {r["tempo_total"]:.4f}s')
    
    # Teste 3: Geração com fallback mk_palavra
    print('\n' + '-' * 60)
    print('  TESTE 3: Gerar com fallback MCRSQLite (mk_palavra)')
    print('-' * 60)
    
    try:
        from mcr.mcr_sqlite import MCRSQLite
        mk_palavra = MCRSQLite(os.path.join(_BASE, 'cache', 'mcr_conversa.db'), n_max=5, identidade='conversa')
        
        def fallback_word(tok):
            p, c = mk_palavra.predizer(tok)
            return (p, c) if p else (None, 0.0)
        
        # Testa com identidade que pode não existir no mcr_adapt
        ident_teste = 'Merlin'
        seq = mk.gerar_com_identidade(ident_teste, 'local', passos=40, fallback_fn=fallback_word)
        tokens_limpos = [t for t in seq if not t.startswith('B:')]
        print(f'  [{ident_teste}] {len(tokens_limpos)} tokens')
        print(f'  Preview: {" ".join(tokens_limpos[:20])}...')
        
        mk_palavra.conn.close()
    except Exception as e:
        print(f'  Erro fallback: {e}')
    
    mk.close()
    pipe.close()
    
    print('\n' + '=' * 60)
    print('  TESTE CONCLUÍDO')
    print('=' * 60)

if __name__ == '__main__':
    main()
