#!/usr/bin/env python3
"""mcr.mcr_signature_cluster — Agrupa padroes do KG por assinatura de API.
Descobre automaticamente "tipos" de entidades sem usar rotulos humanos.
Cada cluster e uma "especie" no ecossistema MCR."""
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

from mcr.paths import KG_DIR


def _normalizar_api(nome: str) -> str:
    """Normaliza nome de API: remove argumentos, lowercase."""
    return nome.split('(')[0].strip().lower()


def _jaccard(a: set, b: set) -> float:
    inter = a & b
    uniao = a | b
    return len(inter) / len(uniao) if uniao else 0.0


def _assinatura_entidade(p: dict) -> Set[str]:
    """Gera assinatura de API de uma entidade do KG."""
    apis = set()
    for api in p.get('api_calls', []):
        nome = _normalizar_api(api)
        if nome:
            apis.add(nome)
    for var in p.get('variaveis', []):
        apis.add('var:' + var.lower())
    return apis


def _entropia(distribuicao: Counter) -> float:
    total = sum(distribuicao.values()) or 1
    h = 0.0
    for count in distribuicao.values():
        p = count / total
        if p > 0:
            h -= p * math.log2(p)
    return h


class SignatureCluster:
    """Cluster de entidades com assinaturas de API similares.
    
    Cada cluster representa um "tipo" abstrato (o que humanos chamariam
    de NPC, Monster, Quest, etc.) descoberto automaticamente.
    """

    def __init__(self, nome: str, entidades: list = None):
        self.nome = nome
        self.entidades: List[Dict] = entidades or []
        self._assinatura_media: Set[str] = set()
        self._raw_fingerprint: Set[str] = set()  # tokens brutos sem parser
        self._entropia: float = 0.0  # entropia do cluster
        self._calcular_assinatura_media()

    def _calcular_assinatura_media(self):
        """Assinatura media = uniao de todas as assinaturas do cluster."""
        for e in self.entidades:
            self._assinatura_media |= _assinatura_entidade(e)

    def adicionar(self, entidade: dict):
        self.entidades.append(entidade)
        self._assinatura_media |= _assinatura_entidade(entidade)

    def computar_raw_fingerprint(self):
        """Computa raw_fingerprint do cluster a partir dos arquivos fonte.
        
        Varre todas as entidades, le o arquivo original e extrai
        raw_token_set usando apenas delimitadores universais (sem parser).
        """
        from devia.kernel.mcr_kernel.signature import raw_token_set_from_file
        for ent in self.entidades:
            arq = ent.get('arquivo', '')
            if arq:
                self._raw_fingerprint |= raw_token_set_from_file(arq)

    def similaridade_raw(self, tokens: set) -> float:
        """Jaccard entre tokens brutos e o raw_fingerprint do cluster."""
        if not self._raw_fingerprint or not tokens:
            return 0.0
        return _jaccard(tokens, self._raw_fingerprint)

    def calcular_entropia(self) -> float:
        """Entropia de Shannon do cluster baseada na distribuicao de tipos."""
        tipos = Counter()
        for e in self.entidades:
            tipos[e.get('tipo', 'unknown')] += 1
        self._entropia = _entropia(tipos)
        return self._entropia

    def similaridade(self, entidade: dict) -> float:
        """Jaccard entre a assinatura da entidade e a assinatura media do cluster."""
        ass_e = _assinatura_entidade(entidade)
        return _jaccard(ass_e, self._assinatura_media)

    def get_assinaturas_caracteristicas(self, top_n: int = 10) -> List[str]:
        """Retorna as APIs mais frequentes no cluster."""
        todas = []
        for e in self.entidades:
            for api in e.get('api_calls', []):
                todas.append(_normalizar_api(api))
        return [api for api, _ in Counter(todas).most_common(top_n)]

    def get_nome_legivel(self) -> str:
        """Gera nome legivel baseado nas APIs mais frequentes.
        Ex: 'Type_A (Game.createNpcType, KeywordHandler)' = NPC tradicional."""
        tops = self.get_assinaturas_caracteristicas(3)
        return "%s (%s)" % (self.nome, ', '.join(tops))

    def __len__(self) -> int:
        return len(self.entidades)

    def __repr__(self) -> str:
        return "<Cluster %s: %d entidades>" % (self.nome, len(self.entidades))


class SignatureAnalyzer:
    """Analisa o KG e descobre clusters de entidades por similaridade de API.
    
    Uso:
        analyzer = SignatureAnalyzer()
        clusters = analyzer.clusterizar()
        for c in clusters:
            print(c.get_nome_legivel())
    """

    def __init__(self, kg_dir: Path = None):
        self.kg_dir = kg_dir or KG_DIR
        self.padroes: List[Dict] = []
        self.clusters: List[SignatureCluster] = []
        self._carregar_kg()

    def _carregar_kg(self):
        for fpath in sorted(self.kg_dir.glob('patterns_*.json')):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                items = dados.get('padroes', dados if isinstance(dados, list) else [])
                self.padroes.extend(items)
            except Exception:
                continue

    def clusterizar(self, threshold: float = 0.30) -> List[SignatureCluster]:
        """Agrupa entidades por similaridade de assinatura.
        
        Algoritmo:
        1. Para cada entidade, calcular assinatura
        2. Agrupar por similaridade Jaccard > threshold
        3. Clusters sao nomeados Type_A, Type_B, etc.
        
        Returns:
            lista de SignatureCluster
        """
        if not self.padroes:
            return []

        # Filtra entidades que tem pelo menos 1 API call
        entidades_validas = [p for p in self.padroes if p.get('api_calls')]

        # Algoritmo guloso: para cada entidade, encontra o melhor cluster
        self.clusters = []
        for ent in entidades_validas:
            melhor_cluster = None
            melhor_score = 0.0

            for cluster in self.clusters:
                score = cluster.similaridade(ent)
                if score > melhor_score:
                    melhor_score = score
                    melhor_cluster = cluster

            if melhor_cluster and melhor_score >= threshold:
                melhor_cluster.adicionar(ent)
            else:
                nome = "Type_%c" % (65 + len(self.clusters))  # A, B, C...
                novo = SignatureCluster(nome, [ent])
                self.clusters.append(novo)

        # Ordena por tamanho decrescente
        self.clusters.sort(key=lambda c: -len(c))

        print('[SignatureAnalyzer] %d clusters de %d entidades (threshold=%.2f):' % (
            len(self.clusters), len(entidades_validas), threshold))
        for c in self.clusters:
            print('  %s: %d entidades | %s' % (c.nome, len(c), c.get_nome_legivel()))

        return self.clusters

    def classificar(self, assinatura: Set[str]) -> Tuple[str, float]:
        """Classifica uma assinatura desconhecida em um cluster existente.
        
        Args:
            assinatura: conjunto de APIs normalizadas
        
        Returns:
            (nome_do_cluster, confianca)
        """
        if not self.clusters:
            return ('desconhecido', 0.0)

        melhor_cluster = None
        melhor_score = 0.0

        # Cria uma entidade fake para comparar
        ent_fake = {'api_calls': list(assinatura), 'variaveis': []}

        for cluster in self.clusters:
            score = cluster.similaridade(ent_fake)
            if score > melhor_score:
                melhor_score = score
                melhor_cluster = cluster

        if melhor_cluster and melhor_score > 0.15:
            return (melhor_cluster.nome, melhor_score)
        return ('novo', 0.0)

    def entropia_entre_clusters(self) -> float:
        """Entropia de Shannon da distribuicao de entidades entre clusters.
        Baixa = dominado por 1 cluster. Alta = distribuicao uniforme."""
        if not self.clusters:
            return 0.0
        distribuicao = Counter()
        for c in self.clusters:
            distribuicao[c.nome] = len(c)
        return _entropia(distribuicao)

    def meta_clusterizar(self, threshold: float = 0.05) -> List['MetaCluster']:
        """Agrupa clusters similares em meta-clusters (2o nivel hierarquico).
        
        Cada meta-cluster e um grupo de clusters cujos centroides
        (fingerprints das APIs caracteristicas) sao similares.
        Isso resolve a fragmentacao: NPCs em varios clusters pequenos
        sao agrupados em um unico meta-cluster "Tipo NPC".
        
        Returns:
            lista de MetaCluster
        """
        from mcr.equacao_mcr import _EQUACAO_ATUAL
        if len(self.clusters) < 2:
            return [MetaCluster("Unico", self.clusters)]

        # Gera fingerprint de cada cluster (8D das APIs caracteristicas)
        fingerprints = {}
        for c in self.clusters:
            api_text = ' '.join(c.get_assinaturas_caracteristicas(15))
            fp = self._fingerprint_8d(api_text)
            fingerprints[c.nome] = fp

        # Algoritmo guloso: agrupa clusters com fingerprint similar
        meta_clusters = []
        usados = set()

        for c in sorted(self.clusters, key=lambda x: -len(x)):
            if c.nome in usados:
                continue
            mc = MetaCluster(c.nome + "_group", [c])
            usados.add(c.nome)

            # APIs discriminantes do cluster central
            apis_centrais = set(c.get_assinaturas_caracteristicas(8))
            tem_monster = 'game.createmonstertype' in apis_centrais
            tem_npc = 'game.createnpctype' in apis_centrais

            for c2 in self.clusters:
                if c2.nome in usados:
                    continue
                apis_c2 = set(c2.get_assinaturas_caracteristicas(8))
                # Se o central tem MonsterType e o candidato tem NpcType, nao agrupa
                if tem_monster and 'game.createnpctype' in apis_c2:
                    continue
                if tem_npc and 'game.createmonstertype' in apis_c2:
                    continue
                sim = _jaccard(apis_centrais, apis_c2)
                fp_sim = _cosseno(fingerprints[c.nome], fingerprints[c2.nome])
                if sim > 0.05 or fp_sim > 0.80:
                    mc.adicionar(c2)
                    usados.add(c2.nome)

            meta_clusters.append(mc)

        # Ordena por tamanho
        meta_clusters.sort(key=lambda mc: -mc.total_entidades())

        print('\n[MetaCluster] %d meta-clusters de %d clusters:' % (
            len(meta_clusters), len(self.clusters)))
        for mc in meta_clusters:
            print('  %s: %d entidades, %d sub-clusters' % (
                mc.nome, mc.total_entidades(), len(mc.clusters)))

        return meta_clusters

    @staticmethod
    def _fingerprint_8d(texto: str) -> list:
        """Fingerprint 8D (a-z, A-Z, 0-9, space, punct, special, high, other)."""
        dados = texto.encode('utf-8')
        if not dados:
            return [0.0] * 8
        buckets = [0.0] * 8
        for b in dados:
            if 97 <= b <= 122:
                buckets[0] += 1
            elif 65 <= b <= 90:
                buckets[1] += 1
            elif 48 <= b <= 57:
                buckets[2] += 1
            elif b == 32:
                buckets[3] += 1
            elif b in (33, 44, 46, 58, 59, 63, 40, 41, 45, 95):
                buckets[4] += 1
            elif b < 65:
                buckets[5] += 1
            elif b > 122:
                buckets[6] += 1
            else:
                buckets[7] += 1
        total = sum(buckets) or 1
        return [round(b / total * 10, 3) for b in buckets]


def _cosseno(a: list, b: list) -> float:
    """Similaridade cosseno entre dois vetores."""
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na * nb else 0.0


class MetaCluster:
    """Grupo de clusters similares (2o nivel hierarquico).
    
    Ex: Type_O + Type_P + Type_G = MetaCluster "NPC" (sem rotulo humano).
    """

    def __init__(self, nome: str, clusters: list = None):
        self.nome = nome
        self.clusters: List[SignatureCluster] = clusters or []

    def adicionar(self, cluster: SignatureCluster):
        self.clusters.append(cluster)

    def total_entidades(self) -> int:
        return sum(len(c) for c in self.clusters)

    def get_nomes_clusters(self) -> List[str]:
        return [c.nome for c in self.clusters]

    def get_api_caracteristica(self) -> str:
        """Junta as APIs de todos os sub-clusters."""
        todas = []
        for c in self.clusters:
            todas.extend(c.get_assinaturas_caracteristicas(5))
        return ', '.join(sorted(set(todas))[:8])

    def __repr__(self) -> str:
        return "<MetaCluster %s: %d clusters, %d entidades>" % (
            self.nome, len(self.clusters), self.total_entidades())


if __name__ == '__main__':
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    print('=' * 55)
    print('  SignatureAnalyzer — Descoberta de Tipos')
    print('=' * 55)
    analyzer = SignatureAnalyzer()
    clusters = analyzer.clusterizar(threshold=0.15)

    print('\nEntropia entre clusters: %.3f' % analyzer.entropia_entre_clusters())

    print('\n--- Meta-Clusters ---')
    meta = analyzer.meta_clusterizar()
    for mc in sorted(meta, key=lambda x: -x.total_entidades()):
        print('  %s: %d entidades, %d sub-clusters' % (
            mc.nome, mc.total_entidades(), len(mc.clusters)))
        if len(mc.clusters) > 1:
            print('    Sub-clusters: %s' % ', '.join(mc.get_nomes_clusters()))
        print('    APIs: %s' % mc.get_api_caracteristica())

    print('\nClassificando "Game.createNpcType, KeywordHandler:new, npcType:register"...')
    tipo, conf = analyzer.classificar({'game.createtype', 'keywordhandler:new', 'npctype:register'})
    print('  -> %s (conf=%.2f)' % (tipo, conf))
