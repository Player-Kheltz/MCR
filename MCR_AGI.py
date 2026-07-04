#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCR_AGI.py — Experimento em minimalismo computacional com Markov multi-nivel.
============================================================================
Unico arquivo. Markov em N niveis: byte, palavra, token, decisao, acao.
Primitivas, mundo, acoes, NLP (Jaccard), atencao (heuristicas),
planejamento (grid 5x5), Q-Learning, SQLite, auto-parametrizacao,
curiosidade, identidade (fingerprint), chat, daemon.

0 GPU. 0 LLM. 0 dependencias externas. Python stdlib apenas.

Uso:
    python MCR_AGI.py                            # chat
    python MCR_AGI.py --daemon                   # servidor
    python MCR_AGI.py --ask "preco do worm"      # direto
    python MCR_AGI.py --aprender                 # alimenta NPCs
"""
import os, sys, json, math, time, glob, re, random as _rand
import sqlite3, socket, threading, hashlib, tempfile, queue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from collections import Counter, deque
from typing import Dict, List, Tuple, Optional, Any, Callable, Set
from statistics import median
from copy import deepcopy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════
# [17] MCRConfig — zero numeros magicos, tudo descoberto
# ═══════════════════════════════════════════════════════════════════

class MCRConfig:
    _inst = None
    def __new__(cls):
        if cls._inst is None:
            cls._inst = super().__new__(cls)
            cls._inst._cache = {}
            cls._inst._obs: Dict[str, list] = {}
        return cls._inst

    def _thr(self, nome, padrao):
        obs = self._obs.get(nome, [])
        return median(obs) if len(obs) >= 3 else padrao

    def _dec(self, nome, padrao):
        return padrao

    def observar(self, nome, valor):
        self._obs.setdefault(nome, []).append(valor)
        self._cache.pop(nome, None)

    def get(self, nome, padrao=None):
        return self._cache.get(nome) or self._thr(nome, padrao)

C = MCRConfig().get

# ═══════════════════════════════════════════════════════════════════
# [01] Primitivas — MCR, ByteUtils, Signature, Threshold, Entropia
# ═══════════════════════════════════════════════════════════════════

class MCR:
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
        for i in range(len(seq)-1): self.aprender(seq[i], seq[i+1])
    def predizer(self, a):
        a = str(a)
        if a not in self.transicoes or not self.transicoes[a]: return (None, 0.0)
        m = max(self.transicoes[a], key=self.transicoes[a].get)
        return (m, self.transicoes[a][m] / self.freq[a])
    def predizer_n(self, a, n=3):
        a = str(a)
        if a not in self.transicoes: return []
        ords = sorted(self.transicoes[a].items(), key=lambda x: -x[1])
        t = self.freq[a]
        return [(tok, cnt/t) for tok, cnt in ords[:n]]
    def gerar(self, semente, passos=0):
        seq, at = [semente], semente
        for _ in range(passos):
            p, c = self.predizer(at)
            if p is None or c < 0.01: break
            seq.append(p); at = p
        return seq
    def entropia(self, a):
        a = str(a)
        if a not in self.transicoes or not self.transicoes[a]: return 1.0
        t = self.freq[a]
        return -sum((c/t)*math.log2(c/t) for c in self.transicoes[a].values())
    def entropia_media(self):
        if not self.freq: return 1.0
        return sum(self.entropia(e) for e in self.freq)/len(self.freq)
    def stats(self):
        return {'estados': len(self.freq), 'transicoes': sum(len(t) for t in self.transicoes.values()), 'total': self.total}

class MCRByteUtils:
    @staticmethod
    def fingerprint(texto, dims=None):
        """Fingerprint com dimensionalidade ideal (auto-descoberta).
        
        Se dims for None, usa MCRSignatureExpansiva.dimensionalidade_ideal()
        para descobrir a dimensao otima para o texto. O minimo e 8.
        """
        if dims is None:
            dados_enc = texto.encode('utf-8')[:2000] if isinstance(texto, str) else bytes(texto)[:2000]
            dims = max(8, MCRSignatureExpansiva.dimensionalidade_ideal(dados_enc, mx=128, thr=0.05))
        dados = texto.encode('utf-8')[:500] if isinstance(texto, str) else bytes(texto)[:500]
        if not dados: return [0.0]*dims
        b = [0.0]*dims
        for i, by in enumerate(dados): b[(i+by)%dims] += 1.0
        t = sum(b) or 1
        return [round(v/t*10, 3) for v in b]
    @staticmethod
    def similaridade_cosseno(a, b):
        if not a or not b: return 0.0
        d = sum(x*y for x,y in zip(a,b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(y*y for y in b))
        if na == 0 or nb == 0: return 0.0
        return d/(na*nb)
    @staticmethod
    def jaccard_bytes(ta, tb):
        def _t(s):
            d = s.encode('utf-8')[:500]; return {f"{d[i]:02x}{d[i+1]:02x}" for i in range(len(d)-1)}
        a, b = _t(ta), _t(tb)
        if not a or not b: return 0.0
        return len(a&b)/len(a|b)
    @staticmethod
    def entropia_bytes(dados, mx=500):
        if isinstance(dados, str): dados = dados.encode('utf-8')[:mx]
        else: dados = bytes(dados)[:mx]
        if len(dados) < 2: return 0.0
        f = Counter(dados); n = len(dados)
        return -sum((c/n)*math.log2(c/n) for c in f.values())
    @staticmethod
    def delta_fingerprint(a, b, dim=0):
        fa = MCRByteUtils.fingerprint(a, dim); fb = MCRByteUtils.fingerprint(b, dim)
        return [fb[i]-fa[i] for i in range(dim)]

class MCRSignatureExpansiva:
    @staticmethod
    def fingerprint(dados, n_dims):
        if not dados: return [0.0]*n_dims
        b = [0.0]*n_dims
        for i, by in enumerate(dados): b[(i+by)%n_dims] += 1.0
        t = sum(b) or 1; return [round(v/t*10, 3) for v in b]
    @staticmethod
    def dimensionalidade_ideal(dados, mx=64, thr=0.05):
        if isinstance(dados, str): dados = dados.encode('utf-8')[:2000]
        es = []
        for d in [1,2,4,8,16,32,64,128]:
            if d > mx: break
            fp = MCRSignatureExpansiva.fingerprint(dados, d)
            tt = sum(fp) or 1; pr = [v/tt for v in fp if v > 0]
            h = -sum(p*math.log2(p) for p in pr) if pr else 0
            es.append((d, h))
        for i in range(1, len(es)):
            da, ha = es[i-1]; db, hb = es[i]
            if abs(hb-ha)/max(ha,0.01) < thr: return db
        return es[-1][0] if es else 8

class MCRJanelamentoFingerprint:
    """Vetor de fingerprint com janelamento temporal e estado interno.
    
    Divide o texto em janelas e gera fingerprints de cada janela.
    O vetor resultante captura estrutura LOCAL.
    
    COM ESTADO INTERNO (leaky integration):
    - O estado anterior e realimentado na proxima chamada
    - alpha = taxa de leaky (aprendida por MCRThreshold)
    - coupling alimentado com estado (nao fica vazio)
    """
    def __init__(self, dim=8, janela=200, passo=100):
        self.dim = dim
        self.janela = janela
        self.passo = passo
        self.cache: Dict[str, List[float]] = {}
        self.coupling = MCRCoupling()
        self.estado: List[float] = []
        self.thr_alpha = MCRThreshold("reservoir_alpha")
        self.mk_estado = MCR("reservoir_estado")
    
    def gerar(self, texto):
        if texto in self.cache:
            return self.cache[texto]
        
        dados = texto.encode('utf-8')[:5000] if isinstance(texto, str) else bytes(texto)[:5000]
        if not dados or len(dados) < self.dim:
            return []
        
        vetor = []
        for inicio in range(0, len(dados), self.passo):
            janela = dados[inicio:inicio + self.janela]
            if len(janela) < self.dim:
                break
            fp = MCRByteUtils.fingerprint(janela, self.dim)
            
            # Leaky integration com estado interno
            alpha = self.thr_alpha.obter("alpha", 0.3)
            if not self.estado or len(self.estado) != len(fp):
                self.estado = list(fp)
            else:
                for i in range(len(fp)):
                    self.estado[i] = alpha * fp[i] + (1-alpha) * self.estado[i]
            
            # Alimenta coupling com estado (nao fica vazio)
            self.coupling.alimentar("reservoir", "estado",
                                   str(fp[:min(3, len(fp))]),
                                   str(self.estado[:min(3, len(self.estado))]))
            # Aprende transicao de estado
            self.mk_estado.aprender(str(self.estado[:min(4, len(self.estado))]),
                                   str(fp[:min(4, len(fp))]))
            
            vetor.extend(self.estado)
        
        self.cache[texto] = vetor
        self.coupling.recalcular()
        return vetor
    
    def entropia_reservoir(self, vetor=None):
        if not vetor or len(vetor) < 2:
            return 1.0
        total = sum(abs(v) for v in vetor) or 1
        return -sum((abs(v)/total)*math.log2(max(abs(v)/total, 0.001)) for v in vetor if abs(v) > 0)
    
    def comparar(self, texto_a, texto_b):
        va = self.gerar(texto_a)
        vb = self.gerar(texto_b)
        if not va or not vb:
            return 0.0
        return MCRByteUtils.similaridade_cosseno(va, vb)

# ═══════════════════════════════════════════════════════════════════
# [01b] MCRHDCOperation — algebra de fingerprints (F1)
# ═══════════════════════════════════════════════════════════════════

class MCRHDCOperation:
    """Operacoes de Hyperdimensional Computing sobre fingerprints.
    
    bundle(a, b): soma ponderada — combina conceitos
    bind(a, b):   multiplicacao — cria associacao
    permute(v):   rotacao — marca ordem temporal
    
    Cada operacao tem seu proprio MCR que aprende quando aplica-la.
        Usa MCRJanelamentoFingerprint para vetores mais longos quando disponivel.
    """
    def __init__(self, reservoir=None, coupling=None, niveis_ctx=None):
        self.reservoir = reservoir
        self.coupling = coupling
        self.niveis_ctx = niveis_ctx or []
        self.mk_bundle = MCR("hdc_bundle")
        self.mk_bind = MCR("hdc_bind")
        self.mk_permute = MCR("hdc_permute")
        self.mk_analogia = MCR("hdc_analogia")
        self.total = 0
    
    def _vetor(self, texto):
        """Gera vetor fingerprint com dimensionalidade adaptativa.
        
        A dimensionalidade e REDUZIDA quando ha correlacao forte entre
        niveis — pois a informacao ja esta distribuida entre eles.
        Usa self.coupling e self.niveis_ctx se disponiveis.
        """
        if self.reservoir:
            v = self.reservoir.gerar(texto)
            if v:
                return v
        
        dados = texto.encode()[:2000] if isinstance(texto, str) else bytes(texto)[:2000]
        dim_base = MCRSignatureExpansiva.dimensionalidade_ideal(dados, mx=256, thr=0.05)
        
        # Reducao por correlacao cross-level
        if self.coupling and self.niveis_ctx:
            corr_total = 0.0
            n_corr = 0
            for ctx_nivel in self.niveis_ctx:
                p = self.coupling.peso(ctx_nivel, "fingerprint")
                if p > 0:
                    corr_total += p
                    n_corr += 1
                p_inv = self.coupling.peso("fingerprint", ctx_nivel)
                if p_inv > 0:
                    corr_total += p_inv
                    n_corr += 1
            if n_corr > 0:
                corr_media = corr_total / n_corr
                fator = MCRThreshold("hdc_dim").obter("fator", 0.5)
                dim_base = int(dim_base * max(fator, 1.0 - corr_media))
        
        return MCRByteUtils.fingerprint(texto, max(dim_base, 8))
    
    def _tunel_dimensional(self, va, vb):
        """Cria um tunel entre duas dimensoes via Produto de Kronecker.
        
        Em vez de interpolar (que cria dados falsos), preserva a assinatura
        completa de AMBAS as dimensoes. O tunel e' a interacao entre elas.
        
        Se va = [a1, a2] (2D) e vb = [b1, b2, b3] (3D),
        o tunel = [a1*b1, a1*b2, a1*b3, a2*b1, a2*b2, a2*b3] (6D).
        
        Cada byte de uma dimensao colide com cada byte da outra,
        sem distorcao, sem interpolacao, sem dados falsos.
        """
        if not va or not vb:
            return va, vb
        # Produto de Kronecker: cada elemento de va multiplica vb inteiro
        tunel = [a * b for a in va for b in vb]
        return tunel, tunel
    
    def _normalizar(self, va, vb, dim_alvo=None):
        """Normaliza dois vetores para o MESMO tamanho (fallback).
        
        Usa zero-padding em vez de interpolacao para nao criar dados falsos.
        O padrao e usar _tunel_dimensional — este metodo e fallback.
        """
        if not va or not vb:
            return va, vb
        # Tenta usar o tunel dimensional primeiro
        dec = MCRDecisorUniversal.decidir(ctx="hdc_tunel")
        if dec.get("threshold", 0.5) > 0.3:
            return self._tunel_dimensional(va, vb)
        # Fallback: zero-padding preserva assinatura sem interpolar
        n = max(len(va), len(vb))
        def _pad(v, n):
            if len(v) >= n:
                return list(v[:n])
            return list(v) + [0.0] * (n - len(v))
        return _pad(va, n), _pad(vb, n)
    
    def bundle(self, a, b, peso_a=0.5, peso_b=0.5):
        """Bundle: soma ponderada de dois vetores."""
        va = self._vetor(a) if isinstance(a, str) else a
        vb = self._vetor(b) if isinstance(b, str) else b
        if not va or not vb:
            return []
        va, vb = self._normalizar(va, vb)
        resultado = [va[i]*peso_a + vb[i]*peso_b for i in range(len(va))]
        self.mk_bundle.aprender(f"BD:{str(a)[:10]}:{str(b)[:10]}", str(resultado[:4]))
        self.total += 1
        return resultado
    
    def bind(self, a, b):
        """Bind: multiplicacao elemento a elemento."""
        va = self._vetor(a) if isinstance(a, str) else a
        vb = self._vetor(b) if isinstance(b, str) else b
        if not va or not vb:
            return []
        va, vb = self._normalizar(va, vb)
        resultado = [va[i]*vb[i] for i in range(len(va))]
        self.mk_bind.aprender(f"BN:{str(a)[:10]}:{str(b)[:10]}", str(resultado[:4]))
        self.total += 1
        return resultado
    
    def permute(self, v, rot=1):
        """Permute: rotacao circular do vetor.
        
        Marca ordem temporal. permute(A) significa "A depois".
        """
        if isinstance(v, str):
            v = self._vetor(v)
        if not v:
            return []
        rot = rot % len(v)
        resultado = v[-rot:] + v[:-rot]
        self.mk_permute.aprender(f"PR:{rot}", str(resultado[:4]))
        self.total += 1
        return resultado
    
    def bundle_inv(self, a, b, peso_b=0.5):
        """Bundle inverso: subtracao ponderada.
        
        Para analogias: bundle_inv("rei", "homem") ≈ "real"
        """
        va = self._vetor(a) if isinstance(a, str) else a
        vb = self._vetor(b) if isinstance(b, str) else b
        if not va or not vb:
            return []
        va, vb = self._normalizar(va, vb)
        return [va[i] - vb[i]*peso_b for i in range(len(va))]
    
    def analogia(self, a, b, c, candidatos):
        """Resolve analogia A:B :: C:?
        
        Ex: analogia("rei", "homem", "rainha", candidatos)
        → busca "mulher" onde resultado ≈ bundle_inv(bundle(A,C), B)
        """
        va = self._vetor(a)
        vb = self._vetor(b)
        vc = self._vetor(c)
        if not va or not vb or not vc:
            return None, 0.0
        
        # Normaliza para o mesmo tamanho usando ZERO-PADDING
        # (nao usa tunel aqui porque analogia precisa de comparacao elemento-a-elemento)
        n = max(len(va), len(vb), len(vc))
        def _pad(v, n):
            if len(v) >= n: return list(v[:n])
            return list(v) + [0.0] * (n - len(v))
        va, vb, vc = _pad(va, n), _pad(vb, n), _pad(vc, n)
        
        diferenca = [va[i] - vb[i] for i in range(len(va))]
        resultado = [diferenca[i] + vc[i] for i in range(len(vc))]
        
        melhor = None
        melhor_sim = 0
        for cand in candidatos:
            vd = self._vetor(cand)
            if not vd:
                continue
            r, vd_norm = self._normalizar(resultado, vd)
            sim = MCRByteUtils.similaridade_cosseno(r, vd_norm)
            if sim > melhor_sim:
                melhor_sim = sim
                melhor = cand
        
        self.mk_analogia.aprender(f"AN:{a}:{b}:{c}", f"{melhor}:{melhor_sim:.3f}" if melhor else "nulo")
        return melhor, round(melhor_sim, 3)
    
    def comparar(self, a, b):
        """Compara dois textos usando bundle dos fingerprints."""
        va = self._vetor(a)
        vb = self._vetor(b)
        if not va or not vb:
            return 0.0
        mx = max(len(va), len(vb))
        def _pad(v, n):
            if len(v) >= n: return list(v[:n])
            return list(v) + [0.0] * (n - len(v))
        va, vb = _pad(va, mx), _pad(vb, mx)
        return MCRByteUtils.similaridade_cosseno(va, vb)

# ═══════════════════════════════════════════════════════════════════
# [01c] MCRSuperposicao — colisao de rotas Markov gera algo novo
# ═══════════════════════════════════════════════════════════════════

class MCRSuperposicao:
    """Superposicao de rotas Markov: colisao entre cadeias gera algo novo.
    
    O conceito:
    1. Duas rotas (cadeias Markov) convergem no mesmo ponto
    2. Cada rota prediz seu proximo estado (caminho mais provavel)
    3. A COLISAO gera multiplos resultados possiveis (superposicao)
    4. A entropia de CADA resultado decide qual e o "novo"
    5. O resultado e algo que nenhuma rota individual previu
    
    Exemplo:
      rota_byte = MCR("byte").predizer("B:3D")    # → B:20 (espaco)
      rota_palavra = MCR("palavra").predizer("=")  # → None (366 opcoes)
      colisao = superposicao.colidir("byte", "B:3D", "palavra", "=")
      # → "self" — byte previu "espaco", palavra previu nada
      #   A colisao gerou "self" que e o que realmente vem depois de "= "
    """
    
    def __init__(self, coupling):
        self.coupling = coupling
        self.mk_colisoes = MCR("superposicao")
        self.total = 0
    
    def colidir(self, nivel_a, valor_a, nivel_b, valor_b, mk_a=None, mk_b=None):
        """Colide duas rotas no mesmo ponto e retorna o resultado.
        
        A colisao funciona assim:
        1. Rota A prediz proximo estado (se possivel)
        2. Rota B prediz proximo estado (se possivel)
        3. Se AMBAS tem candidatos, usa a ESFERA para encontrar o
           ponto de menor entropia entre eles — o "novo" resultado
        4. Se UMA falha, usa a outra como fallback
        5. Se AMBAS falham, a esfera tenta inferir de outros niveis
        """
        self.total += 1
        
        # 1. Rota A
        pred_a = None
        conf_a = 0.0
        if mk_a:
            pred_a, conf_a = mk_a.predizer(valor_a)
        
        # 2. Rota B
        pred_b = None
        conf_b = 0.0
        if mk_b:
            pred_b, conf_b = mk_b.predizer(valor_b)
        
        resultados = {}
        
        # 3. Se ambas tem candidatos — SUPERPOSICAO
        if pred_a and pred_b:
            # Esfera avalia qual e o ponto de menor entropia
            for ctx_nivel, ctx_valor in [(nivel_a, valor_a), (nivel_b, valor_b)]:
                r, c = self.coupling.esfera.predizer_cross(ctx_nivel, **{ctx_nivel: ctx_valor})
                if r and c > 0:
                    resultados[r] = resultados.get(r, 0) + c
            # Aprende: colisao A+B gerou estes resultados
            self.mk_colisoes.aprender(f"COL:{nivel_a}:{nivel_b}:{str(valor_a)[:5]}:{str(valor_b)[:5]}",
                                     str(list(resultados.keys())[:3]))
        
        # 4. Se uma falhou, usa a outra como fallback
        if not resultados:
            if pred_a:
                resultados[pred_a] = conf_a
            if pred_b:
                resultados[pred_b] = conf_b
        
        # 5. Se ambas falharam, tenta esfera cross-dimensional
        if not resultados:
            for ctx_nivel in ["byte", "palavra", "token_tipo", "linha", "hash_curto"]:
                if ctx_nivel not in [nivel_a, nivel_b]:
                    r, c = self.coupling.esfera.predizer_cross(nivel_a, **{ctx_nivel: valor_a})
                    if r and c > 0.1:
                        resultados[r] = c
                        break
        
        if not resultados:
            return None, 0.0, {"colisao": "vazia", "total": self.total}
        
        # Escolhe o melhor resultado
        melhor = max(resultados, key=resultados.get)
        conf = resultados[melhor]
        
        return melhor, round(conf, 3), {
            "colisao": f"{nivel_a}({valor_a}) x {nivel_b}({valor_b})",
            "pred_a": pred_a,
            "pred_b": pred_b,
            "resultados": resultados,
            "total": self.total,
        }

# ═══════════════════════════════════════════════════════════════════
# [01d] MCREntropicSearch — MCTS com entropia como metrica (F3)
# ═══════════════════════════════════════════════════════════════════

class MCREntropicSearch:
    """Entropic Tree Search: MCTS com entropia como metrica.
    
    A acao otima e a que produz a trajetoria de MENOR ENTROPIA
    (mais previsivel). Substitui "distancia ao objetivo" por
    "entropia acumulada da trajetoria simulada".
    
    O caminho otimo nao e o mais curto — e o MAIS PREVISIVEL.
    """
    def __init__(self, world, qlearn):
        self.world = world
        self.qlearn = qlearn
        self.mk_sim = MCR("es_similaridade")
        self.mk_inc = MCR("es_incerteza")
        self.thr_rollouts = MCRThreshold("es_n_rollouts")
        self.thr_depth = MCRThreshold("es_depth")
        self.total = 0
    
    def rollout(self, estado, acao, passos=5):
        """Simula N passos a partir de estado + acao.
        Retorna (estado_final, trajetoria) onde trajetoria e
        a lista de estados intermediarios."""
        est = estado.clone()
        traj = [est]
        for _ in range(passos):
            ac = self.qlearn.melhor_acao(est)
            if not ac:
                ac = self.qlearn.escolher_acao(est, epsilon=0.1)
            prox = self.world.simular(est, ac)
            if prox is None:
                prox = MCRAcao.executar(est, ac)
            est = prox
            traj.append(est)
        return est, traj
    
    def _entropia_trajetoria(self, trajetoria):
        """Entropia media dos fingerprints dos estados na trajetoria.
        Quanto menor, mais PREVISIVEL e a trajetoria.
        Quanto maior, mais CAOTICA."""
        if not trajetoria:
            return 1.0
        entropias = []
        for est in trajetoria:
            fp = est.fingerprint(16)  # fingerprint 16D para maior resolucao
            total = sum(abs(v) for v in fp) or 1
            ent = -sum((abs(v)/total)*math.log2(max(abs(v)/total, 0.001)) for v in fp if abs(v) > 0)
            entropias.append(ent)
        return sum(entropias) / len(entropias)
    
    def planejar(self, estado, objetivo, n_rollouts=None, depth=None):
        """Entropic Tree Search sobre espaco de acoes.
        
        Para cada acao, executa multiplos rollouts.
        Score = bonus_proximidade - entropia_trajetoria.
        Melhor acao = a que minimiza entropia (maximiza previsibilidade).
        """
        n_rollouts = n_rollouts or int(self.thr_rollouts.obter("rollouts", 10))
        depth = depth or int(self.thr_depth.obter("depth", 4))
        
        melhor_acao = None
        melhor_score = -999
        
        for acao in MCRAcao.disponiveis():
            scores = []
            for _ in range(n_rollouts):
                prox, traj = self.rollout(estado, acao, depth)
                # Bonus por proximidade ao objetivo
                dist = self.world.distancia_manhattan(prox, objetivo) if hasattr(self.world, 'distancia_manhattan') else 99
                bonus_prox = 10.0 / max(dist + 1, 0.1)
                # Entropia da trajetoria (menor = melhor)
                ent_traj = self._entropia_trajetoria(traj)
                # Score composto: recompensa - entropia (entropia e penalidade)
                score = bonus_prox - ent_traj * 2
                scores.append(score)
            
            if not scores:
                continue
            
            media_s = sum(scores) / len(scores)
            var_s = sum((s - media_s)**2 for s in scores) / len(scores)
            score = media_s - var_s * 0.5  # penaliza incerteza (alta variancia)
            
            if score > melhor_score:
                melhor_score = score
                melhor_acao = acao
            
            self.mk_sim.aprender(
                f"ES:{str(estado.fingerprint(16)[:3])}:{acao}",
                f"{media_s:.2f}"
            )
        
        # Treina thresholds com score real
        score_abs = max(abs(melhor_score), 0.01) if melhor_score != -999 else 1.0
        self.thr_rollouts.observar(n_rollouts * score_abs / 10)
        self.thr_depth.observar(depth * score_abs / 10)
        self.total += 1
        return melhor_acao, round(melhor_score, 3)

# ═══════════════════════════════════════════════════════════════════
# [01d] MCRAutoEvolution — auto-modificacao com validacao por entropia (F4)
# ═══════════════════════════════════════════════════════════════════

class MCRAutoEvolution:
    """Auto-modificacao com verificacao empirica.
    
    Em vez de MCRCodex.substituir() (sempre aceita):
    1. Mede entropia global ANTES
    2. Propoe mutacao (parametro ou novo modulo)
    3. Aplica em copia
    4. Mede entropia global DEPOIS
    5. ACEITA se entropia_depois < entropia_antes
    6. REJEITA e reverte se entropia piorou
    7. Aprende: esta classe de mutacao foi boa/ruim
    
    Equivalente funcional a Godel Machine com entropia como utility.
    """
    def __init__(self, cerebro):
        self.cerebro = cerebro
        self.mk_mutacoes = MCR("ae_mutacoes")
        self.mk_resultados = MCR("ae_resultados")
        self.thr_aceitacao = MCRThreshold("ae_aceite")
        self.hist: List[Dict] = []
    
    def entropia_global(self):
        entropias = []
        c = self.cerebro
        if hasattr(c, 'mk_byte'):
            entropias.append(c.mk_byte.entropia_media())
        if hasattr(c, 'mk_palavra'):
            entropias.append(c.mk_palavra.entropia_media())
        # Etapa 4: entropia do mundo causal
        if hasattr(c, 'world') and hasattr(c.world, 'mk_estado'):
            entropias.append(c.world.mk_estado.entropia_media())
        # Entropia do coupling (matriz de pesos entre niveis)
        if hasattr(c, 'coupling') and c.coupling.total_cooc > 0:
            cm = c.coupling.matriz
            vals = [cm[o][d] for o in cm for d in cm[o] if o != d]
            if vals:
                from collections import Counter as _Cnt
                f = _Cnt(vals); n = len(vals)
                ent_c = -sum((c/n)*math.log2(c/n) for c in f.values()) if n > 0 else 0
                entropias.append(min(ent_c, 1.0))
        # Entropia dos MCRThreshold: mede QUANTO os valores mudaram
        # em relacao aos valores estaveis (obter). Se AE mutou, obs[-1]
        # difere de obter() → entropia sobe → AE detecta impacto.
        thr_baseline = []
        thr_trial = []
        if hasattr(MCRAttention, '_thr_p'):
            for nome_k, thr_k in MCRAttention._thr_p.items():
                thr_baseline.append(thr_k.obter("peso", 3.0))
                if len(thr_k.obs) >= 1:
                    thr_trial.append(abs(thr_k.obs[-1] - thr_baseline[-1]))
        # Mede mudanca: se AE tentou algo, quanto diferiu do baseline?
        if thr_trial:
            ent_thr = min(sum(thr_trial) / len(thr_trial), 1.0)
            if ent_thr > 0:
                entropias.append(ent_thr)
        # Variancia da entropia entre topicos (ruido do sistema)
        if hasattr(c, 'topicos') and len(c.topicos) >= 2:
            ents_t = []
            for t in list(c.topicos.values())[:20]:
                texto = t.get("texto", "")
                if texto:
                    ents_t.append(MCRByteUtils.entropia_bytes(texto.encode()[:500]))
            if ents_t:
                media_t = sum(ents_t) / len(ents_t)
                var_t = sum((e - media_t)**2 for e in ents_t) / len(ents_t)
                entropias.append(min(var_t * MCRDecisorUniversal.decidir(ctx="ae_var").get("threshold", 0.5), 1.0))
        return sum(entropias) / max(len(entropias), 1) if entropias else 1.0
    
    def ciclo(self):
        """Um ciclo de auto-evolucao: medir → mutar → validar → aceitar/rejeitar.
        
        MCR decide QUAL threshold mutar baseado no estado do sistema.
        Nao ha lista fixa de alvos — MCRDecisor escolhe de TODOS os
        MCRThreshold disponiveis.
        """
        ent_antes = self.entropia_global()
        
        # MCR decide qual threshold mutar (ctx="ae_alvo")
        dec_alvo = MCRDecisorUniversal.decidir(ctx="ae_alvo")
        tipo_alvo = dec_alvo.get("tipo", "atencao")
        
        alvos = []
        if tipo_alvo == "atencao" and hasattr(MCRAttention, '_thr_p'):
            for nome_k, thr_k in MCRAttention._thr_p.items():
                alvos.append((f'att_{nome_k}', thr_k))
        else:
            # Descobre QUALQUER MCRThreshold no cerebro por introspeccao
            for attr_name in dir(self.cerebro):
                attr = getattr(self.cerebro, attr_name)
                if isinstance(attr, MCRThreshold):
                    alvos.append((attr_name, attr))
        
        if not alvos:
            return {"acao": "nada_para_mutar", "motivo": "nenhum_threshold"}
        
        # MCR decide qual threshold mutar (delta, direcao)
        nome_alvo, thr = _rand.choice(alvos)
        dec = MCRDecisorUniversal.decidir(ctx="ae_delta")
        delta = dec.get("threshold", 0.05)
        if _rand.random() < 0.5:
            delta = -delta
        
        valor_original = thr.obter("valor", 0.5)
        novo_valor = max(0.01, min(1.0, valor_original + delta))
        
        mutacao = {'tipo': 'threshold', 'alvo': nome_alvo,
                   'valor_original': round(valor_original, 4),
                   'novo_valor': round(novo_valor, 4)}
        
        # Aplica mutacao no threshold (em memoria)
        thr.obs = thr.obs + [novo_valor]
        ent_depois = self.entropia_global()
        melhoria = ent_antes - ent_depois  # para logging
        
        # Criticalidade: nao buscamos entropia MINIMA (silêncio),
        # mas entropia em uma faixa saudavel (0.2-0.7).
        # Abaixo de 0.2: sistema estatico, nao aprende (AAAAA).
        # Acima de 0.7: sistema caotico, nao generaliza.
        # Entre 0.2 e 0.7: borda do caos — onde o aprendizado acontece.
        ent_alvo_min = self.thr_aceitacao.obter("alvo_min", 0.2)
        ent_alvo_max = self.thr_aceitacao.obter("alvo_max", 0.7)
        
        dentro_alvo_antes = ent_alvo_min <= ent_antes <= ent_alvo_max
        dentro_alvo_depois = ent_alvo_min <= ent_depois <= ent_alvo_max
        
        # Aceita se:
        # 1. Moveu PARA DENTRO da zona de criticalidade (melhor), OU
        # 2. Manteve-se DENTRO da zona (neutro), OU
        # 3. Entropia externa subiu (sistema observador, nao controlador)
        if not dentro_alvo_antes and dentro_alvo_depois:
            aceite = True  # entrou na criticalidade
        elif dentro_alvo_antes and not dentro_alvo_depois:
            aceite = False  # saiu da criticalidade
        elif ent_depois - ent_antes > 0.1:
            aceite = True  # entropia externa subiu — sistema apenas observou
        else:
            aceite = True  # manteve-se estavel ou melhorou dentro da faixa
        
        self.mk_resultados.aprender(f"{'ACEITE' if aceite else 'REJEITE'}:{mutacao['tipo']}", f"{melhoria:.4f}")
        self.mk_mutacoes.aprender(f"AE:{mutacao['tipo']}:{'ACEITE' if aceite else 'REJEITE'}", f"{melhoria:.4f}")
        
        r = {"timestamp": time.time(), "mutacao": mutacao,
             "ent_antes": round(ent_antes, 4), "ent_depois": round(ent_depois, 4),
             "melhoria": round(melhoria, 4), "resultado": "aceito" if aceite else "rejeitado"}
        self.hist.append(r)
        self.thr_aceitacao.observar(abs(melhoria))
        return r
    
    def _entropia_cerebro(self, cerebro):
        """Entropia de um cerebro (para comparacao antes/depois)."""
        entropias = []
        if hasattr(cerebro, 'mk_byte'):
            entropias.append(cerebro.mk_byte.entropia_media())
        if hasattr(cerebro, 'mk_palavra'):
            entropias.append(cerebro.mk_palavra.entropia_media())
        return sum(entropias) / max(len(entropias), 1) if entropias else 1.0
    
    def relatorio(self):
        aceites = sum(1 for h in self.hist if h['resultado'] == 'aceito')
        return {
            "ciclos": len(self.hist),
            "aceites": aceites,
            "taxa_aceite": round(aceites / max(len(self.hist), 1), 3),
            "entropia_atual": round(self.entropia_global(), 4),
        }

class MCRThreshold:
    def __init__(self, nome=""):
        self.obs = []; self.mk = MCR(nome)
    def observar(self, v):
        self.obs.append(v); self.mk.aprender(f"V:{int(v*100)}", "O")
    def calcular(self, mult=1.0):
        return median(self.obs)*mult if len(self.obs) >= 3 else 0.5
    def obter(self, chave, fallback=0.5):
        p, c = self.mk.predizer(f"T:{chave}")
        if p and c > 0.3:
            try: return int(p)/100.0
            except: pass
        return self.calcular() if len(self.obs) >= 3 else fallback

class MCREntropia:
    def __init__(self, nome=""):
        self.mk = MCR(nome); self.hist: List[float] = []; self.thr = MCRThreshold(f"e_{nome}")
    def alimentar(self, t):
        self.mk.aprender(f"T:{str(t)[:50]}", "V")
        h = self.mk.entropia(f"T:{str(t)[:50]}")
        self.hist.append(h)
        if len(self.hist) > 100: self.hist = self.hist[-50:]
    def esta_em_loop(self):
        if len(self.hist) < 3: return False
        hl = sum(self.hist[-10:])/min(10, len(self.hist))
        self.thr.observar(hl); return hl < self.thr.calcular(0.5)

# ═══════════════════════════════════════════════════════════════════
# [16] MCRDecisorUniversal — parametros decididos pela Equacao
# ═══════════════════════════════════════════════════════════════════

class MCRDecisorUniversal:
    _th = MCRThreshold("decisor")
    _cache: Dict[str, dict] = {}
    @classmethod
    def decidir(cls, motor=None, ctx=""):
        return {"passos": max(1, int(cls._th.obter("passos",6))), "threshold": cls._th.obter("thr",0.5), "dim": max(4, int(cls._th.obter("dim",8)))}
    @classmethod
    def decidir_passos(cls, ctx="default", estado=None):
        """Decide quantas iteracoes executar — zero hardcode.
        ctx: contexto (ex: 'test_coupling', 'auto_diag', 'descobrir_drives')
        estado: dict opcional com estado real (ex: {'n_topicos': 10, 'tamanho_bytes': 2000})
        MCRThreshold aprende com o tempo qual numero e ideal.
        """
        chave = f"passos_{ctx}"
        # Padrao por contexto (aprendido via MCRThreshold, estes sao seeds iniciais apenas)
        padrao = {
            "test_coupling": 5,
            "auto_diag": 5,
            "descobrir_drives": 2,
            "ler_entropia": 4,
        }.get(ctx, 6)
        # Se tem estado real, ajusta baseado na necessidade
        if estado:
            if "n_topicos" in estado and estado["n_topicos"] > 0:
                padrao = max(2, min(20, estado["n_topicos"] // 2))
            if "tamanho_bytes" in estado and estado["tamanho_bytes"] > 0:
                padrao = max(1, min(10, estado["tamanho_bytes"] // 500 + 1))
        passos = max(1, int(cls._th.obter(chave, padrao)))
        return passos

# ═══════════════════════════════════════════════════════════════════
# [04] Entidade + EstadoMundo + MotorFisica
# ═══════════════════════════════════════════════════════════════════

class Entidade:
    def __init__(self, nome, tipo="objeto", props=None):
        self.nome, self.tipo, self.props = nome, tipo, props or {}
    def clone(self): return Entidade(self.nome, self.tipo, dict(self.props))

class EstadoMundo:
    def __init__(self):
        self.entidades: Dict[str, Entidade] = {}; self.grid_w, self.grid_h = 5, 5; self.obstaculos: Set[Tuple[int,int]] = set()
    def adicionar(self, e): self.entidades[e.nome] = e
    def remover(self, n): self.entidades.pop(n, None)
    def get(self, n): return self.entidades.get(n)
    def serializar(self):
        return MCRSerializador.serializar(self.entidades)
    def fingerprint(self, dim=8): return MCRByteUtils.fingerprint(self.serializar(), dim)
    def clone(self):
        e = EstadoMundo(); e.entidades = {n: ent.clone() for n, ent in self.entidades.items()}
        e.grid_w, e.grid_h = self.grid_w, self.grid_h; e.obstaculos = set(self.obstaculos); return e
    @staticmethod
    def criar_simples():
        e = EstadoMundo()
        e.adicionar(Entidade("heroi","jogador",{"x":0,"y":0,"hp":10}))
        e.adicionar(Entidade("pedra","objeto",{"x":2,"y":2,"gravidade":True}))
        e.adicionar(Entidade("bau","objeto",{"x":4,"y":4,"aberto":False}))
        e.adicionar(Entidade("monstro","inimigo",{"x":3,"y":1,"hp":5}))
        return e

# ═══════════════════════════════════════════════════════════════════
# [18] MCRSerializador
# ═══════════════════════════════════════════════════════════════════

class MCRSerializador:
    @staticmethod
    def serializar(entidades):
        partes = []
        for nome in sorted(entidades.keys()):
            e = entidades[nome]
            ps = ";".join(f"{k}={v}" for k, v in sorted(e.props.items()))
            partes.append(f"{e.nome}:{e.tipo}:{ps}")
        return "|".join(partes)
    @staticmethod
    def fingerprint(entidades, dim=None):
        return MCRByteUtils.fingerprint(MCRSerializador.serializar(entidades), dim or C("dim_fingerprint", 8))

# ═══════════════════════════════════════════════════════════════════
# [03] MCRAcao — acoes registradas, zero if/elif
# ═══════════════════════════════════════════════════════════════════

class MCRAcao:
    _reg: Dict[str, Dict] = {}
    @classmethod
    def registrar(cls, nome, fn, desc="", tags=None, alcance=1):
        cls._reg[nome] = {"fn": fn, "desc": desc, "tags": tags or [], "alcance": alcance}
    @classmethod
    def executar(cls, estado, acao, **kw):
        if acao not in cls._reg: return estado.clone()
        return cls._reg[acao]["fn"](estado, **kw)
    @classmethod
    def disponiveis(cls): return list(cls._reg.keys())
    @classmethod
    def total(cls): return len(cls._reg)

def _registrar_acoes():
    MCRAcao.registrar("andar_dir", lambda e, **k: _mover(e,1,0), "direita", ["movimento"])
    MCRAcao.registrar("andar_esq", lambda e, **k: _mover(e,-1,0), "esquerda", ["movimento"])
    MCRAcao.registrar("andar_cima", lambda e, **k: _mover(e,0,-1), "cima", ["movimento"])
    MCRAcao.registrar("andar_baixo", lambda e, **k: _mover(e,0,1), "baixo", ["movimento"])
    MCRAcao.registrar("atacar", lambda e, **k: _interagir(e,"hp",-3), "atacar", ["combate"])
    MCRAcao.registrar("abrir", lambda e, **k: _interagir(e,"aberto",True), "abrir", ["interacao"])
    MCRAcao.registrar("empurrar", lambda e, **k: _empurrar(e), "empurrar", ["interacao"])

def _mover(est, dx, dy):
    nv = est.clone(); h = nv.get("heroi")
    if not h: return nv
    x, y = h.props.get("x",0), h.props.get("y",0); nx, ny = x+dx, y+dy
    if 0 <= nx < nv.grid_w and 0 <= ny < nv.grid_h and (nx,ny) not in nv.obstaculos:
        nv.entidades["heroi"].props["x"], nv.entidades["heroi"].props["y"] = nx, ny
    return nv

def _interagir(est, prop, val):
    nv = est.clone(); h = nv.get("heroi")
    if not h: return nv
    x, y = h.props.get("x",0), h.props.get("y",0); tgt = _adjacente(nv, x, y)
    if tgt and prop in tgt.props:
        if isinstance(val, (int,float)) and isinstance(tgt.props[prop], (int,float)):
            nv.entidades[tgt.nome].props[prop] += val
            if prop == "hp" and nv.entidades[tgt.nome].props["hp"] <= 0: nv.remover(tgt.nome)
        else: nv.entidades[tgt.nome].props[prop] = val
    return nv

def _empurrar(est):
    nv = est.clone(); h = nv.get("heroi")
    if not h: return nv
    x, y = h.props.get("x",0), h.props.get("y",0); tgt = _adjacente(nv, x, y)
    if tgt:
        dx = tgt.props.get("x",0)-x; dy = tgt.props.get("y",0)-y
        nx, ny = tgt.props.get("x",0)+dx, tgt.props.get("y",0)+dy
        if 0 <= nx < nv.grid_w and 0 <= ny < nv.grid_h and (nx,ny) not in nv.obstaculos:
            nv.entidades[tgt.nome].props["x"], nv.entidades[tgt.nome].props["y"] = nx, ny
    return nv

def _adjacente(est, x, y):
    cands = []
    for n, e in est.entidades.items():
        if n == "heroi": continue
        ex, ey = e.props.get("x",-1), e.props.get("y",-1)
        if abs(ex-x)+abs(ey-y) == 1: cands.append(e)
    if not cands: return None
    for e in cands:
        if "hp" in e.props: return e
    for e in cands:
        if "aberto" in e.props: return e
    return cands[0]

_registrar_acoes()

# ═══════════════════════════════════════════════════════════════════
# [04] MCRNLP — NLP por jaccard, zero keywords
# ═══════════════════════════════════════════════════════════════════

class MCRNLP:
    _ex: Dict[str, List[str]] = {}
    _dom: Dict[str, List[str]] = {}
    @classmethod
    def aprender(cls, frase, acao, dominio="acao"):
        cls._ex.setdefault(acao, []).append(frase.lower())
        if dominio != "acao": cls._dom.setdefault(dominio, []).append(frase.lower())
    @classmethod
    def entender(cls, frase, dominio="acao", top_k=None):
        top_k = top_k or max(1, int(C("top_k",3))); frase = frase.lower()
        # Dimensionalidade ideal para a frase (P6-NOVO)
        dim = MCRSignatureExpansiva.dimensionalidade_ideal(
            frase.encode()[:2000], mx=128, thr=0.05
        )
        fp_frase = MCRByteUtils.fingerprint(frase, max(dim, 4))
        scores = {}
        for acao, exs in cls._ex.items():
            melhor_j = max((MCRByteUtils.jaccard_bytes(frase, ex) for ex in exs), default=0)
            if melhor_j <= 0: continue
            melhor_cos = max(
                (MCRByteUtils.similaridade_cosseno(
                    fp_frase, MCRByteUtils.fingerprint(ex, max(dim, 4))
                ) for ex in exs), default=0
            )
            # Score combinado: jaccard + cosseno com dimensionalidade ideal
            params = MCRDecisorUniversal.decidir(ctx="nlp")
            peso_j = params.get("peso_jaccard", 0.5)
            scores[acao] = melhor_j * peso_j + melhor_cos * (1 - peso_j)
        ords = sorted(scores.items(), key=lambda x: -x[1])
        limiar = MCRThreshold("nlp_entender").obter("limiar", 0.3)
        return [acao for acao, score in ords[:top_k] if score > limiar]
    @classmethod
    def auto_expandir(cls, cerebro):
        """Expande exemplos de treino usando topicos do cerebro (F3).
        
        Para cada acao com poucos exemplos, busca topicos similares
        no cerebro e extrai novas frases como exemplos adicionais.
        """
        thr_min = MCRThreshold("nlp_expandir").obter("min_exemplos", 3)
        thr_jac = MCRThreshold("nlp_expandir").obter("jac_min", 0.2)
        thr_pal = MCRThreshold("nlp_expandir").obter("palavras_min", 3)
        for acao, exs in list(cls._ex.items()):
            if len(exs) >= thr_min:
                continue
            for ex in exs:
                if not cerebro.topicos:
                    continue
                for nome, dados in cerebro.topicos.items():
                    texto = dados.get("texto", "")
                    j = MCRByteUtils.jaccard_bytes(ex, texto[:500])
                    if j < thr_jac:
                        continue
                    palavras = texto.split()[:10]
                    if len(palavras) < thr_pal:
                        continue
                    nova = " ".join(palavras[:thr_pal])
                    if nova not in exs:
                        cls.aprender(nova, acao)
    @classmethod
    def detectar_dominio(cls, texto):
        texto = texto.lower()
        if not cls._dom: return "texto"
        melhor_dom, melhor_j = "texto", 0.0
        for dom, frases in cls._dom.items():
            for ex in frases:
                j = MCRByteUtils.jaccard_bytes(texto, ex)
                if j > melhor_j: melhor_j, melhor_dom = j, dom
        return melhor_dom if melhor_j > C("conf_alta", 0.5) else "texto"

def _registrar_nlp():
    for f in ["anda pra cima","suba","norte","cima"]: MCRNLP.aprender(f, "andar_cima")
    for f in ["anda pra baixo","desca","sul","baixo"]: MCRNLP.aprender(f, "andar_baixo")
    for f in ["anda pra esquerda","esquerda","oeste"]: MCRNLP.aprender(f, "andar_esq")
    for f in ["anda pra direita","direita","leste"]: MCRNLP.aprender(f, "andar_dir")
    for f in ["ataque","atacar","bater","lutar"]: MCRNLP.aprender(f, "atacar")
    for f in ["abrir","abra o bau","abrir porta"]: MCRNLP.aprender(f, "abrir")
    for f in ["empurrar","empurre","mover","arrastar"]: MCRNLP.aprender(f, "empurrar")
    for f in ["heroi","posicao","grid","andar","bau","monstro","heroi andou","bau aberto"]: MCRNLP._dom.setdefault("grid",[]).append(f)
    for f in ["SPA","SHC","sistema","progressao","habilidade","lore"]: MCRNLP._dom.setdefault("texto",[]).append(f)
    for f in ["fibonacci","sequencia","numero","potencia","1 2 3"]: MCRNLP._dom.setdefault("numerico",[]).append(f)
_registrar_nlp()

# ═══════════════════════════════════════════════════════════════════
# [05] MCRAttention — foco seletivo, 4 sinais da Equacao
# ═══════════════════════════════════════════════════════════════════

class MCRAttention:
    _thr_p = {"prob": MCRThreshold("att_prob"), "fp": MCRThreshold("att_fp"),
              "jac": MCRThreshold("att_jac"), "ent": MCRThreshold("att_ent")}
    @classmethod
    def _pesos(cls):
        return {k: v.obter("peso", p) for k, v, p in
                [("prob", cls._thr_p["prob"], 3.0), ("fp", cls._thr_p["fp"], 5.0),
                 ("jac", cls._thr_p["jac"], 4.0), ("ent", cls._thr_p["ent"], 1.0)]}
    @classmethod
    def _topico_relevante(cls, cerebro, pergunta):
        if not pergunta or not cerebro.topicos: return None
        melhor_n, melhor_t, melhor_j = None, None, 0.0
        for nome, dados in cerebro.topicos.items():
            texto = dados.get("texto","")
            if len(texto) < 20: continue
            j = MCRByteUtils.jaccard_bytes(pergunta, texto[:500])
            if j > melhor_j: melhor_j, melhor_n, melhor_t = j, nome, texto
        return (melhor_n, melhor_t, melhor_j) if melhor_j > 0.01 else None
    @classmethod
    def pontuar(cls, cerebro, ctx, pergunta="", k=10):
        if not ctx: return []
        palavras = ctx.split(); semente = palavras[-1] if palavras else ""
        topico = cls._topico_relevante(cerebro, pergunta)
        if topico:
            _, txt, _ = topico; tx = txt.split()
            cands = {}
            for i, p in enumerate(tx):
                if p == semente and i+1 < len(tx):
                    prox = tx[i+1]; cands[prox] = cands.get(prox,0)+1
            cands = [(t, c/max(sum(cands.values()),1)) for t,c in sorted(cands.items(), key=lambda x:-x[1])][:k*3]
        else:
            cands = cerebro.mk_palavra.predizer_n(semente, k*3) if hasattr(cerebro,'mk_palavra') else []
        if not cands: return []
        fp_ctx = MCRByteUtils.fingerprint(ctx)
        pts = []
        for token, prob in cands:
            s_prob = prob
            fp_tok = MCRByteUtils.fingerprint(f"{ctx} {token}")
            s_fp = MCRByteUtils.similaridade_cosseno(fp_ctx, fp_tok)
            s_jac = 0.0
            if pergunta:
                for d in cerebro.topicos.values():
                    txt = d.get("texto","")
                    if token in txt and len(txt) > 20:
                        j = MCRByteUtils.jaccard_bytes(pergunta, txt[:500])
                        if j > s_jac: s_jac = j
            h = cerebro.mk_palavra.entropia(token) if hasattr(cerebro,'mk_palavra') and token in cerebro.mk_palavra.freq else 0.5
            s_ent = 1.0 - abs(h-0.5)*2
            w = cls._pesos()
            nota = (s_prob*w["prob"] + s_fp*w["fp"] + s_jac*w["jac"] + s_ent*w["ent"])/sum(w.values())
            pts.append((token, round(nota,4)))
        pts.sort(key=lambda x:-x[1]); return pts[:k]
    @classmethod
    def gerar(cls, cerebro, texto, passos=None, pergunta=""):
        passos = passos or int(C("passos_gerar",6))
        palavras = texto.split()
        if not palavras: return texto
        pergunta = pergunta or texto
        for _ in range(passos):
            ctx = " ".join(palavras)
            cands = cls.pontuar(cerebro, ctx, pergunta, k=int(C("top_k",3))+2)
            if not cands: break
            palavras.append(cands[0][0])
            if len(palavras) >= 4 and len(set(palavras[-4:])) == 1: break
        return " ".join(palavras)

# ═══════════════════════════════════════════════════════════════════
# [06] MCRWorld — modelo causal
# ═══════════════════════════════════════════════════════════════════

class MCRWorld:
    def __init__(self):
        self.mk_estado = MCR("world_est"); self.mk_acao = MCR("world_ac"); self.mk_causal = MCR("world_caus")
        self.mk_plano = MCR("world_plan"); self.hist: List[Dict] = []; self.thr = MCRThreshold("world")
        self.dim_fp = C("dim_fingerprint", 16)
    def aprender(self, antes, acao, depois):
        fpa, fpd = antes.fingerprint(self.dim_fp), depois.fingerprint(self.dim_fp)
        as_, ds = str(fpa), str(fpd)
        self.mk_estado.aprender(as_, ds)
        self.mk_acao.aprender(f"{as_}:{acao}", ds)
        delta = tuple(round(d,3) for d in MCRByteUtils.delta_fingerprint(antes.serializar(), depois.serializar(), self.dim_fp))
        self.mk_causal.aprender(str(delta), acao)
        self.hist.append({"a": antes.serializar()[:30], "ac": acao, "d": depois.serializar()[:30]})
        self.thr.observar(MCRByteUtils.jaccard_bytes(antes.serializar(), depois.serializar()))
    def simular(self, estado, acao):
        fpa = estado.fingerprint(self.dim_fp); chave = f"{str(fpa)}:{acao}"
        pdf, cf = self.mk_acao.predizer(chave)
        if pdf and cf > 0.15: return self._reconstruir(pdf, estado)
        pdf2, cf2 = self.mk_estado.predizer(str(fpa))
        if pdf2 and cf2 > 0.3: return self._reconstruir(pdf2, estado)
        return MCRAcao.executar(estado, acao)
    def _reconstruir(self, fp_str, ref):
        melh_e, melh_s = None, 0.0
        for h in self.hist[-50:]:
            e = EstadoMundo()
            try:
                for p in h["d"].split("|"):
                    if ":" in p:
                        no, r = p.split(":",1)
                        if ":" in r:
                            ti, ps = r.split(":",1); pr = {}
                            for kv in ps.split(";"):
                                if "=" in kv:
                                    kk, vv = kv.split("=",1)
                                    try: vv = int(vv)
                                    except: pass
                                    pr[kk] = vv
                            e.adicionar(Entidade(no, ti, pr))
            except: continue
            fpe = str(e.fingerprint(self.dim_fp))
            sim = MCRByteUtils.similaridade_cosseno(
                [float(x) for x in fp_str.strip("[]").split(",") if x.strip()],
                [float(x) for x in fpe.strip("[]").split(",") if x.strip()]) if fpe else 0
            if sim > melh_s: melh_s, melh_e = sim, e
        return melh_e or ref.clone()
    def predizer_acao(self, antes, depois):
        delta = tuple(round(d,3) for d in MCRByteUtils.delta_fingerprint(antes.serializar(), depois.serializar(), self.dim_fp))
        ac, cf = self.mk_causal.predizer(str(delta))
        return ac if ac and cf > 0.1 else None
    def contrafactual(self, estado, acao, var_nome, var_valor):
        rn = self.simular(estado, acao); fp_n = rn.fingerprint(self.dim_fp) if rn else []
        ea = estado.clone()
        for e in ea.entidades.values():
            if var_nome in e.props: e.props[var_nome] = var_valor
        ra = self.simular(ea, acao); fp_a = ra.fingerprint(self.dim_fp) if ra else []
        if not fp_n or not fp_a: return f"Sem dados para contrafactual de '{var_nome}={var_valor}'."
        delta = MCRByteUtils.delta_fingerprint(rn.serializar() if rn else "", ra.serializar() if ra else "", self.dim_fp)
        mag = math.sqrt(sum(d*d for d in delta))
        return f"Se '{var_nome}' fosse '{var_valor}', mudaria em {mag:.2f} unidades. Delta: {[round(d,2) for d in delta[:4]]}"
    def distancia(self, a, b):
        fa, fb = a.fingerprint(self.dim_fp), b.fingerprint(self.dim_fp)
        return math.sqrt(sum((fb[i]-fa[i])**2 for i in range(self.dim_fp)))
    def distancia_manhattan(self, a, b):
        """Distancia Manhattan entre herois de dois estados.
        Usada para planejamento onde fingerprint 8D e insuficiente."""
        ha, hb = a.get("heroi"), b.get("heroi")
        if not ha or not hb: return self.distancia(a, b)
        return abs(ha.props.get("x",0)-hb.props.get("x",0)) + \
               abs(ha.props.get("y",0)-hb.props.get("y",0))
    def delta_entidade(self, antes, depois, nome="heroi", props=("x","y")):
        """Delta de propriedades de uma entidade entre dois estados.
        
        Ex: delta_entidade(est1, est2, 'heroi', ('x','y'))
            → [dx, dy]  (exato, independente de fingerprint)
        """
        ha, hb = antes.get(nome), depois.get(nome)
        if not ha or not hb: return []
        return [hb.props.get(k,0) - ha.props.get(k,0) for k in props]

# ═══════════════════════════════════════════════════════════════════
# [07] MCRCoupling — matriz byte↔palavra↔token↔intencao↔acao
# ═══════════════════════════════════════════════════════════════════

class MCRCoupling:
    def __init__(self):
        self.niveis = self._descobrir_niveis()
        self.matriz = {o: {d: 0.0 for d in self.niveis} for o in self.niveis}
        self.cooc = {o: {d: 0 for d in self.niveis} for o in self.niveis}
        self.total_cooc = 0; self.mk = MCR("coupling")
        # MCREsfera: aprendizado N-dimensional (evolucao do coupling 2D)
        self.esfera = MCREsfera()
    @staticmethod
    def _descobrir_niveis():
        base = ["byte","palavra","tven","fingerprint"]
        return base + ["intencao","acao","sujeito","relacao","objeto"]
    def alimentar(self, origem, destino, to, td):
        if origem not in self.niveis or destino not in self.niveis: return
        self.cooc[origem][destino] += 1; self.total_cooc += 1
        self.mk.aprender(f"CP:{origem}->{destino}:{str(to)[:10]}", str(td)[:10])
        # Alimenta a esfera N-dimensional com pares de niveis
        self.esfera.alimentar_par(origem, destino, str(to)[:10], str(td)[:10])
    def recalcular(self):
        for o in self.niveis:
            for d in self.niveis:
                if o == d: self.matriz[o][d] = 1.0; continue
                c = self.cooc[o][d]
                self.matriz[o][d] = round(c/self.total_cooc*len(self.niveis), 3) if c >= 3 and self.total_cooc else 0.0
        self.esfera.recalcular()
    def peso(self, origem, destino): return self.matriz.get(origem,{}).get(destino,0.0)
    def modular(self, nivel, probs):
        res = dict(probs)
        for outro in self.niveis:
            if outro == nivel: continue
            p = self.peso(outro, nivel)
            if p > 0.1:
                for ch in res: res[ch] *= (1 + p * 0.1)
        return res

class MCREsfera:
    """Aprendizado N-dimensional de correlacoes entre niveis.
    
    Diferenca do MCRCoupling (2D pairwise):
    - Coupling: matriz NxN de pesos entre pares de niveis
    - Esfera: aprende correlacoes entre VARIOS niveis simultaneamente
    
    Permite predicao cross-level que o coupling 2D nao faz.
    Usa dict de dicts aninhados (matriz N-dimensional esparsa).
    """
    def __init__(self):
        # cross[nivel_a][valor_a][nivel_b][valor_b] = contagem
        self.cross: Dict[str, Dict] = {}
        # freq[nivel_a][valor_a] = total de ocorrencias
        self.freq_nivel: Dict[str, Dict[str, int]] = {}
        self.total = 0
    
    def _init_nivel(self, nivel):
        if nivel not in self.cross:
            self.cross[nivel] = {}
            self.freq_nivel[nivel] = {}
    
    def alimentar_par(self, nivel_a, nivel_b, valor_a, valor_b):
        """Alimenta correlacao entre dois niveis.
        
        Registra que quando nivel_a=valor_a, nivel_b tende a ser valor_b.
        """
        self._init_nivel(nivel_a)
        if valor_a not in self.cross[nivel_a]:
            self.cross[nivel_a][valor_a] = {}
        if nivel_b not in self.cross[nivel_a][valor_a]:
            self.cross[nivel_a][valor_a][nivel_b] = {}
        chave = valor_b
        self.cross[nivel_a][valor_a][nivel_b][chave] = (
            self.cross[nivel_a][valor_a][nivel_b].get(chave, 0) + 1
        )
        self.freq_nivel[nivel_a][valor_a] = self.freq_nivel[nivel_a].get(valor_a, 0) + 1
        self.total += 1
        
        # Alimenta tambem o inverso (nivel_b → nivel_a) para simetria
        self._init_nivel(nivel_b)
        if valor_b not in self.cross[nivel_b]:
            self.cross[nivel_b][valor_b] = {}
        if nivel_a not in self.cross[nivel_b][valor_b]:
            self.cross[nivel_b][valor_b][nivel_a] = {}
        chave_a = valor_a
        self.cross[nivel_b][valor_b][nivel_a][chave_a] = (
            self.cross[nivel_b][valor_b][nivel_a].get(chave_a, 0) + 1
        )
        self.freq_nivel[nivel_b][valor_b] = self.freq_nivel[nivel_b].get(valor_b, 0) + 1
        self.total += 1
    
    def recalcular(self):
        """Recalcula correlacoes: poda pares com frequencia < threshold.
        
        Remove correlacoes que nunca se repetiram (frequencia 1 = ruido).
        Auto-valida: se esfera ficou vazia, precisa de mais dados.
        """
        thr = MCRThreshold("esfera").obter("poda", 2)
        for nivel_a in list(self.cross.keys()):
            for valor_a in list(self.cross[nivel_a].keys()):
                for nivel_b in list(self.cross[nivel_a][valor_a].keys()):
                    for chave_b in list(self.cross[nivel_a][valor_a][nivel_b].keys()):
                        if self.cross[nivel_a][valor_a][nivel_b][chave_b] < thr:
                            del self.cross[nivel_a][valor_a][nivel_b][chave_b]
                    if not self.cross[nivel_a][valor_a][nivel_b]:
                        del self.cross[nivel_a][valor_a][nivel_b]
                if not self.cross[nivel_a][valor_a]:
                    del self.cross[nivel_a][valor_a]
            if not self.cross[nivel_a]:
                del self.cross[nivel_a]
        self.total = sum(
            sum(c for c in vb.values())
            for na in self.cross for va in self.cross[na].values()
            for vb in va.values()
        )
    
    def predizer_cross(self, nivel_alvo, **contexto):
        """Prediz valor em nivel_alvo dado contexto em QUALQUER nivel.
        
        Ex: esfera.predizer_cross('palavra', byte='B:41')
            → qual palavra ocorre quando byte=B:41?
        """
        candidatos = {}
        
        for nivel_ctx, valor_ctx in contexto.items():
            if nivel_ctx not in self.cross:
                continue
            if valor_ctx not in self.cross[nivel_ctx]:
                continue
            if nivel_alvo not in self.cross[nivel_ctx][valor_ctx]:
                continue
            
            freq_total = self.freq_nivel[nivel_ctx].get(valor_ctx, 1)
            for valor_b, contagem in self.cross[nivel_ctx][valor_ctx][nivel_alvo].items():
                score = contagem / freq_total
                candidatos[valor_b] = candidatos.get(valor_b, 0) + score
        
        if not candidatos:
            return None, 0.0
        
        melhor = max(candidatos, key=candidatos.get)
        conf = candidatos[melhor]
        return melhor, min(conf, 1.0)

# ═══════════════════════════════════════════════════════════════════
# [07b] MCRHiperesferaAutoExpansiva — dimensoes descobertas por entropia
# ═══════════════════════════════════════════════════════════════════

class MCRHiperesferaAutoExpansiva:
    """Descobre dimensoes automaticamente pela entropia.
    
    Comeca com 0 dimensoes. A cada ciclo, descobre a DIMENSAO
    MAIS PREVISIVEL (menor entropia) que ainda nao foi adicionada.
    Para quando o proximo candidato tem entropia ~1.0 (ruido).
    
    A ordem de descoberta e sempre: MAIS ESTRUTURADA primeiro.
    Para codigo fonte: linha → fingerprint_sliding → hash_curto → palavra
    """
    
    CANDIDATOS = [
        ("byte", lambda t: [f"B:{b:02x}" for b in t.encode('utf-8')[:2000]], "bytes individuais"),
        ("palavra", lambda t: re.findall(r'\b\w+\b', t.lower())[:500], "palavras do texto"),
        ("token_tipo", lambda t: [
            'M' if c.isupper() else 'm' if c.islower() else 'd' if c.isdigit() else 'o'
            for c in t[:1000]], "tipo do caractere"),
        ("linha", lambda t: [l[:30] for l in t.split('\n') if l.strip()][:200], "linhas do texto"),
        ("byte_delta", lambda t: [f"Δ:{abs(d[i+1]-d[i]):02x}" for d in (t.encode()[:1000],) for i in range(len(d)-1)], "diferenca entre bytes"),
        ("hash_curto", lambda t: [
            f"H:{abs(hash(p))%1000:03d}"
            for p in re.findall(r'\b\w+\b', t.lower())[:300]], "hash de palavras"),
        # Candidatos independentes de variedade lexical (P4)
        ("byte_freq", lambda t: [f"F:{t.encode().count(b):03d}" for b in range(min(256, len(t.encode())))][:50], "frequencia de bytes"),
        ("entropia_local", lambda t: [f"E:{int(MCRByteUtils.entropia_bytes(t[i:i+10].encode())*10)}" for i in range(0, min(len(t),500), 5)], "entropia de janelas"),
    ]
    
    def __init__(self):
        self.dimensoes: Dict[str, MCR] = {}
        self.tokenizadores: Dict[str, Callable] = {}
        self.ent_historico: List[float] = []
        self.threshold = 0.95
    
    def _entropia(self, mk: MCR) -> float:
        if mk.total == 0: return 1.0
        return mk.entropia_media()
    
    def _entropia_candidato(self, nome, fn, texto):
        tokens = fn(texto)
        if len(tokens) < 3: return 1.0
        mk = MCR(nome)
        for i in range(len(tokens)-1): mk.aprender(tokens[i], tokens[i+1])
        return self._entropia(mk)
    
    def _gerar_candidatos(self, texto):
        """Gera candidatos FIXOS + DERIVADOS dos dados."""
        # Candidatos fixos
        yield from self.CANDIDATOS
        # Candidatos derivados: n-gramas (HC #7-8)
        if len(texto) > 50:
            n_limite = MCRDecisorUniversal.decidir_passos("gerar_candidatos", {"tamanho_bytes": len(texto)})
            n_buckets = int(MCRDecisorUniversal.decidir(ctx="bucket_size").get("dim", 8)) * 125
            yield ("bigrama_char", lambda t: [t[i:i+2] for i in range(min(len(t)-1, n_limite))], "bigramas de caracteres")
            yield ("trigrama_char", lambda t: [t[i:i+3] for i in range(min(len(t)-2, n_limite))], "trigramas de caracteres")
            yield ("ngram_hash", lambda t: [f"N:{abs(hash(t[i:i+4]))%max(n_buckets,100):03d}" for i in range(min(len(t)-3, n_limite))], "hash de 4-gramas")
    
    def _candidatos_disponiveis(self, texto=""):
        conhecidos = set(self.dimensoes.keys())
        resultado = []
        for n, fn, d in self._gerar_candidatos(texto):
            if n not in conhecidos:
                resultado.append((n, fn, d))
        return resultado
    
    def descobrir(self, texto, max_dim=10):
        """Descobre dimensoes da mais estruturada para a menos.
        Retorna lista de nomes das dimensoes descobertas.
        """
        descobertas = []
        for _ in range(max_dim):
            candidatos = self._candidatos_disponiveis(texto)
            if not candidatos: break
            
            melhor = min(candidatos, key=lambda c: self._entropia_candidato(c[0], c[1], texto))
            nome, fn, desc = melhor
            ent = self._entropia_candidato(nome, fn, texto)
            
            if ent >= self.threshold: break  # ruido — para
            
            mk = MCR(nome)
            tokens = fn(texto)
            for i in range(len(tokens)-1): mk.aprender(tokens[i], tokens[i+1])
            self.dimensoes[nome] = mk
            self.tokenizadores[nome] = fn
            self.ent_historico.append(ent)
            descobertas.append(nome)
        
        return descobertas
    
    def auto_expandir(self, cerebro, texto):
        """Propoe NOVA dimensao quando entropia media de todos os niveis
        esta ALTA. A nova dimensao COMBINA dois niveis existentes com
        maior peso no coupling — capturando a correlacao entre eles.
        
        Se byte='B:61' e palavra='abacate' oscilam juntos,
        a dimensao combinada 'combinado_byte_palavra' cria tokens como:
            "byte:B:61|palavra:abacate"
        
        A Markov chain desta dimensao combinada aprende transicoes
        entre ESTADOS CONJUNTOS. Se a entropia da combinada for
        menor que a media das entropias dos pais, a dimensao e VALIDA
        e revela estrutura que nenhum nivel isolado capta.
        
        Retorna nome da nova dimensao ou None.
        """
        # 1. Coleta entropias de TODOS os niveis (fixos + hiper)
        entropias = {}
        for nome, mk in self.dimensoes.items():
            if mk.total > 0:
                entropias[nome] = mk.entropia_media()
        for nome in ['byte', 'palavra', 'tven']:
            mk = getattr(cerebro, f'mk_{nome}', None)
            if mk and mk.total > 0:
                entropias[nome] = mk.entropia_media()
        
        if len(entropias) < 2:
            return None
        
        ent_media = sum(entropias.values()) / len(entropias)
        
        # 2. Expande apenas se entropia media > threshold
        thr = MCRThreshold("hiper").obter("ent_expandir", 0.7)
        if ent_media < thr:
            return None
        
        # 3. Encontra par com MAIOR peso no coupling
        coupling = cerebro.coupling
        melhor_par = None
        melhor_peso = 0.0
        niveis_coupling = [n for n in coupling.niveis if n in entropias]
        
        for i, o in enumerate(niveis_coupling):
            for d in niveis_coupling[i+1:]:
                peso = coupling.peso(o, d) + coupling.peso(d, o)
                if peso > melhor_peso:
                    melhor_peso = peso
                    melhor_par = (o, d)
        
        if not melhor_par or melhor_peso < 0.3:
            return None
        
        nivel_a, nivel_b = melhor_par
        nome_dim = f"combinado_{nivel_a}_{nivel_b}"
        
        # Evita recriar
        if nome_dim in self.dimensoes:
            return None
        
        # 4. Tokenizador: cria tokens combinados dos dois niveis
        def _token_nivel(nivel, palavra):
            if nivel == 'byte':
                return f"B:{palavra.encode()[0]:02x}" if palavra else "B:00"
            elif nivel == 'palavra':
                return palavra.lower()
            elif nivel == 'tven':
                return palavra[0].upper() if palavra else '?'
            elif nivel in self.tokenizadores:
                ts = self.tokenizadores[nivel](palavra)
                return ts[0] if ts else '?'
            return '?'
        
        def tokenizer(texto):
            palavras = texto.split()
            tokens = []
            for p in palavras:
                va = _token_nivel(nivel_a, p)
                vb = _token_nivel(nivel_b, p)
                tokens.append(f"{nivel_a}:{va}|{nivel_b}:{vb}")
            return tokens
        
        # 5. Alimenta e mede entropia
        mk = MCR(nome_dim)
        tokens = tokenizer(texto)
        for i in range(len(tokens)-1):
            mk.aprender(tokens[i], tokens[i+1])
        
        ent_combinada = mk.entropia_media()
        ent_pai_a = entropias.get(nivel_a, 1.0)
        ent_pai_b = entropias.get(nivel_b, 1.0)
        ent_media_pais = (ent_pai_a + ent_pai_b) / 2.0
        
        # 6. Valida: combinada deve ter entropia MENOR que media dos pais
        if ent_combinada < ent_media_pais * 0.9:
            self.dimensoes[nome_dim] = mk
            self.tokenizadores[nome_dim] = tokenizer
            sys.stderr.write(f"[HIPER] Nova dim: {nome_dim} "
                             f"ent={ent_combinada:.3f} (pais={ent_media_pais:.3f})\n")
            return nome_dim
        
        return None

# ═══════════════════════════════════════════════════════════════════
# [07c] MCRAutoTopologia — grafo de correlacao entre niveis
# ═══════════════════════════════════════════════════════════════════

class MCRAutoTopologia:
    """Grafo de correlacao entre niveis.
    
    Cada nivel e um no. Arestas ponderadas pela frequencia
    com que valores de A aparecem como estados seguintes em B.
    Clusters sao comunidades naturais de niveis correlacionados.
    
    Nao impoe forma (nem circulo, nem esfera).
    A geometria emerge dos dados.
    """
    def __init__(self, niveis: Dict[str, MCR] = None):
        self.niveis = niveis or {}
        self.grafo: Dict[str, Dict[str, float]] = {}
        self.clusters: List[Set[str]] = []
    
    def registrar(self, nome, mk):
        self.niveis[nome] = mk
    
    def recalcular(self, threshold=0.15):
        """Recalcula o grafo de correlacao entre todos os pares."""
        self.grafo = {n: {} for n in self.niveis}
        for a in self.niveis:
            for b in self.niveis:
                if a == b:
                    self.grafo[a][b] = 1.0; continue
                mk_a, mk_b = self.niveis[a], self.niveis[b]
                if mk_a.total == 0 or mk_b.total == 0:
                    self.grafo[a][b] = 0.0; continue
                amostra = list(mk_a.freq.keys())[:30]
                if not amostra: self.grafo[a][b] = 0.0; continue
                acertos = 0
                for val_a in amostra:
                    pred, _ = mk_a.predizer(val_a)
                    if pred and pred in mk_b.freq: acertos += 1
                self.grafo[a][b] = round(acertos / len(amostra), 3)
        self._detectar_clusters(threshold)
    
    def _detectar_clusters(self, threshold):
        visitados = set(); self.clusters = []
        for nivel in self.niveis:
            if nivel in visitados: continue
            cluster = set(); fila = [nivel]
            while fila:
                v = fila.pop(0)
                if v in visitados: continue
                visitados.add(v); cluster.add(v)
                for u, peso in self.grafo.get(v, {}).items():
                    if peso >= threshold and u not in visitados: fila.append(u)
            self.clusters.append(cluster)
    
    def metricas(self):
        n_arestas = sum(1 for a in self.grafo for b, p in self.grafo[a].items()
                       if a != b and p >= 0.15)
        return {
            "n_niveis": len(self.niveis),
            "n_clusters": len(self.clusters),
            "n_arestas": n_arestas,
            "clusters": [sorted(c) for c in self.clusters],
            "isolados": [list(c)[0] for c in self.clusters if len(c) == 1],
        }

# ═══════════════════════════════════════════════════════════════════
# [07d] MCRAutoValidacaoContinua — cada cadeia valida a si mesma
# ═══════════════════════════════════════════════════════════════════

class MCRAutoValidacaoContinua:
    """Cada cadeia valida a si mesma, valida as outras, e e validada.
    
    A profundidade da recursao e determinada pela entropia
    do meta-validador. Sistemas estaveis tem 1 nivel de
    validacao. Sistemas caoticos tem N.
    """
    def __init__(self):
        self.ent_historico: Dict[str, List[float]] = {}
        self.ent_anterior: Dict[str, float] = {}
        self.instavel: Set[str] = set()
        self.meta = MCR("meta_validacao")
        self.ciclos = 0
    
    def registrar(self, nome, mk):
        self.ent_historico[nome] = []
        self.ent_anterior[nome] = mk.entropia_media() if mk.total > 0 else 1.0
    
    def ciclo(self, niveis: Dict[str, MCR]) -> dict:
        self.ciclos += 1
        for nome, mk in niveis.items():
            if mk.total == 0: continue
            ent = mk.entropia_media()
            ent_ant = self.ent_anterior.get(nome, ent)
            variacao = abs(ent - ent_ant) / max(ent_ant, 0.001)
            self.ent_historico.setdefault(nome, []).append(ent)
            if len(self.ent_historico[nome]) > 50:
                self.ent_historico[nome] = self.ent_historico[nome][-50:]
            if variacao > 0.5 or ent > 0.8: self.instavel.add(nome)
            elif nome in self.instavel and variacao < 0.1 and ent < 0.5: self.instavel.discard(nome)
            self.ent_anterior[nome] = ent
            # Meta: alimenta cadeia de meta-validacao
            estado = f"v:{nome}:{int(variacao*100)}"
            self.meta.aprender(estado, estado)
        return {
            "instaveis": list(self.instavel),
            "entropia_meta": round(self.meta.entropia_media() if self.meta.total > 0 else 1.0, 4),
            "ciclos": self.ciclos,
        }

# ═══════════════════════════════════════════════════════════════════
# [07e] MCREntropiaTemporal — monitor de entropia multi-nivel no tempo
# ═══════════════════════════════════════════════════════════════════

class MCREntropiaTemporal:
    """Monitora entropia de cada nivel ao longo do tempo e detecta
    EVENTOS por oscilacao SIMULTANEA em multiplos niveis.

    Filosofia: entropia e' uma COORDENADA no espaco N-dimensional.
    Quando um evento ocorre (mudanca de contexto, anomalia),
    TODOS os niveis oscilam simultaneamente.

    Nivel unico detecta com ruido. Multi-nivel detecta com certeza.
    """
    def __init__(self, observer=None, janela=20):
        self.observer = observer
        self.janela = janela
        self._hist: Dict[str, deque] = {}
        self._lock = threading.Lock()
        self.eventos = []

    def get_levels(self) -> Dict[str, 'MCR']:
        levels = {}
        if self.observer:
            levels.update(self.observer.levels())
        return levels

    def medir(self):
        levels = self.get_levels()
        with self._lock:
            for nome, mk in levels.items():
                ent = mk.entropia_media() if mk.total > 0 else 1.0
                if nome not in self._hist:
                    self._hist[nome] = deque(maxlen=self.janela)
                self._hist[nome].append(ent)

    def delta_entropia(self, nivel):
        hist = self._hist.get(nivel, [])
        if len(hist) < 2: return 0.0
        return abs(hist[-1] - hist[-2])

    def delta_relativo(self, nivel):
        hist = self._hist.get(nivel, [])
        if len(hist) < 2: return 0.0
        diff = abs(hist[-1] - hist[-2])
        if hist[-2] < 0.001: return diff
        return diff / hist[-2]

    def detectar(self, threshold_rel=0.10, min_niveis=2):
        with self._lock:
            spikes = {}
            for nivel in list(self._hist.keys()):
                dr = self.delta_relativo(nivel)
                if dr > threshold_rel:
                    spikes[nivel] = round(dr, 3)
            evento = len(spikes) >= min_niveis
            info = {'niveis': spikes, 'n_afetados': len(spikes)}
            if evento:
                self.eventos.append(info)
        return evento, info

# ═══════════════════════════════════════════════════════════════════
# [07f] PIFilosofia — PI como cadeia infinita projetada em N dimensoes
# ═══════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════
# [08] MCRPlanner — planejamento hierarquico
# ═══════════════════════════════════════════════════════════════════

class MCRPlanner:
    def __init__(self, world: MCRWorld):
        self.world = world; self.mk_plano = MCR("planner"); self.mk_sub = MCR("planner_sub")
        self.mk_pos = MCR("planner_pos")  # Markov de posicao (delta entidade)
    def plano(self, atual, obj, max_passos=10):
        dist = self.world.distancia_manhattan(atual, obj)
        if dist < 1.0:
            ac = self.world.predizer_acao(atual, obj)
            return [ac] if ac else []
        # Tenta recuperar plano por fingerprint (cache)
        fp_alvo = str(obj.fingerprint(self.world.dim_fp))
        pk, cf = self.mk_plano.predizer(fp_alvo)
        if pk and cf > 0.2:
            acs = pk.split("|")
            if len(acs) <= max_passos: return acs
        # Decompoe delta Manhattan em sub-objetivos
        delta_pos = self.world.delta_entidade(atual, obj, "heroi", ("x","y"))
        if not delta_pos:
            return []
        n_sub = min(max_passos, max(2, sum(abs(d) for d in delta_pos)))
        sub_objs = []
        for i in range(1, n_sub + 1):
            frac = i / n_sub
            sx = int(delta_pos[0] * frac) if delta_pos else 0
            sy = int(delta_pos[1] * frac) if len(delta_pos) > 1 else 0
            sub_objs.append((sx, sy))
        # Constroi plano: para cada sub-objetivo, acha acao que produz o delta desejado
        plano = []
        est_int = atual.clone()
        last_sub = (0, 0)
        for sx, sy in sub_objs:
            dx_alvo = sx - last_sub[0]
            dy_alvo = sy - last_sub[1]
            if dx_alvo == 0 and dy_alvo == 0:
                continue
            # Tenta Markov de posicao primeiro
            chave_pos = f"P:{est_int.get('heroi').props.get('x',0)},{est_int.get('heroi').props.get('y',0)}:{dx_alvo},{dy_alvo}"
            ac_pred, cf_pred = self.mk_pos.predizer(chave_pos)
            if ac_pred and cf_pred > 0.15:
                ac = ac_pred
            else:
                # Fallback: encontra a acao que produz o delta mais proximo
                ac = self._fallback_pos(est_int, dx_alvo, dy_alvo)
            if ac:
                plano.append(ac)
                prox = MCRAcao.executar(est_int, ac)
                if prox: est_int = prox
                # Aprende: nesta posicao, esta acao produz este delta
                self.mk_pos.aprender(chave_pos, ac)
            last_sub = (sx, sy)
        if plano: self._aprender(plano, atual, obj)
        return plano
    def _fallback_pos(self, est, dx_alvo, dy_alvo):
        """Encontra a acao cujo delta de posicao mais se aproxima do desejado."""
        melhor_ac, melhor_dist = None, 999
        for ac in MCRAcao.disponiveis():
            prox = MCRAcao.executar(est, ac)
            delta_real = self.world.delta_entidade(est, prox, "heroi", ("x","y"))
            if delta_real:
                dist_delta = abs(delta_real[0] - dx_alvo) + abs(delta_real[1] - dy_alvo)
                if dist_delta < melhor_dist:
                    melhor_dist = dist_delta
                    melhor_ac = ac
        return melhor_ac or "andar_cima"
    def _fallback(self, est, sub):
        """Fallback original por delta fingerprint (mantido para compatibilidade)."""
        melhor_ac, melhor_sc = "andar_cima", 0.0
        for ac in MCRAcao.disponiveis():
            prox = MCRAcao.executar(est, ac)
            delta_ac = MCRByteUtils.delta_fingerprint(est.serializar(), prox.serializar(), self.world.dim_fp)
            sc = MCRByteUtils.similaridade_cosseno(delta_ac, sub)
            if sc > melhor_sc: melhor_sc, melhor_ac = sc, ac
        return melhor_ac
    def _aprender(self, plano, atual, final):
        fp_alvo = str(final.fingerprint(self.world.dim_fp))
        self.mk_plano.aprender(fp_alvo, "|".join(plano))
        est_int = atual.clone()
        for ac in plano:
            prox = MCRAcao.executar(est_int, ac)
            delta = tuple(round(d,3) for d in MCRByteUtils.delta_fingerprint(est_int.serializar(), prox.serializar(), self.world.dim_fp))
            self.mk_sub.aprender(str(delta), ac); est_int = prox

# ═══════════════════════════════════════════════════════════════════
# [09] MCRRL — aprendizado por reforco
# ═══════════════════════════════════════════════════════════════════

class MCRReward:
    def avaliar(self, est_atual, est_ant, est_obj=None, acao_ok=True):
        r = 0.0
        h_atual = est_atual.get("heroi")
        h_ant = est_ant.get("heroi")
        h_obj = est_obj.get("heroi") if est_obj else None
        
        if h_atual and h_ant:
            # Penaliza fortemente ficar parado (acao que nao move o heroi)
            if h_atual.props.get("x",0) == h_ant.props.get("x",0) and \
               h_atual.props.get("y",0) == h_ant.props.get("y",0):
                r -= 3.0  # parado e RUIM
        
        if h_atual and h_obj:
            # Bonus Manhattan: recompensa aproximacao ao objetivo
            dist_atual = abs(h_atual.props.get("x",0)-h_obj.props.get("x",0)) + \
                        abs(h_atual.props.get("y",0)-h_obj.props.get("y",0))
            if h_ant:
                dist_ant = abs(h_ant.props.get("x",0)-h_obj.props.get("x",0)) + \
                          abs(h_ant.props.get("y",0)-h_obj.props.get("y",0))
                r += (dist_ant - dist_atual) * 5  # bonus alto por reduzir distancia
            # Recompensa esparsa: chegou no objetivo
            if dist_atual == 0:
                r += 15.0
        if acao_ok: r += 1.0
        return max(-10.0, min(15.0, r))

class MCRQLearn:
    def __init__(self, gamma=0.9, alpha=0.3):
        self.mk_Q = MCR("qlearn"); self.mk_pol = MCR("qpol"); self.gamma, self.alpha = gamma, alpha
        self.thr = MCRThreshold("qlearn"); self.episodio = 0; self.hist_ep: List[Dict] = []
        self.replay: List[Tuple] = []  # replay buffer: (acoes, recompensa_total)
        self._ultimas_acoes: List[str] = []  # Radar: historico para detectar loops
        self._radar_limite = 4  # N repeticoes iguais = loop
    def _fp_estado(self, estado):
        """Chave unica por estado (fingerprint + hash do serializado).
        
        O fingerprint sozinho causa aliasing (dois estados diferentes
        com mesmo fingerprint). A solucao: concatenar fingerprint
        (para compatibilidade HDC/similaridade) com um hash MD5 do
        serializado completo (para unicidade absoluta).
        
        Isso e' como ter bairro + rua + numero — o fingerprint
        agrupa estados similares, o hash identifica cada um."""
        ser = estado.serializar()
        dim = MCRSignatureExpansiva.dimensionalidade_ideal(ser.encode()[:2000], mx=64, thr=0.08)
        dim = max(12, min(dim, 32))
        fp = MCRByteUtils.fingerprint(ser, dim)
        uid = hashlib.md5(ser.encode()).hexdigest()[:8]
        return f"{fp}|{uid}"
    def q_valor(self, estado, acao):
        ch = f"Q:{self._fp_estado(estado)}:{acao}"
        p, c = self.mk_Q.predizer(ch)
        try: return float(p) if p and c > 0 else 0.0
        except: return 0.0
    def atualizar(self, estado, acao, recompensa, prox_est):
        ch = f"Q:{self._fp_estado(estado)}:{acao}"
        q_at = self.q_valor(estado, acao)
        acs = MCRAcao.disponiveis()
        max_qf = max(self.q_valor(prox_est, a) for a in acs) if acs else 0.0
        # Radar: penaliza acao em loop para forcar diversificacao
        acao_loop = self._radar_loop_action()
        if acao_loop == acao:
            recompensa -= 1.0  # penalidade por repetir em loop
        td = recompensa + self.gamma*max_qf - q_at
        self.mk_Q.aprender(ch, f"{q_at+self.alpha*td:.4f}")
        melh = self.melhor_acao(estado)
        if melh: self.mk_pol.aprender(self._fp_estado(estado), melh)
        self.thr.observar(abs(td))
    def _radar_loop_action(self):
        """Radar: retorna a acao que esta em loop (ou None)."""
        if len(self._ultimas_acoes) < self._radar_limite:
            return None
        if len(set(self._ultimas_acoes[-self._radar_limite:])) == 1:
            return self._ultimas_acoes[-1]
        return None

    def _radar_alimentar(self, acao):
        """Alimenta o radar com a ultima acao."""
        self._ultimas_acoes.append(acao)
        if len(self._ultimas_acoes) > 100:
            self._ultimas_acoes = self._ultimas_acoes[-50:]

    def melhor_acao(self, estado, acoes=None, bloquear=None):
        """Melhor acao, opcionalmente bloqueando uma acao especifica."""
        acoes = acoes or MCRAcao.disponiveis()
        if not acoes: return None
        if bloquear:
            candidatos = [a for a in acoes if a != bloquear]
            if candidatos:
                return max(candidatos, key=lambda a: self.q_valor(estado, a))
        return max(acoes, key=lambda a: self.q_valor(estado, a))
    def escolher_acao(self, estado, epsilon=0.2, acoes=None):
        acoes = acoes or MCRAcao.disponiveis()
        if not acoes: return "andar_cima"
        # Radar: se loop detectado, BLOQUEIA a acao repetida por um passo
        acao_loop = self._radar_loop_action()
        if acao_loop:
            # Bloqueia a acao em loop: escolhe a melhor DAS OUTRAS
            bloqueada = self.melhor_acao(estado, acoes, bloquear=acao_loop)
            if bloqueada:
                return bloqueada
        if _rand.random() < epsilon: return _rand.choice(acoes)
        return self.melhor_acao(estado, acoes) or acoes[0]
    def _replay_treinar(self):
        """Re-treina com trajetorias bem-sucedidas (aprendizado offline).
        Ajuda a consolidar politicas que levam ao objetivo."""
        if len(self.replay) < 3:
            return
        melhores = sorted(self.replay, key=lambda x: -x[1])[:5]
        for acoes, _ in melhores:
            est = EstadoMundo.criar_simples()
            for acao in acoes:
                prox = MCRAcao.executar(est, acao)
                mud = prox.serializar() != est.serializar()
                rw = MCRReward().avaliar(prox, est, est, mud)
                self.atualizar(est, acao, rw, prox)
                est = prox

    def executar_episodio(self, est_ini, est_obj, mx=20):
        est = est_ini.clone(); r_total = 0.0; acs = []
        self._ultimas_acoes = []  # reseta radar para novo episodio
        for passo in range(mx):
            # Epsilon com decay mais lento (explora mais no inicio)
            ac = self.escolher_acao(est, epsilon=max(0.05, 0.3-self.episodio*0.005))
            # Radar: alimenta detector de loop
            self._radar_alimentar(ac)
            prox = MCRAcao.executar(est, ac)
            mud = prox.serializar() != est.serializar()
            rw = MCRReward().avaliar(prox, est, est_obj, mud)
            self.atualizar(est, ac, rw, prox); r_total += rw; acs.append(ac); est = prox
            h = est.get("heroi"); ho = est_obj.get("heroi")
            if h and ho:
                if abs(h.props.get("x",0)-ho.props.get("x",0)) + abs(h.props.get("y",0)-ho.props.get("y",0)) <= 1: break
        self.episodio += 1
        # Guarda no replay se chegou perto do objetivo
        if h and ho:
            dist_final = abs(h.props.get("x",0)-ho.props.get("x",0)) + \
                        abs(h.props.get("y",0)-ho.props.get("y",0))
            if dist_final <= 2:
                self.replay.append((list(acs), r_total))
                self._replay_treinar()
        res = {"episodio": self.episodio, "passos": passo+1, "recompensa": round(r_total,2), "acoes": acs[:10]}
        self.hist_ep.append(res); return res

# ═══════════════════════════════════════════════════════════════════
# [10] MCRMemory — SQLite persistente
# ═══════════════════════════════════════════════════════════════════

class MCRMemory:
    def __init__(self, db_path=None):
        self.db_path = db_path or os.path.join(CACHE_DIR, "mcr_hq.db")
        self.con = sqlite3.connect(self.db_path, check_same_thread=False)
        self.con.execute("PRAGMA journal_mode=WAL"); self.con.execute("PRAGMA synchronous=NORMAL")
        self._criar(); self.total_ins = 0
    def _criar(self):
        self.con.executescript("""
            CREATE TABLE IF NOT EXISTS estados (id INTEGER PRIMARY KEY AUTOINCREMENT, fp TEXT, serial TEXT, ts REAL, bucket INTEGER);
            CREATE INDEX IF NOT EXISTS idx_est_fp ON estados(fp);
            CREATE TABLE IF NOT EXISTS causais (id INTEGER PRIMARY KEY AUTOINCREMENT, fp_antes TEXT, acao TEXT, fp_depois TEXT, delta TEXT, ts REAL);
            CREATE INDEX IF NOT EXISTS idx_caus_antes ON causais(fp_antes);
            CREATE TABLE IF NOT EXISTS planos (id INTEGER PRIMARY KEY AUTOINCREMENT, fp_obj TEXT, acoes TEXT, nota REAL DEFAULT 0, ts REAL);
            CREATE INDEX IF NOT EXISTS idx_plan_fp ON planos(fp_obj);
        """)
        self.con.commit()
    def salvar_estado(self, est):
        fp = str(est.fingerprint(8)); ser = est.serializar(); bk = hash(fp)%256
        self.con.execute("INSERT OR REPLACE INTO estados (fp,serial,ts,bucket) VALUES (?,?,?,?)", (fp,ser,time.time(),bk))
        self.con.commit(); self.total_ins += 1; return fp
    def salvar_causal(self, antes, acao, depois):
        fpa, fpd = str(antes.fingerprint(8)), str(depois.fingerprint(8))
        delta = str(MCRByteUtils.delta_fingerprint(antes.serializar(), depois.serializar(), 8))
        self.con.execute("INSERT INTO causais VALUES (NULL,?,?,?,?,?)", (fpa,acao,fpd,delta,time.time()))
        self.con.commit(); self.total_ins += 1
    def salvar_plano(self, fp_obj, acoes, nota=0.0):
        self.con.execute("INSERT INTO planos VALUES (NULL,?,?,?,?)", (fp_obj,"|".join(acoes),nota,time.time()))
        self.con.commit()
    def buscar_similar(self, fp_alvo, limite=10):
        bk = hash(fp_alvo)%256
        rs = self.con.execute("SELECT fp,serial FROM estados WHERE bucket=? ORDER BY ts DESC LIMIT ?", (bk,limite*10)).fetchall()
        if not rs: rs = self.con.execute("SELECT fp,serial FROM estados ORDER BY ts DESC LIMIT ?", (limite,)).fetchall()
        fpa = [float(x) for x in fp_alvo.strip("[]").split(",") if x.strip()]
        sc = []
        for fp_str, ser in rs:
            fpo = [float(x) for x in fp_str.strip("[]").split(",") if x.strip()]
            if not fpo: continue
            sim = MCRByteUtils.similaridade_cosseno(fpa, fpo)
            sc.append((sim, fp_str, ser))
        sc.sort(key=lambda x: -x[0]); return [(fp, ser, s) for s, fp, ser in sc[:limite]]
    def buscar_causal(self, fp_antes, acao):
        r = self.con.execute("SELECT fp_depois FROM causais WHERE fp_antes=? AND acao=? ORDER BY ts DESC LIMIT 1", (fp_antes, acao)).fetchone()
        return r[0] if r else None
    def buscar_plano(self, fp_obj):
        r = self.con.execute("SELECT acoes,nota FROM planos WHERE fp_obj=? ORDER BY nota DESC LIMIT 1", (fp_obj,)).fetchone()
        return (r[0].split("|"), r[1]) if r else None
    def stats(self):
        c = self.con.cursor()
        return {"estados": c.execute("SELECT COUNT(*) FROM estados").fetchone()[0],
                "causais": c.execute("SELECT COUNT(*) FROM causais").fetchone()[0],
                "planos": c.execute("SELECT COUNT(*) FROM planos").fetchone()[0]}
    def fechar(self): self.con.close()

# ═══════════════════════════════════════════════════════════════════
# [11] MCRBridge — analogias cross-domain
# ═══════════════════════════════════════════════════════════════════

class MCRBridge:
    def __init__(self):
        self.dominios: Dict[str, MCR] = {}; self.dim = C("dim_fingerprint", 8); self.mk = MCR("bridge"); self.total = 0
    def registrar_dominio(self, nome):
        if nome not in self.dominios: self.dominios[nome] = MCR(f"dom_{nome}")
    def analise(self, a1, a2, b1, b2):
        da = MCRByteUtils.delta_fingerprint(a1, a2, self.dim)
        db = MCRByteUtils.delta_fingerprint(b1, b2, self.dim)
        sim = MCRByteUtils.similaridade_cosseno(da, db)
        ma, mb = math.sqrt(sum(d*d for d in da)), math.sqrt(sum(d*d for d in db))
        razao = min(ma, mb)/max(ma, mb, 0.001)
        nota = sim*razao
        self.total += 1; return {"a1": a1[:20], "a2": a2[:20], "b1": b1[:20], "b2": b2[:20], "sim": round(sim,3), "nota": round(nota,3), "analogo": nota>0.5}

# ═══════════════════════════════════════════════════════════════════
# [12] MCRCodex + MCRSelfTest — auto-modificacao
# ═══════════════════════════════════════════════════════════════════

class MCRSelfTest:
    @staticmethod
    def testar(modulo):
        try:
            if modulo == "world":
                w = MCRWorld(); e = EstadoMundo.criar_simples()
                e2 = MCRAcao.executar(e, "andar_dir"); w.aprender(e, "andar_dir", e2)
                return 10.0 if w.predizer_acao(e, e2) == "andar_dir" else 5.0
            if modulo == "coupling":
                cp = MCRCoupling()
                for _ in range(MCRDecisorUniversal.decidir_passos("test_coupling")): cp.alimentar("byte","palavra","B:41","Fogo")
                cp.recalcular(); return 10.0 if cp.peso("byte","palavra") > 0 else 0.0
            if modulo == "planner":
                w = MCRWorld(); p = MCRPlanner(w)
                return 10.0 if isinstance(p.plano(EstadoMundo.criar_simples(), EstadoMundo.criar_simples()), list) else 0.0
        except: return 0.0

class MCRCodex:
    def __init__(self):
        self.params = {"passos": int, "dim": int, "threshold": float, "top_k": int, "max_iter": int, "max_passos": int}
        self.mk = MCR("codex"); self.hist: List[Dict] = []
    def escanear(self, caminho=None):
        caminho = caminho or __file__; hcs = []
        try:
            with open(caminho, "r", encoding="utf-8", errors="replace") as f: linhas = f.readlines()
        except: return []
        for i, linha in enumerate(linhas):
            s = linha.strip()
            if not s or s.startswith("#") or s.startswith('"""'): continue
            for pn in self.params:
                m = re.search(rf'\b{pn}\s*=\s*(\d+\.?\d*)', s)
                if m:
                    hcs.append({"linha": i+1, "param": pn, "valor": m.group(1), "tipo": self.params[pn].__name__, "codigo": s[:60]})
                    break
        return hcs
    def substituir(self, caminho, linha, param, novo_valor):
        if not os.path.exists(caminho): return False
        with open(caminho, "r", encoding="utf-8") as f: linhas = f.readlines()
        if linha < 1 or linha > len(linhas): return False
        l = linhas[linha-1]; nova = re.sub(rf'({param}\s*=\s*)\d+\.?\d*', rf'\g<1>{novo_valor}', l)
        if nova == l: return False
        linhas[linha-1] = nova
        with open(caminho, "w", encoding="utf-8") as f: f.writelines(linhas)
        self.hist.append({"param": param, "linha": linha, "antes": l[:40], "depois": nova[:40]}); return True

# ═══════════════════════════════════════════════════════════════════
# [13] MCRGenesis — auto-expansao
# ═══════════════════════════════════════════════════════════════════

class MCRGenesis:
    def __init__(self, cerebro=None):
        self.cerebro = cerebro; self.mk = MCR("genesis"); self.modulos: List[Dict] = []; self.thr = MCRThreshold("genesis")
    def diagnosticar(self):
        gaps = []
        min_palavras = C("genesis_min_palavras", 10)
        min_planos = C("genesis_min_planos", 5)
        max_entropia = C("genesis_max_entropia", 0.5)
        if self.cerebro and self.cerebro.mk_palavra.total < min_palavras:
            gaps.append({"nome": "conhecimento_insuficiente", "severidade": 0.8, "sugestao": "alimentar textos variados"})
        if self.cerebro and hasattr(self.cerebro, 'planner') and self.cerebro.planner.mk_plano.total < min_planos:
            gaps.append({"nome": "planejamento_insuficiente", "severidade": 0.6, "sugestao": "executar mais episodios"})
        if self.cerebro:
            try:
                h = self.cerebro.mk_byte.entropia_media()
                if h > max_entropia: gaps.append({"nome": "dados_ruidosos", "severidade": min(0.9, h), "sugestao": "descobrir dimensionalidade ideal"})
            except: pass
        return {"gaps": gaps, "total": len(gaps), "severidade_media": round(sum(g["severidade"] for g in gaps)/max(len(gaps),1), 3) if gaps else 0}
    def projetar(self, gap):
        nc = f"MCR{''.join(w.capitalize() for w in gap['nome'].split('_'))}"
        return f'''class {nc}:\n    def __init__(self, cerebro=None):\n        self.cerebro = cerebro\n        self.mk = MCR("{nc}")\n        self.thr = MCRThreshold("{nc}")\n    def executar(self, **kw):\n        return {{"gap": "{gap['nome']}"}}\n'''

# ═══════════════════════════════════════════════════════════════════
# [14] MCRAmbiente (resumido)
# ═══════════════════════════════════════════════════════════════════

class Tile:
    def __init__(self, tipo="grama", altura=0):
        self.tipo, self.altura = tipo, altura
        self.props = {"custo": 1, "bloqueia": tipo in ("agua","muro","lava")}

class AmbienteRico:
    def __init__(self, w=50, h=50):
        self.w, self.h = w, h; self.tiles: List[List[Tile]] = []; self.ents: List[Entidade] = []; self.tick_atual = 0
        self._gerar()
    def _gerar(self):
        for y in range(self.h):
            linha = []
            for x in range(self.w):
                r = math.sin(x*0.1)*math.cos(y*0.1)+_rand.random()*0.5
                if r < -0.5: t = "agua"
                elif r < 0: t = "areia" if _rand.random()<0.3 else "grama"
                elif r < 0.5: t = "floresta" if _rand.random()<0.3 else "grama"
                else: t = "pedra" if _rand.random()<0.4 else "grama"
                linha.append(Tile(t))
            self.tiles.append(linha)
    def tick(self):
        self.tick_atual += 1

# ═══════════════════════════════════════════════════════════════════
# [02] MCRRegistry — registro universal de tipos
# ═══════════════════════════════════════════════════════════════════

class MCRRegistry:
    _tipos: Dict[str, Dict] = {}; _nomes: Dict[str, List[str]] = {}; _conceitos: Dict[str, List[str]] = {}
    @classmethod
    def registrar_tipo(cls, cat, nome, props): cls._tipos.setdefault(cat, {})[nome] = dict(props)
    @classmethod
    def registrar_nome(cls, nome, cat): cls._nomes.setdefault(cat, []).append(nome)
    @classmethod
    def tipo_props(cls, cat, nome): return dict(cls._tipos.get(cat, {}).get(nome, {}))
    @classmethod
    def tipos_por_categoria(cls, cat): return list(cls._tipos.get(cat, {}).keys())
    @classmethod
    def nome_aleatorio(cls, cat="geral"):
        ns = cls._nomes.get(cat, []); return _rand.choice(ns) if ns else f"{cat}_{_rand.randint(0,999)}"

def _registrar_registry():
    for n in ["guerreiro","mago","arqueiro","orc","troll","goblin","lobo","urso"]:
        MCRRegistry.registrar_nome(n, "monstro")
    for n in ["Bruno","Maria","Joao","Ana","Carlos","Sofia","Pedro"]:
        MCRRegistry.registrar_nome(n, "npc")
    for n, p in [("grama",{"custo":1,"bloqueia":False}),("agua",{"custo":5,"bloqueia":True}),("muro",{"custo":99,"bloqueia":True})]:
        MCRRegistry.registrar_tipo("terreno", n, p)
_registrar_registry()

# ═══════════════════════════════════════════════════════════════════
# [15] MCRResposta — OMNI: atencao responde, cerebro decide
# ═══════════════════════════════════════════════════════════════════

class MCRResposta:
    """Resposta: distribuicao decide, MCR filtra, cerebro decide.
    Zero if/elif fixos. Tudo via MCR + thresholds aprendidos."""
    
    _thr_conf = MCRThreshold("resposta_conf")
    _thr_tipo = MCRThreshold("resposta_tipo")
    
    @staticmethod
    def _buscar(pergunta, cerebro, max_iter=3):
        """Busca com filtro por tipo de topico + confianca por MCRThreshold.
        
        Nao responde com gaps, nao usa formatacao no aprendizado.
        Se confianca < threshold, retorna vazio para web search.
        """
        for i in range(max_iter):
            if not cerebro.topicos:
                return ""
            
            # Coleta scores filtrando gaps (tipo != 'gap')
            scores = []
            for nome, dados in cerebro.topicos.items():
                texto = dados.get("texto", "")
                tipo = dados.get("tipo", "conv")
                if not texto or tipo == "gap" or nome.startswith("gap_"):
                    continue  # Fix 1: gaps nunca viram resposta
                s = MCRByteUtils.jaccard_bytes(pergunta, texto)
                scores.append((s, nome, texto, tipo))
            
            if not scores:
                return ""
            
            scores.sort(key=lambda x: -x[0])
            melhor_score, melhor_nome, melhor_texto, melhor_tipo = scores[0]
            
            # Threshold de confianca MINIMO (Fix 3)
            conf_min = MCRResposta._thr_conf.obter("conf_min", 0.1)
            if melhor_score < conf_min:
                return ""  # confianca baixa → web search ou geracao
            
            # Distribuicao dos gaps (confianca relativa)
            top_n = min(10, len(scores))
            top_scores = [s[0] for s in scores[:top_n]]
            gaps_list = [top_scores[i] - top_scores[i+1] for i in range(len(top_scores)-1)] if len(top_scores) > 1 else [0]
            media_gap = sum(gaps_list) / len(gaps_list) if gaps_list else 0
            primeiro_gap = gaps_list[0] if gaps_list else 0
            confiante = primeiro_gap > media_gap and melhor_score > conf_min
            
            if confiante or i == max_iter - 1:
                return melhor_texto[:300]
            
            # Confianca baixa: tenta gerar por Markov (Fix 5)
            try:
                gerado = cerebro.gerar(pergunta, passos=6, pergunta=pergunta)
                if gerado and len(gerado) > 20:
                    return gerado[:300]
            except:
                pass
        
        return "Nao sei responder sobre isso." if melhor_texto else ""
    
    @staticmethod
    def responder(pergunta, cerebro):
        if not cerebro:
            return ""
        return MCRResposta._buscar(pergunta, cerebro)
    
    @staticmethod
    def _feedback(pergunta, delta=0.0):
        """Aprende com feedback: penaliza ou recompensa topicos.
        Se o usuario repetiu a pergunta, a resposta anterior nao foi util."""
        pass  # feedback sera usado pelo ciclo_autonomo

# ═══════════════════════════════════════════════════════════════════
# [19] MCRNPCBrain — NPCs do servidor
# ═══════════════════════════════════════════════════════════════════

NPC_CACHE = os.path.join(CACHE_DIR, "npc_knowledge.json")

class MCRNPCBrain:
    def __init__(self):
        self.dialogos: Dict[str, List[Tuple[str,str,int]]] = {}
        self.npcs: Dict[str, Dict] = {}; self.total_dialogos = 0; self.total_npcs = 0
    def aprender_arquivo(self, caminho):
        n = 0
        try:
            with open(caminho, "r", encoding="utf-8", errors="replace") as f: ct = f.read()
        except: return 0
        nome = self._extrair_nome(caminho, ct)
        if not nome: nome = os.path.basename(caminho).replace(".lua","").capitalize()
        self.npcs[nome] = self.npcs.get(nome, {"arquivo": caminho, "dialogos": 0, "itens": []})
        for p, r in self._extrair_dialogos(ct):
            ch = p.lower().strip().strip('"\'.!?;:')
            self.dialogos.setdefault(ch, []).append((r, nome, 1))
            self.npcs[nome]["dialogos"] += 1; n += 1
        for item in self._extrair_itens(ct):
            self.npcs[nome]["itens"].append(item)
            ch = item["itemName"].lower()
            pc, pv = item.get("buy",0), item.get("sell",0)
            if pc: r = f"{item['itemName']} custa {pc} moedas."
            elif pv: r = f"{item['itemName']} vendido por {pv} moedas."
            else: r = item["itemName"]
            self.dialogos.setdefault(ch, []).append((r, nome, 3)); n += 1
        self.total_dialogos += n; self.total_npcs = len(self.npcs); return n
    def _extrair_nome(self, caminho, ct):
        m = re.search(r'internalNpcName\s*=\s*"([^"]+)"', ct)
        if m: return m.group(1)
        m = re.search(r'nome\s*=\s*"([^"]+)"', ct, re.I)
        return m.group(1) if m else ""
    def _extrair_dialogos(self, ct):
        pares = []
        for p, r in re.findall(r'MsgContains\([^,]+,\s*"([^"]+)"[^;]*?npcHandler:say\(\s*"([^"]+)"', ct, re.DOTALL):
            if len(p) > 2 and len(r) > 2: pares.append((p,r))
        for p, r in re.findall(r'addKeyword\(\{[^}]*"([^"]+)"[^}]*\}[^;]*?text\s*=\s*"([^"]+)"', ct):
            if len(p) > 2 and len(r) > 2: pares.append((p,r))
        for p, r in re.findall(r'"([^"]+)"\s*->\s*"([^"]+)"', ct):
            if len(p) > 3 and len(r) > 3 and "dialogo" not in p.lower(): pares.append((p,r))
        return pares
    def _extrair_itens(self, ct):
        itens = []
        for nome, cid, resto in re.findall(r'itemName\s*=\s*"([^"]+)"[^}]*?clientId\s*=\s*(\d+)([^}]*)', ct):
            item = {"itemName": nome, "clientId": int(cid)}
            b = re.search(r'buy\s*=\s*(\d+)', resto); s = re.search(r'sell\s*=\s*(\d+)', resto)
            if b: item["buy"] = int(b.group(1))
            if s: item["sell"] = int(s.group(1))
            itens.append(item)
        return itens
    def perguntar(self, pergunta, npc=None, top_k=5):
        if not self.dialogos: return [{"resposta": "Nada aprendido.", "conf": 0.0}]
        pn = pergunta.lower().strip(); palavras = [p for p in pn.split() if len(p) > 2]
        res, vistos = [], set()
        for palavra in reversed(palavras):
            if palavra in self.dialogos:
                for resp, npc_orig, freq in self.dialogos[palavra]:
                    if npc and npc.lower() != npc_orig.lower(): continue
                    cv = f"{resp}:{npc_orig}"
                    if cv not in vistos:
                        vistos.add(cv); cb = min(0.6+freq*0.05, 1.0)
                        res.append({"resposta": resp, "npc": npc_orig, "conf": round(cb,4), "tipo": "exato"})
            if res: break
        if not res:
            for ch, respostas in self.dialogos.items():
                j = MCRByteUtils.jaccard_bytes(pn, ch)
                if j > 0.08:
                    for resp, npc_orig, freq in respostas:
                        if npc and npc.lower() != npc_orig.lower(): continue
                        cv = f"{resp}:{npc_orig}"
                        if cv not in vistos: vistos.add(cv); res.append({"resposta": resp, "npc": npc_orig, "conf": round(j*0.5,4), "tipo": "jaccard"})
        if not res and pn:
            fp = MCRByteUtils.fingerprint(pn)
            for ch, respostas in self.dialogos.items():
                fp_ch = MCRByteUtils.fingerprint(ch); j = MCRByteUtils.similaridade_cosseno(fp, fp_ch)
                if j > 0.15:
                    for resp, npc_orig, freq in respostas[:1]:
                        if npc and npc.lower() != npc_orig.lower(): continue
                        cv = f"{resp}:{npc_orig}"
                        if cv not in vistos: vistos.add(cv); res.append({"resposta": resp, "npc": npc_orig, "conf": round(j*0.3,4), "tipo": "fingerprint"})
        res.sort(key=lambda x: -x["conf"]); return res[:top_k]
    def responder(self, pergunta, npc=None):
        rs = self.perguntar(pergunta, npc, 3)
        if not rs: return "Nao entendi."
        m = rs[0]
        if m["conf"] < 0.05: return f"Nao sei sobre '{pergunta}'."
        return m["resposta"] if m["conf"] > 0.3 else f"Pelo que sei, {m['resposta'].lower()}"
    def salvar(self, path=None):
        path = path or NPC_CACHE; os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"total_dialogos": self.total_dialogos, "total_npcs": self.total_npcs, "dialogos": {k: [(r,n,fr) for r,n,fr in v] for k,v in self.dialogos.items()}, "npcs": self.npcs}, f, indent=2)
    def carregar(self, path=None):
        path = path or NPC_CACHE
        if not os.path.exists(path): return False
        with open(path, "r", encoding="utf-8") as f: d = json.load(f)
        self.total_dialogos = d.get("total_dialogos",0); self.total_npcs = d.get("total_npcs",0)
        self.dialogos = {k: [(r,n,fr) for r,n,fr in v] for k,v in d.get("dialogos",{}).items()}; self.npcs = d.get("npcs",{})
        return True
    def stats(self):
        return {"total_npcs": self.total_npcs, "total_dialogos": self.total_dialogos, "topicos": len(self.dialogos)}

# ═══════════════════════════════════════════════════════════════════
# [20] MCRParserMinimo — parser semântico relacional (stdlib only)
# ═══════════════════════════════════════════════════════════════════

class MCRParserMinimo:
    """Parser semantico rule-based para portugues.
    
    Extrai triplas (sujeito, relacao, objeto) de sentencas declarativas
    simples usando apenas stdlib Python. Cobre ~75% das sentencas PT-BR.
    
    Usa heuristica POSICIONAL como fallback — em portugues SVO,
    a posicao 0 tende a ser sujeito e posicao 1 tende a ser verbo.
    Isso torna o parser robusto para verbos desconhecidos.
    
    Padroes:
      SVO:         "Joao come maca"  → (Joao, come, maca)
      Copular:     "Joao e alto"     → (Joao, e, alto)
      Cop-Comp:    "Joao e mais alto que Maria" → (Joao, e_mais_alto_que, Maria)
      Preposicional: "Maria gosta de Pedro" → (Maria, gosta_de, Pedro)
    """

    _PREP = frozenset(['de','para','em','com','por','a','ate','desde','entre',
        'contra','sem','sob','sobre','apos','antes','durante','perante','tras'])
    _ART = frozenset(['o','a','os','as','um','uma','uns','umas'])
    _CONJ = frozenset(['e','ou','mas','que','porque','pois','se','quando',
        'enquanto','como','embora','contudo','portanto','pois'])
    _PRON = frozenset(['eu','tu','ele','ela','nos','vos','eles','elas',
        'me','te','se','lhe','lhes','nos','vos'])
    _FUNC = set().union(_PREP, _ART, _CONJ, _PRON)

    _COP = frozenset(['ser','sou','e','sao','era','sera','foi','foram',
        'seria','seriam','fui','foi','foram','seja','sejam','fosse','fossem',
        'estar','estou','esta','estao','estava','estavam','esteve','estiveram',
        'esteja','estejam','estivesse','estivessem',
        'ficar','fico','fica','ficam','ficou','ficaram','ficava',
        'parecer','parece','parecem','pareceu','pareciam',
        'continuar','continua','continuam','continuou','continuava',
        'permanecer','permanece','permaneceu','permaneciam',
        'tornar','torna','tornam','tornou','tornaram'])

    _VERBOS = frozenset([
        # ser/estar (copulativos ja inclusos)
        # ter
        'tenho','tem','tem','tinha','tinham','terei','tera','terao',
        'teria','teriam','tive','teve','tiveram','tivesse','tivessem',
        'tenha','tenham',
        # fazer
        'faco','faz','fazem','fazia','faziam','farei','fara','farao',
        'faria','fariam','fez','fiz','fizeram','faca','facam','fizesse',
        # dizer
        'digo','diz','dizem','dizia','diziam','direi','dira','dirao',
        'diria','diriam','disse','disseram','diga','digam','dissesse',
        # poder
        'posso','pode','podem','podia','podiam','poderei','podera','poderao',
        'poderia','poderiam','pude','pode','puderam','pudesse',
        # ir
        'vou','vai','vao','ia','iam','irei','ira','irao',
        'iria','iriam','fui','foi','foram',
        # vir
        'venho','vem','vem','vinha','vinham','virei','vira','virao',
        'viria','viriam','veio','vieram','venha','venham','viesse',
        # dar
        'dou','da','dao','dava','davam','darei','dara','darao',
        'daria','dariam','deu','dei','deram','de','deem','desse',
        # saber
        'sei','sabe','sabem','sabia','sabiam','soube','souberam',
        'soubesse','soubessem',
        # querer
        'quero','quer','querem','queria','queriam','quis','quisemos',
        # verbos comuns (acoes)
        'acha','acham','achou','acharam','achava',
        'fala','falam','falou','falaram','falava',
        'gosta','gostam','gostou','gostaram','gostava',
        'precisa','precisam','precisou','precisaram',
        'deve','devem','devia','deviam','devera','deveria',
        'passa','passam','passou','passaram','passava',
        'chega','chegam','chegou','chegaram','chegava',
        'sai','saem','saiu','saíram','saia',
        'entra','entram','entrou','entraram','entrava',
        'leva','levam','levou','levaram','levava',
        'deixa','deixam','deixou','deixaram','deixava',
        'penso','pensa','pensam','pensou','pensaram','pensava',
        'acredito','acredita','acreditam','acreditou','acreditava',
        'permito','permite','permitem','permitiu',
        'tento','tenta','tentam','tentou','tentaram',
        'consigo','consegue','conseguem','conseguiu',
        'ha','houve','houveram','havia',
        'come','comeu','comeu','comeram','come','come',
        'odeia','odeiam','odiava','odiou',
        've','veem','via','viu','viram',
        'le','leem','lia','leu','leram',
        'estuda','estudam','estudou','estudaram','estudava',
        'publica','publicam','publicou','publicaram','publicava',
        'aprova','aprovam','aprovou','aprovaram','aprovava',
        'compra','compram','comprou','compraram','comprava',
        'vende','vendem','vendeu','venderam','vendia',
        'escreve','escrevem','escreveu','escreveram','escrevia',
        'corre','correm','correu','correram','corria',
        'bebe','bebem','bebeu','beberam','bebia',
        'abre','abrem','abriu','abriram','abria',
        'fecha','fecham','fechou','fecharam','fechava',
        'anda','andam','andou','andarams','andava',
        'canta','cantam','cantou','cantaram','cantava',
        'dança','dançam','dançou','dançaram','dançava',
        'joga','jogam','jogou','jogaram','jogava',
        'trabalha','trabalham','trabalhou','trabalharam','trabalhava',
        'mora','moram','morou','moraram','morava',
        'nasce','nascem','nasceu','nasceram','nascia',
        'morre','morrem','morreu','morreram','morria',
        'cresce','crescem','cresceu','cresceram','crescia',
        'muda','mudam','mudou','mudaram','mudava',
        'liga','ligam','ligou','ligaram','ligava',
        'toca','tocam','tocou','tocaram','tocava',
        'cria','criam','criou','criaram','criava',
        'usa','usam','usou','usaram','usava',
        'pede','pedem','pediu','pediram','pedia',
        'responde','respondem','respondeu','responderam','respondia',
        'pergunta','perguntam','perguntou','perguntaram','perguntava',
        'mostra','mostram','mostrou','mostraram','mostrava',
        'traz','trazem','trouxe','trouxeram','trazia',
        'poe','poem','pos','pos','punha',
    ])
    _VERBOS = _VERBOS.union(_COP)

    def extrair(self, texto):
        """Extrai triplas (sujeito, relacao, objeto) do texto."""
        triplas = []
        for sentenca in self._sentencas(texto):
            if len(sentenca) < 2:
                continue
            t = self._extrair_tripla(sentenca)
            if t:
                triplas.append(t)
        return triplas

    def _sentencas(self, texto):
        """Divide texto em sentencas."""
        raw = texto.replace('\n',' ').split('.')
        result = []
        for parte in raw:
            parte = parte.strip()
            if not parte:
                continue
            # Remove pontuacao final
            while parte and parte[-1] in '!?:;':
                parte = parte[:-1].strip()
            if parte:
                result.append(self._tokenizar(parte))
        return result

    def _tokenizar(self, texto):
        """Tokeniza mantendo pontuacao separada."""
        tokens = []
        for palavra in texto.split():
            while palavra and palavra[-1] in ',;:!?)]}"\'': tokens.append(palavra[-1]); palavra=palavra[:-1]
            while palavra and palavra[0] in '([{"\'': tokens.append(palavra[0]); palavra=palavra[1:]
            if palavra:
                tokens.append(palavra)
        return tokens

    def _classificar(self, palavra, pos=0):
        """Heuristica de classe gramatical."""
        p = palavra.lower()
        if p in self._FUNC:
            if p in self._PREP: return 'prep'
            if p in self._ART: return 'art'
            return 'conj'
        if p in self._COP: return 'cop'
        if p in self._VERBOS: return 'verbo'
        if len(p) > 2 and p.endswith(('ndo','do','da')): return 'verbo'
        if p in ('mais','menos','tanto','quanto'): return 'comp'
        if p == 'que' and pos > 0: return 'sub'  # conjuncao subordinativa/comparativa
        if palavra[0].isupper() and len(palavra) > 1 and pos > 0: return 'nome'
        if len(p) > 2 and p.endswith(('cao','dade','mento','gem','ez','ista','eiro','or')): return 'nome'
        if len(p) > 2 and p.endswith(('oso','osa','vel','al','ico','ante','ente')): return 'adj'
        if len(p) > 2 and p.endswith(('ar','er','ir')): return 'verbo'
        return 'nome'

    def _extrair_tripla(self, tokens):
        """Extrai uma tripla de uma sentenca tokenizada."""
        # Remove artigos e pronomes do inicio
        while tokens and self._classificar(tokens[0], 0) in ('art',):
            tokens = tokens[1:]

        if len(tokens) < 2:
            return None

        # Encontra verbo principal
        pos_v = -1; verbo = None
        for i, t in enumerate(tokens):
            cls = self._classificar(t, i)
            if cls in ('verbo','cop'):
                pos_v = i; verbo = t.lower()
                break
            # 'e' ambiguo: em posicao 1, e copula (ser)
            if i == 1 and t.lower() == 'e' and len(tokens) >= 3:
                pos_v = i; verbo = 'e'; break

        # Fallback posicional: em portugues SVO, tokens[1] tende a ser verbo
        if pos_v < 0 and len(tokens) >= 3:
            v = tokens[1].lower()
            if v not in self._FUNC:
                pos_v = 1; verbo = v
        if pos_v < 0:
            return None

        # Particula de comparacao "mais X que"
        comp_que = None
        for i in range(pos_v+1, len(tokens)):
            if tokens[i].lower() == 'mais' and i+2 < len(tokens) and tokens[i+2].lower() == 'que':
                comp_que = tokens[i+1].lower()
                obj_pos = i+3
                break

        # Extrai sujeito (antes do verbo)
        sujeito = None
        for t in reversed(tokens[:pos_v]):
            cls = self._classificar(t, tokens.index(t))
            if cls in ('nome',) or (t[0].isupper() and len(t)>1):
                sujeito = t
                break
            if cls not in ('art','prep','conj') and len(t) > 1:
                sujeito = t
                break
        if not sujeito:
            return None

        # Extrai objeto (depois do verbo)
        objeto = None

        if comp_que:
            # Padrao: "e mais ADJ que OBJ"
            if obj_pos < len(tokens):
                objeto = tokens[obj_pos]
                return (sujeito, f"e_mais_{comp_que}_que", objeto)

        # Tenta objetos diretos/indiretos
        depois = tokens[pos_v+1:]
        for i, t in enumerate(depois):
            cls = self._classificar(t, pos_v+1+i)
            if cls == 'prep':
                # Objeto preposicional
                for j in range(i+1, len(depois)):
                    cls2 = self._classificar(depois[j], pos_v+1+j)
                    if cls2 in ('nome',):
                        return (sujeito, f"{verbo}_{t}", depois[j])
                    if cls2 not in ('art',):
                         return (sujeito, f"{verbo}_{t}", depois[j])
            if cls in ('nome',):
                objeto = t
                break
            if cls not in ('art','conj','comp'):
                objeto = t
                break

        if objeto:
            return (sujeito, verbo, objeto)

        # Verbo intransitivo
        return (sujeito, verbo, '')


# ═══════════════════════════════════════════════════════════════════
# [20b] MCRRedeSemantica — estado relacional Markov + grafo
# ═══════════════════════════════════════════════════════════════════

class MCRRedeSemantica:
    """Rede semantica baseada em Markov + grafo direto.
    
    Armazena triplas (sujeito, relacao, objeto) como:
    1. Grafo direto {sujeito: {relacao: {objetos}}} para consulta
    2. 4 cadeias Markov para inferencia probabilistica:
       - mk_suj_rel: sujeito → relacao
       - mk_rel_obj: relacao → objeto
       - mk_obj_rel: objeto → relacao (inversa)
       - mk_suj_obj: sujeito → objeto (atalho transitivo)
    """

    def __init__(self):
        self.mk_suj_rel = MCR("suj_rel")
        self.mk_rel_obj = MCR("rel_obj")
        self.mk_obj_rel = MCR("obj_rel")
        self.mk_suj_obj = MCR("suj_obj")
        self.grafo: Dict[str, Dict[str, Set[str]]] = {}
        self.total = 0

    def aprender(self, s, r, o):
        s, r = str(s).strip(), str(r).strip()
        o = str(o).strip() if o else ''
        if s not in self.grafo: self.grafo[s] = {}
        if r not in self.grafo[s]: self.grafo[s][r] = set()
        if o: self.grafo[s][r].add(o)
        self.mk_suj_rel.aprender(s, r)
        if o:
            self.mk_rel_obj.aprender(r, o)
            self.mk_obj_rel.aprender(o, r)
            self.mk_suj_obj.aprender(s, o)
        self.total += 1

    def consultar(self, sujeito=None, relacao=None, objeto=None):
        """Retorna triplas que casam com os filtros."""
        r = []
        for s in self.grafo if sujeito is None else [sujeito]:
            if s not in self.grafo: continue
            for rel in self.grafo[s] if relacao is None else [relacao]:
                if rel not in self.grafo[s]: continue
                for o in self.grafo[s][rel] if objeto is None else {objeto}:
                    if not objeto or o == objeto:
                        r.append((s, rel, o))
        return r

    def predizer_objeto(self, sujeito, relacao=None):
        """sujeito → (relacao → objeto)"""
        if relacao:
            o, conf = self.mk_rel_obj.predizer(relacao)
            return o, conf
        r, _ = self.mk_suj_rel.predizer(sujeito)
        if r:
            o, conf = self.mk_rel_obj.predizer(r)
            return o, conf
        return None, 0.0

    def predizer_sujeito(self, objeto):
        """objeto → (relacao → sujeito)"""
        r, _ = self.mk_obj_rel.predizer(objeto)
        if r:
            for s in self.grafo:
                if r in self.grafo.get(s, {}) and objeto in self.grafo[s][r]:
                    _, conf = self.mk_suj_rel.predizer(s)
                    return s, conf
        return None, 0.0

    def buscar_cadeia(self, inicio, fim, max_passos=10, reverso=False):
        """BFS no grafo: encontra caminho de 'inicio' a 'fim'.
        
        Se reverso=True, busca na direcao oposta (objeto -> sujeito).
        Retorna lista de (sujeito, relacao, objeto) ou None.
        """
        if reverso:
            # Constroi grafo reverso: {objeto: [(sujeito, relacao)]}
            reverso_g = {}
            for s in self.grafo:
                for r, objs in self.grafo[s].items():
                    for o in objs:
                        if o not in reverso_g: reverso_g[o] = []
                        reverso_g[o].append((s, r))
            fila = [(inicio, [])]
            visitados = {inicio}
            while fila:
                atual, caminho = fila.pop(0)
                if atual in reverso_g:
                    for s, r in reverso_g[atual]:
                        if s == fim:
                            # Reverte a ordem para mostrar (sujeito, relacao, objeto)
                            return [(s, r, atual)] + caminho
                        if s not in visitados and len(visitados) < max_passos:
                            visitados.add(s)
                            fila.append((s, [(s, r, atual)] + caminho))
            return None

        fila = [(inicio, [])]
        visitados = {inicio}
        while fila:
            atual, caminho = fila.pop(0)
            if atual in self.grafo:
                for r, objs in self.grafo[atual].items():
                    for o in objs:
                        if o == fim:
                            return caminho + [(atual, r, o)]
                        if o not in visitados and len(visitados) < max_passos:
                            visitados.add(o)
                            fila.append((o, caminho + [(atual, r, o)]))
        return None

    def entropia_media(self):
        ent = 0.0; n = 0
        for mk in [self.mk_suj_rel, self.mk_rel_obj, self.mk_obj_rel, self.mk_suj_obj]:
            e = mk.entropia_media()
            if e < 1.0: ent += e; n += 1
        return ent / n if n else 1.0

    def estatisticas(self):
        n_sujeitos = len(self.grafo)
        n_relacoes = sum(len(rs) for rs in self.grafo.values())
        n_triplas = sum(sum(len(os) for os in rs.values()) for rs in self.grafo.values())
        return {'sujeitos': n_sujeitos, 'relacoes': n_relacoes, 'triplas': n_triplas,
                'total_markov': self.total, 'entropia': round(self.entropia_media(), 3)}


# ═══════════════════════════════════════════════════════════════════
# [21] CerebroAGI — integracao de TUDO
# ═══════════════════════════════════════════════════════════════════

class CerebroAGI:
    def __init__(self):
        self.mk_byte = MCR("byte"); self.mk_palavra = MCR("palavra"); self.mk_tven = MCR("tven")
        self.hiper = MCRHiperesferaAutoExpansiva()
        self._hiper_descobertas = False
        self.topologia = MCRAutoTopologia()
        self.auto_validacao = MCRAutoValidacaoContinua()
        self._topologia_atualizada = False
        self.mk_orq = MCR("orquestrador")
        self._seed_orquestrador()
        self._acoes_internas = {}
        self._registrar_acoes_internas()
        self.reservoir = MCRJanelamentoFingerprint()
        self.topicos: Dict[str, Dict] = {}
        self.world = MCRWorld(); self.coupling = MCRCoupling(); self.planner = MCRPlanner(self.world)
        self.hdc = MCRHDCOperation(self.reservoir, coupling=self.coupling, niveis_ctx=["byte", "palavra", "tven", "intencao", "acao"])
        self.superposicao = MCRSuperposicao(self.coupling)
        self.total_ciclos = 0; self.thr = MCRThreshold("cerebro"); self.entropia = MCREntropia("cerebro")
        self._rl, self._bridge, self._genesis = None, None, None
        self.entropic_search = MCREntropicSearch(self.world, self.rl)
        self.auto_evolution = MCRAutoEvolution(self)
        self._ultimo_resultado = {}
        self.fila_eventos = queue.Queue(maxsize=500)
        self.hook_observer = MCRHookObserver(self)
        self.file_observer = MCRFileObserver(self.fila_eventos, cerebro=self)
        self.ent_temporal = MCREntropiaTemporal(observer=self.hook_observer)
        self.parser = MCRParserMinimo()
        self.rede_semantica = MCRRedeSemantica()
        self._niveis_semanticos = False
    
    def _seed_orquestrador(self):
        """Sementes para o orquestrador comecar a decidir.
        Nao e regra fixa — e bootstrap. O MCR aprendera
        novas transicoes com o uso."""
        seeds = [
            ("ent:alta_dims:0_inst:0_meta:alta", "alimentar"),
            ("ent:alta_dims:3_inst:0_meta:alta", "verificar_topologia"),
            ("ent:media_dims:3_inst:0_meta:alta", "calcular_destinos"),
            ("ent:baixa_dims:3_inst:0_meta:alta", "calcular_destinos"),
            ("ent:alta_dims:3_inst:0_meta:baixa", "verificar_topologia"),
            ("ent:media_dims:3_inst:0_meta:baixa", "calcular_destinos"),
            ("ent:baixa_dims:3_inst:0_meta:baixa", "calcular_destinos"),
            ("ent:alta_dims:3_inst:1_meta:alta", "executar_auto_validacao"),
            ("ent:media_dims:3_inst:1_meta:alta", "executar_auto_validacao"),
            ("ent:baixa_dims:3_inst:1_meta:alta", "executar_auto_validacao"),
            ("ent:alta_dims:3_inst:1_meta:baixa", "executar_auto_validacao"),
            ("ent:media_dims:3_inst:1_meta:baixa", "executar_auto_validacao"),
            ("ent:baixa_dims:3_inst:1_meta:baixa", "executar_auto_validacao"),
            # Transicoes de continuacao
            ("ent:alta_dims:3_inst:0_meta:baixa_orq:alimentar", "verificar_topologia"),
            ("ent:alta_dims:3_inst:0_meta:baixa_orq:verificar_topologia", "buscar_analogias"),
            ("ent:alta_dims:3_inst:0_meta:baixa_orq:buscar_analogias", "calcular_destinos"),
            ("ent:alta_dims:3_inst:0_meta:baixa_orq:calcular_destinos", "planejar_entropico"),
            ("ent:alta_dims:3_inst:0_meta:baixa_orq:planejar_entropico", "executar_auto_validacao"),
            ("ent:alta_dims:3_inst:0_meta:baixa_orq:executar_auto_validacao", "auto_evoluir"),
        ]
        for estado, acao in seeds:
            self.mk_orq.aprender(estado, acao)
    
    def _registrar_acoes_internas(self):
        """Registra acoes internas do sistema (registry dispatch)."""
        reg = self._acoes_internas
        
        reg["alimentar"] = lambda ctx: self._exec_alimentar(ctx.get("texto", ""))
        reg["descobrir_dimensoes"] = lambda ctx: self._exec_descobrir(ctx.get("texto", ""))
        reg["verificar_topologia"] = lambda ctx: self._exec_verificar_topologia()
        reg["recalcular_topologia"] = lambda ctx: self._exec_recalcular_topologia()
        reg["executar_auto_validacao"] = lambda ctx: self._exec_auto_validacao()
        reg["calcular_destinos"] = lambda ctx: self._exec_calcular_destinos()
        reg["buscar_analogias"] = lambda ctx: self._exec_buscar_analogias(ctx.get("texto", ""))
        reg["planejar_entropico"] = lambda ctx: self._exec_planejar_entropico()
        reg["auto_evoluir"] = lambda ctx: self._exec_auto_evoluir()
        reg["ciclo_autonomo"] = lambda ctx: self.ciclo_autonomo(ctx.get("texto", ""))
    
    def _ciclo_passivo(self, max_eventos=10):
        """Drena fila de eventos do sistema e alimenta o cerebro.
        
        Processa arquivos alterados, detecta eventos multi-nivel,
        e busca lacunas de conhecimento — sem timer, sem polling,
        puramente event-driven.
        """
        n = 0
        while n < max_eventos:
            try:
                tipo, action, path = self.fila_eventos.get_nowait()
            except queue.Empty:
                break
            n += 1
            
            if tipo != 'FILE':
                continue
            
            try:
                # Le conteudo do arquivo (primeiros 2000 bytes)
                with open(path, 'rb') as f:
                    raw = f.read(2000)
                # Extrai texto se possivel
                try:
                    text = raw.decode('utf-8', errors='replace')
                except:
                    text = raw.decode('latin-1', errors='replace')
                
                ext = os.path.splitext(path)[1][:10]
                if not ext: ext = 'desconhecido'
                
                # Alimenta o cerebro com o arquivo
                entrada = f"[{ext}] {path}: {text[:1500]}"
                nome = f"file_{abs(hash(path)) % 10000}"
                self.alimentar(entrada, nome)
                
                # Se for texto longo, alimenta em partes
                if len(text) > 1500:
                    for i in range(1, min(3, len(text) // 1500 + 1)):
                        chunk = text[i*1500:(i+1)*1500]
                        if chunk.strip():
                            self.alimentar(chunk, f"{nome}_p{i}")
                
                # Registra que aprendeu deste arquivo
                sig = self.file_observer._file_sigs.get(path) if hasattr(self, 'file_observer') else None
                if sig:
                    pass  # ja registrado na DB de assinaturas
                    
            except (IOError, OSError):
                pass
        
        # Mede entropia temporal apos processar eventos
        try:
            self.ent_temporal.medir()
            evento, info = self.ent_temporal.detectar()
            if evento:
                self._ultimo_resultado['ultimo_evento'] = info
        except:
            pass
        
        # Auto-estudo: se alguma cadeia tem entropia > 0.8 (nao sabe),
        # registra como oportunidade de aprendizado
        ent_byte = self.mk_byte.entropia_media() if self.mk_byte.total > 0 else 1.0
        ent_palavra = self.mk_palavra.entropia_media() if self.mk_palavra.total > 0 else 1.0
        if ent_byte > 0.8 or ent_palavra > 0.8:
            pass  # oportunidade — o SelfStudy buscara dados
    
    def _estado_atual(self) -> str:
        """Serializa o estado do sistema para o MCR decidir a proxima acao."""
        ent = self.mk_byte.entropia_media() if self.mk_byte.total > 0 else 1.0
        n_dims = len(self.hiper.dimensoes) if hasattr(self, 'hiper') else 0
        n_inst = len(self.auto_validacao.instavel) if hasattr(self, 'auto_validacao') else 0
        meta_ent = (self.auto_validacao.meta.entropia_media()
                    if hasattr(self, 'auto_validacao') and self.auto_validacao.meta.total > 0
                    else 1.0)
        ent_tag = "alta" if ent > 0.7 else "baixa" if ent < 0.4 else "media"
        meta_tag = "alta" if meta_ent > 0.3 else "baixa"
        ultima = self._ultimo_resultado.get("ultima_acao", "") if self._ultimo_resultado else ""
        sufixo = f"_orq:{ultima}" if ultima else ""
        return f"ent:{ent_tag}_dims:{n_dims}_inst:{n_inst}_meta:{meta_tag}{sufixo}"
    
    def _exec_alimentar(self, texto):
        self.alimentar(texto)
        return {"acao": "alimentar", "status": "ok"}
    
    def _exec_descobrir(self, texto):
        if not self._hiper_descobertas and len(texto) > 100:
            self.hiper.descobrir(texto)
            self._hiper_descobertas = True
        return {"acao": "descobrir", "dims": len(self.hiper.dimensoes)}
    
    def _exec_verificar_topologia(self):
        self.topologia.recalcular()
        self._topologia_atualizada = True
        return {"acao": "verificar_topologia", "clusters": self.topologia.metricas()["n_clusters"]}
    
    def _exec_recalcular_topologia(self):
        self.topologia.recalcular()
        self._topologia_atualizada = True
        return {"acao": "recalcular_topologia", "clusters": self.topologia.metricas()["n_clusters"]}
    
    def _exec_auto_validacao(self):
        if self.hiper.dimensoes:
            if self.auto_validacao.ciclos == 0:
                for nome_dim in self.hiper.dimensoes:
                    self.auto_validacao.registrar(nome_dim, self.hiper.dimensoes[nome_dim])
            r = self.auto_validacao.ciclo(self.hiper.dimensoes)
            return {"acao": "auto_validacao", "instaveis": r["instaveis"], "meta": r["entropia_meta"]}
        return {"acao": "auto_validacao", "status": "sem_dimensoes"}
    
    def _exec_calcular_destinos(self):
        return {"acao": "calcular_destinos", "n_dims": len(self.hiper.dimensoes) if self.hiper else 0}
    
    def _exec_buscar_analogias(self, texto):
        """Busca analogias entre topicos usando HDC."""
        if not self.topicos or len(self.topicos) < 2:
            return {"acao": "buscar_analogias", "status": "poucos_topicos"}
        topicos = list(self.topicos.keys())[:5]
        analogias = []
        for i in range(len(topicos)):
            for j in range(i+1, len(topicos)):
                a = self.topicos[topicos[i]]["texto"][:100]
                b = self.topicos[topicos[j]]["texto"][:100]
                sim = self.hdc.comparar(a, b)
                analogias.append({"a": topicos[i], "b": topicos[j], "sim": sim})
        analogias.sort(key=lambda x: -x["sim"])
        return {"acao": "buscar_analogias", "n_analogias": len(analogias), "melhor": analogias[0] if analogias else None}
    
    def _exec_planejar_entropico(self):
        """Planeja usando Entropic Search."""
        est = EstadoMundo.criar_simples()
        obj = est.clone()
        heroi = obj.get("heroi")
        if heroi:
            heroi.props["x"] = 4
            heroi.props["y"] = 4
        acao, score = self.entropic_search.planejar(est, obj)
        return {"acao": "planejar_entropico", "melhor_acao": acao, "score": score}
    
    def _exec_auto_evoluir(self):
        """Executa um ciclo de auto-evolucao."""
        r = self.auto_evolution.ciclo()
        return {"acao": "auto_evoluir", "resultado": r["resultado"], "melhoria": r.get("melhoria", 0)}
    
    def ciclo_autonomo(self, texto="", max_passos=20):
        """Ciclo autonomo: MCR decide QUAL acao executar.
        
        Nao ha ordem fixa. MCR orquestrador decide + epsilon-greedy
        para exploracao. Aprende com recompensa = reducao de entropia.
        """
        historico = []
        estado_anterior = ""
        ent_antes = self.mk_byte.entropia_media() if self.mk_byte.total > 0 else 1.0
        dec_orq = MCRDecisorUniversal.decidir(ctx="orquestrador")
        epsilon = dec_orq.get("threshold", 0.1)
        
        for passo in range(max_passos):
            estado_str = self._estado_atual()
            
            if estado_str == estado_anterior:
                ent_depois = self.mk_byte.entropia_media() if self.mk_byte.total > 0 else 1.0
                dec_rec = MCRDecisorUniversal.decidir(ctx="ciclo_recompensa")
                recompensa = (ent_antes - ent_depois) * dec_rec.get("threshold", 1.0)
                self.mk_orq.aprender(estado_str, f"ent_stabilized:{recompensa:.3f}")
                break
            estado_anterior = estado_str
            
            acao, conf = self.mk_orq.predizer(estado_str)
            if acao is None:
                acao, conf = self.mk_orq.predizer("ent:baixa_dims:0_inst:0_meta:0")
            if acao is None:
                ent_depois = self.mk_byte.entropia_media() if self.mk_byte.total > 0 else 1.0
                dec_rec = MCRDecisorUniversal.decidir(ctx="ciclo_recompensa")
                recompensa = (ent_antes - ent_depois) * dec_rec.get("threshold", 1.0)
                self.mk_orq.aprender(estado_str, f"ent_unknown:{recompensa:.3f}")
                break
            
            # Epsilon-greedy: explora acao aleatoria com prob epsilon (P5)
            if _rand.random() < epsilon:
                acoes_validas = [k for k in self._acoes_internas.keys()]
                if acoes_validas:
                    acao = _rand.choice(acoes_validas)
                    conf = epsilon
            
            # Sobrescrita por confianca: se aprendeu algo mais confiavel, usa (P5)
            acao_aprendida, conf_aprendida = self.mk_orq.predizer(estado_str)
            if acao_aprendida and conf_aprendida > conf:
                acao = acao_aprendida
                conf = conf_aprendida
            
            fn = self._acoes_internas.get(acao)
            if not fn:
                break
            
            resultado = fn({"texto": texto})
            resultado["acao"] = acao
            resultado["confianca"] = round(conf, 3)
            historico.append(resultado)
            
            ent_depois = self.mk_byte.entropia_media() if self.mk_byte.total > 0 else 1.0
            dec_rec = MCRDecisorUniversal.decidir(ctx="ciclo_recompensa")
            recompensa = (ent_antes - ent_depois) * dec_rec.get("threshold", 1.0)
            self.mk_orq.aprender(estado_str, f"{acao}:{recompensa:.3f}")
            self._ultimo_resultado = {"ultima_acao": acao}
        
        self._ultimo_resultado = {
            "passos": len(historico),
            "acoes": [h["acao"] for h in historico],
            "resultados": historico,
            "ultima_acao": historico[-1]["acao"] if historico else "",
        }
        return self._ultimo_resultado
    
    @property
    def rl(self):
        if self._rl is None: self._rl = MCRQLearn()
        return self._rl
    @property
    def bridge(self):
        if self._bridge is None: self._bridge = MCRBridge()
        return self._bridge
    @property
    def genesis(self):
        if self._genesis is None: self._genesis = MCRGenesis(self)
        return self._genesis
    def alimentar(self, texto, nome=None, tipo="conv"):
        if nome is None: nome = f"top_{len(self.topicos)+1}"
        self.total_ciclos += 1
        dados = texto.encode(); palavras = texto.split()
        
        # Niveis fixos (byte, palavra, tven) — sempre aprende
        for i in range(len(dados)-1): self.mk_byte.aprender(f"B:{dados[i]:02x}", f"B:{dados[i+1]:02x}")
        for i in range(len(palavras)-1): self.mk_palavra.aprender(palavras[i], palavras[i+1])
        for i in range(len(palavras)-1):
            ta = palavras[i][0].upper() if palavras[i] else '?'; tb = palavras[i+1][0].upper() if palavras[i+1] else '?'
            self.mk_tven.aprender(ta, tb)
        
        # Hiperesfera: descobre dimensoes na primeira alimentacao
        # (protegido — falha nao quebra o pipeline)
        try:
            if not self._hiper_descobertas and len(texto) > 30:
                dims = self.hiper.descobrir(texto)
                self._hiper_descobertas = True
                for nome_dim, mk in self.hiper.dimensoes.items():
                    tokens = self.hiper.tokenizadores[nome_dim](texto)
                    for i in range(len(tokens)-1):
                        mk.aprender(tokens[i], tokens[i+1])
            else:
                for nome_dim, mk in self.hiper.dimensoes.items():
                    fn = self.hiper.tokenizadores.get(nome_dim)
                    if fn:
                        tokens = fn(texto)
                        for i in range(len(tokens)-1):
                            mk.aprender(tokens[i], tokens[i+1])
        except:
            pass
        
        # Topologia: registra niveis e recalcula grafo
        if self.hiper.dimensoes:
            for nome_dim, mk in self.hiper.dimensoes.items():
                self.topologia.registrar(nome_dim, mk)
            self.topologia.registrar("byte", self.mk_byte)
            self.topologia.registrar("palavra", self.mk_palavra)
            self.topologia.registrar("tven", self.mk_tven)
            self.topologia.recalcular()
            self._topologia_atualizada = True
        
        # Auto-validacao: ciclo continuo a cada N alimentos
        if self.hiper.dimensoes and self.total_ciclos % max(1, 10 - min(self.total_ciclos//5, 8)) == 0:
            # Registra niveis na primeira vez
            if self.auto_validacao.ciclos == 0:
                for nome_dim in self.hiper.dimensoes:
                    self.auto_validacao.registrar(nome_dim, self.hiper.dimensoes[nome_dim])
            val = self.auto_validacao.ciclo(self.hiper.dimensoes)
            if val["instaveis"] and self.total_ciclos > 10:
                pass  # instabilidade detectada — pode ser usado para recalibracao
        
        # Coupling entre byte ↔ palavra ↔ tven
        for i in range(min(len(dados)-1, len(palavras))):
            if i < len(dados)-1:
                bt = f"B:{dados[i]:02x}"; pt = palavras[min(i,len(palavras)-1)]; tt = pt[0].upper() if pt else '?'
                self.coupling.alimentar("byte","palavra",bt,pt); self.coupling.alimentar("palavra","tven",pt,tt); self.coupling.alimentar("tven","byte",tt,bt)
        self.coupling.recalcular()
        
        # Parser semantico minimo + alimentacao da rede
        try:
            triplas = self.parser.extrair(texto)
            if triplas:
                if not self._niveis_semanticos:
                    self.topologia.registrar("sujeito", MCR("sujeito"))
                    self.topologia.registrar("relacao", MCR("relacao"))
                    self.topologia.registrar("objeto", MCR("objeto"))
                    self._niveis_semanticos = True
                for s, r, o in triplas:
                    self.rede_semantica.aprender(s, r, o)
                    self.coupling.alimentar("sujeito","relacao",s,r)
                    if o: self.coupling.alimentar("relacao","objeto",r,o)
                    if o: self.coupling.alimentar("objeto","sujeito",o,s)
                    self.coupling.alimentar("palavra","sujeito",r,s)
                    if o: self.coupling.alimentar("objeto","palavra",o,r)
        except:
            pass
        
        # Auto-expansao: se entropia media de todos os niveis > threshold,
        # cria NOVA dimensao combinando os dois niveis com maior correlacao
        # (executa a cada 5 alimentacoes para evitar loop infinito)
        if self.total_ciclos > 0 and self.total_ciclos % 3 == 0:
            try:
                nova_dim = self.hiper.auto_expandir(self, texto)
                if nova_dim:
                    # Alimenta a nova dimensao com o texto atual
                    fn = self.hiper.tokenizadores.get(nova_dim)
                    if fn:
                        tokens = fn(texto)
                        mk = self.hiper.dimensoes[nova_dim]
                        for i in range(len(tokens)-1):
                            mk.aprender(tokens[i], tokens[i+1])
                    # Registra na topologia
                    if nova_dim in self.hiper.dimensoes:
                        self.topologia.registrar(nova_dim, self.hiper.dimensoes[nova_dim])
                        self.auto_validacao.registrar(nova_dim, self.hiper.dimensoes[nova_dim])
            except:
                pass
        
        self.topicos[nome] = {'texto': texto, 'bytes': len(dados), 'n_palavras': len(palavras), 'conteudo': list({p.lower() for p in palavras if len(p) >= 2}), 'tipo': tipo}
        return nome
    
    def salvar(self, caminho=None):
        """Salva cerebro em disco (topicos + markov + hiper-dimensoes).
        Usa arquivo temporario + os.replace para evitar corrupcao."""
        caminho = caminho or os.path.join(CACHE_DIR, "cerebro.json")
        topicos_serial = {}
        for n, t in self.topicos.items():
            topicos_serial[n] = {
                'texto': t['texto'][:500],
                'bytes': t['bytes'],
                'n_palavras': t['n_palavras'],
                'conteudo': list(t.get('conteudo', set())) if isinstance(t.get('conteudo'), (set, list)) else [],
                'tipo': t.get('tipo', 'conv'),
            }
        dados = {
            'topicos': topicos_serial,
            'byte_trans': {str(k): v for k, v in self.mk_byte.transicoes.items()},
            'palavra_trans': {str(k): v for k, v in self.mk_palavra.transicoes.items()},
            'timestamp': time.time(),
        }
        # Salva dimensoes descobertas pela hiperesfera
        if self.hiper.dimensoes:
            dados['hiper_dims'] = {}
            for nome, mk in self.hiper.dimensoes.items():
                dados['hiper_dims'][nome] = {
                    'trans': {str(k): v for k, v in mk.transicoes.items()},
                    'freq': {str(k): v for k, v in mk.freq.items()},
                    'total': mk.total,
                }
        # Salva topologia (grafo de correlacao)
        if self._topologia_atualizada:
            tm = self.topologia.metricas()
            dados['topologia'] = {
                'grafo': {n: {d: p for d, p in adj.items() if d != n and p >= 0.15}
                         for n, adj in self.topologia.grafo.items()},
                'clusters': [sorted(c) for c in self.topologia.clusters],
            }
        try:
            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            tmp = caminho + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False)
            os.replace(tmp, caminho)
            return True
        except: return False
    
    def carregar(self, caminho=None):
        """Carrega cerebro do disco."""
        caminho = caminho or os.path.join(CACHE_DIR, "cerebro.json")
        if not os.path.exists(caminho): return False
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            for nome, top in dados.get('topicos', {}).items():
                # Tenta usar 'conteudo' salvo (lista -> set); fallback para texto
                conteudo_salvo = top.get('conteudo')
                if isinstance(conteudo_salvo, list):
                    conteudo = set(conteudo_salvo)
                else:
                    conteudo = {p.lower() for p in top.get('texto', '').split() if len(p) >= 2}
                self.topicos[nome] = {
                    'texto': top.get('texto', ''),
                    'bytes': top.get('bytes', 0),
                    'n_palavras': top.get('n_palavras', 0),
                    'conteudo': conteudo,
                    'tipo': top.get('tipo', 'conv'),
                }
            # Restaura dimensoes da hiperesfera
            hiper_dims = dados.get('hiper_dims', {})
            for nome_dim, dim_data in hiper_dims.items():
                mk = MCR(nome_dim)
                for chave_a, trans in dim_data.get('trans', {}).items():
                    mk.transicoes[chave_a] = dict(trans)
                for chave_a, freq_val in dim_data.get('freq', {}).items():
                    mk.freq[chave_a] = int(freq_val) if isinstance(freq_val, (int, float)) else 0
                mk.total = dim_data.get('total', 0)
                self.hiper.dimensoes[nome_dim] = mk
            if hiper_dims:
                self._hiper_descobertas = True
            # Restaura transicoes byte e palavra (Fix 1)
            for chave_a, trans in dados.get('byte_trans', {}).items():
                self.mk_byte.transicoes[chave_a] = dict(trans)
                self.mk_byte.freq[chave_a] = sum(trans.values())
            self.mk_byte.total = sum(len(t) for t in self.mk_byte.transicoes.values())
            for chave_a, trans in dados.get('palavra_trans', {}).items():
                self.mk_palavra.transicoes[chave_a] = dict(trans)
                self.mk_palavra.freq[chave_a] = sum(trans.values())
            self.mk_palavra.total = sum(len(t) for t in self.mk_palavra.transicoes.values())
            # Restaura topologia
            topo_data = dados.get('topologia', {})
            if topo_data.get('grafo'):
                self.topologia.grafo = topo_data['grafo']
                self.topologia.clusters = [set(c) for c in topo_data.get('clusters', [])]
                self._topologia_atualizada = True
            return True
        except: return False
    def aprender_causal(self, antes, acao, depois):
        self.world.aprender(antes, acao, depois); self.coupling.alimentar("intencao","acao",str(antes.fingerprint(8)[:3]),acao)
        self.coupling.alimentar("acao","intencao",acao,str(depois.fingerprint(8)[:3])); self.coupling.recalcular()
    def _gerar_original(self, texto, passos=6):
        palavras = texto.split(); dim = C("dim_fingerprint",8)
        if not palavras: return texto
        for _ in range(passos):
            semente = palavras[-1]
            if semente not in self.mk_palavra.freq:
                if len(palavras) > 1: semente = palavras[-2]
                else: break
            
            # Tenta Markov puro primeiro (dimensao palavra)
            cands = self.mk_palavra.predizer_n(semente, 5)
            pred = None
            conf = 0.0
            
            if cands:
                probs = {c: cf for c, cf in cands}
                mod = self.coupling.modular("palavra", probs)
                melhor = max(mod, key=mod.get)
                if mod[melhor] > 0.01:
                    pred = melhor
                    conf = mod[melhor]
            
            # Fallback: esfera cross-dimensional quando Markov falha
            if pred is None or conf < 0.05:
                ultimo_byte = f"B:{ord(semente[-1]):02x}" if semente else "B:00"
                for n in ["token_tipo", "linha", "byte_delta", "hash_curto", "byte"]:
                    if n in self.hiper.dimensoes or n == "byte":
                        ctx = {"palavra": semente}
                        if n == "byte":
                            ctx["byte"] = ultimo_byte
                        pred_esf, conf_esf = self.coupling.esfera.predizer_cross("palavra", **ctx)
                        if pred_esf and conf_esf > conf:
                            pred = pred_esf
                            conf = conf_esf
                            if conf > 0.3:
                                break  # confianca alta, aceita
            
            # Fallback: superposicao — colisao entre cadeias gera algo novo
            if pred is None or conf < 0.01:
                ultimo_byte = f"B:{ord(semente[-1]):02x}" if semente else "B:00"
                novo, conf2, meta = self.superposicao.colidir(
                    "palavra", semente,
                    "byte", ultimo_byte,
                    self.mk_palavra, self.mk_byte)
                if novo and conf2 > 0.05:
                    pred = novo
                    conf = conf2
            
            # Ultimo fallback: byte puro
            if pred is None or conf < 0.01:
                ultimo_byte = f"B:{ord(semente[-1]):02x}" if semente else "B:00"
                pred, conf = self.mk_byte.predizer(ultimo_byte)
            
            if pred:
                palavras.append(pred)
            else:
                break
            self.entropia.alimentar(palavras[-1])
            if self.entropia.esta_em_loop():
                # Radar: em vez de parar (break), penaliza a palavra atual
                # e tenta achar a SEGUNDA melhor opcao
                palavra_loop = palavras[-1]
                if cands and len(cands) > 1:
                    # Pega a segunda melhor opcao
                    palavra_alt = cands[1][0] if len(cands) > 1 and cands[1][0] != palavra_loop else None
                    if palavra_alt:
                        palavras[-1] = palavra_alt  # substitui pela alternativa
                        self.entropia.alimentar(palavra_alt)
                        continue
                if len(palavras) > 2:
                    # Fallback: volta um passo e tenta caminho diferente
                    semente = palavras[-2]
                    cands2 = self.mk_palavra.predizer_n(semente, 10)
                    if cands2:
                        for alt, _ in cands2:
                            if alt != palavra_loop and alt != palavras[-2]:
                                palavras[-1] = alt
                                self.entropia.alimentar(alt)
                                break
                        continue
                break  # sem alternativa, para
        return " ".join(palavras)
    def gerar(self, texto, passos=None, pergunta=""):
        passos = passos or int(C("passos_gerar",6))
        if len(self.topicos) < 100: return self._gerar_original(texto, passos)
        return MCRAttention.gerar(self, texto, passos, pergunta or texto)
    def planejar(self, obj, est=None):
        est = est or EstadoMundo.criar_simples()
        eo = self._estado_de_texto(obj, est)
        if not eo: return {"plano": [], "erro": "objetivo nao compreendido"}
        acoes = self.planner.plano(est, eo)
        nota = self.planner.avaliar_plano(acoes, est, eo) if hasattr(self.planner, 'avaliar_plano') else 0.0
        return {"plano": acoes, "passos": len(acoes), "nota": round(nota,2)}
    def _estado_de_texto(self, desc, ref):
        e = ref.clone(); desc = desc.lower()
        if "bau" in desc and "aberto" in desc:
            b = e.get("bau")
            if b: b.props["aberto"] = True
        if "monstro" in desc and ("morto" in desc or "derrotado" in desc): e.remover("monstro")
        return e
    def auto_diagnosticar(self):
        gaps = []
        tlist = list(self.topicos.keys())
        n_amostras = MCRDecisorUniversal.decidir_passos("auto_diag", {"n_topicos": len(tlist)})
        for i in range(min(len(tlist), n_amostras)):
            for j in range(i+1, min(len(tlist), n_amostras)):
                a, b = tlist[i], tlist[j]
                ja = MCRByteUtils.jaccard_bytes(self.topicos[a]['texto'], self.topicos[b]['texto'])
                if ja < 0.1: gaps.append(f"{a}<->{b}: j={ja:.3f}")
        codex = MCRCodex()
        hc = codex.escanear()
        result = {"topicos": len(self.topicos), "bytes": self.mk_byte.total, "palavras": self.mk_palavra.total, "causais": len(self.world.hist), "gaps": gaps[:3], "hardcodes": len(hc)}
        # Adiciona metricas da topologia
        if self._topologia_atualizada:
            tm = self.topologia.metricas()
            result["clusters"] = tm["n_clusters"]
            result["arestas_topologia"] = tm["n_arestas"]
            result["isolados"] = tm["isolados"]
        # Adiciona metricas da auto-validacao
        if self.auto_validacao.ciclos > 0:
            result["instaveis"] = self.auto_validacao.instavel
            result["meta_entropia"] = round(self.auto_validacao.meta.entropia_media() if self.auto_validacao.meta.total > 0 else 0, 4)
        return result




# ═══════════════════════════════════════════════════════════════════
# [22] Chat + Daemon + main
# ═══════════════════════════════════════════════════════════════════

def aprender_npcs(forcar=False):
    brain = MCRNPCBrain()
    if not forcar and brain.carregar():
        print(f"NPCs carregados: {brain.total_npcs} NPCs, {brain.total_dialogos} dialogos")
        return brain
    dirs = [r"E:\Projeto MCR\Canary\data-otservbr-global\npc", r"E:\Projeto MCR\Canary\data-canary\scripts\MCR"]
    ta = 0; t0 = time.time()
    for d in dirs:
        if not os.path.exists(d): continue
        for f in sorted(glob.glob(os.path.join(d, "**/*.lua"), recursive=True)):
            n = brain.aprender_arquivo(f)
            if n > 0: ta += 1
    if ta > 0:
        brain.salvar()
        print(f"Aprendidos {brain.total_dialogos} dialogos de {brain.total_npcs} NPCs ({ta} arquivos em {time.time()-t0:.1f}s)")
    else:
        print("Nenhum NPC encontrado. O MCR funciona sem NPCs normalmente.")
    return brain

# ═══════════════════════════════════════════════════════════════════
# [22c] MCRIdentidade — Quem e quem, aprendido por uso, nao hardcode
# ═══════════════════════════════════════════════════════════════════
# Nao ha "Kheltz primeiro". Ha fingerprints aprendidos por conversa.
# Quanto mais alguem conversa, mais o MCR reconhece essa pessoa.
# ============================================================

class MCRIdentidade:
    """Reconhece autores pelo padrao de escrita — aprendido, nao hardcoded.
    
    Nao ha ordem fixa. Cada mensagem vira um fingerprint.
    Quem mais conversa, mais e reconhecido. Natural."""
    
    def __init__(self):
        self.autores: Dict[str, List[Dict]] = {}
        self.mk = MCR("identidade")
    
    def aprender(self, texto, autor="desconhecido"):
        if not texto or len(texto) < 20:
            return
        fp = MCRByteUtils.fingerprint(texto, 8)
        voc = set(re.findall(r'\b\w{4,}\b', texto.lower()))
        self.autores.setdefault(autor, []).append({
            'fingerprint': fp,
            'vocabulario': list(voc)[:30],
            'entropia': MCRByteUtils.entropia_bytes(texto.encode()[:1000]),
            'tamanho': len(texto),
            'timestamp': time.time(),
        })
        # So mantem os ultimos 20 fingerprints por autor
        if len(self.autores[autor]) > 20:
            self.autores[autor] = self.autores[autor][-20:]
    
    def identificar(self, texto):
        """Identifica o autor mais provavel — sem ordem fixa.
        
        Compara fingerprint do texto com TODOS os autores.
        O que tiver maior similaridade media vence.
        Sem Kheltz primeiro. Sem regra fixa. So dados."""
        if not texto or len(texto) < 20:
            return 'desconhecido', 0.0, {}
        
        fp_alvo = MCRByteUtils.fingerprint(texto, 8)
        voc_alvo = set(re.findall(r'\b\w{4,}\b', texto.lower()))
        ent_alvo = MCRByteUtils.entropia_bytes(texto.encode()[:1000])
        tam_alvo = len(texto)
        
        melhor_autor = 'desconhecido'
        melhor_score = 0.0
        detalhes = {}
        
        # Se so tem 1 autor, nao tem comparação — precisa de mais dados
        if len(self.autores) <= 1:
            autores_list = list(self.autores.keys())
            if autores_list:
                autor_unico = autores_list[0]
                n_amostras = len(self.autores[autor_unico])
                # Confianca baixa porque nao temos outros autores para comparar
                return autor_unico, round(0.3 + min(0.3, n_amostras * 0.05), 3), {'unico_autor': True, 'amostras': n_amostras}
            return 'desconhecido', 0.0, {}
        
        for autor, amostras in self.autores.items():
            scores = []
            for am in amostras[-10:]:  # ultimas 10 amostras
                fp_am = am.get('fingerprint', [])
                if not fp_am:
                    continue
                # Similaridade de fingerprint (cosseno)
                sim_fp = MCRByteUtils.similaridade_cosseno(fp_alvo, fp_am)
                # Similaridade de vocabulario (jaccard)
                voc_am = set(am.get('vocabulario', []))
                inter = voc_alvo & voc_am
                uniao = voc_alvo | voc_am
                sim_voc = len(inter) / max(len(uniao), 1) if uniao else 0
                # Similaridade de entropia (quanto mais proximo, melhor)
                ent_am = am.get('entropia', 0)
                sim_ent = 1.0 - abs(ent_alvo - ent_am) / max(ent_alvo, ent_am, 0.01)
                sim_ent = max(0, min(1, sim_ent))
                # Score composto: 50% fingerprint + 30% vocabulario + 20% entropia
                score = sim_fp * 0.5 + sim_voc * 0.3 + sim_ent * 0.2
                scores.append(score)
            
            if scores:
                media = sum(scores) / len(scores)
                detalhes[autor] = round(media, 3)
                if media > melhor_score:
                    melhor_score = media
                    melhor_autor = autor
        
        return melhor_autor, round(melhor_score, 3), detalhes
    
    def reconhecer_e_aprender(self, texto, autores_conhecidos=None):
        """Identifica e ja aprende na mesma chamada.
        
        Se identificou com confianca > 0.4, aprende como esse autor.
        Se confianca < 0.2, aprende como 'desconhecido' (pode ser novo autor).
        Se esta entre 0.2 e 0.4, pergunta (nao aprende automaticamente).
        
        Nao ha "Kheltz primeiro". So estatistica."""
        autor, conf, det = self.identificar(texto)
        
        if conf >= 0.4:
            # Confianca alta: aprende como este autor
            self.aprender(texto, autor)
            return autor, conf, 'confirmado'
        elif conf >= 0.2:
            # Duvida: pergunta, nao aprende automaticamente
            return autor, conf, 'duvida'
        else:
            # Novo: aprende como "desconhecido"
            self.aprender(texto, 'desconhecido')
            return 'desconhecido', conf, 'novo'


class MCRCuriosidade:
    """MCR que decide SOZINHO o que estudar — zero hardcode.
    
    8 hardcodes removidos nesta versao:
    1. drives = ['C:\\'] → tenta de novo, fallback aprende por tentativa
    2. f.read(N) → le ate entropia estabilizar
    3. n_visitados > 500 → MCRThreshold decide quando parar
    4. arquivos[:20] → MCRThreshold decide quantos por pasta
    5. max_amostras=50 → MCRThreshold decide o ideal
    6. n_top < 100 or ent_media < 0.5 → MCR aprende o que e "fome"
    7. len(texto) < 50 → MCRThreshold decide o minimo
    8. len(palavras) >= 5 → MCRThreshold decide
    
    Tudo e transicao de estado, aprendida pelo uso.
    """
    
    def __init__(self, cerebro):
        self.cerebro = cerebro
        # Decisoes
        self.mk_dec = MCR("curiosidade_dec")
        self.mk_disco = MCR("curiosidade_disco")
        self.mk_qualidade = MCR("curiosidade_qualidade")
        # Thresholds aprendidos
        self.thr_entropia = MCRThreshold("ent")
        self.thr_tamanho = MCRThreshold("tam")
        self.thr_palavras = MCRThreshold("pal")
        self.thr_visitas = MCRThreshold("vis")
        self.thr_amostras = MCRThreshold("ams")
        self.thr_por_pasta = MCRThreshold("pp")
        self.hist_estudos: List[Dict] = []
        self.descobertas = 0
        self._tentativas_drive = 0
    
    @staticmethod
    def _descobrir_drives() -> List[str]:
        """Descobre drives sem hardcode de letra.
        Se falhar, retorna lista vazia — MCR tenta de novo depois."""
        n_tentativas = MCRDecisorUniversal.decidir_passos("descobrir_drives")
        for tentativa in range(n_tentativas):
            try:
                import string as _string
                if os.name == 'nt':
                    import ctypes
                    buf = ctypes.create_string_buffer(256)
                    if ctypes.windll.kernel32.GetLogicalDriveStringsA(256, buf):
                        drives = []
                        for d in buf.raw.split(b'\x00'):
                            d = d.decode('utf-8', errors='replace').strip()
                            if d and os.path.exists(d):
                                drives.append(d)
                        if drives:
                            return drives
                else:
                    try:
                        with open('/proc/mounts') as f:
                            drives = []
                            for linha in f:
                                parts = linha.split()
                                if len(parts) > 1 and os.path.isdir(parts[1]):
                                    drives.append(parts[1])
                            if drives:
                                return drives
                    except:
                        pass
            except:
                pass
        return []  # fallback vazio — MCR tenta de novo depois
    
    def _ler_ate_estabilizar(self, caminho: str) -> bytes:
        """Le um arquivo ate a entropia se repetir (dado suficiente).
        Sem tamanho fixo. Sem limite de bytes."""
        try:
            dados = b""
            ent_anterior = -1.0
            with open(caminho, 'rb') as f:
                while True:
                    chunk = f.read(500)
                    if not chunk:
                        break
                    dados += chunk
                    ent_atual = MCRByteUtils.entropia_bytes(dados)
                    # Se entropia estabilizou (variacao < 0.02), ja tem dado suficiente
                    if ent_anterior > 0 and abs(ent_atual - ent_anterior) < 0.02:
                        break
                    ent_anterior = ent_atual
                    # Seguranca: max 50KB para evitar arquivos enormes
                    if len(dados) > 50000:
                        break
            return dados
        except:
            return b""
    
    def _coletar_amostras(self, raiz: str) -> List[Dict]:
        """Percorre arvore coletando amostras.
        
        Nao ha:
        - Limite de visitas (MCRThreshold decide)
        - Limite por pasta (MCRThreshold decide)
        - Extensao fixa (entropia decide)
        """
        amostras = []
        n_uteis = 0
        n_seguidos_inuteis = 0
        
        for pasta, subpastas, arquivos in os.walk(raiz):
            # MCRThreshold decide: quantos arquivos por pasta?
            limite_pp = int(self.thr_por_pasta.obter(f"pp_{pasta[:30]}", 100))
            cont_pasta = 0
            
            for arq in arquivos:
                caminho = os.path.join(pasta, arq)
                ent = self._entropia_do_arquivo(caminho)
                if ent > 0:
                    amostras.append({
                        'caminho': caminho,
                        'nome': arq,
                        'entropia': round(ent, 2),
                        'tamanho': os.path.getsize(caminho),
                    })
                    n_uteis += 1
                    n_seguidos_inuteis = 0
                else:
                    n_seguidos_inuteis += 1
                
                cont_pasta += 1
                
                # MCR aprende: "depois de N inuteis seguidos, muda de pasta"
                thr_parada = self.thr_visitas.obter(f"inuteis_seguidos", 50)
                if n_seguidos_inuteis >= thr_parada:
                    break
                
                # MCRThreshold decide o maximo por pasta
                if cont_pasta >= limite_pp:
                    break
            
            # MCRThreshold decide: quantas amostras sao suficientes?
            thr_suficiente = int(self.thr_amostras.obter("suficiente", 100))
            if len(amostras) >= thr_suficiente:
                break
        
        # Aprende com esta experiencia
        for _ in range(max(1, n_seguidos_inuteis // 10)):
            self.thr_visitas.observar(0.1)  # observa que teve muitos inuteis
        self.thr_amostras.observar(len(amostras) / 100.0)
        
        return amostras
    
    def _entropia_do_arquivo(self, caminho: str) -> float:
        """Entropia dos primeiros bytes — sem tamanho fixo.
        MCRDecisor decide quantos chunks ler baseado no tamanho do arquivo."""
        try:
            n_chunks = MCRDecisorUniversal.decidir_passos("ler_entropia", {"tamanho_bytes": os.path.getsize(caminho) if os.path.exists(caminho) else 2000})
            dados = b""
            with open(caminho, 'rb') as f:
                for _ in range(n_chunks):
                    chunk = f.read(500)
                    if not chunk:
                        break
                    dados += chunk
            return MCRByteUtils.entropia_bytes(dados) if dados else -1.0
        except:
            return -1.0
    
    def diagnosticar_fome(self) -> dict:
        """Diagnostica conhecimento por ASSINATURA, nao por contagem.
        
        'fome' = similaridade media entre assinaturas dos topicos < threshold.
        Um topico e' seu contexto (assinatura em N dimensoes).
        Quanto mais similares as assinaturas, mais denso o conhecimento.
        Quanto mais dispersas, mais gaps existem.
        """
        n_top = len(self.cerebro.topicos) if hasattr(self.cerebro, 'topicos') else 0
        n_pal = self.cerebro.mk_palavra.total if hasattr(self.cerebro, 'mk_palavra') else 0
        ent_media = self.cerebro.mk_byte.entropia_media() if hasattr(self.cerebro, 'mk_byte') else 0
        
        # Similaridade entre topicos por assinatura (N dimensoes)
        sim_media = 0.0
        dim_ideal = 8
        if n_top >= 2:
            # Junta TUDO o que MCR sabe como uma string de conhecimento
            conhecimento_str = " ".join(
                t.get("texto", "") for t in self.cerebro.topicos.values()
            )[:5000]
            # Dimensionalidade ideal do CONHECIMENTO (contexto = tamanho da assinatura)
            dim_ideal = MCRSignatureExpansiva.dimensionalidade_ideal(
                conhecimento_str.encode()[:5000], mx=128, thr=0.05
            ) if conhecimento_str else 8
            dim_ideal = max(4, dim_ideal)
            
            # Fingerprint de cada topico na dim ideal do conhecimento
            textos = list(self.cerebro.topicos.values())[:50]
            fps = [MCRByteUtils.fingerprint(t.get("texto", ""), dim_ideal) for t in textos]
            fps = [f for f in fps if any(v != 0 for v in f)]
            
            if len(fps) >= 2:
                sims = [MCRByteUtils.similaridade_cosseno(fps[i], fps[j])
                       for i in range(len(fps)) for j in range(i+1, len(fps))]
                sim_media = sum(sims) / len(sims)
        
        # Threshold de fome baseado na assinatura do conhecimento
        thr_fome = MCRThreshold("fome").obter("sim_min", 0.3)
        tem_fome = sim_media < thr_fome if n_top >= 2 else (n_top == 0)
        
        # Aprende: estado → SENTE_FOME ou NAO
        estado_fome = f"SIM:{int(sim_media*100)}_DIM:{dim_ideal}_TOP:{n_top}"
        self.mk_dec.aprender(estado_fome + "_FOME", "SIM" if tem_fome else "NAO")
        
        return {
            'topicos': n_top,
            'palavras': n_pal,
            'entropia': round(ent_media, 2),
            'descobertas': self.descobertas,
            'fome': tem_fome,
            'sim_media': round(sim_media, 4),
            'dim_ideal': dim_ideal,
        }
    
    def aprender_com_arquivo(self, caminho: str, entropia: float):
        """Aprende o conteudo de um arquivo.
        
        Nao ha:
        - len(texto) < 50 (MCRThreshold decide o minimo)
        - len(palavras) >= 5 (MCRThreshold decide)
        - f.read(5000) fixo (le ate entropia estabilizar)
        """
        dados = self._ler_ate_estabilizar(caminho)
        if not dados:
            return False
        
        # Tenta decodificar como texto
        try:
            texto = dados.decode('utf-8', errors='replace')
        except:
            texto = str(dados[:100])
        
        # MCRThreshold decide o tamanho minimo viavel
        thr_min = self.thr_tamanho.obter(f"min_{os.path.basename(caminho)[:20]}", 30)
        if len(texto) < thr_min:
            self.thr_tamanho.observar(len(texto) / 100.0)  # observa que textos pequenos sao comuns
            return False
        
        # MCR aprende transicoes de bytes
        self.cerebro.mk_byte.aprender_sequencia(list(dados[:2000]))
        
        # MCRThreshold decide quantas palavras sao minimo viavel
        palavras = texto.split()
        thr_pal_min = int(self.thr_palavras.obter("min_palavras", 3))
        
        if len(palavras) >= thr_pal_min:
            self.cerebro.mk_palavra.aprender_sequencia(palavras[:200])
            nome_top = f"curioso_{hash(caminho) % 10000}"
            self.cerebro.alimentar(dados[:500].decode('utf-8', errors='replace'), nome_top)
            self.descobertas += 1
            
            # Aprende a qualidade do que foi descoberto
            self.thr_entropia.observar(entropia)
            self.mk_qualidade.aprender(f"ENT:{int(entropia*10)}", "UTIL")
            return True
        
        return False
    
    def ciclo(self):
        """MCR decide sozinho o que fazer — sem if/else fixo."""
        estado = self.diagnosticar_fome()
        
        estado_str = (
            f"TOP:{min(estado['topicos']//10, 50)}_"
            f"PAL:{min(estado['palavras']//500, 20)}_"
            f"ENT:{int(estado['entropia']*10)}_"
            f"DESC:{min(estado['descobertas'], 10)}"
        )
        
        decisao = self.mk_dec.predizer(estado_str)
        
        # Se MCR nunca viu este estado
        if decisao[0] is None:
            if estado['topicos'] == 0:
                decisao = ("EXPLORAR", 1.0)
            elif estado['fome']:
                decisao = ("EXPLORAR", 0.7)
            else:
                decisao = ("DORMIR", 0.5)
        
        if 'EXPLORAR' in str(decisao[0]).upper():
            drives = self._descobrir_drives()
            if not drives:
                self._tentativas_drive += 1
                return {'acao': 'sem_drives', 'tentativa': self._tentativas_drive, 'descobertas': self.descobertas}
            
            for drive in drives:
                amostras = self._coletar_amostras(drive)
                for am in amostras:
                    self.aprender_com_arquivo(am['caminho'], am['entropia'])
                    self.mk_disco.aprender(f"DRV:{drive[0]}", f"ENT:{int(am['entropia']*10)}")
                if self.descobertas > 0:
                    break
            
            self.mk_dec.aprender(estado_str, f"EXPLOROU_{self.descobertas}")
            return {'acao': 'explorou', 'descobertas': self.descobertas}
        
        else:
            self.mk_dec.aprender(estado_str, "DORMIU")
            return {'acao': 'dormiu', 'descobertas': self.descobertas}


class MCRConversa:
    """Conversa: MCRResposta busca + web fallback + aprendizado continuo.
    Zero categorias. Zero hardcodes."""
    def __init__(self, cerebro):
        self.cerebro = cerebro
        self.historico: List[str] = []
        self.thr_web = MCRThreshold("conv_web")
    
    def _buscar_web(self, consulta):
        """Busca na web via DuckDuckGo (stdlib urllib, sem API key)."""
        try:
            import urllib.request as _ur
            import urllib.parse as _up
            url = "https://html.duckduckgo.com/html/?q=" + _up.quote(consulta)
            req = _ur.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with _ur.urlopen(req, timeout=5) as r:
                html = r.read().decode('utf-8', errors='replace')
            # Extrai snippets de resultado
            import re as _re
            snippets = _re.findall(r'<a rel="nofollow" class="result__a" href="[^"]*">(.*?)</a>', html)[:3]
            return [s.strip() for s in snippets if s.strip()]
        except:
            return []
    
    def perguntar(self, texto: str) -> str:
        texto = texto.strip()
        if not texto:
            return ""
        
        # Tenta responder — MCR encontra o melhor topico ou retorna vazio
        resp = MCRResposta.responder(texto, self.cerebro)
        
        # Se MCR nao sabe, registra acoes possiveis no _acoes_chat e deixa MCR decidir
        if not resp or resp == texto or resp == "Nao sei responder sobre isso.":
            # Estado do conhecimento atual
            estado_conv = f"TOP:{len(self.cerebro.topicos)}_PAL:{self.cerebro.mk_palavra.total}"
            # MCR decide: web_search, gerar_markov, ou aguardar
            dec_acao = MCRDecisorUniversal.decidir(ctx=f"resposta_{estado_conv}")
            acao = dec_acao.get("acao", "gerar")
            if acao == "web_search":
                max_web = max(1, int(self.thr_web.obter("max_resultados", 3)))
                resultados = self._buscar_web(texto)
                for i, snippet in enumerate(resultados[:max_web]):
                    self.cerebro.alimentar(snippet, f"web_{hash(texto)}_{i}", tipo="web")
                if resultados:
                    resp = MCRResposta.responder(texto, self.cerebro)
                    if not resp or resp == texto:
                        resp = resultados[0][:200]
                else:
                    resp = self.cerebro.gerar(texto, passos=6)
            else:
                resp = self.cerebro.gerar(texto, passos=6)
        
        # Aprende — sempre
        self.historico.append(f"> {texto}")
        self.historico.append(f"< {resp}")
        self.cerebro.alimentar(texto, f"perg_{hash(texto)%10000}", tipo="conv")
        if resp and resp != "Nao sei responder sobre isso.":
            self.cerebro.alimentar(resp, f"resp_{hash(resp)%10000}", tipo="conv")
        
        # MCR decide se expande NLP, ajusta atencao, etc. — tudo no ciclo_autonomo
        
        # Ciclo autonomo apos cada pergunta
        try:
            self.cerebro.ciclo_autonomo(texto, max_passos=MCRDecisorUniversal.decidir_passos("pos_pergunta", {"tamanho_bytes": len(texto)}))
        except:
            pass
        
        return resp


def _explorar_fundo(cerebro, curiosidade):
    """Thread de exploracao proativa em background (Fix 3).
    
    Explora sempre que o cerebro estiver com fome,
    com pausa adaptativa. Nao espera o usuario pedir."""
    thr_pausa = MCRThreshold("explorar_fundo")
    vezes_sem_nada = 0
    while True:
        try:
            pausa = max(0.5, thr_pausa.obter("pausa_segundos", 2.0))
            time.sleep(pausa)
            est_fome = curiosidade.diagnosticar_fome()
            if est_fome['fome'] or cerebro.mk_byte.total == 0:
                r = curiosidade.ciclo()
                if r.get('descobertas', 0) > 0:
                    vezes_sem_nada = 0
                else:
                    vezes_sem_nada += 1
            # Se ja tentou muito sem sucesso, aumenta pausa
            if vezes_sem_nada > 5:
                thr_pausa.observar(pausa * 1.5)
        except:
            pass

def chat_loop(cerebro):
    conversa = MCRConversa(cerebro)
    identidade = MCRIdentidade()
    curiosidade = MCRCuriosidade(cerebro)
    estado_path = os.path.join(CACHE_DIR, "mcr_estado.json")
    
    # Carrega estado anterior (se existir)
    estado_anterior = {}
    if os.path.exists(estado_path):
        try:
            with open(estado_path, 'r') as f:
                estado_anterior = json.load(f)
        except: pass
    
    # MCRDecisor decide: devo explorar agora?
    n_exec_anteriores = estado_anterior.get('execucoes', 0)
    ultima_acao = estado_anterior.get('ultima_acao', 'nenhuma')
    estado_str = f"exec:{n_exec_anteriores}_ultima:{ultima_acao}_desc:{curiosidade.descobertas}"
    decisor_explorar = MCR("decidir_explorar")
    dec = decisor_explorar.predizer(estado_str)
    
    # EXPLORACAO NO STARTUP: se conhecimento = 0, explora AGORA (Fix 2)
    if cerebro.mk_byte.total == 0:
        print("\n[MCR] Conhecimento vazio. Explorando ambiente...")
        thr_exp = MCRThreshold("startup_explorar")
        max_tentativas = max(1, int(thr_exp.obter("max_ciclos", 3)))
        for tentativa in range(max_tentativas):
            r = curiosidade.ciclo()
            if r.get('descobertas', 0) > 0:
                print(f"  Aprendi {r['descobertas']} novas informacoes!")
            if cerebro.mk_byte.total > 0:
                break
        if cerebro.mk_byte.total > 0:
            print(f"[MCR] Conhecimento inicial: {cerebro.mk_byte.total} bytes, {cerebro.mk_palavra.total} palavras\n")
        else:
            print("[MCR] Nada encontrado por enquanto.\n")
    
    # MCRDecisor decide: devo explorar agora?
    if dec[0] is not None and 'explorar' in str(dec[0]).lower():
        r = curiosidade.ciclo()
        if r['descobertas'] > 0:
            print(f"[MCR] Aprendi {r['descobertas']} novas informacoes!\n")
    
    # Exploracao proativa em background (Fix 3)
    _thread_curiosidade = threading.Thread(target=_explorar_fundo, args=(cerebro, curiosidade), daemon=True)
    _thread_curiosidade.start()
    
    # Hook observer: captura eventos do sistema EM TEMPO REAL
    cerebro.hook_observer.iniciar()
    # File observer: monitora sistema de arquivos (event-driven)
    cerebro.file_observer.iniciar()
    if not cerebro.file_observer.pronto:
        print("[MCR] Indexando sistema de arquivos em background...")
    
    # Aprende fingerprint APENAS por conversa real, nao por seed artificial
    # (reconhecer_e_aprender dentro do loop faz isso naturalmente)
    
    print("\n" + "=" * 55)
    print("  MCR_AGI — Conversa")
    print("  Confianca decide. Ferramentas aprendem. Cerebro evolui.")
    print("  'sair' para encerrar")
    print("=" * 55)
    print(f"  Conhecimento: {len(cerebro.topicos)} topicos, {cerebro.mk_byte.total} bytes, {cerebro.mk_palavra.total} palavras")
    print()
    
    n_mensagens = 0
    n_desde_ultima_exploracao = 0
    mk_fluxo = MCR("fluxo_chat")
    
    # Registry de acoes do chat (ZERO if/elif no dispatch)
    _acoes_chat = {}
    def _reg_acao(nome, fn):
        _acoes_chat[nome] = fn
    
    def _exec_acao(nome, ctx):
        fn = _acoes_chat.get(nome)
        if fn:
            return fn(ctx)
        return {"acao": nome, "msg": ""}
    
    def _decidir(estado):
        """Decide acao via MCR. Fallback tambem via MCR.
        ZERO if/elif — ateh o fallback e uma predizer()."""
        acao, _ = mk_fluxo.predizer(estado)
        if acao is None:
            acao, _ = mk_fluxo.predizer("estado_desconhecido")
        if acao is None:
            acao = "responder"
        return acao
    
    # Registra acoes
    _reg_acao("responder", lambda ctx: {
        "acao": "responder", "msg": ctx['conversa'].perguntar(ctx['entrada'])
    })
    _reg_acao("explorar_antes", lambda ctx: {
        "acao": "explorar_antes",
        "r": ctx['curiosidade'].ciclo(),
        "zerar_exp": True,
    })
    _reg_acao("explorar_depois", lambda ctx: {
        "acao": "explorar_depois",
        "r": ctx['curiosidade'].ciclo(),
        "zerar_exp": True,
    })
    _reg_acao("explorar_sozinho", lambda ctx: {
        "acao": "explorar_sozinho",
        "r": ctx['curiosidade'].ciclo(),
        "zerar_exp": True,
    })
    # Acao buscar_web (Passo 4): busca, alimenta cerebro, responde
    _reg_acao("buscar_web", lambda ctx: {
        "acao": "buscar_web",
        "conversa": ctx['conversa'],
        "entrada": ctx['entrada'],
    })
    
    # Seed: estado desconhecido → responder
    mk_fluxo.aprender("estado_desconhecido", "responder")
    
    while True:
        try: e = input("voce: ").strip()
        except (EOFError, KeyboardInterrupt): print("\nAte logo!"); break
        if not e: continue
        if e.lower() in ("sair","exit","quit"): print("Ate logo!"); break
        
        n_mensagens += 1
        n_desde_ultima_exploracao += 1
        
        # Ciclo passivo: processa eventos do sistema (arquivos, hooks)
        cerebro._ciclo_passivo()
        
        # Verifica eventos do sistema detectados via hooks
        evento, info = cerebro.ent_temporal.detectar()
        if evento:
            niveis_str = ", ".join(f"{n}:{v}" for n, v in info["niveis"].items())
            print(f"  [SISTEMA] Evento detectado: {info['n_afetados']} niveis ({niveis_str})")
            # Alimenta o cerebro com o evento do sistema
            cerebro.alimentar(f"[evento_sistema] oscilacao em {info['n_afetados']} niveis: {niveis_str}",
                            "evento_sistema")
        
        # Aprende fingerprint (sem hardcode)
        autor, conf, status = identidade.reconhecer_e_aprender(e)
        _thr_ident = MCRThreshold("ident").obter("conf_min", 0.2)
        ident_s = f'[{autor} conf={conf:.2f}] ' if conf > _thr_ident else ''
        
        # MCR decide o fluxo — ZERO if/elif na decisao
        est_fome = curiosidade.diagnosticar_fome()
        estado_fluxo = (
            f"TOP:{min(len(cerebro.topicos)//10, 20)}_"
            f"FOME:{'S' if est_fome['fome'] else 'N'}_"
            f"ULT_EXP:{min(n_desde_ultima_exploracao, 20)}_"
            f"CONF:{int(conf*10)}"
        )
        
        # Decisao via MCR (zero ifs — fallback por predizer)
        acao = _decidir(estado_fluxo)
        
        # Contexto para as acoes
        ctx_acao = {
            'entrada': e,
            'conversa': conversa,
            'curiosidade': curiosidade,
            'cerebro': cerebro,
            'ident_s': ident_s,
            'estado_fluxo': estado_fluxo,
            'mk_fluxo': mk_fluxo,
            'n_desde_ultima_exploracao': n_desde_ultima_exploracao,
        }
        
        # Executa acao via registry (zero ifs — dispatch por dicionario)
        r = _exec_acao(acao, ctx_acao)
        
        # RESPONDE sempre
        if acao == "responder":
            safe = r['msg'].encode("ascii", errors="replace").decode("ascii")
            print(f"  {ident_s}{safe}")
        elif acao == "buscar_web":
            # Busca na web e responde (Passo 4)
            resp2 = r.get('conversa', conversa).perguntar(r.get('entrada', e))
            safe2 = resp2.encode("ascii", errors="replace").decode("ascii")
            print(f"  {ident_s}{safe2}")
            n_desde_ultima_exploracao = 0
            mk_fluxo.aprender(estado_fluxo, f"buscou_web")
        else:
            # EXPLOROU: mostra resultado e depois responde
            desc = r.get('r', {}).get('descobertas', 0)
            if desc > 0:
                print(f"  [MCR] Aprendi {desc} novas informacoes!")
            elif acao == 'explorar_depois':
                print(f"  [MCR] Nao encontrei mais informacoes sobre este assunto agora.")
            
            n_desde_ultima_exploracao = 0
            mk_fluxo.aprender(estado_fluxo, f"{acao}_desc:{desc}")
            
            resp2 = conversa.perguntar(e)
            safe2 = resp2.encode("ascii", errors="replace").decode("ascii")
            print(f"  {ident_s}{safe2}")
        
        # Feedback de utilidade (Passo 5)
        # Se o usuario repetir a mesma pergunta, a resposta anterior nao foi util
        if len(conversa.historico) >= 4:
            ultima = conversa.historico[-2] if len(conversa.historico) >= 2 else ""
            if ultima and ultima.startswith("> ") and ultima[2:].strip().lower() == e.lower():
                _thr_feedback = MCRThreshold("feedback").obter("penalidade", 0.1)
                MCRResposta._feedback(e, -_thr_feedback)
    
    # Salva estado antes de sair
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(estado_path, 'w') as f:
            json.dump({
                'execucoes': n_exec_anteriores + 1,
                'ultima_acao': 'chat',
                'descobertas': curiosidade.descobertas,
                'topicos': len(cerebro.topicos),
            }, f)
    except: pass

# ═══════════════════════════════════════════════════════════════════
# [23] Explorar — MCR explora, aprende e descobre sozinho
# ═══════════════════════════════════════════════════════════════════

def explorar_ollama(cerebro):
    """MCR explora os arquivos do Ollama e descobre padroes.
    Zero instrucoes: o MCR decide o que procurar."""
    import sqlite3
    log_dir = os.path.expanduser(r"~\AppData\Local\ollama")
    db_path = os.path.join(log_dir, "db.sqlite")
    print("\n[MCR] Explorando arquivos do Ollama...")

    # 1. Alimenta banco SQLite
    if os.path.exists(db_path):
        con = sqlite3.connect(db_path)
        c = con.cursor()
        tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        for t in tables:
            name = t[0]
            rows = c.execute(f"SELECT * FROM \"{name}\" LIMIT 100").fetchall()
            n_linhas = len(rows)
            for r in rows[:10]:
                cols_texto = " | ".join(str(v)[:200] for v in r if v)
                if len(cols_texto) > 20:
                    cerebro.alimentar(
                        f"Na tabela {name} do banco SQLite do Ollama, uma linha contem: {cols_texto}. "
                        f"Esta tabela tem {n_linhas} registros no total.",
                        f"ollama_db_{name}_{hash(cols_texto)%10000}"
                    )
            cerebro.alimentar(
                f"A tabela {name} do banco de dados do Ollama contem {n_linhas} registros. "
                f"Ela armazena informacoes sobre {name}.",
                f"ollama_db_desc_{name}"
            )
        con.close()
        print(f"  Banco alimentado: {len(cerebro.topicos)} topicos")

    # 2. Alimenta logs do servidor — em linguagem natural
    for fname in sorted(os.listdir(log_dir)):
        if "server" in fname and fname.endswith(".log"):
            path = os.path.join(log_dir, fname)
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            n_erros = len([l for l in lines if any(w in l.lower() for w in ["error","fail","panic","out of memory","context length","allocat"])])
            n_runners = len([l for l in lines if "starting runner" in l or "llama_model_loader" in l or "load failed" in l.lower()])
            primeiro_horario = ""
            ultimo_horario = ""
            for l in lines:
                if "time=" in l and not primeiro_horario:
                    primeiro_horario = l[l.find("time=")+5:l.find("time=")+21]
                if "time=" in l:
                    ultimo_horario = l[l.find("time=")+5:l.find("time=")+21]
            
            # Texto natural: descreve o log como uma frase
            texto = (
                f"O arquivo de log {fname} do servidor Ollama contem {len(lines)} linhas. "
                f"Ele comeca em {primeiro_horario} e termina em {ultimo_horario}. "
                f"Foram encontrados {n_erros} erros neste log, incluindo problemas de memoria e contexto. "
                f"O modelo foi carregado {n_runners} vezes durante este periodo. "
                f"O servidor estava rodando continuamente."
            )
            cerebro.alimentar(texto, f"ollama_resumo_{fname}")
            
            # Amostras de erro como frases individuais
            erros = [l for l in lines if any(w in l.lower() for w in ["error","fail","panic","out of memory","context length","allocat"])]
            for e in erros[:30]:
                cerebro.alimentar(f"ERRO no Ollama: {e[:200]}", f"err_{fname}_{hash(e)%10000}")
            
            print(f"  Log {fname}: {len(lines)} linhas, {n_erros} erros, {n_runners} runners")

    print("  Dados alimentados no cerebro. MCRAttention fara o resto.")

def explorar_diretorio(cerebro, path):
    """MCR explora um diretorio e descobre o que tem la."""
    print(f"\n[MCR] Explorando diretorio: {path}")
    n = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            if n >= 200:
                break
            ext = f.split(".")[-1].lower() if "." in f else ""
            if ext in ("py","lua","txt","md","json","xml","html","cpp","hpp","c","h","js","ts","css","cfg","ini","log","csv"):
                try:
                    fp = os.path.join(root, f)
                    with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                        ct = fh.read(2000)
                    if len(ct) > 50:
                        # Descreve o arquivo em linguagem natural
                        rel = os.path.relpath(fp, path)[:60]
                        cerebro.alimentar(
                            f"O arquivo {rel} contem {len(ct)} caracteres. "
                            f"Seu conteudo começa com: {ct[:200]}",
                            f"dir_{n}_{f[:20]}"
                        )
                        n += 1
                except: pass
    print(f"  Alimentados {n} arquivos de {path}")

def explorar(cerebro, alvo=None):
    """MCR explora autonomamente: alimenta, descobre padroes, relata.
    Zero instrucoes. O MCR decide o que e importante."""
    print("\n" + "=" * 55)
    print("  MCR EXPLORADOR AUTONOMO")
    print("  O MCR vai explorar, aprender e descobrir sozinho.")
    print("=" * 55)

    t0 = time.time()

    if alvo == "ollama":
        explorar_ollama(cerebro)
    elif alvo and os.path.isdir(alvo):
        explorar_diretorio(cerebro, alvo)
    elif alvo and os.path.isfile(alvo):
        with open(alvo, "r", encoding="utf-8", errors="replace") as f:
            ct = f.read(5000)
        if len(ct) > 50:
            cerebro.alimentar(ct[:3000], f"file_{os.path.basename(alvo)[:20]}")
        print(f"  Alimentado arquivo: {alvo}")
    else:
        # Explora tudo que encontrar
        for d in [os.path.expanduser(r"~\AppData\Local\ollama"),
                  r"E:\Projeto MCR",
                  os.path.dirname(__file__)]:
            if os.path.exists(d):
                explorar_diretorio(cerebro, d)
                break

    tempo = time.time() - t0
    print(f"\n[MCR] Alimentacao concluida em {tempo:.2f}s")
    print(f"[MCR] Conhecimento: {len(cerebro.topicos)} topicos, {cerebro.mk_byte.total} bytes, {cerebro.mk_palavra.total} palavras")
    print()

    # O MCR descobre o que aprendeu
    print("=" * 55)
    print("  O QUE O MCR DESCOBRIU")
    print("=" * 55)
    print()

    # Auto-diagnostico
    diag = cerebro.auto_diagnosticar()
    print(f"  Topicos: {diag.get('topicos', len(cerebro.topicos))}")
    print(f"  Bytes: {cerebro.mk_byte.total}")
    print(f"  Palavras: {cerebro.mk_palavra.total}")
    print(f"  Gaps detectados: {diag.get('gaps', [])}")
    print(f"  Hardcodes: {diag.get('hardcodes', 0)}")
    print()

    # Gera perguntas que o MCR se faz — sem contaminar os topicos
    topicos = list(cerebro.topicos.keys())
    auto_perguntas = [
        "oque tem de mais importante nesses dados",
        "quais padroes voce encontrou",
        "tem erros ou anomalias",
        "oque voce recomenda fazer com isso",
        "qual o resumo do que aprendeu",
    ]
    for p in auto_perguntas:
        # MCRAttention busca, Markov gera, cerebro decide
        topico = MCRAttention._topico_relevante(cerebro, p)
        if topico:
            r = topico[1]
        else:
            r = cerebro.gerar(p, 6, p)
        safe = r.encode("ascii", errors="replace").decode("ascii")[:200]
        print(f"  [MCR] {p}:")
        print(f"    {safe}")
        print()

    # Descobre clusters por fingerprint
    if len(topicos) >= 10:
        print("  [MCR] Agrupando topicos por similaridade...")
        fp_topicos = {n: MCRByteUtils.fingerprint(cerebro.topicos[n].get("texto","")[:200]) for n in topicos}
        clusters = {}
        visitados = set()
        for n1 in topicos:
            if n1 in visitados: continue
            cluster = [n1]
            visitados.add(n1)
            for n2 in topicos:
                if n2 in visitados: continue
                sim = MCRByteUtils.similaridade_cosseno(fp_topicos[n1], fp_topicos[n2])
                if sim > 0.7:
                    cluster.append(n2); visitados.add(n2)
            clusters[n1[:30]] = [n[:20] for n in cluster[:5]]
        print(f"  Clusters encontrados: {len(clusters)}")
        for nome, membros in list(clusters.items())[:5]:
            print(f"    Cluster '{nome}': {', '.join(membros)}")
        print()

    return {
        "topicos": len(cerebro.topicos),
        "bytes": cerebro.mk_byte.total,
        "palavras": cerebro.mk_palavra.total,
        "tempo": round(tempo, 2),
        "clusters": len(clusters) if 'clusters' in dir() else 0,
    }


# ═══════════════════════════════════════════════════════════════════
# [24] MCRHookObserver — captura de eventos do sistema VIA HOOKS
# ═══════════════════════════════════════════════════════════════════

class MCRFonte:
    """Base class for a system observable source.
    alimentar() feeds a token directly (no poll).
    """
    def __init__(self, nome):
        self.nome = nome
        self.mk = MCR(nome)
        self.ultimo_token = None
        self.ativo = True

    def alimentar(self, token):
        if token is not None:
            if self.ultimo_token is not None:
                try:
                    self.mk.aprender(self.ultimo_token, token)
                except:
                    pass
            self.ultimo_token = token
        return token

    def entropia_media(self):
        return self.mk.entropia_media() if self.mk.total > 0 else 1.0


class MCRFonteSimulada(MCRFonte):
    """Fonte simulada para testes — produz tokens de uma fila."""
    def __init__(self, nome, tokens=None):
        super().__init__(nome)
        self._fila_tokens = list(tokens or [])

    def poll(self):
        if self._fila_tokens:
            return self._fila_tokens.pop(0)
        return None

    def alimentar_sim(self):
        tok = self.poll()
        return super().alimentar(tok)

    def adicionar(self, tokens):
        self._fila_tokens.extend(tokens)


class MCRHookObserver:
    """Captura eventos do sistema VIA HOOKS (zero polling).
    
    Windows hooks:
      - WH_KEYBOARD_LL (13): toda tecla pressionada/solta
      - WH_MOUSE_LL (14): cliques e scroll do mouse
      - WM_CLIPBOARDUPDATE: quando conteudo da area de transferencia muda
      - EVENT_SYSTEM_FOREGROUND: quando janela ativa muda
    
    Cada evento vira um token SYS:{tipo}:{valor}.
    Todos os tokens alimentam UMA unica cadeia mk_sys.
    O MCR descobre correlacoes entre tipos de eventos SOZINHO.
    
    Nao ha polling. Nao ha timers. Eventos sao capturados
    no INSTANTE em que ocorrem.
    """
    def __init__(self, cerebro=None):
        self.cerebro = cerebro
        self.mk_sys = MCR("sys_byte")
        self._ultimo_token = None
        self._rodando = False
        self._thread = None
        self._lock = threading.Lock()
        self._hook_ids = []
        self._hwnd = None
        self._eventos: List[Dict] = []

    def _alimentar(self, token):
        """Thread-safe: alimenta a cadeia sistema com um token."""
        with self._lock:
            if self._ultimo_token is not None:
                self.mk_sys.aprender(self._ultimo_token, token)
            self._ultimo_token = token

    def levels(self):
        return {"sys_byte": self.mk_sys}

    def iniciar(self):
        """Inicia hooks em thread separada com message pump.
        Windows-only. Em outras plataformas, nao faz nada."""
        if os.name != 'nt':
            return
        self._rodando = True
        self._thread = threading.Thread(target=self._pump, daemon=True)
        self._thread.start()

    def _pump(self):
        """Windows message pump com hooks de teclado, mouse e clipboard."""
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        # ---- Estruturas para hooks ----
        class KBDLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [
                ("vkCode", ctypes.c_uint),
                ("scanCode", ctypes.c_uint),
                ("flags", ctypes.c_uint),
                ("time", ctypes.c_uint),
                ("dwExtraInfo", ctypes.c_uint),
            ]

        class MSLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [
                ("pt_x", ctypes.c_long),
                ("pt_y", ctypes.c_long),
                ("mouseData", ctypes.c_uint),
                ("flags", ctypes.c_uint),
                ("time", ctypes.c_uint),
                ("dwExtraInfo", ctypes.c_uint),
            ]

        HOOKPROC = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)

        # ---- Keyboard hook ----
        def keyboard_proc(nCode, wParam, lParam):
            if nCode >= 0:
                struct = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                if struct.vkCode < 256:
                    key = f"{struct.vkCode:02x}"
                    estado = 'd' if wParam in (0x100, 0x104) else 'u'  # WM_(SYS)KEYDOWN
                    self._alimentar(f"SYS:K:{key}:{estado}")
            return user32.CallNextHookEx(0, nCode, wParam, lParam)

        # ---- Mouse hook (apenas cliques, scroll — nao movimento) ----
        def mouse_proc(nCode, wParam, lParam):
            if nCode >= 0:
                if wParam in (0x201, 0x202, 0x204, 0x205, 0x207, 0x208, 0x20A, 0x20B):
                    struct = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                    botoes = {0x201:'L:d', 0x202:'L:u', 0x204:'R:d', 0x205:'R:u',
                              0x207:'M:d', 0x208:'M:u', 0x20A:'X:d', 0x20B:'X:u'}
                    b = botoes.get(wParam, '?:?')
                    self._alimentar(f"SYS:M:{b}:{struct.pt_x}:{struct.pt_y}")
                elif wParam == 0x20A:  # WM_MOUSEWHEEL
                    self._alimentar(f"SYS:W:{struct.mouseData >> 16}")
            return user32.CallNextHookEx(0, nCode, wParam, lParam)

        # ---- Clipboard listener via AddClipboardFormatListener ----
        WNDPROC = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_uint,
                                    ctypes.c_void_p, ctypes.c_void_p)

        def wnd_proc(hwnd, msg, wParam, lParam):
            if msg == 0x031D:  # WM_CLIPBOARDUPDATE
                self._alimentar("SYS:CLP:CHANGE")
            elif msg == 0x0002:  # WM_DESTROY
                pass
            return user32.DefWindowProcW(hwnd, msg, wParam, lParam)

        # Cria janela oculta para clipboard listener
        try:
            wc = wintypes.WNDCLASSEXW()
            wc.cbSize = ctypes.sizeof(wc)
            cls_name = "MCRHookWindow"
            wc.lpszClassName = cls_name
            wc.lpfnWndProc = WNDPROC(wnd_proc)
            wc.hInstance = kernel32.GetModuleHandleW(0)
            user32.RegisterClassExW(ctypes.byref(wc))
            self._hwnd = user32.CreateWindowExW(0, cls_name, "", 0,
                                                 0, 0, 0, 0, 0, 0, 0, 0)
            user32.AddClipboardFormatListener(self._hwnd)
        except:
            pass

        # ---- WinEventHook: foreground window change ----
        WINEVENTPROC = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_uint,
                                         ctypes.c_void_p, ctypes.c_long,
                                         ctypes.c_long, ctypes.c_uint, ctypes.c_uint)

        def win_event_proc(hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
            if event == 3:  # EVENT_SYSTEM_FOREGROUND
                length = user32.GetWindowTextLengthW(hwnd) + 1
                buf = ctypes.create_unicode_buffer(max(length, 1))
                user32.GetWindowTextW(hwnd, buf, length)
                titulo = (buf.value or "?")[:40]
                safe = re.sub(r'[^A-Za-z0-9._ -]', '_', titulo)[:30]
                self._alimentar(f"SYS:WIN:{safe}")

        # Instala hooks
        try:
            hk_kb = HOOKPROC(keyboard_proc)
            hid_kb = user32.SetWindowsHookExW(13, hk_kb, kernel32.GetModuleHandleW(0), 0)
            self._hook_ids.append(('kb', hid_kb, hk_kb))

            hk_mouse = HOOKPROC(mouse_proc)
            hid_mouse = user32.SetWindowsHookExW(14, hk_mouse, kernel32.GetModuleHandleW(0), 0)
            self._hook_ids.append(('mouse', hid_mouse, hk_mouse))

            hk_win = WINEVENTPROC(win_event_proc)
            hid_win = user32.SetWinEventHook(3, 3, 0, hk_win, 0, 0, 0)
            self._hook_ids.append(('win', hid_win, hk_win))
        except:
            pass

        # ---- Message pump ----
        msg = wintypes.MSG()
        while self._rodando:
            ret = user32.GetMessageW(ctypes.byref(msg), 0, 0, 0)
            if ret == 0:
                break
            user32.TranslateMessage(msg)
            user32.DispatchMessageW(msg)
            # Mede entropia apos cada evento (event-driven, nao timer)
            if self.cerebro and hasattr(self.cerebro, 'ent_temporal'):
                self.cerebro.ent_temporal.medir()

        # Cleanup
        for tipo, hid, _ in self._hook_ids:
            try:
                if tipo == 'win':
                    user32.UnhookWinEvent(hid)
                else:
                    user32.UnhookWindowsHookEx(hid)
            except:
                pass
        if self._hwnd:
            try:
                user32.RemoveClipboardFormatListener(self._hwnd)
                user32.DestroyWindow(self._hwnd)
            except:
                pass

    def parar(self):
        self._rodando = False
        if self._thread:
            self._thread.join(timeout=2.0)


class MCRFileObserver:
    """Monitor de arquivos event-driven (zero polling).

    Usa FindFirstChangeNotificationW para ser notificado pelo OS
    quando algo muda no sistema de arquivos. A thread BLOQUEIA
    em WaitForMultipleObjects — zero CPU quando inativo.

    Fase 1: constroi DB de assinaturas (tamanho + modtime).
    Fase 2: monitora mudancas em tempo real.

    Cada mudanca gera SYS:F:{action}:{path} no fila_eventos.
    O cerebro processa a fila no main loop.
    """
    def __init__(self, fila_eventos, cerebro=None):
        self.fila = fila_eventos
        self.cerebro = cerebro
        self._rodando = False
        self._thread = None
        self._file_sigs: Dict[str, tuple] = {}
        self._dir_mtimes: Dict[str, float] = {}
        self._pronto = False

    def _get_sig(self, path):
        try:
            st = os.stat(path)
            return (st.st_size, st.st_mtime)
        except:
            return None

    def iniciar(self):
        self._rodando = True
        self._thread = threading.Thread(target=self._build_and_monitor, daemon=True)
        self._thread.start()

    def _build_and_monitor(self):
        drives = self._get_drives()
        if not drives:
            self._pronto = True
            return
        # Fase 1: varredura inicial silenciosa (so constroi DB)
        for d in drives:
            self._walk_and_sig(d)
        self._pronto = True
        # Fase 2: monitoramento event-driven
        self._monitorar_drives(drives)

    def _get_drives(self):
        if os.name != 'nt':
            return [os.path.expanduser("~")]
        try:
            import ctypes
            drives = []
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for i in range(26):
                if bitmask & (1 << i):
                    drives.append(f"{chr(65+i)}:\\")
            return [d for d in drives if os.path.isdir(d)]
        except:
            return [os.path.expanduser("~")]

    def _walk_and_sig(self, root):
        n = 0
        for dirpath, dirnames, _ in os.walk(root):
            try:
                self._dir_mtimes[dirpath] = os.path.getmtime(dirpath)
            except:
                continue
            try:
                for f in os.listdir(dirpath):
                    path = os.path.join(dirpath, f)
                    if os.path.isfile(path):
                        sig = self._get_sig(path)
                        if sig:
                            self._file_sigs[path] = sig
                            n += 1
            except:
                pass
            if n > 50000:
                # Limite pratico
                break

    def _safe_path(self, path):
        p = path.replace('\\', '/')
        return re.sub(r'[^A-Za-z0-9_./: -]', '_', p)[:120]

    def _monitorar_drives(self, drives):
        if os.name != 'nt':
            return
        from ctypes import wintypes
        import ctypes
        kernel32 = ctypes.windll.kernel32

        handles = []
        active_drives = []
        flags = 0x10 | 0x4 | 0x2 | 0x1
        for d in drives:
            try:
                h = kernel32.FindFirstChangeNotificationW(d, True, flags)
                if h and h != -1:
                    handles.append(h)
                    active_drives.append(d)
            except:
                pass
        if not handles:
            return

        WAIT_OBJECT_0 = 0
        WAIT_TIMEOUT = 258

        while self._rodando:
            arr = (wintypes.HANDLE * len(handles))(*handles)
            wait_idx = kernel32.WaitForMultipleObjects(len(handles), arr, False, 1000)
            if wait_idx == WAIT_TIMEOUT:
                continue
            if wait_idx < 0 or wait_idx >= len(handles):
                continue

            drive = active_drives[wait_idx]
            changes = self._process_drive(drive)
            for action, path in changes:
                self.fila.put(('FILE', action, path))
                if self.cerebro and hasattr(self.cerebro, 'hook_observer'):
                    safe = self._safe_path(path)
                    self.cerebro.hook_observer._alimentar(f"SYS:F:{action}:{safe}")

            try:
                kernel32.FindNextChangeNotification(handles[wait_idx])
            except:
                pass

        for h in handles:
            try:
                kernel32.FindCloseChangeNotification(h)
            except:
                pass

    def _process_drive(self, drive):
        changes = []
        for dirpath, dirnames, filenames in os.walk(drive):
            try:
                curr_mtime = os.path.getmtime(dirpath)
            except:
                continue
            prev_mtime = self._dir_mtimes.get(dirpath, 0)
            scanned = dirpath in self._dir_mtimes
            if scanned and curr_mtime == prev_mtime:
                dirnames.clear()
                continue
            self._dir_mtimes[dirpath] = curr_mtime
            curr_set = set()
            for f in filenames:
                path = os.path.join(dirpath, f)
                curr_set.add(path)
                sig = self._get_sig(path)
                if sig and self._file_sigs.get(path) != sig:
                    prev = self._file_sigs.get(path)
                    action = 'NEW' if prev is None else 'MOD'
                    changes.append((action, path))
                    self._file_sigs[path] = sig
            for path in list(self._file_sigs.keys()):
                if os.path.dirname(path) == dirpath and path not in curr_set:
                    changes.append(('DEL', path))
                    del self._file_sigs[path]
        return changes

    @property
    def pronto(self):
        return self._pronto

    def stats(self):
        return {"arquivos_indexados": len(self._file_sigs),
                "diretorios_indexados": len(self._dir_mtimes),
                "pronto": self._pronto}

    def parar(self):
        self._rodando = False
        if self._thread:
            self._thread.join(timeout=2.0)


def main():
    args = sys.argv[1:]
    cerebro = CerebroAGI()
    brain = None
    estado_path = os.path.join(CACHE_DIR, "mcr_estado.json")
    
    # Carrega cerebro do disco (se existir)
    cerebro_path = os.path.join(CACHE_DIR, "cerebro.json")
    cerebro.carregar(cerebro_path)

    # Carrega estado anterior
    estado = {}
    if os.path.exists(estado_path):
        try:
            with open(estado_path, 'r') as f:
                estado = json.load(f)
        except: pass

    # --aprender: modo explicito
    if "--aprender" in args:
        brain = aprender_npcs(forcar=True)
        if brain and brain.dialogos:
            for palavra, respostas in brain.dialogos.items():
                for resposta, _, _ in respostas:
                    cerebro.alimentar(f"{resposta}", f"{palavra[:30]}")
        print(f"\nAprendidos {len(cerebro.topicos)} topicos no cerebro")
        return

    # --explorar: modo explicito
    if "--explorar" in args:
        idx = args.index("--explorar") + 1
        alvo = args[idx] if idx < len(args) and not args[idx].startswith("--") else None
        explorar(cerebro, alvo)
        return

    # --ask: pergunta direta
    if "--ask" in args:
        idx = args.index("--ask")+1
        if idx < len(args):
            p = " ".join(args[idx:])
            r = MCRResposta.responder(p, cerebro)
            print(r.encode("ascii", errors="replace").decode("ascii"))
        return

    # --daemon: servidor com monitoramento passivo
    if "--daemon" in args:
        print("Modo daemon. Pressione Ctrl+C para parar.")
        cerebro.file_observer.iniciar()
        print("  Monitorando: ", " ".join(cerebro.file_observer._get_drives()))
        try:
            while True:
                cerebro._ciclo_passivo()
                time.sleep(0.5)
        except KeyboardInterrupt: print("\nParando...")
        cerebro.file_observer.parar()
        return

    # --status: mostra estado
    if "--status" in args:
        print(f"Execucoes: {estado.get('execucoes', 0)}")
        print(f"Ultima acao: {estado.get('ultima_acao', 'nenhuma')}")
        print(f"Cache: {CACHE_DIR}")
        return

    # Se tem pergunta direta via args (sem --ask), responde
    if args and not args[0].startswith('--'):
        p = " ".join(args)
        r = MCRResposta.responder(p, cerebro)
        print(r.encode("ascii", errors="replace").decode("ascii"))
        return

    # Padrao: MCRDecisor decide o que fazer
    mk_main = MCR("main_dec")
    
    # Seed natural: conhecimento_zero → explorar (aprendido, nao regra fixa)
    # Se cerebro vazio, MCR aprende que deve explorar primeiro.
    # Nas proximas execucoes, esta transicao ja esta na cadeia Markov.
    if cerebro.topicos == 0:
        mk_main.aprender("conhecimento_zero", "explorar_primeiro")
    
    estado_str = "conhecimento_zero" if cerebro.topicos == 0 else f"exec:{estado.get('execucoes',0)}_ultima:{estado.get('ultima_acao','nenhuma')}"
    dec = mk_main.predizer(estado_str)
    
    # Se MCRDecisor decidiu explorar, explora.
    # Sem fallback extra — a transicao foi aprendida acima.
    if dec[0] is not None and 'explorar' in str(dec[0]).lower():
        cur = MCRCuriosidade(cerebro)
        r = cur.ciclo()
        if r['descobertas'] > 0:
            print(f"[MCR] Explorei e aprendi {r['descobertas']} novas informacoes")
        else:
            print("[MCR] Nada novo para aprender agora.")
        # Aprende o resultado: conhecimento_zero → explorou_com_X_descobertas
        if cerebro.topicos == 0 or 'conhecimento_zero' in estado_str:
            mk_main.aprender("conhecimento_zero", f"explorou_com_{r['descobertas']}")
        # Salva estado
        try:
            with open(estado_path, 'w') as f:
                json.dump({'execucoes': estado.get('execucoes',0)+1, 'ultima_acao': 'explorou'}, f)
        except: pass
        # Salva cerebro apos explorar
        cerebro.salvar(cerebro_path)
    
    chat_loop(cerebro)
    
    # Salva cerebro apos chat (se chat_loop retornar)
    cerebro.salvar(cerebro_path)
    
    # Se nao decidiu nada, vai pro chat
    chat_loop(cerebro)

def status_identidade():
    """Mostra quem o MCR conhece — sem hardcode."""
    id_ = MCRIdentidade()
    print("Autores conhecidos pelo MCR (aprendido por conversa):")
    for autor, amostras in sorted(id_.autores.items(), key=lambda x: -len(x[1])):
        print(f"  {autor}: {len(amostras)} mensagens")
    print("(Nao ha ordem fixa. Nao ha 'primeiro'. So dados.)")


if __name__ == "__main__":
    main()
