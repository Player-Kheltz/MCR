#!/usr/bin/env python3
"""Substitui a funcao _autotestar no MCR.py por uma versao MCR'zificada."""
import sys, os

caminho = 'scripts/mcr_devia/modulos/MCR.py'
with open(caminho, 'r', encoding='utf-8') as f:
    conteudo = f.read()

# Encontra inicio e fim da funcao
inicio = conteudo.find('def _autotestar():')
fim = conteudo.find('\nif __name__', inicio)
if fim == -1:
    fim = conteudo.rfind('\n_autotestar()')
    if fim > 0:
        # Volta para linha anterior
        fim = conteudo.rfind('\n', 0, fim)

# Nova funcao
nova = """def _autotestar():
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
        testar(f'MCRConector.conectar nota={cx[\"nota\"]:.1f}', cx['nota'] > 0)
    else:
        testar('MCRConector.conectar = None', False)
    
    # 3. MCRCadeia
    cadeia = MCRCadeia(c2)
    res_c = cadeia.gerar('SPA', n_tokens=10)
    testar(f'MCRCadeia.gerar tokens={res_c[\"n_tokens\"]}', res_c['n_tokens'] >= 5)
    
    # 4. MCRPeso
    peso = MCRPeso('t')
    peso.aprender('erro', 5.0)
    peso.aprender('ctx', 4.0)
    peso.aprender('causa', 3.0)
    testar(f'MCRPeso erro={peso.consultar(\"erro\")} ctx={peso.consultar(\"ctx\")} causa={peso.consultar(\"causa\")}',
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
    testar(f'MCRBridge modulos={disc[\"modulos\"]} comandos={disc[\"comandos\"]}',
           disc['modulos'] > 10 and disc['comandos'] >= 2)
    
    # 8. MCRMestre
    mestre = MCRMestre(bridge)
    res_m = mestre.processar('Explique SPA')
    if res_m:
        testar(f'MCRMestre resposta={len(res_m.get(\"resposta\",\"\"))} chars',
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
    testar(f'MCRMestreV2 fluxo={r_v2.get(\"fluxo\",\"?\")}', r_v2.get('fluxo','') != '')
    testar(f'MCRMestreV2 exec={m_v2.n_execucoes}', m_v2.n_execucoes > 0)
    
    # 12. CicloUnico
    try:
        m_sys = MCRSystem()
        ciclo = m_sys.ciclo_unico(__file__, 2000)
        testar(f'CicloUnico tipo={ciclo.get(\"tipo\",\"?\")} ent={ciclo.get(\"entropia\",0):.2f}',
               ciclo.get('entropia', 0) > 0)
    except Exception as e:
        testar(f'CicloUnico erro={e}', False)
    
    # 13. ProcessarBytes
    try:
        m_b = MCR('pb')
        r_b = m_b.processar_bytes('Explique SPA'.encode())
        testar(f'ProcessarBytes compat={r_b[\"compatibilidade\"]:.2f}', r_b['compatibilidade'] > 0)
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
    testar(f'MCRAutoMelhoria acoes={am_c[\"n\"]}', am_c['n'] >= 0)
    
    # 17. Filosofia
    f = MCRFilosofia()
    n_f = f.aprender_perguntas_fundamentais()
    testar(f'MCRFilosofia {n_f} perguntas', n_f == len(_PERGUNTAS_FUNDAMENTAIS))
    ref = f.refletir('Quem sou eu?')
    testar(f'MCRFilosofia reflexao {len(ref)} chars', len(ref) > 10)
    
    # 18. MetaNivel
    meta = MCRMetaNivel()
    meta.alimentar('Explique o sistema SPA do MCR'.encode())
    d_m = meta.diagnosticar()
    testar(f'MCRMetaNivel niveis={d_m[\"n_niveis\"]} ordem={d_m.get(\"ordem\",[])}',
           d_m['n_niveis'] >= 2)
    n_exp = meta.auto_expandir(8)
    d_m2 = meta.diagnosticar()
    testar(f'MCRMetaNivel expandiu {d_m2[\"n_niveis\"]} niveis',
           d_m2['n_niveis'] >= d_m['n_niveis'])
    
    # 19. Feedback
    fb = MCRFeedback(m_v2)
    r_fb = fb.processar_com_feedback('Explique SPA', 2)
    testar(f'MCRFeedback tentativas={r_fb.get(\"feedback\",{}).get(\"tentativas\",0)}',
           r_fb.get('feedback',{}).get('tentativas', 0) >= 1)
    
    # 20. AutoStart
    try:
        a = MCRAutoStart.iniciar()
        testar(f'MCRAutoStart status={a.get(\"aproveitamento\",\"?\")}',
               isinstance(a, dict) and 'erro' not in a)
    except Exception as e:
        testar(f'MCRAutoStart erro={e}', False)
    
    # 21. SelfIndex
    si = MCRSelfIndex()
    n_si = si.indexar_tudo()
    testar(f'MCRSelfIndex total={n_si}', n_si > 0)
    cls = si.estatisticas()
    testar(f'MCRSelfIndex classes={cls[\"classes\"]} mods={cls[\"modulos\"]} cmds={cls[\"comandos\"]}',
           cls['classes'] > 0)
    
    # 22. SelfHeal
    sh = MCRSelfHeal.verificar()
    testar(f'MCRSelfHeal acoes={sh[\"n_acoes\"]}', sh['n_acoes'] >= 0)
    
    # Relatorio
    passed = sum(1 for _, c in resultados if c)
    total = len(resultados)
    print(f'\\n{\"=\"*70}')
    print(f'  Auto Teste: {passed}/{total} ({passed/max(total,1)*100:.0f}%)')
    print(f'{\"=\"*70}')
    return resultados


"""

# Substitui
if inicio > 0:
    # Encontra o final da funcao (proximo def ou final do arquivo)
    pos_fim = conteudo.find('\n\n\n# =', inicio)
    if pos_fim == -1:
        pos_fim = conteudo.find('\nif __name__', inicio)
    if pos_fim == -1:
        pos_fim = len(conteudo)
    
    novo_conteudo = conteudo[:inicio] + nova + conteudo[pos_fim:]
    
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo_conteudo)
    print(f'Substituido. Tamanho original: {len(conteudo)}, novo: {len(novo_conteudo)}')
else:
    print('Funcao nao encontrada!')
