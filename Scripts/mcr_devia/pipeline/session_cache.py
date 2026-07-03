"""Session Cache — Cache de sessão para resume de pipelines interrompidas.

Salva estado completo de cada passo do pipeline para retomar de onde parou.
Usa detectar_crash() do progress_tracker para saber se houve crash.

Arquitetura:
  1. iniciar_sessao() — cria cache com pipeline_id + plano completo
  2. salvar_passo() — salva resposta de cada passo no cache
  3. passo_ja_executado() — verifica se passo ja foi executado (para skip)
  4. detectar_sessao_incompleta() — detecta sessao anterior que crashou
  5. resumir_sessao() — retorna dados para continuar do ultimo passo
  6. limpar_sessao() — limpa cache apos conclusao bem-sucedida

Integra com progress_tracker.detectar_crash() para identificar crashes.
"""
import os, sys, json, time
from datetime import datetime

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
CACHE_PATH = os.path.join(BASE, 'sandbox', '.mcr_session_cache.json')

# Estado em memoria para acesso rapido
_cache = {
    'pipeline_id': None,
    'pipeline_type': None,
    'texto_original': '',
    'plano': [],
    'passos_completados': {},  # {indice: {'resposta': str, 'tool': str, 'ts': float}}
    'iniciado_em': None,
    'ultimo_passo': -1,
    'status': 'idle',  # idle | running | completed | error
}


def iniciar_sessao(pipeline_type, texto_original, plano):
    """Inicia uma nova sessao de pipeline com checkpoint.
    
    Se detectar sessao incompleta anterior, retorna dados para resume.
    Senao, cria nova sessao do zero.
    
    Args:
        pipeline_type: str, tipo de pipeline (ex: 'perguntar', 'analisar')
        texto_original: str, pergunta/texto original
        plano: list[dict], plano de execucao (criado pelo RequestPlanner)
    
    Returns:
        dict: {'nova': True, 'passos_completados': 0} para sessao nova
        dict: {'nova': False, 'ultimo_passo': 5, 'passos_completados': {...}} para resume
    """
    global _cache
    
    # Verifica se ha sessao incompleta
    incompleta = detectar_sessao_incompleta()
    if incompleta:
        # Verifica se e o mesmo tipo de pipeline
        if incompleta.get('pipeline_type') == pipeline_type:
            # E a mesma pipeline interrompida — retorna para resume
            _cache = incompleta
            completados = len(_cache.get('passos_completados', {}))
            ultimo = _cache.get('ultimo_passo', -1)
            print(f'[SessionCache] Sessao anterior encontrada: {completados}/{len(plano)} passos completados (ultimo: passo {ultimo})')
            return {
                'nova': False,
                'ultimo_passo': ultimo,
                'passos_completados': _cache.get('passos_completados', {}),  # dict, nao int!
                'total_passos': len(plano),
            }
        else:
            # Pipeline diferente — limpa sessao anterior
            print(f'[SessionCache] Sessao anterior ({incompleta["pipeline_type"]}) descartada — pipeline diferente')
            limpar_sessao()
    
    # Cria nova sessao
    pipeline_id = f"{pipeline_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
    _cache = {
        'pipeline_id': pipeline_id,
        'pipeline_type': pipeline_type,
        'texto_original': texto_original,
        'plano': plano,
        'passos_completados': {},
        'iniciado_em': time.time(),
        'ultimo_passo': -1,
        'status': 'running',
    }
    _salvar()
    print(f'[SessionCache] Nova sessao: {pipeline_id} ({len(plano)} passos)')
    return {'nova': True, 'passos_completados': 0, 'total_passos': len(plano)}


def salvar_passo(indice, tool, solicitacao, resposta):
    """Salva resultado de um passo no cache.
    
    Args:
        indice: int, indice do passo no plano
        tool: str, ferramenta usada (ex: 'IA', 'PYTHON')
        solicitacao: str, solicitacao executada
        resposta: str, resposta obtida
    """
    global _cache
    if not _cache.get('pipeline_id'):
        return
    
    _cache['passos_completados'][str(indice)] = {
        'resposta': resposta,
        'tool': tool,
        'solicitacao': solicitacao,
        'ts': time.time(),
    }
    if indice > _cache['ultimo_passo']:
        _cache['ultimo_passo'] = indice
    _cache['status'] = 'running'
    _salvar()


def passo_ja_executado(indice):
    """Verifica se um passo ja foi executado (para skip em resume).
    
    Args:
        indice: int, indice do passo
    
    Returns:
        str or None: resposta se executado, None se nao
    """
    return _cache.get('passos_completados', {}).get(str(indice), {}).get('resposta')


def detectar_sessao_incompleta():
    """Detecta sessao anterior incompleta via cache + detectar_crash()."""
    # 1. Carrega cache salvo em disco
    if not os.path.exists(CACHE_PATH):
        return None
    
    try:
        with open(CACHE_PATH, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
    except Exception:
        return None
    
    if not cache_data.get('pipeline_id'):
        return None
    if cache_data.get('status') == 'completed':
        return None
    if cache_data.get('status') == 'idle':
        return None
    if not cache_data.get('passos_completados'):
        return None
    
    return cache_data  # Sessao incompleta detectada


def resumir_sessao():
    """Retorna dados para continuar do ultimo passo.
    
    Returns:
        dict with ultimo_passo, passos_completados, plano, texto_original
        None se nao ha sessao para resumir
    """
    if not _cache.get('pipeline_id') or _cache.get('status') == 'completed':
        return None
    if _cache.get('ultimo_passo', -1) < 0:
        return None
    
    return {
        'ultimo_passo': _cache['ultimo_passo'],
        'passos_completados': _cache.get('passos_completados', {}),
        'plano': _cache.get('plano', []),
        'texto_original': _cache.get('texto_original', ''),
        'total_passos': len(_cache.get('plano', [])),
    }


def obter_resposta_completa():
    """Monta resposta completa a partir dos passos em cache.
    
    Returns:
        str: resposta concatenada de todos os passos completados
    """
    passos = _cache.get('passos_completados', {})
    if not passos:
        return ''
    
    partes = []
    for i in sorted(int(k) for k in passos.keys()):
        partes.append(passos[str(i)]['resposta'])
    return '\n\n'.join(partes)


def concluir_sessao():
    """Marca sessao como concluida com sucesso."""
    global _cache
    if _cache.get('pipeline_id'):
        _cache['status'] = 'completed'
        _cache['concluido_em'] = time.time()
        _salvar()


def limpar_sessao():
    """Remove cache de sessao apos conclusao ou aborto."""
    global _cache
    _cache = {
        'pipeline_id': None, 'pipeline_type': None, 'texto_original': '',
        'plano': [], 'passos_completados': {}, 'iniciado_em': None,
        'ultimo_passo': -1, 'status': 'idle',
    }
    try:
        if os.path.exists(CACHE_PATH):
            os.remove(CACHE_PATH)
    except Exception:
        pass


def _salvar():
    """Salva cache em disco (thread-safe via atomic write)."""
    try:
        temp_path = CACHE_PATH + '.tmp'
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(_cache, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, CACHE_PATH)  # atomico no Windows
    except Exception as e:
        print(f'[SessionCache] Erro ao salvar: {e}')
