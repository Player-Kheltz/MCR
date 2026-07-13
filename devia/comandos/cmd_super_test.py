"""Comando: super-test — Pipeline de Validacao Universal do MCR-DevIA.
Executa 6 fases que testam todos os componentes do sistema:

FASE 1 - FUNDACAO: TruncationFixer, PatternEngine, KG stats
FASE 2 - APRENDIZADO: KG buscar, expandido, embedding
FASE 3 - CONSCIENCIA: EMERGIR, Conselho, ToT5, Self-Study
FASE 4 - RESPOSTA: Fragmentacao, Context Weaver, Reconstructor
FASE 5 - VALIDACAO: Validation Pipeline, Auto-Revisor, Ciclo
FASE 6 - RELATORIO: Metricas, eixo geral, recomendacoes

Uso:
  mcr super-test                # Pipeline completa
  mcr super-test --fase 3       # Fase especifica
  mcr super-test --relatorio    # Mostra ultimo relatorio
"""
import os, sys, json, time, re, hashlib
from datetime import datetime

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SANDBOX = os.path.join(BASE, 'sandbox')
RELATORIO_PATH = os.path.join(SANDBOX, '.mcr_super_test.json')


def register():
    return {
        "name": "super-test",
        "desc": "Pipeline de Validacao Universal: testa EMERGIR, KG, PatternEngine, Conselho, ToT5, Reconstructor, Validation, Ciclo de Aprendizado.",
        "handler": execute,
        "args": [],
        "categoria": "teste",
    }


def execute(kg, ia, args, ctx_crew=None):
    t0 = time.time()
    
    # Parse args
    fase_especifica = None
    if args:
        for a in args:
            if a == '--relatorio':
                return _mostrar_relatorio()
            if a.startswith('--fase'):
                try:
                    fase_especifica = int(a.split('=')[-1]) if '=' in a else int(args[args.index(a)+1])
                except Exception:
                    pass
    
    print('=' * 70)
    print('MCR-DevIA SUPER TEST — Pipeline de Validacao Universal')
    print('=' * 70)
    print()
    
    metricas = {
        'f1_fundacao': {},
        'f2_aprendizado': {},
        'f3_consciencia': {},
        'f4_resposta': {},
        'f5_validacao': {},
        'f6_relatorio': {},
        'timestamp': datetime.now().isoformat(),
        'tempo_total': 0,
    }
    
    # FASE 1: FUNDACAO
    if not fase_especifica or fase_especifica == 1:
        metricas['f1_fundacao'] = _fase1_fundacao(kg)
    
    # FASE 2: APRENDIZADO
    if not fase_especifica or fase_especifica == 2:
        metricas['f2_aprendizado'] = _fase2_aprendizado(kg, ia)
    
    # FASE 3: CONSCIENCIA
    if not fase_especifica or fase_especifica == 3:
        metricas['f3_consciencia'] = _fase3_consciencia(kg, ia)
    
    # FASE 4: RESPOSTA
    if not fase_especifica or fase_especifica == 4:
        metricas['f4_resposta'] = _fase4_resposta(kg, ia, ctx_crew)
    
    # FASE 5: VALIDACAO
    if not fase_especifica or fase_especifica == 5:
        metricas['f5_validacao'] = _fase5_validacao(kg, ia)
    
    # FASE 6: RELATORIO
    if not fase_especifica or fase_especifica == 6:
        metricas['f6_relatorio'] = _fase6_relatorio(metricas)
    
    metricas['tempo_total'] = round(time.time() - t0, 1)
    
    # Salva relatorio
    try:
        with open(RELATORIO_PATH, 'w', encoding='utf-8') as f:
            json.dump(metricas, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    
    # Resumo final
    _mostrar_resumo(metricas)
    
    return True


# ===================================================================
# FASE 1: FUNDACAO
# ===================================================================

def _fase1_fundacao(kg):
    print(f'\n{"="*60}')
    print('FASE 1: FUNDACAO — TruncationFixer + PatternEngine + KG')
    print(f'{"="*60}')
    m = {}
    
    # 1.1 TruncationFixer
    print('\n[1.1] TruncationFixer...')
    try:
        from modulos.truncation_fixer import escanear
        devia_dir = os.path.join(BASE, 'Scripts', 'mcr_devia')
        ocorrencias = escanear(devia_dir)
        m['truncamentos_residuais'] = len(ocorrencias)
        m['truncamentos_ok'] = len(ocorrencias) == 0
        print(f'  Truncamentos residuais: {len(ocorrencias)}')
        if ocorrencias:
            for o in ocorrencias:
                print(f'    {o["arquivo"]}:L{o["linha"]}: {o["texto"]}')
    except Exception as e:
        m['truncamentos_erro'] = str(e)
        print(f'  ERRO: {e}')
    
    # 1.2 PatternEngine — eixo do proprio sistema
    print('\n[1.2] PatternEngine — eixo do codigo fonte...')
    try:
        from modulos.pattern_engine import PatternEngine
        pe = PatternEngine()
        tokens_totais = []
        modulos_dir = os.path.join(BASE, 'Scripts', 'mcr_devia', 'modulos')
        for f in sorted(os.listdir(modulos_dir)):
            if f.endswith('.py') and not f.startswith('_'):
                fpath = os.path.join(modulos_dir, f)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                        codigo = fh.read()
                    tokens_totais.extend(pe.tokenizar(codigo, 'codigo'))
                except Exception:
                    pass
        if tokens_totais:
            fp = pe.fingerprint(tokens_totais)
            eixo = pe.eixo_nirvana_caos(tokens_totais)
            padroes = pe.extrair_padroes(tokens_totais)
            m['eixo_codigo'] = round(eixo, 3)
            m['fingerprint_len'] = len(fp)
            m['entropia'] = round(padroes.get('entropia', 0), 3)
            m['tokens'] = len(tokens_totais)
            print(f'  Eixo Nirvana-Caos: {eixo:.3f}')
            print(f'  Fingerprint: {len(fp)} dimensoes')
            print(f'  Entropia: {padroes.get("entropia", 0):.3f}')
            print(f'  Tokens: {len(tokens_totais)}')
        else:
            m['eixo_erro'] = 'sem tokens'
    except Exception as e:
        m['eixo_erro'] = str(e)
        print(f'  ERRO: {e}')
    
    # 1.3 KG stats
    print('\n[1.3] KG — estatisticas...')
    try:
        if kg:
            licoes = kg._get_licoes()
            ativas = [l for l in licoes if not l.get('inactive')]
            m['lessons_total'] = len(licoes)
            m['lessons_ativas'] = len(ativas)
            m['lessons_inativas'] = len(licoes) - len(ativas)
            ctxs = set(l.get('ctx', '?') for l in ativas)
            m['ctxs_distintos'] = len(ctxs)
            print(f'  Lessons: {len(licoes)} total, {len(ativas)} ativas, {len(licoes)-len(ativas)} inativas')
            print(f'  Contextos: {len(ctxs)}')
        else:
            m['kg_erro'] = 'KG nao disponivel'
    except Exception as e:
        m['kg_erro'] = str(e)
    
    return m


# ===================================================================
# FASE 2: APRENDIZADO
# ===================================================================

def _fase2_aprendizado(kg, ia):
    print(f'\n{"="*60}')
    print('FASE 2: APRENDIZADO — KG buscar + expandido + embedding')
    print(f'{"="*60}')
    m = {}
    
    if not kg:
        m['erro'] = 'KG nao disponivel'
        return m
    
    # 2.1 KG.aprender() — registra lessons de teste
    print('\n[2.1] KG.aprender()...')
    try:
        for i in range(3):
            kg.aprender(
                erro=f'teste_super_{i}: conceito de teste {i}',
                causa=f'Teste automatico da pipeline super-test',
                solucao=f'Resposta de teste {i}: o padrao universal existe em tudo',
                ctx='super_test'
            )
        m['aprender_ok'] = True
        print('  3 lessons de teste registradas (ctx=super_test)')
    except Exception as e:
        m['aprender_erro'] = str(e)
        print(f'  ERRO: {e}')
    
    # 2.2 KG.buscar() — busca por keyword
    print('\n[2.2] KG.buscar() — keyword...')
    try:
        resultados = kg.buscar('teste_super_0', max_r=3)
        m['buscar_keyword'] = len(resultados)
        m['buscar_keyword_ok'] = len(resultados) > 0
        print(f'  Resultados: {len(resultados)}')
        for r in resultados:
            print(f'    {r.get("erro","?")}')
    except Exception as e:
        m['buscar_keyword_erro'] = str(e)
        print(f'  ERRO: {e}')
    
    # 2.3 KG.buscar_expandido() — fuzzy + ctx
    print('\n[2.3] KG.buscar_expandido() — fuzzy...')
    try:
        if hasattr(kg, 'buscar_expandido'):
            resultados2 = kg.buscar_expandido('teste super conceito', max_r=5)
            m['buscar_expandido'] = len(resultados2)
            m['buscar_expandido_ok'] = len(resultados2) > 0
            print(f'  Resultados: {len(resultados2)}')
        else:
            print('  Metodo nao disponivel')
            m['buscar_expandido_ok'] = False
    except Exception as e:
        m['buscar_expandido_erro'] = str(e)
        print(f'  ERRO: {e}')
    
    # 2.4 KG.buscar_por_embedding() — semantico
    print('\n[2.4] KG.buscar_por_embedding() — semantico...')
    try:
        if hasattr(kg, 'buscar_por_embedding'):
            resultados3 = kg.buscar_por_embedding('conceito universal padrao', n=3)
            m['buscar_embedding'] = len(resultados3)
            m['buscar_embedding_ok'] = len(resultados3) > 0
            print(f'  Resultados: {len(resultados3)}')
        else:
            print('  Metodo nao disponivel')
            m['buscar_embedding_ok'] = False
    except Exception as e:
        m['buscar_embedding_erro'] = str(e)
        print(f'  ERRO: {e}')
    
    return m


# ===================================================================
# FASE 3: CONSCIENCIA
# ===================================================================

def _fase3_consciencia(kg, ia):
    print(f'\n{"="*60}')
    print('FASE 3: CONSCIENCIA — EMERGIR + Conselho + ToT5 + Self-Study')
    print(f'{"="*60}')
    m = {}
    
    # 3.1 EMERGIR — deteccao de padroes emergentes
    print('\n[3.1] EMERGIR — padroes emergentes...')
    try:
        from modulos.emergir import EmergirEngine
        emergir = EmergirEngine(kg=kg, ia=ia)
        resultado = emergir.processar() if hasattr(emergir, 'processar') else emergir.executar()
        m['emergir_padroes'] = len(resultado) if resultado else 0
        m['emergir_ok'] = bool(resultado)
        if resultado:
            padroes = resultado.get('padroes', resultado.get('insights', []))
            print(f'  Padroes encontrados: {len(padroes)}')
            for p in padroes:
                print(f'    {str(p)}')
        else:
            print('  Nenhum padrao emergente detectado')
    except Exception as e:
        m['emergir_erro'] = str(e)
        print(f'  ERRO: {e}')
    
    # 3.2 Conselho — 9 membros deliberam
    print('\n[3.2] Conselho — deliberacao...')
    try:
        from modulos.conselho import Conselho
        conselho = Conselho(kg=kg, ia=ia)
        pergunta = 'O que e o padrao universal do MCR-DevIA?'
        resultado = conselho.deliberar(pergunta)
        opinioes = resultado.get('opinioes', resultado.get('respostas', []))
        m['conselho_membros'] = len(opinioes)
        m['conselho_ok'] = len(opinioes) >= 1
        print(f'  Membros que opinaram: {len(opinioes)}')
        for o in opinioes:
            nome = o.get('nome', o.get('membro', '?'))
            texto = str(o.get('opiniao', o.get('texto', '')))
            print(f'    {nome}: {texto}')
    except Exception as e:
        m['conselho_erro'] = str(e)
        print(f'  ERRO: {e}')
    
    # 3.3 TreeOfThought — 5 perspectivas
    print('\n[3.3] ToT5 — 5 perspectivas...')
    try:
        from modulos.tree_of_thought import TreeOfThought, _CAMINHOS
        m['tot_disponiveis'] = len(_CAMINHOS)
        print(f'  Perspectivas disponiveis: {len(_CAMINHOS)}')
        for c in _CAMINHOS:
            print(f'    {c["nome"]}')
    except Exception as e:
        m['tot_erro'] = str(e)
        print(f'  ERRO: {e}')
    
    # 3.4 Self-Study — escaneia anti-padroes
    print('\n[3.4] Self-Study — analise de anti-padroes...')
    try:
        from modulos.self_study import SelfStudyEngine
        ss = SelfStudyEngine(kg=kg, ia=ia)
        resultado = ss.escanear_projeto()
        anti_padroes = resultado.get('anti_patterns', resultado.get('problemas', []))
        m['self_study_anti_padroes'] = len(anti_padroes)
        m['self_study_ok'] = True
        print(f'  Anti-padroes encontrados: {len(anti_padroes)}')
        for ap in list(anti_padroes):
            print(f'    {str(ap)}')
    except Exception as e:
        m['self_study_erro'] = str(e)
        print(f'  ERRO: {e}')
    
    return m


# ===================================================================
# FASE 4: RESPOSTA
# ===================================================================

def _fase4_resposta(kg, ia, ctx_crew):
    print(f'\n{"="*60}')
    print('FASE 4: RESPOSTA — Fragmentacao + Weaver + Reconstructor')
    print(f'{"="*60}')
    m = {}
    
    pergunta_teste = 'Explique o padrao universal do PatternEngine: o que e tokenizacao, como funciona o fingerprint de 64 dimensoes, o que o eixo Nirvana-Caos mede, e como o Conselho usa esses padroes para deliberar?'
    
    # 4.1 ContextCrew.fragmentar_recursivo()
    print('\n[4.1] ContextCrew.fragmentar_recursivo()...')
    try:
        if ctx_crew and hasattr(ctx_crew, 'fragmentar_recursivo'):
            arvore = ctx_crew.fragmentar_recursivo(pergunta_teste)
            folhas = ctx_crew.extrair_folhas(arvore)
            m['fragmentos'] = len(folhas)
            m['fragmentos_ok'] = len(folhas) >= 1
            prof = arvore.get('profundidade', 0)
            m['profundidade'] = prof
            print(f'  Folhas (padroes brutos): {len(folhas)}')
            print(f'  Profundidade da arvore: {prof}')
            for f in folhas:
                print(f'    Entropia {f.get("entropia",0):.3f}: {f["texto"]}')
        else:
            print('  ContextCrew ou fragmentar_recursivo nao disponivel')
            m['fragmentos_ok'] = False
    except Exception as e:
        m['fragmentos_erro'] = str(e)
        print(f'  ERRO: {e}')
    
    # 4.2 Context Weaver + Reconstructor
    print('\n[4.2] Reconstructor — bottom-up...')
    try:
        if ctx_crew and hasattr(ctx_crew, 'fragmentar_recursivo'):
            from modulos.reconstructor import Reconstructor
            from modulos.pattern_engine import PatternEngine
            
            arvore = ctx_crew.fragmentar_recursivo(pergunta_teste)
            pe = PatternEngine()
            recon = Reconstructor(kg=kg, ia=ia, pe=pe)
            resultado = recon.reconstruir(arvore, pergunta_teste)
            
            m['reconstructor_chars'] = len(resultado.get('resposta_final', ''))
            m['reconstructor_folhas'] = resultado.get('folhas_processadas', 0)
            m['reconstructor_eixo'] = resultado.get('eixo_final', 0)
            m['reconstructor_ok'] = len(resultado.get('resposta_final', '')) > 50
            
            print(f'  Resposta: {resultado.get("resposta_final", "")}...')
            print(f'  Caracteres: {m["reconstructor_chars"]}')
            print(f'  Eixo final: {m["reconstructor_eixo"]}')
        else:
            print('  Reconstructor nao executado (sem ctx_crew)')
    except Exception as e:
        m['reconstructor_erro'] = str(e)
        print(f'  ERRO: {e}')
    
    # 4.3 Conceptual Planner
    print('\n[4.3] Conceptual Planner...')
    try:
        from modulos.conceptual_planner import ConceptualPlanner
        from modulos.pattern_engine import PatternEngine
        pe = PatternEngine()
        planner = ConceptualPlanner(kg=kg, ia=ia, pe=pe)
        plano = planner.criar_plano('PatternEngine')
        m['plano_metafora'] = bool(plano.get('metafora', ''))
        m['plano_passos'] = plano.get('passos', 0)
        m['plano_ok'] = bool(plano.get('plano', ''))
        if plano.get('plano'):
            print(f'  Plano conceitual gerado ({len(plano["plano"])} chars)')
            if plano.get('metafora'):
                print(f'  Metafora: {plano["metafora"]}')
        else:
            print('  Nenhum plano gerado')
    except Exception as e:
        m['plano_erro'] = str(e)
        print(f'  ERRO: {e}')
    
    return m


# ===================================================================
# FASE 5: VALIDACAO
# ===================================================================

def _fase5_validacao(kg, ia):
    print(f'\n{"="*60}')
    print('FASE 5: VALIDACAO — Validation Pipeline + Auto-Revisor + Ciclo')
    print(f'{"="*60}')
    m = {}
    
    # Usa uma resposta pronta para validar
    resposta_teste = (
        'O eixo Nirvana-Caos e uma metrica continua de 0.0 a 1.0 calculada pelo '
        'PatternEngine. O metodo eixo_nirvana_caos() em pattern_engine.py:L303 '
        'tokeniza a entrada, extrai padroes, calcula a entropia e normaliza o '
        'resultado para a escala. 0.0 representa Caos (alta entropia) e 1.0 '
        'representa Nirvana (perfeicao estrutural).'
    )
    pergunta_teste = 'O que e o eixo Nirvana-Caos?'
    
    # 5.1 Validation Pipeline
    print('\n[5.1] Validation Pipeline — 7 estagios...')
    try:
        from modulos.validation_pipeline import ValidationPipeline
        from modulos.pattern_engine import PatternEngine
        pe = PatternEngine()
        vp = ValidationPipeline(kg=kg, pe=pe, ia=ia)
        resultado = vp.validar(pergunta_teste, resposta_teste)
        estagios = resultado.get('estagios', [])
        m['validation_estagios'] = len(estagios)
        m['validation_ok'] = len(estagios) >= 7
        print(f'  Estagios executados: {len(estagios)}')
        for e in estagios:
            print(f'    {e["nome"]}: {e["detalhes"]}')
    except Exception as e:
        m['validation_erro'] = str(e)
        print(f'  ERRO: {e}')
    
    # 5.2 Auto-Revisor
    print('\n[5.2] Auto-Revisor — eixo + entropia + n-grama...')
    try:
        from modulos.auto_revisor import AutoRevisor
        revisor = AutoRevisor(kg=kg)
        revisao = revisor.revisar(resposta_teste, pergunta_original=pergunta_teste)
        m['auto_revisor_alucinacoes'] = revisao.get('total', 0)
        m['auto_revisor_eixo'] = revisao.get('eixo', 0)
        m['auto_revisor_entropia'] = revisao.get('entropia', 0)
        print(f'  Alucinacoes: {revisao.get("total", 0)}')
        print(f'  Eixo: {revisao.get("eixo", 0)}')
        print(f'  Entropia: {revisao.get("entropia", 0)}')
        if revisao.get('sugestao'):
            print(f'  Sugestao: {revisao["sugestao"]}')
    except Exception as e:
        m['auto_revisor_erro'] = str(e)
        print(f'  ERRO: {e}')
    
    # 5.3 Session Cache
    print('\n[5.3] Session Cache — save + load...')
    try:
        from modulos.session_cache import iniciar_sessao, salvar_passo, passo_ja_executado, concluir_sessao, detectar_sessao_incompleta
        plano_teste = [{'tool': 'IA', 'solicitacao': 'teste'}]
        s = iniciar_sessao('super_test', 'Pergunta de teste', plano_teste)
        salvar_passo(0, 'IA', 'teste', 'Resposta de teste do super test')
        carregado = passo_ja_executado(0)
        m['session_cache_ok'] = carregado == 'Resposta de teste do super test'
        print(f'  Salvo e recuperado: {m["session_cache_ok"]}')
        concluir_sessao()
    except Exception as e:
        m['session_cache_erro'] = str(e)
        print(f'  ERRO: {e}')
    
    return m


# ===================================================================
# FASE 6: RELATORIO
# ===================================================================

def _fase6_relatorio(metricas):
    """Calcula nota geral e recomendacoes."""
    m = {}
    
    # Extrai metricas-chave
    f1 = metricas.get('f1_fundacao', {})
    f2 = metricas.get('f2_aprendizado', {})
    f3 = metricas.get('f3_consciencia', {})
    f4 = metricas.get('f4_resposta', {})
    f5 = metricas.get('f5_validacao', {})
    
    # Calcula pontuacao por fase (0-10)
    pesos = {
        'truncamentos_ok': (f1.get('truncamentos_ok', False), 0.5),
        'eixo_codigo': (f1.get('eixo_codigo', 0) / 1.0, 0.5),  # 0.639 / 1.0 = 0.639
        'buscar_keyword_ok': (f2.get('buscar_keyword_ok', False), 0.3),
        'buscar_expandido_ok': (f2.get('buscar_expandido_ok', False), 0.3),
        'buscar_embedding_ok': (f2.get('buscar_embedding_ok', False), 0.4),
        'emergir_ok': (f3.get('emergir_ok', False), 0.3),
        'conselho_membros': (min(f3.get('conselho_membros', 0) / 5, 1.0), 0.3),
        'tot_disponiveis': (min(f3.get('tot_disponiveis', 0) / 5, 1.0), 0.2),
        'self_study_ok': (f3.get('self_study_ok', False), 0.2),
        'fragmentos_ok': (f4.get('fragmentos_ok', False), 0.3),
        'reconstructor_ok': (f4.get('reconstructor_ok', False), 0.4),
        'plano_ok': (f4.get('plano_ok', False), 0.3),
        'validation_ok': (f5.get('validation_ok', False), 0.5),
        'session_cache_ok': (f5.get('session_cache_ok', False), 0.5),
    }
    
    score_total = 0.0
    peso_total = 0.0
    for nome, (valor, peso) in pesos.items():
        # Converte bool para 0/1
        v = 1.0 if valor is True else (0.0 if valor is False else float(valor))
        score_total += v * peso
        peso_total += peso
    
    nota_geral = (score_total / peso_total) * 10 if peso_total > 0 else 0
    
    m['nota_geral'] = round(nota_geral, 1)
    m['eixo_geral'] = f1.get('eixo_codigo', 0)
    m['lessons_ativas'] = f1.get('lessons_ativas', 0)
    m['total_estagios_validacao'] = f5.get('validation_estagios', 0)
    
    # Recomendacoes
    recomendacoes = []
    if not f1.get('truncamentos_ok', True):
        recomendacoes.append(f'Corrigir {f1.get("truncamentos_residuais", 0)} truncamentos residuais')
    if f1.get('eixo_codigo', 0) < 0.5:
        recomendacoes.append('Eixo do codigo abaixo de 0.5 — priorizar refatoracao')
    if not f2.get('buscar_embedding_ok', True):
        recomendacoes.append('KG.buscar_por_embedding() pode estar offline (Ollama)')
    if not f4.get('reconstructor_ok', False):
        recomendacoes.append('Reconstructor nao gerou resposta valida')
    if not f3.get('emergir_ok', False):
        recomendacoes.append('EMERGIR precisa de mais dados no KG para detectar padroes')
    if not recomendacoes:
        recomendacoes.append('Sistema saudavel. Nenhuma acao urgente.')
    
    m['recomendacoes'] = recomendacoes
    m['pesos_avaliados'] = len(pesos)
    
    return m


# ===================================================================
# RELATORIO / RESUMO
# ===================================================================

def _mostrar_relatorio():
    """Mostra o ultimo relatorio salvo."""
    if not os.path.exists(RELATORIO_PATH):
        print('[SuperTest] Nenhum relatorio encontrado. Execute mcr super-test primeiro.')
        return True
    
    with open(RELATORIO_PATH, 'r', encoding='utf-8') as f:
        metricas = json.load(f)
    
    _mostrar_resumo(metricas)
    return True


def _mostrar_resumo(metricas):
    """Mostra resumo final formatado."""
    f1 = metricas.get('f1_fundacao', {})
    f2 = metricas.get('f2_aprendizado', {})
    f3 = metricas.get('f3_consciencia', {})
    f4 = metricas.get('f4_resposta', {})
    f5 = metricas.get('f5_validacao', {})
    f6 = metricas.get('f6_relatorio', {})
    
    nota = f6.get('nota_geral', '?')
    eixo = f6.get('eixo_geral', f1.get('eixo_codigo', '?'))
    
    print()
    print('=' * 70)
    print(f'SUPER TEST — RELATORIO FINAL')
    print('=' * 70)
    print(f'  Timestamp: {metricas.get("timestamp", "?")}')
    print(f'  Tempo total: {metricas.get("tempo_total", "?")}s')
    print()
    print(f'  NOTA GERAL: {nota}/10')
    print(f'  EIXO DO SISTEMA: {eixo}')
    print()
    print(f'  FASE 1 - FUNDACAO:')
    print(f'    Truncamentos residuais: {f1.get("truncamentos_residuais", "?")}')
    print(f'    Eixo do codigo: {f1.get("eixo_codigo", "?")}')
    print(f'    Fingerprint: {f1.get("fingerprint_len", "?")} dim')
    print(f'    Lessons: {f1.get("lessons_ativas", "?")} ativas / {f1.get("lessons_total", "?")} total')
    print()
    print(f'  FASE 2 - APRENDIZADO:')
    print(f'    KG.buscar(): {f2.get("buscar_keyword", "?")} resultados')
    print(f'    KG.buscar_expandido(): {f2.get("buscar_expandido", "?")}')
    print(f'    KG.buscar_por_embedding(): {f2.get("buscar_embedding", "?")}')
    print()
    print(f'  FASE 3 - CONSCIENCIA:')
    print(f'    EMERGIR padroes: {f3.get("emergir_padroes", "?")}')
    print(f'    Conselho membros: {f3.get("conselho_membros", "?")}')
    print(f'    ToT5 perspectivas: {f3.get("tot_disponiveis", "?")}')
    print(f'    Self-Study anti-padroes: {f3.get("self_study_anti_padroes", "?")}')
    print()
    print(f'  FASE 4 - RESPOSTA:')
    print(f'    Fragmentos: {f4.get("fragmentos", "?")}')
    print(f'    Reconstructor chars: {f4.get("reconstructor_chars", "?")}')
    print(f'    Reconstructor eixo: {f4.get("reconstructor_eixo", "?")}')
    print(f'    Plano conceitual: {f4.get("plano_passos", "?")} passos')
    print()
    print(f'  FASE 5 - VALIDACAO:')
    print(f'    Validation estagios: {f5.get("validation_estagios", "?")}')
    print(f'    Auto-Revisor eixo: {f5.get("auto_revisor_eixo", "?")}')
    print(f'    Session Cache: {"OK" if f5.get("session_cache_ok") else "FALHA"}')
    print()
    print(f'  RECOMENDACOES:')
    for r in f6.get('recomendacoes', ['Nenhuma']):
        print(f'    - {r}')
    print('=' * 70)
