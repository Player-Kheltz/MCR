"""Emergir — Reconhecimento automatico de padroes emergentes.
Extraido de master_agent.py para modularizacao.

Engine de EMERGIR: combina topicos distantes do KG, gera insights Z
criativos, expande com visao critica (cenario, padrao, potencial),
e aprende novos conhecimentos no KG.
"""
import os, sys, time, re, random, hashlib, json as _json

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class EmergirEngine:
    """Motor do sistema EMERGIR — reconhecimento de padroes emergentes."""
    
    def __init__(self, ia, kg, log_callback=None, execution_count_getter=None):
        self._ia = ia
        self._kg = kg
        self._log = log_callback or (lambda e, m: None)
        self._get_count = execution_count_getter or (lambda: 0)
        self._combinacoes_feitas = set()
    
    # ===== AMOSTRAGEM =====
    
    def amostrar_topicos(self, n=3):
        """Amostra N lessons de contextos DIFERENTES no KG."""
        try:
            lessons = self._kg.data.get('licoes', [])
            ativas = [l for l in lessons if not l.get('inactive', False)]
            if len(ativas) < 2: return []
            from collections import defaultdict
            por_ctx = defaultdict(list)
            for l in ativas:
                por_ctx[l.get('ctx', 'geral')].append(l)
            ctxs_validos = [c for c, ls in por_ctx.items() if len(ls) >= 1]
            if len(ctxs_validos) < 2:
                return random.sample(ativas, min(n, len(ativas)))
            n_ctxs = min(n, len(ctxs_validos))
            ctxs_escolhidos = random.sample(ctxs_validos, n_ctxs)
            topicos = []
            for ctx in ctxs_escolhidos:
                candidatos = [c for c in por_ctx[ctx] if len(c.get('solucao', '')) > 50]
                if candidatos:
                    topicos.append(random.choice(candidatos))
            return topicos
        except Exception:
            return []
    
    def gerar_fingerprint(self, topicos):
        """Gera fingerprint MD5 ordem-independente para combinacao."""
        textos = []
        for t in topicos:
            texto = f"{t.get('erro','')} {t.get('ctx','')}"
            texto = re.sub(r'[^a-z0-9\s]', '', texto.lower().strip())
            textos.append(' '.join(sorted(texto.split())))
        return hashlib.md5('|'.join(sorted(textos)).encode()).hexdigest()
    
    def gerar_pergunta(self, topicos):
        """Decider gera pergunta 'E se X com Y?' combinando topicos."""
        try:
            from modulos.decider import Decider
            decider = Decider(self._ia)
            descs = '\n'.join(
                f"{i+1}. {t.get('erro','')}: {t.get('solucao','')}"
                for i, t in enumerate(topicos)
            )
            dados = decider.extrair_json(
                texto=descs,
                esquema_exemplo={"pergunta": ""},
                instrucao=(
                    "Crie uma pergunta CRIATIVA e INESPERADA que combine "
                    "esses topicos de forma inovadora.\n"
                    "A pergunta deve comecar com 'E se' ou "
                    "'O que aconteceria se'.\n"
                    "O objetivo: gerar algo NOVO (Z) que nao estava "
                    "explicito em nenhum dos topicos originais."
                ),
                exemplos=[
                    ("1. SPA: Sistema de Progressao do Aventureiro\n2. Arvores de Natal festivas",
                     {"pergunta": "E se o SPA fosse usado para fazer as arvores de Natal do servidor evoluirem com cada quest sazonal completada?"}),
                    ("1. Eridanus: Cidade inicial portuaria\n2. Ciclo Dia-Noite: Iluminacao dinâmica",
                     {"pergunta": "E se a marinha de Eridanus saisse para pescar apenas a noite, revelando criaturas marinhas luminescentes que guiam barcos perdidos?"}),
                ]
            )
            return dados.get('pergunta', '').strip()
        except Exception:
            return ''
    
    # ===== AUTO-AVALIACAO =====
    
    def autoavaliar(self, pergunta, resposta, topicos):
        """Pergunta a SI MESMO se o insight e genuinamente novo."""
        if len(resposta) < 100:
            return False
        try:
            desc_topicos = '\n'.join(f"- {t.get('erro','')}" for t in topicos)
            prompt = (
                f"[SISTEMA]\nAnalise se a resposta abaixo contem um padrao "
                f"GENUINAMENTE NOVO ou apenas repete conhecimento obvio.\n\n"
                f"[TOPICOS ORIGINAIS]\n{desc_topicos}\n\n"
                f"[PERGUNTA CRIATIVA]\n{pergunta}\n\n"
                f"[RESPOSTA]\n{resposta}\n\n"
                f"[PERGUNTA]\n"
                f"Essa resposta revela uma conexao NAO-OBVIA entre os topicos?\n"
                f"Responda APENAS com 'SIM' ou 'NAO'."
            )
            r = self._ia.fast(prompt, 0.1, 'ultra_leve')
            return 'SIM' in r.upper()
        except Exception:
            return True
    
    def verificar_alucinacao(self, texto):
        """Verifica se resposta contem expansoes erradas de siglas MCR."""
        if not texto:
            return True
        proibidos = [
            r'FAST\s*\([^)]*FastAPI', r'FAST\s*\([^)]*Authentication',
            r'SPA\s*\([^)]*Single\s*Page', r'SHC\s*\([^)]*Sistema\s*Hospitalar',
            r'SHC\s*\([^)]*Health',
        ]
        for padrao in proibidos:
            if re.search(padrao, texto, re.IGNORECASE):
                self._log('EMERGIR', f'Alucinacao (regex): {padrao}')
                return False
        try:
            prompt = (
                f"[SISTEMA]\nConceitos oficiais MCR (Tibia OTServ):\n"
                f"FAST = Decider (classificador universal)\n"
                f"SPA = Sistema de Progressao do Aventureiro\n"
                f"SHC = Sistema de Habilidades Contextuais\n\n"
                f"[TEXTO]\n{texto}\n\n"
                f"[PERGUNTA]\nO texto explica ALGUMA sigla de forma ERRADA?\n"
                f"Ex: 'FAST = FastAPI' (errado), 'SPA = Single Page' (errado).\n"
                f"Se houver erro, diga QUAL sigla esta errada.\n"
                f"Se NAO houver erro, responda EXATAMENTE: OK"
            )
            r = self._ia.fast(prompt, 0.1, 'ultra_leve') or ""
            if 'OK' not in r.upper() and 'NENHUM' not in r.upper():
                if any(s in r.upper() for s in ['FASTAPI', 'FAST API', 'SINGLE PAGE', 'HOSPITALAR', 'HEALTH']):
                    self._log('EMERGIR', f'Alucinacao (FAST): {r}')
                    return False
            return True
        except Exception:
            return True
    
    # ===== STREAMING =====
    
    def _gerar_com_stream(self, prompt, temp, tarefa, nome_secao, label_secao=""):
        """Gera texto com streaming SSE + fallback batch."""
        from modulos.sse_server import emit
        t0 = time.time()
        emit('narrator', f'{label_secao or nome_secao}...')
        emit('prompt', {'modelo': tarefa, 'temp': temp, 'texto': prompt, 'secao': nome_secao, 'timestamp': t0})
        texto = [""]
        counter = [0]
        def on_token(chunk, acumulado):
            texto[0] = acumulado
            counter[0] += 1
            if counter[0] % 3 == 0:
                emit('token', {'chunk': chunk, 'acumulado': acumulado, 'secao': nome_secao})
            if counter[0] % 50 == 0:
                elapsed = time.time() - t0
                emit('status', {'tokens': counter[0], 'tps': round(counter[0]/elapsed, 1) if elapsed > 0 else 0, 'elapsed': round(elapsed, 1)})
        resultado = self._ia.gerar_stream(prompt, temp, tarefa, callback_token=on_token)
        if resultado is None:
            emit('narrator', 'Streaming indisponivel — usando modo batch...')
            resultado = self._ia.gerar(prompt, temp, tarefa) or ""
            if resultado:
                emit('token', {'chunk': resultado, 'acumulado': resultado, 'secao': nome_secao, 'batch': True})
        if resultado:
            emit('narrator', '[OK] {}: {} chars'.format(label_secao or nome_secao, len(resultado)))
        else:
            emit('narrator', '[FALHA] {}: modelo nao respondeu'.format(label_secao or nome_secao))
            emit('error', {'msg': '{}: timeout ou erro'.format(label_secao or nome_secao)})
        return resultado or ""
    
    # ===== FRAGMENTADOR =====
    
    def gerar_fragmentado(self, pergunta, topicos, ctx_enriquecido=""):
        """Gera resposta emergente em 4 secoes fragmentadas."""
        from modulos.sse_server import emit
        secoes = []
        contexto = ""
        desc_topicos = '\n'.join(f'- {t.get("erro","")}: {t.get("solucao","")}' for t in topicos)
        ID = ("MCR = servidor customizado de Tibia (OTServ)\n"
              "FAST = Decider (classificador). NAO e FastAPI.\n"
              "SPA = Sistema de Progressao do Aventureiro\n"
              "SHC = Sistema de Habilidades Contextuais\n"
              "V12 = Cache inteligente do Knowledge Graph\n"
              "NAO invente expansoes para siglas.")
        
        # SECAO 1
        emit('stage', {'name': 'analise_topicos', 'label': 'Secao 1: Analise dos topicos', 'progress': 0.3})
        p1 = (f"[SISTEMA]\nVoce e um ANALISTA do projeto MCR (Tibia OTServ).\nContexto do projeto:\n{ID}\n\n"
              f"[CONTEXTO ADICIONAL DOS TOPICOS]\n{ctx_enriquecido}\n\n[TOPICOS]\n{desc_topicos}\n\n"
              f"[INSTRUCAO]\nExplique CADA topico individualmente em profundidade:\n- O que significa?\n"
              f"- Por que e relevante para o projeto MCR?\n- Qual seu contexto?\n"
              f"Seja especifico e detalhado. Responda em PT-BR.")
        r1 = self._gerar_com_stream(p1, 0.3, 'analisar', 'analise_topicos', 'Analisando cada topico em profundidade')
        if r1 and len(r1) > 50:
            secoes.append(f"### ANALISE DOS TOPICOS\n{r1}")
            contexto = '\n\n'.join(secoes)
        
        # SECAO 2: Z
        emit('stage', {'name': 'conexao_z', 'label': 'Secao 2: Conexao Z criativa', 'progress': 0.42})
        p2 = (f"[SISTEMA]\nVoce e um CRIATIVO do projeto MCR.\n{ID}\n\n"
              f"[CONTEXTO ANTERIOR]\n{contexto}\n\n[PERGUNTA CRIATIVA]\n{pergunta}\n\n"
              f"[INSTRUCAO]\nQual a CONEXAO NAO-OBVIA entre esses topicos?\n"
              f"O que Z revela que nao estava explicito antes?\n"
              f"Pense em analogias, metaforas, possibilidades inesperadas.\nSeja ousado e original. Responda em PT-BR.")
        r2 = self._gerar_com_stream(p2, 0.8, 'leve', 'conexao_z', 'Buscando conexao NAO-OBVIA entre os topicos')
        if r2 and len(r2) > 50:
            z_exp = self._expandir_z(r2, pergunta, contexto)
            r2c = f"{r2}\n\n{z_exp}" if z_exp else r2
            secoes.append(f"### A CONEXAO EMERGENTE (Z)\n{r2c}")
            contexto = '\n\n'.join(secoes)
        
        # SECAO 3: Implicacoes
        emit('stage', {'name': 'implicacoes_praticas', 'label': 'Secao 3: Implicacoes praticas', 'progress': 0.7})
        p3 = (f"[SISTEMA]\nVoce e um ARQUITETO do projeto MCR.\n{ID}\n\n"
              f"[CONTEXTO ANTERIOR]\n{contexto}\n\n[INSTRUCAO]\n"
              f"Com base em tudo acima, quais as IMPLICACOES PRATICAS dessa conexao no projeto MCR (Tibia OTServ)?\n"
              f"- O que muda no desenvolvimento?\n- Que novas ferramentas ou sistemas surgem?\n"
              f"- Como implementar essa ideia?\n- Que riscos ou desafios existem?\n"
              f"Seja concreto e acionavel. Responda em PT-BR.")
        r3 = self._gerar_com_stream(p3, 0.3, 'analisar', 'implicacoes_praticas', 'Mapeando implicacoes praticas')
        if r3 and len(r3) > 50:
            secoes.append(f"### IMPLICACOES PRATICAS\n{r3}")
            contexto = '\n\n'.join(secoes)
        
        # SECAO 4: Sintese
        emit('stage', {'name': 'sintese', 'label': 'Secao 4: Sintese final', 'progress': 0.82})
        p4 = (f"[SISTEMA]\nVoce e um SINTETIZADOR.\n"
              f"[CONTEXTO ANTERIOR]\n{contexto}\n\n[INSTRUCAO]\n"
              f"Escreva UM PARAGRAFO de sintese que capture a ESSENCIA do insight emergente.\n"
              f"Seja conciso e impactante. Maximo 5 frases. Responda em PT-BR.")
        r4 = self._gerar_com_stream(p4, 0.5, 'leve', 'sintese', 'Sintetizando insight')
        if r4 and len(r4) > 30:
            secoes.append(f"### SINTESE\n{r4}")
        
        if not secoes:
            return ""
        resposta = '\n\n'.join(secoes)
        self._log('EMERGIR', f'Fragmentador: {len(secoes)} secoes, {len(resposta)} chars total')
        return resposta
    
    # ===== EXPANSAO CRITICA DO Z =====
    
    def _expandir_z(self, z_cru, pergunta, contexto_anterior):
        """Expande o insight Z com 3 visoes usando BlankFiller (cadeia)."""
        from modulos.sse_server import emit
        from modulos.blank_filler import BlankFiller
        
        bf = BlankFiller(self._ia)
        
        esqueleto = (
            f"### CENARIO CONCRETO\n@BLANK_CENARIO\n\n"
            f"### PADRAO SUBJACENTE\n@BLANK_PADRAO\n\n"
            f"### POTENCIAL TRANSFORMADOR\n@BLANK_POTENCIAL"
        )
        
        contexto = (
            f"[SISTEMA]\nProjeto MCR (Tibia OTServ). SPA = progressao.\n"
            f"[INSIGHT Z]\n{z_cru}\n[PERGUNTA]\n{pergunta}\n"
            f"{contexto_anterior}"
        )
        
        emit('stage', {'name': 'visao_z', 'label': 'Expandindo Z (3 visoes)...', 'progress': 0.55})
        emit('narrator', 'Expandindo Z com visao humana via blanks...')
        
        # Preenche em cadeia (cada blank ve os anteriores)
        resultado = bf.preencher_tudo(esqueleto, contexto, modo='cadeia')
        
        if resultado and resultado != esqueleto:
            return '### EXPANSAO CRITICA DO Z (Visao Humana)\n' + resultado
        return ""
    
    # ===== PIPELINE PRINCIPAL =====
    
    def processar(self):
        """Pipeline EMERGIR completo com checkpoint."""
        from modulos.progress_tracker import salvar_checkpoint, registrar_erro
        from modulos.sse_server import emit
        from context_crew import ContextCrew
        
        salvar_checkpoint('inicio', 0.01)
        ec = self._get_count()
        if ec % 5 != 0:
            return
        
        emit('stage', {'name': 'inicio', 'label': 'Iniciando EMERGIR V4...', 'progress': 0.01})
        
        # 1. Amostra topicos
        emit('narrator', 'Procurando topicos distantes no Knowledge Graph...')
        topicos = self.amostrar_topicos(n=3)
        if len(topicos) < 2:
            emit('narrator', 'Nao encontrei topicos suficientes.')
            return
        emit('narrator', f'Encontrei {len(topicos)} topicos DIFERENTES.')
        
        # 2. Fingerprint
        fp = self.gerar_fingerprint(topicos)
        if fp in self._combinacoes_feitas:
            emit('narrator', 'Combinacao ja tentada. Pulando.')
            return
        self._combinacoes_feitas.add(fp)
        
        # 3. Pergunta criativa
        emit('stage', {'name': 'pergunta', 'label': 'Criando pergunta E se...', 'progress': 0.05})
        pergunta = self.gerar_pergunta(topicos)
        if not pergunta:
            return
        self._log('EMERGIR', f'Combinando: {" + ".join(t.get("erro","") for t in topicos)}')
        emit('narrator', f'Pergunta gerada: "{pergunta}"')
        salvar_checkpoint('pergunta', 0.1, topicos=len(topicos))
        
        # 4. ContextCrew
        emit('stage', {'name': 'context_crew', 'label': 'Buscando contexto...', 'progress': 0.1})
        ctx_enriquecido = ""
        try:
            cc = ContextCrew()
            for t in topicos:
                ctx = cc.executar(t.get('erro', '')) or ""
                if ctx:
                    ctx_enriquecido += f"--- {t.get('erro','')} ---\n{ctx}\n"
            if ctx_enriquecido:
                self._log('EMERGIR', f'ContextCrew: {len(ctx_enriquecido)} chars')
                emit('narrator', f'Contexto enriquecido: {len(ctx_enriquecido)} chars.')
        except Exception as e:
            self._log('EMERGIR', f'ContextCrew falhou: {e}')
        
        # 5. Fragmentador
        emit('stage', {'name': 'fragmentador', 'label': 'Geracao fragmentada...', 'progress': 0.15})
        resposta = self.gerar_fragmentado(pergunta, topicos, ctx_enriquecido)
        if not resposta or len(resposta) < 200:
            emit('narrator', 'Resposta muito curta. Descartando.')
            return
        salvar_checkpoint('fragmentado', 0.6, chars=len(resposta))
        
        # 6. Autoavaliacao
        emit('stage', {'name': 'autoavalia', 'label': 'Autoavaliando...', 'progress': 0.85})
        if not self.autoavaliar(pergunta, resposta, topicos):
            self._log('EMERGIR', 'Padrao descartado pela autoavaliacao.')
            emit('narrator', 'Padrao considerado ruido. Descartado.')
            return
        emit('narrator', 'SIM! Conexao genuinamente nova identificada.')
        
        # 7. Verificacao de alucinacao
        emit('stage', {'name': 'alucinacao', 'label': 'Verificando alucinacoes...', 'progress': 0.92})
        if not self.verificar_alucinacao(resposta):
            emit('narrator', 'Alucinacao detectada. Descartado.')
            return
        emit('narrator', 'Zero alucinacoes!')
        
        # 8. Salva no KG
        emit('stage', {'name': 'salvar', 'label': 'Salvando no KG...', 'progress': 0.98})
        titulo = f"[Emergente] {pergunta}"
        causa = ' + '.join(t.get('erro', '') for t in topicos)
        try:
            self._kg.aprender(erro=titulo, causa=f'De: {causa}', solucao=resposta, ctx='emergente')
            self._log('EMERGIR', f'Novo padrao aprendido ({len(resposta)} chars)')
            emit('narrator', f'Conhecimento SALVO! {len(resposta)} chars.')
            emit('result', {'sucesso': True, 'chars': len(resposta), 'secoes': 4, 'alucinacoes': 0})
            emit('stage', {'name': 'fim', 'label': 'EMERGIR concluido!', 'progress': 1.0})
            salvar_checkpoint('fim', 1.0)
        except Exception as e:
            emit('error', {'msg': str(e)})
            registrar_erro(str(e), type(e).__name__)
