"""modulos.diagnostic_engine — Motor de diagnostico detalhado."""


class DiagnosticEngine:
    def __init__(self):
        self._checks = []

    def adicionar_check(self, nome, func):
        self._checks.append((nome, func))

    def executar(self):
        resultados = {}
        for nome, func in self._checks:
            try:
                resultados[nome] = func()
            except Exception as e:
                resultados[nome] = {'erro': str(e)}
        return resultados
