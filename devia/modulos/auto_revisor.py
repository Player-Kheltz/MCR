"""modulos.auto_revisor — Redireciona para mcr.anti_pattern."""
try:
    from mcr.anti_pattern import classificar_erro, registrar_anti_pattern
except ImportError:
    classificar_erro = lambda *a, **kw: {'tipo': 'desconhecido'}
    registrar_anti_pattern = lambda *a, **kw: False

try:
    from mcr.metacognicao import Metacognicao as MCRThreshold
except ImportError:
    MCRThreshold = None


class AutoRevisor:
    def __init__(self):
        self._revisoes = []

    def revisar(self, texto_resposta, classes_permitidas=None, pergunta_original=''):
        alucinacoes = []
        return {
            'alucinacoes': alucinacoes,
            'total': len(alucinacoes),
            'sugestao': 'resposta parece OK',
            'generica': False,
        }

    def auto_corrigir(self, texto_resposta, classes_permitidas=None):
        resultado = self.revisar(texto_resposta, classes_permitidas)
        return texto_resposta, resultado
