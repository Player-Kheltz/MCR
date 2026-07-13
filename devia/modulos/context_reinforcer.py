"""modulos.context_reinforcer — Reforco de contexto entre turnos."""


class ContextReinforcer:
    def __init__(self):
        self._historico = []

    def reforcar(self, contexto, novo_conteudo):
        self._historico.append(novo_conteudo)
        if len(self._historico) > 20:
            self._historico = self._historico[-20:]
        return contexto + '\n' + novo_conteudo if contexto else novo_conteudo
