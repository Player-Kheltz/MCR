"""Progress Tracker Universal — Rastreamento em tempo real do pipeline MCR-DevIA.
Checkpoint persistente: salva estado a cada fase para retomada apos crash.

Fluxo:
  1. tracker.stage("CR") → escreve .mcr_progress.json com stage + progresso
  2. tracker.step() → incrementa substage
  3. Ao sair do context manager → marca como concluído
  4. Dashboard/CLI lê .mcr_progress.json para feedback em tempo real
  
  Checkpoint Recovery (NOVO):
    1. iniciar_pipeline("self_study") inicia pipeline com checkpoint
    2. checkpoint("scan", {...}) salva dados da fase
    3. Se o processo morrer, detectar_crash() retorna onde parou
    4. Pode retomar da ultima fase
"""
import os, sys, json, time, threading, contextlib
from datetime import datetime
from modulos.util import safe_ler_arquivo, safe_escrever_arquivo

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
PROGRESS_PATH = os.path.join(BASE, 'sandbox', '.mcr_progress.json')

_lock = threading.Lock()
_state = {
    'pid': os.getpid(),
    'started_at': None,
    'stage': None,
    'stage_started_at': None,
    'substage': '',
    'substage_index': 0,
    'substage_total': 0,
    'progress': 0.0,        # 0.0 a 1.0
    'elapsed': 0.0,
    'eta': None,
    'question_current': 0,
    'question_total': 0,
    'stages_history': [],    # lista de stages concluídos
    'last_updated': None,
    'status': 'idle',        # idle | running | completed | error
    'error': None,
    'pipeline': '',          # autoteste | perguntar | analisar | ...
}


def _agora():
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


def _escrever():
    """Escreve estado atual no .mcr_progress.json (thread-safe)."""
    with _lock:
        _state['last_updated'] = _agora()
        _state['elapsed'] = round(time.time() - (_state.get('started_at') or time.time()), 1)
        if _state['stage_started_at']:
            _state['stage_elapsed'] = round(time.time() - _state['stage_started_at'], 1)
        try:
            os.makedirs(os.path.dirname(PROGRESS_PATH), exist_ok=True)
            safe_escrever_arquivo(PROGRESS_PATH, json.dumps(_state, ensure_ascii=False, indent=2))
        except Exception:
            pass


def _calcular_eta():
    """Estima tempo restante baseado no progresso atual."""
    if _state['progress'] <= 0:
        return None
    elapsed = time.time() - (_state['started_at'] or time.time())
    if elapsed < 1:
        return None
    total_estimado = elapsed / _state['progress']
    restante = total_estimado - elapsed
    return round(restante, 1)


def iniciar(pipeline='', question_current=0, question_total=0):
    """Inicializa o tracker para uma nova execução."""
    with _lock:
        _state['pid'] = os.getpid()
        _state['started_at'] = time.time()
        _state['stage'] = None
        _state['stage_started_at'] = None
        _state['substage'] = ''
        _state['substage_index'] = 0
        _state['substage_total'] = 0
        _state['progress'] = 0.0
        _state['elapsed'] = 0.0
        _state['eta'] = None
        _state['question_current'] = question_current
        _state['question_total'] = question_total
        _state['stages_history'] = []
        _state['last_updated'] = _agora()
        _state['status'] = 'running'
        _state['error'] = None
        _state['pipeline'] = pipeline
    _escrever()
    _print_progress()


def reportar(stage, substage='', progress=None, question_current=None):
    """Reporta progresso atual. Chamado de qualquer módulo."""
    with _lock:
        if _state['stage'] != stage:
            # Stage diferente: registra o anterior no histórico
            if _state['stage'] and _state['stage'] != stage:
                _state['stages_history'].append({
                    'stage': _state['stage'],
                    'substage': _state['substage'],
                    'elapsed': round(time.time() - (_state['stage_started_at'] or time.time()), 1),
                })
            _state['stage'] = stage
            _state['stage_started_at'] = time.time()
            _state['substage_index'] = 0
            _state['substage_total'] = 0
        _state['substage'] = substage
        if progress is not None:
            _state['progress'] = progress
        if question_current is not None:
            _state['question_current'] = question_current
        _state['eta'] = _calcular_eta()
    _escrever()
    _print_progress()


def step(substage=''):
    """Avança um substage (ex: passo 3 de 5)."""
    with _lock:
        _state['substage_index'] += 1
        _state['substage'] = substage or f"passo_{_state['substage_index']}"
        _state['eta'] = _calcular_eta()
    _escrever()
    _print_progress()


def concluir():
    """Marca o tracker como concluído."""
    with _lock:
        if _state['stage']:
            _state['stages_history'].append({
                'stage': _state['stage'],
                'substage': _state['substage'],
                'elapsed': round(time.time() - (_state['stage_started_at'] or time.time()), 1),
            })
        _state['stage'] = 'COMPLETED'
        _state['progress'] = 1.0
        _state['substage'] = ''
        _state['status'] = 'completed'
        _state['eta'] = 0
    _escrever()
    _print_progress()


def erro(msg):
    """Marca o tracker como erro."""
    with _lock:
        if _state['stage']:
            _state['stages_history'].append({
                'stage': _state['stage'],
                'substage': _state['substage'],
                'elapsed': round(time.time() - (_state['stage_started_at'] or time.time()), 1),
            })
        _state['status'] = 'error'
        _state['error'] = msg
        _state['progress'] = min(_state['progress'], 0.95)  # never 100% on error
    _escrever()
    _print_progress()


@contextlib.contextmanager
def stage(name, total_steps=1, progress_start=None, progress_end=None):
    """Context manager para um stage. Uso:
        with tracker.stage("CR", total_steps=3) as ctx:
            ctx.step("extraindo termos")
            ctx.step("validando")
            ctx.step("gerando instrucao")
    """
    reportar(name)
    _ProgressCtx._current = _ProgressCtx(name, total_steps, progress_start, progress_end)
    try:
        yield _ProgressCtx._current
    except Exception as e:
        erro(f"{name}: {e}")
        raise
    finally:
        _ProgressCtx._current = None
        # Só marca conclusão se não houve troca de stage manual
        with _lock:
            if _state['stage'] == name:
                _state['stages_history'].append({
                    'stage': name,
                    'substage': _state.get('substage', ''),
                    'elapsed': round(time.time() - (_state['stage_started_at'] or time.time()), 1),
                })
                _state['progress'] = _state.get('progress', 0.0)


class _ProgressCtx:
    """Contexto interno do stage atual para chamadas step()."""
    _current = None
    
    def __init__(self, name, total_steps=1, progress_start=None, progress_end=None):
        self.name = name
        self.total_steps = total_steps
        self.progress_start = progress_start
        self.progress_end = progress_end
        self._step_count = 0
    
    def step(self, substage=''):
        self._step_count += 1
        # Calcula progress baseado nos steps
        if self.total_steps > 0:
            pct = self._step_count / self.total_steps
            if self.progress_start is not None and self.progress_end is not None:
                pct = self.progress_start + (self.progress_end - self.progress_start) * pct
            with _lock:
                _state['progress'] = min(pct, 1.0)
        step(substage)


def _print_progress():
    """Saída colorida no terminal para feedback imediato."""
    with _lock:
        s = _state
        stage_name = s.get('stage', '?') or '?'
        pct = int(s.get('progress', 0) * 100)
        eta = s.get('eta')
        q = s.get('question_current', 0)
        q_total = s.get('question_total', 0)
        substage = s.get('substage', '') or ''
    
    # Barra de progresso textual
    bar_len = 20
    filled = int(bar_len * pct / 100)
    bar = '#' * filled + '-' * (bar_len - filled)
    
    question_info = f" [Pergunta {q}/{q_total}]" if q_total > 0 else ""
    eta_info = f" ETA: {eta}s" if eta else ""
    substage_info = f" ({substage})" if substage else ""
    
    # Status line (limpa a linha atual com \r para não poluir)
    line = f"\r  [{bar}] {pct:3d}% | {stage_name}{substage_info}{question_info}{eta_info}"
    
    # Escreve no terminal (flush para aparecer imediatamente)
    sys.stdout.write(line)
    sys.stdout.flush()


def ler():
    """Lê o estado atual do .mcr_progress.json (para Dashboard/CLI)."""
    try:
        if os.path.exists(PROGRESS_PATH):
            return json.loads(safe_ler_arquivo(PROGRESS_PATH))
    except Exception:
        pass
    return {'status': 'not_found'}


def limpar():
    """Remove o arquivo de progresso."""
    with _lock:
        _state['status'] = 'idle'
    try:
        if os.path.exists(PROGRESS_PATH):
            os.remove(PROGRESS_PATH)
    except Exception:
        pass
    sys.stdout.write("\n")  # Nova linha após a última barra
    sys.stdout.flush()

# ============================================================
# CHECKPOINT PERSISTENTE — Retomada apos crash
# ============================================================

def iniciar_pipeline(pipeline_type):
    """Inicia uma pipeline com checkpoint. Salva ID unico + dados iniciais."""
    partes = [pipeline_type, datetime.now().strftime('%Y%m%d_%H%M%S'), str(os.getpid())]
    pipeline_id = '_'.join(partes)
    with _lock:
        _state['pipeline'] = pipeline_type
        _state['pipeline_id'] = pipeline_id
        _state['pipeline_started_at'] = time.time()
        _state['crashed_at'] = None
        _state['checkpoint'] = {'phase': 'inicio', 'data': {}}
        _state['error_info'] = None
        _state['pid'] = os.getpid()
        _state['status'] = 'running'
    reportar('iniciando')
    return pipeline_id


def salvar_checkpoint(phase, progress=None, **extra_data):
    """Salva checkpoint com dados especificos da fase.
    
    Args:
        phase: Nome da fase (ex: 'scan', 'auto_repair', 'insight')
        progress: Progresso 0.0-1.0 (opcional)
        **extra_data: Dados para salvar (ex: files_done=[...], current_file='...')
    """
    with _lock:
        _state['checkpoint'] = {'phase': phase, 'data': extra_data}
        _state['crashed_at'] = None  # limpa marca de crash anterior
        if progress is not None:
            _state['progress'] = progress
    reportar(phase, progress=progress)
    _escrever()


def registrar_erro(erro_msg, erro_type='Exception', arquivo=None, linha=None, trace=None):
    """Registra informacoes do erro para diagnostico de crash."""
    with _lock:
        _state['error_info'] = {
            'type': erro_type,
            'msg': str(erro_msg),
            'arquivo': arquivo,
            'linha': linha,
            'traceback': str(trace) if trace else None,
        }
        _state['crashed_at'] = time.time()
        _state['status'] = 'error'
    _escrever()


def detectar_crash():
    """Verifica se a execucao anterior crashou e retorna info para recovery.
    
    Returns:
        dict com checkpoint, error_info, crashed_at se houve crash
        None se nao houve crash ou pipeline completou com sucesso
    """
    try:
        if not os.path.exists(PROGRESS_PATH):
            return None
        estado = json.loads(safe_ler_arquivo(PROGRESS_PATH))
    except Exception:
        return None
    
    # Verifica se a pipeline nao completou (crashed_at existe)
    crashed_at = estado.get('crashed_at')
    if not crashed_at:
        return None  # nao crashou ou ja foi limpo
    
    # Verifica se o processo que iniciou ainda existe
    pid = estado.get('pid')
    if pid:
        try:
            import signal
            os.kill(pid, 0)  # verifica se o processo existe
            # Processo ainda existe — pode ser uma pipeline longa ainda rodando
            return None
        except (OSError, ImportError):
            pass  # Processo nao existe — crash confirmado
    
    # Crash confirmado! Retorna dados para recovery
    return {
        'pipeline_id': estado.get('pipeline_id'),
        'pipeline_type': estado.get('pipeline'),
        'checkpoint': estado.get('checkpoint', {}),
        'error_info': estado.get('error_info'),
        'crashed_at': crashed_at,
        'stages': estado.get('stages_history', []),
    }


def limpar_checkpoint():
    """Remove checkpoint apos conclusao bem-sucedida."""
    limpar()


@contextlib.contextmanager
def checkpoint_pipeline(pipeline_type):
    """Context manager que inicia pipeline com checkpoint e limpa ao final.
    
    Uso:
        with checkpoint_pipeline('self_study') as ctx:
            ctx.checkpoint('scan', files_found=arquivos)
            ...  # se der erro, checkpoint salva erro_info
            ctx.checkpoint('fim', progress=1.0)
    
    Se o processo crashar, detectar_crash() retorna os dados do checkpoint.
    """
    pipeline_id = iniciar_pipeline(pipeline_type)
    try:
        yield _CheckpointCtx(pipeline_id)
        concluir()
        limpar_checkpoint()
    except Exception as e:
        registrar_erro(str(e), type(e).__name__)
        # Re-raise a excecao para nao esconder erros
        raise


class _CheckpointCtx:
    """Contexto interno para checkpoint pipeline."""
    
    def __init__(self, pipeline_id):
        self.pipeline_id = pipeline_id
    
    def checkpoint(self, phase, progress=None, **data):
        salvar_checkpoint(phase, progress, **data)
