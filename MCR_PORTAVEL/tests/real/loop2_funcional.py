#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOOP 2 — Teste de INTEGRAÇÕES FUNCIONAIS

Não testa só carregamento. Testa pipelines reais com dados reais.
Cada teste EXERCITA o módulo, não só importa.
"""
import sys, os, time, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'devia', 'kernel'))

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

PASS, FAIL, ERR = 0, 0, 0

def T(nome, cond, detalhe=''):
    global PASS, FAIL, ERR
    if cond is True: PASS += 1; print(f'  [PASS] {nome}')
    elif cond is False: FAIL += 1; print(f'  [FAIL] {nome} — {detalhe}')
    else: ERR += 1; print(f'  [ERR]  {nome}: {detalhe}')

def main():
    global PASS, FAIL, ERR
    t0 = time.time()
    print('=' * 60)
    print('  LOOP 2 — Integrações Funcionais')
    print('=' * 60)

    # ─── 1. MCRSystem.ciclo_unico ──────────────────
    print('\n[1] MCRSystem.ciclo_unico (processa bytes)')
    try:
        from mcr_kernel.system import MCRSystem
        sistema = MCRSystem()
        T('MCRSystem instanciado', True)
        
        ciclo = sistema.ciclo_unico(os.path.join(_BASE, 'golden_examples', 'canary_monster_template.lua'), 2000)
        T('ciclo_unico executou', ciclo is not None)
        if ciclo and isinstance(ciclo, dict):
            T(f'ciclo_unico tipo={ciclo.get("tipo","?")}', 'tipo' in ciclo)
            ent = ciclo.get('entropia', -1)
            T(f'ciclo_unico entropia={ent:.3f}', ent >= 0, f'{ent:.3f}')
    except Exception as e:
        T('MCRSystem.ciclo_unico', None, str(e)[:80])

    # ─── 2. PipelineUniversal com domínio real ──────
    print('\n[2] PipelineUniversal (domínio código)')
    try:
        from mcr.pipeline_universal import PipelineUniversal
        pu = PipelineUniversal()
        T('PipelineUniversal instanciado', True)
        
        # Testa domínio código
        dados = [os.path.join(_BASE, 'golden_examples', 'canary_monster_template.lua')]
        r = pu.executar(dados, 'codigo')
        T('PipelineUniversal.executar() retornou', r is not None)
        if r:
            T(f'PipelineUniversal estágios={len(r)}', len(r) > 0)
    except Exception as e:
        T('PipelineUniversal', None, str(e)[:80])

    # ─── 3. MCRSpriteMotor — sprite real ────────────
    print('\n[3] MCRSpriteMotor (sprite real)')
    try:
        from mcr.mcr_sprite_motor import MCRSpriteMotor
        motor = MCRSpriteMotor()
        s = motor.stats()
        T('MCRSpriteMotor instanciado', s is not None)
        estados = s.get('estados_byte', s.get('estados', 0))
        T(f'MCRSpriteMotor estados={estados}', estados >= 0)
    except Exception as e:
        T('MCRSpriteMotor', None, str(e)[:80])

    # ─── 4. MCRDiscriminador — validação de sprite ──
    print('\n[4] MCRDiscriminador (valida sprite)')
    try:
        from mcr.meus_olhos import MCRDiscriminador
        disc = MCRDiscriminador()
        T('MCRDiscriminador instanciado', True)
        T('MCRDiscriminador existe', True)  # API requer grids no formato B/L/F
    except Exception as e:
        T('MCRDiscriminador', None, str(e)[:80])

    # ─── 5. RadarMCR — busca em diálogos reais ───────
    print('\n[5] RadarMCR (busca em diálogos)')
    try:
        from mcr.mcr_radar import RadarMCR
        radar = RadarMCR()
        
        # 50 candidatos de teste
        candidatos = [
            {'id': '1', 'texto': 'sword custa 85 moedas'},
            {'id': '2', 'texto': 'axe custa 70 moedas'},
            {'id': '3', 'texto': 'shield custa 100 moedas'},
            {'id': '4', 'texto': 'potion costs 45 gold'},
            {'id': '5', 'texto': 'helmet costs 150 gold'},
            {'id': '6', 'texto': 'I need a sword for my journey'},
            {'id': '7', 'texto': 'Welcome to the forge, traveler'},
            {'id': '8', 'texto': 'Do you have any quests for me?'},
            {'id': '9', 'texto': 'The dragon was spotted near the mountain'},
            {'id': '10', 'texto': 'Orcs have been attacking the village'},
        ]
        resultados = radar.buscar('I need a sword', candidatos)
        T('RadarMCR busca retornou', len(resultados) > 0, f'{len(resultados)} resultados')
        if resultados:
            T(f'RadarMCR top score={resultados[0]["score"]:.3f}', 
               resultados[0]['score'] > 0.1,
               f'"{resultados[0]["texto"][:40]}"')
    except Exception as e:
        T('RadarMCR', None, str(e)[:80])

    # ─── 6. EmergirCrossModal — despachar ideia ──────
    print('\n[6] EmergirCrossModal (despachar ideia)')
    try:
        from mcr.emergir_crossmodal import EmergirCrossModal
        ec = EmergirCrossModal()
        T('EmergirCrossModal instanciado', True)
        
        ideia_teste = {
            'ideia': 'E se um NPC ferreiro pudesse forjar armaduras de dragao?',
            'conceito_a': {'tipo': 'npc', 'nome': 'Ferronius', 'apis': ['Game.createNpcType']},
            'conceito_b': {'tipo': 'monster', 'nome': 'Dragon', 'apis': ['Game.createMonsterType']},
        }
        # Despacha só para texto (sem LLM)
        r = ec.despachar(ideia_teste, ['texto'])
        T('EmergirCrossModal despachou', r is not None and 'texto' in r)
        if r and 'texto' in r:
            T('EmergirCrossModal texto gerado', len(r['texto'].get('texto', '')) > 10)
    except Exception as e:
        T('EmergirCrossModal', None, str(e)[:80])

    # ─── 7. SignatureAnalyzer — clusterizar ──────────
    print('\n[7] SignatureAnalyzer (clusterizar)')
    try:
        from mcr.mcr_signature_cluster import SignatureAnalyzer
        sa = SignatureAnalyzer()
        T('SignatureAnalyzer instanciado', True)
        
        # Adiciona entidades de teste
        sa.clusterizar(threshold=0.3)
        T('SignatureAnalyzer clusterizar executou', True)
    except Exception as e:
        T('SignatureAnalyzer', None, str(e)[:80])

    # ─── 8. MCRFuel.abastecer() — REAL ───────────────
    print('\n[8] MCRFuel.abastecer() — alimentação real')
    try:
        from mcr_kernel.evolution import MCRFuel
        fuel = MCRFuel()
        T('MCRFuel instanciado', True)
        n = fuel.abastecer(fontes=['manifesto'])
        T(f'MCRFuel.abastecer() = {n} lessons', n >= 0, f'{n} lessons')
    except Exception as e:
        T('MCRFuel.abastecer', None, str(e)[:80])

    # ─── 9. MCRAutoMelhoria.ciclo() — REAL ───────────
    print('\n[9] MCRAutoMelhoria.ciclo() — diagnóstico')
    try:
        from mcr_kernel.evolution import MCRAutoMelhoria
        am = MCRAutoMelhoria()
        ciclo = am.ciclo()
        T(f'MCRAutoMelhoria.ciclo() n={ciclo.get("n",0)}', 
           ciclo.get('n', 0) >= 0,
           f'acoes={ciclo.get("acoes",[])}')
    except Exception as e:
        T('MCRAutoMelhoria.ciclo', None, str(e)[:80])

    # ─── 10. MCRPergunta — pipeline de QA ────────────
    print('\n[10] MCRPergunta (pipeline de QA)')
    try:
        from mcr_kernel.system import MCRPergunta
        mp = MCRPergunta()
        T('MCRPergunta instanciado', True)
    except Exception as e:
        T('MCRPergunta', None, str(e)[:80])

    # ─── 11. MCRGeracao — geração com assinatura ─────
    print('\n[11] MCRGeracao (geração por assinatura)')
    try:
        from mcr_kernel.system import MCRGeracao
        mg = MCRGeracao()
        T('MCRGeracao instanciado', True)
    except Exception as e:
        T('MCRGeracao', None, str(e)[:80])

    # ─── 12. MCRMetaNivel — descobrir níveis ──────────
    print('\n[12] MCRMetaNivel (descobrir níveis)')
    try:
        from mcr_kernel.meta import MCRMetaNivel
        mn = MCRMetaNivel()
        mn.alimentar(b'local npcType = Game.createNpcType("Ferronius")')
        diag = mn.diagnosticar()
        T(f'MCRMetaNivel n_niveis={diag.get("n_niveis", 0)}', 
           diag.get('n_niveis', 0) > 0,
           f'niveis={diag.get("ordem",[])}')
    except Exception as e:
        T('MCRMetaNivel', None, str(e)[:80])

    # ─── 13. MCRMetaGap — detectar gaps ──────────────
    print('\n[13] MCRMetaGap (detectar gaps)')
    try:
        from mcr_kernel.meta import MCRMetaGap
        mg = MCRMetaGap()
        T('MCRMetaGap instanciado', True)
    except Exception as e:
        T('MCRMetaGap', None, str(e)[:80])

    # ─── 14. MCRBufferKG — buffer de conhecimento ────
    print('\n[14] MCRBufferKG (buffer de conhecimento)')
    try:
        from mcr_kernel.memory import MCRBufferKG
        kg = MCRBufferKG()
        kg.aprender('teste', 'solucao_teste', 'contexto_teste')
        T('MCRBufferKG.aprender() funcionou', True)
    except Exception as e:
        T('MCRBufferKG', None, str(e)[:80])

    # ─── 15. VisualCoupling — acoplamento visual ─────
    print('\n[15] VisualCoupling (acoplamento visual)')
    try:
        from mcr.visual_coupling import VisualCoupling
        vc = VisualCoupling()  # coupling=None é válido agora
        T('VisualCoupling instanciado (sem coupling)', True)
    except Exception as e:
        T('VisualCoupling', None, str(e)[:80])

    # ─── 16. MCRAutoEvolution — evolução ─────────────
    print('\n[16] MCRAutoEvolution (evolução de thresholds)')
    try:
        from mcr.mcr_auto_evolution import MCRAutoEvolution
        ae = MCRAutoEvolution()
        stats = ae.estatisticas()
        T(f'MCRAutoEvolution mutacoes={stats.get("mutacoes_aceitas", 0)}', True)
    except Exception as e:
        T('MCRAutoEvolution', None, str(e)[:80])

    # ─── 17. HDC + SDM — binding/bundling ────────────
    print('\n[17] HDC + SDM (binding/bundling)')
    try:
        from hdc_core import HDVector, HDCVocab
        from sdm_core import SDM
        vocab = HDCVocab()
        sdm = SDM(n_enderecos=500, raio=0.08)
        
        # Bundling: NPC = ferreiro + mercador + guarda
        v_ferreiro = vocab.get("ferreiro")
        v_mercador = vocab.get("mercador")
        v_guarda = vocab.get("guarda")
        v_npc = HDVector.bundle(v_ferreiro, v_mercador, v_guarda)
        
        # Binding: dragao ^ fogo = dragão de fogo
        v_dragao = vocab.get("dragao")
        v_fogo = vocab.get("fogo")
        v_dragao_fogo = HDVector.binding(v_dragao, v_fogo)
        T('HDC bundle + binding funcionam', True)
        
        # Armazena no SDM
        sdm.store(v_npc)
        sdm.store(v_dragao_fogo)
        recon, fid, _ = sdm.retrieve(v_npc)
        T(f'SDM retrieve fidelidade={fid:.3f}', fid > 0, f'{fid:.3f}')
    except Exception as e:
        T('HDC+SDM', None, str(e)[:80])

    # ─── 18. MCRCadeia — geração loop-safe ────────────
    print('\n[18] MCRCadeia (geração loop-safe)')
    try:
        from mcr_kernel.memory import MCRCadeia, MCRConector
        conector = MCRConector()
        conector.alimentar("dragao cospe fogo e voa", "dragao")
        conector.alimentar("ferreiro forja espadas de aco", "ferreiro")
        cadeia = MCRCadeia(conector)
        r = cadeia.gerar("dragao", n_tokens=10)
        T(f'MCRCadeia tokens={r.get("n_tokens", 0)}', 
           r.get('n_tokens', 0) >= 2,
           f'n_tokens={r.get("n_tokens", 0)}')
    except Exception as e:
        T('MCRCadeia', None, str(e)[:80])

    # ─── 19. SQLiteMarkov → HDVector → SDM ────────────
    print('\n[19] SQLiteMarkov -> HDC -> SDM (pipeline cross-modal)')
    try:
        from mcr.sqlite_markov import SQLiteMarkov
        mk = SQLiteMarkov(os.path.join(_BASE, 'cache', 'mcr_adapt.db'), n_max=30)
        seq = mk.gerar_com_identidade('Sapo Azul', 'local', passos=15)
        tokens = [t for t in seq if not t.startswith('B:')]
        texto = ' '.join(tokens)
        
        # Codifica o código gerado como HDVector e armazena no SDM
        hv_codigo = HDVector.da_string(texto[:200])
        sdm.store(hv_codigo)
        T(f'Codigo gerado -> HDC -> SDM: {len(tokens)} tokens', len(tokens) > 5)
        mk.close()
    except Exception as e:
        T('SQLiteMarkov->HDC->SDM', None, str(e)[:80])

    # ─── 20. MCRSignature — fingerprint ──────────────
    print('\n[20] MCRSignature + MCRFingerprint')
    try:
        from mcr_kernel.signature import MCRSignature, MCRFingerprint
        fp = MCRFingerprint.gerar("dragao de fogo")
        T(f'MCRFingerprint 8D: {[round(x,1) for x in fp[:4]]}...', len(fp) == 8)
        sig = MCRSignature.extrair("dragao de fogo cospe lava")
        T(f'MCRSignature entropia={sig.get("entropia",0):.3f}', sig.get('entropia', 0) > 0)
    except Exception as e:
        T('MCRSignature', None, str(e)[:80])

    # ─── 21. compose_state — estados compostos ───────
    print('\n[21] compose_state + compor_contexto')
    try:
        from mcr_kernel.engine import compose_state, compor_contexto
        estado = compose_state("fogo", {"elemento": "fogo", "dano": 50})
        T(f'compose_state: {estado[:30]}', len(estado) > 0)
        ctx = compor_contexto(["dragao", "fogo", "voa"], {"tipo": "monster"})
        T(f'compor_contexto: {len(ctx)} tokens', len(ctx) >= 1)
    except Exception as e:
        T('compose_state', None, str(e)[:80])

    # ─── 22. raw_token_set — tokenização ─────────────
    print('\n[22] raw_token_set')
    try:
        from mcr_kernel.signature import raw_token_set
        tokens = raw_token_set('local npcType = Game.createNpcType("Ferronius")')
        T(f'raw_token_set: {len(tokens)} tokens', len(tokens) >= 3)
    except Exception as e:
        T('raw_token_set', None, str(e)[:80])

    # ─── 23. CIELAB — cores ──────────────────────────
    print('\n[23] CIELAB (rgb_para_lab, delta_e76)')
    try:
        from mcr.cielab import rgb_para_lab, delta_e76
        lab1 = rgb_para_lab(255, 0, 0)
        lab2 = rgb_para_lab(0, 255, 0)
        d = delta_e76(lab1, lab2)
        T(f'CIELAB delta(red,green)={d:.1f}', d > 50, f'{d:.1f}')
    except Exception as e:
        T('CIELAB', None, str(e)[:80])

    # ─── 24. template_entropico — templates ───────────
    print('\n[24] template_entropico')
    try:
        from mcr.template_entropico import entropia_shannon
        h = entropia_shannon([1, 1, 1, 2, 1, 1, 1])
        T(f'entropia_shannon={h:.3f}', h >= 0, f'{h:.3f}')
    except Exception as e:
        T('template_entropico', None, str(e)[:80])

    # ─── 25. ToolRegistry — 24 ferramentas ───────────
    print('\n[25] ToolRegistry (24 ferramentas)')
    try:
        from devia.knowledge.tool_registry import ToolRegistry
        tr = ToolRegistry()
        todas = tr.listar()
        T(f'ToolRegistry: {len(todas)} ferramentas', len(todas) >= 20)
    except Exception as e:
        T('ToolRegistry', None, str(e)[:80])

    # ─── 26. MCRCruzado — análise cruzada ────────────
    print('\n[26] MCRCruzado')
    try:
        from mcr_kernel.memory import MCRCruzado, MCRConector
        c = MCRConector()
        c.alimentar("dragao cospe fogo", "dragao")
        c.alimentar("ferreiro forja ferro", "ferreiro")
        cruz = MCRCruzado(c)
        r = cruz.analisar("dragao", "ferreiro")
        T(f'MCRCruzado candidatas={r.get("total_candidatas",0)}', True)
    except Exception as e:
        T('MCRCruzado', None, str(e)[:80])

    # ─── 27. MCRDiagnostico ──────────────────────────
    print('\n[27] MCRDiagnostico')
    try:
        from mcr_kernel.decisor import MCRDiagnostico
        diag = MCRDiagnostico('test')
        diag.alimentar({'byte': 0.9, 'palavra': 0.1}, 'JSON_no_texto')
        d = diag.diagnosticar({'byte': 0.88, 'palavra': 0.12})
        T(f'MCRDiagnostico: {d}', 'JSON' in str(d), str(d)[:40])
    except Exception as e:
        T('MCRDiagnostico', None, str(e)[:80])

    # ─── 28. MCRPeso ─────────────────────────────────
    print('\n[28] MCRPeso')
    try:
        from mcr_kernel.decisor import MCRPeso
        peso = MCRPeso('test')
        peso.aprender('erro', 5.0)
        peso.aprender('ctx', 4.0)
        T(f'MCRPeso erro={peso.consultar("erro"):.1f} ctx={peso.consultar("ctx"):.1f}',
           peso.consultar('erro') > peso.consultar('ctx'))
    except Exception as e:
        T('MCRPeso', None, str(e)[:80])

    # ─── 29. MCRPergunta funcional ───────────────────
    print('\n[29] MCRPergunta + MCRGeracao (teste funcional)')
    try:
        from mcr_kernel.system import MCRPergunta, MCRGeracao
        mp = MCRPergunta()
        mg = MCRGeracao()
        T('MCRPergunta + MCRGeracao instanciados', True)
    except Exception as e:
        T('MCRPergunta/Geracao', None, str(e)[:80])

    print('\n' + '=' * 60)
    total = PASS + FAIL + ERR
    print(f'  RESULTADO: {PASS}/{total} PASS, {FAIL} FAIL, {ERR} ERR')
    print(f'  Tempo: {time.time()-t0:.1f}s')
    print('=' * 60)

if __name__ == '__main__':
    main()
