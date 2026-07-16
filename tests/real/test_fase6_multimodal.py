"""test_fase6_multimodal.py — Teste da FASE 6: Multimodalidade.

Valida MCRMultimodal: assinatura unificada texto/audio/imagem via NMI.
MCR descobre equivalencia cross-modal sem dicionario, sem embedding,
sem GPU — apenas Markov + Entropia + NMI.

Criterios do plano (docs/PLANO_EVOLUCAO_MCR.md):
  6.1 Assinatura unificada — qualquer modalidade vira features
  6.2 Cross-modal via NMI — acoes compartilhadas => convergencia
  6.3 Traducao cross-modal — audio -> texto, imagem -> texto
  6.4 Equacao 5D avalia match cross-modal

Pilar 1: P(feature | conceito) — transicao markoviana
Pilar 2: NMI descobre cross-modal (sem threshold)
Pilar 3: mesmo motor, qualquer modalidade
Pilar 5: alimentar -> recuperar -> aprender

Dados sinteticos (zero dependencias externas):
  Audio: struct + math geram WAV-like (ruido = fogo, senoide = agua)
  Imagem: bytes RGB brutos (vermelho = fogo, azul = agua)
"""
import sys, os, math, struct, random
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcr.multimodal import MCRMultimodal
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


# ─── Geradores de dados sinteticos ──────────────────────────

def gerar_audio_ruido(n_amostras=2000, seed=42):
    """Audio de ruido — simula som de fogo (caotico, alta energia)."""
    random.seed(seed)
    dados = bytearray()
    for _ in range(n_amostras):
        val = random.randint(-32767, 32767)
        dados.extend(struct.pack('<h', val))
    return bytes(dados)


def gerar_audio_senoide(n_amostras=2000, freq=220, seed=99):
    """Audio de senoide — simula som de agua calma (estruturado)."""
    random.seed(seed)
    dados = bytearray()
    for i in range(n_amostras):
        val = int(32000 * math.sin(2 * math.pi * freq * i / 44100))
        val += random.randint(-100, 100)
        dados.extend(struct.pack('<h', val))
    return bytes(dados)


def gerar_imagem_fogo(largura=32, altura=32):
    """Imagem vermelho/laranja — simula imagem de fogo."""
    dados = bytearray()
    for _ in range(largura * altura):
        r = random.randint(200, 255)
        g = random.randint(50, 150)
        b = random.randint(0, 30)
        dados.extend([r, g, b])
    return bytes(dados)


def gerar_imagem_agua(largura=32, altura=32):
    """Imagem azul — simula imagem de agua."""
    dados = bytearray()
    for _ in range(largura * altura):
        r = random.randint(0, 30)
        g = random.randint(50, 100)
        b = random.randint(180, 255)
        dados.extend([r, g, b])
    return bytes(dados)


def gerar_imagem_floresta(largura=32, altura=32):
    """Imagem verde — simula imagem de floresta."""
    dados = bytearray()
    for _ in range(largura * altura):
        r = random.randint(20, 80)
        g = random.randint(150, 255)
        b = random.randint(20, 80)
        dados.extend([r, g, b])
    return bytes(dados)


def main():
    global PASS, FAIL
    print('=' * 72)
    print('  FASE 6 — TESTE DE MULTIMODALIDADE')
    print('  Plano de Evolucao MCR v2.2')
    print('=' * 72)

    # Gerar dados sinteticos
    audio_fogo = gerar_audio_ruido(n_amostras=2000, seed=42)
    audio_fogo_2 = gerar_audio_ruido(n_amostras=2000, seed=100)
    audio_agua = gerar_audio_senoide(n_amostras=2000, freq=220, seed=99)
    audio_agua_2 = gerar_audio_senoide(n_amostras=2000, freq=440, seed=77)

    img_fogo = gerar_imagem_fogo()
    img_agua = gerar_imagem_agua()
    img_floresta = gerar_imagem_floresta()

    print('\n[1] MCRMultimodal — instanciacao')
    mm = MCRMultimodal()
    T('instanciou', mm is not None)
    T('coupling subjacente e MCRCoupling', isinstance(mm.coupling, MCRCoupling))
    T('comeca sem conceitos', len(mm._conceitos) == 0)

    print('\n[2] Extracao de features por modalidade')
    feat_texto = mm._extrair_features_modal("texto", "fogo queima")
    feat_audio = mm._extrair_features_modal("audio", audio_fogo)
    feat_imagem = mm._extrair_features_modal("imagem", img_fogo)
    feat_codigo = mm._extrair_features_modal("codigo", "def criar(): pass")

    T('texto extrai features', len(feat_texto) > 0, f'feat="{feat_texto[:50]}"')
    T('audio extrai features', len(feat_audio) > 0, f'feat="{feat_audio[:50]}"')
    T('imagem extrai features', len(feat_imagem) > 0, f'feat="{feat_imagem[:50]}"')
    T('codigo extrai features', len(feat_codigo) > 0, f'feat="{feat_codigo[:50]}"')
    T('audio tem tokens auh', 'auh' in feat_audio, f'feat="{feat_audio[:80]}"')
    T('imagem tem tokens im', 'im' in feat_imagem, f'feat="{feat_imagem[:80]}"')
    T('tokens audio sao puramente alfabeticos',
      all(w.isalpha() for w in feat_audio.split()),
      f'feat="{feat_audio[:80]}"')

    print('\n[3] Features distinguem modalidades')
    feat_fogo_audio = mm._extrair_features_modal("audio", audio_fogo)
    feat_agua_audio = mm._extrair_features_modal("audio", audio_agua)
    feat_fogo_img = mm._extrair_features_modal("imagem", img_fogo)
    feat_agua_img = mm._extrair_features_modal("imagem", img_agua)

    T('audio fogo != audio agua', feat_fogo_audio != feat_agua_audio)
    T('imagem fogo != imagem agua', feat_fogo_img != feat_agua_img)
    T('audio fogo tem mais energia', 'aue' in feat_fogo_audio)
    T('imagem fogo tem vermelho (imr)', 'imr' in feat_fogo_img)
    T('imagem agua tem azul (imb)', 'imb' in feat_agua_img)

    print('\n[4] Alimentar — texto, audio, imagem com mesma acao')
    # Multiplas observacoes por conceito para fortalecer o sinal
    for _ in range(5):
        mm.alimentar("texto", "fogo queima monstro", "criar_monstro", chave="fogo")
        mm.alimentar("texto", "fire burn monster", "criar_monstro", chave="fire")
        mm.alimentar("audio", audio_fogo, "criar_monstro", chave="som_fogo")
        mm.alimentar("imagem", img_fogo, "criar_monstro", chave="img_fogo")

        mm.alimentar("texto", "agua cura mago", "curar", chave="agua")
        mm.alimentar("texto", "water heal mage", "curar", chave="water")
        mm.alimentar("audio", audio_agua, "curar", chave="som_agua")
        mm.alimentar("imagem", img_agua, "curar", chave="img_agua")

    T('alimentou 8 conceitos', len(mm._conceitos) == 8,
      f'total={len(mm._conceitos)}')
    T('3 modalidades ativas', len(mm._modalidades) == 3,
      f'mods={mm._modalidades}')
    T('coupling tem observacoes', mm.coupling._total >= 8)

    print('\n[5] Cross-modal NMI — acoes compartilhadas convergem')
    # fogo (texto) e som_fogo (audio) compartilham acao criar_monstro
    nmi_fogo_somfogo = mm.similaridade_crossmodal("fogo", "som_fogo")
    nmi_fogo_somagua = mm.similaridade_crossmodal("fogo", "som_agua")
    print(f'    NMI(fogo, som_fogo) = {nmi_fogo_somfogo:.4f}')
    print(f'    NMI(fogo, som_agua) = {nmi_fogo_somagua:.4f}')
    T('NMI fogo-som_fogo > 0', nmi_fogo_somfogo > 0,
      f'nmi={nmi_fogo_somfogo:.4f}')
    T('NMI fogo-som_fogo > fogo-som_agua',
      nmi_fogo_somfogo > nmi_fogo_somagua,
      f'{nmi_fogo_somfogo:.4f} vs {nmi_fogo_somagua:.4f}')

    # imagem tambem
    nmi_fogo_imgfogo = mm.similaridade_crossmodal("fogo", "img_fogo")
    nmi_fogo_imgagua = mm.similaridade_crossmodal("fogo", "img_agua")
    print(f'    NMI(fogo, img_fogo) = {nmi_fogo_imgfogo:.4f}')
    print(f'    NMI(fogo, img_agua) = {nmi_fogo_imgagua:.4f}')
    T('NMI fogo-img_fogo > fogo-img_agua',
      nmi_fogo_imgfogo > nmi_fogo_imgagua,
      f'{nmi_fogo_imgfogo:.4f} vs {nmi_fogo_imgagua:.4f}')

    print('\n[6] Traducao cross-modal — audio -> texto')
    traduzido = mm.traduzir("audio", audio_fogo, "texto")
    print(f'    traduzir(audio_fogo) -> "{traduzido}"')
    T('traduziu audio para texto', traduzido is not None)
    T('tradutor acertou "fogo" ou "fire"',
      traduzido in ("fogo", "fire"),
      f'traduzido="{traduzido}"')

    traduzido_agua = mm.traduzir("audio", audio_agua, "texto")
    print(f'    traduzir(audio_agua) -> "{traduzido_agua}"')
    T('tradutor acertou "agua" ou "water"',
      traduzido_agua in ("agua", "water"),
      f'traduzido="{traduzido_agua}"')

    print('\n[7] Traducao cross-modal — imagem -> texto')
    trad_img = mm.traduzir("imagem", img_fogo, "texto")
    print(f'    traduzir(img_fogo) -> "{trad_img}"')
    T('traduziu imagem para texto', trad_img is not None)
    T('tradutor imagem acertou "fogo" ou "fire"',
      trad_img in ("fogo", "fire"),
      f'traduzido="{trad_img}"')

    trad_img_agua = mm.traduzir("imagem", img_agua, "texto")
    print(f'    traduzir(img_agua) -> "{trad_img_agua}"')
    T('tradutor imagem acertou "agua" ou "water"',
      trad_img_agua in ("agua", "water"),
      f'traduzido="{trad_img_agua}"')

    print('\n[8] Recuperacao cross-modal — top-N resultados')
    resultados = mm.recuperar_crossmodal("audio", audio_fogo, "texto", top_n=3)
    print(f'    recuperar(audio_fogo, texto) -> {resultados}')
    T('recuperacao retornou resultados', len(resultados) > 0)
    T('top resultado e fogo ou fire',
      resultados and resultados[0][0] in ("fogo", "fire"),
      f'top={resultados[0] if resultados else None}')

    print('\n[9] Predicao de acao cross-modal')
    acao, conf = mm.predizer_acao("audio", audio_fogo)
    print(f'    predizer_acao(audio_fogo) -> acao={acao}, conf={conf:.3f}')
    T('predicao retornou acao', acao is not None)
    T('predicao audio_fogo = criar_monstro', acao == "criar_monstro",
      f'acao={acao}')

    acao2, conf2 = mm.predizer_acao("imagem", img_agua)
    print(f'    predizer_acao(img_agua) -> acao={acao2}, conf={conf2:.3f}')
    T('predicao img_agua = curar', acao2 == "curar",
      f'acao={acao2}')

    acao3, conf3 = mm.predizer_acao("texto", "fogo queima")
    print(f'    predizer_acao(texto_fogo) -> acao={acao3}, conf={conf3:.3f}')
    T('predicao texto_fogo = criar_monstro', acao3 == "criar_monstro",
      f'acao={acao3}')

    print('\n[10] Equacao 5D — avaliacao de match cross-modal')
    nota_correct = mm.avaliar_crossmodal("texto", "fogo", "audio", audio_fogo)
    nota_wrong = mm.avaliar_crossmodal("texto", "fogo", "audio", audio_agua)
    print(f'    5D(fogo, som_fogo) = {nota_correct:.4f}')
    print(f'    5D(fogo, som_agua) = {nota_wrong:.4f}')
    T('5D match correto > 0', nota_correct > 0)
    T('5D match correto > match errado',
      nota_correct > nota_wrong,
      f'{nota_correct:.4f} vs {nota_wrong:.4f}')

    print('\n[11] Cross-modal sem dicionario — PT <-> EN')
    nmi_fogo_fire = mm.similaridade_crossmodal("fogo", "fire")
    nmi_fogo_water = mm.similaridade_crossmodal("fogo", "water")
    print(f'    NMI(fogo, fire) = {nmi_fogo_fire:.4f}')
    print(f'    NMI(fogo, water) = {nmi_fogo_water:.4f}')
    T('NMI fogo-fire > fogo-water (traducao sem dicionario)',
      nmi_fogo_fire > nmi_fogo_water,
      f'{nmi_fogo_fire:.4f} vs {nmi_fogo_water:.4f}')

    nmi_agua_water = mm.similaridade_crossmodal("agua", "water")
    nmi_agua_fire = mm.similaridade_crossmodal("agua", "fire")
    print(f'    NMI(agua, water) = {nmi_agua_water:.4f}')
    print(f'    NMI(agua, fire) = {nmi_agua_fire:.4f}')
    T('NMI agua-water > agua-fire',
      nmi_agua_water > nmi_agua_fire,
      f'{nmi_agua_water:.4f} vs {nmi_agua_fire:.4f}')

    print('\n[12] Robustez — audio similar ao mesmo conceito')
    mm.alimentar("audio", audio_fogo_2, "criar_monstro", chave="som_fogo_2")
    nmi_fogo_somfogo2 = mm.similaridade_crossmodal("fogo", "som_fogo_2")
    print(f'    NMI(fogo, som_fogo_2) = {nmi_fogo_somfogo2:.4f}')
    T('segundo audio de fogo tambem converge',
      nmi_fogo_somfogo2 > 0,
      f'nmi={nmi_fogo_somfogo2:.4f}')

    print('\n[13] Nova modalidade desconhecida — generico')
    dados_genericos = os.urandom(512)
    mm.alimentar("sensor", dados_genericos, "monitorar", chave="sensor_1")
    T('modalidade desconhecida aceita', "sensor" in mm._modalidades)
    feat_gen = mm._extrair_features_modal("sensor", dados_genericos)
    T('features genericas extraidas', 'gn' in feat_gen)

    print('\n[14] Estatisticas')
    stats = mm.estatisticas()
    print(f'    {stats}')
    T('estatisticas tem conceitos', stats['conceitos'] > 0)
    T('estatisticas tem modalidades', len(stats['modalidades']) > 0)

    print('\n[15] Nao regressao — FASE 1-5 ainda funcionam')
    c = MCRCoupling()
    c.alimentar("criar monstro dragao", "criar_monstro")
    c.alimentar("gerar monstro orc", "criar_monstro")
    c.alimentar("analisar codigo fonte", "analisar")
    c.alimentar("examinar texto log", "analisar")

    # FASE 1
    sig_frase = c._assinatura_frase("monstro verde")
    T('FASE 1 assinatura_frase funciona', len(sig_frase) > 0)

    # FASE 2
    rel = c.extrair_relacoes("criar")
    T('FASE 2 extrair_relacoes funciona', bool(rel))

    # FASE 3
    c.alimentar_estado("fogo", {"temp": 200, "dano": 5})
    estado_fogo = c.predizer_estado("fogo")
    T('FASE 3 predizer_estado funciona', "temp" in estado_fogo)

    # FASE 4
    from mcr.grounding_ambiental import GroundingAmbiental
    g = GroundingAmbiental(intervalo=0.5)
    g.iniciar()
    import time
    time.sleep(0.8)
    est = g.estado()
    T('FASE 4 grounding ambiental funciona', len(est) > 0)
    g.parar()

    # FASE 5
    from mcr.acoplamento_hierarquico import MCRHierarquico
    h = MCRHierarquico(max_niveis=5)
    for _ in range(5):
        h.alimentar("criar monstro dragao", "criar_monstro")
        h.alimentar("curar mago ferido", "curar")
    acao_h, _ = h.predizer("curar mago ferido")
    T('FASE 5 acoplamento hierarquico funciona', acao_h == "curar",
      f'acao={acao_h}')

    print('\n' + '=' * 72)
    print(f'  RESULTADO: {PASS} PASS / {FAIL} FAIL')
    print('=' * 72)
    return FAIL == 0


if __name__ == '__main__':
    ok = main()
    sys.exit(0 if ok else 1)
