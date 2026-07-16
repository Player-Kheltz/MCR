"""test_fase4_grounding_ambiental.py — Teste da FASE 4: Grounding Ambiental.

Valida GroundingAmbiental: thread background com sensores do PC que
alimentam o MCRCoupling com contexto ambiental.

Criterios do plano (docs/PLANO_EVOLUCAO_MCR.md):
  4.1 Arquitetura assincrona (sem pesar performance)
  4.2 Sensores: relogio, carga, janela, clipboard
  4.3 Thread background 1Hz, loop MCR 3ms inalterado
  4.4 Integracao com FASE 3 (grounding simbolico)

Pilar 1: P(acao | texto + estado_ambiental) — transicao
Pilar 2: entropia descobre padroes temporais
Pilar 3: sensores sao dict generérico
Pilar 5: loop fechado — sensor -> coupling -> decide
"""
import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcr.coupling import MCRCoupling
from mcr.grounding_ambiental import GroundingAmbiental

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
    print('  FASE 4 — TESTE DE GROUNDING AMBIENTAL')
    print('  Plano de Evolucao MCR v2.2')
    print('=' * 72)

    print('\n[1] GroundingAmbiental — instanciacao e sensores')
    g = GroundingAmbiental(intervalo=0.5)
    T('instanciou', g is not None)
    T('4 sensores ativos', len(g._sensores_ativos) == 4,
      f'sensores={list(g._sensores_ativos.keys())}')

    print('\n[2] Thread background — estado atualizado apos iniciar()')
    g.iniciar()
    time.sleep(1.5)
    estado = g.estado()
    print(f'    estado: {estado}')
    T('estado nao vazio apos thread', len(estado) > 0)
    T('tem hora', "hora" in estado, f'keys={list(estado.keys())}')
    T('tem periodo', "periodo" in estado)
    T('tem cpu', "cpu" in estado)
    T('tem janela', "janela" in estado)
    T('tem dia_semana', "dia_semana" in estado)

    print('\n[3] Sensores individuais — relogio')
    relogio = g._sensor_relogio()
    print(f'    relogio: {relogio}')
    T('relogio tem hora', "hora" in relogio)
    T('relogio tem periodo', "periodo" in relogio)
    T('relogio tem dia_semana', "dia_semana" in relogio)
    periodos_validos = {"manha", "tarde", "noite", "madrugada"}
    T('periodo valido', relogio["periodo"] in periodos_validos,
      f'periodo={relogio["periodo"]}')

    print('\n[4] Sensores individuais — carga (psutil)')
    carga = g._sensor_carga()
    print(f'    carga: {carga}')
    T('carga tem cpu', "cpu" in carga)
    T('carga tem ram_pct', "ram_pct" in carga)
    T('cpu >= 0', carga.get("cpu", -1) >= 0)
    T('ram_pct >= 0', carga.get("ram_pct", -1) >= 0)

    print('\n[5] Sensores individuais — janela ativa')
    janela = g._sensor_janela()
    print(f'    janela: {janela}')
    T('janela tem titulo', "janela" in janela)
    T('janela tem dominio', "dominio" in janela)
    dominios_validos = {"codigo", "jogo", "navegador", "terminal",
                        "comunicacao", "outro"}
    T('dominio valido', janela["dominio"] in dominios_validos,
      f'dominio={janela["dominio"]}')

    print('\n[6] _formatar_contexto — string de contexto ambiental')
    estado_teste = {"periodo": "manha", "dominio": "terminal", "dia_semana": "qui"}
    ctx = GroundingAmbiental._formatar_contexto(estado_teste)
    print(f'    contexto: "{ctx}"')
    T('contexto nao vazio', bool(ctx))
    T('contexto tem periodo', "manha" in ctx)
    T('contexto tem dominio', "terminal" in ctx)
    T('contexto formato [a|b|c]', ctx.startswith("[") and ctx.endswith("]"))

    print('\n[7] Integracao com MCRCoupling — alimentar_coupling()')
    g.parar()
    c = MCRCoupling()

    # Simular contexto matutino no terminal
    g2 = GroundingAmbiental(intervalo=0.5)
    g2.iniciar()
    time.sleep(1.0)

    # Alimentar com contexto ambiental
    g2.alimentar_coupling(c, "criar monstro dragao", "criar_monstro")
    g2.alimentar_coupling(c, "gerar npc orc", "gerar_npc")

    T('alimentar_coupling executou', c._total >= 2)
    print(f'    coupling total: {c._total}')

    print('\n[8] decidir_com_contexto() — decisao com contexto ambiental')
    acao, conf = g2.decidir_com_contexto(c, "criar monstro orc", None)
    print(f'    decidir("criar monstro orc") -> acao={acao}, conf={conf:.3f}')
    T('decisao retornou acao', acao is not None)
    T('decisao retornou confianca', 0.0 <= conf <= 1.0)

    print('\n[9] Performance — estado() e O(1)')
    t0 = time.time()
    for _ in range(10000):
        g2.estado()
    dt = (time.time() - t0) * 1000
    print(f'    10000 chamadas estado() em {dt:.1f}ms ({dt/10:.3f}ms/call)')
    T('estado() < 1ms por chamada (O(1))', dt / 10 < 1.0,
      f'{dt/10:.3f}ms/call')

    g2.parar()

    print('\n[10] Nao regressao — FASE 1, 2, 3 ainda funcionam')
    c2 = MCRCoupling()
    c2.alimentar("criar monstro dragao", "criar_monstro")
    c2.alimentar("gerar monstro orc", "criar_monstro")
    c2.alimentar("analisar codigo fonte", "analisar")
    c2.alimentar("examinar texto log", "analisar")

    # FASE 1
    sig_frase = c2._assinatura_frase("monstro verde")
    T('FASE 1 assinatura_frase funciona', len(sig_frase) > 0)

    # FASE 2
    rel = c2.extrair_relacoes("criar")
    T('FASE 2 extrair_relacoes funciona', bool(rel))

    # FASE 3
    c2.alimentar_estado("fogo", {"temp": 200, "dano": 5})
    estado_fogo = c2.predizer_estado("fogo")
    T('FASE 3 predizer_estado funciona', "temp" in estado_fogo)

    print('\n[11] Fallback gracioso — sensor inexistente')
    g3 = GroundingAmbiental(sensores=["relogio", "sensor_inexistente"])
    T('sensor inexistente ignorado', "sensor_inexistente" not in g3._sensores_ativos)
    T('relogio mantido', "relogio" in g3._sensores_ativos)

    print('\n[12] Thread para e limpa')
    g3.iniciar()
    time.sleep(0.5)
    g3.parar()
    T('thread parou', not g3._rodando)

    print('\n' + '=' * 72)
    print(f'  RESULTADO: {PASS} PASS / {FAIL} FAIL')
    print('=' * 72)
    return FAIL == 0


if __name__ == '__main__':
    ok = main()
    sys.exit(0 if ok else 1)
