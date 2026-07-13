#!/usr/bin/env python3
"""signature.py — MCRFingerprint and MCRSignature for data fingerprinting.

Observação e clusterização de dados via assinaturas Markovianas.
Cache global _SIG_CACHE para evitar recálculos.
"""
import math, re
from collections import Counter
from typing import Dict, List, Set

from .engine import MCR


class MCRFingerprint:
    """Fingerprint MCR — configuração de nivel, nao classe separada.
    
    Usa MCR nivel 'assinatura' internamente.
    Mantido como compatibilidade — prefira MCR('assinatura').
    """
    
    @staticmethod
    def gerar(texto: str) -> list:
        dados = texto.encode('utf-8')
        if not dados:
            return [0.0]*8
        buckets = [0.0]*8
        for b in dados:
            if 97 <= b <= 122:
                buckets[0] += 1
            elif 65 <= b <= 90:
                buckets[1] += 1
            elif 48 <= b <= 57:
                buckets[2] += 1
            elif b == 32:
                buckets[3] += 1
            elif b in (33,44,46,58,59,63,40,41,45,95):
                buckets[4] += 1
            elif b < 65:
                buckets[5] += 1
            elif b > 122:
                buckets[6] += 1
            else:
                buckets[7] += 1
        total = sum(buckets) or 1
        return [round(b/total*10, 3) for b in buckets]
    
    @staticmethod
    def extrair_estilo(texto: str) -> dict:
        if not texto: return {}
        bytes_dados = texto.encode('utf-8')
        n = len(bytes_dados)
        if n == 0: return {}
        caps = sum(1 for b in bytes_dados if 65 <= b <= 90)
        nums = sum(1 for b in bytes_dados if 48 <= b <= 57)
        punct = sum(1 for b in bytes_dados if b in [33,44,46,58,59,63,
                   40,41,45,47,8212,8211,8220,8221])
        exclam = sum(1 for b in bytes_dados if b == 33)
        quest = sum(1 for b in bytes_dados if b == 63)
        espacos = sum(1 for b in bytes_dados if b == 32)
        palavras = texto.split()
        n_palavras = len(palavras)
        frases = [s for s in texto.replace('!','.').replace('?','.').split('.') if s.strip()]
        n_frases = len(frases)
        upper_first = sum(1 for p in palavras if p and p[0].isupper())
        palavras_unicas = len(set(p.lower() for p in palavras))
        from collections import Counter
        freq = Counter(bytes_dados)
        h = 0.0
        for c in freq.values():
            p = c / n
            if p > 0: h -= p * math.log2(p)
        return {
            'caps_ratio': round(caps / n, 4),
            'num_ratio': round(nums / n, 4),
            'punct_ratio': round(punct / n, 4),
            'exclam_ratio': round(exclam / n, 4),
            'quest_ratio': round(quest / n, 4),
            'space_ratio': round(espacos / n, 4),
            'upper_first_ratio': round(upper_first / max(n_palavras, 1), 4),
            'avg_word_len': round(n / max(n_palavras, 1), 2),
            'avg_sentence_len': round(n_palavras / max(n_frases, 1), 2),
            'unique_ratio': round(palavras_unicas / max(n_palavras, 1), 4),
            'byte_entropy': round(h, 4),
        }


_SIG_CACHE = {}


class MCRSignature:
    """Assinatura unica de QUALQUER dado.
    
    A assinatura NAO e um conjunto de campos fixos.
    E a SEQUENCIA COMPLETA de transicoes do dado em bytes.
    MCRByte ja captura isso. MCRMetaNivel ja expande.
    Esta classe so CONECTA o que ja existe.
    """
    
    @staticmethod
    def extrair(dados, rapido=False) -> dict:
        if not dados:
            return {'entropia': 0, 'estados': 0, 'transicoes': 0, 'fingerprint': [0]*64}
        if isinstance(dados, str):
            dados = dados.encode('utf-8')
        h = hash(dados)
        if h in _SIG_CACHE:
            return _SIG_CACHE[h]
        mk = MCR("sig_byte")
        mk.aprender_sequencia(list(dados))
        estados = len(mk.transicoes)
        n_trans = sum(len(v) for v in mk.transicoes.values())
        entropia = mk.entropia_media()
        fingerprint = []
        if rapido:
            # Fingerprint 8-dim (rapido)
            buckets = [0.0]*8
            for b in dados:
                if 97 <= b <= 122: buckets[0] += 1
                elif 65 <= b <= 90: buckets[1] += 1
                elif 48 <= b <= 57: buckets[2] += 1
                elif b == 32: buckets[3] += 1
                elif b <= 31 or b == 127: buckets[4] += 1
                elif b > 127: buckets[5] += 1
                else: buckets[6] += 1
            total = sum(buckets) or 1
            fingerprint = [round(b/total*10, 3) for b in buckets]
        else:
            # Fingerprint 64-dim: histograma de bigramas
            fingerprint = [0.0]*64
            for i in range(len(dados)-1):
                bigrama = (dados[i] * 256 + dados[i+1]) % 64
                fingerprint[bigrama] += 1.0
            total = sum(fingerprint) or 1
            fingerprint = [round(b/total*10, 3) for b in fingerprint]
        resultado = {
            'entropia': round(entropia, 3),
            'estados': estados,
            'transicoes': n_trans,
            'fingerprint': fingerprint,
            'tamanho': len(dados),
        }
        _SIG_CACHE[h] = resultado
        return resultado
    
    @staticmethod
    def comparar(a: dict, b: dict) -> float:
        fp_a = a.get('fingerprint', [])
        fp_b = b.get('fingerprint', [])
        if not fp_a or not fp_b:
            return 0.0
        dot = sum(x*y for x, y in zip(fp_a, fp_b))
        na = math.sqrt(sum(x*x for x in fp_a))
        nb = math.sqrt(sum(y*y for y in fp_b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)
    
    @staticmethod
    def extrair_palavras(texto: str, max_palavras: int = 30) -> dict:
        if not texto:
            return {'entropia': 0, 'estados': 0, 'transicoes': 0, 'palavras': []}
        palavras = texto.split()[:max_palavras]
        mk = MCR("sig_palavra")
        mk.aprender_sequencia(palavras)
        return {
            'entropia': round(mk.entropia_media(), 3),
            'estados': len(mk.transicoes),
            'transicoes': sum(len(v) for v in mk.transicoes.values()),
            'palavras': palavras,
        }
    
    @staticmethod
    def comparar_palavras(a: dict, b: dict) -> float:
        pal_a = set(a.get('palavras', []))
        pal_b = set(b.get('palavras', []))
        if not pal_a or not pal_b:
            return 0.0
        inter = pal_a & pal_b
        uniao = pal_a | pal_b
        return len(inter) / len(uniao) if uniao else 0.0
    
    @staticmethod
    def metaniveis(dados, max_niveis=10) -> dict:
        if not dados:
            return {'niveis': 0, 'dados': []}
        if isinstance(dados, str):
            dados = dados.encode('utf-8')
        niveis = []
        atual = list(dados)
        for _ in range(max_niveis):
            if len(atual) < 2:
                break
            mk = MCR(f"meta_{_}")
            mk.aprender_sequencia(atual)
            entropia = mk.entropia_media()
            n_estados = len(mk.transicoes)
            prox = []
            for a, b in zip(atual, atual[1:]):
                pred, _ = mk.predizer(f"{a:02x}")
                if pred:
                    try:
                        prox.append(int(str(pred), 16))
                    except Exception:
                        prox.append(a)
            niveis.append({
                'nivel': _, 'entropia': round(entropia, 3),
                'estados': n_estados, 'tamanho': len(atual),
            })
            atual = prox[:len(atual)]
        return {'niveis': len(niveis), 'dados': niveis}
    
    @staticmethod
    def identificar(dados, banco: list = None) -> dict:
        sig = MCRSignature.extrair(dados)
        if not banco:
            return {'assinatura': sig, 'match': None}
        melhor = None
        melhor_score = 0
        for item in banco:
            if isinstance(item, dict) and 'assinatura' in item:
                score = MCRSignature.comparar(sig, item['assinatura'])
                if score > melhor_score:
                    melhor_score = score
                    melhor = item
        return {
            'assinatura': sig,
            'match': melhor,
            'score': round(melhor_score, 3) if melhor else 0,
        }


# ─── Raw Token Set (Fingerprint bruto, sem parser) ─────

_DELIMITADORES_UNIVERSAIS = re.compile(r'[\s{}();.,:\[\]"\'\`/\\#<>!=+\-*%&|^~@?]+')

def raw_token_set(texto: str) -> Set[str]:
    """Tokeniza texto usando apenas delimitadores universais.
    
    Divide por:
    - whitespace
    - {}();.,:[]"'`/\\#<>!=+-*%&|^~@
    
    Normaliza para lowercase. Retorna conjunto de tokens unicos.
    Nao usa gramatica, AST ou qualquer conhecimento previo da lingua.
    """
    if not texto:
        return set()
    tokens = _DELIMITADORES_UNIVERSAIS.split(texto)
    return {t.strip().lower() for t in tokens if t.strip()}


def raw_token_set_from_file(path: str) -> Set[str]:
    """Le arquivo e extrai raw_token_set."""
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return raw_token_set(f.read())
    except Exception:
        return set()
