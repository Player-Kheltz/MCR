#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCR AUTONOMO — Ciclo perpetuo de aprendizado autonomo.
explorar -> pensar -> evoluir -> repetir.
Uso: python start_mcr_organism.py --autonomo
"""
import sys
import os
import time
import threading

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, 'devia', 'kernel'))

from mcr.auto_curiosidade import AutoCuriosidade
from mcr.mcr_inner_voice import InnerVoice
from mcr.mcr_auto_evolution import MCRAutoEvolution
from mcr.mcr_meta import MCRMeta, MCRPesoNota


class CicloAutonomo:
    """Ciclo perpetuo: explorar -> pensar -> evoluir -> repetir."""

    def __init__(self, mcr_system=None):
        self.mcr_system = mcr_system
        self.curiosidade = AutoCuriosidade()
        self.inner_voice = InnerVoice(mcr_system=mcr_system)
        self.evolution = MCRAutoEvolution(mcr_system=mcr_system)
        self.peso_nota = MCRPesoNota()
        self._ciclo_atual = 0

    def executar(self):
        print("""
==================================================
  MCR AUTONOMO — Ciclo Perpetuo
  explorar -> pensar -> evoluir -> repetir
==================================================
""")
        while True:
            self._ciclo_atual += 1
            print('\n===== CICLO %d =====' % self._ciclo_atual)

            # 1. EXPLORAR
            print('\n[EXPLORAR] Diagnosticando gaps no KG...')
            try:
                self.curiosidade.ciclo_de_estudo()
            except Exception as e:
                print('  Erro: %s' % e)

            # 2. PENSAR
            print('\n[PENSAR] Gerando pensamentos...')
            try:
                pensamento = self.inner_voice.pensar()
                if pensamento:
                    print('  Pensamento: %s' % pensamento['pensamento'][:120])
                else:
                    print('  Nada novo para pensar.')
            except Exception as e:
                print('  Erro: %s' % e)

        # 3. EVOLUIR
        print('\n[EVOLUIR] Testando pesos, evoluindo equacao e mutando thresholds...')
        try:
            # Testa pesos da equacao
            pesos = self.peso_nota.testar()
            if 'melhor_combinacao' in pesos:
                print('  Melhores pesos MCRPesoNota: %s (score=%.2f)' % (
                    pesos['melhor_combinacao'], pesos['melhor_nota']))
            
            # Evolui a equacao (algoritmo genetico simples)
            from mcr.equacao_mcr import _EQUACAO_ATUAL, _FORMULAS_DISPONIVEIS
            eq_atual = dict(_EQUACAO_ATUAL)
            print('  Equacao atual: formula=%s, pesos=(%d,%d,%d)' % (
                eq_atual.get('formula', 'N/A'),
                eq_atual.get('peso_byte', 0),
                eq_atual.get('peso_palavra', 0),
                eq_atual.get('peso_token', 0)))
            
            # Muta thresholds
            self.evolution.ciclo(n_mutacoes=3)
        except Exception as e:
            print('  Erro na evolucao: %s' % e)

            # Diagnostico geral
            print('\n[DIAGNOSTICO]')
            try:
                diag = MCRMeta.diagnosticar()
                print('  KG: nota=%.2f/10, topicos=%d, gaps=%d' % (
                    diag['nota_geral'], diag['total_topicos'], diag['conexoes_fracas']))
            except Exception as e:
                print('  Erro: %s' % e)

            print('\n[Aguardando 60s para proximo ciclo...]')
            time.sleep(60)


if __name__ == '__main__':
    ciclo = CicloAutonomo()
    try:
        ciclo.executar()
    except KeyboardInterrupt:
        print('\n[Autonomo] Ciclo encerrado pelo usuario.')
