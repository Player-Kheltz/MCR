"""
HDC+SDM Memory para Knowledge Graph.
Converte entidades do KG em HD vectors para recuperacao semantica.
Zero dependencias externas — apenas hdc_core e sdm_core.
"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'devia', 'kernel'))
from hdc_core import HDVector, HDCVocab
from sdm_core import SDM


class HDCKGMemory:
    def __init__(self, n_enderecos: int = 1000, raio: float = 0.05):
        self.sdm = SDM(n_enderecos=n_enderecos, raio=raio)
        self.vocab = HDCVocab()
        self.entidades: dict = {}
        self.n_armazenados_sdm = 0

    def _string_to_hdv(self, texto: str) -> HDVector:
        return self.vocab.get(texto)

    def _dados_to_hdv(self, dados: dict) -> HDVector:
        vetores = []
        for chave, valor in dados.items():
            if isinstance(valor, (str, int, float)):
                vetores.append(self.vocab.get(f'{chave}:{valor}'))
        if not vetores:
            return HDVector()
        return HDVector.bundle(*vetores)

    def store_entity(self, nome: str, dados: dict):
        vec = self._string_to_hdv(nome)
        dados_vec = self._dados_to_hdv(dados)
        combinado = HDVector.bundle(vec, dados_vec)

        self.sdm.store(combinado)
        self.entidades[nome] = combinado
        self.n_armazenados_sdm += 1

    def query_similar(self, consulta: str, top_k: int = 5) -> list:
        vec_consulta = self._string_to_hdv(consulta)
        similares = []
        for nome, ent_vec in self.entidades.items():
            sim = HDVector.cosine(vec_consulta, ent_vec)
            if sim > 0.0:
                similares.append((nome, sim))
        similares.sort(key=lambda x: x[1], reverse=True)
        return similares[:top_k]

    def query_similar_por_texto(self, texto: str, top_k: int = 5) -> list:
        palavras = texto.split()
        if not palavras:
            return []
        vec = self._string_to_hdv(palavras[0])
        for p in palavras[1:]:
            vec = HDVector.bundle(vec, self._string_to_hdv(p))
        similares = []
        for nome, ent_vec in self.entidades.items():
            sim = HDVector.cosine(vec, ent_vec)
            if sim > 0.0:
                similares.append((nome, sim))
        similares.sort(key=lambda x: x[1], reverse=True)
        return similares[:top_k]

    def store_interaction(self, pergunta: str, resposta: str,
                          metadados: dict = None):
        vetores = [
            self._string_to_hdv(pergunta[:200]),
            self._string_to_hdv(resposta[:500]),
        ]
        if metadados:
            chave_valor = '_'.join(f'{k}:{v}' for k, v in metadados.items()
                                   if isinstance(v, (str, int, float)))
            if chave_valor:
                vetores.append(self._string_to_hdv(chave_valor[:200]))
        vec = HDVector.bundle(*vetores)

        self.sdm.store(vec)
        if not hasattr(self, 'interacoes'):
            self.interacoes = []
        self.interacoes.append({
            'pergunta': pergunta[:100],
            'resposta': resposta[:100],
            'vec': vec,
        })

    def query_similar_interactions(self, consulta: str,
                                   top_k: int = 3) -> list:
        if not hasattr(self, 'interacoes') or not self.interacoes:
            return []
        vec_consulta = self._string_to_hdv(consulta)
        similares = []
        for inter in self.interacoes:
            sim = HDVector.cosine(vec_consulta, inter['vec'])
            similares.append((inter['pergunta'], inter['resposta'], sim))
        similares.sort(key=lambda x: x[2], reverse=True)
        return similares[:top_k]

    def stats(self) -> dict:
        return {
            'entidades': len(self.entidades),
            'sdm_enderecos_memoria': self.sdm.n_enderecos,
            'sdm_armazenados': self.n_armazenados_sdm,
            'interacoes': len(getattr(self, 'interacoes', [])),
        }
