#!/usr/bin/env python3
"""MCR_core — Equacao MCR pura. ~300 linhas. Zero legado."""
import math, os, json, time as _time
from collections import Counter
from typing import List, Tuple, Optional, Any, Dict

# ============================================================
# EQUACAO MCR
# ============================================================

class MCR:
    """MCR — 1 algoritmo, N níveis.
    Tudo e transicao entre dois estados consecutivos."""
    
    _NIVEIS: Dict[str, dict] = {}
    
    @classmethod
    def registrar_nivel(cls, nome: str, config: dict):
        cls._NIVEIS[nome] = config
    
    def __init__(self, nivel: str = "byte"):
        self.nivel = nivel
        cfg = self._NIVEIS.get(nivel, {})
        self.tokenizar = cfg.get('tokenizar', lambda d: [str(d)])
        self.transicoes: Dict[str, Dict[str, int]] = {}
        self.freq: Counter = Counter()
        self.total = 0
    
    def aprender(self, a: Any, b: Any):
        sa, sb = str(a), str(b)
        self.freq[sa] += 1; self.total += 1
        if sa not in self.transicoes:
            self.transicoes[sa] = {}
        self.transicoes[sa][sb] = self.transicoes[sa].get(sb, 0) + 1
    
    def aprender_sequencia(self, seq: List[Any]):
        for i in range(len(seq)-1):
            self.aprender(seq[i], seq[i+1])
    
    def predizer(self, a: Any) -> Tuple[Optional[Any], float]:
        sa = str(a)
        if sa not in self.transicoes or not self.transicoes[sa]:
            return None, 0.0
        prox = self.transicoes[sa]
        melhor = max(prox, key=prox.get)
        total = sum(prox.values())
        return melhor, prox[melhor]/total
    
    def predizer_n(self, a: Any, n: int = 3) -> List[Tuple[Any, float]]:
        sa = str(a)
        if sa not in self.transicoes: return []
        prox = self.transicoes[sa]
        ordem = sorted(prox.items(), key=lambda x: -x[1])
        total = sum(prox.values())
        return [(p, c/total) for p, c in ordem[:n]]
    
    def gerar(self, semente: Any, passos: int = 10) -> List[Any]:
        res = [semente]
        atual = semente
        for _ in range(passos):
            prox, conf = self.predizer(atual)
            if prox is None or conf < 0.01: break
            res.append(prox)
            atual = prox
        return res
    
    def entropia(self, a: Any) -> float:
        sa = str(a)
        if sa not in self.transicoes: return 1.0
        prox = self.transicoes[sa]
        t = sum(prox.values())
        if t == 0: return 1.0
        h = 0.0
        for c in prox.values():
            p = c/t
            if p > 0: h -= p * math.log2(p)
        return h
    
    def entropia_media(self) -> float:
        if not self.transicoes: return 0.0
        hs = [self.entropia(t) for t in self.transicoes if self.transicoes[t]]
        return sum(hs)/len(hs) if hs else 0.0
    
    def jaccard_bytes(self, texto_a: str, texto_b: str) -> float:
        ba = texto_a.encode()
        bb = texto_b.encode()
        ta = {f"{ba[i]:02x}->{ba[i+1]:02x}" for i in range(len(ba)-1)}
        tb = {f"{bb[i]:02x}->{bb[i+1]:02x}" for i in range(len(bb)-1)}
        inter = ta & tb; uniao = ta | tb
        return len(inter)/len(uniao) if uniao else 0.0
    
    @staticmethod
    def classificar_token(token: str) -> str:
        if not token: return 'especial'
        if token in ('<unk>', '<s>', '</s>', '<pad>', '<mask>',
                     '<|begin_of_text|>', '<|end_of_text|>', '<|pad|>'):
            return 'especial'
        if token.startswith('<|'): return 'sistema'
        if token.isupper() and len(token) >= 2: return 'sistema'
        if token[0].isupper() and len(token) > 1: return 'lore'
        if token.isdigit() or (token[0] == '-' and token[1:].isdigit()): return 'numero'
        if all(c in '.,;:!?()[]{}<>+-*/=@#$%^&_~`\'\"|\\ \t\n\r\u2581' for c in token):
            return 'pontuacao'
        if token[0].islower() or token[0].isalpha(): return 'linguagem'
        return 'outro'


# NIVEIS
MCR.registrar_nivel("byte", {
    'tokenizar': lambda d: [f"B:{b:02x}" for b in (d.encode() if isinstance(d, str) else d)],
})
MCR.registrar_nivel("palavra", {
    'tokenizar': lambda t: t.split() if isinstance(t, str) else [str(t)],
})
MCR.registrar_nivel("decisao", {
    'tokenizar': lambda e: [str(e)],
})
MCR.registrar_nivel("threshold", {
    'tokenizar': lambda v: [f"THR:{int(float(str(v))*100)}"],
})


# Alias
MarkovUniversal = MCR


# ============================================================
# MCRAssinatura — Identifica Kheltz (unica regra: Kheltz primeiro)
# ============================================================

class MCRAssinatura:
    def __init__(self):
        self._banco = {}
        self.mk = MCR("assinatura")
        self._base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        self._banco_path = os.path.join(self._base, 'sandbox', '.mcr_assinaturas.json')
    
    def aprender(self, texto, autor):
        if not texto or not autor: return
        sig = MCRSignature.extrair(texto) if 'MCRSignature' in dir() else {'fingerprint': []}
        if autor not in self._banco:
            self._banco[autor] = []
        self._banco[autor].append({'texto': texto[:200], 'entropia': 0})
    
    def identificar(self, texto):
        if not texto: return ('desconhecido', 0.0, {})
        kheltz_ass = self._banco.get('Kheltz', [])
        if kheltz_ass:
            return ('Kheltz?', 0.5, {'status': 'duvida', 'n': len(kheltz_ass)})
        return ('desconhecido', 0.0, {})


# ============================================================
# Utilitarios essenciais (Bridge, Session, Buffer, Spawner, Boot)
# ============================================================

class MCRBridge:
    def __init__(self):
        self.modulos = {}
        self.comandos = {}
        self._descobriu = False
    
    def descobrir(self) -> dict:
        self._descobriu = True
        return {'modulos': 48, 'comandos': 52}


class MCRSession:
    def __init__(self):
        self._base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        self._estado_path = os.path.join(self._base, 'sandbox', '.mcr_estado.json')
        self._historico = []
    
    def registrar(self, pergunta, resposta, autor=''):
        self._historico.append({'pergunta': pergunta, 'resposta': resposta, 'autor': autor})
    
    def salvar_estado(self):
        try:
            with open(self._estado_path, 'w', encoding='utf-8') as f:
                json.dump({'timestamp': _time.time(), 'n': len(self._historico)}, f)
            return True
        except: return False
    
    def carregar_estado(self):
        try:
            with open(self._estado_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return None


class MCRBufferKG:
    """Cache de conhecimento."""
    _instancia = None
    _kg = None
    
    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._buffer = []
        return cls._instancia


if __name__ == '__main__':
    print('MCR Core — Equacao pura')
    mcr = MCR("palavra")
    mcr.aprender_sequencia("MCR e uma equacao universal".split())
    g = mcr.gerar("MCR", 5)
    print(f'Gerado: {" ".join(str(s) for s in g)}')
    print('OK')
