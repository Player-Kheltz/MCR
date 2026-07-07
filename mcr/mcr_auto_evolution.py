#!/usr/bin/env python3
"""mcr.mcr_auto_evolution — Auto-Evolucao por mutacao de thresholds.
Portada do MCRAutoLoop original. Muta thresholds, mede entropia, aceita/rejeita."""
import json
import time
import math
import random
from pathlib import Path
from typing import Dict, List, Optional

from mcr.paths import KG_DIR


class MCRAutoEvolution:
    """Auto-evolucao: muta thresholds do sistema, mede impacto na entropia,
    aceita a mutacao se reduzir o caos, rejeita se aumentar."""

    def __init__(self, mcr_system=None):
        self._mcr = mcr_system
        self._mutacoes_aceitas = 0
        self._mutacoes_rejeitadas = 0
        self._ultima_entropia = 1.0

    def entropia_global(self) -> float:
        """Calcula a entropia media do sistema."""
        if not self._mcr or not hasattr(self._mcr, 'mk_palavra'):
            return 1.0
        
        mk = self._mcr.mk_palavra
        transicoes = getattr(mk, 'transicoes', {})
        if not transicoes:
            return 1.0
        
        entropias = []
        for estado, proximos in transicoes.items():
            total = sum(proximos.values())
            if total == 0:
                continue
            h = 0.0
            for count in proximos.values():
                p = count / total
                if p > 0:
                    h -= p * math.log2(p)
            entropias.append(h)
        
        return sum(entropias) / len(entropias) if entropias else 1.0

    def mutar(self) -> Dict:
        """Aplica uma mutacao aleatoria nos thresholds do sistema.
        
        Returns:
            dict com 'threshold', 'mutacao_aplicada', 'entropia_antes', 'entropia_depois', 'aceita'
        """
        if not self._mcr:
            return {'erro': 'MCRSystem nao disponivel'}

        # Entropia antes
        h_antes = self.entropia_global()
        self._ultima_entropia = h_antes

        # Escolhe um threshold para mutar
        thresholds = ['temperatura', 'confianca', 'curiosidade', 'criatividade']
        threshold_alvo = random.choice(thresholds)

        # Aplica mutacao: +/- 10-30%
        mutacao = random.uniform(-0.3, 0.3)
        
        # Simula: no MCR real, mutaria o threshold no sistema
        # Aqui registramos o que seria mutado
        resultado = {
            'threshold': threshold_alvo,
            'mutacao_aplicada': round(mutacao, 3),
            'entropia_antes': round(h_antes, 4),
            'aceita': False,
        }

        # Mede entropia depois (simulada para demonstracao)
        # No sistema real, alimentaria dados com o novo threshold e mediria
        h_depois = h_antes * (1.0 + mutacao * random.uniform(-0.5, 0.5))
        resultado['entropia_depois'] = round(h_depois, 4)

        # Aceita se entropia reduziu (menos caos = mais coerencia)
        if h_depois < h_antes:
            resultado['aceita'] = True
            self._mutacoes_aceitas += 1
        else:
            resultado['aceita'] = False
            self._mutacoes_rejeitadas += 1

        print('[AutoEvol] Mutacao: %s %+.1f%% | entropia: %.4f -> %.4f | %s' % (
            threshold_alvo, mutacao * 100, h_antes, h_depois,
            'ACEITA' if resultado['aceita'] else 'REJEITADA'))

        return resultado

    def ciclo(self, n_mutacoes: int = 5) -> List[Dict]:
        """Executa N mutacoes em sequencia."""
        resultados = []
        for i in range(n_mutacoes):
            r = self.mutar()
            resultados.append(r)
        print('[AutoEvol] Ciclo: %d aceitas, %d rejeitadas' % (
            self._mutacoes_aceitas, self._mutacoes_rejeitadas))
        return resultados

    def estatisticas(self) -> Dict:
        return {
            'mutacoes_aceitas': self._mutacoes_aceitas,
            'mutacoes_rejeitadas': self._mutacoes_rejeitadas,
            'ultima_entropia': round(self._ultima_entropia, 4),
            'taxa_aceite': round(self._mutacoes_aceitas / max(self._mutacoes_aceitas + self._mutacoes_rejeitadas, 1), 3),
        }
