"""
Adapter que conecta MCRHybridClassifier + MCRGuardrail ao PipelineCompleto.
Usa mcr_universal (prototype) como backend de decisao.
"""
import os, re, sys
from pathlib import Path
from typing import Dict, Optional

_MCR_ROOT = str(Path(__file__).resolve().parent.parent)

from mcr_universal.hybrid.classifier import MCRHybridClassifier
from mcr_universal.hybrid.guardrail import MCRGuardrail
from mcr_universal.emergence.motor import MCRMotor


class HybridRouter:
    def __init__(self, motor: MCRMotor = None):
        self.motor = motor or MCRMotor()
        self.classifier = MCRHybridClassifier(motor=self.motor)
        self.guardrail = MCRGuardrail(motor=self.motor)
        self.stats = {'mcr': 0, 'llm': 0, 'rejeitadas': 0}

    def decidir_rota(self, pergunta: str) -> Dict:
        return self.classifier.classificar(pergunta)

    def validar_resposta(self, resposta: str, pergunta: str) -> Dict:
        return self.guardrail.validar(resposta, pergunta)

    def gerar_mcr(self, pergunta: str, passos: int = 15) -> str:
        try:
            from mcr.generator_multinivel import GeradorMultinivel
            gen = GeradorMultinivel(motor=self.motor)
            resultado = gen.gerar_livre(pergunta, passos=passos)
            if resultado:
                return resultado
        except Exception:
            pass

        palavras = pergunta.split()
        semente = None
        for p in reversed(palavras):
            if p in self.motor.mk_palavra.freq:
                semente = p
                break
        if not semente:
            return ''
        seq = self.motor.mk_palavra.gerar(semente, passos=passos)
        texto = ' '.join(seq[1:]) if seq else ''
        return texto[:500]

    def gerar_por_classe(self, classe: str, pergunta: str) -> str:
        try:
            from mcr.generator_multinivel import GeradorMultinivel
            gen = GeradorMultinivel(motor=self.motor)
            return gen.gerar_por_classe(classe, pergunta)
        except Exception:
            return ''

    def alimentar_motor(self, texto: str, nome_topico: str = None):
        self.motor.alimentar(texto, nome_topico)

    def alimentar_de_arquivos_lua(self, diretorio, max_n: int = 100):
        diretorio = Path(diretorio)
        if not diretorio.exists():
            return 0
        count = 0
        for fpath in sorted(diretorio.rglob('*.lua')):
            if count >= max_n:
                break
            try:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    codigo = f.read()
                if len(codigo) < 50:
                    continue
                nome = fpath.stem
                self.motor.alimentar(codigo[:5000], f'npc_{nome}')
                count += 1
            except Exception:
                continue
        return count
