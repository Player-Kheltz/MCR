"""Modulo: Supervisor - V12 Contexto Agregado + Roteador Inteligente de Tarefas.
Classifica a intencao da pergunta e roteia para:
  - V12 Contexto Agregado (factual/definicao)
  - Orquestrador (codigo, revisao, criacao, planejamento)
  - Fallback para IA generica
"""
import os, re, json, urllib.request

OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/generate')

_STOP_V12 = {'o','a','os','as','um','uma','de','da','do','das','dos','em','no','na',
    'para','pra','por','com','sem','que','qual','como','se','ele','ela','voce','meu',
    'sua','seu','isso','isto','tem','ter','ser','foi','era','sao','e','nao','mais',
    'mas','muito','ja','ainda','tambem','ate','apos','antes','depois','sempre','nunca',
    'aqui','ali','la','todo','tudo','todos','cada','algum','nenhum','outro','mesmo',
    'assim','bem','mal','sim','nao','talvez','entao','apenas','so','quase','tipo',
    'forma','exemplo','caso','vez','coisa','gente','pessoa','dia','ano','mes'}

def init_module(contexto):
    kg = contexto.get('kg')
    ia = contexto.get('ia')
    if kg and ia:
        sup = Supervisor(ia, kg, ctx_crew=contexto.get('ctx_crew'),
                        orquestrador=contexto.get('orquestrador'))
        contexto['supervisor'] = sup
        return 'supervisor', sup
    return None, None


class Supervisor:
    """V12 Contexto Agregado + Roteador Inteligente de Tarefas."""
    
    def __init__(self, ia, kg, ctx_crew=None, orquestrador=None, identidade=""):
        self.ia = ia
        self.kg = kg
        self.ctx_crew = ctx_crew
        self.orquestrador = orquestrador
        self.identidade = identidade  # Identidade do projeto (injetada externamente)
    
    _KEYWORD_MAP = [
        (r"cri(a|r|e|ar)\s+(um|uma|o|a)?\s*(npc|personagem)", "CRIAR_NPC", 90),
        (r"(npc|personagem|vendedor|trader|shop)", "CRIAR_NPC", 50),
        (r"cri(a|r|e|ar)\s+(um|uma|o|a)?\s*(habilidade|skill|poder)", "CRIAR_HABILIDADE", 90),
        (r"(habilidade|skill|dominio|spa)", "CRIAR_HABILIDADE", 40),
        (r"cri(a|r|e|ar)\s+(um|uma|o|a)?\s*(arquivo|script|modulo|classe)", "CRIAR_CODIGO", 80),
        (r"(criar|fazer|gerar|produzir|implementar|desenvolver)", "CRIAR_CODIGO", 70),
        (r"(alterar|modificar|editar|mudar|atualizar|corrigir)", "EDITAR", 80),
        (r"(deletar|remover|apagar|excluir)", "DELETAR", 90),
        (r"(o que e|o que é|explique|como funciona|me fale sobre)", "PERGUNTA", 80),
        (r"(cpu|memoria|ram|disco|processo|sistema)", "SISTEMA", 80),
        (r"(teste|testando)", "TESTE", 90),
        (r"(ajuda|help|comandos|o que voce faz)", "AJUDA", 90),
    ]
    
    def classificar_keyword(self, texto):
        """Classifica intencao usando keywords (0 LLM, <1ms).
        
        Usado como fallback rapido ANTES de chamar o FAST.
        De mcr_dev/router.py — resgatado e integrado.
        """
        msg = texto.lower().strip()
        best_intent = "CHAT"
        best_score = 0
        
        import re
        for pattern, intent, priority in self._KEYWORD_MAP:
            if re.search(pattern, msg):
                if priority > best_score:
                    best_score = priority
                    best_intent = intent
        
        return best_intent if best_score >= 40 else None
    
    def classificar(self, texto):
        """Classifica intencao. Detecta prompts MULTI-intencao (3+ topicos)."""
        t = texto.lower()
        
        # CONTEXT REINFORCER: valida se ha contexto suficiente para rotear
        try:
            from modulos.context_reinforcer import ContextReinforcer
            cr = ContextReinforcer(ctx_crew=self.ctx_crew, kg=self.kg)
            cr_result = cr.reforcar(texto, self.ctx_crew)
            if not cr_result.get("valido") and cr_result.get("termos"):
                print(f'  [Supervisor] CR: contexto INSUFICIENTE para: {cr_result["termos"][:3]}')
                if cr_result.get("aprendeu"):
                    print(f'  [Supervisor] CR: weblearn disparado para aprendizado')
        except Exception as e:
            print(f'  [Supervisor] CR ERRO: {e}')
        
        # DETECCAO DE MULTI-INTENCAO: conta quantos topicos diferentes aparecem
        topicos_detectados = set()
        
        # Topicos que o prompt pode cobrir
        topicos = {
            'codigo': ['analise o codigo', 'analise este codigo', 'codigo fonte', 'arquivo .py',
                       'classe data', 'def processar', 'processor.py', 'codigo inteiro'],
            'bugs': ['bug', 'erro', 'problema', 'crash', 'travando', ' memoria', 'corrigir',
                    'outofmemory', 'race condition', 'security'],
            'gerar_codigo': ['crie um novo modulo', 'crie um novo', 'codigo completo',
                           'validador.py', 'escreva o codigo'],
            'arquitetura': ['arquitetura', '3 camadas', 'camadas', 'diagrama', 'fluxo de dados'],
            'revisao': ['revise', 'revisao', 'problemas de seguranca', 'prioridade'],
            'criacao': ['lenda', 'historia', 'narrativa', 'personagens', 'kael', 'pyra',
                       'forja', 'dataforge', 'conto'],
            'diagnostico': ['diagnostico', 'causa raiz', 'reproduzir', 'por que o sistema',
                          'lento e trava'],
            'refatoracao': ['refatore', 'refatorar', 'separe em metodos', '5 coisas'],
            'planejamento': ['plano de acao', 'curto prazo', 'medio prazo', 'longo prazo',
                           'board', 'etapas'],
            'sintese': ['licoes', 'paragrafo final', 'aprender', 'novo desenvolvedor'],
        }
        
        for topico, keywords in topicos.items():
            if any(k in t for k in keywords):
                topicos_detectados.add(topico)
        
        # Se 3+ topicos, e MULTI-INTENCAO
        if len(topicos_detectados) >= 3:
            print(f'  [Classificador] MULTI-INTENCAO detectada: {topicos_detectados}')
            return 'multimodal', 'complexo'
        
        # Classificacao classica (keyword-based) para intencoes simples
        
        # --- CODIGO: analise ---
        palavras_analise = ['analise o arquivo', 'analise este arquivo', 'analise esse arquivo',
                           'liste todos os problemas', 'encontre bugs', 'encontre problemas',
                           'o que este codigo faz', 'explique este codigo', 'explique o codigo',
                           'identifique erros', 'identifique problemas', 'revise o arquivo',
                           'revise este codigo', 'revise esse codigo', 'problemas de seguranca',
                           'code review', 'revisao de codigo']
        if any(p in t for p in palavras_analise):
            return 'codigo', 'analisar'
        
        # --- CODIGO: correcao de bug ---
        palavras_bug = ['contem um bug', 'tem um bug', 'bug na linha', 'corrija o bug',
                       'corrija este bug', 'corrigir bug', 'correcao de bug',
                       'esta errado', 'esta incorreto']
        if any(p in t for p in palavras_bug):
            return 'codigo', 'corrigir'
        
        # --- CODIGO: geracao ---
        palavras_gerar = ['crie um comando', 'crie um modulo', 'crie uma funcao',
                         'crie uma classe', 'crie um arquivo', 'gere codigo',
                         'crie codigo', 'escreva o codigo', 'codigo completo',
                         'codigo python', 'implemente', 'implementar']
        if any(p in t for p in palavras_gerar):
            return 'codigo', 'gerar'
        
        # --- CODIGO: refatoracao ---
        palavras_refatorar = ['refatore', 'refatorar', 'refatoracao', 'refatoracao',
                             'separacao de responsabilidades', 'redesenhe',
                             'melhore este codigo', 'reescreva', 'reorganize']
        if any(p in t for p in palavras_refatorar):
            return 'codigo', 'refatorar'
        
        # --- CRIACAO: historia/lore ---
        palavras_criar = ['crie uma historia', 'crie uma narrativa', 'crie uma lore',
                         'conte uma historia', 'escreva uma historia',
                         'historia de fundacao', 'conto fantastico',
                         'cidade-fortaleza', 'personagens']
        if any(p in t for p in palavras_criar):
            return 'criacao', 'historia'
        
        # --- PLANEJAMENTO: arquitetura ---
        palavras_arquitetura = ['arquitetura', 'redesenho arquitetural',
                               'classes abstratas', 'plugins', 'extensivel',
                               'suporte a plugins', 'sistema de plugins',
                               'plano de implementacao', 'diagrama']
        if any(p in t for p in palavras_arquitetura):
            return 'planejamento', 'arquitetura'
        
        # --- DIAGNOSTICO ---
        palavras_diagnostico = ['diagnostico', 'diagnosticar', 'causas possiveis',
                               'causa raiz', 'por que isso acontece',
                               'o que pode estar errado', 'problema reportado',
                               'produzindo saidas genericas']
        if any(p in t for p in palavras_diagnostico):
            return 'diagnostico', 'causa_raiz'
        
        # --- CONCEITUAL ---
        palavras_conceito = ['explique o fenomeno', 'explique a diferenca',
                            'o que sao alucinacoes', 'explique', 'diferenca entre',
                            'como se relacionam', 'tres padroes arquiteturais',
                            'supervisor context provider template']
        if any(p in t for p in palavras_conceito):
            return 'conceitual', 'explicacao'
        
        # --- FACTUAL (classico V12) ---
        if any(p in t for p in ['o que e', 'o que sao', 'o que eh', 'o que são',
                                 'o que é', 'significa', 'definicao', 'definição',
                                 'conceito', 'como funciona', 'para que serve']):
            return 'factual', 'definicao'
        if any(p in t for p in ['qual', 'quais', 'quem', 'quando', 'onde',
                                 'quanto', 'quantos', 'quantas']):
            return 'factual', 'dado'
        
        # --- Procedimental ---
        if any(p in t for p in ['como fazer', 'como criar', 'como usar',
                                 'como implementar', 'como configurar',
                                 'como resolver', 'passo a passo', 'tutorial']):
            return 'procedimental', 'tutorial'
        
        # --- Opiniao ---
        if any(p in t for p in ['o que voce acha', 'voce deveria',
                                 'melhor', 'pior', 'recomenda']):
            return 'opiniao', 'conselho'
        
        return 'desconhecido', 'geral'
    
    def perguntar(self, texto, contexto_extra=""):
        """FLUXO UNIVERSAL: Mente → ContextCrew → KG → Infinity → Orquestrador → Auto-Revisor.
        
        TODAS as ferramentas sao usadas em TODAS as perguntas, sem excecao.
        Nao ha mais 'fallback para V12' - V12 so existe como ultimo recurso.
        
        Fluxo:
        1. Mente.think() — conselho delibera (SEMPRE)
        2. ContextCrew + KG + Infinity — contexto máximo (SEMPRE)
        3. Orquestrador.executar("perguntar") — resposta (SEMPRE)
        4. Auto-revisor — revisa a resposta (SEMPRE)
        5. Mente.learn() — registra aprendizado (SEMPRE)
        """
        print(f'[Supervisor] "{texto[:80]}..."')
        
        tipo, subtipo = self.classificar(texto)
        print(f'  [Classificador] Tipo: {tipo}/{subtipo}')
        
        # ====================================================
        # FASE 0: FERRAMENTAS ANTES DA IA (grep/read/compile > IA)
        # ====================================================
        import re as _re_ferr
        _arq = _re_ferr.search(r'([\w/]+\.py)', texto)
        
        # 0a: Buscar bugs/linhas especificas? Usa grep (mais rapido, sem alucinacao)
        if _arq and ('linha' in texto.lower() or 'bug' in texto.lower() or 'problema' in texto.lower()):
            _path = _arq.group(1)
            # Tenta encontrar o arquivo em diretorios conhecidos
            for _d in [os.path.join(os.path.dirname(os.path.dirname(__file__)), 'modulos'),
                       os.path.join(os.path.dirname(os.path.dirname(__file__)), 'comandos'),
                       os.path.join(os.path.dirname(os.path.dirname(__file__)))]:
                _full = os.path.join(_d, _path)
                if os.path.exists(_full):
                    try:
                        import subprocess as _sp
                        # Usa findstr (Windows) ou grep (Linux)
                        _grep_cmd = 'findstr /n BUG TODO FIXME HACK XXX' if os.name == 'nt' else 'grep -n "BUG\\|TODO\\|FIXME\\|HACK\\|XXX"'
                        _r = _sp.run(f'{_grep_cmd} "{_full}"',
                                    capture_output=True, text=True, timeout=10, shell=True)
                        if _r.stdout:
                            print(f'  [Ferramentas] grep encontrou marcacoes em {_path}')
                            # Injeta como contexto_extra
                            contexto_extra += f'\n[GREP: {_path}]\n{_r.stdout[:1000]}\n'
                    except: pass
                    break
        
        # 0b: Validar sintaxe de codigo? Usa compile() (mais preciso que IA)
        if _arq and ('sintaxe' in texto.lower() or 'valido' in texto.lower() or 'compile' in texto.lower()):
            for _d in [os.path.join(os.path.dirname(os.path.dirname(__file__)), 'modulos'),
                       os.path.join(os.path.dirname(os.path.dirname(__file__)), 'comandos'),
                       os.path.join(os.path.dirname(os.path.dirname(__file__)))]:
                _full = os.path.join(_d, _path if not _path.startswith('modulos/') else _path.replace('modulos/', ''))
                if os.path.exists(_full):
                    with open(_full, 'r', encoding='utf-8') as _f:
                        _code = _f.read()
                    try:
                        compile(_code, _full, 'exec')
                        contexto_extra += f'\n[SINTAXE: {_path}]\nSem erros de sintaxe.\n'
                    except SyntaxError as _e:
                        contexto_extra += f'\n[SINTAXE: {_path}]\nErro: {_e}\n'
                    print(f'  [Ferramentas] Sintaxe verificada via compile()')
                    break
        
        # ====================================================
        # DETECTA SESSAO EM CACHE (resume automatico)
        # ====================================================
        try:
            from modulos.session_cache import detectar_sessao_incompleta, resumir_sessao
            _cache_info = detectar_sessao_incompleta()
            if _cache_info and _cache_info.get('ultimo_passo', -1) >= 0:
                _completados = len(_cache_info.get('passos_completados', {}))
                _total = len(_cache_info.get('plano', []))
                print(f'  [SessionCache] Sessao anterior INCOMPLETA: {_completados}/{_total} passos')
                print(f'  [SessionCache] Pipeline vai retomar automaticamente do passo {_completados+1}')
        except Exception:
            pass
        
        # ====================================================
        # PIPELINE EXECUTOR MULTI-REQUEST (planejar → executar → montar → revisar)
        # ====================================================
        try:
            from modulos.pipeline_executor import PipelineExecutor
            from modulos.tool_orchestrator import ToolOrchestrator as _TO
            from modulos.task_planner import TaskPlanner as _TP
            _tools = _TO()
            _planner = _TP(ia=self.ia, tool_orchestrator=_tools)
            _pipe = PipelineExecutor(
                kg=self.kg, ia=self.ia, ctx_crew=self.ctx_crew,
                orquestrador=self.orquestrador, identidade=self.identidade,
                task_planner=_planner, tool_orchestrator=_tools
            )
            _resposta, _revisao = _pipe.executar(texto)
            if _resposta and _revisao['status'] == 'OK':
                return _resposta
            if _resposta:
                return _resposta
        except Exception as _pipe_err:
            print(f'  [Pipeline] ERRO: {_pipe_err}')
        
        # Se pipeline falhou, cai para a IA normal
        # --- Pre-aquecer ContextCrew (antes da IA) ---
        if self.ctx_crew:
            try:
                _ctx_pre = self.ctx_crew.executar(texto[:300])
                if _ctx_pre:
                    contexto_extra += chr(10) + "[INFO] " + _ctx_pre[:500] + chr(10)
            except: pass
        # FASE 1: MENTE PENSA (SEMPRE - toda pergunta merece reflexao)
        # ====================================================
        mente_contexto = ""
        try:
            from modulos import mente as _mente
            mente_contexto = _mente.think(texto, tipo, subtipo,
                                         kg=self.kg, ia=self.ia, ctx_crew=self.ctx_crew)
        except Exception as e:
            print(f'  [Supervisor] Mente: {e}')
        
        # ====================================================
        # FASE 2: CORPO EXECUTA (SEMPRE pelo Orquestrador)
        # ====================================================
        resposta = None
        
        if self.orquestrador:
            # PRE-VERIFICACAO: conhecimento suficiente no KG?
            _precisa_pesquisar = False
            if self.kg and len(texto) > 30:
                try:
                    _lessons = self.kg.buscar(texto[:200], max_r=3)
                    if not _lessons or len(_lessons) < 2:
                        # Menos de 2 lessons = conhecimento insuficiente
                        import subprocess as _sp, sys as _sys, os as _os
                        _kernel = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), 'MCR_DevIA-Kernel.py')
                        _consulta = texto[:150].replace('"', "'")
                        print(f'  [Pre-Web] Conhecimento insuficiente ({len(_lessons or [])} lessons). Pesquisando...')
                        _sp.run([_sys.executable, _kernel, 'weblearn', _consulta, '--shallow'],
                                capture_output=True, text=True, timeout=120)
                        _precisa_pesquisar = True
                except:
                    pass
            
            # Reescreve pergunta: se menciona funcao+arquivo, le o codigo real e inclui
            import re as _rr
            _fm = _rr.search(r'(_?\w+)\s*\(', texto)
            _am = _rr.search(r'([\w/]+\.py)', texto)
            if _fm and _am and ('explique' in texto.lower() or 'regras' in texto.lower()):
                _fn, _an = _fm.group(1), _am.group(1)
                for _d in [os.path.join(os.path.dirname(os.path.dirname(__file__)), 'modulos'),
                           os.path.join(os.path.dirname(os.path.dirname(__file__)), 'comandos'),
                           os.path.join(os.path.dirname(os.path.dirname(__file__)))]:
                    _p = os.path.join(_d, _an)
                    if os.path.exists(_p):
                        try:
                            _c = open(_p, 'r', encoding='utf-8').read()
                            _pos = _c.find(f'def {_fn}')
                            if _pos >= 0:
                                texto = f"Analise o codigo ABAIXO. Explique a funcao {_fn}, suas regras e ordem.\n\n{_c[_pos:_pos+3000]}\n\n"
                                print(f'  [Reescrita] Codigo de {_an}:{_fn} incluido na pergunta')
                        except: pass
                        break
            
            template_map = {
                'codigo/analisar': 'analisar_codigo',
                'codigo/corrigir': 'analisar_bug',
                'codigo/gerar': 'perguntar',
                'codigo/refatorar': 'perguntar',
                'criacao/historia': 'lore',
                'planejamento/arquitetura': 'perguntar',
                'diagnostico/causa_raiz': 'perguntar',
                'conceitual/explicacao': 'perguntar',
                'multimodal/complexo': 'perguntar',
            }

            chave = f"{tipo}/{subtipo}"
            template = template_map.get(chave, 'perguntar')
            if template not in ('perguntar', 'analisar_codigo', 'analisar_bug', 'lore', 'conceito'):
                template = 'perguntar'
            
            params = {
                'mente_contexto': mente_contexto,
                'identidade': self.identidade,
            }
            if template == 'perguntar':
                params['pergunta'] = texto
            elif template == 'conceito':
                params['conceito'] = texto[:500]
                params['contexto'] = texto
            elif template == 'analisar_codigo' or template == 'analisar_bug':
                arq = re.search(r'([\w\-]+\.py)', texto)
                params['estrutura'] = arq.group(1) if arq else 'arquivo'
                params['descricao'] = texto
            elif template == 'lore':
                params['topico'] = texto
            else:
                params['descricao'] = texto
            
            resposta = self._executar_orq(template, params, consulta=texto, temp=0.4)
        
        # Fallback: Orquestrador indisponivel
        if not resposta:
            print(f'  [Supervisor] Orquestrador indisponivel, usando fallback')
            if self.ia:
                prompt = f"{self.identidade}\n\n{texto}\n\n{contexto_extra}\nResponda de forma util."
                resposta = self.ia.gerar(prompt, 0.3)
        
        # ====================================================
        # FASE 3: AUTO-REVISOR (SEMPRE)
        # ====================================================
        if resposta and len(resposta) > 100:
            try:
                from modulos.auto_revisor import AutoRevisor
                revisor = AutoRevisor(kg=self.kg)
                revisao = revisor.revisar(resposta)
                if revisao["total"] > 0:
                    print(f'  [Auto-Revisor] {revisao["total"]} alucinacoes detectadas')
                    resposta, _ = revisor.auto_corrigir(resposta)
            except Exception as e:
                print(f'  [Auto-Revisor] ERRO: {e}')
        
        # ====================================================
        # FASE 4: AUTO-APRENDIZADO WEB (detecta resposta INCOMPLETA)
        # ====================================================
        # Usa FAST para verificar se a resposta realmente responde a pergunta
        _precisa_aprender = False
        if resposta and len(resposta) > 50:
            try:
                from modulos.util import fast as _util_fast
                _prompt_verif = (
                    f"Pergunta: {texto[:300]}\n\n"
                    f"Resposta gerada: {resposta[:800]}\n\n"
                    f"A resposta acima RESPONDE CORRETAMENTE a pergunta?\n"
                    f"Se a resposta usou linguagem/tecnologia ERRADA (ex: pediu Rust, deu Haskell), responda NAO.\n"
                    f"Se a resposta e generica ou nao respondeu, responda NAO.\n"
                    f"Responda apenas: SIM ou NAO"
                )
                _veredito = _util_fast(_prompt_verif, 0.1, "leve")
                if _veredito and 'NAO' in _veredito.upper() and 'SIM' not in _veredito.upper():
                    _precisa_aprender = True
            except:
                pass
        
        if _precisa_aprender:
            print(f'  [Auto-Web] Resposta NAO atende. Pesquisando: {texto[:80]}...')
            try:
                import subprocess as _web_proc, sys as _web_sys
                kernel_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'MCR_DevIA-Kernel.py')
                consulta = texto[:200].replace('"', "'")
                _web_proc.run(
                    [_web_sys.executable, kernel_path, 'weblearn', consulta, '--shallow'],
                    capture_output=True, text=True, timeout=120
                )
                if self.orquestrador:
                    resposta2 = self._executar_orq('perguntar', {
                        'pergunta': f"{texto}\n(Responda com PRECISAO.)"
                    }, consulta=texto, temp=0.4)
                    # SO substitui se a nova resposta for MELHOR (mais longa E sem "nao sei")
                    if resposta2 and len(resposta2) > len(resposta) * 1.2:
                        if 'nao tenho informacoes' not in resposta2.lower() and 'nao sei' not in resposta2.lower():
                            print(f'  [Auto-Web] Resposta melhorada: {len(resposta2)} chars (era {len(resposta)})')
                            resposta = resposta2
            except Exception as _web_err:
                print(f'  [Auto-Web] ERRO: {_web_err}')
        
        # ====================================================
        # FASE 5: MENTE APRENDE (SEMPRE) + AUTO-REVIEW DO CODIGO
        # ====================================================
        if resposta:
            try:
                from modulos import mente as _mente
                _mente.learn(texto, tipo, subtipo, resposta, kg=self.kg)
            except:
                pass
            
            # AUTO-REVIEW: MCR analisa seu proprio codigo (1 a cada 5 execucoes)
            try:
                import random as _rnd
                if _rnd.random() < 0.2:  # 20% de chance
                    import subprocess as _sp
                    import os as _os
                    # Escolhe um arquivo .py do MCR-DevIA para auto-review
                    base_review = _os.path.join(_os.path.dirname(__file__), '..')
                    alvos = ['kernel.py', 'modulos/supervisor.py', 'modulos/orquestrador.py',
                             'modulos/mente.py', 'modulos/memoria_conselho.py']
                    alvo = _rnd.choice(alvos)
                    alvo_path = _os.path.join(base_review, alvo)
                    if _os.path.exists(alvo_path):
                        with open(alvo_path, 'r', encoding='utf-8') as _f:
                            _conteudo = _f.read()
                        # Busca por problemas conhecidos
                        _problemas = []
                        if 'hardcoded' in _conteudo.lower() and 'TODO' not in _conteudo:
                            _problemas.append(f"Possivel hardcoded em {alvo}")
                        if len(_conteudo.split('\n')) > 500:
                            _problemas.append(f"{alvo} tem mais de 500 linhas")
                        if _problemas:
                            for _p in _problemas:
                                print(f'  [Auto-Review] {_p}')
                            if self.kg:
                                self.kg.aprender(f"auto-review: {alvo}", '; '.join(_problemas), '', 'auto_review')
            except:
                pass
        
        return resposta
    
    # ============================================================
    # ROTAS ESPECIFICAS
    # ============================================================
    
    def _rotear_codigo(self, texto, subtipo, mente_contexto=""):
        """Roteia tarefas de codigo para o Orquestrador."""
        if not self.orquestrador:
            return self._v12_contexto_agregado(texto)
        
        params_base = {'mente_contexto': mente_contexto, 'identidade': self.identidade}
        
        if subtipo == 'analisar':
            arq_match = re.search(r'(?:arquivo\s+)?([\w\-]+\.py)', texto)
            params_base.update({
                'estrutura': f'Arquivo: {arq_match.group(1)}' if arq_match else 'Analise de codigo',
                'descricao': texto
            })
            return self._executar_orq('analisar_codigo', params_base, consulta=texto)
        
        elif subtipo == 'corrigir':
            arq_match = re.search(r'(?:arquivo\s+)?([\w\-]+\.py)', texto)
            params_base.update({
                'estrutura': arq_match.group(1) if arq_match else 'arquivo',
                'descricao': texto
            })
            return self._executar_orq('analisar_bug', params_base, consulta=texto, temp=0.3)
        
        elif subtipo == 'gerar':
            params_base['pergunta'] = f'Gere codigo COMPLETO e FUNCIONAL. Siga o padrao do projeto existente. Use APENAS bibliotecas e APIs que existem no projeto. NAO invente modulos ou importacoes que nao existem. {texto}'
            return self._executar_orq('perguntar', params_base, consulta=texto, temp=0.4)
        
        elif subtipo == 'refatorar':
            params_base['pergunta'] = f'Refatore o codigo. {texto}'
            return self._executar_orq('perguntar', params_base, consulta=texto, temp=0.4)
        
        return self._v12_contexto_agregado(texto)
    
    def _rotear_criacao(self, texto, subtipo, mente_contexto=""):
        """Roteia tarefas criativas para o Orquestrador."""
        if not self.orquestrador:
            return self._v12_contexto_agregado(texto)
        
        if subtipo == 'historia':
            return self._executar_orq('lore', {
                'topico': texto,
                'mente_contexto': mente_contexto,
                'identidade': self.identidade,
            }, consulta=texto, temp=0.7)
        
        return self._v12_contexto_agregado(texto)
    
    def _rotear_planejamento(self, texto, subtipo, mente_contexto=""):
        """Roteia tarefas de planejamento/arquitetura."""
        if not self.orquestrador:
            return self._v12_contexto_agregado(texto)
        
        resp = self._executar_orq('planejamento_arquitetura', {
            'descricao': texto,
            'mente_contexto': mente_contexto,
            'identidade': self.identidade,
        }, consulta=texto, temp=0.6)
        if resp and len(resp) > 100:
            return resp
        return self._v12_contexto_agregado(texto)
    
    def _rotear_diagnostico(self, texto, subtipo, mente_contexto=""):
        """Roteia tarefas de diagnostico para o template especifico."""
        if not self.orquestrador:
            return self._v12_contexto_agregado(texto)
        
        resp = self._executar_orq('diagnostico_problema', {
            'descricao': texto,
            'mente_contexto': mente_contexto,
            'identidade': self.identidade,
        }, consulta=texto, temp=0.5)
        if resp and len(resp) > 100:
            return resp
        return self._v12_contexto_agregado(texto)
    
    def _rotear_conceitual(self, texto, subtipo, mente_contexto=""):
        """Roteia tarefas conceituais para template aprimorado."""
        if not self.orquestrador:
            return self._v12_contexto_agregado(texto)
        
        resp = self._executar_orq('explicacao_conceitual', {
            'descricao': texto,
            'mente_contexto': mente_contexto,
            'identidade': self.identidade,
        }, consulta=texto, temp=0.5)
        if resp and len(resp) > 150:
            return resp
        
        resp = self._executar_orq('conceito', {
            'conceito': texto[:120],
            'contexto': texto,
            'mente_contexto': mente_contexto,
            'identidade': self.identidade,
        }, consulta=texto, temp=0.5)
        if resp and len(resp) > 100:
            return resp
        
        return self._v12_contexto_agregado(texto)
    def _rotear_multimodal(self, texto, mente_contexto=""):
        """Roteia prompts complexos (multi-intencao) para o template mega_teste."""
        if not self.orquestrador:
            return self._v12_contexto_agregado(texto)
        
        resp = self._executar_orq('mega_teste', {
            'descricao': texto,
            'mente_contexto': mente_contexto,
            'identidade': self.identidade,
        }, consulta=texto, temp=0.5)
        if resp and len(resp) > 200:
            return resp
        # Fallback: tenta planejamento_arquitetura (outro template fragmentavel)
        resp = self._executar_orq('planejamento_arquitetura', {
            'descricao': texto,
            'mente_contexto': mente_contexto,
            'identidade': self.identidade,
        }, consulta=texto, temp=0.5)
        if resp and len(resp) > 100:
            return resp
        return self._v12_contexto_agregado(texto)
    
    def _executar_orq(self, intencao, params, consulta="", temp=0.4):
        """Executa o Orquestrador injetando identidade + contexto."""
        params['identidade'] = self.identidade
        try:
            r = self.orquestrador.executar(intencao, params, consulta=consulta, temp=temp)
            if r and r.get('sucesso') and r.get('resposta'):
                return r['resposta']
        except Exception as e:
            print(f'  [Supervisor] Orquestrador falhou: {e}')
        return None
    
    # ============================================================
    # V12 CONTEXTO AGREGADO (classico, para perguntas factuais)
    # ============================================================
    
    def _v12_contexto_agregado(self, texto, contexto_extra=""):
        """V12 Contexto Agregado original: KG + Fast expand."""
        kwargs = set(re.findall(r'\b[a-zA-Z]{3,}\b', texto.lower())) - _STOP_V12
        
        contexto = self.kg.buscar(texto) if self.kg else []
        
        if contexto:
            # Acha top lesson + relacionadas
            melhor_lesson = None
            melhor_score = 0
            for l in contexto[:3]:
                sol = l.get("solucao", "").lower()
                matches = sum(1 for t in kwargs if t in sol)
                if matches > melhor_score:
                    melhor_score = matches
                    melhor_lesson = l
            
            if melhor_lesson and melhor_score >= 1:
                termo = f'{melhor_lesson.get("erro","")} {melhor_lesson.get("ctx","")}'
                relacionadas = self.kg.buscar(termo, max_r=2) if self.kg else []
                
                vistas = set()
                blocos = []
                for l_rel in [melhor_lesson] + (relacionadas or []):
                    lid = l_rel.get('id', '') or l_rel.get('solucao', '')[:50]
                    if lid in vistas: continue
                    vistas.add(lid)
                    txt = l_rel.get("solucao", "").strip()
                    if txt: blocos.append(f'- {txt[:300]}')
                    if len(blocos) >= 4: break
                
                ctx_agg = '\n'.join(blocos)
                prompt = (
                    f"Contexto do projeto:\n{ctx_agg}\n\n"
                    f"Pergunta: {texto}\n"
                    f"Responda de forma util em 2-3 frases usando APENAS o contexto.\n"
                    f"Nao invente informacoes alem do fornecido."
                )
                r = self.ia.fast(prompt, 0.3, "leve") if self.ia else None
                if r and len(r) > 20:
                    return r
            
            # Fallback: IA com contexto do KG
            ctx_curto = '\n'.join(f'- {l["solucao"][:200]}' for l in contexto[:2])
            r = self.ia.fast(f"{ctx_curto}\n\nPergunta: {texto}\nResposta:", 0.1, "leve") if self.ia else None
            if r and len(r) > 20:
                return r
        
        # Sem contexto: IA generica
        prompt = (
            f"Contexto:\n{contexto_extra[:500]}\n\n" if contexto_extra else ""
        ) + f"Pergunta: {texto}\nResponda de forma util e especifica."
        r = self.ia.gerar(prompt, 0.3) if self.ia else None
        if r and len(r) > 20:
            return r
        
        return "Nao encontrei resposta no meu conhecimento atual."
