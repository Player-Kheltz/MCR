"""MasterAgent — Agente universal que faz QUALQUER coisa.

Ciclo: PERCEBER -> PLANEJAR -> EXECUTAR -> INTEGRAR -> APRENDER

Recebe QUALQUER request e:
1. Percebe o que e (TaskAnalyzer + memorias + KG)
2. Planeja subtarefas (TaskPlanner)
3. Executa cada subtarefa (ToolOrchestrator + IA)
4. Integra resultados (compila artefato final)
5. Aprende com o processo (EpisodicMemory + KG)

Uso:
    agent = MasterAgent()
    resultado = agent.executar("Cria um jogo de plataforma em Python com 3 fases")
    # -> Projeto completo com codigo e instrucoes
"""
import os, sys, json, time, re, random, hashlib
try:
    from mcr.conselho_multi import tree_of_thought
except ImportError:
    try:
        from mcr.modules.conselho import tree_of_thought
    except ImportError:
        from mcr.conselho_multi import tree_of_thought
try:
    from context_crew import ContextCrew
except ImportError:
    ContextCrew = None
try:
    from context_infinity import SessionCache
except ImportError:
    SessionCache = None
import re as _re
from typing import Dict, List, Optional

try:
    from mcr.sse_server import emit
except ImportError:
    emit = lambda *a, **kw: None

# Caminhos
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia'))

from mcr.episodic_memory import EpisodicMemory
from mcr.task_planner import TaskPlanner, PlanValidator
from mcr.tool_orchestrator import ToolOrchestrator
from mcr.sandbox_executor import SandboxExecutor
from mcr.ia import IA
from mcr.kg import KnowledgeGraph
try:
    from context_infinity import SessionCache
except ImportError:
    SessionCache = None
from mcr.enricher import Enricher  # atalho para Conselho (fundido)
from mcr.emergir import EmergirEngine  # EMERGIR V4
from mcr.self_study import SelfStudyEngine  # Self-Study
from mcr.task_executor import TaskExecutor  # Execucao de subtarefas


class MasterAgent:
    """Agente universal. Faz QUALQUER coisa."""

    def __init__(self):
        self.ia = IA()
        self.kg = KnowledgeGraph()
        self.memoria = EpisodicMemory()
        self.tools = ToolOrchestrator()
        self.planner = TaskPlanner(tools_orchestrator=self.tools, ia=self.ia)
        self.sandbox = SandboxExecutor()
        self._passos = []
        self._execution_count = 0  # G10: contador para auto-diagnostico
        self._buffer_episodios = []  # J2: buffer para registro em lote
        self._identity_base_cache = None  # lazy load docs/AGENT_IDENTITY.md
        self._combinacoes_feitas = set()  # fingerprints de combinacoes emergentes ja tentadas
        # Motores especializados (modularizacao)
        self.emergir = EmergirEngine(
            ia=self.ia, kg=self.kg,
            log_callback=self._log,
            execution_count_getter=lambda: getattr(self, '_execution_count', 0),
        )
        self.self_study = SelfStudyEngine(
            ia=self.ia, kg=self.kg,
            log_callback=self._log,
            execution_count_getter=lambda: getattr(self, '_execution_count', 0),
        )
        self.task_executor = TaskExecutor(
            ia=self.ia, tools=self.tools, sandbox=self.sandbox,
            ask_user_callback=self._ask_user,
            log_callback=self._log,
            identity_base_callback=self._get_identity_base,
            identity_tarefa_callback=self._buscar_identity_tarefa,
        )

    def autoavaliar(self, request):
        """Autoavaliacao: o sistema sabe o que sabe e o que nao sabe.
        
        AGI: consciencia dos proprios limites antes de agir.
        Retorna dict com confianca, gaps, e acao sugerida.
        """
        lessons = self.kg.buscar(request, max_r=3)
        lessons_sem = []
        try:
            if hasattr(self.kg, 'buscar_por_embedding'):
                lessons_sem = self.kg.buscar_por_embedding(request, n=2)
        except Exception:
            pass
        total_conhecimento = len(lessons) + len(lessons_sem)
        experiencias = self.memoria.buscar(request, n=3)
        n_exp = len(experiencias)
        tx_suc = sum(1 for e in experiencias if e.get('sucesso')) / max(n_exp, 1)

        if total_conhecimento >= 3 and n_exp >= 2 and tx_suc >= 0.7:
            return {'confianca': 'alta', 'gaps': [], 'acao': 'executar'}
        if total_conhecimento >= 1:
            gaps = []
            if n_exp < 2:
                gaps.append('pouca experiencia pratica')
            if total_conhecimento < 3:
                gaps.append('conhecimento teorico limitado')
            return {'confianca': 'media', 'gaps': gaps, 'acao': 'executar_com_cautela'}
        return {
            'confianca': 'baixa',
            'gaps': ['nenhum conhecimento previo no KG'],
            'acao': 'estudar_antes'
        }

    def _buscar_sabedoria(self, request, max_lessons=5):
        """Busca conhecimento no KG como fonte principal de sabedoria.
        
        Usa TANTO keyword (rapido, preciso) QUANTO embedding (semantico)
        para maxima cobertura do conhecimento disponivel.
        """
        lessons = []
        seen_ids = set()
        
        # Keyword match
        try:
            for l in self.kg.buscar(request, max_r=max_lessons):
                lid = l.get('id', '')
                if lid not in seen_ids:
                    lessons.append(l)
                    seen_ids.add(lid)
        except Exception:
            pass
        
        # Embedding match (semantico)
        try:
            if hasattr(self.kg, 'buscar_por_embedding'):
                for l in self.kg.buscar_por_embedding(request, n=max_lessons):
                    lid = l.get('id', '')
                    if lid not in seen_ids:
                        lessons.append(l)
                        seen_ids.add(lid)
        except Exception:
            pass
        
        return lessons

    def _get_identity_base(self):
        """Carrega docs/AGENT_IDENTITY.md (1 vez, lazy).
        
        Retorna string com identidade base do MasterAgent,
        ou '' se o arquivo nao existir.
        """
        if self._identity_base_cache is None:
            path = os.path.join(BASE, 'docs', 'AGENT_IDENTITY.md')
            try:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        self._identity_base_cache = f.read().strip()
                else:
                    self._identity_base_cache = ''
            except Exception:
                self._identity_base_cache = ''
        return self._identity_base_cache

    def _buscar_identity_tarefa(self, task_type, request=''):
        """Busca identidade pra tarefa: SessionCache L1 → V12 KG L2 → FAST L3 → auto-cache.
        
        Args:
            task_type: Tipo da tarefa (ex: 'pesquisa_web', 'criar_codigo')
            request: Request original (contexto pro FAST fallback)
        
        Returns:
            str: Texto da identidade (vazio '' se nada funcionar)
        """
        if not task_type:
            return ''
        
        # ============================================================
        # L1: SessionCache (memoria da execucao atual, 0ms)
        # ============================================================
        ctx = getattr(self, 'ctx', None)
        if ctx is not None:
            try:
                cache = ctx.pescar(
                    pergunta=task_type,
                    tipos=['identity'],
                    max_tokens=500,
                    n=1
                )
                if cache and len(cache[0].conteudo) > 20:
                    self._log('IDENTITY', f'L1 (SessionCache): {task_type}')
                    return cache[0].conteudo
            except Exception:
                pass
        
        # ============================================================
        # L2: KG — V12 lookup filtrado por ctx='identity_tarefa'
        # ============================================================
        try:
            lessons = self.kg.buscar(task_type, max_r=5)
            melhor = None
            melhor_score = 0
            palavras = set(re.findall(r'\w+', task_type.lower()))
            
            for l in lessons:
                if l.get('ctx') != 'identity_tarefa':
                    continue
                score = sum(1 for p in palavras 
                           if p in l.get('erro', '').lower() and len(p) >= 3)
                if score > melhor_score:
                    melhor_score = score
                    melhor = l
            
            if melhor and palavras:
                confidence = melhor_score / max(len(palavras), 1)
                if confidence >= 0.7:
                    self._log('IDENTITY', f'L2 (V12 KG): {task_type} '
                              f'(confidence={confidence:.0%})')
                    # Cacheia em SessionCache pra L1 pegar depois
                    if ctx is not None:
                        try:
                            ctx.absorver(
                                f'identity_{task_type}',
                                melhor['solucao'],
                                tipo='identity',
                                tags=['identity', task_type],
                                origem='v12_kg'
                            )
                        except Exception:
                            pass
                    return melhor['solucao']
        except Exception:
            pass
        
        # ============================================================
        # L3: FAST — gera identity sob demanda via Decider.extrair_json
        # ============================================================
        try:
            from mcr.decider import Decider
            decider = Decider(self.ia)
            
            exemplos = [
                ("pesquisa_web", {
                    "identity": (
                        "Seu papel: relator de pesquisa.\n"
                        "Contexto web REAL foi fornecido.\n"
                        "USE os dados do contexto. NAO crie codigo.\n"
                        "Responda em PT-BR com relatorio conciso."
                    )
                }),
                ("criar_codigo", {
                    "identity": (
                        "Seu papel: gerador de codigo.\n"
                        "Crie codigo funcional e bem estruturado.\n"
                        "Responda APENAS com o codigo, sem explicacoes.\n"
                        "Comentarios em portugues."
                    )
                }),
            ]
            
            dados = decider.extrair_json(
                texto=f"task_type: {task_type}\nrequest: {request}",
                esquema_exemplo={"identity": ""},
                instrucao=(
                    "Gere uma identidade/instrucao de papel para o modelo de IA "
                    "baseado no tipo de tarefa. A identity deve ter 2-5 linhas "
                    "dizendo claramente o que o modelo DEVE fazer e NAO DEVE fazer."
                ),
                exemplos=exemplos
            )
            
            identity = dados.get('identity', '').strip()
            if identity and len(identity) > 20:
                # AUTO-CACHE: salva no KG pra V12 pegar na proxima
                try:
                    self.kg.aprender(
                        erro=task_type,
                        causa=f'Identity gerada via FAST para tarefa {task_type}',
                        solucao=identity,
                        ctx='identity_tarefa'
                    )
                    self._log('IDENTITY', f'L3 (FAST): {task_type} — cacheado no KG')
                except Exception:
                    pass
                
                # Cacheia em SessionCache tambem
                if ctx is not None:
                    try:
                        ctx.absorver(
                            f'identity_{task_type}',
                            identity,
                            tipo='identity',
                            tags=['identity', task_type],
                            origem='fast'
                        )
                    except Exception:
                        pass
                
                return identity
        except Exception as e:
            self._log('IDENTITY', f'L3 (FAST) falhou: {e}')
        
        return ''

    def _buscar_hierarquico(self, pergunta):
        """Busca em 3 niveis ate encontrar resposta satisfatoria.
        
        Nivel 1 — LOCAL: SessionCache → KG → ContextCrew
        Nivel 2 — WEBLEARN: pesquisas web anteriores (cache local)
        Nivel 3 — WEB: DuckDuckGo ao vivo + Wikipedia fallback
        """
        resultados = []
        seen_textos = set()
        
        def _add(texto, limite=300):
            t = str(texto)
            if t and t not in seen_textos:
                seen_textos.add(t)
                resultados.append(t)
        
        # NIVEL 1: LOCAL — SessionCache
        try:
            if hasattr(self, 'ctx'):
                cache = self.ctx.pescar(pergunta=pergunta, tipos=['contexto', 'codigo'],
                                         max_tokens=1000, n=5)
                for c in cache:
                    _add(c.conteudo)
        except Exception:
            pass
        if len(resultados) >= 3:
            return resultados
        
        # NIVEL 1: LOCAL — KG sabedoria
        for l in self._buscar_sabedoria(pergunta, 3):
            _add(l.get('solucao', ''))
        if len(resultados) >= 3:
            return resultados
        
        # NIVEL 1: LOCAL — ContextCrew
        try:
            from context_crew import ContextCrew
            for texto, fonte in ContextCrew().buscar(pergunta, max_r=2):
                _add(texto)
        except Exception:
            pass
        if len(resultados) >= 3:
            return resultados
        
        # NIVEL 2: WEBLEARN (cache local de pesquisas anteriores)
        try:
            wl_dir = os.path.join(BASE, 'sandbox', '.mcr_devia', 'weblearn')
            if os.path.exists(wl_dir):
                termos = set(pergunta.lower().split())
                for f in sorted(os.listdir(wl_dir)):
                    if not f.endswith('.json') or f.startswith('.'):
                        continue
                    try:
                        with open(os.path.join(wl_dir, f), 'r', encoding='utf-8') as fh:
                            item = json.load(fh)
                        txt = str(item.get('texto', '')) or str(item.get('conteudo', ''))
                        if any(t in txt.lower() for t in termos if len(t) > 3):
                            _add(txt)
                            if len(resultados) >= 3:
                                return resultados
                    except Exception:
                        pass
        except Exception:
            pass
        
        # NIVEL 3: WEB AO VIVO
        try:
            web = self.ia.buscar_web(pergunta, max_resultados=3)
            if web:
                _add(web, 500)
        except Exception:
            pass
        
        return resultados if resultados else []

    def _feedback(self, request, tipo_porte, plano, resultados):
        """Feedback do resultado para ajustar decisoes futuras.
        
        Backpropagation: erro na saida ajusta camadas anteriores.
        Se a execucao falhou muito, registra licao de 'o que nao fazer'.
        """
        sucesso = all(r.get('sucesso', False) for r in resultados.values())
        if sucesso:
            return
        n_ok = sum(1 for r in resultados.values() if r.get('sucesso'))
        n_total = len(plano)
        if n_total > 0 and n_ok < n_total * 0.5:
            licao = (f"FRACASSO: {n_ok}/{n_total} subtarefas para "
                     f"'{request}'. Tipo classificado como "
                     f"'{tipo_porte}' parece incorreto.")
            self.kg.aprender(
                erro=f"Feedback: {request}",
                causa=f"tipo={tipo_porte} | sucesso={n_ok}/{n_total}",
                solucao=licao,
                ctx='feedback_fracasso'
            )

    def executar(self, request, task_type=''):
        """Executa QUALQUER request.

        Args:
            request: O que fazer (ex: "cria um mod BG3 com espada de fogo")
            task_type: Tipo de tarefa (se conhecido, opcional)

        Returns:
            Dict com resultado final e artefatos gerados
        """
        t0 = time.time()
        self._passos = []

        # === CONTEXT INFINITY (SessionCache) ===
        self.ctx = SessionCache()
        # PRÉ-CARREGA conhecimento relevante ANTES de qualquer passo
        try:
            n_pre = self.ctx.precarregar(kg=self.kg, request=request,
                                          memorias=self.memoria.buscar(request, 3))
            if n_pre > 0:
                self._log('SABEDORIA', f'Pre-carregados {n_pre} fragmentos do KG/memoria')
        except Exception as e:
            self._log('SABEDORIA', f'Pre-carregamento: {e}')
        self.ctx.absorver('request', request, 'request', tags=['request', task_type or 'geral'], origem='usuario')

        self._log('PERCEBER', f'Request: {request}')

        # === METACOGNICAO (AGI) ===
        try:
            avaliacao = self.autoavaliar(request)
            if avaliacao['confianca'] != 'alta':
                self._log('METACOG', f'Confianca {avaliacao["confianca"]}: {", ".join(avaliacao["gaps"])}')
        except Exception:
            pass

        # === 1. PERCEBER ===
        # Buscar experiencias similares
        memorias = self.memoria.buscar(request, 3)
        if memorias:
            self._log('PERCEBER', f'Encontradas {len(memorias)} experiencias similares')
            self.ctx.absorver('memorias', str(memorias), 'contexto', tags=['memoria'], origem='episodic_memory')
            for m in memorias:
                status = 'OK' if m.get('sucesso') else 'FALHA'
                self._log('PERCEBER', f"  -> {m['request']} ({status})")

        # Buscar conhecimento relevante
        lessons = self.kg.buscar(request, max_r=3)
        if lessons:
            self._log('PERCEBER', f'Encontradas {len(lessons)} licoes no KG')
            self.ctx.absorver('kg_lessons', str(lessons), 'contexto', tags=['kg'], origem='kg')

        # === 1.5 PAUSE-AND-ASK (projetos grandes) ===
        # Usa Decider para classificar o porte do projeto
        projeto_grande = False
        request_ambiguo = False
        tipo_porte = 'simples'
        try:
            from mcr.decider import Decider
            decider = Decider(self.ia)
            exemplos_porte = [
                ("Cria um jogo de plataforma em Python com 3 fases", "projeto"),
                ("Cria um site em HTML com CSS", "projeto"),
                ("Cria um script que imprime hello", "simples"),
                ("O que e SPA no MCR?", "simples"),
                ("faz um joguinho", "projeto"),
            ]
            tipo_porte = decider.classificar(
                request, ['simples', 'projeto'],
                exemplos=exemplos_porte,
                instrucao="'jogo'/'game'/'projeto'/'site' = projeto. 'script'/'funcao'/'o que' = simples."
            )
            projeto_grande = tipo_porte == 'projeto'
            request_ambiguo = projeto_grande and len(request) < 60
        except Exception:
            pass
            # Fallback: regex
            projeto_grande = any(p in request.lower() for p in ['jogo', 'game', 'projeto', 'site'])
            request_ambiguo = len(request) < 60 and projeto_grande

        if projeto_grande:
            from mcr.util import extrair_nome_projeto
            nome_proj = extrair_nome_projeto(request)
            resposta = self._ask_user(
                f"Vou criar o projeto '{nome_proj}' com src/, 4 modulos "
                f"(main, entities, phases, utils), requirements.txt e run.bat. Posso prosseguir?",
                opcoes=['sim', 'nao', 'modificar']
            )
            if resposta == 'nao':
                return {'sucesso': False, 'request': request,
                        'artefato': {'resposta_final': 'Cancelado pelo usuario'},
                        'n_subtarefas': 0, 'n_sucesso': 0, 'tempo': 0}
            if resposta == 'modificar' or request_ambiguo:
                engine = self._ask_user(
                    "Qual engine usar? (recomendo: pygame)",
                    opcoes=['pygame', 'phaser', 'love2d', 'nenhum']
                )
                if engine not in ('pygame', 'nenhum'):
                    request = f"{request} (usando {engine})"

        # === 2. PLANEJAR ===
        self._log('PLANEJAR', 'Criando plano de execucao...')
        plano = self.planner.planejar(request, task_type)
        self._log('PLANEJAR', f'Plano: {len(plano)} subtarefas')
        self.ctx.absorver('plano', json.dumps([{'id': p['id'], 'acao': p['acao'], 'desc': p['descricao']} for p in plano]),
                          'plano', tags=['plano', task_type or 'geral'], origem='planner')

        for p in plano:
            self._log('PLANEJAR', f'  {p["id"]}. {p["acao"]} - {p["descricao"]}')

        # === 3. EXECUTAR ===
        self._log('EXECUTAR', f'Iniciando execucao de {len(plano)} subtarefas...')
        resultados = {}
        artefatos = {}  # artefatos gerados por tipo ('codigo', 'npc', etc)

        for subtarefa in plano:
            self._log('EXECUTAR', f'  Subtarefa {subtarefa["id"]}: {subtarefa["acao"]}')

            # Verificar dependencias
            dependencias_ok = all(
                dep in resultados and resultados[dep].get('sucesso', False)
                for dep in subtarefa.get('depende_de', [])
            )
            if not dependencias_ok:
                self._log('EXECUTAR', f'  -> Dependencias nao satisfeitas, pulando')
                resultados[subtarefa['id']] = {'sucesso': False, 'erro': 'Dependencias nao satisfeitas'}
                continue

            # PESCA contexto relevante do SessionCache para esta subtarefa
            # Usa params['pergunta'] se disponivel (contem o request original),
            # senao usa a descricao do template
            ctx_query = subtarefa.get('params', {}).get('pergunta') or subtarefa.get('params', {}).get('consulta') or subtarefa['descricao']
            ctx_passo = self.ctx.pescar(
                pergunta=ctx_query,
                tipos=['codigo', 'request', 'plano', 'resultado', 'contexto'],
                max_tokens=500
            )
            ctx_passo_str = str([c.conteudo for c in ctx_passo]) if ctx_passo else ''

            # Herdar resultado do passo que gerou codigo (nao o de validacao)
            codigo_anterior = artefatos.get('codigo_gerado')

            # Executar com contexto enriquecido do SessionCache
            contexto_extra_passo = ctx_passo_str if ctx_passo_str else ''
            
            resultado = self._executar_subtarefa(subtarefa, artefatos=artefatos, 
                                                  contexto_extra=contexto_extra_passo,
                                                  codigo_anterior=codigo_anterior)
            resultados[subtarefa['id']] = resultado

            # ABSORVE resultado no SessionCache
            acao_atual = subtarefa.get('acao', '')
            res = resultado.get('resultado', '')
            if isinstance(res, str) and len(res) > 20:
                tags_resultado = [acao_atual, task_type or 'geral']
                tags_resultado.append('sucesso' if resultado.get('sucesso') else 'falha')
                self.ctx.absorver(
                    f'passo_{subtarefa["id"]}_{acao_atual}',
                    res,
                    tipo='codigo' if 'gerar_' in acao_atual else 'resultado',
                    tags=tags_resultado,
                    origem=f'executor:{acao_atual}'
                )

            # Se gerou codigo, armazena como artefato
            if resultado.get('sucesso'):
                if isinstance(res, dict) and res.get('codigo'):
                    # NPCGenerator/gerar_npc retorna dict com campo 'codigo'
                    artefatos['codigo_gerado'] = res['codigo']
                    for k in ['arquivo', 'nome', 'tipo']:
                        if k in res:
                            artefatos[f'npc_{k}'] = res[k]
                elif isinstance(res, str) and len(res) > 50:
                    if 'gerar_modulo' in acao_atual:
                        nome_mod = acao_atual.replace('gerar_modulo_', '')
                        artefatos[f'modulo_{nome_mod}'] = res
                    elif acao_atual == 'gerar_codigo':
                        artefatos['codigo_gerado'] = res

            # Se falhou, tenta busca HIERARQUICA (local → weblearn → web)
            if not resultado.get('sucesso') and resultado.get('erro'):
                self._log('EXECUTAR', f'  -> Falhou: {str(resultado.get("erro",""))}. Busca hierarquica...')
                contexto_ajuda = self._buscar_hierarquico(
                    f"Como resolver: {subtarefa.get('descricao', request)}. "
                    f"Erro: {resultado.get('erro', '')}"
                )
                if contexto_ajuda:
                    contexto_ajuda_str = '\n'.join(str(c) for c in contexto_ajuda)
                    self.ctx.absorver(f'ajuda_{subtarefa["id"]}', contexto_ajuda_str,
                                      'contexto', tags=['ajuda'], origem='busca_hierarquica')
                    resultado_retry = self._executar_subtarefa(subtarefa, artefatos=artefatos,
                                       contexto_extra=contexto_ajuda_str, codigo_anterior=codigo_anterior)
                    if resultado_retry.get('sucesso'):
                        resultados[subtarefa['id']] = resultado_retry
                        origem = 'cache' if len(contexto_ajuda) < 3 else 'web'
                        self._log('EXECUTAR', f'  -> Busca hierarquica ({origem}) ajudou!')
                    else:
                        self._log('EXECUTAR', f'  -> Busca hierarquica nao foi suficiente')
                else:
                    self._log('EXECUTAR', f'  -> Nada encontrado na busca hierarquica')

        # === 4. INTEGRAR ===
        self._log('INTEGRAR', 'Integrando resultados...')
        artefato_final = self._integrar(request, plano, resultados)

        tempo_total = time.time() - t0
        sucesso_geral = all(
            r.get('sucesso', False) for r in resultados.values()
        )

        resultado_final = {
            'sucesso': sucesso_geral,
            'request': request,
            'artefato': artefato_final,
            'plano': [{'id': p['id'], 'acao': p['acao']} for p in plano],
            'resultados': resultados,
            'n_subtarefas': len(plano),
            'n_sucesso': sum(1 for r in resultados.values() if r.get('sucesso')),
            'tempo': round(tempo_total, 1),
            'passos': self._passos,
            'task_type': task_type or tipo_porte or 'geral',
        }

        # === 5. APRENDER ===
        licao = self._extrair_licao(request, plano, resultados)
        self._registrar_episodio(request, resultado_final, licao)
        self._aprender_kg(request, resultado_final, licao, task_type=task_type)

        # === 6. FEEDBACK (Backpropagation) ===
        self._feedback(request, tipo_porte, plano, resultados)

        # === 7. G11 — AUTO-REVISAO FINAL ===
        if artefato_final.get('resposta_final'):
            try:
                from mcr.auto_revisor import AutoRevisor
                revisor = AutoRevisor()
                revisao = revisor.revisar(artefato_final['resposta_final'])
                if revisao.get('problemas'):
                    self._log('REVISOR', f'{len(revisao["problemas"])} problemas encontrados')
            except Exception:
                pass

        self._log('APRENDER', f'Licao registrada: {licao}')
        self._log('FIM', f'Concluido em {tempo_total:.1f}s - '
                  f'{resultado_final["n_sucesso"]}/{len(plano)} subtarefas OK')

        # === 8. G10 — AUTO-DIAGNOSTICO PERIODICO (a cada 10 execucoes) ===
        self._execution_count += 1
        if self._execution_count % 10 == 0:
            try:
                from mcr.diagnostico import Diagnostico
                diag = Diagnostico()
                resultado_diag = diag.diagnosticar()
                score = resultado_diag.get('score', 0)
                self._log('DIAG', f'Auto-diagnostico: score {score}/100')
            except Exception:
                pass

        # === 9. FLUSH de buffers pendentes ===
        self._flush_episodios()

        # === 10. EMERGIR — reconhecimento automatico de padroes emergentes ===
        try:
            self._processar_emergencia()
        except Exception as e:
            self._log('EMERGIR', f'Erro: {e}')
        
        # === 11. SELF-STUDY — auto-conhecimento a cada 10 execucoes ===
        if getattr(self, '_execution_count', 0) % 10 == 0 and self._execution_count > 0:
            try:
                self._self_study()
            except Exception as e:
                self._log('SELF', f'Erro no auto-conhecimento: {e}')
        
        # === 12. AUTO-MELHORIA — loop AGI a cada 20 execucoes ===
        if getattr(self, '_execution_count', 0) % 20 == 0 and self._execution_count > 0:
            try:
                self._auto_melhorar()
            except Exception as e:
                self._log('AUTO', f'Erro na auto-melhoria: {e}')

        return resultado_final

    # ============================================================
    # EMERGIR — RECONHECIMENTO AUTOMATICO DE PADROES EMERGENTES
    # ============================================================
    # Maquina reconhece padroes → padroes existem em TUDO →
    # as vezes X+Y = Z (nao XY). Z e aprendido.
    # ============================================================

    # ============================================================
    # DELEGACAO: EMERGIR + SELF-STUDY (implementados em modulos/)
    # ============================================================

    def _processar_emergencia(self):
        """Delega para EmergirEngine.processar() (modulos/emergir.py)."""
        return self.emergir.processar()

    def _amostrar_topicos_distantes(self, n=3):
        return self.emergir.amostrar_topicos(n)

    def _gerar_fingerprint_combinacao(self, topicos):
        return self.emergir.gerar_fingerprint(topicos)

    def _gerar_pergunta_emergente(self, topicos):
        return self.emergir.gerar_pergunta(topicos)

    def _autoavaliar_padrao_novo(self, pergunta, resposta, topicos):
        return self.emergir.autoavaliar(pergunta, resposta, topicos)

    def _expandir_z_com_visao_critica(self, z_cru, pergunta, contexto_anterior):
        return self.emergir._expandir_z(z_cru, pergunta, contexto_anterior)

    def _gerar_emergencia_fragmentada(self, pergunta, topicos, ctx_enriquecido=""):
        return self.emergir.gerar_fragmentado(pergunta, topicos, ctx_enriquecido)

    def _verificar_alucinacao_siglas(self, texto):
        return self.emergir.verificar_alucinacao(texto)

    # ============================================================
    # SELF-STUDY (implementado em modulos/self_study.py)
    # ============================================================

    def _self_study(self):
        """Delega para SelfStudyEngine.executar() (modulos/self_study.py)."""
        return self.self_study.executar()

    def _escanear_projeto(self, max_arquivos=60):
        return self.self_study.escanear_projeto(max_arquivos)

    def _extrair_metricas(self, arquivos):
        return self.self_study.extrair_metricas(arquivos)

    def _gerar_auto_insight(self, metricas):
        return self.self_study.gerar_auto_insight(metricas)

    # ============================================================
    # AUTO-MELHORIA AUTONOMA — Loop AGI completo
    # ============================================================

    def _decidir_melhoria(self):
        """Usa IA para decidir QUAL melhoria fazer baseado em dados reais.
        
        Consulta Self-Study + anti-patterns + metricas.
        Retorna dict com {arquivo, acao, tipo, prioridade} ou None se nada a fazer.
        """
        import re as _re
        
        # 1. Coleta dados atuais
        arquivos = self.self_study.escanear_projeto(max_arquivos=30)
        metricas = self.self_study.extrair_metricas(arquivos)
        anti = self.self_study._analisar_anti_patterns(arquivos)
        
        # 2. IA decide
        prompt = (
            f"[SISTEMA]\nVoce e um ARQUITETO DE SOFTWARE revisando codigo.\n"
            f"[METRICAS]\nTotal arquivos: {metricas['total_arquivos']}\n"
            f"Total linhas: {metricas['total_linhas']}\n"
            f"Total funcoes: {metricas['total_funcoes']}\n\n"
            f"[PROBLEMAS ENCONTRADOS]\n"
        )
        for k, v in sorted(anti.items(), key=lambda x: -len(x[1])):
            prompt += f"- {k}: {len(v)} ocorrencias\n"
            for o in v:
                prompt += f"  {o['arquivo']}:L{o['linha']} {o['codigo']}\n"
        
        prompt += (
            f"\n[PERGUNTA]\nQual a UNICA melhoria mais importante de fazer agora?\n"
            f"Responda EXATAMENTE neste formato:\n"
            f"ARQUIVO: nome_do_arquivo.py\n"
            f"ACAO: descricao da mudanca em 1 linha\n"
            f"TIPO: except|import|refatorar\n"
            f"PRIORIDADE: alta|media\n"
        )
        
        decisao = self.ia.gerar(prompt, 0.3, 'leve') or ""
        
        # 3. Parseia a decisao
        resultado = {}
        for linha in decisao.split('\n'):
            m = _re.match(r'(ARQUIVO|ACAO|TIPO|PRIORIDADE):\s*(.*)', linha.strip())
            if m:
                resultado[m.group(1).lower()] = m.group(2).strip()
        
        if resultado.get('arquivo'):
            return resultado
        return None

    def _gerar_e_aplicar(self, decisao):
        """Gera codigo via IA + aplica + valida (sintaxe E semantica). 
        Mantem .autobak ate o proximo ciclo bem-sucedido.
        """
        import shutil, re as _re
        
        arquivo = decisao.get('arquivo', '')
        acao = decisao.get('acao', '')
        
        caminhos_possiveis = [
            os.path.join(BASE, 'Scripts', 'mcr_devia', 'modulos', arquivo),
            os.path.join(BASE, 'Scripts', 'mcr_devia', arquivo),
            os.path.join(BASE, 'Scripts', 'mcr_devia', 'comandos', arquivo),
        ]
        caminho = None
        for c in caminhos_possiveis:
            if os.path.exists(c):
                caminho = c
                break
        if not caminho:
            return False
        
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo_original = f.read()
        except Exception:
            return False
        
        # Backup ANTES de qualquer modificacao
        shutil.copy2(caminho, caminho + '.autobak')
        
        # Gera correcao DIRETA via IA
        prompt_correcao = (
            f"[SISTEMA]\nVoce e um reparador de codigo. Gere APENAS a correcao, "
            f"sem explicacoes, sem markdown.\n\n"
            f"[ARQUIVO]\n{arquivo}\n[ACAO]\n{acao}\n\n"
            f"[CODIGO ATUAL]\n{conteudo_original}\n\n"
            f"[INSTRUCAO]\nGere o ARQUIVO COMPLETO corrigido.\n"
            f"PRESERVE todos os metodos e classes existentes.\n"
            f"NAO remova nada — apenas corrija o problema indicado.\n"
            f"Preserve a indentacao original. Responda APENAS com o codigo."
        )
        codigo_novo = self.ia.gerar(prompt_correcao, 0.3, 'analisar') or ''
        
        if not codigo_novo or len(codigo_novo) < 50:
            shutil.copy2(caminho + '.autobak', caminho)
            return False
        
        # Extrai codigo puro (remove markdown ``` se houver)
        m = _re.search(r'```(?:python)?\s*\n(.*?)```', codigo_novo, _re.DOTALL)
        if m:
            codigo_novo = m.group(1).strip()
        
        # Validacao 1: SINTAXE
        try:
            compile(codigo_novo, caminho, 'exec')
        except SyntaxError as e:
            self._log('AUTO', f'Erro de sintaxe na correcao: {e}')
            shutil.copy2(caminho + '.autobak', caminho)
            return False
        
        # Validacao 2: SEMANTICA (metodos essenciais)
        metodos_essenciais = []
        if arquivo == 'diagnostic_engine.py':
            metodos_essenciais = ['diagnosticar', 'remediar', 'executar',
                                  'check_compilacao', 'check_io_manual', 'gerar_relatorio']
        elif arquivo == 'master_agent.py':
            metodos_essenciais = ['executar', '_auto_melhorar', '_processar_emergencia',
                                  '_executar_subtarefa', '_log']
        elif arquivo == 'self_study.py':
            metodos_essenciais = ['executar', 'escanear_projeto', '_analisar_anti_patterns']
        
        for metodo in metodos_essenciais:
            if f'def {metodo}' not in codigo_novo:
                self._log('AUTO', f'Metodo essencial {metodo} ausente apos correcao! Revertendo.')
                shutil.copy2(caminho + '.autobak', caminho)
                return False
        
        # Validacao 3: TAMANHO minimo (nao perdeu metades do arquivo)
        if len(codigo_novo) < len(conteudo_original) * 0.5:
            self._log('AUTO', f'Arquivo encolheu demais! {len(codigo_novo)} vs {len(conteudo_original)}. Revertendo.')
            shutil.copy2(caminho + '.autobak', caminho)
            return False
        
        # Validacao 4: PATTERN GATEKEEPER (fingerprint + eixo)
        try:
            from mcr.util import reparar_com_validacao
            codigo_final = reparar_com_validacao(
                conteudo_original, lambda c: codigo_novo, similaridade_min=0.7)
            if codigo_final == conteudo_original:
                self._log('AUTO', 'Gatekeeper rejeitou: similaridade ou eixo comprometido.')
                shutil.copy2(caminho + '.autobak', caminho)
                return False
        except Exception:
            codigo_final = codigo_novo  # fallback: prossegue sem gatekeeper
        
        # Escreve codigo validado
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(codigo_final)
        
        # Mantem .autobak ate proximo ciclo (NUNCA remove)
        return True

    def _auto_melhorar(self):
        """Pipeline completa de auto-melhoria: escanear -> decidir -> gerar -> aplicar -> validar -> aprender.
        
        Chamado automaticamente a cada 20 execucoes ou manualmente via comando.
        """
        from mcr.sse_server import emit
        from mcr.progress_tracker import salvar_checkpoint, registrar_erro
        
        t0 = time.time()
        salvar_checkpoint('auto_melhorar', 0.01)
        emit('stage', {'name': 'auto_melhorar', 'label': 'Auto-melhoria...', 'progress': 0.01})
        emit('narrator', 'Iniciando ciclo autonomo de auto-melhoria...')
        
        try:
            # 1. DECIDIR
            emit('narrator', 'Analisando codigo para decidir melhoria...')
            decisao = self._decidir_melhoria()
            if not decisao or not decisao.get('arquivo'):
                emit('narrator', 'Nenhuma melhoria necessaria no momento.')
                return
            
            emit('narrator', f"Decisao: {decisao['arquivo']} - {decisao.get('acao','')}")
            salvar_checkpoint('decidir', 0.3, arquivo=decisao['arquivo'])
            
            # 2. GERAR E APLICAR
            emit('narrator', f'Gerando e aplicando correcao em {decisao["arquivo"]}...')
            sucesso = self._gerar_e_aplicar(decisao)
            
            if sucesso:
                emit('narrator', f'Correcao aplicada com sucesso em {decisao["arquivo"]}!')
                salvar_checkpoint('aplicar', 0.7)
            else:
                emit('narrator', f'Falha ao aplicar correcao em {decisao["arquivo"]}. Revertido.')
                salvar_checkpoint('falha', 0.7)
            
            # 3. APRENDER
            try:
                self.kg.aprender(
                    erro=f'auto-melhoria: {decisao.get("arquivo","")}',
                    causa=decisao.get('acao', ''),
                    solucao=f'Sucesso: {sucesso} | Tipo: {decisao.get("tipo","")}',
                    ctx='auto_melhoria'
                )
            except Exception:
                pass
            
            salvar_checkpoint('fim', 1.0)
            emit('narrator', f'Auto-melhoria concluida em {round(time.time()-t0, 1)}s')
        
        except Exception as e:
            import traceback
            registrar_erro(str(e), type(e).__name__, trace=traceback.format_exc())
            emit('error', {'msg': f'Auto-melhoria: {e}'})
            raise

    def _executar_subtarefa(self, subtarefa, artefatos=None, contexto_extra='', codigo_anterior=None):
        """Delega para TaskExecutor (modulos/task_executor.py)."""
        return self.task_executor.executar_subtarefa(subtarefa, artefatos, contexto_extra, codigo_anterior)

    def _integrar(self, request, plano, resultados):
        """Delega para TaskExecutor (modulos/task_executor.py)."""
        return self.task_executor.integrar(request, plano, resultados)

    def _registrar_episodio(self, request, resultado, licao):
        """J2: acumula episodio no buffer. Faz flush ao atingir 10."""
        req_str = request if isinstance(request, str) else str(request)
        self._buffer_episodios.append({
            'request': req_str,
            'resultado': resultado,  # pode ser dict (registrar_lote aceita)
            'licao': licao,
        })
        if len(self._buffer_episodios) >= 10:
            self._flush_episodios()

    def _flush_episodios(self):
        """J2: registra lote com 1 embedding batch."""
        if not self._buffer_episodios:
            return
        try:
            self.memoria.registrar_lote(self._buffer_episodios)
        except Exception as e:
            print(f"[EpisodioBuffer] Erro ao registrar lote: {e}")
            for ep in self._buffer_episodios:
                try:
                    self.memoria.registrar(ep['request'], ep['resultado'], ep['licao'])
                except Exception:
                    pass
        self._buffer_episodios = []

    def _extrair_licao(self, request, plano, resultados):
        """Extrai licao aprendida do processo, estruturada em 3 blocos.
        
        Formato:
        Contexto: <request>
        Resultado: <n_ok/n_total> subtarefas OK, <tempo>s
        Falhas: <acoes>: <erro>
        Causa provavel: <analise>
        Licao: <recomendacao>
        """
        n_sucesso = sum(1 for r in resultados.values() if r.get('sucesso'))
        n_total = len(plano)
        falhas = [(p, resultados.get(p['id'], {})) for p in plano 
                  if not resultados.get(p['id'], {}).get('sucesso')]
        
        linhas = []
        linhas.append(f"Contexto: {request}")
        
        if not falhas:
            linhas.append(f"Resultado: {n_sucesso}/{n_total} subtarefas OK")
            linhas.append(f"Licao: Plano funcionou integralmente. Reutilizar template.")
        else:
            # Coleta erros das falhas
            erros_detalhes = []
            for p, r in falhas:
                erro_msg = str(r.get('erro', 'erro desconhecido'))
                erros_detalhes.append(f"{p['acao']}: {erro_msg}")
            linhas.append(f"Resultado: {n_sucesso}/{n_total} subtarefas")
            linhas.append(f"Falhas: {'; '.join(erros_detalhes)}")
            
            # Causa provavel
            acoes_falhas = [p['acao'] for p, _ in falhas]
            if any('depend' in str(r.get('erro', '')).lower() for _, r in falhas):
                linhas.append("Causa provavel: dependencia entre passos nao satisfeita")
            elif any('ferramenta' in str(r.get('erro', '')).lower() for _, r in falhas):
                linhas.append("Causa provavel: ferramenta nao encontrada ou parametro errado")
            elif any('valid' in a for a in acoes_falhas):
                linhas.append("Causa provavel: codigo gerado continha erros de sintaxe")
            elif any('web' in a or 'web' in str(r).lower() for a, r in [(p['acao'], resultados.get(p['id'], {})) for p, _ in falhas]):
                linhas.append("Causa provavel: busca web falhou (fonte indisponivel ou consulta inadequada)")
            else:
                linhas.append("Causa provavel: falha generica na execucao")
            
            linhas.append(f"Licao: {n_sucesso}/{n_total} passos OK. Revisar {'; '.join(acoes_falhas)}")
        
        return '\n'.join(linhas)

    def _aprender_kg(self, request, resultado, licao, task_type=''):
        """Registra aprendizado no Knowledge Graph como DATASET estruturado.
        
        [G9] Usa LessonsBuffer para detectar contradicoes antes de salvar.
        """
        try:
            erro = request
            tt = resultado.get('task_type', task_type) or 'geral'
            n_ok = resultado.get('n_sucesso', 0)
            n_total = resultado.get('n_subtarefas', 0)
            tempo = resultado.get('tempo', 0)
            causa = (f"tipo={tt} | subtarefas={n_ok}/{n_total} | "
                     f"tempo={tempo}s | request={request}")
            solucao = licao
            ctx = f'exec_{tt}'
            
            # G9 + J1: LessonsBuffer com batch embedding
            try:
                from mcr.lessons_buffer import LessonsBuffer
                buffer = LessonsBuffer(self.kg)
                buffer.adicionar(erro, causa, solucao, ctx)
                buffer.comitar()  # batch embedding + flush para KG
            except Exception:
                # Fallback: salva direto no KG
                self.kg.aprender(erro, causa, solucao, ctx)
        except Exception:
            pass

    def _ask_user(self, mensagem, opcoes=None):
        """Pergunta ao usuario antes de prosseguir. Timeout 60s, fallback 'sim'."""
        sandbox = os.path.join(BASE, 'sandbox')
        question_path = os.path.join(sandbox, '.mcr_question.json')
        answer_path = os.path.join(sandbox, '.mcr_answer.json')

        # Limpa respostas anteriores
        for f_ in [answer_path]:
            if os.path.exists(f_):
                os.remove(f_)

        # Salva pergunta
        with open(question_path, 'w', encoding='utf-8') as f_:
            json.dump({
                'pergunta': mensagem,
                'opcoes': opcoes or ['sim', 'nao'],
                'timestamp': time.time(),
            }, f_, ensure_ascii=False)

        print(f"\n[MasterAgent] PERGUNTA: {mensagem}")
        if opcoes:
            print(f"[MasterAgent] Opcoes: {', '.join(opcoes)}")
        print(f"[MasterAgent] Responda em .mcr_answer.json ou aguarde 60s (default: sim)")

        # Aguarda resposta (max 60s)
        for _ in range(60):
            if os.path.exists(answer_path):
                try:
                    with open(answer_path, 'r', encoding='utf-8') as f_:
                        resp = json.load(f_)
                    return resp.get('resposta', 'sim')
                except Exception:
                    pass
            time.sleep(1)

        print(f"[MasterAgent] Sem resposta, prosseguindo (default: sim)")
        return 'sim'

    def _log(self, etapa, mensagem):
        """Registra passo da execucao."""
        entry = {
            'etapa': etapa,
            'mensagem': mensagem,
            'tempo': time.strftime('%H:%M:%S'),
        }
        self._passos.append(entry)
        print(f'[{entry["tempo"]}] {etapa}: {mensagem}', flush=True)

    def metricas(self):
        """Retorna metricas gerais do agente."""
        return {
            'episodios': self.memoria.metricas(),
            'sandbox': self.sandbox.metricas(),
            'ultima_execucao': self._passos[-1]['mensagem'] if self._passos else 'Nenhuma',
        }
