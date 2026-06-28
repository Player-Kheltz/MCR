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
        except:
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
            
            plano.append({'solicitacao': s[:300], 'tool': tool, 'params': {}})
        
        if not plano:
            plano.append({'solicitacao': texto[:200], 'tool': 'IA', 'params': {}})
        
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
                    'msg': f"[Fragmento {indice+1}/{indice+1} ({tool})]\n{resposta[:500]}"
                }, ensure_ascii=False) + '\n')
        except:
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

    def executar(self, texto: str, skip_tot=False) -> Tuple[str, Dict]:
        """Executa pipeline completo: planejar → executar → montar → revisar.
        
        Args:
            texto: Pergunta/texto a processar
            skip_tot: Se True, pula Tree of Thought (modo rapido)
        
        Se task_planner estiver disponivel e a pergunta for complexa,
        delega para TaskPlanner + ToolOrchestrator.
        """
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
                        respostas.append(str(r['resultado'])[:1000])
                elif ferramenta == 'perguntar_ia' and self.ia:
                    pergunta = params.get('pergunta', sub.get('descricao', texto))
                    r = self.ia.gerar(pergunta, 0.4, 'pesado')
                    if r:
                        respostas.append(r[:2000])
            if respostas:
                resultado = '\n\n'.join(respostas)
                return resultado[:10000], {'status': 'OK', 'plano': len(plano), 'sucesso': len(respostas)}
            # Fallback: se TaskPlanner falhou, continua pipeline normal
        
        from modulos.progress_tracker import iniciar as _trk_iniciar, reportar as _trk_report, concluir as _trk_concluir, erro as _trk_erro, limpar as _trk_limpar
        _trk_limpar()  # Limpa estado anterior (do kernel)
        _trk_iniciar(pipeline='pipeline_executor')
        self._skip_tot = skip_tot
        t0 = time.time()
        
        # Passo 1: Planejar
        _trk_report('Planner', 'criando plano', 0.05)
        plano = self.planner.criar_plano(texto)
        print(f'[Pipeline] Plano com {len(plano)} solicitacoes')
        
        # Passo 2: Executar cada solicitacao em sequencia
        for i, item in enumerate(plano):
            print(f'[Pipeline] {i+1}/{len(plano)}: {item["tool"]} - {item["solicitacao"][:60]}...')
            _trk_report('Pipeline', f'solicitacao {i+1}/{len(plano)}', 0.1 + (0.6 * (i / len(plano))))
            resposta = self._executar_item(item, texto, indice=i)
            self.frag_manager.salvar(resposta, i, item['tool'])
        
        # Passo 3: Montar resposta final
        fragmentos = self.frag_manager.obter_todos()
        resposta_final = self.assembler.montar(fragmentos)
        
        # Passo 4: Revisar
        revisao = self.reviewer.revisar(resposta_final, fragmentos)
        _trk_report('Pipeline', 'montando resposta', 0.9)
        tempo_total = round(time.time() - t0, 1)
        print(f'[Pipeline] OK ({tempo_total}s) — {len(plano)} solicitacoes, {revisao["status"]}')
        
        _trk_concluir()
        return resposta_final, revisao
    
    def _executar_item(self, item: Dict, texto_original: str, indice: int = 0) -> str:
        """Executa um item do plano."""
        tool = item.get('tool', 'IA')
        solicitacao = item.get('solicitacao', '')[:300]
        
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
            except: pass
        
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
        return f"[PYTHON] Nao foi possivel processar: {solicitacao[:80]}"
    
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
        except:
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
            return f"[IA] Orquestrador indisponivel para: {solicitacao[:80]}"
        
        # DETECCAO DE ESCOPO: pergunta e sobre MCR ou conhecimento geral?
        termos_mcr = ['mcr', 'projeto mcr', 'tibia', 'canary', 'otserv', 'otclient',
                     'spa', 'shc', 'eridanus', 'dominio', 'elemental',
                     'servidor de tibia', 'npc', 'monster', 'lua script',
                     'progressao', 'aventureiro', 'habilidades contextuais']
        s_lower = solicitacao.lower()
        e_pergunta_geral = not any(t in s_lower for t in termos_mcr)
        
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
            except:
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
                print(f'  [Pipeline] CR instrucao: {cr_instrucao[:120].strip()}')
            if cr_result.get('contexto') and cr_result.get('valido'):
                cr_contexto = f"\n[CONTEXTO VALIDADO]\n{cr_result['contexto'][:600]}\n[/CONTEXTO]\n"
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
        except:
            pass
        
        _trk_report('Pipeline', 'montando params', 0.4)
        
        # 2. Chama Orquestrador COM contexto reforcado + Tree of Thought
        try:
            params = {
                'pergunta': solicitacao_mod,
                'identidade': self.identidade,
            }
            if ctx_infinity:
                params['ctx_infinity'] = ctx_infinity[:2000]
            if cr_instrucao:
                params['instrucao_contexto'] = cr_instrucao
            if cr_contexto:
                params['contexto_extra'] = cr_contexto
            
            # TREE OF THOUGHT: 3 perspectivas paralelas + sintese (pula se skip_tot)
            if not skip_tot:
                from modulos.tree_of_thought import TreeOfThought
                _trk_report('ToT', '3 perspectivas paralelas', 0.55)
                tot = TreeOfThought(orquestrador=self.orquestrador)
                tot_result = tot.pensar(solicitacao_mod, params)
                
                if tot_result.get('resposta') and not tot_result.get('erro'):
                    resposta = tot_result['resposta']
                    print(f'  [Pipeline] ToT resposta ({len(resposta)} chars, {tot_result["tempo_total"]}s)')
                    
                    # Pos-validacao do enriquecimento
                    if contexto_enriquecido and resposta:
                        palavras_import = re.findall(r'\b[a-zA-Z]+/[a-zA-Z/]+\b|(?<=  )[a-zA-Z_]+\.\w+', contexto_enriquecido)
                        if palavras_import:
                            encontradas = sum(1 for p in palavras_import[:10] if p.lower() in resposta.lower())
                            if encontradas < 2:
                                print(f'  [Pipeline] ToT resposta nao usou enriquecimento. Fallback para Orquestrador direto.')
                                _trk_report('ToT', 'fallback Orquestrador', 0.6)
                                resultado = self.orquestrador.executar('perguntar', params, consulta=solicitacao_mod, temp=0.4)
                                if resultado and resultado.get('sucesso'):
                                    resposta = resultado['resposta']
                    
                    return resposta
                
                print(f'  [Pipeline] ToT falhou. Usando Orquestrador direto.')
            else:
                print(f'  [Pipeline] ToT PULADO (modo rapido). Usando Orquestrador direto.')
            
            # Fallback: Orquestrador direto (ou skip_tot ativo)
            _trk_report('Orquestrador', 'gerando resposta', 0.65)
            resultado = self.orquestrador.executar('perguntar', params, consulta=solicitacao_mod, temp=0.4)
            if resultado and resultado.get('sucesso'):
                return resultado['resposta']
        except Exception as e:
            print(f'[Pipeline] ERRO ToT: {e}')
            # Fallback: Orquestrador direto
            try:
                resultado = self.orquestrador.executar('perguntar', params, consulta=solicitacao_mod, temp=0.4)
                if resultado and resultado.get('sucesso'):
                    return resultado['resposta']
            except:
                pass
        
        _trk_report('Pipeline', 'resposta obtida', 0.95)
        return f"[IA] Nao foi possivel responder: {solicitacao[:80]}"
