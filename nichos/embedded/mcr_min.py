#!/usr/bin/env python3
"""mcr_min.py — MCR minimal (~160 lines).

Nucleo do MCR extraido para uso embedded / microcontrolador.
Zero dependencias alem de stdlib Python.

Uso:
    mk = MCR("exemplo")
    mk.aprender("a", "b")
    mk.aprender("b", "c")
    print(mk.predizer("a"))  # ('b', 1.0)
    print(mk.gerar("a", 3))  # ['a', 'b', 'c']
"""

import math
from collections import Counter
from typing import Dict, List, Tuple, Optional


class MCR:
    """Markov chain — dicionario de transicoes.
    
    aprende(a, b): registra que a → b
    predizer(a):    retorna (b_mais_provavel, confianca)
    gerar(semente): gera sequencia a partir de semente
    """
    def __init__(self, nome=""):
        self.nome = nome
        self.transicoes: Dict[str, Dict[str, int]] = {}
        self.freq: Dict[str, int] = {}
        self.total = 0

    def aprender(self, a, b):
        a, b = str(a), str(b)
        if a not in self.transicoes:
            self.transicoes[a] = {}
            self.freq[a] = 0
        self.transicoes[a][b] = self.transicoes[a].get(b, 0) + 1
        self.freq[a] += 1
        self.total += 1

    def aprender_sequencia(self, seq):
        for i in range(len(seq)-1):
            self.aprender(seq[i], seq[i+1])

    def predizer(self, a) -> Tuple[Optional[str], float]:
        a = str(a)
        if a not in self.transicoes or not self.transicoes[a]:
            return (None, 0.0)
        m = max(self.transicoes[a], key=self.transicoes[a].get)
        return (m, self.transicoes[a][m] / self.freq[a])

    def predizer_n(self, a, n=3) -> List[Tuple[str, float]]:
        a = str(a)
        if a not in self.transicoes:
            return []
        ords = sorted(self.transicoes[a].items(), key=lambda x: -x[1])
        t = self.freq[a]
        return [(tok, cnt/t) for tok, cnt in ords[:n]]

    def gerar(self, semente, passos=0) -> List[str]:
        seq, at = [semente], semente
        for _ in range(passos):
            p, c = self.predizer(at)
            if p is None or c < 0.01:
                break
            seq.append(p)
            at = p
        return seq

    def entropia(self, a) -> float:
        a = str(a)
        if a not in self.transicoes or not self.transicoes[a]:
            return 1.0
        t = self.freq[a]
        return -sum((c/t)*math.log2(c/t) for c in self.transicoes[a].values())

    def entropia_media(self) -> float:
        if not self.freq:
            return 1.0
        return sum(self.entropia(e) for e in self.freq) / len(self.freq)

    def stats(self) -> Dict:
        n_trans = sum(len(t) for t in self.transicoes.values())
        return {'estados': len(self.freq), 'transicoes': n_trans, 'total': self.total}


class MCRByteUtils:
    """Utilitarios para fingerprint, entropia e similaridade."""

    @staticmethod
    def fingerprint(texto, dims=16) -> List[float]:
        """Fingerprint: histograma com hash-based binning.
        
        Cada byte incrementa o balde (posicao + valor_byte) % dims.
        Resultado normalizado entre 0 e 10.
        """
        dados = texto.encode('utf-8')[:500] if isinstance(texto, str) else bytes(texto)[:500]
        if not dados:
            return [0.0] * dims
        b = [0.0] * dims
        for i, by in enumerate(dados):
            b[(i + by) % dims] += 1.0
        t = sum(b) or 1
        return [round(v / t * 10, 3) for v in b]

    @staticmethod
    def similaridade_cosseno(a, b) -> float:
        if not a or not b:
            return 0.0
        d = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return d / (na * nb)

    @staticmethod
    def jaccard_bytes(ta, tb) -> float:
        def _t(s):
            d = s.encode('utf-8')[:500]
            return {f"{d[i]:02x}{d[i+1]:02x}" for i in range(len(d) - 1)}
        a, b = _t(ta), _t(tb)
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    @staticmethod
    def entropia_bytes(dados, mx=500) -> float:
        if isinstance(dados, str):
            dados = dados.encode('utf-8')[:mx]
        else:
            dados = bytes(dados)[:mx]
        if len(dados) < 2:
            return 0.0
        f = Counter(dados)
        n = len(dados)
        return -sum((c / n) * math.log2(c / n) for c in f.values())

    @staticmethod
    def delta_fingerprint(a, b, dim=8) -> List[float]:
        fa = MCRByteUtils.fingerprint(a, dim)
        fb = MCRByteUtils.fingerprint(b, dim)
        return [fb[i] - fa[i] for i in range(dim)]


if __name__ == '__main__':
    print(f"mcr_min.py — {__import__('inspect').currentframe().f_code.co_name}")
    print(f"  MCR: {len(dir(MCR))} metodos")
    print(f"  MCRByteUtils: {len(dir(MCRByteUtils))} metodos")
    
    # Teste rapido
    mk = MCR("teste")
    mk.aprender_sequencia("o rato roeu a roupa do rei de roma".split())
    print(f"  predizer('rato') = {mk.predizer('rato')}")
    print(f"  gerar('o', 5) = {mk.gerar('o', 5)}")
    print(f"  entropia_media = {mk.entropia_media():.3f}")
    print(f"  stats = {mk.stats()}")
    
    fp_a = MCRByteUtils.fingerprint("MCR e universal", 16)
    fp_b = MCRByteUtils.fingerprint("MCR e universal", 16)
    fp_c = MCRByteUtils.fingerprint("outra coisa", 16)
    print(f"  cos(mesmo) = {MCRByteUtils.similaridade_cosseno(fp_a, fp_b):.6f}")
    print(f"  cos(diferente) = {MCRByteUtils.similaridade_cosseno(fp_a, fp_c):.4f}")
    print(f"  OK — {sum(1 for _ in open(__file__))} linhas")
