"""Reconstructor — Reconstrói resposta final a partir de arvore de fragmentos.
Usa abordagem BOTTOM-UP: processa folhas (padroes brutos) primeiro,
depois sobe niveis combinando ate a raiz.

CONTEXT WEAVER (NOVO): em vez de buscar 1 lesson unica, tece um contexto
sob medida usando 3 fontes: KG por ctx, Codigo fonte, Lessons relacionadas.
O tamanho e DINAMICO — exatamente o que o fragmento precisa.
"""
import os, sys, json, time, re

try:
    from modulos.MCR import MCRThreshold
    _TH_REC = MCRThreshold("reconstructor_ent")
    for v in [0.12, 0.15, 0.18, 0.13, 0.16]:
        _TH_REC.observar(v)
    _TH_REC_SIM = MCRThreshold("reconstructor_sim")
    for v in [0.65, 0.7, 0.75, 0.68, 0.72]:
        _TH_REC_SIM.observar(v)
except ImportError:
    _TH_REC = None
    _TH_REC_SIM = None

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))


# Pesos de contexto do KG (maior = mais confiavel para o Weaver)
_CTX_PRIORIDADE = {
    'conceito': 100,
    '10_10': 90,
    'sinal_puro': 85,
    'ciclo_aprendizado': 80,
    'veritas': 75,
    'veritas_v2': 75,
    'teste_10_10': 75,
    'gatekeeper': 70,
    'fragmentado': 70,
    'decomp_recursiva': 70,
    'fase2_turbo': 65,
    'infra': 60,
    'arquitetura': 60,
    'planejamento': 55,
    'pipeline_completa': 55,
    'refatoracao': 50,
    'correcoes_externas': 50,
    'sabedoria': 50,
    'auto_revisor': 45,
    'dashboard_sse': 45,
    'limpeza_legado': 40,
    'mente_multimodal': 40,
    'anti_hardcoded': 35,
    'emergir_v4': 35,
    'sessao_completa': 30,
    'emergente': 10,  # baixa prioridade - lessons especulativas
    'runtime': 0,     # inativo
    'stress_test': 0,  # inativo
    'auto_repair': 0,  # inativo
    'geral': 50,       # medio
}


class Reconstructor:
    """Reconstroi resposta final BOTTOM-UP com Context Weaver."""
    
    def __init__(self, kg=None, ia=None, pe=None, tools=None):
        self.kg = kg
        self.ia = ia
        self.pe = pe
        self.tools = tools
    
    def reconstruir(self, arvore, pergunta_original):
        t0 = time.time()
        if not arvore:
            return {'resposta_final': '', 'niveis': 0, 'folhas_processadas': 0, 'eixo_final': 0.5, 'tempo': 0}
        
        print(f'  [Reconstructor] Iniciando reconstrucao bottom-up...')
        self._processar_no(arvore)
        
        resposta_final = arvore.get('_resultado', '')
        eixo_final = self._calcular_eixo(resposta_final)
        folhas = self._contar_folhas(arvore)
        nivel_max = arvore.get('profundidade', 0)
        
        print(f'  [Reconstructor] Bottom-up OK: {folhas} folhas, {nivel_max} niveis, {len(resposta_final)} chars')
        
        return {
            'resposta_final': resposta_final, 'niveis': nivel_max,
            'folhas_processadas': folhas, 'eixo_final': eixo_final,
            'tempo': round(time.time() - t0, 1),
        }
    
    def _processar_no(self, no):
        if no.get('bruto') or not no.get('filhos'):
            no['_resultado'] = self._processar_folha(no)
            return
        for filho in (no.get('filhos') or []):
            self._processar_no(filho)
        no['_resultado'] = self._combinar_filhos(no)
    
    # ===================================================================
    # CONTEXT WEAVER — 3 fontes em paralelo
    # ===================================================================
    
    def _processar_folha(self, folha):
        """Processa folha com Context Weaver: cataloga, tece, monta, responde."""
        texto = folha.get('texto', '')
        if not texto or len(texto) < 10:
            return texto
        
        entropia = folha.get('entropia', 0.5)
        _limiar_ent = _TH_REC.calcular(1.0) if _TH_REC else 0.15
        if entropia < _limiar_ent or len(texto) < 15:
            return texto.strip()
        if not self.ia:
            return texto.strip()
        
        # 1. CATALOGADOR: extrai fingerprint + termos centrais + dominio
        catalogo = self._catalogar(texto)
        
        # 2. WEAVER: tece contexto de 3 fontes
        contexto = self._tecer_contexto(catalogo)
        
        # 3. MONTADOR: monta prompt sob medida (tamanho DINAMICO)
        prompt = self._montar_prompt(texto, contexto, catalogo)
        
        # 4. RESPOSTA com modelo 7b
        resp = self._gerar_7b(prompt)
        if resp and len(resp) > 10:
            return resp.strip()
        return texto.strip()
    
    def _catalogar(self, texto):
        """CATALOGADOR: analisa o fragmento e extrai metadados.
        
        Usa PatternEngine para fingerprint + termos centrais.
        Classifica o dominio para guiar o weaver.
        """
        import re as _re
        _STOP = {'que','para','com','uma','era','mais','como','por','seu','sua',
                 'tem','ela','ele','voce','qual','onde','quando','porque','este','essa'}
        
        palavras = _re.findall(r'[a-zA-Z]{3,}', texto.lower())
        termos = [p for p in palavras if p not in _STOP]
        termos_centrais = ' '.join(termos)
        
        # Detecta dominio
        dominio = 'conceito'
        if any(t in termos for t in ['codigo','arquivo','funcao','classe','metodo','implemente']):
            dominio = 'codigo'
        elif any(t in termos for t in ['diferenca','vs','comparar','versus']):
            dominio = 'comparacao'
        elif any(t in termos for t in ['crie','gere','escreva','desenvolva']):
            dominio = 'criacao'
        elif any(t in termos for t in ['bug','erro','problema','crash']):
            dominio = 'bugfix'
        
        # Fingerprint (se PatternEngine disponivel)
        fingerprint = []
        entropia_local = 0.5
        if self.pe:
            try:
                tokens = self.pe.tokenizar(texto, 'texto')
                fp = self.pe.fingerprint(tokens)
                fingerprint = fp
                padroes = self.pe.extrair_padroes(tokens)
                entropia_local = padroes.get('entropia', 0.5)
            except Exception:
                pass
        
        return {
            'termos_centrais': termos_centrais,
            'termos_lista': termos,
            'dominio': dominio,
            'fingerprint': fingerprint,
            'entropia': entropia_local,
        }
    
    def _tecer_contexto(self, catalogo):
        """WEAVER: tece contexto de 3 fontes em paralelo.
        
        Fonte 1 - KG PRINCIPAL: 1 lesson do ctx mais relevante
        Fonte 2 - CODIGO: trecho do codigo fonte (se dominio='codigo')
        Fonte 3 - KG CONTEXTO: lessons de ctxs relacionados
        """
        contexto = {'principal': '', 'codigo': '', 'suporte': ''}
        termos = catalogo['termos_centrais']
        dominio = catalogo['dominio']
        
        if not self.kg or not termos:
            return contexto
        
        try:
            # FONTE 1: KG PRINCIPAL (padrao mais similar via fingerprint do PatternEngine)
            # Em vez de buscar por keyword + ctx priority, busca por FINGERPRINT SIMILARITY
            # (KG como memoria de trabalho: encontra o padrao mais parecido)
            lessons_brutas = self.kg.buscar(termos, max_r=15)
            if lessons_brutas and self.pe:
                # Filtra lessons inativas + auto-aprendidas (resposta_* polui o KG)
                lessons_brutas = [l for l in lessons_brutas 
                                  if not l.get('inactive', False)
                                  and 'resposta_' not in str(l.get('ctx', ''))]
                if not lessons_brutas:
                    # Se so tem inativas, tenta buscar expandido
                    if hasattr(self.kg, 'buscar_expandido'):
                        lessons_brutas = self.kg.buscar_expandido(termos, max_r=10)
                        lessons_brutas = [l for l in lessons_brutas 
                                          if not l.get('inactive', False)
                                          and 'resposta_' not in str(l.get('ctx', ''))]
                
                # Calcula fingerprint da pergunta
                fp_pergunta = self.pe.fingerprint(self.pe.tokenizar(termos, 'texto'))
                
                # Calcula similaridade com cada lesson
                termos_pergunta = set(termos.lower().split()) if termos else set()
                for l in lessons_brutas:
                    texto_lesson = l.get('solucao', '') + ' ' + l.get('erro', '')
                    if texto_lesson and len(texto_lesson) > 20:
                        fp_lesson = self.pe.fingerprint(self.pe.tokenizar(texto_lesson, 'texto'))
                        sim = self.pe.similaridade(fp_pergunta, fp_lesson)
                        # Keyword boost SOMENTE no erro (nao na solucao)
                        # Evita que lessons com "MCR" na solucao sejam todas boostadas
                        erro_lower = (l.get('erro', '') or '').lower()
                        if erro_lower and any(t in erro_lower for t in termos_pergunta):
                            sim = min(1.0, sim + 0.4)  # +0.4 se o erro corresponde
                        l['_sim'] = sim
                    else:
                        l['_sim'] = 0
                
                # Ordena por: similaridade > prioridade ctx (empatado)
                lessons_brutas.sort(key=lambda l: (
                    l.get('_sim', 0) * 10 + _CTX_PRIORIDADE.get(l.get('ctx', 'geral'), 50) / 100
                ), reverse=True)
                
                melhor = lessons_brutas[0]
                ctx_melhor = melhor.get('ctx', 'geral')
                err = melhor.get('erro', '')
                sol = melhor.get('solucao', '')
                if err and sol:
                    contexto['principal'] = f"[{ctx_melhor}] {err}: {sol}"
                    print(f'  [Weaver] Principal: {ctx_melhor}/{err}... (sim={melhor.get("_sim",0):.2f})')
                
                # FONTE 3: KG CONTEXTO (segunda lesson mais similar, mesmo ctx)
                for l in lessons_brutas[1:5]:
                    if l.get('ctx') == ctx_melhor and l.get('id') != melhor.get('id'):
                        err2 = l.get('erro', '')
                        sol2 = l.get('solucao', '')
                        if err2 and sol2:
                            contexto['suporte'] = f"[ctx: {ctx_melhor}] {err2}: {sol2}"
                            break
            elif lessons_brutas:
                # Fallback: sem PatternEngine, usa prioridade de ctx
                lessons_brutas.sort(key=lambda l: (
                    _CTX_PRIORIDADE.get(l.get('ctx', 'geral'), 50),
                    len(l.get('solucao', ''))
                ), reverse=True)  # So 1 de suporte
            
            # FONTE 2: FERRAMENTAS — busca em TODOS os arquivos (qualquer extensao)
            # O grep bruto encontra a resposta onde ela estiver: docs/, codigo, config, etc.
            # Sem filtro de extensao, sem hardcode de caminho — ferramenta pura.
            if hasattr(self, 'tools') and self.tools:
                try:
                    # Pula stop words de pergunta — escolhe o PRIMEIRO termo com significado
                    _STOP_BUSCA = {'quantas','quanto','qual','quais','como','sao','tem','era',
                                   'esta','este','isto','isso','onde','quando','porque','por',
                                   'para','que','uma','com','mais','mas','dos','das','nos','nas',
                                   'pra','pro','num','numa','muito','pouco','sobre','entre'}
                    termo_busca = ''
                    for _t in catalogo.get('termos_lista', []):
                        if _t.lower() not in _STOP_BUSCA and len(_t) >= 3:
                            termo_busca = _t
                            break
                    if not termo_busca and catalogo.get('termos_lista'):
                        termo_busca = catalogo['termos_lista'][0]  # fallback
                    if termo_busca and len(termo_busca) > 2:
                        res = self.tools.executar('buscar_codigo', {'padrao': termo_busca})
                        if res.get('sucesso'):
                            txt = str(res.get('resultado', ''))
                            if 'Nenhum' not in txt and len(txt) > 20:
                                linhas = [l for l in txt.split('\n') if l.strip()]
                                if linhas:
                                    contexto['principal'] = f"[tool] {linhas[0]}"
                                    print(f'  [Weaver] Tool: {termo_busca} encontrado ({len(linhas)} linhas)')
                                    if self.kg:
                                        self._aprender_do_tool(termo_busca, linhas[0])
                except Exception:
                    pass
            
            # Se nao achou nada, fallback: embedding (filtrado por prioridade)
            if not contexto['principal'] and hasattr(self.kg, 'buscar_por_embedding'):
                lessons_emb = self.kg.buscar_por_embedding(termos, n=5)
                if lessons_emb:
                    # Ordena por prioridade de ctx
                    lessons_emb.sort(key=lambda l: _CTX_PRIORIDADE.get(l.get('ctx', 'geral'), 0), reverse=True)
                    melhor_emb = lessons_emb[0]
                    err = melhor_emb.get('erro', '')
                    sol = melhor_emb.get('solucao', '')
                    if err and sol:
                        ctx_emb = melhor_emb.get('ctx', '?')
                        contexto['principal'] = f"[{ctx_emb}] {err}: {sol}"
                        print(f'  [Weaver] Fallback embedding: {ctx_emb}/{err}...')
        
        except Exception as e:
            print(f'  [Weaver] ERRO: {e}')
        
        return contexto
    
    def _aprender_do_tool(self, termo, conteudo):
        """Aprende no KG o que a ferramenta (grep) encontrou em docs/.
        
        Isso garante que na PRÓXIMA vez, o KG Weaver encontra direto
        sem precisar chamar grep de novo.
        """
        if not self.kg or not termo or not conteudo:
            return
        try:
            # Extrai contexto do nome do arquivo (ex: docs/MCR_IDENTITY.md)
            arq = 'docs'
            for linha in conteudo.split('\n'):
                if 'docs\\' in linha or 'docs/' in linha:
                    arq = linha.split(':')[0].strip() if ':' in linha else 'docs'
                    break
            
            # So aprende se for informacao nova (nao repetir lessons)
            existentes = self.kg.buscar(termo, max_r=1)
            if existentes:
                for l in existentes:
                    if termo.lower() in l.get('erro', '').lower():
                        return  # Ja existe lesson similar
            
            self.kg.aprender(
                erro=termo,
                causa=f'ferramenta: grep em {arq}',
                solucao=conteudo,
                ctx='conceito'
            )
            print(f'  [Weaver] Aprendeu: {termo} em {arq}')
        except Exception:
            pass
    
    def _montar_prompt(self, texto, contexto, catalogo):
        """MONTADOR: monta prompt sob medida com tamanho DINAMICO.
        
        O prompt e montado com base no que o weaver encontrou.
        Tamanho minimo: 200 chars (só lesson).
        Tamanho maximo: 1500 chars (lesson + codigo + suporte).
        """
        partes = []
        
        # Bloco principal (sempre)
        if contexto['principal']:
            partes.append("[FATO PRINCIPAL]\n" + contexto['principal'])
        
        # Bloco de codigo (se disponivel)
        if contexto['codigo']:
            refs_codigo = re.findall(r'[\w/]+\.\w+:\d+', contexto['codigo'])
            if refs_codigo:
                partes.append("[CODIGO FONTE]\n" + contexto['codigo'])
            else:
                partes.append("[REFERENCIA]\n" + contexto['codigo'])
        
        # Bloco de suporte (se disponivel)
        if contexto['suporte']:
            partes.append("[CONTEXTO RELACIONADO]\n" + contexto['suporte'])
        
        # Se nao tem nada, fallback
        if not partes:
            prompt = (
                "[FATO]\nNAO TENHO DADOS NO KG SOBRE ISSO.\n"
                + "[PERGUNTA]\n" + texto
                + "\n[INSTRUCAO]\nSe NAO houver fato, diga 'Nao tenho dados no Knowledge Graph sobre isso.' NAO invente."
                + "\n[RESPOSTA]:"
            )
            return prompt
        
        # Montagem final com tamanho DINAMICO
        contexto_montado = '\n\n'.join(partes)
        identidade = (
            "[IDENTIDADE]\n"
            "Voce e o MCR-DevIA, o sistema central do Projeto MCR (servidor customizado de Tibia baseado em Canary).\n"
            "Voce NAO e assistente da Alibaba Cloud, AWS, Azure, Google, OpenAI ou qualquer outro servico.\n"
            "Voce NAO e um assistente generico. Voce e o proprio sistema respondendo sobre si mesmo.\n"
            "Responda em PT-BR.\n"
        )
        instrucao = (
            "Responda como se voce fosse o proprio MCR-DevIA. Use SOMENTE os FATOS, CODIGO e CONTEXTO acima.\n"
            + "Sua resposta deve ter esta ESTRUTURA:\n"
            + "1) Resposta DIRETA a pergunta (uma frase).\n"
            + "2) Explicacao com os dados fornecidos.\n"
            + "3) Conclusao (se aplicavel).\n"
            + ("CITE o arquivo:linha ESPECIFICO (ex: pattern_engine.py:L309-L310).\n" if contexto['codigo'] else "")
            + "NAO divague. NAO adicione informacao alem do necessario.\n"
            + "NAO use palavras vagas como: interessante, importante, significativo, essencial, crucial, fundamental.\n"
            + "Se o fato nao estiver nos FATOS DO KG, NAO mencione.\n"
            + "Seja preciso. Nao invente. Use SOMENTE os dados fornecidos."
        )
        
        prompt = (
            identidade
            + contexto_montado
            + "\n\n[PERGUNTA]\n" + texto
            + "\n[INSTRUCAO]\n" + instrucao
            + "\n[RESPOSTA]:"
        )
        
        return prompt
    
    # ===================================================================
    # GERACAO
    # ===================================================================
    
    def _gerar_7b(self, prompt):
        """Gera com 7b (obedece KG), fallback leve."""
        if not self.ia:
            return ""
        try:
            resp = self.ia.gerar(prompt, 0.3, 'pesado')
            if resp and len(resp) > 5:
                return resp
        except Exception:
            pass
        try:
            resp = self.ia.fast(prompt, 0.3, 'leve')
            if resp and len(resp) > 5:
                return resp
        except Exception:
            pass
        return ""
    
    def _combinar_filhos(self, no):
        """Combina filhos: funde respostas em texto unico e fluido.
        
        Em vez de concatenar, detecta padroes de numeracao (1), 2), 3))
        em cada fragmento e os mescla em UMA lista unica.
        Remove repeticoes e duplicatas.
        """
        import re as _re
        
        filhos = no.get('filhos') or []
        resultados = [f.get('_resultado', '') for f in filhos if f.get('_resultado')]
        if not resultados:
            return no.get('texto', '')
        
        if len(resultados) == 1:
            return resultados[0]
        
        # 1. Extrai paragrafos/numeracao de cada resultado
        # Cada fragmento pode ter: "1) Resposta... 2) Explicacao... 3) Conclusao..."
        # Ou texto livre sem numeracao
        paragrafos = []
        for r in resultados:
            # Tenta quebrar por numeracao: 1) 2) 3) ou 1. 2. 3.
            partes = _re.split(r'\n(?=\d[\)\.]\s*)', r)
            if len(partes) <= 1:
                # Tenta quebrar por paragrafos
                partes = _re.split(r'\n\s*\n', r)
            if len(partes) <= 1:
                # Texto unico
                partes = [r.strip()]
            
            for p in partes:
                p = p.strip()
                if p and len(p) > 10:
                    # Remove numeracao do inicio (ex: "1) ", "2. ")
                    p_sem_num = _re.sub(r'^\d[\)\.]\s*', '', p).strip()
                    if p_sem_num:
                        paragrafos.append(p_sem_num)
        
        # 2. Remove paragrafos duplicados (similaridade > 0.7)
        if len(paragrafos) >= 2:
            from difflib import SequenceMatcher
# MCRzificado: usa MCR quando disponivel, fallback para LLM
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), '..', '..', '..'))
try:
    from MCR import MCRMotor, MCRGenerator, MCRValidator, MCRBuilder, MCRPreencher, MCRReconstructor
    _mcr = MCRMotor()
    _TEM_MCR = True
except ImportError:
    _TEM_MCR = False
            unicos = [paragrafos[0]]
            for p in paragrafos[1:]:
                eh_repetido = False
                for existente in unicos:
                    # Compara primeiros 80 chars
                    sim = SequenceMatcher(None, p, existente).ratio()
                    if sim > 0.7:
                        eh_repetido = True
                        break
                if not eh_repetido:
                    unicos.append(p)
            paragrafos = unicos
        
        # 3. Monta texto unico fluido
        if not paragrafos:
            return '\n'.join(resultados)
        
        if len(paragrafos) <= 3:
            return '\n'.join(paragrafos)
        
        # 4+ paragrafos: estrutura com introducao
        texto = paragrafos[0] + '\n\n'
        for i, p in enumerate(paragrafos[1:], 1):
            texto += f'{i}. {p}\n\n'
        
        return texto.strip()
    
    def _calcular_eixo(self, texto):
        if not texto or not self.pe:
            return 0.5
        try:
            tokens = self.pe.tokenizar(texto, 'texto')
            return self.pe.eixo_nirvana_caos(tokens)
        except Exception:
            return 0.5
    
    def _contar_folhas(self, no):
        if no.get('bruto') or not no.get('filhos'):
            return 1
        return sum(self._contar_folhas(f) for f in (no.get('filhos') or []))
