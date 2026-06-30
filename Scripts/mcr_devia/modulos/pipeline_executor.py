"""Pipeline Executor Multi-Request — Processa múltiplas solicitações em sequência.
Arquitetura:
  1. RequestPlanner: FAST1 classifica → FAST2 delega → cria plano de execução
  2. PipelineExecutor: executa cada solicitação UMA POR UMA
  3. FragmentManager: salva cada resultado parcial (ContextInfinity + .mcr_conversa.jsonl)
  4. ResponseAssembler: monta resposta final concatenando fragmentos (SEM IA)
  5. PipelineReviewer: verifica qualidade e consistência

ContextCrew supervisiona todo o processo para ninguém esquecer nada.
"""
import os, sys, json, time, re, subprocess, datetime as _dt
from typing import List, Tuple, Dict, Any

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SANDBOX = os.path.join(BASE, 'sandbox')

def init_module(contexto):
    pipe = PipelineExecutor(
        kg=contexto.get('kg'),
        ia=contexto.get('ia'),
        ctx_crew=contexto.get('ctx_crew'),
        orquestrador=contexto.get('orquestrador'),
        identidade=contexto.get('identidade', ''),
    )
    contexto['pipeline_executor'] = pipe
    return 'pipeline_executor', pipe


class RequestPlanner:
    """FAST1 classifica → FAST2 delega → retorna plano de execução."""
    
    def __init__(self, ia=None):
        self.ia = ia
    
    def _fast(self, prompt, temp=0.1):
        """Chamada rápida ao modelo leve."""
        if self.ia:
            return self.ia.fast(prompt, temp, "leve") or ""
        # Fallback: chamada direta
        try:
            import urllib.request as _ur
            OLLAMA = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/generate')
            d = json.dumps({'model': 'qwen2.5-coder:1.5b', 'prompt': prompt, 'stream': False,
                'options': {'temperature': temp, 'num_ctx': 2048, 'num_predict': 512}}).encode()
            r = _ur.Request(OLLAMA, data=d, headers={'Content-Type': 'application/json'})
            return (json.loads(_ur.urlopen(r, timeout=30).read()).get('response') or "").strip()
        except Exception:
            return ""
    
    def criar_plano(self, texto: str) -> List[Dict[str, str]]:
        """Analisa o texto original e retorna plano.
        Divide por ? e \\n, funde siblings (e, ou, mas, continuacoes).
        Preserva texto original (.lua, acentos, pontuacao)."""
        plano = []
        
        # Divide por ? e \\n (NAO remove pontos, NAO modifica texto)
        partes = re.split(r'[?\n]+', texto)
        fragmentos = []
        for parte in partes:
            p = parte.strip()
            if not p:
                continue
            # Funde com anterior se for continuacao (curta OU com conjuncao)
            # NUNCA funde se tiver numeros/operadores (pergunta independente)
            if fragmentos and (
                (len(p) < 12 and not re.search(r'\d+\s*[\*\+]', p)) or 
                re.match(r'^(e |ou |mas |tamb[ée]m |que |como |onde |quando )', p.lower())
            ):
                fragmentos[-1] += '? ' + p
            else:
                fragmentos.append(p)
        
        # Classifica cada fragmento
        for s in fragmentos:
            s_lower = s.lower()
            tool = 'IA'
            
            if any(k in s_lower for k in ['hora', 'horario', 'data', 'dia', 'amanha', 'segundos para', 'minutos para']):
                tool = 'PYTHON'
            elif re.search(r'\d+\s*[\*\+]\s*\d+', s):
                tool = 'PYTHON'
            elif re.search(r'\bpi\b', s_lower) or 'π' in s:
                tool = 'PYTHON'
            elif any(k in s_lower for k in ['processo', 'recursos', 'cpu', 'memoria', 'tasklist']):
                tool = 'TASKLIST'
            
            plano.append({'solicitacao': s, 'tool': tool, 'params': {}})
        
        if not plano:
            plano.append({'solicitacao': texto, 'tool': 'IA', 'params': {}})
        
        return plano


class FragmentManager:
    """Gerencia fragmentos: salva cada resposta parcial."""
    
    def __init__(self):
        self.fragmentos = []
    
    def salvar(self, resposta: str, indice: int, tool: str):
        """Salva um fragmento de resposta."""
        fragmento = {
            'indice': indice,
            'tool': tool,
            'resposta': resposta,
            'ts': time.time(),
        }
        self.fragmentos.append(fragmento)
        
        # Salva no .mcr_conversa.jsonl (ContextInfinity lê daqui)
        try:
            conv_path = os.path.join(SANDBOX, '.mcr_conversa.jsonl')
            with open(conv_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    'ts': fragmento['ts'],
                    'role': f'fragmento_{indice}',
                    'msg': f"[Fragmento {indice+1}/{indice+1} ({tool})]\n{resposta}"
                }, ensure_ascii=False) + '\n')
        except Exception:
            pass
    
    def obter_todos(self) -> List[Dict]:
        return self.fragmentos


class ResponseAssembler:
    """Monta resposta final SEM IA — apenas concatena fragmentos."""
    
    def montar(self, fragmentos: List[Dict]) -> str:
        """Concatena fragmentos em uma resposta unificada."""
        if not fragmentos:
            return "Nenhuma resposta gerada."
        
        partes = []
        for i, frag in enumerate(fragmentos):
            resp = frag.get('resposta', '').strip()
            if resp:
                if len(fragmentos) > 1:
                    partes.append(f"{resp}")
                else:
                    partes.append(resp)
        
        return '\n\n'.join(partes)


class PipelineReviewer:
    """Revisa a resposta final verificando qualidade."""
    
    def revisar(self, resposta: str, fragmentos: List[Dict]) -> Dict:
        """Revisa a resposta final. Retorna dict com status e problemas."""
        problemas = []
        
        # Verifica se todos os fragmentos estão na resposta
        for frag in fragmentos:
            resp_frag = frag.get('resposta', '')
            if resp_frag and len(resp_frag) < 10:
                problemas.append(f"Fragmento {frag.get('indice')} muito curto")
            if resp_frag and 'não posso' in resp_frag.lower():
                problemas.append(f"Fragmento {frag.get('indice')} recusou responder")
        
        # Verifica tamanho total
        if len(resposta) < 20:
            problemas.append("Resposta final muito curta")
        
        return {
            'status': 'OK' if not problemas else 'WARN',
            'problemas': problemas,
            'total_fragmentos': len(fragmentos),
            'tamanho': len(resposta),
        }


# ============================================================
# PIPELINE EXECUTOR PRINCIPAL
# ============================================================

class PipelineExecutor:
    """Orquestrador do pipeline multi-request."""
    
    def __init__(self, kg=None, ia=None, ctx_crew=None, orquestrador=None, identidade="",
                 task_planner=None, tool_orchestrator=None):
        self.kg = kg
        self.ia = ia
        self.ctx_crew = ctx_crew
        self.orquestrador = orquestrador
        self.identidade = identidade
        self.task_planner = task_planner
        self.tool_orchestrator = tool_orchestrator
        self.planner = RequestPlanner(ia=ia)
        self.frag_manager = FragmentManager()
        self.assembler = ResponseAssembler()
        self.reviewer = PipelineReviewer()
    
    def _detectar_complexidade(self, texto):
        """Detecta se a pergunta e complexa o suficiente para usar TaskPlanner."""
        # Perguntas com multiplas interrogacoes
        if texto.count('?') > 1:
            return True
        # Perguntas de comparacao
        if any(p in texto.lower() for p in ['diferenca', 'comparar', 'vs ', ' x ', 'ou']):
            return True
        # Perguntas longas
        if len(texto) > 300:
            return True
        return False

    def executar(self, texto: str, skip_tot=False, turbo=False, fragmentar=False, token_a_bloco=True, modo_ia="auto") -> Tuple[str, Dict]:
        """Executa pipeline completo: planejar -> executar -> montar -> revisar.
        
        Args:
            texto: Pergunta/texto a processar
            skip_tot: Se True, pula Tree of Thought (modo rapido)
            turbo: Se True, ativa Modo Offline Turbinado
            fragmentar: Se True, ativa modo Bolo Desconstruido
            token_a_bloco: Se True (padrao), modo LLM caseiro
            modo_ia: "zero" (0 IA), "kg" (+KG), "conselho" (+Conselho), "maximo" (+LLM 7b), "auto" (decide)
        """
        # Quality Loop: tenta com menos IA, sobe se qualidade insuficiente
        if modo_ia != "maximo":
            return self._executar_com_qualidade(texto, modo_ia)
        
        if token_a_bloco:
            return self._executar_token_a_bloco(texto)
        
        if fragmentar:
            return self._executar_fragmentado(texto)
        
        # Se tem TaskPlanner e a pergunta e complexa, usa plano avancado
        if self.task_planner and self._detectar_complexidade(texto):
            print(f'[Pipeline] Pergunta complexa detectada, usando TaskPlanner')
            plano = self.task_planner.planejar(texto)
            # Executa cada subtarefa do TaskPlanner via ToolOrchestrator
            respostas = []
            for sub in plano:
                ferramenta = sub.get('ferramenta', '')
                params = sub.get('params', {})
                if ferramenta and self.tool_orchestrator:
                    r = self.tool_orchestrator.executar(ferramenta, params)
                    if r.get('sucesso'):
                        respostas.append(str(r['resultado']))
                elif ferramenta == 'perguntar_ia' and self.ia:
                    pergunta = params.get('pergunta', sub.get('descricao', texto))
                    r = self.ia.gerar(pergunta, 0.4, 'pesado')
                    if r:
                        respostas.append(r)
            if respostas:
                resultado = '\n\n'.join(respostas)
                return resultado, {'status': 'OK', 'plano': len(plano), 'sucesso': len(respostas)}
            # Fallback: se TaskPlanner falhou, continua pipeline normal
        
        from modulos.progress_tracker import iniciar as _trk_iniciar, reportar as _trk_report, concluir as _trk_concluir, erro as _trk_erro, limpar as _trk_limpar
        from modulos.session_cache import iniciar_sessao, salvar_passo, passo_ja_executado, concluir_sessao, resumir_sessao, obter_resposta_completa
        
        _trk_limpar()  # Limpa estado anterior (do kernel)
        _trk_iniciar(pipeline='pipeline_executor')
        self._skip_tot = skip_tot
        t0 = time.time()
        
        # Passo 1: Planejar
        _trk_report('Planner', 'criando plano', 0.05)
        plano = self.planner.criar_plano(texto)
        print(f'[Pipeline] Plano com {len(plano)} solicitacoes')
        
        # Inicia sessao com cache (detecta resume automaticamente)
        sessao = iniciar_sessao('pipeline', texto, plano)
        
        # Se for resume, carrega respostas ja salvas no FragmentManager
        if not sessao.get('nova'):
            print(f'[Pipeline] RESUMINDO sessao anterior — passo {sessao["ultimo_passo"]+1}/{sessao["total_passos"]}')
            for idx_str, dados in sessao.get('passos_completados', {}).items():
                idx = int(idx_str)
                self.frag_manager.salvar(dados['resposta'], idx, dados['tool'])
        
        # Passo 2: Executar cada solicitacao em sequencia (pulando as ja executadas)
        for i, item in enumerate(plano):
            # Verifica se ja foi executado (resume)
            resposta_cache = passo_ja_executado(i)
            if resposta_cache:
                print(f'[Pipeline] {i+1}/{len(plano)}: {item["tool"]} — {item["solicitacao"]}... [CACHE]')
                continue  # Pula — ja foi executado na sessao anterior
            
            print(f'[Pipeline] {i+1}/{len(plano)}: {item["tool"]} - {item["solicitacao"]}...')
            _trk_report('Pipeline', f'solicitacao {i+1}/{len(plano)}', 0.1 + (0.6 * (i / len(plano))))
            resposta = self._executar_item(item, texto, indice=i)
            self.frag_manager.salvar(resposta, i, item['tool'])
            salvar_passo(i, item['tool'], item['solicitacao'], resposta)
        
        # Passo 3: Montar resposta final
        fragmentos = self.frag_manager.obter_todos()
        resposta_final = self.assembler.montar(fragmentos)
        
        # Passo 4: Revisar
        revisao = self.reviewer.revisar(resposta_final, fragmentos)
        _trk_report('Pipeline', 'montando resposta', 0.9)
        tempo_total = round(time.time() - t0, 1)
        print(f'[Pipeline] OK ({tempo_total}s) — {len(plano)} solicitacoes, {revisao["status"]}')
        
        # Marca sessao como concluida
        concluir_sessao()
        _trk_concluir()
        return resposta_final, revisao
    
    def _validar_resposta(self, pergunta, resposta, params):
        """Valida resposta: agora apenas relata fatos. Sem aprovado/reprovado."""
        if not resposta or len(resposta) < 20:
            return resposta
        
        try:
            from modulos.validation_pipeline import ValidationPipeline
            from modulos.kg import KnowledgeGraph
            from modulos.pattern_engine import PatternEngine
            
            _kg_v = self.kg or KnowledgeGraph()
            _pe_v = PatternEngine()
            _vp = ValidationPipeline(kg=_kg_v, pe=_pe_v, ia=self.ia)
            
            resultado = _vp.validar(pergunta, resposta)
            
            # Mostra relatorio de fatos
            for estagio in resultado.get('estagios', []):
                print(f'  [Validation] {estagio["nome"]}: {estagio["detalhes"]}')
            
            return resposta
            
        except Exception as e:
            print(f'  [Validation] ERRO: {e}')
        
        return resposta
    
    def _executar_fragmentado(self, texto):
        """Modo Bolo Desconstruido RECURSIVO: fragmenta por entropia, processa folhas, reconstroi bottom-up.
        
        Cada nivel de fragmentacao e guiado pela entropia (PatternEngine).
        Folhas (padroes brutos) usam IA leve com prompt < 500 chars.
        Reconstrucao bottom-up: folhas -> galhos -> raiz.
        """
        from modulos.session_cache import iniciar_sessao, salvar_passo, concluir_sessao
        from modulos.progress_tracker import reportar as _trk_report
        
        t0 = __import__('time').time()
        
        # FASE 0: CONSULTA APRENDIZADOS PASSADOS (ciclo de aprendizado)
        contexto_aprendizado = ""
        if self.kg:
            try:
                from modulos.pattern_engine import PatternEngine
                _pe_temp = PatternEngine()
                _tokens = _pe_temp.tokenizar(texto, 'texto')
                _fp = _pe_temp.fingerprint(_tokens)
                # Busca no KG por aprendizado anterior com fingerprint similar
                _lessons_passadas = self.kg.buscar(f"ciclo:", max_r=3)
                for _l in _lessons_passadas:
                    if _l.get('ctx') == 'ciclo_aprendizado':
                        _sol = _l.get('solucao', '')
                        if _sol:
                            contexto_aprendizado = f"[APRENDIZADO ANTERIOR] Resposta similar encontrada no KG: {_sol}"
                            print(f'  [Ciclo] Aprendizado anterior encontrado!')
                            break
            except Exception as _e:
                print(f'  [Ciclo] Consulta: {_e}')
        
        if contexto_aprendizado:
            texto = contexto_aprendizado + '\n\n[PERGUNTA ATUAL]\n' + texto
            print(f'  [Ciclo] Contexto de aprendizado injetado')
        
        # FASE 0.5: CALCULA EIXO REAL DO CODIGO FONTE (nao inventado pelo modelo)
        eixo_real_str = ""
        try:
            from modulos.pattern_engine import PatternEngine as _PEr
            _pe_r = _PEr()
            _tokens_totais = []
            _modulos_dir = os.path.join(BASE, 'Scripts', 'mcr_devia', 'modulos')
            for _f in sorted(os.listdir(_modulos_dir)):
                if _f.endswith('.py') and not _f.startswith('_'):
                    _fp = os.path.join(_modulos_dir, _f)
                    try:
                        with open(_fp, 'r', encoding='utf-8', errors='replace') as _fh:
                            _codigo = _fh.read()
                        _tokens_totais.extend(_pe_r.tokenizar(_codigo, 'codigo'))
                    except:
                        pass
            if _tokens_totais:
                _eixo_real = _pe_r.eixo_nirvana_caos(_tokens_totais)
                eixo_real_str = f"[MEU EIXO NIRVANA-CAOS REAL: {_eixo_real:.3f}]\n"
                print(f'  [Eixo] Eixo real calculado: {_eixo_real:.3f}')
                texto = eixo_real_str + texto
        except Exception as _eixo_err:
            print(f'  [Eixo] Erro: {_eixo_err}')
        
        # 1. Fragmentacao RECURSIVA por entropia
        print(f'[Pipeline] Decompondo recursivamente por entropia...')
        arvore = None
        try:
            if hasattr(self.ctx_crew, 'fragmentar'):
                arvore = self.ctx_crew.fragmentar(texto)
                folhas = self.ctx_crew.extrair_folhas(arvore)
                print(f'[Pipeline] Arvore: {len(folhas)} folhas (padroes brutos) em {arvore.get("profundidade", 0)} niveis')
            else:
                arvore = {'texto': texto, 'bruto': True, 'profundidade': 0, 'filhos': None}
                folhas = [{'texto': texto, 'entropia': 0.5, 'profundidade': 0}]
        except Exception as e:
            print(f'[Pipeline] Decomposicao: {e}')
            arvore = {'texto': texto, 'bruto': True, 'profundidade': 0, 'filhos': None}
            folhas = [{'texto': texto, 'entropia': 0.5, 'profundidade': 0}]
        
        _trk_report('Reconstructor', f'decomp: {len(folhas)} folhas', 0.1)
        
        # 2. Inicia sessao cache
        iniciar_sessao('fragmentado', texto, folhas)
        
        # 3. Reconstrucao BOTTOM-UP (processa arvore inteira)
        print(f'[Pipeline] Reconstrucao bottom-up...')
        _trk_report('Reconstructor', 'reconstruindo', 0.5)
        
        from modulos.reconstructor import Reconstructor
        recon = Reconstructor(kg=self.kg, ia=self.ia, pe=getattr(self, '_pe', None), tools=self.tool_orchestrator)
        resultado = recon.reconstruir(arvore, texto)
        
        resposta_final = resultado.get('resposta_final', '')
        tempo_total = round(__import__('time').time() - t0, 1)
        
        folhas_count = resultado.get('folhas_processadas', 0)
        niveis = resultado.get('niveis', 0)
        eixo = resultado.get('eixo_final', 0.5)
        
        print(f'[Pipeline] Decomp Recursiva OK ({tempo_total}s) - {folhas_count} folhas, {niveis} niveis, {len(resposta_final)} chars, eixo {eixo:.3f}')
        
        # FASE 5: REGISTRO AUTOMATICO NO KG (hash curto, sem poluir)
        if resposta_final and self.kg and len(resposta_final) > 50:
            try:
                from modulos.pattern_engine import PatternEngine
                _pe_reg = PatternEngine()
                _fp_pergunta = _pe_reg.fingerprint(_pe_reg.tokenizar(texto, 'texto'))
                _fp_resposta = _pe_reg.fingerprint(_pe_reg.tokenizar(resposta_final, 'texto'))
                _hash = hashlib.md5(str(_fp_pergunta).encode()).hexdigest()
                
                self.kg.aprender(
                    erro=f'ciclo_hash:{_hash}',
                    causa=f'folhas={folhas_count}',
                    solucao=f'{len(resposta_final)} chars',
                    ctx='ciclo_aprendizado'
                )
                print(f'  [Ciclo] Aprendizado registrado: {_fp_str}')
                
                # Tambem registra na memoria episodica
                try:
                    from modulos.episodic_memory import EpisodicMemory
                    _mem = EpisodicMemory()
                    _mem.registrar(texto, resposta_final, f'ciclo: eixo={eixo:.2f}')
                except Exception:
                    pass
            except Exception as _reg_err:
                print(f'  [Ciclo] Registro: {_reg_err}')
        
        concluir_sessao()
        
        return resposta_final, {
            'status': 'OK' if resposta_final else 'FALHA',
            'folhas': folhas_count,
            'niveis': niveis,
            'tamanho': len(resposta_final),
            'eixo_final': eixo,
        }
    
    def _executar_token_a_bloco(self, texto):
        """Modo token-a-bloco: gera UM bloco por vez, valida, repete.
        
        Mesmo pipeline (Weaver + Reconstructor + 7b), mas em loop.
        Cada iteracao gera UM paragrafo, valida se pode continuar,
        e repete ate a resposta estar completa.
        Nao cria nada novo — so usa o que ja existe em loop.
        """
        from modulos.progress_tracker import reportar as _trk_report
        from modulos.reconstructor import Reconstructor
        from modulos.pattern_engine import PatternEngine
        from modulos.validation_pipeline import ValidationPipeline
        from modulos.kg import KnowledgeGraph
        import time as _time
        
        t0 = _time.time()
        print(f'[Pipeline] Modo token-a-bloco ativado')
        
        # Prepara componentes (ja existentes)
        _kg_v = self.kg or KnowledgeGraph()
        _pe_v = PatternEngine()
        _recon = Reconstructor(kg=_kg_v, ia=self.ia, pe=_pe_v)
        _vp = ValidationPipeline(kg=_kg_v, pe=_pe_v, ia=self.ia)
        
        resposta = ""
        MAX_BLOCOS = 15
        
        for ciclo in range(MAX_BLOCOS):
            print(f'  [Token-a-bloco] Ciclo {ciclo+1}/{MAX_BLOCOS}')
            _trk_report('TokenABloco', f'ciclo {ciclo+1}', ciclo/MAX_BLOCOS)
            
            # 1. Gera proximo bloco
            bloco = _recon.gerar_proximo_bloco(texto, resposta)
            if not bloco or len(bloco) < 10:
                print(f'  [Token-a-bloco] Bloco vazio — finalizando')
                break
            
            print(f'  [Token-a-bloco] Bloco gerado: {len(bloco)} chars')
            
            # 2. Valida completude
            tentativa = resposta + bloco
            validacao = _vp.validar(texto, tentativa)
            
            # 3. Extrai decisao do V8
            decisao = 'CONTINUAR'
            for estagio in validacao.get('estagios', []):
                if estagio.get('nome') == 'Completude':
                    decisao = estagio.get('decisao', 'CONTINUAR')
                    break
            
            if decisao == 'REFAZER':
                print(f'  [Token-a-bloco] Rejeitado — tentando de novo')
                continue
            
            resposta = tentativa
            print(f'  [Token-a-bloco] Aceito ({len(resposta)} chars total, decisao={decisao})')
            
            if decisao == 'COMPLETO':
                print(f'  [Token-a-bloco] Resposta completa — {ciclo+1} ciclos')
                break
        
        tempo_total = round(_time.time() - t0, 1)
        print(f'[Pipeline] Token-a-bloco OK ({tempo_total}s) — {len(resposta)} chars, {ciclo+1} ciclos')
        
        return resposta, {
            'status': 'OK' if resposta else 'FALHA',
            'tamanho': len(resposta),
            'ciclos': ciclo + 1,
        }
    

    def _executar_com_qualidade(self, texto, modo_ia="auto"):
        """Quality Loop: tenta com menos IA, sobe de nivel se qualidade insuficiente.
        
        Niveis:
          0 - Pi Engine (Markov + PatternEngine, 0 IA, 0 KG)
          1 - +KG Weaver (fingerprint + lessons, 0 IA)
          2 - +Conselho votado (score historico, 0 IA)
          3 - +LLM 7b (fallback final)
        
        Cada nivel gera uma resposta, o Validation Pipeline da uma nota 0-10.
        Se nota >= 8, entrega. Se nao, sobe de nivel com feedback.
        """
        from modulos.progress_tracker import reportar as _trk_report
        from modulos.validation_pipeline import ValidationPipeline
        from modulos.pattern_engine import PatternEngine
        from modulos.kg import KnowledgeGraph
        from modulos.pi_engine import PiEngine
        import time as _time
        
        t0 = _time.time()
        _kg_v = self.kg or KnowledgeGraph()
        _pe_v = PatternEngine()
        _pi = PiEngine(pe=_pe_v, kg=_kg_v)
        _vp = ValidationPipeline(kg=_kg_v, pe=_pe_v, ia=self.ia)
        
        # Decide niveis a tentar baseado no modo_ia
        if modo_ia == "zero":
            niveis = ['pi']
        elif modo_ia == "kg":
            niveis = ['pi', 'kg']
        elif modo_ia == "conselho":
            niveis = ['pi', 'kg', 'conselho']
        elif modo_ia == "auto":
            # Decide baseado na entropia
            entropia = _pi.avaliar_entropia(texto)
            if entropia < 0.4:
                niveis = ['pi']
            elif entropia < 0.65:
                niveis = ['pi', 'kg']
            elif entropia < 0.85:
                niveis = ['pi', 'kg', 'conselho']
            else:
                niveis = ['pi', 'kg', 'conselho', 'llm']
            print(f'  [Qualidade] Entropia {entropia:.2f} -> niveis: {niveis}')
        else:
            niveis = ['pi', 'kg', 'conselho', 'llm']
        
        resposta = ""
        feedback = ""
        nivel_atual = ""
        
        for nivel in niveis:
            nivel_atual = nivel
            print(f'  [Qualidade] Tentando nivel: {nivel}')
            _trk_report('Qualidade', nivel, niveis.index(nivel)/len(niveis))
            
            if nivel == 'pi':
                # Pi Engine: Markov extrapolation (0 IA, 0 KG)
                resposta = _pi.continuar_padrao(texto)
                
            elif nivel == 'kg':
                # KG Weaver: fingerprint + lessons
                from modulos.reconstructor import Reconstructor
                _recon = Reconstructor(kg=_kg_v, ia=self.ia, pe=_pe_v, tools=self.tool_orchestrator)
                catalogo = _recon._catalogar(texto)
                contexto = _recon._tecer_contexto(catalogo)
                
                if contexto.get('principal'):
                    resposta = contexto['principal']
                if contexto.get('codigo'):
                    resposta += '\n' + contexto['codigo']
                if not resposta:
                    continue  # Tenta proximo nivel
                
            elif nivel == 'conselho':
                # Conselho votado + BlankFiller (0 IA)
                from modulos.blank_filler import BlankFiller
                _bf = BlankFiller()
                resposta = _bf.preencher_tudo(texto, modo='cadeia')
                if not resposta or len(resposta) < 30:
                    continue
                
            elif nivel == 'llm':
                # LLM 7b fallback (ultimo recurso)
                if hasattr(self, '_executar_token_a_bloco'):
                    from modulos.reconstructor import Reconstructor
                    _recon2 = Reconstructor(kg=_kg_v, ia=self.ia, pe=_pe_v)
                    
                    # Gera via token-a-bloco
                    resposta = ""
                    for ciclo in range(10):
                        bloco = _recon2.gerar_proximo_bloco(texto, resposta)
                        if not bloco or len(bloco) < 10:
                            break
                        resposta += " " + bloco
                    
                    if not resposta:
                        # Fallback: chamada direta 7b
                        if self.ia:
                            prompt = f"[PERGUNTA]\n{texto}\n\n[RESPOSTA]:"
                            resposta = self.ia.gerar(prompt, 0.3, 'pesado') or ""
            
            # Valida a resposta
            if resposta and len(resposta) > 20:
                validacao = _vp.validar(texto, resposta)
                nota = validacao.get('nota_geral', 0)
                print(f'  [Qualidade] Nivel {nivel}: {len(resposta)} chars, nota {nota}')
                
                if nota >= 8.0 or nivel == niveis[-1]:
                    # Aprovado ou ultimo nivel
                    tempo_total = round(_time.time() - t0, 1)
                    print(f'[Pipeline] OK ({tempo_total}s) nivel={nivel}, nota={nota}, {len(resposta)} chars')
                    
                    # Aprende no KG
                    try:
                        _kg_v.aprender(
                            erro=f'resposta_{nivel}: {texto}',
                            causa=f'nivel={nivel}, nota={nota}',
                            solucao=f'{resposta}',
                            ctx=f'resposta_{nivel}'
                        )
                    except Exception:
                        pass
                    
                    return resposta, {
                        'status': 'OK', 'tamanho': len(resposta),
                        'nivel': nivel, 'nota': nota, 'tempo': tempo_total
                    }
                else:
                    feedback = f'Nota {nota} insuficiente. Subindo nivel...'
                    print(f'  [Qualidade] {feedback}')
        
        # Se chegou aqui, todos os niveis falharam
        tempo_total = round(_time.time() - t0, 1)
        return resposta or "Nao foi possivel gerar resposta.", {
            'status': 'FALHA', 'tamanho': len(resposta or ''),
            'nivel': nivel_atual, 'tempo': tempo_total
        }
    def _executar_ia_fragmento(self, prompt, frag):
        """Executa um fragmento via IA leve. Prompt < 2K chars."""
        if self.ia:
            try:
                return self.ia.gerar(prompt, 0.3, 'leve') or "[IA] Sem resposta"
            except Exception:
                pass
        # Fallback
        from modulos.util import gerar as _gerar_g
        return _gerar_g(prompt, 0.3, "leve") or "[IA] Sem resposta"
    
    def _executar_item(self, item: Dict, texto_original: str, indice: int = 0) -> str:
        """Executa um item do plano."""
        tool = item.get('tool', 'IA')
        solicitacao = item.get('solicitacao', '')
        
        if tool == 'PYTHON':
            return self._executar_python(solicitacao, texto_original)
        elif tool == 'TASKLIST':
            return self._executar_tasklist()
        else:
            return self._executar_ia(solicitacao, indice)
    
    def _executar_python(self, solicitacao: str, texto_original: str = "") -> str:
        """Executa comandos Python para responder UMA solicitacao especifica."""
        resultados = []
        s = solicitacao.lower()
        
        # Hora/data (da propria solicitacao)
        if any(p in s for p in ['hora', 'horario', 'data', 'dia']):
            agora = _dt.datetime.now()
            resultados.append(f"Sao {agora.strftime('%H:%M:%S')} do dia {agora.strftime('%d/%m/%Y')}")
        
        # Tempo para alvos (da propria solicitacao)
        for match in re.finditer(r'(?:segundos|minutos|horas|dias)\s+(?:para|em|ate)\s+(.+?)(?:\?|$)', solicitacao, re.IGNORECASE):
            alvo = match.group(1).strip().lower()
            agora = _dt.datetime.now()
            try:
                if any(a in alvo for a in ['amanha', 'meia-noite']):
                    alvo_dt = agora.replace(hour=0, minute=0, second=0, microsecond=0) + _dt.timedelta(days=1)
                elif re.search(r'20\d{2}', alvo):
                    ano = int(re.search(r'(20\d{2})', alvo).group(1))
                    alvo_dt = _dt.datetime(ano, 1, 1, 0, 0, 0)
                else:
                    continue
                diff = int((alvo_dt - agora).total_seconds())
                if diff > 0:
                    resultados.append(f"Faltam {diff} segundos ({diff//60} min, {diff//3600} h)")
            except Exception:
                pass
        
        # Matematica
        for m in re.finditer(r'(\d+)\s*[\*x]\s*(\d+)', solicitacao):
            a, b = int(m.group(1)), int(m.group(2))
            resultados.append(f"{a} x {b} = {a*b}")
        for m in re.finditer(r'(\d+)\s*\+\s*(\d+)', solicitacao):
            a, b = int(m.group(1)), int(m.group(2))
            resultados.append(f"{a} + {b} = {a+b}")
        
        # PI
        if 'pi' in s or 'π' in solicitacao:
            resultados.append("PI = 3.1415926535897932384626433832795...")
        
        if resultados:
            return '\n'.join(resultados)
        return f"[PYTHON] Nao foi possivel processar: {solicitacao}"
    
    def _executar_tasklist(self) -> str:
        """Executa tasklist do Windows."""
        try:
            r = subprocess.run(
                'tasklist /fi "STATUS eq running" /nh',
                capture_output=True, text=True, timeout=15, shell=True
            )
            if r.stdout:
                linhas = [l for l in r.stdout.split('\n') if l.strip() and not l.startswith('=')]
                return f"Processos ativos: {len(linhas)}"
        except Exception:
            pass
        return "Não foi possível verificar os processos."
    
    def _executar_ia(self, solicitacao: str, indice: int = 0) -> str:
        """Executa uma solicitacao via IA com Context Reinforcer.
        TODO: 1. CR extrai termos + valida + weblearn + gera instrucao
              2. ctx_infinity dos fragmentos anteriores
              3. Chama Orquestrador com contexto reforcado"""
        from modulos.progress_tracker import reportar as _trk_report, step as _trk_step
        # Verifica skip_tot: atributo do objeto OU env var (para subprocessos)
        skip_tot = getattr(self, '_skip_tot', False) or os.environ.get('MCR_SKIP_TOT') == '1'
        if not self.orquestrador:
            return f"[IA] Orquestrador indisponivel para: {solicitacao}"
        
        # DETECCAO DE ESCOPO: pergunta e sobre MCR ou conhecimento geral?
        termos_mcr = ['mcr', 'projeto mcr', 'tibia', 'canary', 'otserv', 'otclient',
                     'spa', 'shc', 'eridanus', 'dominio', 'elemental',
                     'servidor de tibia', 'npc', 'monster', 'lua script',
                     'progressao', 'aventureiro', 'habilidades contextuais']
        s_lower = solicitacao.lower()
        e_pergunta_geral = not any(t in s_lower for t in termos_mcr)
        
        # KG FORCE V2: SEMPRE injeta contexto + OBRIGACAO de uso
        try:
            from modulos.kg import KnowledgeGraph
            _kg_local = self.kg or KnowledgeGraph()
            _buscar = _kg_local.buscar_expandido if hasattr(_kg_local, 'buscar_expandido') else _kg_local.buscar
            _lessons = _buscar(solicitacao, max_r=5)
            if _lessons:
                _ctx_kg = '\n'.join([f'- {l.get("erro","")}: {l.get("solucao","")}' for l in _lessons])
                solicitacao = (
                    "[FATOS DO KG — VOCE DEVE USAR ESTES DADOS NA RESPOSTA]\n"
                    + _ctx_kg +
                    "\n[/KG]\n\n"
                    "[REGRA ABSOLUTA]\n"
                    "- SUA RESPOSTA DEVE CITAR ARQUIVOS E LINHAS ESPECIFICAS DO CODIGO\n"
                    "- SUA RESPOSTA DEVE USAR PELO MENOS 2 FATOS DO KG ACIMA\n"
                    "- NAO seja generico — se poderia ser sobre QUALQUER projeto, esta ERRADA\n"
                    "- NAO trate metrica continua como dicotomia (eixo NAO e ordem vs caos)\n"
                    "- PatternEngine NAO guia nem aconselha — ele ANALISA, TOKENIZA, CALCULA\n\n"
                    "[PERGUNTA]\n" + solicitacao
                )
                print(f'  [Pipeline] KG Force V2 injetado: {len(_lessons)} lessons + regras')
        except Exception as _kg_err:
            print(f'  [Pipeline] KG Force: {_kg_err}')
        
        if e_pergunta_geral:
            print(f'  [Pipeline] Escopo: CONHECIMENTO GERAL (pulando CR + Enricher + MCR context)')
            # Pula direto para Orquestrador sem contexto MCR
            try:
                params = {
                    'pergunta': solicitacao,
                    'identidade': '',
                    'instrucao_contexto': '',
                    'contexto_enriquecido': '',
                    'escopo': 'geral',  # Sinaliza para orquestrador nao injetar contexto MCR
                }
                resultado = self.orquestrador.executar('perguntar', params, consulta=solicitacao, temp=0.4)
                if resultado and resultado.get('sucesso'):
                    return resultado['resposta']
            except Exception as e:
                print(f'[Pipeline] ERRO: {e}')
            # Fallback: IA generica sem pipeline
            try:
                from modulos.util import gerar as _gerar_g
                return _gerar_g(solicitacao, 0.4, "pesado") or "[IA] Sem resposta"
            except Exception:
                pass
            return "[IA] Nao foi possivel responder"
        
        print(f'  [Pipeline] Escopo: MCR (ativando CR + Enricher + ToT)')
        
        # 0. Context Reinforcer: extrai, valida, aprende, desambigua
        _trk_report('CR', 'iniciando', 0.1)
        cr_contexto = ""
        cr_instrucao = ""
        solicitacao_mod = solicitacao  # Pode ser modificada pelo CR
        cr_termos = []
        try:
            from modulos.context_reinforcer import ContextReinforcer
            cr = ContextReinforcer(ctx_crew=self.ctx_crew, kg=self.kg)
            _trk_step('chamando CR')
            print(f'  [Pipeline] Chamando CR...')
            cr_result = cr.reforcar(solicitacao, self.ctx_crew)
            _trk_step('CR concluido')
            cr_termos = cr_result.get('termos', [])
            if cr_result.get('instrucao'):
                cr_instrucao = cr_result['instrucao']
                print(f'  [Pipeline] CR instrucao: {cr_instrucao.strip()}')
            if cr_result.get('contexto') and cr_result.get('valido'):
                cr_contexto = f"\n[CONTEXTO VALIDADO]\n{cr_result['contexto']}\n[/CONTEXTO]\n"
                print(f'  [Pipeline] CR contexto valido ({len(cr_contexto)} chars)')
            elif cr_result.get('aprendeu'):
                print(f'  [Pipeline] CR: weblearn disparado, contexto pode ser fraco')
        except Exception as e:
            print(f'  [CR] ERRO: {e}')
        
        # 0.5. Context Enricher: gera conteudo NOVO para enriquecer resposta
        _trk_report('Enricher', 'iniciando', 0.25)
        cr_instrucao_limpa = ""
        contexto_enriquecido = ""
        try:
            from modulos.context_enricher import ContextEnricher
            enricher = ContextEnricher(ctx_crew=self.ctx_crew, kg=self.kg)
            _trk_step('chamando Enricher')
            print(f'  [Pipeline] Chamando Enricher...')
            enr_result = enricher.enriquecer(solicitacao, cr_termos)
            if enr_result.get('valido') and enr_result.get('conteudo'):
                contexto_enriquecido = enr_result['conteudo']
                print(f'  [Pipeline] Enricher OK: tipo={enr_result["tipo"]} ({enr_result["tempo"]}s)')
            else:
                print(f'  [Pipeline] Enricher: sem conteudo viavel')
        except Exception as e:
            print(f'  [Pipeline] Enricher ERRO: {e}')
        
        # FORÇA: CR + Enricher na propria pergunta (LLM nao pode ignorar)
        if cr_instrucao and contexto_enriquecido:
            instr_limpa = cr_instrucao.replace('[INSTRUCAO]','').replace('\n','').strip()
            # Monta pergunta com contexto EMBUTIDO (modelo NAO pode ignorar)
            solicitacao_mod = (
                f"CONTEXTO OBRIGATORIO: {instr_limpa}\n\n"
                f"DADOS PARA USAR NA RESPOSTA:\n{contexto_enriquecido}\n\n"
                f"Com base no contexto e dados acima, responda: {solicitacao}\n\n"
                f"IMPORTANTE: USE os dados fornecidos. NAO seja generico."
            )
            print(f'  [Pipeline] Pergunta FORCADA com CR+Enricher ({len(solicitacao_mod)} chars)')
        elif cr_instrucao:
            instr_limpa = cr_instrucao.replace('[INSTRUCAO]','').replace('\n','').strip()
            solicitacao_mod = f"CONTEXTO: {instr_limpa}\n\nPergunta: {solicitacao}"
            print(f'  [Pipeline] Pergunta modificada com CR ({len(solicitacao_mod)} chars)')
        
        # 1. Carrega ctx_infinity dos fragmentos anteriores
        ctx_infinity = ""
        try:
            conv_path = os.path.join(SANDBOX, '.mcr_conversa.jsonl')
            if os.path.exists(conv_path):
                with open(conv_path, 'r', encoding='utf-8') as f:
                    linhas = [json.loads(l) for l in f if l.strip()]
                if linhas:
                    ctx_infinity = '\n'.join([
                        l.get('msg', '') for l in linhas[-15:]
                    ])
        except Exception:
            pass
        
        _trk_report('Pipeline', 'montando params', 0.4)
        
        # 2. Chama Orquestrador COM contexto reforcado + Tree of Thought
        try:
            params = {
                'pergunta': solicitacao_mod,
                'identidade': self.identidade,
            }
            if ctx_infinity:
                params['ctx_infinity'] = ctx_infinity
            if cr_instrucao:
                params['instrucao_contexto'] = cr_instrucao
            if cr_contexto:
                params['contexto_extra'] = cr_contexto
            
            # TREE OF THOUGHT: 3 perspectivas paralelas + sintese (pula se skip_tot)
            if not skip_tot:
                from modulos.tree_of_thought import TreeOfThought
                _trk_report('ToT', '3 perspectivas paralelas', 0.55)
                tot = TreeOfThought(orquestrador=self.orquestrador)
                tot_result = tot.pensar(solicitacao_mod, params, turbo=getattr(self, "_turbo", False))
                
                if tot_result.get('resposta') and not tot_result.get('erro'):
                    resposta = tot_result['resposta']
                    print(f'  [Pipeline] ToT resposta ({len(resposta)} chars, {tot_result["tempo_total"]}s)')
                    
                    # Pos-validacao do enriquecimento
                    if contexto_enriquecido and resposta:
                        palavras_import = re.findall(r'\b[a-zA-Z]+/[a-zA-Z/]+\b|(?<=  )[a-zA-Z_]+\.\w+', contexto_enriquecido)
                        if palavras_import:
                            encontradas = sum(1 for p in palavras_import if p.lower() in resposta.lower())
                            if encontradas < 2:
                                print(f'  [Pipeline] ToT resposta nao usou enriquecimento. Fallback para Orquestrador direto.')
                                _trk_report('ToT', 'fallback Orquestrador', 0.6)
                                resultado = self.orquestrador.executar('perguntar', params, consulta=solicitacao_mod, temp=0.4)
                                if resultado and resultado.get('sucesso'):
                                    resposta = resultado['resposta']
                    
                    # VALIDATION PIPELINE + SELF-CORRECT
                    resposta = self._validar_resposta(solicitacao_mod, resposta, params)
                    return resposta
                
                print(f'  [Pipeline] ToT falhou. Usando Orquestrador direto.')
            else:
                print(f'  [Pipeline] ToT PULADO (modo rapido). Usando Orquestrador direto.')
            
            # Fallback: Orquestrador direto (ou skip_tot ativo)
            _trk_report('Orquestrador', 'gerando resposta', 0.65)
            resultado = self.orquestrador.executar('perguntar', params, consulta=solicitacao_mod, temp=0.4)
            if resultado and resultado.get('sucesso'):
                resposta = resultado['resposta']
                resposta = self._validar_resposta(solicitacao_mod, resposta, params)
                return resposta
        except Exception as e:
            print(f'[Pipeline] ERRO ToT: {e}')
            # Fallback: Orquestrador direto
            try:
                resultado = self.orquestrador.executar('perguntar', params, consulta=solicitacao_mod, temp=0.4)
                if resultado and resultado.get('sucesso'):
                    return resultado['resposta']
            except Exception:
                pass
        
        _trk_report('Pipeline', 'resposta obtida', 0.95)
        return f"[IA] Nao foi possivel responder: {solicitacao}"
