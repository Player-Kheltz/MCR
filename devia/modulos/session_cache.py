"""modulos.session_cache — Cache de sessao para pipelines."""
import json, time
from pathlib import Path

_CACHE_PATH = Path(__file__).resolve().parent.parent.parent / 'cache' / 'session_cache.json'


def detectar_sessao_incompleta():
    if _CACHE_PATH.exists():
        try:
            with open(_CACHE_PATH, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            if dados.get('timestamp', 0) > time.time() - 3600:
                return dados
        except Exception:
            pass
    return None


def resumir_sessao(dados):
    return dados


def salvar_sessao(dados):
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    dados['timestamp'] = time.time()
    with open(_CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
