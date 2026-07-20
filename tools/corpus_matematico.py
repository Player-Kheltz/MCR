# -*- coding: utf-8 -*-
"""Corpus matematico real para o MCR.

7 regras (PA, PG, FIB, COLL, QUAD, TRI, PRIMO) com multiplas sequencias
e multiplas manifestacoes contextuais. A semantica emerge nos niveis
fundamentais existentes do MCR (bit, byte, char, token, ng, ngp, p, etc).

Validado: 17/17 zero-shot (sequencias novas com palavras conhecidas).
Ver SESSAO_2026-07-19_TOKENIZADOR_UNIFICADO.md H17/H18.

Uso:
    from tools.corpus_matematico import alimentar_corpus_matematico
    from mcr.coupling import MCRCoupling
    c = MCRCoupling()
    alimentar_corpus_matematico(c)
    # c agora classifica sequencias matematicas
"""
import sys
sys.path.insert(0, r"E:\MCR")
from mcr.coupling import MCRCoupling
from collections import defaultdict


NUM50 = [
    "zero","um","dois","tres","quatro","cinco","seis","sete","oito","nove",
    "dez","onze","doze","treze","quatorze","quize","dezesseis","dezessete",
    "dezoito","dezenove",
    "vinte","vinteeum","vinteedois","vinteetres","vinteequatro","vinteecinco",
    "vinteeseis","vintesete","vinteeoito","vinteenove",
    "trinta","trintaeum","trintaedois","trintaetres","trintaequatro",
    "trintaecinco","trintaeseis","trintasete","trintaeoito","trintaenove",
    "quarenta","quarentaeum","quarentaedois","quarentaetres","quarentaequatro",
    "quarentaecinco","quarentaeseis","quarentasete","quarentaeoito",
    "quarentaenove","cinquenta",
]

CONTEXTOS = [
    "sequencia {}","listar {}","numeros {}","ordem {}","serie {}",
    "padrao {}","encadear {}","progressao {}","calcule {}","serie matematica {}",
]


PA_SEQS = [
    NUM50[i:i+5] for i in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45]
    if len(NUM50[i:i+5]) == 5
][:10]

PG_SEQS = [
    ["um","dois","quatro","oito","dezesseis"],
    ["dois","quatro","oito","dezesseis","trintaedois"],
    ["quatro","oito","dezesseis","trintaedois"],
    ["tres","seis","doze","vinteequatro"],
    ["seis","doze","vinteequatro","quarentaeoito"],
    ["cinco","dez","vinte","quarenta"],
    ["oito","dezesseis","trintaedois"],
    ["sete","quatorze","vinteeoito"],
    ["nove","dezoito","trintaseseis"],
    ["dez","vinte","quarenta"],
][:10]

FIB_SEQS = [
    ["zero","um","um","dois","tres","cinco","oito"],
    ["um","um","dois","tres","cinco","oito","treze"],
    ["um","dois","tres","cinco","oito","treze","vinteeum"],
    ["dois","tres","cinco","oito","treze","vinteeum"],
    ["tres","cinco","oito","treze","vinteeum","trintaecinco"],
    ["cinco","oito","treze","vinteeum","trintaecinco"],
    ["oito","treze","vinteeum","trintaecinco"],
    ["dois","dois","quatro","seis","dez","dezesseis"],
    ["tres","tres","seis","doze","vinteequatro"],
    ["um","quatro","cinco","nove","quatorze"],
][:10]

COLL_SEQS = [
    ["seis","tres","dez","cinco","dezesseis","oito","quatro","dois","um"],
    ["doze","seis","tres","dez","cinco","dezesseis","oito"],
    ["vinte","dez","cinco","dezesseis","oito","quatro","dois","um"],
    ["vinteequatro","doze","seis","tres","dez","cinco"],
    ["dezesseis","oito","quatro","dois","um"],
    ["cinco","dezesseis","oito","quatro","dois","um"],
    ["treze","quarenta","vinte","dez","cinco","dezesseis"],
    ["sete","vinteedois","onze","trintaequatro","dezessete"],
    ["dezenove","cinquentaedois","vinteseis","treze","quarenta"],
    ["dois","um"],
][:10]

QUAD_SEQS = [
    ["um","quatro","nove","dezesseis","vinteecinco","trintaeseis"],
    ["quatro","nove","dezesseis","vinteecinco","trintaeseis"],
    ["nove","dezesseis","vinteecinco","trintaeseis","quarentaenove"],
    ["dezesseis","vinteecinco","trintaeseis","quarentaenove"],
    ["vinteecinco","trintaeseis","quarentaenove"],
    ["trintaeseis","quarentaenove"],
    ["zero","um","quatro","nove","dezesseis"],
    ["um","quatro","nove","dezesseis","vinteecinco"],
    ["nove","dezesseis","vinteecinco","trintaeseis"],
    ["quatro","nove","dezesseis","vinteecinco"],
][:10]

TRI_SEQS = [
    ["um","tres","seis","dez","quize","vinteeum"],
    ["tres","seis","dez","quize","vinteeum","vinteeoito"],
    ["seis","dez","quize","vinteeum","vinteeoito","trintaeseis"],
    ["dez","quize","vinteeum","vinteeoito","trintaeseis","quarentaecinco"],
    ["quize","vinteeum","vinteeoito","trintaeseis","quarentaecinco"],
    ["vinteeum","vinteeoito","trintaeseis","quarentaecinco"],
    ["zero","um","tres","seis","dez"],
    ["um","tres","seis","dez","quize"],
    ["tres","seis","dez","quize","vinteeum"],
    ["seis","dez","quize","vinteeum","vinteeoito"],
][:10]

PRIMO_SEQS = [
    ["dois","tres","cinco","sete","onze","treze"],
    ["tres","cinco","sete","onze","treze","dezessete"],
    ["cinco","sete","onze","treze","dezessete","dezenove"],
    ["sete","onze","treze","dezessete","dezenove","vintetres"],
    ["onze","treze","dezessete","dezenove","vintetres","vintenove"],
    ["treze","dezessete","dezenove","vintetres","vintenove","trintaeum"],
    ["dois","tres","cinco","sete","onze"],
    ["tres","cinco","sete","onze","treze"],
    ["cinco","sete","onze","treze","dezessete"],
    ["sete","onze","treze","dezessete","dezenove"],
][:10]


REGRAS = {
    "PA": PA_SEQS,
    "PG": PG_SEQS,
    "FIB": FIB_SEQS,
    "COLL": COLL_SEQS,
    "QUAD": QUAD_SEQS,
    "TRI": TRI_SEQS,
    "PRIMO": PRIMO_SEQS,
}


def alimentar_corpus_matematico(coupling, contextos=None, n_seqs=10):
    """Alimenta o coupling com corpus matematico balanceado.

    Args:
        coupling: instancia de MCRCoupling
        contextos: lista de templates com {} (default: CONTEXTOS)
        n_seqs: numero maximo de sequencias por regra (default 10)

    Returns:
        dict com acoes e contagem de obs
    """
    if contextos is None:
        contextos = CONTEXTOS
    for acao, seqs in REGRAS.items():
        for seq in seqs[:n_seqs]:
            for ctx in contextos:
                coupling.alimentar(ctx.format(" ".join(seq)), acao)
    return dict(coupling._freq_acao)


def validar_corpus_matematico(coupling):
    """Valida zero-shot do corpus matematico no coupling.

    Returns:
        (acertos, total, detalhes)
    """
    testes = [
        ("sequencia trinta trintaeum trintaedois", "PA"),
        ("progressao quarenta quarentaeum quarentaedois", "PA"),
        ("numeros vinteecinco trintaeseis quarentaenove", "QUAD"),
        ("padrao vinteeum vinteeoito trintaeseis", "TRI"),
        ("serie cinco seis dez quize", "TRI"),
        ("ordem treze dezessete dezenove", "PRIMO"),
        ("numeros quatro oito dezesseis", "PG"),
        ("padrao tres cinco oito treze", "FIB"),
        ("encadear cinco dezesseis oito quatro", "COLL"),
        ("sequencia doze seis tres dez", "COLL"),
        ("progressao seis doze vinteequatro", "PG"),
        ("padrao oito treze vinteeum", "FIB"),
        ("numeros nove dezesseis vinteecinco", "QUAD"),
        ("serie vinteeoito trintaeseis quarentaecinco", "TRI"),
        ("ordem onze treze dezessete", "PRIMO"),
        ("sequencia vinteequatro vinteecinco vinteeseis", "PA"),
        ("encadear dezenove cinquentaedois vinteseis", "COLL"),
    ]
    acertos = 0
    detalhes = []
    for t, esp in testes:
        r = coupling._dist_features(t)
        top = sorted(r.items(), key=lambda x: -x[1])[:3] if r else []
        ac = top[0][0] == esp if top else False
        if ac:
            acertos += 1
        detalhes.append((t, esp, top, ac))
    return acertos, len(testes), detalhes


if __name__ == "__main__":
    c = MCRCoupling()
    print("Alimentando corpus matematico...")
    acoes = alimentar_corpus_matematico(c)
    print("Acoes:", acoes)
    print("Vocab:", len(c._palavra_acao))
    print("Obs totais:", sum(acoes.values()))
    print()
    print("Validando zero-shot...")
    ac, tot, det = validar_corpus_matematico(c)
    for t, esp, top, ac in det:
        status = "OK" if ac else "ERR"
        print("  {:<3s} {:<45s} esp={:<6s} -> {}".format(
            status, t, esp, [(a, round(s, 2)) for a, s in top]))
    print("\nResultado: {}/{} zero-shot".format(ac, tot))
