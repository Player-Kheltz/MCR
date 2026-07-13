"""modulos.progress_tracker — Tracking de progresso de pipeline."""
import json
from pathlib import Path

_CKPT_DIR = Path(__file__).resolve().parent.parent.parent / 'cache' / 'checkpoints'


def salvar_checkpoint(nome, dados):
    _CKPT_DIR.mkdir(parents=True, exist_ok=True)
    path = _CKPT_DIR / f'{nome}.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    return path


def carregar_checkpoint(nome):
    path = _CKPT_DIR / f'{nome}.json'
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def registrar_erro(etapa, erro, contexto=''):
    _CKPT_DIR.mkdir(parents=True, exist_ok=True)
    path = _CKPT_DIR / 'erros.json'
    erros = []
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            erros = json.load(f)
    erros.append({'etapa': etapa, 'erro': str(erro), 'contexto': contexto})
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(erros[-100:], f, ensure_ascii=False, indent=2)
