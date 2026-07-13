"""modulos.lessons_buffer — Buffer de lições aprendidas."""
import json, time
from pathlib import Path

_BUFFER_PATH = Path(__file__).resolve().parent.parent.parent / 'cache' / 'lessons_buffer.json'


class LessonsBuffer:
    def __init__(self):
        self._lições = []
        self._carregar()

    def _carregar(self):
        if _BUFFER_PATH.exists():
            try:
                with open(_BUFFER_PATH, 'r', encoding='utf-8') as f:
                    self._lições = json.load(f)
            except Exception:
                self._lições = []

    def salvar(self):
        _BUFFER_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_BUFFER_PATH, 'w', encoding='utf-8') as f:
            json.dump(self._lições[-200:], f, ensure_ascii=False, indent=2)

    def adicionar(self, lição, contexto=''):
        self._lições.append({
            'lição': lição,
            'contexto': contexto,
            'timestamp': time.time(),
        })
        self.salvar()

    def recuperar(self, tema='', limite=5):
        if not tema:
            return self._lições[-limite:]
        return [l for l in self._lições if tema.lower() in str(l).lower()][-limite:]
