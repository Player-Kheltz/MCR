"""Comando: resume - Retoma sessao de pipeline interrompida."""
def register():
    return {
        "name": "resume",
        "desc": "Retoma sessao de pipeline interrompida. Detecta cache e continua de onde parou.",
        "handler": execute,
        "args": [],
        "categoria": "pipeline",
    }

def execute(kg, ia, args, ctx_crew=None):
    """Verifica se ha sessao incompleta e mostra status para resume."""
    import os, sys, json
    
    BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    CACHE_PATH = os.path.join(BASE, 'sandbox', '.mcr_session_cache.json')
    PROGRESS_PATH = os.path.join(BASE, 'sandbox', '.mcr_progress.json')
    
    # 1. Verifica session_cache
    tem_cache = os.path.exists(CACHE_PATH)
    tem_progress = os.path.exists(PROGRESS_PATH)
    
    print(f'\n=== Status de Sessao ===')
    print(f'Session cache: {"EXISTE" if tem_cache else "NAO EXISTE"}')
    print(f'Progress tracker: {"EXISTE" if tem_progress else "NAO EXISTE"}')
    
    if not tem_cache:
        print('Nenhuma sessao para resumir.')
        return True
    
    try:
        with open(CACHE_PATH, 'r', encoding='utf-8') as f:
            cache = json.load(f)
    except Exception as e:
        print(f'Erro ao ler cache: {e}')
        return True
    
    pipeline_id = cache.get('pipeline_id', 'N/A')
    status = cache.get('status', 'unknown')
    pipeline_type = cache.get('pipeline_type', 'N/A')
    ultimo_passo = cache.get('ultimo_passo', -1)
    passos = cache.get('passos_completados', {})
    plano = cache.get('plano', [])
    
    print(f'\nPipeline ID: {pipeline_id}')
    print(f'Tipo: {pipeline_type}')
    print(f'Status: {status}')
    print(f'Passos completados: {len(passos)}/{len(plano)}')
    print(f'Ultimo passo: {ultimo_passo}')
    
    if status == 'completed':
        print('\nSessao ja foi concluida com sucesso.')
        print('Para limpar: o proximo pipeline automaticamente cria nova sessao.')
        return True
    
    if status == 'running' and ultimo_passo >= 0:
        pendentes = len(plano) - len(passos)
        print(f'\n>>> Sessao INCOMPLETA: {pendentes} passos pendentes para resume')
        print(f'>>> Execute o mesmo comando novamente para retomar automaticamente.')
        
        # Mostra quais passos estao pendentes
        if plano:
            print(f'\nPassos pendentes:')
            for i, item in enumerate(plano):
                if str(i) not in passos:
                    print(f'  [{i+1}/{len(plano)}] {item["tool"]}: {item["solicitacao"]}...')
    
    # Mostra info de crash se progress existir
    if tem_progress:
        try:
            from modulos.progress_tracker import detectar_crash
            crash = detectar_crash()
            if crash:
                print(f'\nCrash detectado em: {crash.get("crashed_at")}')
                erro = crash.get('error_info', {})
                if erro:
                    print(f'Erro: {erro.get("type")}: {erro.get("msg")}')
        except Exception:
            pass
    
    return True
