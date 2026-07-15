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
        """Aplica uma mutacao real nos thresholds do sistema e MEDE o impacto.
        
        Fluxo:
        1. Snapshot da entropia global atual
        2. Muta um threshold real (MCRThreshold existente)
        3. Executa 3 predicoes de teste no MCR
        4. Mede a entropia REAL apos a mutacao
        5. Aceita se entropia reduziu, rejeita se aumentou
        6. Reverte a mutacao se rejeitada
        
        Returns:
            dict com resultados da mutacao
        """
        if not self._mcr:
            return {'erro': 'MCRSystem nao disponivel'}
        
        from mcr.decisor import MCRThreshold
        
        # 1. Entropia antes (medida real)
        h_antes = self.entropia_global()
        self._ultima_entropia = h_antes
        
        # 2. Escolhe threshold real para mutar (inclui equação MCR)
        from mcr.equacao_mcr import _EQUACAO_ATUAL
        tipo_mutacao = random.choice(['threshold', 'equacao'])
        
        if tipo_mutacao == 'equacao':
            # M4: Muta parâmetro da equação MCR
            param_alvo = random.choice(['ponte_divergencia', 'ponte_especificidade',
                                         'ponte_profundidade', 'penalidade_parcial'])
            valor_atual = _EQUACAO_ATUAL[param_alvo]
            mutacao = random.uniform(-0.5, 0.5)
            novo_valor = max(0.0, min(10.0, valor_atual + mutacao))
            _EQUACAO_ATUAL[param_alvo] = round(novo_valor, 2)
            resultado_base = {
                'threshold': f'equacao:{param_alvo}',
                'mutacao_aplicada': round(novo_valor - valor_atual, 3),
                'valor_anterior': round(valor_atual, 3),
                'valor_novo': round(novo_valor, 3),
            }
            # Mede impacto
            h_depois = self.entropia_global()
            delta_h = h_depois - h_antes
            resultado_base.update({
                'entropia_antes': round(h_antes, 4),
                'entropia_depois': round(h_depois, 4),
                'aceita': delta_h < -0.001,
            })
            if delta_h >= -0.001:
                _EQUACAO_ATUAL[param_alvo] = valor_atual  # reverte
            return resultado_base
        
        thresholds_disponiveis = [
            ('threshold', MCRThreshold, 'obter', 'aprender'),
        ]
        threshold_alvo = random.choice(['threshold_confianca', 'threshold_tamanho',
                                          'threshold_repeticao', 'threshold_palavra'])
        
        # Cria/Muta threshold real
        thr = MCRThreshold(threshold_alvo)
        valor_atual = thr.obter(threshold_alvo, 0.5)
        mutacao = random.uniform(-0.3, 0.3)
        novo_valor = max(0.05, min(0.95, valor_atual + mutacao * 0.5))
        
        # 3. Executa predicoes de teste com o threshold mutado
        h_depois_list = []
        for _ in range(3):
            # Aplica mutacao no threshold
            thr.aprender(threshold_alvo, novo_valor)
            
            # Executa predicoes no MCR para medir impacto real
            if hasattr(self._mcr, 'mk_palavra') and self._mcr.mk_palavra.transicoes:
                mk = self._mcr.mk_palavra
                # Pega estados mais frequentes e faz predicoes
                estados = sorted(mk.freq.keys(), key=lambda e: -mk.freq[e])[:10]
                for estado in estados:
                    mk.predizer(estado)  # predizer altera cache de entropia
            h_depois_list.append(self.entropia_global())
        
        # 4. Mede entropia REAL depois
        h_depois = sum(h_depois_list) / len(h_depois_list) if h_depois_list else h_antes
        
        resultado = {
            'threshold': threshold_alvo,
            'mutacao_aplicada': round(novo_valor - valor_atual, 3),
            'valor_anterior': round(valor_atual, 3),
            'valor_novo': round(novo_valor, 3),
            'entropia_antes': round(h_antes, 4),
            'entropia_depois': round(h_depois, 4),
            'aceita': False,
        }
        
        # 5. Aceita se entropia reduziu (delta_h < -0.001 para evitar ruido)
        delta_h = h_depois - h_antes
        if delta_h < -0.001:
            resultado['aceita'] = True
            self._mutacoes_aceitas += 1
            # Mantem threshold mutado
            thr.aprender(threshold_alvo, novo_valor)
            print('[AutoEvol] ACEITA: %s %.3f -> %.3f (entropia: %.4f -> %.4f, delta=%.4f)' % (
                threshold_alvo, valor_atual, novo_valor, h_antes, h_depois, delta_h))
        else:
            # 6. Reverte mutacao
            thr.aprender(threshold_alvo, valor_atual)
            resultado['aceita'] = False
            self._mutacoes_rejeitadas += 1
            print('[AutoEvol] REJEITADA: %s %.3f -> %.3f (entropia: %.4f -> %.4f, delta=%.4f)' % (
                threshold_alvo, valor_atual, novo_valor, h_antes, h_depois, delta_h))
        
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
