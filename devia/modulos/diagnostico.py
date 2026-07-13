"""modulos.diagnostico — Diagnostico leve do sistema."""


class Diagnostico:
    def __init__(self):
        self._problemas = []

    def diagnosticar(self):
        return {
            'problemas': self._problemas,
            'status': 'ok' if not self._problemas else 'atencao',
        }

    def registrar(self, problema, severidade='baixa'):
        self._problemas.append({'problema': problema, 'severidade': severidade})
