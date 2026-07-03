#!/usr/bin/env python3
"""Equacao MCR — prototipo universal.
1 algoritmo, N niveis, 0 wrappers, 0 legado."""
import math
from collections import Counter
from typing import List, Tuple, Optional, Any, Dict

# ============================================================
# EQUACAO MCR (1 classe, ~80 linhas)
# ============================================================

class MCR:
    """MCR — 1 algoritmo, N niveis.
    
    Tudo e transicao entre dois estados consecutivos.
    O que muda e o NIVEL. O algoritmo e o mesmo.
    """
    
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
    
    @staticmethod
    def jaccard_bytes(texto_a: str, texto_b: str) -> float:
        ba = texto_a.encode()
        bb = texto_b.encode()
        ta = {f"{ba[i]:02x}->{ba[i+1]:02x}" for i in range(len(ba)-1)}
        tb = {f"{bb[i]:02x}->{bb[i+1]:02x}" for i in range(len(bb)-1)}
        inter = ta & tb
        uniao = ta | tb
        return len(inter)/len(uniao) if uniao else 0.0


# ============================================================
# NIVEIS (configuracoes, nao classes, ~50 linhas)
# ============================================================

MCR.registrar_nivel("byte", {
    'nome': 'byte',
    'tokenizar': lambda d: [f"B:{b:02x}" for b in (d.encode() if isinstance(d, str) else d)],
})

MCR.registrar_nivel("palavra", {
    'nome': 'palavra',
    'tokenizar': lambda t: t.split() if isinstance(t, str) else [str(t)],
})

MCR.registrar_nivel("token_tipo", {
    'nome': 'token_tipo',
    'tokenizar': lambda t: [p[0].upper() for p in t.split() if p] if isinstance(t, str) else [str(t)[:1]],
})

MCR.registrar_nivel("decisao", {
    'nome': 'decisao',
    'tokenizar': lambda e: [str(e)],
})

MCR.registrar_nivel("intencao", {
    'nome': 'intencao',
    'tokenizar': lambda e: [str(e)],
})

MCR.registrar_nivel("threshold", {
    'nome': 'threshold',
    'tokenizar': lambda v: [f"THR:{int(float(str(v))*100)}"],
})


# ============================================================
# TESTE REAL (5 experiencias, ~70 linhas)
# ============================================================

ok = 0
falha = 0

def testar(nome, cond):
    global ok, falha
    if cond:
        ok += 1
        print(f"  [OK] {nome}")
    else:
        falha += 1
        print(f"  [FALHA] {nome}")

print("=" * 60)
print("  EQUACAO MCR — 1 algoritmo, N niveis")
print("=" * 60)

# Experiencia 1: BYTES
print("\n[1] NIVEL BYTE: aprender e predizer bytes")
mcr_b = MCR("byte")
texto = "Ola MCR!"
tokens = mcr_b.tokenizar(texto)
mcr_b.aprender_sequencia(tokens)
primeiro = tokens[0]
segundo = tokens[1]
prox, conf = mcr_b.predizer(primeiro)
print(f"  Texto: '{texto}' ({len(tokens)} bytes)")
print(f"  Predizer({primeiro}) = ({prox}, {conf:.2f})")
testar(f"Byte: {primeiro} -> {prox} (esperado: {segundo})", prox == segundo)

# Experiencia 2: PALAVRAS + GERACAO
print("\n[2] NIVEL PALAVRA: aprender e gerar texto")
mcr_p = MCR("palavra")
frase = "MCR e uma equacao universal que aprende qualquer coisa"
palavras = mcr_p.tokenizar(frase)
mcr_p.aprender_sequencia(palavras)
gerado = mcr_p.gerar("MCR", 6)
texto_gerado = ' '.join(gerado)
print(f"  Aprendeu: '{frase}'")
print(f"  Gerado: '{texto_gerado}'")
testar(f"Palavra: gerou {len(gerado)} tokens (>= 3)", len(gerado) >= 3)
testar(f"Palavra: comeca com 'MCR'", gerado[0] == 'MCR' if gerado else False)

# Experiencia 3: DECISOES
print("\n[3] NIVEL DECISAO: aprender e decidir acoes")
mcr_d = MCR("decisao")
mcr_d.aprender("explicacao_ok", "buscar_kg")
mcr_d.aprender("buscar_kg_ok", "conectar_topicos")
mcr_d.aprender("conectar_topicos_ok", "gerar_resposta")
mcr_d.aprender("gerar_resposta_ok", "entregar")
decisao = mcr_d.predizer("explicacao_ok")
print(f"  Fluxo: explicacao -> buscar_kg -> conectar -> gerar -> entregar")
print(f"  Predizer('explicacao_ok') = {decisao}")
testar(f"Decisao: explicacao -> buscar_kg", decisao[0] == 'buscar_kg')

# Experiencia 4: GERACAO LONGA
print("\n[4] NIVEL PALAVRA: gerar texto sobre SPA")
mcr_s = MCR("palavra")
texto_spa = "SPA e o sistema de progressao do aventureiro em dominios elementais"
mcr_s.aprender_sequencia(texto_spa.split())
gerado_spa = mcr_s.gerar("SPA", 10)
texto_gerado_spa = ' '.join(gerado_spa)
print(f"  Entrada: '{texto_spa}'")
print(f"  Gerado: '{texto_gerado_spa}'")
testar(f"Geracao SPA: {len(gerado_spa)} tokens (>= 4)", len(gerado_spa) >= 4)
testar(f"Geracao SPA: comeca com 'SPA'", gerado_spa[0] == 'SPA' if gerado_spa else False)

# Experiencia 5: JACCARD
print("\n[5] FUNCAO UNIVERSAL: jaccard_bytes")
sim_igual = MCR.jaccard_bytes("MCR e universal", "MCR e universal")
sim_similar = MCR.jaccard_bytes("MCR e universal", "MCR e legal")
sim_diferente = MCR.jaccard_bytes("MCR e universal", "Python e legal")
sim_total = MCR.jaccard_bytes("abc", "xyz")
print(f"  Identicos:  {sim_igual:.3f}")
print(f"  Similares:  {sim_similar:.3f}")
print(f"  Diferentes: {sim_diferente:.3f}")
print(f"  Total dif:  {sim_total:.3f}")
testar(f"Jaccard: identicos = 1.00", abs(sim_igual - 1.0) < 0.01)
testar(f"Jaccard: identicos > similares", sim_igual > sim_similar)
testar(f"Jaccard: similares > diferentes", sim_similar > sim_diferente)

# Experiencia 6: ENTROPIA
print("\n[6] ENTROPIA: medir incerteza de cada nivel")
ent_byte = mcr_b.entropia(tokens[0])
ent_dec = mcr_d.entropia("explicacao_ok")
print(f"  Entropia byte[{tokens[0]}]:    {ent_byte:.2f}")
print(f"  Entropia decisao[explicacao]: {ent_dec:.2f}")
testar(f"Entropia: valores validos (0-5)", 0 <= ent_byte <= 5)

print("\n" + "=" * 60)
print(f"  RESULTADO: {ok}/{ok+falha} testes OK")
print("=" * 60)
print(f"\n  1 equacao. {len(MCR._NIVEIS)} niveis. 0 wrappers. 0 legado.")
print(f"  A MESMA equacao que aprende bytes TAMBEM decide acoes.")
print(f"  A MESMA equacao que gera texto TAMBEM compara textos.")
print(f"  A MESMA equacao que aprende palavras TAMBEM mede entropia.")
