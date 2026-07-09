"""mcr.silent_log — Log silencioso para threads de background.
Escreve em arquivo em vez de imprimir no stdout, para nao invadir o terminal de conversa."""
import os
import time
from pathlib import Path

from mcr.paths import DEVIA_DIR

_LOG_PATH = DEVIA_DIR / "mcr_background.log"


def log(mensagem: str, arquivo=None):
    """Escreve uma mensagem no arquivo de log silencioso.
    
    Args:
        mensagem: texto para logar.
        arquivo: caminho alternativo (opcional).
    """
    caminho = Path(arquivo) if arquivo else _LOG_PATH
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        with open(caminho, 'a', encoding='utf-8') as f:
            f.write('[%s] %s\n' % (time.strftime('%H:%M:%S'), mensagem))
    except Exception:
        pass  # Nunca quebrar por causa de log


def limpar():
    """Limpa o arquivo de log."""
    try:
        if _LOG_PATH.exists():
            _LOG_PATH.unlink()
    except Exception:
        pass


def ler(linhas=20):
    """Le as ultimas N linhas do log."""
    try:
        if not _LOG_PATH.exists():
            return []
        with open(_LOG_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return [l.rstrip() for l in lines[-linhas:]]
    except Exception:
        return []
