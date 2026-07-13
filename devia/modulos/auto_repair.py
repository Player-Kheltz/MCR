"""modulos.auto_repair — Auto-reparo basico de codigo."""


class AutoRepair:
    def __init__(self):
        self._reparos = []

    def reparar(self, codigo, tipo='lua'):
        reparos = []
        if tipo == 'lua':
            if 'end' not in codigo and ('if ' in codigo or 'for ' in codigo):
                codigo += '\nend'
                reparos.append('end adicionado')
        self._reparos.extend(reparos)
        return codigo, reparos
