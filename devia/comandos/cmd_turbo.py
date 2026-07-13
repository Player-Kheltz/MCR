"""Comando: turbo - Modo Offline Turbinado — respostas sem internet."""
def register():
    return {
        "name": "turbo",
        "desc": "Modo Offline Turbinado: usa KG + PatternEngine + Conselho + ToT5 para responder sem internet. Use --fragmentar para modo Bolo Desconstruido.",
        "handler": execute,
        "args": [{"name": "pergunta", "type": "str", "required": True}],
        "categoria": "ia",
    }

def execute(kg, ia, args, ctx_crew=None):
    if not args:
        print('[Turbo] Uso: turbo [--fragmentar] <pergunta>')
        return True
    
    # Detecta flag --fragmentar
    fragmentar = False
    if '--fragmentar' in args:
        fragmentar = True
        args = [a for a in args if a != '--fragmentar']
    
    texto = ' '.join(args)
    print(f'\n[Turbo] Modo Offline Turbinado ATIVADO')
    print(f'[Turbo] Fontes: KG + PatternEngine + Conselho + ToT5 + BlankFiller')
    print(f'[Turbo] Zero dependencia de internet.\n')
    
    # 1. PatternEngine analisa o KG em busca de padroes
    print('  [Turbo] Consultando PatternEngine no KG...')
    try:
        from modulos.pattern_engine import PatternEngine
        pe = PatternEngine()
        kg_result = pe.kg_pattern_analyze(kg, texto)
        if kg_result and 'conceitos' in kg_result:
            print(f'  [Turbo] {kg_result["total_encontrados"]} conceitos encontrados em {kg_result["ctxs_distintos"]} ctxs')
    except Exception as e:
        print(f'  [Turbo] PatternAnalyze: {e}')
        kg_result = None
    
    # 2. Busca expandida no KG
    print('  [Turbo] Busca expandida no KG...')
    try:
        lessons = kg.buscar_expandido(texto) if hasattr(kg, 'buscar_expandido') else kg.buscar(texto, max_r=10)
        print(f'  [Turbo] {len(lessons)} lessons encontradas')
    except Exception as e:
        print(f'  [Turbo] KG: {e}')
        lessons = []
    
    # 3. Conselho + ToT (via Supervisor)
    print('  [Turbo] Ativando pipeline offline...\n')
    try:
        import sys as _sys
        _sys.path.insert(0, _sys.path[0] if _sys.path else '')
        from supervisor import Supervisor
        from orquestrador import Orquestrador as _Orq
        
        orq = _Orq(kg=kg, ia=ia, ctx_crew=ctx_crew)
        sup = Supervisor(ia, kg, ctx_crew=ctx_crew, orquestrador=orq)
        
        # Usa pipeline_executor com flag turbo
        from modulos.pipeline_executor import PipelineExecutor
        from modulos.task_planner import TaskPlanner
        from modulos.tool_orchestrator import ToolOrchestrator
        _tools = ToolOrchestrator()
        _planner = TaskPlanner(ia=ia, tool_orchestrator=_tools)
        pipe = PipelineExecutor(
            kg=kg, ia=ia, ctx_crew=ctx_crew, orquestrador=orq,
            task_planner=_planner, tool_orchestrator=_tools
        )
        # Detecta fragmentar e passa para o pipeline
        if fragmentar:
            print(f'[Turbo] Modo Fragmentado ativado — pergunta sera desconstruida')
        resposta, revisao = pipe.executar(texto, turbo=True, fragmentar=fragmentar)
        
        if resposta:
            # VALIDATION PIPELINE
            try:
                from modulos.validation_pipeline import ValidationPipeline
                from modulos.pattern_engine import PatternEngine
                _vp = ValidationPipeline(kg=kg, pe=PatternEngine(), ia=ia)
                _validacao = _vp.validar(texto, resposta)
                print(f'\n[Veritas] Relatorio de Validacao:')
                for _e in _validacao.get('estagios', []):
                    print(f'  {_e["nome"]}: {_e["detalhes"]}')
            except Exception as _vp_err:
                print(f'[Veritas] Validation: {_vp_err}')
            
            # Salva resposta
            try:
                import os as _os
                _rp = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)),
                                    '..', '..', 'sandbox', '.mcr_resposta_turbo.txt')
                with open(_rp, 'w', encoding='utf-8') as _f:
                    _f.write(resposta)
                print(f'[Turbo] Resposta salva em: {_rp}')
            except Exception:
                pass
            print(f'\n{resposta}')
            return True
    except Exception as e:
        print(f'[Turbo] Pipeline: {e}')
    
    # Fallback: IA direta com contexto enriquecido
    print('  [Turbo] Usando fallback IA direta...')
    contexto_extra = ""
    if lessons:
        contexto_extra = '\n'.join([f"- {l.get('erro','')}: {l.get('solucao','')}"
                                   for l in lessons])
    
    prompt = (
        f"[SISTEMA]\nVoce esta em MODO OFFLINE TURBINADO.\n"
        f"SEM INTERNET. Use apenas o conhecimento interno do KG.\n\n"
        f"[CONTEXTO DO KG]\n{contexto_extra}\n\n"
        f"[PERGUNTA]\n{texto}\n\n"
        f"[INSTRUCAO]\nResponda de forma completa e especifica.\n"
        f"Use os dados do KG fornecidos. Nao seja generico.\n"
        f"Se nao souber, diga 'Nao tenho dados suficientes no KG'."
    )
    resposta = ia.gerar(prompt, 0.3) if ia else None
    if resposta:
        print(f'\n{resposta}')
    else:
        print('[Turbo] Nao foi possivel gerar resposta.')
    
    return True
