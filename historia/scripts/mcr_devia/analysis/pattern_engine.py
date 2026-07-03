"""Pattern Engine Universal — Reconhecimento de Padrões em QUALQUER Domínio.
Tokeniza, extrai padrões, gera fingerprint, calcula eixo Nirvana-Caos,
e sugere o próximo passo ótimo — para código, texto, logs, KG, comportamento.

Uso:
    pe = PatternEngine()
    tokens = pe.tokenizar("def foo(): pass", "codigo")
    fp = pe.fingerprint(tokens)
    eixo = pe.eixo_nirvana_caos(tokens)  # 0.0 (Caos) a 1.0 (Nirvana)
"""
import os, json, re, math, ast, collections, keyword as _kw
from typing import List, Tuple, Dict, Any, Optional


class PatternEngine:
    """Engine universal de reconhecimento de padrões."""
    
    def __init__(self, ia=None, kg=None):
        self._ia = ia
        self._kg = kg
        self._cache_fingerprint = {}
    
    # ===== TOKENIZACAO =====
    
    def tokenizar(self, entrada, dominio: str = 'texto') -> List[Tuple[str, Any]]:
        """Tokeniza qualquer entrada em tokens universais.
        
        Args:
            entrada: str, list, dict — qualquer dado
            dominio: 'codigo' | 'texto' | 'logs' | 'kg' | 'comportamento'
        Returns:
            Lista de (tipo, valor)
        """
        if dominio == 'codigo':
            return self._tokenizar_codigo(entrada)
        elif dominio == 'texto':
            return self._tokenizar_texto(entrada)
        elif dominio == 'logs':
            return self._tokenizar_logs(entrada)
        elif dominio == 'kg':
            return self._tokenizar_kg(entrada)
        elif dominio == 'comportamento':
            return self._tokenizar_comportamento(entrada)
        return []
    
    def _tokenizar_codigo(self, codigo: str) -> List[Tuple]:
        """Tokeniza código Python: AST + indent + keywords."""
        tokens = []
        linhas = codigo.split('\n')
        
        # 1. Indentação de cada linha
        for linha in linhas:
            indent = len(linha) - len(linha.lstrip())
            if indent >= 0:
                tokens.append(('INDENT', indent // 4))
        
        # 2. AST nodes
        try:
            tree = ast.parse(codigo)
            for node in ast.walk(tree):
                tokens.append(('AST', type(node).__name__))
        except SyntaxError:
            tokens.append(('AST', 'SYNTAX_ERROR'))
        
        # 3. Keywords Python
        for palavra in codigo.split():
            p = palavra.strip('():;,\'"')
            if p in _kw.kwlist:
                tokens.append(('KW', p))
        
        # 4. Tamanho de funcoes (linhas entre def e return/proximo def)
        in_func = False
        func_lines = 0
        for linha in linhas:
            if linha.strip().startswith('def '):
                if in_func and func_lines > 0:
                    tokens.append(('FUNC_SIZE', func_lines))
                in_func = True
                func_lines = 0
            elif in_func:
                func_lines += 1
        if in_func and func_lines > 0:
            tokens.append(('FUNC_SIZE', func_lines))
        
        return tokens
    
    def _tokenizar_texto(self, texto: str) -> List[Tuple]:
        """Tokeniza texto: palavras, pontuação, estilo."""
        tokens = []
        palavras = re.findall(r'\w+', texto.lower()) if texto else []
        
        # Distribuição de tamanho de palavras
        for p in palavras:
            if len(p) <= 3: tokens.append(('PAL_CURTA', 1))
            elif len(p) <= 7: tokens.append(('PAL_MEDIA', 1))
            else: tokens.append(('PAL_LONGA', 1))
        
        # Pontuação (ritmo de escrita)
        for char in texto or '':
            if char in '.!?': tokens.append(('FIM_FRASE', 1))
            elif char in ',;': tokens.append(('PAUSA', 1))
        
        # Verbos de ação (marcador de estilo ativo vs passivo)
        acao = {'fazer','criar','implementar','precisar','poder','dever','querer',
                'usar','aplicar','construir','desenvolver','montar','gerar'}
        for p in palavras:
            if p in acao: tokens.append(('ACAO', 1))
        
        # Tamanho médio de frase
        frases = re.split(r'[.!?]+', texto or '')
        for f in frases:
            palavras_f = f.split()
            tokens.append(('FRASE_TAM', len(palavras_f)))
        
        return tokens
    
    def _tokenizar_logs(self, logs: list) -> List[Tuple]:
        """Tokeniza logs: tipos de evento, erros, timestamps."""
        tokens = []
        for log in (logs or []):
            if isinstance(log, str):
                tokens.append(('RAW', log))
                continue
            role = log.get('role', log.get('tipo', log.get('agente', '?')))
            tokens.append(('ROLE', str(role)))
            if log.get('erro') or log.get('error'):
                tokens.append(('ERRO', 1))
            if log.get('msg') or log.get('mensagem'):
                msg = str(log.get('msg', log.get('mensagem', '')))
                tokens.append(('MSG_SIZE', len(msg)))
        return tokens
    
    def _tokenizar_kg(self, lessons: list) -> List[Tuple]:
        """Tokeniza lessons: ctx, timestamp, tamanho."""
        tokens = []
        for l in (lessons or []):
            ctx = l.get('ctx', 'geral')
            tokens.append(('CTX', ctx))
            tokens.append(('SOL_SIZE', len(l.get('solucao', ''))))
            if l.get('tipo') == 'benchmark':
                tokens.append(('BENCH', 1))
        return tokens
    
    def _tokenizar_comportamento(self, passos: list) -> List[Tuple]:
        """Tokeniza comportamento: ações, resultados."""
        tokens = []
        for p in (passos or []):
            etapa = p.get('etapa', p.get('acao', '?'))
            tokens.append(('ETAPA', str(etapa)))
            msg = p.get('mensagem', p.get('resultado', ''))
            if 'erro' in str(msg).lower() or 'fail' in str(msg).lower():
                tokens.append(('FALHA', 1))
            else:
                tokens.append(('SUCESSO', 1))
        return tokens
    
    # ===== EXTRACAO DE PADROES =====
    
    def extrair_padroes(self, tokens: List[Tuple], n: int = 3) -> Dict:
        """Extrai padroes dos tokens: n-gramas, markov, entropia.
        
        Returns:
            {'n_gramas': {tupla: count}, 'markov': {tipo: {prox: prob}},
             'entropia': float, 'total': int}
        """
        if not tokens:
            return {'n_gramas': {}, 'markov': {}, 'entropia': 0.0, 'total': 0}
        
        # N-gramas
        n_gramas = {}
        for i in range(len(tokens) - n + 1):
            seq = tuple(t[0] for t in tokens[i:i+n])
            n_gramas[seq] = n_gramas.get(seq, 0) + 1
        
        # Markov: matriz de transicao (dado tipo A, qual a probabilidade de B?)
        markov = {}
        for i in range(len(tokens) - 1):
            t_atual = tokens[i][0]
            t_prox = tokens[i+1][0]
            if t_atual not in markov:
                markov[t_atual] = {}
            markov[t_atual][t_prox] = markov[t_atual].get(t_prox, 0) + 1
        
        # Normaliza markov para probabilidades
        for t_atual, transicoes in markov.items():
            total = sum(transicoes.values())
            for t_prox in transicoes:
                transicoes[t_prox] /= total
        
        # Entropia (Shannon): H = -sum(p * log2(p))
        total_tokens = len(tokens)
        freq = {}
        for t in tokens:
            freq[t[0]] = freq.get(t[0], 0) + 1
        
        entropia = 0.0
        for t, count in freq.items():
            p = count / total_tokens
            if p > 0:
                entropia -= p * math.log2(p)
        
        # Normaliza entropia para 0-1 (dividido por log2(num_tipos))
        num_tipos = len(freq)
        if num_tipos > 1:
            entropia /= math.log2(num_tipos)
        
        return {
            'n_gramas': dict(sorted(n_gramas.items(), key=lambda x: -x[1])),
            'markov': markov,
            'entropia': round(entropia, 4),
            'total': total_tokens,
        }
    
    # ===== FINGERPRINT =====
    
    def fingerprint(self, tokens: List[Tuple]) -> List[float]:
        """Gera fingerprint de 256 dimensoes unico para esta sequencia de tokens.
        
        Caracteristicas extraidas:
        - Distribuicao de tipos de token
        - Transicoes entre tipos (bigramas)
        - Entropia
        - Tamanho medio
        """
        if not tokens:
            return [0.0] * 64
        
        cache_key = str(tokens)  # limita para cache
        if cache_key in self._cache_fingerprint:
            return self._cache_fingerprint[cache_key]
        
        # 1. Distribuicao de tipos
        tipos = {}
        for t in tokens:
            tipos[t[0]] = tipos.get(t[0], 0) + 1
        total = len(tokens)
        
        # 2. Histograma de 16 bins (colapsa tipos em buckets)
        histograma = [0.0] * 16
        tipos_ordenados = sorted(tipos.keys())
        for i, t in enumerate(tipos_ordenados):
            bucket = hash(t) % 16
            histograma[bucket] += tipos[t] / total
        
        # 3. Transicoes entre tipos (bigramas em 16 buckets)
        transicoes = [0.0] * 16
        for i in range(len(tokens) - 1):
            b1 = hash(tokens[i][0]) % 16
            b2 = hash(tokens[i+1][0]) % 16
            idx = b1  # combina os dois buckets
            transicoes[idx] += 1
        max_t = max(transicoes) if max(transicoes) > 0 else 1
        transicoes = [t / max_t for t in transicoes]
        
        # 4. Metricas globais
        metricas = [
            min(1.0, total / 500),      # densidade (max 500)
            self._entropia_amostra(tokens),  # entropia normalizada
            sum(1 for t in tokens if t[0] == 'AST') / max(total, 1),
            sum(1 for t in tokens if t[0].startswith('PAL')) / max(total, 1),
            sum(1 for t in tokens if t[0] == 'ERRO') / max(total, 1),
            sum(1 for t in tokens if t[0] == 'FUNC_SIZE' and t[1] > 30) / max(total, 1),
        ]
        
        # Monta vetor de 64 dimensoes
        fp = histograma + transicoes + metricas + [0.0] * (64 - 16 - 16 - len(metricas))
        fp = fp
        
        self._cache_fingerprint[cache_key] = fp
        return fp
    
    def _entropia_amostra(self, tokens):
        """Calcula entropia normalizada (0-1) de uma amostra de tokens."""
        freq = {}
        for t in tokens:
            freq[t[0]] = freq.get(t[0], 0) + 1
        n = len(tokens)
        if n == 0:
            return 0.0
        h = 0.0
        for f in freq.values():
            p = f / n
            if p > 0:
                h -= p * math.log2(p)
        n_tipos = len(freq)
        if n_tipos > 1:
            h /= math.log2(n_tipos)
        return h
    
    def similaridade(self, fp_a: List[float], fp_b: List[float]) -> float:
        """Calcula similaridade por cosseno entre dois fingerprints."""
        if not fp_a or not fp_b:
            return 0.0
        dot = sum(a * b for a, b in zip(fp_a, fp_b))
        na = math.sqrt(sum(a * a for a in fp_a))
        nb = math.sqrt(sum(b * b for b in fp_b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)
    
    # ===== EIXO NIRVANA-CAOS =====
    
    def eixo_nirvana_caos(self, tokens: List[Tuple]) -> float:
        """Calcula onde a entrada esta no eixo Nirvana (1.0) ↔ Caos (0.0).
        
        Pondera:
        - Baixa entropia = mais ordem = mais proximo do Nirvana
        - Baixa frequencia de anti-padroes = mais Nirvana
        - Funcoes curtas = mais Nirvana
        """
        if not tokens:
            return 0.5
        
        padroes = self.extrair_padroes(tokens)
        entropia = padroes.get('entropia', 0.5)
        
        # Fatores que puxam para o Caos
        fator_caos = 0.0
        peso_total = 0
        
        # 1. Entropia (alta = caos)
        fator_caos += entropia * 3
        peso_total += 3
        
        # 2. Anti-padroes conhecidos
        tipos_token = [t[0] for t in tokens]
        if 'ERRO' in tipos_token:
            fator_caos += 0.5
        if 'SYNTAX_ERROR' in tipos_token:
            fator_caos += 1.0
        
        peso_total += 1
        
        # 3. Funcoes grandes (>30 linhas) = tendencia ao caos
        funcs_grandes = sum(1 for t in tokens if t[0] == 'FUNC_SIZE' and t[1] > 30)
        funcs_totais = sum(1 for t in tokens if t[0] == 'FUNC_SIZE')
        if funcs_totais > 0:
            fator_caos += (funcs_grandes / funcs_totais) * 0.5
            peso_total += 0.5
        
        # Normaliza
        eixo = 1.0 - (fator_caos / peso_total) if peso_total > 0 else 0.5
        return max(0.0, min(1.0, eixo))
    
    # ===== SUGESTAO =====
    
    def sugerir_proximo(self, tokens: List[Tuple], padroes: Dict = None) -> str:
        """Sugere o proximo passo para ir em direcao ao Nirvana.
        
        Se IA estiver disponivel, usa LLM para analise.
        Senao, usa heuristica.
        """
        if not tokens:
            return "Nao ha dados suficientes para analise."
        
        eixo = self.eixo_nirvana_caos(tokens)
        
        if self._ia:
            # Resumo dos tokens para o prompt
            tipos = {}
            for t in tokens:
                tipos[t[0]] = tipos.get(t[0], 0) + 1
            resumo = ', '.join(f'{k}: {v}' for k, v in sorted(tipos.items(), key=lambda x: -x[1]))
            
            prompt = (
                f"[SISTEMA]\nVoce e um oraculo de padroes. Analise o estado atual "
                f"e sugira o PROXIMO PASSO para melhorar.\n\n"
                f"[ESTADO ATUAL]\n"
                f"Eixo Nirvana-Caos: {eixo:.2f} (0=Caos, 1=Nirvana)\n"
                f"Tokens: {resumo}\n"
                f"Total de tokens: {len(tokens)}\n\n"
                f"[PERGUNTA]\nQual o PROXIMO PASSO para aproximar do Nirvana?\n"
                f"Sugira UMA acao especifica. Responda em PT-BR."
            )
            return self._ia.gerar(prompt, 0.3, 'leve') or "Nao foi possivel gerar sugestao."
        
        # Heuristica fallback
        if eixo < 0.3:
            return "O sistema esta proximo do Caos. Priorize a correcao de anti-padroes e reducao de complexidade."
        elif eixo < 0.6:
            return "O sistema esta moderado. Foque em refinamento e consistencia."
        else:
            return "O sistema esta proximo do Nirvana. Monitore para evitar regressao."
    
    # ===== APRENDIZADO =====
    
    def aprender(self, entrada: Any, resultado: Any, dominio: str = 'texto'):
        """Salva o padrao descoberto no KG."""
        if not self._kg:
            return
        try:
            tokens = self.tokenizar(entrada, dominio)
            fp = self.fingerprint(tokens)
            eixo = self.eixo_nirvana_caos(tokens)
            
            self._kg.aprender(
                erro=f'pattern: {dominio} | eixo: {eixo:.2f}',
                causa=f'Tokens: {len(tokens)} | Fingerprint: {fp}...',
                solucao=json.dumps({'fingerprint': fp, 'eixo': eixo,
                                     'entropia': self.extrair_padroes(tokens).get('entropia', 0)},
                                    ensure_ascii=False),
                ctx='pattern_learn'
            )
        except Exception:
            pass
    
    # ===== KG PATTERN ANALYZE (Modo Offline Turbinado) =====
    
    def kg_pattern_analyze(self, kg, consulta: str) -> Dict:
        """Analisa padroes no Knowledge Graph para encontrar conceitos relacionados.
        
        Usa buscar_expandido() + tokenizacao interna para identificar:
        - Conceitos mais proximos da consulta
        - Eixo Nirvana-Caos de cada conceito
        - Padroes entre ctxs diferentes
        
        Args:
            kg: KnowledgeGraph instance
            consulta: str, pergunta/texto para buscar padroes
        
        Returns:
            dict: {conceitos, eixos, padroes_ctx, sugestao}
        """
        if not kg:
            return {'erro': 'KG nao disponivel'}
        
        # 1. Busca expandida no KG
        lessons = kg.buscar_expandido(consulta, max_r=15)
        if not lessons:
            return {'erro': 'Nenhuma lesson encontrada'}
        
        # 2. Tokeniza cada lesson
        conceitos = []
        for l in lessons:
            tokens = self._tokenizar_kg([l])
            fp = self.fingerprint(tokens)
            eixo = self.eixo_nirvana_caos(tokens)
            conceitos.append({
                'id': l.get('id', '?'),
                'ctx': l.get('ctx', 'geral'),
                'erro': l.get('erro', ''),
                'eixo': round(eixo, 3),
                'fingerprint': fp,
            })
        
        # 3. Identifica padroes entre ctxs
        ctxs = {}
        for c in conceitos:
            ctx = c['ctx']
            if ctx not in ctxs:
                ctxs[ctx] = {'count': 0, 'eixos': []}
            ctxs[ctx]['count'] += 1
            ctxs[ctx]['eixos'].append(c['eixo'])
        
        padroes_ctx = {}
        for ctx, dados in ctxs.items():
            eixo_medio = sum(dados['eixos']) / len(dados['eixos']) if dados['eixos'] else 0.5
            padroes_ctx[ctx] = {
                'ocorrencias': dados['count'],
                'eixo_medio': round(eixo_medio, 3),
            }
        
        # 4. Sugestao baseada nos padroes
        ctxs_baixo = [ctx for ctx, d in padroes_ctx.items() if d['eixo_medio'] < 0.5]
        ctxs_alto = [ctx for ctx, d in padroes_ctx.items() if d['eixo_medio'] >= 0.7]
        
        sugestao = ""
        if ctxs_baixo:
            sugestao += f"Atencao aos ctxs com baixo eixo: {', '.join(ctxs_baixo)}. "
        if ctxs_alto:
            sugestao += f"Contextos solidos: {', '.join(ctxs_alto)}. "
        if not sugestao:
            sugestao = "Padroes internos estaveis."
        
        return {
            'conceitos': conceitos,
            'padroes_ctx': padroes_ctx,
            'total_encontrados': len(conceitos),
            'ctxs_distintos': len(padroes_ctx),
            'sugestao': sugestao.strip(),
        }
    
    # ===== ANALISE COMPLETA =====
    
    def analisar(self, entrada: Any, dominio: str = 'texto') -> Dict:
        """Pipeline completa: tokenizar → padroes → fingerprint → eixo."""
        tokens = self.tokenizar(entrada, dominio)
        padroes = self.extrair_padroes(tokens)
        fp = self.fingerprint(tokens)
        eixo = self.eixo_nirvana_caos(tokens)
        sugestao = self.sugerir_proximo(tokens, padroes)
        
        return {
            'dominio': dominio,
            'tokens': len(tokens),
            'tipos': dict(collections.Counter(t[0] for t in tokens)),
            'padroes': padroes,
            'fingerprint': fp,  # amostra
            'eixo_nirvana_caos': round(eixo, 3),
            'sugestao': sugestao,
        }
