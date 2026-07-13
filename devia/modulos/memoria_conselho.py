"""modulos.memoria_conselho — Memoria para decisoes do conselho.

Redireciona para dialogue_trainer para historico de dialogos.
"""
try:
    from mcr.dialogue_trainer import DialogueTrainer as _DT
except ImportError:
    _DT = None


class MemoriaConselho:
    def __init__(self):
        self._historico = []

    def salvar(self, decisao, contexto=''):
        self._historico.append({'decisao': decisao, 'contexto': contexto})

    def carregar(self, limite=10):
        return self._historico[-limite:]

    def limpar(self):
        self._historico.clear()
