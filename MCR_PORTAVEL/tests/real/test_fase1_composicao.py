"""test_fase1_composicao.py — Teste da FASE 1 do Plano de Evolução MCR.

Valida o operador compor() e a assinatura composicional de frases.

Criterios do plano (docs/PLANO_EVOLUCAO_MCR.md):
  1.1 compor(): combinacao modificacao vs complemento
  1.2 _assinatura_frase(): frase multi-palavra -> assinatura unica
  1.3 validacao:
    - "cachorro verde" closer de "cachorro" que de "verde"
    - "correr rapido" closer de "correr" que de "rapido"
    - "nao bom" closer de "ruim" (negacao inverte)

Métrica de sucesso (plano): >70% de acerto em composicao nominal.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcr.coupling import MCRCoupling

PASS, FAIL = 0, 0


def T(nome, cond, detalhe=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  [PASS] {nome}')
    else:
        FAIL += 1
        print(f'  [FAIL] {nome} — {detalhe}')


def main():
    global PASS, FAIL
    print('=' * 72)
    print('  FASE 1 — TESTE DE COMPOSICAO SEMANTICA')
    print('  Plano de Evolucao MCR v2.0')
    print('=' * 72)

    # === Base de treino ===
    # Precisamos de um corpus onde "cachorro", "verde", "correr",
    # "rapido", "bom", "ruim", "nao" aparecem em contextos que
    # permitam ao MCR aprender suas assinaturas.
    # 
    # Contraste de acao: bom→aprovar, ruim→rejeitar (para antonimos)
    # "nao" aparece com MUITAS acoes diversas (alta entropia = funtor)
    # "nao" NAO aparece junto com bom/ruim para evitar poluicao
    pares = [
        ("criar cachorro magico", "criar_monstro"),
        ("cachorro corre rapido", "mover"),
        ("cachorro verde corre", "mover"),
        ("verde grama planicie", "descrever"),
        ("verde floresta natureza", "descrever"),
        ("correr rapido fugir", "mover"),
        ("correr lento andar", "mover"),
        ("rapido veloz agil", "descrever"),
        ("bom personagem aliado", "aprovar"),
        ("ruim personagem inimigo", "rejeitar"),
        ("bom forte corajoso", "aprovar"),
        ("ruim fraco covarde", "rejeitar"),
        ("nao corre parado", "mover"),
        ("nao voa baixo", "mover"),
        ("nao ataca defendo", "descrever"),
        ("nao ajuda atrapalha", "descrever"),
        ("nao cria destroi", "destruir"),
        ("nao cura fere", "atacar"),
        ("nao aceita recusa", "rejeitar"),
        ("nao abre fecha", "editar"),
        ("cachorro late forte", "descrever"),
        ("gato late fraco", "descrever"),
        ("verde olho magico", "descrever"),
        ("monstro verde cachorro", "criar_monstro"),
        ("dragao voa alto", "mover"),
        ("bom item raro", "aprovar"),
        ("ruim item comum", "rejeitar"),
    ]

    c = MCRCoupling()
    for t, a in pares:
        for _ in range(3):
            c.alimentar(t, a)

    print('\n[1] compor() — deteccao automatica modificacao vs complemento')
    sig_cachorro = c._assinatura_palavra("cachorro")
    sig_verde = c._assinatura_palavra("verde")
    sig_correr = c._assinatura_palavra("correr")
    sig_rapido = c._assinatura_palavra("rapido")

    T("sig(cachorro) extraida", len(sig_cachorro) > 0, f"len={len(sig_cachorro)}")
    T("sig(verde) extraida", len(sig_verde) > 0, f"len={len(sig_verde)}")
    T("sig(correr) extraida", len(sig_correr) > 0, f"len={len(sig_correr)}")
    T("sig(rapido) extraida", len(sig_rapido) > 0, f"len={len(sig_rapido)}")

    print('\n[2] compor() — tipos conforme entropia')
    sig_cv_mod = c.compor(sig_cachorro, sig_verde, tipo="modificacao")
    sig_cv_comp = c.compor(sig_cachorro, sig_verde, tipo="complemento")
    T("compor(modificacao) nao vazio", len(sig_cv_mod) > 0)
    T("compor(complemento) nao vazio", len(sig_cv_comp) > 0)
    T("modificacao preserva base (tem features de cachorro)",
      any(k.startswith("acao:") for k in sig_cv_mod),
      f"keys={list(sig_cv_mod.keys())[:5]}")

    sig_cv_auto = c.compor(sig_cachorro, sig_verde)
    T("compor(auto) detecta tipo", sig_cv_auto != {})

    print('\n[3] _assinatura_frase() — frase multi-palavra')
    sig_frase_cv = c._assinatura_frase("cachorro verde")
    T("sig_frase(cachorro verde) nao vazia", len(sig_frase_cv) > 0,
      f"len={len(sig_frase_cv)}")
    sig_frase_cr = c._assinatura_frase("correr rapido")
    T("sig_frase(correr rapido) nao vazia", len(sig_frase_cr) > 0,
      f"len={len(sig_frase_cr)}")

    print('\n[4] TESTE CRITICO 1.3a — "cachorro verde" closer de "cachorro"')
    sim_cv_cachorro = c.similaridade("cachorro verde", "cachorro")
    sim_cv_verde = c.similaridade("cachorro verde", "verde")
    print(f'    sim("cachorro verde", "cachorro") = {sim_cv_cachorro:.4f}')
    print(f'    sim("cachorro verde", "verde")    = {sim_cv_verde:.4f}')
    T('"cachorro verde" closer de "cachorro"',
      sim_cv_cachorro > sim_cv_verde,
      f'{sim_cv_cachorro:.4f} vs {sim_cv_verde:.4f}')

    print('\n[5] TESTE CRITICO 1.3b — "correr rapido" closer de "correr"')
    sim_cr_correr = c.similaridade("correr rapido", "correr")
    sim_cr_rapido = c.similaridade("correr rapido", "rapido")
    print(f'    sim("correr rapido", "correr") = {sim_cr_correr:.4f}')
    print(f'    sim("correr rapido", "rapido") = {sim_cr_rapido:.4f}')
    T('"correr rapido" closer de "correr"',
      sim_cr_correr > sim_cr_rapido,
      f'{sim_cr_correr:.4f} vs {sim_cr_rapido:.4f}')

    print('\n[6] TESTE CRITICO 1.3c — "nao bom" closer de "ruim" (negacao)')
    sim_nb_ruim = c.similaridade("nao bom", "ruim")
    sim_nb_bom = c.similaridade("nao bom", "bom")
    print(f'    sim("nao bom", "ruim") = {sim_nb_ruim:.4f}')
    print(f'    sim("nao bom", "bom")  = {sim_nb_bom:.4f}')
    T('"nao bom" closer de "ruim" que de "bom"',
      sim_nb_ruim > sim_nb_bom,
      f'{sim_nb_ruim:.4f} vs {sim_nb_bom:.4f} [LIMITACAO FASE 1: negacao requer dados de treino onde "nao X" e rotulado como oposto de X]')

    print('\n[7] Assinatura preserva conceito base em modificacao')
    sig_mod = c.compor(sig_cachorro, sig_verde, tipo="modificacao")
    sig_comp = c.compor(sig_cachorro, sig_verde, tipo="complemento")
    nmi_mod_cachorro = c._nmi(sig_mod, sig_cachorro)
    nmi_comp_cachorro = c._nmi(sig_comp, sig_cachorro)
    print(f'    NMI(modificacao, cachorro) = {nmi_mod_cachorro:.4f}')
    print(f'    NMI(complemento, cachorro) = {nmi_comp_cachorro:.4f}')
    T('modificacao mais proxima da base que complemento',
      nmi_mod_cachorro >= nmi_comp_cachorro,
      f'{nmi_mod_cachorro:.4f} vs {nmi_comp_cachorro:.4f}')

    print('\n[8] Nao regressao — similaridade palavra-palavra funciona')
    sim_criar_gerar = c.similaridade("cachorro", "verde")
    T('similaridade palavra unica ainda funciona',
      0.0 <= sim_criar_gerar <= 1.0,
      f'valor={sim_criar_gerar:.4f}')

    print('\n[9] Idempotencia — compor(x, x) preserva x')
    sig_xx = c.compor(sig_cachorro, sig_cachorro, tipo="complemento")
    nmi_xx = c._nmi(sig_xx, sig_cachorro)
    print(f'    NMI(compor(x,x,complemento), x) = {nmi_xx:.4f}')
    T('compor(x,x,complemento) proximo de x (>= 0.90)',
      nmi_xx >= 0.90,
      f'{nmi_xx:.4f} (esperado >= 0.90)')

    print('\n' + '=' * 72)
    print(f'  RESULTADO: {PASS} PASS / {FAIL} FAIL')
    print('=' * 72)
    return FAIL == 0


if __name__ == '__main__':
    ok = main()
    sys.exit(0 if ok else 1)
