"""modulos.blank_filler — Preenche slots vazios em templates."""


class BlankFiller:
    def __init__(self):
        self._fallbacks = {}

    def preencher(self, template, slots=None):
        if not slots:
            slots = {}
        resultado = template
        for k, v in slots.items():
            resultado = resultado.replace(f'{{{k}}}', str(v))
        return resultado
