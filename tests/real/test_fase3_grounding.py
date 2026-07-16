"""test_fase3_grounding.py — Teste da FASE 3: Grounding Simbolico.

Valida alimentar_estado(), predizer_estado(), consultar_atributo() e
raciocinar_estado() — tudo por Markov + Entropia, zero rotulos.

Criterios do plano (docs/PLANO_EVOLUCAO_MCR.md):
  3.1 Alimentar com pares (texto, estado_do_mundo)
  3.2 Raciocinio sobre estados (fogo + gelo -> temperatura)
  3.3 Grounding via Tibia (estado aninhado: ator, acao, elemento, dano)

Pilar 1: P(state_feature | word) — tudo transicao
Pilar 2: entropia decide, sem threshold
Pilar 5: alimenta -> predizer -> aprende (loop)
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
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
    print('  FASE 3 — TESTE DE GROUNDING SIMBOLICO')
    print('  Plano de Evolucao MCR v2.2')
    print('=' * 72)

    c = MCRCoupling()

    # === 3.1 Alimentar com pares (texto, estado) ===
    print('\n[1] alimentar_estado() — pares (texto, estado_do_mundo)')

    c.alimentar_estado("fogo", {"temp": 200, "dano": 5, "cor": "vermelho"})
    c.alimentar_estado("gelo", {"temp": -5, "dano": 0, "cor": "branco"})
    c.alimentar_estado("espada", {"dano": 50, "cor": "prata", "peso": 3})
    c.alimentar_estado("escudo", {"defesa": 30, "cor": "azul", "peso": 5})
    c.alimentar_estado("cura", {"cura": 100, "mana": -10, "cor": "verde"})

    # Tibia-like (estado aninhado)
    c.alimentar_estado("mago atacou fogo", {
        "ator": "mago", "acao": "atacar", "elemento": "fogo",
        "dano": 150, "mana": -30
    })
    c.alimentar_estado("guerreiro atacou espada", {
        "ator": "guerreiro", "acao": "atacar", "elemento": "fisico",
        "dano": 80, "mana": 0
    })

    # Verificar que _estado_features foi populado
    T('_estado_features populado', len(c._estado_features) > 0,
      f'len={len(c._estado_features)}')
    T('"fogo" tem features de estado', "fogo" in c._estado_features,
      f'keys={list(c._estado_features.keys())[:5]}')

    feats_fogo = c._estado_features.get("fogo", {})
    print(f'    features de "fogo": {dict(list(feats_fogo.items())[:6])}')
    T('"fogo" tem est_attr:temp', any("est_attr:temp" in k for k in feats_fogo),
      f'feats={list(feats_fogo.keys())[:6]}')
    T('"fogo" tem est_val:temp:200', "est_val:est:temp:200" in feats_fogo,
      f'feats={list(feats_fogo.keys())[:8]}')

    print('\n[2] predizer_estado() — prediz estado do mundo associado ao texto')

    estado_fogo = c.predizer_estado("fogo")
    print(f'    estado predito para "fogo": {estado_fogo}')
    T('predizer_estado("fogo") nao vazio', bool(estado_fogo))
    T('"fogo" tem temp no estado', "temp" in estado_fogo,
      f'estado={estado_fogo}')
    temp_fogo, conf_fogo = estado_fogo.get("temp", (None, 0))
    T('"fogo" temp = "200"', temp_fogo == "200",
      f'temp={temp_fogo} conf={conf_fogo:.3f}')

    estado_gelo = c.predizer_estado("gelo")
    print(f'    estado predito para "gelo": {estado_gelo}')
    temp_gelo, conf_gelo = estado_gelo.get("temp", (None, 0))
    T('"gelo" temp = "-5"', temp_gelo == "-5",
      f'temp={temp_gelo} conf={conf_gelo:.3f}')

    print('\n[3] consultar_atributo() — consulta atributo especifico')

    val, conf = c.consultar_atributo("fogo", "temp")
    print(f'    consultar_atributo("fogo", "temp") = ({val}, {conf:.3f})')
    T('consultar temp de "fogo" = "200"', val == "200", f'val={val}')

    val, conf = c.consultar_atributo("gelo", "cor")
    print(f'    consultar_atributo("gelo", "cor") = ({val}, {conf:.3f})')
    T('consultar cor de "gelo" = "branco"', val == "branco", f'val={val}')

    val, conf = c.consultar_atributo("espada", "dano")
    print(f'    consultar_atributo("espada", "dano") = ({val}, {conf:.3f})')
    T('consultar dano de "espada" = "50"', val == "50", f'val={val}')

    print('\n[4] raciocinar_estado() — fogo + gelo -> temperatura (conceito emergente)')

    resultado = c.raciocinar_estado("fogo", "gelo")
    print(f'    raciocinar_estado("fogo", "gelo") = {resultado}')
    T('fogo e gelo compartilham atributos',
      len(resultado.get("atributos_compartilhados", [])) > 0,
      f'resultado={resultado}')
    T('fogo e gelo compartilham "temp"',
      "temp" in resultado.get("atributos_compartilhados", []),
      f'attrs={resultado.get("atributos_compartilhados")}')
    T('fogo e gelo compartilham "cor"',
      "cor" in resultado.get("atributos_compartilhados", []),
      f'attrs={resultado.get("atributos_compartilhados")}')
    T('fogo e gelo compartilham "dano"',
      "dano" in resultado.get("atributos_compartilhados", []),
      f'attrs={resultado.get("atributos_compartilhados")}')
    T('NMI entre fogo e gelo > 0',
      resultado.get("nmi", 0) > 0,
      f'nmi={resultado.get("nmi")}')

    print('\n[5] raciocinar_estado() — fogo + espada -> dano, cor (parcial)')

    resultado2 = c.raciocinar_estado("fogo", "espada")
    print(f'    raciocinar_estado("fogo", "espada") = {resultado2}')
    T('fogo e espada compartilham "dano"',
      "dano" in resultado2.get("atributos_compartilhados", []),
      f'attrs={resultado2.get("atributos_compartilhados")}')
    T('fogo e espada compartilham "cor"',
      "cor" in resultado2.get("atributos_compartilhados", []),
      f'attrs={resultado2.get("atributos_compartilhados")}')
    T('fogo e espada NAO compartilham "temp"',
      "temp" not in resultado2.get("atributos_compartilhados", []),
      f'attrs={resultado2.get("atributos_compartilhados")}')

    print('\n[6] Grounding Tibia-like — estado aninhado (ator, acao, elemento)')

    estado_mago = c.predizer_estado("mago atacou fogo")
    print(f'    estado predito para "mago atacou fogo": {estado_mago}')
    T('estado aninhado: tem "ator"',
      "ator" in estado_mago, f'estado={estado_mago}')
    ator_val, _ = estado_mago.get("ator", (None, 0))
    T('ator = "mago"', ator_val == "mago", f'ator={ator_val}')
    T('estado aninhado: tem "elemento"',
      "elemento" in estado_mago, f'estado={estado_mago}')
    elem_val, _ = estado_mago.get("elemento", (None, 0))
    T('elemento = "fogo"', elem_val == "fogo", f'elem={elem_val}')
    T('estado aninhado: tem "dano"',
      "dano" in estado_mago, f'estado={estado_mago}')

    print('\n[7] Nao regressao — FASE 1 e 2 ainda funcionam')

    # FASE 1
    c.alimentar("criar monstro dragao", "criar_monstro")
    c.alimentar("gerar monstro orc", "criar_monstro")
    sig_frase = c._assinatura_frase("monstro verde")
    T('assinatura_frase (FASE 1) ainda funciona', len(sig_frase) > 0)

    # FASE 2
    c.alimentar("analisar codigo fonte", "analisar")
    c.alimentar("examinar texto log", "analisar")
    rel = c.extrair_relacoes("criar")
    T('extrair_relacoes (FASE 2) ainda funciona', bool(rel))

    print('\n[8] Pilar 1 — tudo e P(b|a) (transicao markoviana)')

    # Verificar que estado_features e uma matriz de transicao
    sig_est_fogo = c._assinatura_estado("fogo")
    T('_assinatura_estado("fogo") nao vazia', bool(sig_est_fogo),
      f'sig={sig_est_fogo}')
    T('sig_est tem features est_val:*',
      any(k.startswith("est_val:") for k in sig_est_fogo),
      f'keys={list(sig_est_fogo.keys())[:5]}')
    T('sig_est tem features est_attr:*',
      any(k.startswith("est_attr:") for k in sig_est_fogo),
      f'keys={list(sig_est_fogo.keys())[:5]}')

    print('\n[9] Persistencia — save/load com _estado_features')

    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as f:
        tmp_path = f.name

    c.save(tmp_path)
    c2 = MCRCoupling()
    loaded = c2.load(tmp_path)
    T('load() retornou True', loaded)
    T('_estado_features restaurado', len(c2._estado_features) > 0,
      f'len={len(c2._estado_features)}')
    estado_loaded = c2.predizer_estado("fogo")
    T('predizer_estado apos load funciona',
      "temp" in estado_loaded, f'estado={estado_loaded}')

    os.unlink(tmp_path)

    print('\n' + '=' * 72)
    print(f'  RESULTADO: {PASS} PASS / {FAIL} FAIL')
    print('=' * 72)
    return FAIL == 0


if __name__ == '__main__':
    ok = main()
    sys.exit(0 if ok else 1)
