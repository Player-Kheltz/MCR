"""modulos.pos_processamento — Pos-processamento de codigo gerado."""


class PosProcessamento:
    def __init__(self):
        self._regras = []

    def processar(self, codigo, linguagem='lua'):
        resultado = codigo
        if linguagem == 'lua':
            resultado = resultado.rstrip() + '\n'
        return resultado
