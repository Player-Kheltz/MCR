"""
mcr.generator_multinivel — Geracao de codigo via Markov Multinivel.
Usa MCRMotor + DeterministicFiller para gerar sem LLM.
"""
import os, sys, re

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'devia', 'kernel'))


class GeradorMultinivel:
    def __init__(self, motor=None):
        self.motor = motor
        self._filler_ok = False
        self._init_filler()

    def _init_filler(self):
        try:
            from DeterministicFiller import preencher_gap, preencher_template
            self._preencher_gap = preencher_gap
            self._preencher_template = preencher_template
            self._filler_ok = True
        except Exception:
            self._filler_ok = False

    def gerar_por_classe(self, classe: str, pergunta: str) -> str:
        if not self.motor or self.motor.mk_palavra.total < 20:
            return ''

        palavras = pergunta.split()
        semente = None
        for p in reversed(palavras):
            if p in self.motor.mk_palavra.freq:
                semente = p
                break
        if not semente:
            for _, topico in list(self.motor.topicos.items())[:5]:
                cands = [w for w in topico.get('palavras', [])
                         if w in self.motor.mk_palavra.freq]
                if cands:
                    semente = cands[0]
                    break

        if not semente:
            return ''

        passos = 20 if classe in ('criar_npc', 'criar_codigo') else 10
        seq = self.motor.mk_palavra.gerar(semente, passos=passos)
        texto = ' '.join(seq[1:]) if len(seq) > 1 else seq[0] if seq else ''

        if self._filler_ok:
            texto = self._preencher_template(texto, {'classe': classe})

        return texto[:800]

    def gerar_livre(self, semente: str, passos: int = 15) -> str:
        if not self.motor:
            return ''
        if semente not in self.motor.mk_palavra.freq:
            return ''
        seq = self.motor.mk_palavra.gerar(semente, passos=passos)
        return ' '.join(seq[1:])

    def stats(self):
        if not self.motor:
            return {'ativo': False}
        return {
            'ativo': True,
            'palavras': self.motor.mk_palavra.total,
            'topicos': len(self.motor.topicos),
            'entropia': round(self.motor.mk_palavra.entropia_media(), 4),
            'estados_unicos': len(self.motor.mk_palavra.freq),
        }
