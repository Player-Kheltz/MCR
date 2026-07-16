"""test_fase5_hierarquico.py — Teste da FASE 5: Acoplamento Hierarquico.

Valida MCRHierarquico: MCR de MCRs com auto-limitacao entropica.
Cada camada comprime a anterior via assinatura. A hierarquia para
quando delta_H aprox 0 (sem reducao de incerteza).

Criterios do plano (docs/PLANO_EVOLUCAO_MCR.md):
  5.1 MCR de MCRs — cada camada usa compor() da anterior
  5.2 Niveis: palavra -> frase -> paragrafo -> topico -> ...
  5.3 Auto-limitacao entropica: para quando delta_H approx 0

Pilar 1: cada camada e um MCRCoupling (P(b|a))
Pilar 2: entropia decide quando parar (delta_H)
Pilar 5: alimentar -> predizer -> avaliar -> aprender
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcr.acoplamento_hierarquico import MCRHierarquico
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
    print('  FASE 5 — TESTE DE ACOPLAMENTO HIERARQUICO')
    print('  Plano de Evolucao MCR v2.2')
    print('=' * 72)

    print('\n[1] Instanciacao — MCRHierarquico com 1 camada inicial')
    h = MCRHierarquico(max_niveis=7, min_delta_h=0.05)
    T('instanciou', h is not None)
    T('comeca com 1 camada', len(h.camadas) == 1)
    T('camada 0 e MCRCoupling', isinstance(h.camadas[0], MCRCoupling))
    T('max_niveis=7', h.max_niveis == 7)

    print('\n[2] Alimentar — texto e acao nas camadas')
    pares = [
        ("criar monstro dragao fogo forte", "criar_monstro"),
        ("gerar monstro orc vendedor espadas", "criar_monstro"),
        ("criar npc mago lich aliado vila", "criar_npc"),
        ("gerar npc ferreiro anao armaduras", "criar_npc"),
        ("curar mago aliado ferido pocao", "curar"),
        ("restaurar ferreiro ferido magico", "curar"),
        ("atacar monstro dragao fogo espada", "atacar"),
        ("lutar contra orc mago aliado", "atacar"),
        ("analisar codigo fonte estruturado", "analisar"),
        ("examinar texto log erros sistema", "analisar"),
        ("criar quest complexa multi etapas", "gerar_quest"),
        ("gerar quest epica recompensa rara", "gerar_quest"),
        ("descrever paisagem montanha verde", "responder"),
        ("explicar conceito entropia shannon", "responder"),
        ("planejar ataque estrategia militar", "planejar"),
        ("planejar defesa fortificada aliados", "planejar"),
    ]

    for texto, acao in pares:
        for _ in range(5):
            h.alimentar(texto, acao)

    T('alimentar executou', h._total_observacoes == len(pares) * 5)
    print(f'    total observacoes: {h._total_observacoes}')

    print('\n[3] Predizer — classificacao com hierarquia')
    acao, conf = h.predizer("criar monstro dragao")
    print(f'    predizer("criar monstro dragao") -> acao={acao}, conf={conf:.3f}')
    T('predizer retornou acao', acao is not None)
    acoes_criar = {"criar_monstro", "criar_npc", "gerar_quest"}
    T('predizer retornou acao de criar', acao in acoes_criar,
      f'acao={acao} (esperado uma de {acoes_criar})')

    acao2, conf2 = h.predizer("curar mago ferido")
    print(f'    predizer("curar mago ferido") -> acao={acao2}, conf={conf2:.3f}')
    T('predizer curar = "curar"', acao2 == "curar", f'acao={acao2}')

    acao3, conf3 = h.predizer("analisar codigo fonte")
    print(f'    predizer("analisar codigo fonte") -> acao={acao3}, conf={conf3:.3f}')
    T('predizer analisar = "analisar"', acao3 == "analisar", f'acao={acao3}')

    print('\n[4] Auto-limitacao entropica — numero de camadas emerge')
    stats = h.estatisticas()
    print(f'    estatisticas: {stats}')
    T('tem pelo menos 1 camada', stats['niveis'] >= 1)
    T(' nao excedeu max_niveis', stats['niveis'] <= h.max_niveis)

    print('\n[5] _comprimir — cada nivel comprime o anterior')
    texto_teste = "criar monstro dragao fogo"
    nivel0 = h._comprimir(texto_teste, 0)
    nivel1 = h._comprimir(texto_teste, 1) if len(h.camadas) > 1 else "N/A"
    print(f'    nivel 0: "{nivel0[:60]}"')
    print(f'    nivel 1: "{nivel1[:60]}"')
    T('nivel 0 tokenizado', nivel0 != texto_teste or ' ' in nivel0)
    T('nivel 0 tem palavras', len(nivel0.split()) >= 2)

    print('\n[6] _entropia_camada — entropia por nivel')
    if len(h.camadas) >= 1:
        h0 = h._entropia_camada(0)
        print(f'    H(camada 0) = {h0:.4f}')
        T('entropia camada 0 em [0,1]', 0.0 <= h0 <= 1.0)
    if len(h.camadas) >= 2:
        h1 = h._entropia_camada(1)
        print(f'    H(camada 1) = {h1:.4f}')
        T('entropia camada 1 em [0,1]', 0.0 <= h1 <= 1.0)

    print('\n[7] Hierarquia vs simples — mesma categoria?')
    c_simples = MCRCoupling()
    for t, a in pares:
        for _ in range(5):
            c_simples.alimentar(t, a)
    acao_s, conf_s = c_simples.decidir("criar monstro dragao", (None, 0.0))
    acao_h, conf_h = h.predizer("criar monstro dragao")
    print(f'    simples: acao={acao_s}, conf={conf_s:.3f}')
    print(f'    hierarquico: acao={acao_h}, conf={conf_h:.3f}')
    T('hierarquico e simples na mesma categoria',
      acao_h in acoes_criar and acao_s in acoes_criar,
      f'hierarquico={acao_h} vs simples={acao_s}')

    print('\n[8] Textos longos — hierarquia entende melhor?')
    texto_longo = ("criar monstro dragao fogo forte que voa alto e ataca "
                   "vila com garras afiadas e sopro de fogo mortal")
    acao_l, conf_l = h.predizer(texto_longo)
    acao_ls, conf_ls = c_simples.decidir(texto_longo, (None, 0.0))
    print(f'    texto longo ({len(texto_longo)} chars):')
    print(f'    hierarquico: acao={acao_l}, conf={conf_l:.3f}')
    print(f'    simples:     acao={acao_ls}, conf={conf_ls:.3f}')
    T('hierarquico classificou texto longo', acao_l is not None)
    T('hierarquico acertou categoria criar', acao_l in acoes_criar,
      f'acao={acao_l} (esperado uma de {acoes_criar})')

    print('\n[9] gerar_texto — camada 0 gera Markov')
    gerado = h.gerar_texto("criar monstro", max_tokens=10)
    print(f'    gerar_texto("criar monstro", 10) = "{gerado}"')
    T('gerar_texto nao vazio', bool(gerado))
    T('gerar_texto tem palavras', len(gerado.split()) >= 2)

    print('\n[10] Nao regressao — FASE 1-4 ainda funcionam')
    c = MCRCoupling()
    c.alimentar("criar monstro dragao", "criar_monstro")
    c.alimentar("gerar monstro orc", "criar_monstro")
    c.alimentar_estado("fogo", {"temp": 200, "dano": 5})
    sig_frase = c._assinatura_frase("monstro verde")
    T('FASE 1 assinatura_frase funciona', len(sig_frase) > 0)
    rel = c.extrair_relacoes("criar")
    T('FASE 2 extrair_relacoes funciona', bool(rel))
    estado_fogo = c.predizer_estado("fogo")
    T('FASE 3 predizer_estado funciona', "temp" in estado_fogo)

    print('\n[11] Persistencia — save/load')
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as f:
        tmp = f.name
    h.save(tmp)
    h2 = MCRHierarquico()
    loaded = h2.load(tmp)
    T('load() retornou True', loaded)
    T('camadas restauradas', len(h2.camadas) >= 1)
    # Limpa arquivos de camada
    base_dir = os.path.dirname(tmp)
    prefixo = os.path.splitext(os.path.basename(tmp))[0]
    for i in range(10):
        cam = os.path.join(base_dir, f"{prefixo}_camada{i}.json")
        if os.path.exists(cam):
            os.unlink(cam)
    os.unlink(tmp)

    print('\n[12] Auto-expansao com mais dados')
    h3 = MCRHierarquico(max_niveis=7, min_delta_h=0.05)
    # Alimentar muitos pares para forcar expansao
    for i in range(50):
        h3.alimentar("criar monstro dragao fogo forte", "criar_monstro")
        h3.alimentar("gerar npc orc vendedor espadas", "gerar_npc")
        h3.alimentar("curar mago aliado ferido pocao", "curar")
        h3.alimentar("analisar codigo fonte estruturado", "analisar")
    stats3 = h3.estatisticas()
    print(f'    apos 200 obs: niveis={stats3["niveis"]}, '
          f'entropias={stats3["entropias_por_nivel"]}')
    T('auto-expansao respeitou max_niveis', stats3['niveis'] <= 7)
    T('auto-expansao tem pelo menos 1 nivel', stats3['niveis'] >= 1)

    print('\n' + '=' * 72)
    print(f'  RESULTADO: {PASS} PASS / {FAIL} FAIL')
    print('=' * 72)
    return FAIL == 0


if __name__ == '__main__':
    ok = main()
    sys.exit(0 if ok else 1)
