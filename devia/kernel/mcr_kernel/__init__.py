#!/usr/bin/env python3
"""mcr_kernel — Motor Cognitivo Universal (MCR-DevIA).

Dividido em 10 módulos para manutenção sem alterar a matemática.
Re-exporta TODAS as classes públicas para compatibilidade com código legado.
"""
# engine — Núcleo Markov (zero dependências do pacote)
from .engine import MCR, MCRBridge, MarkovUniversal

# signature — Fingerprints e assinaturas
from .signature import MCRFingerprint, MCRSignature

# decisor — Decisão, entropia, thresholds
from .decisor import (
    MCRPeso, MCREntropia, MCRRuido, MCRDecisor, MCRDiagnostico,
    MCRPesoNota, MCRThreshold,
    _MCR_THRESHOLD_FILTRO, _MCR_THRESHOLD_CONF, _MCR_THRESHOLD_TAMANHO,
    _MCR_THRESHOLD_REPETICAO, _MCR_THRESHOLD_PALAVRA,
    _MCR_THRESHOLD_CONEXAO, _MCR_THRESHOLD_NOTA,
)

# memory — KG, conectores, cadeias, buffer
from .memory import (
    MCRBufferKG, MCRConector, MCRCruzado, MCRCadeia, MCRKGAuto,
    CONECTORES, _get_kg, _get_mk_qualidade, _registrar_consumo_global, _buscar_kg_task,
)

# persistence — Documentos, fragmentação, persistência
from .persistence import (
    MCRDocIndex, _get_doc_index, MCRDocIndex as MCRDocIndex,
    MCRFragmento, MCRFragmentador, MCRSegmentador, MCRPersistencia,
)

# meta — Metacognição
from .meta import (
    MCRMeta, MCRNivel, MCRMetaNivel, MCRMetaGap,
    MCRSelfIndex, MCRSelfHeal, _NIVEIS_BASE,
)

# evolution — Spawner, expansão, fuel, melhoria
from .evolution import (
    MCRTarefa, MCRWorker, MCRSpawner, MCRExpansao, MCRFuel, MCRAutoMelhoria,
    _executar_lote,
)

# feedback — Assinatura, sessão, web learn, feedback loop
from .feedback import (
    MCRFeedback, MCRAssinatura, MCRSession, MCRWebLearn,
)

# system — Orquestração, perguntas, geração
from .system import (
    MCRSystem, MCRPergunta, MCRMestre, MCRMestreV2, MCRGeracao,
    AutoavaliadorSemantico, GeradorNarrativa, termo_relevante,
)

# state — Estado global, boot, auto-start
from .state import (
    _MCR_STATE, _MCR_DATA, MCRBoot, MCRAutoStart, _MCR_SELF_CHECK,
)

# MCR autossuficiente — não depende de módulos externos.
MCR_COMPLETO = True


def _autotestar():
    '''MCR testa a si mesmo — nomes gerados dos resultados reais.'''
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    resultados = []
    def testar(nome, cond):
        status = 'PASS' if cond else 'FAIL'
        resultados.append((nome, cond))
        print(f'  [{status}] {nome}')
        sys.stdout.flush()
    print('=' * 70)
    print('  MCR - Auto Teste')
    print('=' * 70)
    
    # Warmup
    try:
        from modulos.kg import KnowledgeGraph
        kg_warm = KnowledgeGraph()
        l_warm = kg_warm._get_licoes()
        if len(l_warm) > 200:
            from .memory import MCRKGAuto
            auto_warm = MCRKGAuto(kg_warm)
            n_dedup = auto_warm.dedup()
            if n_dedup > 0:
                kg_warm.salvar()
    except Exception:
        pass
    
    # 1. MCR base
    mk = MCR('autoteste')
    mk.aprender_sequencia([1, 2, 3])
    testar(f'MCR.aprender_sequencia([1,2,3]) total={mk.total}', mk.total > 0)
    p1, c1 = mk.predizer(1)
    testar(f'MCR.predizer(1) = ({p1}, {c1:.2f})', p1 is not None)
    h1 = mk.entropia(1)
    testar(f'MCR.entropia(1) = {h1:.2f}', h1 >= 0)
    j1 = mk.jaccard_bytes('SPA', 'SPA')
    testar(f'MCR.jaccard_bytes(SPA,SPA) = {j1:.3f}', j1 > 0.99)
    j2 = mk.jaccard_bytes_ponderado('SPA A', 'SPA B')
    testar(f'MCR.jaccard_ponderado(SPA) = {j2:.3f}', j2 > 0)
    
    # 2. MCRConector
    c2 = MCRConector()
    c2.alimentar('SPA = Sistema.', 'spa')
    c2.alimentar('Eridanus era cidade.', 'eridanus')
    cx = c2.conectar('spa', 'eridanus')
    if cx:
        testar(f'MCRConector.conectar nota={cx["nota"]:.1f}', cx['nota'] > 0)
    else:
        testar('MCRConector.conectar = None', False)
    
    # 3. MCRCadeia
    cadeia = MCRCadeia(c2)
    res_c = cadeia.gerar('SPA', n_tokens=10)
    testar(f'MCRCadeia.gerar tokens={res_c["n_tokens"]}', res_c['n_tokens'] >= 3)
    
    # 4. MCRPeso
    peso = MCRPeso('t')
    peso.aprender('erro', 5.0)
    peso.aprender('ctx', 4.0)
    peso.aprender('causa', 3.0)
    testar(f'MCRPeso erro={peso.consultar("erro")} ctx={peso.consultar("ctx")} causa={peso.consultar("causa")}',
           peso.consultar('erro') >= peso.consultar('ctx') >= peso.consultar('causa'))
    
    # 5. MCREntropia
    ent = MCREntropia('t')
    for _ in range(10): ent.alimentar('X')
    testar(f'MCREntropia.loop({ent.esta_em_loop()})', ent.esta_em_loop())
    
    # 6. MCRDecisor
    dec = MCRDecisor('t')
    d = dec.decidir('Explique SPA')
    testar(f'MCRDecisor.decidir = {d}', d is not None)
    
    # 7. MCRBridge
    bridge = MCRBridge()
    disc = bridge.descobrir()
    testar(f'MCRBridge modulos={disc["modulos"]} comandos={disc["comandos"]}',
           disc['modulos'] >= 0 and disc['comandos'] >= 0)
    
    # 8. MCRMestre
    mestre = MCRMestre(bridge)
    res_m = mestre.processar('Explique SPA')
    if res_m:
        testar(f'MCRMestre resposta={len(res_m.get("resposta",""))} chars',
               len(res_m.get('resposta','')) > 0)
    
    # 9. MCRPesoNota
    pn = MCRPesoNota('t')
    pn.aprender({'byte': 0.8, 'palavra': 0.2}, 3.0)
    pn.aprender({'byte': 0.4, 'palavra': 0.8}, 8.0)
    nb = pn.calcular(byte_s=8.0, palavra_s=2.0)
    na = pn.calcular(byte_s=4.0, palavra_s=8.0)
    testar(f'MCRPesoNota JSON={nb:.1f} Texto={na:.1f}', nb < na)
    
    # 10. MCRThreshold
    th = MCRThreshold('t')
    for v in [0.8, 0.85, 0.9, 0.82, 0.88]:
        th.observar(v)
    tc = th.calcular()
    testar(f'MCRThreshold mediana={tc:.2f}', 0.8 < tc < 0.9)
    th2 = MCRThreshold('t2')
    for _ in range(10): th2.observar(0.1)
    tc2 = th2.calcular(0.5)
    testar(f'MCRThreshold loop={tc2:.3f}', tc2 < 0.2)
    
    # 11. MCRMestreV2
    m_v2 = MCRMestreV2(bridge)
    r_v2 = m_v2.processar('Explique SPA')
    testar(f'MCRMestreV2 fluxo={r_v2.get("fluxo","?")}', r_v2.get('fluxo','') != '')
    testar(f'MCRMestreV2 exec={m_v2.n_execucoes}', m_v2.n_execucoes > 0)
    
    # 12. CicloUnico
    try:
        m_sys = MCRSystem()
        ciclo = m_sys.ciclo_unico(__file__, 2000)
        testar(f'CicloUnico tipo={ciclo.get("tipo","?")} ent={ciclo.get("entropia",0):.2f}',
               ciclo.get('entropia', 0) > 0)
    except Exception as e:
        testar(f'CicloUnico erro={e}', False)
    
    # 13. ProcessarBytes
    try:
        m_b = MCR('pb')
        r_b = m_b.processar_bytes('Explique SPA'.encode())
        testar(f'ProcessarBytes compat={r_b["compatibilidade"]:.2f}', r_b['compatibilidade'] > 0)
    except Exception as e:
        testar(f'ProcessarBytes erro={e}', False)
    
    # 14. MCRDiagnostico
    diag = MCRDiagnostico('t')
    diag.alimentar({'byte': 0.9, 'palavra': 0.1}, 'JSON_no_texto')
    diag.alimentar({'byte': 0.8, 'palavra': 0.15}, 'JSON_no_texto')
    d_j = diag.diagnosticar({'byte': 0.85, 'palavra': 0.12})
    diag.alimentar({'byte': 0.2, 'token': 0.9}, 'loop_detectado')
    d_l = diag.diagnosticar({'byte': 0.18, 'token': 0.88})
    testar(f'MCRDiagnostico JSON={d_j} Loop={d_l}', 'JSON' in d_j and 'loop' in d_l)
    
    # 15. Fuel + MetaGap
    fuel = MCRFuel(kg=None, bridge=bridge)
    testar(f'MCRFuel type={type(fuel).__name__}', isinstance(fuel, MCRFuel))
    mg = MCRMetaGap(kg=None, bridge=bridge)
    testar(f'MCRMetaGap type={type(mg).__name__}', isinstance(mg, MCRMetaGap))
    
    # 16. AutoMelhoria
    am = MCRAutoMelhoria(kg=None, bridge=bridge)
    am_c = am.ciclo()
    testar(f'MCRAutoMelhoria acoes={am_c["n"]}', am_c['n'] >= 0)
    
    # 17. Filosofia
    f = MCRFilosofia()
    n_f = f.aprender_perguntas_fundamentais()
    testar(f'MCRFilosofia {n_f} perguntas', n_f == len(_PERgUNTAS_FUNDAMENTAIS))
    ref = f.refletir('Quem sou eu?')
    testar(f'MCRFilosofia reflexao {len(ref)} chars', len(ref) > 10)
    
    # 18. MetaNivel
    meta = MCRMetaNivel()
    meta.alimentar('Explique o sistema SPA do MCR'.encode())
    d_m = meta.diagnosticar()
    testar(f'MCRMetaNivel niveis={d_m["n_niveis"]} ordem={d_m.get("ordem",[])}',
           d_m['n_niveis'] >= 2)
    
    # 19. Feedback
    try:
        fb = MCRFeedback(m_v2)
        r_fb = fb.processar_com_feedback('Explique SPA', 2)
        testar(f'MCRFeedback tentativas={r_fb.get("feedback",{}).get("tentativas",0)}',
               r_fb.get('feedback',{}).get('tentativas', 0) >= 1)
    except Exception as e:
        testar(f'MCRFeedback erro={e}', False)
    
    # 20. SelfHeal
    try:
        sh = MCRSelfHeal.verificar()
        testar(f'MCRSelfHeal acoes={sh["n_acoes"]}', sh['n_acoes'] >= 0)
    except Exception as e:
        testar(f'MCRSelfHeal erro={e}', False)
    
    # 21. MCRSignature
    sig_a = MCRSignature.extrair('Explique o sistema SPA do MCR')
    sig_b = MCRSignature.extrair('Crie um NPC ferreiro em Eridanus')
    sig_sim = MCRSignature.extrair('Explique o sistema SPA do MCR')
    comp_ab = MCRSignature.comparar(sig_a, sig_b)
    comp_aa = MCRSignature.comparar(sig_a, sig_sim)
    testar(f'MCRSignature.extrair ent={sig_a["entropia"]} est={sig_a["estados"]} trans={sig_a["transicoes"]}',
           sig_a['estados'] > 0)
    testar(f'MCRSignature.comparar diferentes={comp_ab:.3f} iguais={comp_aa:.3f}',
           comp_aa > comp_ab)
    
    # 22. MCRSession
    sess = MCRSession()
    sess.registrar("teste", "resposta_teste", "autoteste")
    st = sess.salvar_estado()
    testar(f'MCRSession salvar={st}', st)
    sess2 = MCRSession()
    car = sess2.carregar_estado()
    testar(f'MCRSession carregar={car is not None}', car is not None)
    
    # 23. MCRAssinatura
    banco = MCRAssinatura()
    banco.aprender("Eu criei o MCR", "Kheltz", rapido=True)
    autor = banco.identificar("Eu criei o MCR-DevIA")
    testar(f'MCRAssinatura autor={autor[0]}', autor[0] in ('Kheltz', 'Kheltz?'))
    
    # 24. AutoStart
    try:
        a = MCRAutoStart.iniciar()
        testar(f'MCRAutoStart status={a.get("aproveitamento","?")}',
               isinstance(a, dict) and 'erro' not in a)
    except Exception as e:
        testar(f'MCRAutoStart erro={e}', False)
    
    print('=' * 70)
    n_pass = sum(1 for _, c in resultados if c)
    n_fail = sum(1 for _, c in resultados if not c)
    print(f'  Resultado: {n_pass}/{len(resultados)} pass, {n_fail} fail')
    print('=' * 70)
    return resultados
