#!/usr/bin/env python3
"""
MCR Demo — Notebook educacional interativo.

Uso:
    python mcr_demo.py
    python mcr_demo.py --verbose   # mostra todas as cadeias

Demonstra Markov multi-nivel: byte, palavra, tven, decisao,
e o acoplamento entre eles via coupling + esfera.
"""

import sys, os, json, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Importa o MCR real
__file__ = os.path.join(os.path.dirname(__file__), '..', '..', 'MCR.py')
with open(__file__, encoding='utf-8') as f:
    _code = f.read().split('def main():')[0]
exec(compile(_code, 'MCR.py', 'exec'))

VERBOSE = '--verbose' in sys.argv
SEP = '-' * 60


def secao(titulo):
    print(f"\n{SEP}")
    print(f"  {titulo}")
    print(SEP)


def mostrar_cadeia(mk, nome, semente, passos=4):
    """Mostra predicoes e entropia de uma cadeia Markov."""
    print(f"\n  [{nome}] entropia_media={mk.entropia_media():.3f}")
    if semente in mk.freq:
        pred, conf = mk.predizer(semente)
        print(f"  predizer('{semente}') = ('{pred}', {conf:.3f})")
    gerado = mk.gerar(semente, passos)
    print(f"  gerar('{semente}', {passos}) = {' -> '.join(gerado)}")
    if VERBOSE:
        for estado, trans in sorted(mk.transicoes.items())[:5]:
            for prox, cnt in sorted(trans.items(), key=lambda x: -x[1])[:3]:
                print(f"    '{estado}' -> '{prox}' ({cnt}x)")


def mostrar_matriz(coupling):
    """Mostra matriz de acoplamento como heatmap textual."""
    niveis = coupling.niveis
    print(f"\n  Matriz de Coupling ({len(niveis)} niveis):")
    print(f"  {'':>12}", ' '.join(f"{n:<10}" for n in niveis[:6]))
    for o in niveis[:6]:
        linha = f"  {o:>12}"
        for d in niveis[:6]:
            peso = coupling.peso(o, d)
            linha += f" {peso:<10.2f}"
        print(linha)


# ════════════════════════════════════════════════════════════
# 1. CRIACAO DO SISTEMA
# ════════════════════════════════════════════════════════════
secao("1. Criando o sistema multi-nivel")

c = CerebroAGI()
print("  CerebroAGI criado com niveis:")
print(f"    mk_byte    = {c.mk_byte.nome}")
print(f"    mk_palavra = {c.mk_palavra.nome}")
print(f"    mk_tven    = {c.mk_tven.nome}")
print(f"    coupling   = {len(c.coupling.niveis)} niveis registrados")

# ════════════════════════════════════════════════════════════
# 2. ALIMENTACAO MULTI-NIVEL
# ════════════════════════════════════════════════════════════
secao("2. Alimentando texto — 3 niveis simultaneos")

texto = "O MCR e uma equacao universal que processa informacao em multiplos niveis"
c.alimentar(texto, "exemplo_1")
print(f"  Texto: '{texto}'")
print(f"  Bytes: {len(texto.encode())} | Palavras: {len(texto.split())}")

# Mostra o que cada nivel aprendeu
mostrar_cadeia(c.mk_byte, "byte (hex)", "B:4F", 6)
mostrar_cadeia(c.mk_palavra, "palavra", "O", 6)
mostrar_cadeia(c.mk_tven, "tven (primeira letra)", "O", 6)

# ════════════════════════════════════════════════════════════
# 3. COUPLING ENTRE NIVEIS
# ════════════════════════════════════════════════════════════
secao("3. Acoplamento entre niveis (coupling)")

mostrar_matriz(c.coupling)

# ════════════════════════════════════════════════════════════
# 4. MAIS TEXTOS — SISTEMA APRENDE
# ════════════════════════════════════════════════════════════
secao("4. Segundo texto — sistema acumula conhecimento")

texto2 = "Markov descobriu cadeias que processam sequencias de estados"
c.alimentar(texto2, "exemplo_2")
print(f"  Texto: '{texto2}'")
print(f"  Topicos totais: {len(c.topicos)}")

# ════════════════════════════════════════════════════════════
# 5. GERACAO MULTI-NIVEL
# ════════════════════════════════════════════════════════════
secao("5. Geracao — o Markov 'conversa'")

pergunta = "MCR"
resposta = c.gerar(pergunta, passos=5)
print(f"  Pergunta: '{pergunta}'")
print(f"  Resposta: '{resposta}'")

if VERBOSE:
    print("\n  Passo a passo:")
    palavras = pergunta.split()
    for _ in range(5):
        semente = palavras[-1] if palavras else ""
        preds = c.mk_palavra.predizer_n(semente, 3)
        palavras.append(preds[0][0] if preds else "?")
        confs = [f"{p}({c:.2f})" for p, c in preds]
        print(f"    '{semente}' -> {confs} -> '{palavras[-1]}'")

# ════════════════════════════════════════════════════════════
# 6. DECISAO MAROV (ORQUESTRADOR)
# ════════════════════════════════════════════════════════════
secao("6. Decisao Markov — orquestrador interno")

estado = c._estado_atual()
acao, conf = c.mk_orq.predizer(estado)
print(f"  Estado do sistema: {estado}")
print(f"  Acao decidida: '{acao}' (conf={conf:.3f})")
print(f"  Acoes registradas: {list(c._acoes_internas.keys())[:6]}")

# ════════════════════════════════════════════════════════════
# 7. PARSER SEMANTICO (SE HOUVER)
# ════════════════════════════════════════════════════════════
if hasattr(c, 'parser'):
    secao("7. Parsing semantico — extraindo relacoes")
    frases = [
        "Joao come maca",
        "Maria gosta de Pedro",
        "O sol e amarelo",
    ]
    for frase in frases:
        triplas = c.parser.extrair(frase)
        print(f"  '{frase}' -> {triplas}")

# ════════════════════════════════════════════════════════════
# 8. RESUMO
# ════════════════════════════════════════════════════════════
secao("8. Resumo do sistema")

print(f"  Bytes: {c.mk_byte.total} transicoes (ent={c.mk_byte.entropia_media():.2f})")
print(f"  Palavras: {c.mk_palavra.total} transicoes (ent={c.mk_palavra.entropia_media():.2f})")
print(f"  Tven: {c.mk_tven.total} transicoes (ent={c.mk_tven.entropia_media():.2f})")
print(f"  Topicos: {len(c.topicos)}")
print(f"  Coupling: {c.coupling.total_cooc} co-ocorrencias")
print()
print("  Uma equacao. N niveis. Zero GPU. Zero LLM.")
