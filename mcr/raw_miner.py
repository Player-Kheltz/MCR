#!/usr/bin/env python3
"""raw_miner.py — Mineracao sem tree-sitter (Fase C→G).

Implementa o atalho que permite ao sistema classificar entidades
sem invocar o parser, usando apenas similaridade Jaccard entre
tokens brutos e a entropia do cluster.

A decisao de pular o parser e feita pelo MCRDecisor via Ponte Otima,
sem thresholds fixos.
"""
import os, json, math
from pathlib import Path
from typing import Dict, List, Set, Optional
from collections import Counter

from devia.kernel.mcr_kernel.signature import raw_token_set, raw_token_set_from_file
from devia.kernel.mcr_kernel.decisor import MCRDecisor
from mcr.mcr_signature_cluster import SignatureCluster, SignatureAnalyzer, _jaccard, _assinatura_entidade


def computar_raw_fingerprints(clusters: List[SignatureCluster]):
    """Computa raw_fingerprint para todos os clusters.
    
    Deve ser chamado apos a clusterizacao inicial (tree-sitter).
    Varre os arquivos fonte de cada entidade e extrai raw_token_set.
    """
    for c in clusters:
        c.computar_raw_fingerprint()
        c.calcular_entropia()
    print(f'[RawMiner] Raw fingerprints computados para {len(clusters)} clusters')


def classificar_sem_parser(
    arquivo: str,
    clusters: List[SignatureCluster],
    decisor: Optional[MCRDecisor] = None,
) -> Dict:
    """Tenta classificar um arquivo sem usar tree-sitter.
    
    Fluxo:
    1. Extrai raw_token_set do arquivo (sem parser)
    2. Calcula similaridade Jaccard com cada cluster
    3. Pega o cluster com maior similaridade
    4. Se MCRDecisor decidir que e suficiente, classifica
    
    Args:
        arquivo: caminho do arquivo fonte
        clusters: lista de clusters existentes (com raw_fingerprint)
        decisor: MCRDecisor para decidir (cria um se None)
    
    Returns:
        dict com resultado da classificacao:
            'classificado': bool
            'cluster': SignatureCluster ou None
            'similaridade': float
            'entropia_cluster': float
            'decisao': str ('pular_parser' ou 'usar_parser')
            'raw_tokens': int (numero de tokens unicos extraidos)
    """
    if decisor is None:
        decisor = MCRDecisor('raw_miner')
    
    if not os.path.isfile(arquivo):
        return {'classificado': False, 'cluster': None, 'similaridade': 0, 'entropia_cluster': 0, 'decisao': 'arquivo_inexistente', 'raw_tokens': 0}
    
    # 1. Extrai tokens brutos
    tokens = raw_token_set_from_file(arquivo)
    if not tokens:
        return {'classificado': False, 'cluster': None, 'similaridade': 0, 'entropia_cluster': 0, 'decisao': 'sem_tokens', 'raw_tokens': 0}
    
    # 2. Encontra melhor cluster
    melhor_cluster = None
    melhor_similaridade = 0.0
    
    for c in clusters:
        sim = c.similaridade_raw(tokens)
        if sim > melhor_similaridade:
            melhor_similaridade = sim
            melhor_cluster = c
    
    if melhor_cluster is None:
        return {'classificado': False, 'cluster': None, 'similaridade': 0, 'entropia_cluster': 0, 'decisao': 'sem_cluster', 'raw_tokens': len(tokens)}
    
    entropia = melhor_cluster._entropia if hasattr(melhor_cluster, '_entropia') else melhor_cluster.calcular_entropia()
    
    # 4. Decide se pode pular parser
    decisao = decisor.decidir_pular_parser(entropia, melhor_similaridade)
    
    if decisao == 'pular_parser':
        return {
            'classificado': True,
            'cluster': melhor_cluster,
            'similaridade': round(melhor_similaridade, 4),
            'entropia_cluster': round(entropia, 4),
            'decisao': 'pular_parser',
            'raw_tokens': len(tokens),
        }
    
    return {
        'classificado': False,
        'cluster': melhor_cluster,
        'similaridade': round(melhor_similaridade, 4),
        'entropia_cluster': round(entropia, 4),
        'decisao': 'usar_parser',
        'raw_tokens': len(tokens),
    }


def gerar_entidade_de_cluster(arquivo: str, cluster: SignatureCluster) -> Dict:
    """Gera uma entidade a partir do prototipo do cluster.
    
    Quando o sistema pula o parser, ele nao tem acesso a AST.
    Em vez disso, cria uma entidade usando a assinatura media
    do cluster + o nome do arquivo.
    """
    nome_base = Path(arquivo).stem
    assinatura_media = cluster._assinatura_media
    
    # Gera api_calls a partir da assinatura media
    api_calls = list(assinatura_media)
    
    return {
        'arquivo': str(arquivo),
        'tipo': cluster.nome,
        'api_calls': api_calls,
        'raw_classificado': True,
        'cluster_origem': cluster.nome,
    }


def validar_pipeline(clusters: List[SignatureCluster], arquivos: List[str]) -> Dict:
    """Executa pipeline completo de validacao.
    
    Para cada arquivo, tenta classificar sem parser.
    Retorna metricas de desempenho.
    """
    decisor = MCRDecisor('raw_miner_val')
    
    total = len(arquivos)
    classificados_sem_parser = 0
    similaridades = []
    entropias = []
    
    for arq in arquivos:
        res = classificar_sem_parser(arq, clusters, decisor)
        if res['classificado']:
            classificados_sem_parser += 1
            similaridades.append(res['similaridade'])
            entropias.append(res['entropia_cluster'])
    
    return {
        'total_arquivos': total,
        'classificados_sem_parser': classificados_sem_parser,
        'percentual': round(classificados_sem_parser / max(total, 1) * 100, 1),
        'similaridade_media': round(sum(similaridades) / max(len(similaridades), 1), 4) if similaridades else 0,
        'entropia_media': round(sum(entropias) / max(len(entropias), 1), 4) if entropias else 0,
    }
