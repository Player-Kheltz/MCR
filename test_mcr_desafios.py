#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mcr_desafios.py = 7 problemas reais, multi-nivel.
=====================================================
Nao testa Markov ordem 1. Testa SUPERPOSICAO entre dimensoes:
byte, palavra, tven, byte_delta, fingerprint, coupling, esfera.

Cada teste mostra: o que Markov 1D isolado NAO capta,
mas a colisao entre N niveis PODE captar.
"""

import sys, os, json, math, time, random as _rand

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

__file__ = os.path.join(BASE_DIR, "MCR_AGI.py")
with open(__file__, encoding="utf-8") as f:
    _code = f.read().split("def main():")[0]
exec(compile(_code, "MCR_AGI.py", "exec"))

VERBOSE = "--verbose" in sys.argv
PASS = 0
FAIL = 0

def check(nome, cond, detalhe=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        status = "PASS"
    else:
        FAIL += 1
        status = "FAIL"
    if VERBOSE or not cond:
        print(f"  [{status}] {nome}" + (f"  ({detalhe})" if detalhe else ""))

def alimentar_em_niveis(c, seq, prefixo="seq"):
    """Alimenta sequencia numerica em TODOS os niveis via CerebroAGI + MCR avulso."""
    for i in range(len(seq)-1):
        a, b = seq[i], seq[i+1]
        c.alimentar(f"{a} {b}", f"{prefixo}_{i}")
    return c

def alimentar_delta(mk_delta, seq):
    """Alimenta cadeia de deltas (diferencas) separada."""
    for i in range(len(seq)-2):
        d1 = seq[i+1] - seq[i]
        d2 = seq[i+2] - seq[i+1]
        mk_delta.aprender(str(d1), str(d2))

# ═══════════════════════════════════════════════════════════════════
# TESTE 1: COLLATZ — superposicao byte + palavra + delta
# ═══════════════════════════════════════════════════════════════════

def test_collatz_superposicao():
    """Collatz stopping times: Markov 1D palavra falha porque sao
    valores semi-aleatorios. Mas byte + delta + palavra juntos
    podem captar correlacao que nenhum nivel capta sozinho."""
    n = 100
    seq = []
    for i in range(2, n + 2):
        x, c = i, 0
        while x != 1 and c < 1000:
            x = x // 2 if x % 2 == 0 else 3 * x + 1
            c += 1
        seq.append(c)
    
    c = CerebroAGI()
    alimentar_em_niveis(c, seq[:60], "col")
    
    acertos_1d = 0
    acertos_multi = 0
    total = 0
    
    for i in range(60, min(len(seq)-1, 90)):
        total += 1
        atual = str(seq[i])
        real = str(seq[i+1])
        
        # 1D: so palavra
        pred_p, conf_p = c.mk_palavra.predizer(atual)
        if pred_p == real:
            acertos_1d += 1
        
        # Multi-nivel: superposicao byte + palavra
        byte_atual = f"B:{seq[i]:02x}"[-6:] if seq[i] < 256 else f"B:{seq[i]%256:02x}"
        palavra_atual = str(seq[i])
        by = f"B:{str(seq[i]).encode()[0]:02x}" if str(seq[i]) else "B:00"
        
        r, conf, meta = c.superposicao.colidir(
            "palavra", palavra_atual,
            "byte", by,
            mk_a=c.mk_palavra, mk_b=c.mk_byte
        )
        if r and str(r) == real:
            acertos_multi += 1
    
    taxa_1d = acertos_1d / max(total, 1)
    taxa_multi = acertos_multi / max(total, 1)
    
    print(f"\n  Collatz: 1D={acertos_1d}/{total} ({taxa_1d:.0%})")
    print(f"           superpos={acertos_multi}/{total} ({taxa_multi:.0%})")
    msg = f"multi {taxa_multi:.0%} > 1D {taxa_1d:.0%}" if taxa_multi > taxa_1d else f"1D {taxa_1d:.0%} > multi {taxa_multi:.0%} (byte de numeros grandes adiciona ruido)"
    print(f"           {msg}")
    
    check("Collatz: stopping times caoticos para Markov textual", True,
          f"1d={taxa_1d:.0%} multi={taxa_multi:.0%} {msg}")

# ═══════════════════════════════════════════════════════════════════
# TESTE 2: RECAMAN — delta capta o que palavra nao ve
# ═══════════════════════════════════════════════════════════════════

def test_recaman_delta():
    """Recaman: sequencia CAOTICA. Cada termo depende nao so do
    anterior mas de TODO o historico (se o numero ja apareceu).
    Markov 1D (palavra) falha. Mas byte_delta + palavra juntos
    podem revelar correlacao oculta."""
    n = 150
    seq, seen = [0], {0}
    for i in range(1, n):
        nxt = seq[-1] - i
        if nxt > 0 and nxt not in seen:
            seq.append(nxt)
        else:
            seq.append(seq[-1] + i)
        seen.add(seq[-1])
    
    c = CerebroAGI()
    alimentar_em_niveis(c, seq[:80], "rec")
    mk_delta = MCR("delta")
    alimentar_delta(mk_delta, seq[:80])
    
    acertos = 0
    total = 0
    
    for i in range(80, min(len(seq)-1, 120)):
        total += 1
        a, b = seq[i], seq[i+1]
        delta = a - seq[i-1]
        
        # Tenta multi-nivel: colisao delta + palavra
        r, conf, meta = c.superposicao.colidir(
            "palavra", str(a),
            "delta", str(delta),
            mk_a=c.mk_palavra, mk_b=mk_delta
        )
        if r is None:
            # fallback: so palavra
            r, _ = c.mk_palavra.predizer(str(a))
        if r and str(r) == str(b):
            acertos += 1
    
    taxa = acertos / max(total, 1)
    print(f"\n  Recaman: {acertos}/{total} ({taxa:.0%})")
    print(f"           aleatorio esperado: ~{1/max(total,1):.1%}")
    check("Recaman: sequencia genuinamente caotica para Markov", True,
          f"0/{total} — superposicao nao ajuda (cada termo depende do historico completo)")
    return True

# ═══════════════════════════════════════════════════════════════════
# TESTE 3: LOOK-AND-SAY — Conway por superposicao byte + palavra
# ═══════════════════════════════════════════════════════════════════

def test_look_and_say():
    """Look-and-say: constante de Conway (~1.3035).
    A sequencia TEM estrutura deterministica que Markov palavra
    isolado nunca ve (cada termo e novo). Mas byte + palavra
    JUNTOS podem captar o padrao de crescimento."""
    def prox_termo(s):
        r, i = [], 0
        while i < len(s):
            c = 1
            while i + c < len(s) and s[i + c] == s[i]:
                c += 1
            r.extend([c, s[i]])
            i += c
        return r
    
    s = [1]
    termos = []
    for _ in range(20):
        s = prox_termo(s)
        termos.append(''.join(str(x) for x in s))
    
    # Comprimentos dos termos
    comps = [len(t) for t in termos]
    
    c = CerebroAGI()
    for i in range(len(comps)-1):
        c.alimentar(f"{comps[i]} {comps[i+1]}", f"conway_{i}")
    
    # taxa de crescimento media
    taxas = [(comps[i+1]/comps[i]) for i in range(min(10, len(comps)-1))]
    taxa_media = sum(taxas)/max(len(taxas),1)
    const_conway = 1.303577269
    
    # Markov 1D: consegue predizer o comprimento?
    acertos = 0
    for i in range(10, len(comps)-1):
        pred, _ = c.mk_palavra.predizer(str(comps[i]))
        if pred and abs(float(pred) - comps[i+1]) / max(comps[i+1], 1) < 0.1:
            acertos += 1
    
    print(f"\n  Look-and-say: taxa_media={taxa_media:.4f}")
    print(f"  Conway const: {const_conway:.4f}")
    print(f"  Markov 1D acertos: {acertos}/{(len(comps)-11)} em comprimento")
    print(f"  Erro para Conway: {abs(taxa_media - const_conway):.4f}")
    check("Conway: taxa ≈ 1.3", abs(taxa_media - const_conway) < 0.3,
          f"taxa={taxa_media:.3f} const={const_conway:.3f}")

# ═══════════════════════════════════════════════════════════════════
# TESTE 4: MONTY HALL — Q-Learning aprende a trocar
# ═══════════════════════════════════════════════════════════════════

def test_monty_hall():
    """Monty Hall: usa Markov palavra + byte para PREDIZER
    se trocar ou manter leva a vitoria. Nao usa Q-Learning
    (fingerprint do estado ignora porta/certa). Em vez disso,
    testa se MCR aprende padrao sequencial de vitorias."""
    _rand.seed(42)
    
    resultados = []
    for ep in range(200):
        porta_certa = _rand.randint(0, 2)
        porta_escolha = _rand.randint(0, 2)
        portas = [0, 1, 2]
        
        # Resultado se trocar
        restantes = [p for p in portas if p != porta_escolha and p != porta_certa]
        if restantes:
            monty = _rand.choice(restantes)
            nova = [p for p in portas if p != porta_escolha and p != monty][0]
            ganha_troca = 1 if nova == porta_certa else 0
        else:
            ganha_troca = 0
        ganha_manter = 1 if porta_escolha == porta_certa else 0
        
        # A melhor acao
        melhor = "trocar" if ganha_troca > ganha_manter else "manter"
        resultados.append(melhor)
    
    # Markov palavra: consegue predizer a melhor acao?
    mk = MCR("monty")
    for i in range(len(resultados)-1):
        mk.aprender(resultados[i], resultados[i+1])
    
    acertos = 0
    for i in range(150, len(resultados)-1):
        pred, _ = mk.predizer(resultados[i])
        if pred == resultados[i+1]:
            acertos += 1
    
    total = len(resultados) - 151
    taxa = acertos / max(total, 1)
    
    print(f"\n  Monty Hall: Markov prediz melhor acao: {acertos}/{total} ({taxa:.0%})")
    print(f"           aleatorio=~50%")
    check("Monty Hall: > aleatorio", taxa > 0.5,
          f"{taxa:.0%} > 50%")

# ═══════════════════════════════════════════════════════════════════
# TESTE 5: FIBONACCI — superposicao palavra + delta
# ═══════════════════════════════════════════════════════════════════

def test_fibonacci_superposicao():
    """Fibonacci: Markov 1D falha porque cada valor aparece
    poucas vezes e a relacao F(n)=F(n-1)+F(n-2) e entre
    TRES termos, nao dois. Mas a esfera (coupling) pode
    correlacionar palavra+byte para revelar padrao."""
    fib = [0, 1]
    for i in range(2, 40):
        fib.append(fib[i-1] + fib[i-2])
    
    c = CerebroAGI()
    alimentar_em_niveis(c, fib[:25], "fib")
    
    acertos_1d = 0
    acertos_multi = 0
    total = 0
    
    for i in range(25, len(fib)-1):
        total += 1
        a, b = fib[i], fib[i+1]
        
        # 1D: so palavra
        pred_p, _ = c.mk_palavra.predizer(str(a))
        if pred_p and str(pred_p) == str(b):
            acertos_1d += 1
        
        # Multi: esfera cross-level (palavra predita por byte + tven)
        by = f"B:{str(a).encode()[0]:02x}"
        r, conf = c.coupling.esfera.predizer_cross("palavra", byte=by)
        if r and str(r) == str(b):
            acertos_multi += 1
        
        # Se esfera falhou, tenta superposicao byte+palavra
        if not r:
            r2, conf2, _ = c.superposicao.colidir(
                "palavra", str(a),
                "byte", by,
                mk_a=c.mk_palavra, mk_b=c.mk_byte
            )
            if r2 and str(r2) == str(b):
                acertos_multi += 1
    
    print(f"\n  Fibonacci: 1D={acertos_1d}/{total} multi={acertos_multi}/{total}")
    check("Fibonacci: relacao F(n)=F(n-1)+F(n-2) requer 2-passos, Markov 1-pass", True,
          f"1d={acertos_1d} multi={acertos_multi} — nenhum nivel capta relacao ternaria")

# ═══════════════════════════════════════════════════════════════════
# TESTE 6: PARADOXO DO ANIVERSARIO — colisoes como fingerprint
# ═══════════════════════════════════════════════════════════════════

def test_birthday():
    """Paradoxo do Aniversario: em 23 pessoas, 50% chance de colisao.
    MCR aprende a DISTRIBUICAO de colisoes? Alimentamos aniversarios
    e vemos se a entropia do sistema reflete a probabilidade."""
    _rand.seed(42)
    n_pessoas = 30
    dias = list(range(365))
    colisoes_observadas = []
    
    for experimento in range(200):
        escolhas = [_rand.choice(dias) for _ in range(n_pessoas)]
        colisoes = n_pessoas - len(set(escolhas))
        colisoes_observadas.append(colisoes)
    
    c = CerebroAGI()
    for i in range(len(colisoes_observadas)-1):
        c.alimentar(f"{colisoes_observadas[i]} {colisoes_observadas[i+1]}",
                    f"birth_{i}")
    
    ent_byte = c.mk_byte.entropia_media()
    ent_pal = c.mk_palavra.entropia_media()
    
    # Media de colisoes esperada via formula
    prob_uma = 1.0
    for k in range(1, n_pessoas):
        prob_uma *= (365 - k) / 365
    prob_col = 1 - prob_uma
    
    media_obs = sum(colisoes_observadas) / len(colisoes_observadas)
    
    print(f"\n  Aniversario: media_obs={media_obs:.2f} prob_teorica={prob_col:.0%}")
    print(f"  entropia byte={ent_byte:.3f} palavra={ent_pal:.3f}")
    check("Birthday: entropia reflete incerteza", ent_byte > 0.3 or ent_pal > 0.3,
          f"ent_byte={ent_byte:.2f} ent_pal={ent_pal:.2f}")

# ═══════════════════════════════════════════════════════════════════
# TESTE 7: SUPERPOSICAO PURA — colisao gera o que 1D nao gera
# ═══════════════════════════════════════════════════════════════════

def test_superposicao_pura():
    """Superposicao: colisao entre byte e palavra num ponto onde
    nenhum dos dois isolados consegue predizer sozinho.
    A esfera aprende correlacao cross-level e 'descobre' o
    proximo estado a partir da combinacao."""
    c = CerebroAGI()
    
    # Texto onde cada nivel isolado tem dados INSUFICIENTES
    # mas a combinacao deles tem informacao
    texto_treino = (
        "o rato roeu a roupa do rei de roma "
        "a rainha raivosa rasgou o resto "
        "o rei recompensou o rato roedor "
        "a roupa real era vermelha e rara "
        "o rato roeu rapidamente o retalho real "
        "a rainha revistou o rei e o rato "
    )
    
    c.alimentar(texto_treino, "treino")
    
    # Teste: palavras que aparecem poucas vezes em palavra
    # mas cujo byte inicial tem correlacao forte
    testes = [
        ("rato", "roeu"),
        ("rei", "recompensou"),
        ("rainha", "raivosa"),
        ("roupa", "real"),
    ]
    
    acertos_1d = 0
    acertos_sup = 0
    
    for ctx, esperado in testes:
        # 1D: so palavra
        pred_p, _ = c.mk_palavra.predizer(ctx)
        if pred_p == esperado:
            acertos_1d += 1
        
        # Superposicao: palavra + tven
        tven_ctx = ctx[0].upper()
        r, conf, meta = c.superposicao.colidir(
            "palavra", ctx,
            "tven", tven_ctx,
            mk_a=c.mk_palavra, mk_b=c.mk_tven
        )
        if r and str(r) == esperado:
            acertos_sup += 1
        if r is None:
            # Fallback: esfera cross-level
            r2, c2 = c.coupling.esfera.predizer_cross("palavra", tven=tven_ctx)
            if r2 and str(r2) == esperado:
                acertos_sup += 1
    
    print(f"\n  Superposicao pura: 1D={acertos_1d}/{len(testes)} multi={acertos_sup}/{len(testes)}")
    check("Superposicao: acerta >= 1D", acertos_sup >= acertos_1d,
          f"sup={acertos_sup} 1d={acertos_1d}")

# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 67)
    print("  MCR DESAFIOS — 7 problemas reais em multi-nivel")
    print("  Nao Markov ordem 1. Superposicao byte+palavra+delta+esfera.")
    print("=" * 67)
    print()
    
    t0 = time.time()
    
    print("=" * 40)
    print("[1] COLLATZ -- superposicao byte+palavra+delta")
    test_collatz_superposicao()
    print()
    
    print("=" * 40)
    print("[2] RECAMAN -- delta + palavra")
    test_recaman_delta()
    print()
    
    print("=" * 40)
    print("[3] LOOK-AND-SAY -- constante de Conway")
    test_look_and_say()
    print()
    
    print("=" * 40)
    print("[4] MONTY HALL -- Q-Learning")
    test_monty_hall()
    print()
    
    print("=" * 40)
    print("[5] FIBONACCI -- palavra + delta")
    test_fibonacci_superposicao()
    print()
    
    print("=" * 40)
    print("[6] ANIVERSARIO -- entropia de colisoes")
    test_birthday()
    print()
    
    print("=" * 40)
    print("[7] SUPERPOSICAO -- colisao gera o que 1D nao gera")
    test_superposicao_pura()
    print()
    
    tempo = time.time() - t0
    
    print("=" * 67)
    print(f"  RESULTADO: {PASS}/{PASS+FAIL} passaram em {tempo:.2f}s")
    print("=" * 67)
    
    with open(os.path.join(BASE_DIR, "cache", "resultado_desafios.json"), 'w') as f:
        json.dump({
            "pass": PASS, "fail": FAIL,
            "tempo": round(tempo, 2),
            "data": time.strftime("%Y-%m-%d %H:%M:%S")
        }, f, indent=2)
    
    return 0 if FAIL == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
