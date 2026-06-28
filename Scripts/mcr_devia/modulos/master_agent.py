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
import os, sys, json, time
from typing import Dict, List, Optional

# Caminhos
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia'))

from modulos.episodic_memory import EpisodicMemory
from modulos.task_planner import TaskPlanner, PlanValidator
from modulos.tool_orchestrator import ToolOrchestrator
from modulos.sandbox_executor import SandboxExecutor
from modulos.ia import IA
from modulos.kg import KnowledgeGraph
from context_infinity import SessionCache


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
                     f"'{request[:60]}'. Tipo classificado como "
                     f"'{tipo_porte}' parece incorreto.")
            self.kg.aprender(
                erro=f"Feedback: {request[:60]}",
                causa=f"tipo={tipo_porte} | sucesso={n_ok}/{n_total}",
                solucao=licao[:300],
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
        self.ctx.absorver('request', request, 'request', tags=['request', task_type or 'geral'], origem='usuario')

        self._log('PERCEBER', f'Request: {request[:100]}')

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
                self._log('PERCEBER', f"  -> {m['request'][:60]} ({status})")

        # Buscar conhecimento relevante
        lessons = self.kg.buscar(request, max_r=3)
        if lessons:
            self._log('PERCEBER', f'Encontradas {len(lessons)} licoes no KG')
            self.ctx.absorver('kg_lessons', str(lessons[:2]), 'contexto', tags=['kg'], origem='kg')

        # === 1.5 PAUSE-AND-ASK (projetos grandes) ===
        # Usa Decider para classificar o porte do projeto
        projeto_grande = False
        request_ambiguo = False
        tipo_porte = 'simples'
        try:
            from modulos.decider import Decider
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
            # Fallback: regex
            projeto_grande = any(p in request.lower() for p in ['jogo', 'game', 'projeto', 'site'])
            request_ambiguo = len(request) < 60 and projeto_grande

        if projeto_grande:
            from modulos.util import extrair_nome_projeto
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
        self.ctx.absorver('plano', json.dumps([{'id': p['id'], 'acao': p['acao'], 'desc': p['descricao'][:50]} for p in plano]),
                          'plano', tags=['plano', task_type or 'geral'], origem='planner')

        for p in plano:
            self._log('PLANEJAR', f'  {p["id"]}. {p["acao"]} - {p["descricao"][:60]}')

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
            ctx_passo = self.ctx.pescar(
                pergunta=subtarefa['descricao'],
                tipos=['codigo', 'request', 'plano', 'resultado', 'contexto'],
                max_tokens=500
            )
            ctx_passo_str = str([c.conteudo[:200] for c in ctx_passo]) if ctx_passo else ''

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
                    res[:1000],
                    tipo='codigo' if 'gerar_' in acao_atual else 'resultado',
                    tags=tags_resultado,
                    origem=f'executor:{acao_atual}'
                )

            # Se gerou codigo, armazena como artefato
            if resultado.get('sucesso'):
                if isinstance(res, str) and len(res) > 50:
                    if 'gerar_modulo' in acao_atual:
                        nome_mod = acao_atual.replace('gerar_modulo_', '')
                        artefatos[f'modulo_{nome_mod}'] = res
                    elif acao_atual == 'gerar_codigo':
                        artefatos['codigo_gerado'] = res

            # Se falhou, tenta web search para contexto extra
            if not resultado.get('sucesso') and resultado.get('erro'):
                self._log('EXECUTAR', f'  -> Falhou: {str(resultado.get("erro",""))[:80]}. Buscando contexto web...')
                contexto_web = self.ia.buscar_web(
                    f"Como resolver: {subtarefa.get('descricao', request)}. "
                    f"Erro: {resultado.get('erro', '')}",
                    max_resultados=3
                )
                if contexto_web:
                    self.ctx.absorver(f'web_search_{subtarefa["id"]}', contexto_web[:500],
                                      'contexto', tags=['web', 'ajuda'], origem='web_search')
                    resultado_retry = self._executar_subtarefa(subtarefa, artefatos=artefatos, contexto_extra=contexto_web, codigo_anterior=codigo_anterior)
                    if resultado_retry.get('sucesso'):
                        resultados[subtarefa['id']] = resultado_retry
                        self._log('EXECUTAR', f'  -> Web search ajudou a resolver!')
                    else:
                        self._log('EXECUTAR', f'  -> Web search nao foi suficiente')
                else:
                    self._log('EXECUTAR', f'  -> Web search nao disponivel/sem resultados')

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
        self.memoria.registrar(request, resultado_final, licao)
        self._aprender_kg(request, resultado_final, licao, task_type=task_type)

        # === 6. FEEDBACK (Backpropagation) ===
        self._feedback(request, tipo_porte, plano, resultados)

        self._log('APRENDER', f'Licao registrada: {licao[:80]}')
        self._log('FIM', f'Concluido em {tempo_total:.1f}s - '
                  f'{resultado_final["n_sucesso"]}/{len(plano)} subtarefas OK')

        return resultado_final

    def _executar_subtarefa(self, subtarefa, artefatos=None, contexto_extra='', codigo_anterior=None):
        """Executa uma subtarefa do plano.
        
        Args:
            subtarefa: Dict com acao, params, ferramenta
            artefatos: Dict de artefatos acumulados (modifica in-place)
            contexto_extra: Contexto adicional da web (opcional)
            codigo_anterior: Codigo gerado em passo anterior (para validar/salvar)
        """
        if artefatos is None:
            artefatos = {}
        acao = subtarefa.get('acao', '')
        params = subtarefa.get('params', {})
        ferramenta = subtarefa.get('ferramenta', '')

        # Ajusta params para ferramentas que precisam do codigo gerado anteriormente
        if ferramenta == 'validar_python' and 'codigo' not in params and codigo_anterior:
            params['codigo'] = codigo_anterior
        
        if ferramenta == 'escrever_artefato' and 'codigo' not in params and codigo_anterior:
            params['codigo'] = codigo_anterior
            if 'caminho' not in params:
                params['caminho'] = os.path.join(BASE, 'sandbox', 'artefato_gerado.py')

        # ============================================================
        # ACOES ESPECIAIS (precisam de logica extra + artefatos)
        # ============================================================

        if acao == 'perguntar_usuario':
            pergunta = params.get('pergunta', 'Posso prosseguir?')
            resp = self._ask_user(pergunta)
            return {'sucesso': True, 'resultado': f"Usuario: {resp}"}

        if acao == 'criar_estrutura_pastas':
            caminho = params.get('caminho', '')
            if caminho:
                for sub in ['src', 'assets', 'runs']:
                    sub_path = os.path.join(caminho, sub)
                    self.tools.executar('criar_diretorio', {'caminho': sub_path})
                artefatos['projeto_path'] = caminho
                return {'sucesso': True, 'resultado': f"Estrutura criada em {caminho}"}
            return {'sucesso': False, 'erro': 'Caminho nao especificado'}

        if acao == 'validar_codigo':
            # Valida QUALQUER linguagem usando _cmd_validar_codigo (tool_orchestrator)
            modulos = {k: v for k, v in artefatos.items() if k.startswith('modulo_') and not k.endswith('_puro')}
            erros = []
            if modulos:
                # projeto_jogo: valida CADA modulo individualmente
                for nome_mod, codigo in modulos.items():
                    if codigo and len(codigo) > 20:
                        r = self.tools.executar('validar_codigo', {'codigo': codigo[:5000]})
                        if r.get('sucesso'):
                            res = r['resultado']
                            if not res.get('valido', True):
                                erros.append(f"{nome_mod}: {res.get('erros', ['erro'])}")
            elif codigo_anterior:
                # criar_codigo: valida o codigo unico
                r = self.tools.executar('validar_codigo', {'codigo': codigo_anterior[:5000]})
                if r.get('sucesso'):
                    res = r['resultado']
                    if not res.get('valido', True):
                        erros.append(f"codigo: {res.get('erros', ['erro'])}")
                    else:
                        return {'sucesso': True, 'resultado': f"Validacao OK ({res.get('linguagem', '?')})"}
            if erros:
                return {'sucesso': False, 'erro': f"Erros em: {', '.join(erros[:3])}"}
            return {'sucesso': True, 'resultado': f"Validados {len(modulos) if modulos else 1} modulo(s) sem erros"}

        if acao == 'extrair_codigo':
            modulos = {k: v for k, v in artefatos.items() if k.startswith('modulo_') and not k.endswith('_puro')}
            projeto_path = artefatos.get('projeto_path', os.path.join(BASE, 'sandbox'))
            src_path = os.path.join(projeto_path, 'src')
            os.makedirs(src_path, exist_ok=True)
            salvos = []
            for nome_mod, codigo_bruto in modulos.items():
                r = self.tools.executar('extrair_codigo', {'conteudo': codigo_bruto})
                if r.get('sucesso'):
                    codigo_puro = r['resultado']
                    artefatos[nome_mod] = codigo_puro
                    # Nome do arquivo sem prefixo 'modulo_'
                    nome_arquivo = nome_mod.replace('modulo_', '')
                    # Detecta extensao pelo conteudo do codigo
                    amostra = codigo_puro[:200]
                    if 'const ' in amostra or 'require(' in amostra or 'var ' in amostra \
                       or 'import React' in amostra or 'function ' in amostra:
                        ext = '.js'
                    elif 'local ' in amostra or 'function ' in amostra:
                        ext = '.lua'
                    else:
                        ext = '.py'
                    caminho_arquivo = os.path.join(src_path, f"{nome_arquivo}{ext}")
                    try:
                        with open(caminho_arquivo, 'w', encoding='utf-8') as f_:
                            f_.write(codigo_puro)
                        salvos.append(f"{nome_arquivo}{ext}")
                    except Exception as e_:
                        print(f"[MasterAgent] Erro ao salvar {caminho_arquivo}: {e_}")
            return {'sucesso': True, 'resultado': f"Extraidos e salvos {len(salvos)} modulos: {', '.join(salvos)}"}

        if acao == 'testar_execucao':
            projeto_path = artefatos.get('projeto_path', '')
            if not projeto_path:
                return {'sucesso': False, 'erro': 'projeto_path nao definido'}
            src_path = os.path.join(projeto_path, 'src')
            if os.path.exists(src_path):
                arquivos = os.listdir(src_path)
                # So executa teste se for Python (JS/Lua precisam de runtime especifico)
                main_file = None
                for f in arquivos:
                    if f.startswith('main.'):
                        main_file = os.path.join(src_path, f)
                        break
                if main_file and os.path.exists(main_file):
                    if not main_file.endswith('.py'):
                        return {'sucesso': True, 'resultado': f'Teste ignorado ({os.path.splitext(main_file)[1]} nao executavel localmente)'}
                    with open(main_file, 'r') as f:
                        codigo = f.read()
                    return self.sandbox.executar_python(codigo)
                return {'sucesso': False, 'erro': f'main.* nao encontrado em {src_path}'}
            return {'sucesso': False, 'erro': f'Pasta src/ nao encontrada em {projeto_path}'}

        if acao == 'relatorio_final':
            projeto_path = artefatos.get('projeto_path', os.path.join(BASE, 'sandbox'))
            relatorio = f"Projeto criado!\nLocal: {projeto_path}\nEstrutura:\n"
            if os.path.exists(projeto_path):
                for root, dirs, files in os.walk(projeto_path):
                    nivel = root.replace(projeto_path, '').count(os.sep)
                    relatorio += f"{'  ' * nivel}{os.path.basename(root)}/\n"
                    for fname in sorted(files):
                        relatorio += f"{'  ' * (nivel + 1)}{fname}\n"
            return {'sucesso': True, 'resultado': relatorio}

        # ============================================================
        # FERRAMENTAS REGISTRADAS
        # ============================================================

        # Se tem ferramenta especifica, usa
        if ferramenta and ferramenta != 'perguntar_ia':
            resultado = self.tools.executar(ferramenta, params)
            return resultado

        # Se e pergunta, usa IA
        if acao == 'perguntar_ia':
            pergunta = params.get('pergunta', subtarefa.get('descricao', ''))
            if contexto_extra:
                pergunta = f"Contexto adicional:\n{contexto_extra}\n\nPergunta:\n{pergunta}"
            resposta = self.ia.gerar(pergunta, 0.4, 'pesado')
            return {
                'sucesso': bool(resposta),
                'resultado': resposta or 'Sem resposta',
                'erro': '' if resposta else 'IA nao retornou resposta',
            }

        # Fallback: IA generica
        descricao = subtarefa.get('descricao', str(params))
        if contexto_extra:
            descricao = f"Contexto adicional:\n{contexto_extra}\n\n{descricao}"
        resposta = self.ia.gerar(descricao, 0.4, 'code')
        return {
            'sucesso': bool(resposta),
            'resultado': resposta or 'Sem resposta',
            'erro': '' if resposta else 'IA nao retornou resposta',
        }

    def _integrar(self, request, plano, resultados):
        """Junta todos os resultados parciais num artefato coeso."""
        partes = []

        for p in plano:
            r = resultados.get(p['id'], {})
            if r.get('sucesso') and r.get('resultado'):
                partes.append({
                    'passo': p['id'],
                    'acao': p['acao'],
                    'descricao': p.get('descricao', ''),
                    'conteudo': r['resultado'],
                })

        if not partes:
            # Se nada funcionou, tenta IA direta
            resposta = self.ia.gerar(
                f"Responda da melhor forma possivel: {request}",
                0.4, 'pesado'
            )
            return {'resposta_final': resposta or 'Nao foi possivel completar a tarefa'}

        # Se so tem 1 parte, retorna direto
        if len(partes) == 1:
            return {'resposta_final': partes[0]['conteudo']}

        # Multiplas partes - compila em artefato
        compilado = []
        for p in partes:
            compilado.append(f"### Passo {p['passo']}: {p['descricao']}\n{p['conteudo']}")

        return {'resposta_final': '\n\n'.join(compilado), 'partes': partes}

    def _extrair_licao(self, request, plano, resultados):
        """Extrai licao aprendida do processo."""
        n_sucesso = sum(1 for r in resultados.values() if r.get('sucesso'))
        n_total = len(plano)
        falhas = [p for p in plano if not resultados.get(p['id'], {}).get('sucesso')]

        if not falhas:
            return f"Tarefa concluida com sucesso em {n_sucesso}/{n_total} passos"
        else:
            acoes_falhas = ', '.join(f['acao'] for f in falhas[:3])
            return f"Tarefa parcial ({n_sucesso}/{n_total}). Falhas em: {acoes_falhas}"

    def _aprender_kg(self, request, resultado, licao, task_type=''):
        """Registra aprendizado no Knowledge Graph como DATASET estruturado.
        
        Agora salva com contexto rico que permite consultas semanticas:
        - ctx indica o TIPO de tarefa (exec_projeto_jogo, exec_criar_codigo, etc)
        - causa detalha metricas de sucesso para analise futura
        """
        try:
            erro = request[:80]
            tt = resultado.get('task_type', task_type) or 'geral'
            n_ok = resultado.get('n_sucesso', 0)
            n_total = resultado.get('n_subtarefas', 0)
            tempo = resultado.get('tempo', 0)
            causa = (f"tipo={tt} | subtarefas={n_ok}/{n_total} | "
                     f"tempo={tempo}s | request={request[:50]}")
            solucao = licao[:500]
            ctx = f'exec_{tt}'  # ex: exec_projeto_jogo, exec_criar_codigo
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
        print(f'[{entry["tempo"]}] {etapa}: {mensagem}')

    def metricas(self):
        """Retorna metricas gerais do agente."""
        return {
            'episodios': self.memoria.metricas(),
            'sandbox': self.sandbox.metricas(),
            'ultima_execucao': self._passos[-1]['mensagem'] if self._passos else 'Nenhuma',
        }
