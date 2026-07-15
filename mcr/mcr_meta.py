#!/usr/bin/env python3
"""mcr.mcr_meta — Auto-Evolucao do Conhecimento.
Equacao PONTE_OTIMA, loop auto_melhoria, e MCRPesoNota (descobre pesos otimos)."""
import json
import time
import math
import random
from pathlib import Path
from typing import Dict, List, Optional

from mcr.paths import KG_DIR


class MCRPesoNota:
    """Descobre os pesos otimos da Equacao MCR testando combinacoes.
    
    Testa 5 combinacoes de pesos (byte, palavra, token) e escolhe
    a que maximiza a separacao entre topicos no Knowledge Graph.
    """

    COMBINACOES = [
        (1, 3, 1),
        (2, 5, 3),
        (3, 4, 3),
        (1, 4, 2),
        (2, 3, 2),
    ]

    def __init__(self):
        self.historico: List[Dict] = []
        self._melhor_combinacao = (2, 5, 3)
        self._melhor_nota = 0.0

    def testar(self, kg_dir: Optional[Path] = None) -> Dict:
        """Testa as 5 combinacoes de pesos e retorna a melhor.
        
        Returns:
            dict com 'combinacoes_testadas', 'melhor_combinacao', 'melhor_nota'
        """
        kg_dir = kg_dir or KG_DIR

        # Carrega padroes do KG
        padroes = []
        for fpath in sorted(kg_dir.glob('patterns_*.json')):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                padroes.extend(dados.get('padroes', dados if isinstance(dados, list) else []))
            except Exception:
                continue

        if not padroes:
            return {'erro': 'KG vazio', 'combinacoes_testadas': []}

        resultados = []
        melhor_nota = 0.0
        melhor_comb = self.COMBINACOES[0]

        for peso_byte, peso_palavra, peso_token in self.COMBINACOES:
            notas = []
            for p in padroes[:200]:  # Amostra de 200 para velocidade
                api_calls = p.get('api_calls', [])
                variaveis = p.get('variaveis', [])

                # Byte: diversidade de API calls
                byte = len(set(api_calls)) / max(len(api_calls), 1) if api_calls else 0.3
                # Palavra: especificidade de variaveis
                palavra = len(set(variaveis)) / max(len(variaveis), 1) if variaveis else 0.3
                # Token: profundidade normalizada
                token = min(1.0, p.get('tamanho_linhas', 50) / 200.0)

                nota = (peso_byte * byte + peso_palavra * palavra + peso_token * token) / (peso_byte + peso_palavra + peso_token)
                notas.append(nota * 10)

            if notas:
                nota_media = sum(notas) / len(notas)
                # Maximiza separacao = variancia alta + media alta
                variancia = sum((n - nota_media) ** 2 for n in notas) / len(notas)
                score = nota_media * 0.6 + math.sqrt(variancia) * 0.4

                print('[MCRPesoNota] (%d,%d,%d): nota=%.2f var=%.2f score=%.2f' % (
                    peso_byte, peso_palavra, peso_token, nota_media, variancia, score))

                resultados.append({
                    'pesos': (peso_byte, peso_palavra, peso_token),
                    'nota_media': round(nota_media, 2),
                    'variancia': round(variancia, 2),
                    'score': round(score, 2),
                })

                if score > melhor_nota:
                    melhor_nota = score
                    melhor_comb = (peso_byte, peso_palavra, peso_token)

        self._melhor_combinacao = melhor_comb
        self._melhor_nota = melhor_nota
        self.historico.append({'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                               'melhor': melhor_comb, 'nota': melhor_nota})

        return {
            'combinacoes_testadas': resultados,
            'melhor_combinacao': melhor_comb,
            'melhor_nota': round(melhor_nota, 2),
        }

    def get_melhores_pesos(self) -> tuple:
        return self._melhor_combinacao


class MCRMeta:
    """Auto-avaliacao do Knowledge Graph.
    
    Equacao PONTE_OTIMA = (5*DIVERGENCIA + 3*ESPECIFICIDADE + 2*PROFUNDIDADE) / 10
    """

    @staticmethod
    def _calcular_ponte_otima(api_calls: list, variaveis: list, tamanho_linhas: int = 50) -> float:
        """Calcula PONTE_OTIMA para um unico padrao.
        
        Retorna score 0-10 onde:
        10 = maxima divergencia (muitas APIs diferentes)
              + maxima especificidade (muitas variaveis)
              + maxima profundidade (arquivo grande)
        """
        divergencia = len(set(api_calls)) / max(len(api_calls), 1) if api_calls else 0.0
        especificidade = len(set(variaveis)) / max(len(variaveis), 1) if variaveis else 0.3
        profundidade = min(1.0, tamanho_linhas / 200.0)
        nota = (5.0 * divergencia + 3.0 * especificidade + 2.0 * profundidade) / 10.0
        return round(min(10.0, nota * 10.0), 2)

    @staticmethod
    def diagnosticar(kg_dir: Optional[Path] = None) -> Dict:
        kg_dir = kg_dir or KG_DIR
        padroes = []
        for fpath in sorted(kg_dir.glob('patterns_*.json')):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                padroes.extend(dados.get('padroes', dados if isinstance(dados, list) else []))
            except Exception:
                continue

        if not padroes:
            return {'nota_geral': 0.0, 'gap_principal': 'KG vazio',
                    'conexoes_boas': 0, 'conexoes_fracas': 0, 'topicos': {}}

        topicos = {}
        for p in padroes:
            tipo = p.get('tipo', 'generic')
            api_calls = p.get('api_calls', [])
            variaveis = p.get('variaveis', [])
            arquivo = Path(p.get('arquivo', '')).stem

            # Calcula componentes individualmente
            div = len(set(api_calls)) / max(len(api_calls), 1) if api_calls else 0.0
            espec = len(set(variaveis)) / max(len(variaveis), 1) if variaveis else 0.3
            prof = min(1.0, p.get('tamanho_linhas', 50) / 200.0)
            nota = MCRMeta._calcular_ponte_otima(
                api_calls, variaveis, p.get('tamanho_linhas', 50))

            topicos[arquivo] = {
                'arquivo': p.get('arquivo', ''),
                'tipo': tipo,
                'divergencia': round(div, 3),
                'especificidade': round(espec, 3),
                'profundidade': round(prof, 3),
                'nota': nota,
                'api_calls': api_calls[:5],
            }

        notas = [t['nota'] for t in topicos.values()]
        nota_geral = round(sum(notas) / len(notas), 2) if notas else 0.0
        gap_principal = min(topicos, key=lambda k: topicos[k]['nota']) if topicos else '(nenhum)'
        conexoes_boas = sum(1 for t in topicos.values() if t['nota'] >= 7.0)
        conexoes_fracas = sum(1 for t in topicos.values() if t['nota'] < 5.0)

        return {
            'nota_geral': nota_geral,
            'gap_principal': gap_principal,
            'conexoes_boas': conexoes_boas,
            'conexoes_fracas': conexoes_fracas,
            'topicos': topicos,
            'total_topicos': len(topicos),
        }

    @staticmethod
    def auto_melhoria(kg_dir: Optional[Path] = None, max_iter: int = 5) -> List[Dict]:
        kg_dir = kg_dir or KG_DIR
        historico = []
        for ciclo in range(max_iter):
            diag = MCRMeta.diagnosticar(kg_dir)
            nota_atual = diag['nota_geral']
            gap = diag['gap_principal']
            entrada = {
                'ciclo': ciclo, 'nota': nota_atual, 'gap': gap,
                'conexoes_boas': diag['conexoes_boas'],
                'conexoes_fracas': diag['conexoes_fracas'],
            }
            historico.append(entrada)
            print('[MCRMeta] Ciclo %d: nota=%.2f gap=%s boas=%d fracas=%d' % (
                ciclo, nota_atual, gap, diag['conexoes_boas'], diag['conexoes_fracas']))
            if nota_atual >= 9.0 and diag['conexoes_fracas'] == 0:
                print('[MCRMeta] Convergencia atingida!')
                break
            if gap != '(nenhum)' and gap != 'KG vazio' and diag['topicos'].get(gap):
                topico_info = diag['topicos'][gap]
                print('[MCRMeta] Gap "%s": diverg=%.2f espec=%.2f prof=%.2f nota=%.2f' % (
                    gap, topico_info['divergencia'], topico_info['especificidade'],
                    topico_info['profundidade'], topico_info['nota']))
            if diag['conexoes_fracas'] == 0:
                break
        return historico

    @staticmethod
    def estatisticas(kg_dir: Optional[Path] = None) -> Dict:
        diag = MCRMeta.diagnosticar(kg_dir)
        return {
            'nota_geral': diag['nota_geral'],
            'total_topicos': diag['total_topicos'],
            'conexoes_boas': diag['conexoes_boas'],
            'conexoes_fracas': diag['conexoes_fracas'],
            'gap_principal': diag['gap_principal'],
        }
