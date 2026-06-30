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
from collections import Counter


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
    
    # ===================================================================
    # TOKENIZACAO UNIVERSAL — descobre o dominio automaticamente
    # ===================================================================
    
    def tokenizar_universal(self, entrada) -> List[Tuple[str, Any]]:
        """Tokeniza QUALQUER entrada sem precisar de dominio fixo.
        
        Detecta o tipo Python e roteia para o tokenizador adequado:
        - bytes → _tokenizar_bytes()
        - str → AST (codigo), JSON, texto_v2, texto classico
        - list → cada item vira token
        - dict → chaves viram tipos
        - outros → RAW
        
        Returns:
            List[Tuple[str, Any]] — mesmo formato de tokenizar()
        """
        import ast as _ast_uni, json as _json_uni
        
        if isinstance(entrada, bytes):
            return self._tokenizar_bytes(entrada)
        
        elif isinstance(entrada, str):
            # Tenta AST (codigo Python)
            try:
                _ast_uni.parse(entrada)
                return self._tokenizar_codigo(entrada)
            except SyntaxError:
                pass
            
            # Tenta JSON
            try:
                _json_uni.loads(entrada)
                return [('FORMAT_JSON', entrada[:200])]
            except Exception:
                pass
            
            # Tenta lexico_v2 PRIMEIRO (antes de SUSPEITO_CODIGO)
            try:
                from modulos.lexico_v2 import tokenizar_v2 as _tv2
                tokens_v2_raw = _tv2(entrada)
                tokens_v2 = [(t[0], t[1]) for t in tokens_v2_raw] if tokens_v2_raw else []
                if tokens_v2:
                    tipos = set(t[0] for t in tokens_v2)
                    if not tipos.issubset({'PAL_CURTA', 'PAL_MEDIA', 'PAL_LONGA'}):
                        # Se tambem parece codigo, adiciona marcador
                        if re.search(r'\b(function|local|end|if|then|else|for|while|return)\b', entrada):
                            tokens_v2.append(('SUSPEITO_CODIGO', 1))
                        return tokens_v2
            except ImportError:
                pass
            
            # Detecta padroes de codigo nao-Python (Lua, C, JS)
            # NOTA: 'do' nao esta aqui porque 'do MCR' em portugues nao e keyword
            if re.search(r'\b(function|local|end|if|then|else|for|while|return|import|class|def|var|let|const)\b', entrada):
                tokens = self._tokenizar_texto(entrada)
                tokens.append(('SUSPEITO_CODIGO', 1))
                return tokens
            
            # Fallback: texto classico
            tokens_cls = self._tokenizar_texto(entrada)
            
            # Se entropia > 0.8, tenta descobrir estrutura
            if tokens_cls:
                try:
                    padroes = self.extrair_padroes(tokens_cls)
                    if padroes.get('entropia', 1.0) > 0.8:
                        return self._tokenizar_desconhecido(entrada)
                except Exception:
                    pass
            
            return tokens_cls
        
        elif isinstance(entrada, (list, tuple)):
            tokens = []
            for i, item in enumerate(entrada[:50]):
                if isinstance(item, str):
                    tokens.append(('LIST_ITEM', item[:200]))
                elif isinstance(item, (int, float)):
                    tokens.append(('LIST_NUM', item))
                elif isinstance(item, dict):
                    for k, v in item.items():
                        tokens.append((f'DICT_{k}', str(v)[:100]))
                elif isinstance(item, (list, tuple)):
                    tokens.append(('LIST_SUB', f'{len(item)} itens'))
                else:
                    tokens.append(('LIST_RAW', str(item)[:100]))
            return tokens
        
        elif isinstance(entrada, dict):
            tokens = []
            for k, v in entrada.items():
                if isinstance(v, (str, int, float, bool)):
                    tokens.append((f'KEY_{k}', str(v)[:200]))
                elif isinstance(v, (list, tuple)):
                    tokens.append((f'KEY_{k}', f'list[{len(v)}]'))
                elif isinstance(v, dict):
                    tokens.append((f'KEY_{k}', f'dict[{len(v)}]'))
                else:
                    tokens.append((f'KEY_{k}', str(type(v).__name__)))
            return tokens
        
        else:
            return [('RAW', str(entrada)[:500])]
    
    # ===================================================================
    # TOKENIZACAO FRAGMENTADA — quebra pergunta em intencoes multiplas
    # ===================================================================
    
    def tokenizar_fragmentado(self, texto: str, max_fragmentos: int = 5) -> List[Dict]:
        """Fragmenta o texto e tokeniza CADA fragmento separadamente.
        
        Usa SuperFragmentador para quebrar perguntas complexas
        em frases independentes (separadas por '.', '?', '!', '\\n').
        Cada fragmento vira uma lista de tokens separada.
        
        Args:
            texto: pergunta do usuario (pode conter multiplas intencoes)
            max_fragmentos: maximo de fragmentos a processar
            
        Returns:
            List[Dict]: cada dict tem:
                - 'fragmento': str, o texto do fragmento
                - 'tokens': List[Tuple], tokens do fragmento
                - 'tipos': List[str], tipos unicos em ordem
                - 'intencao': (cat, params, conf) ou None
        """
        if not texto or len(texto) < 10:
            # Texto curto, nao fragmenta
            tokens = self.tokenizar_universal(texto)
            tipos = list(dict.fromkeys([t[0] for t in tokens])) if tokens else []
            return [{
                'fragmento': texto,
                'tokens': tokens or [],
                'tipos': tipos,
                'intencao': None,
            }]
        
        # Tentativa 1: divisao por pontuacao (perguntas com multiplas intencoes)
        resultados = []
        frases = re.split(r'[.!?\n]+(?:\s+|$)', texto)
        frases_validas = [f.strip() for f in frases if len(f.strip()) > 10]
        
        if len(frases_validas) >= 2:
            # Pergunta tem multiplas intencoes — usa divisao por frases
            for frase in frases_validas[:max_fragmentos]:
                tokens = self.tokenizar_universal(frase)
                tipos = list(dict.fromkeys([t[0] for t in tokens])) if tokens else []
                resultados.append({
                    'fragmento': frase,
                    'tokens': tokens or [],
                    'tipos': tipos,
                    'intencao': None,
                })
            return resultados
        
        # Tentativa 2: SuperFragmentador (textos longos com paragrafos)
        try:
            from analysis.fragmenter import SuperFragmentador
            frag = SuperFragmentador()
            fragmentos = frag.fragmentar(texto)
            for f in fragmentos[:max_fragmentos]:
                conteudo = f.conteudo if hasattr(f, 'conteudo') else str(f)
                if not conteudo or len(conteudo) < 5:
                    continue
                tokens = self.tokenizar_universal(conteudo)
                tipos = list(dict.fromkeys([t[0] for t in tokens])) if tokens else []
                resultados.append({
                    'fragmento': conteudo,
                    'tokens': tokens or [],
                    'tipos': tipos,
                    'intencao': None,
                })
            if resultados:
                return resultados
        except Exception:
            pass
        
        # Tentativa 3: fallback — texto unico
        if len(frases_validas) == 1:
            tokens = self.tokenizar_universal(frases_validas[0])
            tipos = list(dict.fromkeys([t[0] for t in tokens])) if tokens else []
            return [{
                'fragmento': frases_validas[0],
                'tokens': tokens or [],
                'tipos': tipos,
                'intencao': None,
            }]
        
        # Fallback final
        tokens = self.tokenizar_universal(texto)
        tipos = list(dict.fromkeys([t[0] for t in tokens])) if tokens else []
        return [{
            'fragmento': texto,
            'tokens': tokens or [],
            'tipos': tipos,
            'intencao': None,
        }]
    
    # ===================================================================
    # TOKENIZACAO DE BYTES — descobre formato por magic + distribuicao
    # ===================================================================
    
    def _tokenizar_bytes(self, data: bytes) -> List[Tuple[str, Any]]:
        """Tokeniza bytes BRUTOS — apenas header + amostra estrutural.
        
        Nao le o arquivo todo. So header (16B) + amostra (4KB)
        para detectar magic bytes, entropia, e blocos repetidos.
        """
        if not data or len(data) < 4:
            return [('BINARY_EMPTY', 0)]
        
        tokens = []
        tamanho = len(data)
        tokens.append(('BINARY_SIZE', tamanho))
        
        # FASE 1: Magic bytes
        header = data[:16]
        MAGIC_MAP = [
            (b'\x89PNG\r\n\x1a\n', 'FORMAT_PNG'),
            (b'\x7fELF', 'FORMAT_ELF'),
            (b'PK\x03\x04', 'FORMAT_ZIP'),
            (b'GIF8', 'FORMAT_GIF'),
            (b'\xff\xd8\xff', 'FORMAT_JPEG'),
            (b'%PDF', 'FORMAT_PDF'),
            (b'MZ', 'FORMAT_PE'),
            (b'\x00\x00\x00\x1cftyp', 'FORMAT_MP4'),
            (b'RIFF', 'FORMAT_AVI_WAV'),
            (b'\x1f\x8b\x08', 'FORMAT_GZIP'),
            (b'BZh', 'FORMAT_BZ2'),
            (b'\xca\xfe\xba\xbe', 'FORMAT_CLASS'),
            (b'\xef\xbb\xbf', 'FORMAT_UTF8_BOM'),
            (b'\xff\xfe', 'FORMAT_UTF16_LE'),
            (b'\xfe\xff', 'FORMAT_UTF16_BE'),
        ]
        formato = 'BINARY_UNKNOWN'
        for magic, nome in MAGIC_MAP:
            if header[:len(magic)] == magic:
                formato = nome
                break
        tokens.append(('BINARY_FORMAT', formato))
        
        # FASE 2: Distribuicao de bytes (amostra 4KB)
        amostra = data[:4096]
        n = len(amostra)
        if n > 0:
            freq_byte = [0] * 256
            for b in amostra:
                freq_byte[b] += 1
            n_distintos = sum(1 for f in freq_byte if f > 0)
            tokens.append(('BINARY_BYTE_DIVERSITY', n_distintos))
            
            entropia = 0.0
            for f in freq_byte:
                if f > 0:
                    p = f / n
                    entropia -= p * math.log2(p)
            entropia_norm = entropia / 8.0
            tokens.append(('BINARY_ENTROPY', round(entropia_norm, 4)))
        
        # FASE 3: Blocos repetidos (struct detection)
        if n >= 100:
            bloco2 = Counter()
            for i in range(0, min(n - 1, 2000), 2):
                bloco2[data[i:i+2]] += 1
            n_blocos2 = sum(1 for c in bloco2.values() if c > 5)
            if n_blocos2 > 0:
                tokens.append(('BINARY_BLOCK2', n_blocos2))
            
            bloco4 = Counter()
            for i in range(0, min(n - 3, 2000), 4):
                bloco4[data[i:i+4]] += 1
            n_blocos4 = sum(1 for c in bloco4.values() if c > 3)
            if n_blocos4 > 0:
                tokens.append(('BINARY_BLOCK4', n_blocos4))
        
        # FASE 4: Classificacao
        if 'BINARY_ENTROPY' in [t[0] for t in tokens]:
            idx = next(i for i, t in enumerate(tokens) if t[0] == 'BINARY_ENTROPY')
            ent = tokens[idx][1]
            if ent < 0.3:
                tokens.append(('BINARY_TYPE', 'LOW_ENTROPY'))
            elif ent < 0.6:
                tokens.append(('BINARY_TYPE', 'MIXED'))
            else:
                tokens.append(('BINARY_TYPE', 'HIGH_ENTROPY'))
        
        if formato == 'BINARY_UNKNOWN' and not any(t[0] == 'BINARY_TYPE' for t in tokens):
            tokens.append(('BINARY_TYPE', 'UNKNOWN_STRUCTURED'))
        
        return tokens
    
    # ===================================================================
    # TOKENIZACAO DE CONTEUDO DESCONHECIDO — descobre estrutura
    # ===================================================================
    
    def _tokenizar_desconhecido(self, texto: str) -> List[Tuple[str, Any]]:
        """Tokeniza conteudo que nao se encaixa em nenhum dominio conhecido.
        
        Usa n-gramas de caracteres para detectar repeticoes e criar
        tokens baseados na estrutura do proprio texto.
        """
        if not texto or len(texto) < 10:
            return self._tokenizar_texto(texto)
        
        tokens = []
        palavras_reais = re.findall(r'\w+', texto)
        
        # N-gramas de caracteres (tamanho 3-5) para detectar repeticoes
        ngramas_char = Counter()
        for n_tam in [3, 4]:
            for i in range(len(texto) - n_tam + 1):
                ngramas_char[texto[i:i+n_tam]] += 1
        
        # N-gramas que aparecem 3+ vezes → padrao estrutural
        padroes_estruturais = [ng for ng, c in ngramas_char.most_common(20) if c >= 3]
        
        if padroes_estruturais:
            for i, ng in enumerate(padroes_estruturais[:10]):
                tokens.append((f'PATTERN_{i}', ng[:50]))
            tokens.append(('PATTERN_COUNT', len(padroes_estruturais)))
        
        # Distribuicao de caracteres
        maiusculas = sum(1 for c in texto if c.isupper())
        minusculas = sum(1 for c in texto if c.islower())
        digitos = sum(1 for c in texto if c.isdigit())
        espacos = sum(1 for c in texto if c.isspace())
        outros = len(texto) - maiusculas - minusculas - digitos - espacos
        total_car = max(len(texto), 1)
        
        tokens.append(('TEXT_UPPER', round(maiusculas / total_car, 3)))
        tokens.append(('TEXT_LOWER', round(minusculas / total_car, 3)))
        tokens.append(('TEXT_DIGIT', round(digitos / total_car, 3)))
        tokens.append(('TEXT_SPACE', round(espacos / total_car, 3)))
        tokens.append(('TEXT_OTHER', round(outros / total_car, 3)))
        
        return tokens
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
