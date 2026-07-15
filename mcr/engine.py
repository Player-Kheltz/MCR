#!/usr/bin/env python3
"""engine.py — Core MCR class and level definitions.

Núcleo matemático puro: Cadeias de Markov 1ª ordem,
Entropia de Shannon, Jaccard, Fingerprinting.
Zero dependências externas. Zero imports do pacote mcr_kernel.
"""
import os, re, json, math, random, time as _time
from collections import Counter
from typing import List, Dict, Tuple, Optional, Any


class MCR:
    """MCR — 1 algoritmo, N níveis. Mesmo código para bytes, tokens, intenções, decisões.
    
    MCR é o CONCEITO: tudo é transição entre dois estados consecutivos.
    O que muda é o que entra como "token".
    O mesmo código aprende bytes, palavras, intenções, ações, filosofias.
    
    Niveis sao REGISTRADOS (nao classes separadas):
        MCR.registrar_nivel("decisao", {
            'tokenizar': lambda e: [str(e)],
            'comparar': lambda a, b: 1.0 if a == b else 0.0,
        })
    
    Uso:
        mcr = MCR("byte")
        mcr.aprender_sequencia([...])
        mcr.predizer("SPA")  # → ("é", 0.5)
    """
    
    # Registro de niveis (configuracoes, nao classes)
    _NIVEIS: Dict[str, dict] = {}
    
    @classmethod
    def registrar_nivel(cls, nome: str, config: dict):
        cls._NIVEIS[nome] = {
            'nome': config.get('nome', nome),
            'tokenizar': config.get('tokenizar', lambda d: [str(d)]),
            'comparar': config.get('comparar', lambda a, b: 1.0 if a == b else 0.0),
            'processar': config.get('processar', None),
        }
    
    def __init__(self, nome: str = ""):
        self.nome = nome
        self.transicoes = {}
        self.freq = Counter()
        self.total = 0
        self._entropia_cache: Dict[str, float] = {}
    
    def aprender(self, a: Any, b: Any):
        sa, sb = str(a), str(b)
        self.freq[sa] += 1; self.total += 1
        if sa not in self.transicoes: self.transicoes[sa] = {}
        self.transicoes[sa][sb] = self.transicoes[sa].get(sb, 0) + 1
        self._entropia_cache.pop(sa, None)
    
    def aprender_sequencia(self, seq: List[Any]):
        for i in range(len(seq)-1): self.aprender(seq[i], seq[i+1])
    
    def aprender_batch(self, sequencias: List[List[Any]]):
        """Aprende multiplas sequencias em batch.
        
        Usa dict temporario para contar, depois mescla.
        Muito mais rapido que N chamadas de aprender_sequencia.
        """
        temp: Dict[str, Counter] = {}
        for seq in sequencias:
            for i in range(len(seq) - 1):
                a, b = str(seq[i]), str(seq[i+1])
                if a not in temp:
                    temp[a] = Counter()
                temp[a][b] += 1
        for a, counter in temp.items():
            if a not in self.transicoes:
                self.transicoes[a] = {}
                self.freq[a] = 0
            for b, count in counter.items():
                self.transicoes[a][b] = self.transicoes[a].get(b, 0) + count
                self.freq[a] += count
                self.total += count
            self._entropia_cache.pop(a, None)
    
    def predizer(self, a: Any) -> Tuple[Optional[Any], float]:
        sa = str(a)
        if sa not in self.transicoes or not self.transicoes[sa]: return None, 0.0
        prox = self.transicoes[sa]; melhor = max(prox, key=prox.get)
        total = sum(prox.values())
        return melhor, prox[melhor]/total
    
    def predizer_n(self, a: Any, n: int = 3) -> List[Tuple[Any, float]]:
        sa = str(a)
        if sa not in self.transicoes: return []
        prox = self.transicoes[sa]
        sorted_prox = sorted(prox.items(), key=lambda x: -x[1])
        total = sum(prox.values())
        return [(p, c/total) for p, c in sorted_prox[:n]]
    
    def entropia(self, a: Any) -> float:
        sa = str(a)
        if sa in self._entropia_cache: return self._entropia_cache[sa]
        if sa not in self.transicoes: return 1.0
        prox = self.transicoes[sa]; t = sum(prox.values())
        if t == 0: return 1.0
        h = 0.0
        for c in prox.values():
            p = c/t
            if p > 0: h -= p * math.log2(p)
        self._entropia_cache[sa] = h
        return h
    
    def entropia_media(self) -> float:
        if not self.transicoes: return 0.0
        hs = [self.entropia(t) for t in self.transicoes if self.transicoes[t]]
        return sum(hs)/len(hs) if hs else 0.0
    
    def entropia_sequencia(self, seq: List[Any]) -> float:
        if not seq: return 1.0
        hs = [self.entropia(s) for s in seq]
        return sum(hs)/len(hs)
    
    def jaccard(self, outra: 'MCR') -> float:
        estados_a = set(self.freq.keys())
        estados_b = set(outra.freq.keys())
        if not estados_a or not estados_b: return 0.0
        inter = estados_a & estados_b
        uniao = estados_a | estados_b
        return len(inter)/len(uniao)
    
    def jaccard_transicoes(self, outra: 'MCR') -> float:
        trans_a = set(f"{a}→{b}" for a in self.transicoes for b in self.transicoes[a])
        trans_b = set(f"{a}→{b}" for a in outra.transicoes for b in outra.transicoes[a])
        if not trans_a or not trans_b: return 0.0
        inter = trans_a & trans_b
        uniao = trans_a | trans_b
        return len(inter)/len(uniao)
    
    def gerar(self, semente: Any, passos: int = 10) -> List[Any]:
        res = [semente]; atual = semente
        for _ in range(passos):
            prox, conf = self.predizer(atual)
            if prox is None or conf < 0.01: break
            res.append(prox); atual = prox
        return res
    
    def jaccard_bytes(self, texto_a: str, texto_b: str) -> float:
        ba = texto_a.encode('utf-8')
        bb = texto_b.encode('utf-8')
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
        if token.startswith('<|') or token.startswith('<|'):
            return 'sistema'
        if token.isupper() and len(token) >= 2: return 'sistema'
        if token[0].isupper() and len(token) > 1: return 'lore'
        if token.isdigit() or (token[0] == '-' and token[1:].isdigit()): return 'numero'
        if all(c in '.,;:!?()[]{}<>+-*/=@#$%^&_~`\'\"|\\ \t\n\r\u2581' for c in token):
            return 'pontuacao'
        if token[0].islower() or token[0].isalpha(): return 'linguagem'
        return 'outro'
    
    def similaridade_transicoes(self, texto_a: str, texto_b: str,
                                 max_bytes: int = 500) -> float:
        ba = texto_a.encode('utf-8')
        bb = texto_b.encode('utf-8')
        fa = {}
        fb = {}
        for i in range(len(ba) - 1):
            t = f"{ba[i]:02x}->{ba[i+1]:02x}"
            fa[t] = fa.get(t, 0) + 1
        for i in range(len(bb) - 1):
            t = f"{bb[i]:02x}->{bb[i+1]:02x}"
            fb[t] = fb.get(t, 0) + 1
        todas = set(fa.keys()) | set(fb.keys())
        dot = sum(fa.get(t, 0) * fb.get(t, 0) for t in todas)
        na = math.sqrt(sum(v * v for v in fa.values()))
        nb = math.sqrt(sum(v * v for v in fb.values()))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)
    
    def jaccard_bytes_ponderado(self, texto_a: str, texto_b: str) -> float:
        da = texto_a.encode('utf-8')
        db = texto_b.encode('utf-8')
        pesos = {}
        for i in range(max(len(da), len(db)) - 1):
            if i < len(da) - 1:
                t = f"{da[i]:02x}->{da[i+1]:02x}"
                pesos[t] = pesos.get(t, 0) + (2.0 if i < 10 else 1.0)
            if i < len(db) - 1:
                t = f"{db[i]:02x}->{db[i+1]:02x}"
                pesos[t] = pesos.get(t, 0) + (2.0 if i < 10 else 1.0)
        trans_a = {f"{da[i]:02x}->{da[i+1]:02x}" for i in range(len(da)-1)}
        trans_b = {f"{db[i]:02x}->{db[i+1]:02x}" for i in range(len(db)-1)}
        inter = trans_a & trans_b
        uniao = trans_a | trans_b
        if not uniao: return 0.0
        peso_inter = sum(pesos.get(t, 1) for t in inter)
        peso_uniao = sum(pesos.get(t, 1) for t in uniao)
        return peso_inter / peso_uniao
    
    def _extrair_assinatura(self, dados: bytes) -> dict:
        mk = MCR("assinatura")
        mk.aprender_sequencia(list(dados))
        top5 = []
        for estado, prox in sorted(mk.transicoes.items(),
                                     key=lambda x: -sum(x[1].values())):
            melhor = max(prox, key=prox.get) if prox else ''
            top5.append(f"{estado}->{melhor}")
        return {
            'entropia': round(mk.entropia_media(), 3),
            'estados': len(mk.transicoes),
            'transicoes': sum(len(v) for v in mk.transicoes.values()),
            'top5': top5,
            'tamanho': len(dados),
        }
    
    def _comparar_assinaturas(self, a: dict, b: dict) -> float:
        score = 0.0
        diff_ent = abs(a['entropia'] - b['entropia'])
        score += 3.0 * (1.0 - min(1.0, diff_ent))
        diff_est = abs(a['estados'] - b['estados']) / max(a['estados'], b['estados'], 1)
        score += 3.0 * (1.0 - min(1.0, diff_est))
        if a['top5'] and b['top5']:
            ta, tb = set(a['top5']), set(b['top5'])
            inter = ta & tb
            uniao = ta | tb
            score += 4.0 * (len(inter) / len(uniao) if uniao else 0)
        return score / 10.0
    
    def processar_bytes(self, entrada: bytes, max_iter: int = 3) -> dict:
        import time
        t0 = time.time()
        assinatura_in = self._extrair_assinatura(entrada)
        try:
            texto = entrada.decode('utf-8', errors='replace')
        except Exception:
            texto = str(entrada)
        palavras = texto.split()
        semente = palavras[0] if palavras else 'byte'
        from .memory import MCRConector, MCRCadeia
        conector = MCRConector()
        conector.alimentar(texto, "entrada_bytes")
        cadeia = MCRCadeia(conector)
        res = cadeia.gerar(semente, n_tokens=30)
        saida_texto = res.get('texto', semente)
        saida_bytes = saida_texto.encode('utf-8')
        assinatura_out = self._extrair_assinatura(saida_bytes)
        compatibilidade = self._comparar_assinaturas(assinatura_in, assinatura_out)
        iteracao = 0
        while compatibilidade < 0.3 and iteracao < max_iter - 1:
            iteracao += 1
            if iteracao < len(palavras):
                semente = palavras[iteracao]
            cadeia = MCRCadeia(conector)
            res = cadeia.gerar(semente, n_tokens=30)
            saida_texto = res.get('texto', semente)
            saida_bytes = saida_texto.encode('utf-8')
            assinatura_out = self._extrair_assinatura(saida_bytes)
            compatibilidade = self._comparar_assinaturas(assinatura_in, assinatura_out)
        nota = round(compatibilidade * 10, 1)
        self.aprender(f"BYTES:{hash(entrada)%10000}", f"COMPAT:{compatibilidade:.2f}")
        return {
            'entrada_tamanho': len(entrada),
            'saida_tamanho': len(saida_bytes),
            'assinatura_entrada': assinatura_in,
            'assinatura_saida': assinatura_out,
            'compatibilidade': round(compatibilidade, 3),
            'nota': nota,
            'iteracoes': iteracao,
            'saida': saida_texto if len(saida_texto) > 300 else saida_texto,
            'tempo': round(time.time() - t0, 3),
        }
    
    def stats(self) -> Dict:
        return {
            'nome': self.nome, 'estados': len(self.transicoes),
            'transicoes': sum(len(v) for v in self.transicoes.values()),
            'entropia': round(self.entropia_media(), 3),
        }

    def save(self, caminho: str = None):
        """Persiste transições e frequências em JSON."""
        if caminho is None:
            caminho = os.path.join(os.path.dirname(__file__),
                                   f'markov_{self.nome}.json')
        dados = {
            'nome': self.nome,
            'total': self.total,
            'transicoes': self.transicoes,
            'freq': dict(self.freq),
        }
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False)

    def load(self, caminho: str = None) -> bool:
        """Carrega transições de JSON. Retorna True se sucesso."""
        if caminho is None:
            caminho = os.path.join(os.path.dirname(__file__),
                                   f'markov_{self.nome}.json')
        if not os.path.exists(caminho):
            return False
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            self.nome = dados.get('nome', self.nome)
            self.total = dados.get('total', 0)
            self.transicoes = dados.get('transicoes', {})
            self.freq = Counter(dados.get('freq', {}))
            self._entropia_cache = {}
            return True
        except Exception:
            return False


MarkovUniversal = MCR


MCR.registrar_nivel("byte", {
    'nome': 'byte',
    'tokenizar': lambda d: [f"B:{b:02x}" for b in (d.encode() if isinstance(d, str) else d)],
})

MCR.registrar_nivel("palavra", {
    'nome': 'palavra',
    'tokenizar': lambda t: t.split() if isinstance(t, str) else [str(t)],
})

MCR.registrar_nivel("token", {
    'nome': 'token',
    'tokenizar': lambda t: [p[0].upper() for p in t.split() if p] if isinstance(t, str) else [str(t)[:1]],
})

MCR.registrar_nivel("decisao", {
    'nome': 'decisao',
    'tokenizar': lambda e: [str(e)],
})

MCR.registrar_nivel("threshold", {
    'nome': 'threshold',
    'tokenizar': lambda v: [f"THR:{int(float(str(v))*100)}"],
})

MCR.registrar_nivel("peso", {
    'nome': 'peso',
    'tokenizar': lambda c: [f"{k}:{int(v*10)}" for k, v in (c.items() if isinstance(c, dict) else [('v', c)])],
})

MCR.registrar_nivel("assinatura", {
    'nome': 'assinatura',
    'tokenizar': lambda d: MCR("byte").gerar(list(MCR("byte").aprender_sequencia(
        list(d.encode() if isinstance(d, str) else bytes(d))
    ))[0], 50) if d else [],
})

MCR.registrar_nivel("filosofia", {
    'nome': 'filosofia',
    'tokenizar': lambda p: [str(p)],
})

MCR.registrar_nivel("qualidade", {
    'nome': 'qualidade',
    'tokenizar': lambda sol: MCR("assinatura").gerar(sol, 10) if sol else [],
})

MCR.Nivel = MarkovUniversal


# ============================================================
# ESTADOS COMPOSTOS — Contexto sintático sem aumentar ordem
# ============================================================
# Concatena informações contextuais ao rótulo do estado,
# permitindo que a cadeia de Markov 1ª ordem carregue
# memória de curto prazo sem violar a propriedade Markoviana.
# Ex: compose_state("return", {"em_bloco": "metodo"})
#   → "return|em_bloco:metodo"
# ============================================================

def compose_state(base: str, context: dict) -> str:
    """Concatena contexto a um estado base de forma determinística.
    
    Args:
        base: estado base (ex: "return", "var", "class")
        context: dicionário de contexto (ex: {"em_bloco": "metodo"})
    
    Returns:
        string composta: "base|chave1:valor1|chave2:valor2"
        Se context vazio, retorna base inalterada.
    """
    if not context:
        return base
    
    # Ordena alfabeticamente para consistência
    pares = sorted(f"{k}:{v}" for k, v in context.items())
    return base + "|" + "|".join(pares)


def compor_contexto(tokens_gerados: list, contexto_atual: dict = None) -> dict:
    """Atualiza contexto sintático baseado em tokens gerados.
    
    Regras genéricas baseadas em delimitadores e keywords
    comuns a múltiplas linguagens (C#, Lua, Python, Java).
    Nenhuma regra específica de linguagem.
    
    Args:
        tokens_gerados: lista de tokens gerados até agora
        contexto_atual: contexto atual (opcional)
    
    Returns:
        contexto atualizado
    """
    ctx = dict(contexto_atual or {})
    if not tokens_gerados:
        return ctx
    
    ultimo = str(tokens_gerados[-1]) if tokens_gerados else ''
    
    # Contagem de blocos abertos/fechados
    if ultimo == '{':
        ctx['profundidade_bloco'] = str(int(ctx.get('profundidade_bloco', '0')) + 1)
        ctx['em_bloco'] = 'sim'
    elif ultimo == '}':
        ctx['profundidade_bloco'] = str(max(0, int(ctx.get('profundidade_bloco', '1')) - 1))
        if ctx.get('profundidade_bloco') == '0':
            ctx.pop('em_bloco', None)
    
    # Detecta keywords estruturais
    if ultimo in ('class', 'struct', 'interface', 'record'):
        ctx['declarando_tipo'] = 'sim'
    elif ultimo in ('def', 'function', 'void', 'int', 'string', 'bool',
                    'var', 'let', 'const', 'public', 'private', 'protected',
                    'static', 'override', 'virtual', 'abstract', 'sealed'):
        ctx['em_declaracao'] = 'sim'
    elif ultimo in ('return', 'yield', 'break', 'continue', 'throw'):
        ctx['em_fluxo'] = 'sim'
    elif ultimo == ';':
        ctx['em_declaracao'] = 'nao'
        ctx['em_fluxo'] = 'nao'
    
    # Delimitadores de string/comentário
    if ultimo.startswith('"') or ultimo.startswith("'"):
        ctx['em_string'] = 'sim' if ctx.get('em_string') != 'sim' else 'nao'
    if ultimo.startswith('//') or ultimo.startswith('#'):
        ctx['em_comentario'] = 'sim'
    
    return ctx


class MCRBridge:
    def __init__(self):
        self._descobriu = True
        self.modulos = {}
        self.comandos = {}
    def descobrir(self):
        return {'modulos': len(self.modulos), 'comandos': len(self.comandos)}
