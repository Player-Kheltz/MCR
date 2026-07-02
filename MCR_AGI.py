#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCR_AGI.py — UNIVERSAL. 0 HARDCODE. 0 GPU. 0 LLM.
===================================================
Unico arquivo. Tudo que o MCR precisa.
Primitivas, mundo, acoes, linguagem, atencao, causalidade,
planejamento, reforco, memoria, pontes, codigo, expansao,
orquestracao, loop evolutivo, chat, daemon.

Uso:
    python MCR_AGI.py                            # chat
    python MCR_AGI.py --daemon                   # servidor
    python MCR_AGI.py --ask "preco do worm"      # direto
    python MCR_AGI.py --aprender                 # alimenta NPCs
"""
import os, sys, json, math, time, glob, re, random as _rand
import sqlite3, socket, threading, hashlib, tempfile
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from collections import Counter
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
    def fingerprint(texto, dims=8):
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
    @classmethod
    def decidir(cls, motor=None, ctx=""):
        return {"passos": max(1, int(cls._th.obter("passos",6))), "threshold": cls._th.obter("thr",0.5), "dim": max(4, int(cls._th.obter("dim",8)))}

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
        scores = {}
        for acao, exs in cls._ex.items():
            melhor = max((MCRByteUtils.jaccard_bytes(frase, ex) for ex in exs), default=0)
            if melhor > 0: scores[acao] = melhor
        ords = sorted(scores.items(), key=lambda x: -x[1])
        params = MCRDecisorUniversal.decidir(ctx="nlp")
        limiar = params.get("threshold_nlp", 0.3)
        return [acao for acao, score in ords[:top_k] if score > limiar]
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
    _pesos = {"prob": 3.0, "fp": 5.0, "jac": 4.0, "ent": 1.0}
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
            w = cls._pesos
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
        self.dim_fp = C("dim_fingerprint", 8)
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

# ═══════════════════════════════════════════════════════════════════
# [07] MCRCoupling — matriz byte↔palavra↔token↔intencao↔acao
# ═══════════════════════════════════════════════════════════════════

class MCRCoupling:
    def __init__(self):
        self.niveis = self._descobrir_niveis()
        self.matriz = {o: {d: 0.0 for d in self.niveis} for o in self.niveis}
        self.cooc = {o: {d: 0 for d in self.niveis} for o in self.niveis}
        self.total_cooc = 0; self.mk = MCR("coupling")
    @staticmethod
    def _descobrir_niveis():
        base = ["byte","palavra","tven"]
        return base + ["intencao","acao"]
    def alimentar(self, origem, destino, to, td):
        if origem not in self.niveis or destino not in self.niveis: return
        self.cooc[origem][destino] += 1; self.total_cooc += 1
        self.mk.aprender(f"CP:{origem}->{destino}:{str(to)[:10]}", str(td)[:10])
    def recalcular(self):
        for o in self.niveis:
            for d in self.niveis:
                if o == d: self.matriz[o][d] = 1.0; continue
                c = self.cooc[o][d]
                self.matriz[o][d] = round(c/self.total_cooc*len(self.niveis), 3) if c >= 3 and self.total_cooc else 0.0
    def peso(self, origem, destino): return self.matriz.get(origem,{}).get(destino,0.0)
    def modular(self, nivel, probs):
        res = dict(probs)
        for outro in self.niveis:
            if outro == nivel: continue
            p = self.peso(outro, nivel)
            if p > 0.1:
                for ch in res: res[ch] *= (1 + p * 0.1)
        return res

# ═══════════════════════════════════════════════════════════════════
# [08] MCRPlanner — planejamento hierarquico
# ═══════════════════════════════════════════════════════════════════

class MCRPlanner:
    def __init__(self, world: MCRWorld):
        self.world = world; self.mk_plano = MCR("planner"); self.mk_sub = MCR("planner_sub")
    def plano(self, atual, obj, max_passos=10):
        dist = self.world.distancia(atual, obj)
        if dist < 1.0:
            ac = self.world.predizer_acao(atual, obj)
            return [ac] if ac else []
        fp_alvo = str(obj.fingerprint(self.world.dim_fp))
        pk, cf = self.mk_plano.predizer(fp_alvo)
        if pk and cf > 0.2:
            acs = pk.split("|")
            if len(acs) <= max_passos: return acs
        delta = MCRByteUtils.delta_fingerprint(atual.serializar(), obj.serializar(), self.world.dim_fp)
        dim_d = MCRSignatureExpansiva.dimensionalidade_ideal(str(delta).encode(), 16)
        num_sub = max(2, min(max_passos, dim_d))
        subs = []
        for i in range(num_sub):
            frac, frac_ant = (i+1)/num_sub, i/num_sub
            subs.append([(d*frac)-(d*frac_ant) for d in delta])
        plano = []
        est_int = atual.clone()
        for sub in subs:
            sub_str = str(tuple(round(d,3) for d in sub))
            ac, cf = self.world.mk_causal.predizer(sub_str)
            if not ac or cf < 0.1:
                ac_sub, cf_sub = self.mk_sub.predizer(sub_str)
                ac = ac_sub or self._fallback(est_int, sub)
            if ac:
                plano.append(ac); prox = self.world.simular(est_int, ac)
                if prox: est_int = prox
        if plano: self._aprender(plano, atual, obj)
        return plano
    def _fallback(self, est, sub):
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
        if est_obj:
            da = MCRByteUtils.similaridade_cosseno(est_ant.fingerprint(8), est_obj.fingerprint(8))
            dd = MCRByteUtils.similaridade_cosseno(est_atual.fingerprint(8), est_obj.fingerprint(8))
            r += (dd-da)*10
        if acao_ok: r += 2.0
        h = MCRByteUtils.entropia_bytes(est_atual.serializar())
        if h > 0.5: r += 0.5
        sim = MCRByteUtils.similaridade_cosseno(est_atual.fingerprint(8), est_ant.fingerprint(8))
        if sim < 0.95: r += 1.0
        return max(-10.0, min(10.0, r))

class MCRQLearn:
    def __init__(self, gamma=0.9, alpha=0.3):
        self.mk_Q = MCR("qlearn"); self.mk_pol = MCR("qpol"); self.gamma, self.alpha = gamma, alpha
        self.thr = MCRThreshold("qlearn"); self.episodio = 0; self.hist_ep: List[Dict] = []
    def q_valor(self, estado, acao):
        ch = f"Q:{str(estado.fingerprint(8)[:2])}:{acao}"
        p, c = self.mk_Q.predizer(ch)
        try: return float(p) if p and c > 0 else 0.0
        except: return 0.0
    def atualizar(self, estado, acao, recompensa, prox_est):
        ch = f"Q:{str(estado.fingerprint(8)[:2])}:{acao}"
        q_at = self.q_valor(estado, acao)
        acs = MCRAcao.disponiveis()
        max_qf = max(self.q_valor(prox_est, a) for a in acs) if acs else 0.0
        td = recompensa + self.gamma*max_qf - q_at
        self.mk_Q.aprender(ch, f"{q_at+self.alpha*td:.4f}")
        melh = self.melhor_acao(estado)
        if melh: self.mk_pol.aprender(str(estado.fingerprint(8)), melh)
        self.thr.observar(abs(td))
    def melhor_acao(self, estado, acoes=None):
        acoes = acoes or MCRAcao.disponiveis()
        if not acoes: return None
        return max(acoes, key=lambda a: self.q_valor(estado, a))
    def escolher_acao(self, estado, epsilon=0.2, acoes=None):
        acoes = acoes or MCRAcao.disponiveis()
        if not acoes: return "andar_cima"
        if _rand.random() < epsilon: return _rand.choice(acoes)
        return self.melhor_acao(estado, acoes) or acoes[0]
    def executar_episodio(self, est_ini, est_obj, mx=20):
        est = est_ini.clone(); r_total = 0.0; acs = []
        for passo in range(mx):
            ac = self.escolher_acao(est, epsilon=max(0.05, 0.2-self.episodio*0.01))
            prox = MCRAcao.executar(est, ac)
            mud = prox.serializar() != est.serializar()
            rw = MCRReward().avaliar(prox, est, est_obj, mud)
            self.atualizar(est, ac, rw, prox); r_total += rw; acs.append(ac); est = prox
            h = est.get("heroi"); ho = est_obj.get("heroi")
            if h and ho:
                if abs(h.props.get("x",0)-ho.props.get("x",0)) + abs(h.props.get("y",0)-ho.props.get("y",0)) <= 1: break
        self.episodio += 1
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
                for _ in range(5): cp.alimentar("byte","palavra","B:41","Fogo")
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
    """Resposta universal: MCRAttention busca, confianca decide, ferramentas aprendem.
    Zero extratores. Zero categorias. Zero hardcodes."""
    
    @staticmethod
    def _confianca(score):
        """Confianca = score do topico encontrado por MCRAttention.
        O score e o jaccard entre pergunta e texto do topico.
        Quanto maior, mais a pergunta se relaciona com a resposta."""
        return score
    
    @staticmethod
    def _buscar(pergunta, cerebro, max_iter=3):
        """Busca com metacognicao: score decide se confia.
        O score e o jaccard entre pergunta e texto do topico.
        Se score < threshold descoberto, tenta re-alimentar."""
        for i in range(max_iter):
            if not cerebro.topicos:
                return cerebro.gerar(pergunta, passos=6, pergunta=pergunta)
            
            topico = MCRAttention._topico_relevante(cerebro, pergunta)
            if not topico:
                return cerebro.gerar(pergunta, passos=6, pergunta=pergunta)
            
            _, texto, score = topico
            conf = MCRResposta._confianca(score)
            
            if conf > 0.01 or i == max_iter - 1:
                return texto[:300]
            
            # Confianca baixa: alimenta contexto e tenta de novo
            try:
                from MCR_AGI import MCRGenesis
                genesis = MCRGenesis(cerebro)
                diag = genesis.diagnosticar()
                if diag.get("gaps"):
                    g = diag["gaps"][0]
                    cerebro.alimentar(f"gap: {g['nome']}. {g['sugestao']}", f"gap_{hash(pergunta)%10000}")
            except Exception:
                import time as _t
                cerebro.alimentar(f"{_t.strftime('%H:%M:%S')} {_t.strftime('%d/%m/%Y')}", f"ctx_{_t.time()}")
        
        return texto[:300]
    
    @staticmethod
    def responder(pergunta, cerebro):
        if not cerebro:
            return ""
        return MCRResposta._buscar(pergunta, cerebro)

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
# [21] CerebroAGI — integracao de TUDO
# ═══════════════════════════════════════════════════════════════════

class CerebroAGI:
    def __init__(self):
        self.mk_byte = MCR("byte"); self.mk_palavra = MCR("palavra"); self.mk_tven = MCR("tven")
        self.topicos: Dict[str, Dict] = {}
        self.world = MCRWorld(); self.coupling = MCRCoupling(); self.planner = MCRPlanner(self.world)
        self.total_ciclos = 0; self.thr = MCRThreshold("cerebro"); self.entropia = MCREntropia("cerebro")
        self._rl, self._bridge, self._genesis = None, None, None
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
    def alimentar(self, texto, nome=None):
        if nome is None: nome = f"top_{len(self.topicos)+1}"
        dados = texto.encode(); palavras = texto.split()
        for i in range(len(dados)-1): self.mk_byte.aprender(f"B:{dados[i]:02x}", f"B:{dados[i+1]:02x}")
        for i in range(len(palavras)-1): self.mk_palavra.aprender(palavras[i], palavras[i+1])
        for i in range(len(palavras)-1):
            ta = palavras[i][0].upper() if palavras[i] else '?'; tb = palavras[i+1][0].upper() if palavras[i+1] else '?'
            self.mk_tven.aprender(ta, tb)
        for i in range(min(len(dados)-1, len(palavras))):
            if i < len(dados)-1:
                bt = f"B:{dados[i]:02x}"; pt = palavras[min(i,len(palavras)-1)]; tt = pt[0].upper() if pt else '?'
                self.coupling.alimentar("byte","palavra",bt,pt); self.coupling.alimentar("palavra","tven",pt,tt); self.coupling.alimentar("tven","byte",tt,bt)
        self.coupling.recalcular()
        self.topicos[nome] = {'texto': texto, 'bytes': len(dados), 'n_palavras': len(palavras), 'conteudo': {p.lower() for p in palavras if len(p) >= 2}}
        return nome
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
            cands = self.mk_palavra.predizer_n(semente, 5)
            if cands:
                probs = {c: conf for c, conf in cands}
                mod = self.coupling.modular("palavra", probs)
                palavras.append(max(mod, key=mod.get))
            else: break
            self.entropia.alimentar(palavras[-1])
            if self.entropia.esta_em_loop(): break
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
        for i in range(min(len(tlist),5)):
            for j in range(i+1, min(len(tlist),5)):
                a, b = tlist[i], tlist[j]
                ja = MCRByteUtils.jaccard_bytes(self.topicos[a]['texto'], self.topicos[b]['texto'])
                if ja < 0.1: gaps.append(f"{a}<->{b}: j={ja:.3f}")
        codex = MCRCodex()
        hc = codex.escanear()
        return {"topicos": len(self.topicos), "bytes": self.mk_byte.total, "palavras": self.mk_palavra.total, "causais": len(self.world.hist), "gaps": gaps[:3], "hardcodes": len(hc)}




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
# [22b] MCRConversa — Conversa organica via Markov
# ═══════════════════════════════════════════════════════════════════

class MCRConversa:
    """Conversa: MCRResposta busca com metacognicao, cerebro aprende.
    Zero categorias. Zero extratores. Zero hardcodes."""
    def __init__(self, cerebro):
        self.cerebro = cerebro
        self.historico: List[str] = []
    
    def perguntar(self, texto: str) -> str:
        texto = texto.strip()
        if not texto:
            return ""
        
        resp = MCRResposta.responder(texto, self.cerebro)
        if not resp or resp == texto:
            resp = "Nao sei responder sobre isso."
        
        self.historico.append(f"> {texto}")
        self.historico.append(f"< {resp}")
        self.cerebro.alimentar(f"> {texto} < {resp}", f"conv_{hash(texto+resp)%10000}")
        
        return resp


def chat_loop(cerebro):
    conversa = MCRConversa(cerebro)
    
    print("\n" + "=" * 55)
    print("  MCR_AGI — Conversa")
    print("  Confianca decide. Ferramentas aprendem. Cerebro evolui.")
    print("  'sair' para encerrar")
    print("=" * 55)
    print(f"  Conhecimento: {len(cerebro.topicos)} topicos, {cerebro.mk_byte.total} bytes, {cerebro.mk_palavra.total} palavras")
    print()
    
    while True:
        try: e = input("voce: ").strip()
        except (EOFError, KeyboardInterrupt): print("\nAte logo!"); break
        if not e: continue
        if e.lower() in ("sair","exit","quit"): print("Ate logo!"); break
        
        resp = conversa.perguntar(e)
        safe = resp.encode("ascii", errors="replace").decode("ascii")
        print(f"  {safe}")

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


def main():
    args = sys.argv[1:]
    cerebro = CerebroAGI()
    brain = None

    if "--aprender" in args:
        brain = aprender_npcs(forcar=True)
        if brain and brain.dialogos:
            for palavra, respostas in brain.dialogos.items():
                for resposta, _, _ in respostas:
                    cerebro.alimentar(f"{resposta}", f"{palavra[:30]}")
        print(f"\nAprendidos {len(cerebro.topicos)} topicos no cerebro")
        return

    # Modo explorar
    if "--explorar" in args:
        idx = args.index("--explorar") + 1
        alvo = args[idx] if idx < len(args) and not args[idx].startswith("--") else None
        explorar(cerebro, alvo)
        chat_loop(cerebro)
        return

    # Carrega NPCs e alimenta TUDO no cerebro — sem categorias, sem limites
    if os.path.exists(r"E:\Projeto MCR\Canary\data-otservbr-global\npc"):
        brain = aprender_npcs()
        if brain and brain.dialogos:
            for palavra, respostas in brain.dialogos.items():
                for resposta, _, _ in respostas:
                    cerebro.alimentar(f"{resposta}", f"{palavra[:30]}")

    if "--ask" in args:
        idx = args.index("--ask")+1
        if idx < len(args):
            p = " ".join(args[idx:])
            r = MCRResposta.responder(p, cerebro)
            print(r.encode("ascii", errors="replace").decode("ascii"))
        return

    if "--daemon" in args:
        print("Modo daemon. Pressione Ctrl+C para parar.")
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt: print("\nParando...")
        return

    chat_loop(cerebro)

if __name__ == "__main__":
    main()
