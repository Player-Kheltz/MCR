"""AprendizDePadroes — Aprendiz autônomo de padrões para IE e PE.

Lê QUALQUER fonte de dados, usa PE.tokenizar_universal() + extrair_padroes()
para descobrir estruturas e co-ocorrências, e salva lessons no KG
(ctx='padrao_aprendido') que a IntentionEngine carrega em runtime.

1 método universal substitui 6 especializados.
"""
import os, json, re
from collections import Counter, defaultdict
from typing import List, Dict, Optional


class AprendizDePadroes:
    """Aprendiz autônomo: lê fontes, extrai padrões, ensina IE."""
    
    def __init__(self, pe=None, kg=None):
        self._pe = pe
        self._kg = kg
        self._base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        self._padroes_encontrados = []
    
    # ============================================================
    # API PÚBLICA
    # ============================================================
    
    def estudar_tudo(self) -> Dict[str, int]:
        """Estuda TODAS as fontes disponíveis."""
        resultados = {}
        fontes = self._listar_fontes()
        
        for nome_fonte, dados in fontes.items():
            try:
                padroes = self._estudar_dados(dados, nome_fonte)
                if padroes:
                    self._padroes_encontrados.extend(padroes)
                    resultados[nome_fonte] = len(padroes)
            except Exception as e:
                print(f'  [Aprendiz] {nome_fonte}: ERRO - {e}')
        
        return resultados
    
    def estudar_fonte(self, fonte: str) -> List[Dict]:
        """Estuda UMA fonte específica pelo nome."""
        fontes = self._listar_fontes()
        dados = fontes.get(fonte)
        if dados is None:
            return []
        padroes = self._estudar_dados(dados, fonte)
        self._padroes_encontrados.extend(padroes)
        return padroes
    
    def estudar_dados(self, dados, nome_fonte: str = 'custom') -> List[Dict]:
        """Estuda dados ARBITRÁRIOS passados diretamente.
        
        Args:
            dados: qualquer formato (str, bytes, list, dict)
            nome_fonte: identificador para debug
        Returns:
            lista de padrões descobertos
        """
        padroes = self._estudar_dados(dados, nome_fonte)
        self._padroes_encontrados.extend(padroes)
        return padroes
    
    def salvar_kg(self):
        """Salva padrões no KG (ctx='padrao_aprendido')."""
        if not self._kg or not self._padroes_encontrados:
            return 0
        salvos = 0
        for p in self._padroes_encontrados:
            if p.get('conf', 0) >= 0.5:
                try:
                    self._kg.aprender(
                        erro=f"padrao: {p.get('tipo', 'descoberto')} | {str(p.get('n_grama', ''))[:60]}",
                        causa=f"fonte={p.get('fonte','?')}, freq={p.get('freq',0)}",
                        solucao=json.dumps(p, ensure_ascii=False),
                        ctx='padrao_aprendido'
                    )
                    salvos += 1
                except Exception:
                    pass
        return salvos
    
    def recarregar_ie(self, ie):
        """Carrega padrões na IntentionEngine em runtime."""
        if not ie or not self._padroes_encontrados:
            return
        if not hasattr(ie, '_lexico_dinamico'):
            ie._lexico_dinamico = []
        if not hasattr(ie, '_markov_dinamico'):
            ie._markov_dinamico = []
        
        for p in self._padroes_encontrados:
            conf = p.get('conf', 0.5)
            if 'sugestao_ie' in p:
                s = p['sugestao_ie']
                if 'tipo' in s and 'padrao_regex' in s:
                    ie._lexico_dinamico.append((s['tipo'], s['padrao_regex'], conf))
            if 'markov' in p and isinstance(p['markov'], dict):
                ie._markov_dinamico.append({'markov': p['markov'], 'conf': conf, 'fonte': p.get('fonte', '?')})
            if p.get('tipo') == 'risco' and 'n_grama' in p:
                if not hasattr(ie, '_risco_ngramas'):
                    ie._risco_ngramas = []
                ie._risco_ngramas.append({'n_grama': p['n_grama'], 'taxa_risco': p.get('taxa_risco', 0.5), 'conf': conf})
    
    def relatorio(self) -> str:
        """Gera relatório dos padrões encontrados."""
        linhas = [f"Total de padrões: {len(self._padroes_encontrados)}"]
        por_fonte = Counter(p.get('fonte', '?') for p in self._padroes_encontrados)
        for fonte, qtd in por_fonte.most_common():
            linhas.append(f"  {fonte}: {qtd}")
        top = sorted(self._padroes_encontrados, key=lambda x: -x.get('conf', 0))
        linhas.append(f"\nTop 10 por confiança:")
        for p in top:
            nome = str(p.get('n_grama', p.get('termos', p.get('tipo', '?'))))[:60]
            linhas.append(f"  [{p.get('conf',0):.2f}] {p.get('fonte','?')}: {nome}")
        return '\n'.join(linhas)
    
    # ============================================================
    # MÉTODO UNIVERSAL — substitui os 6 especializados
    # ============================================================
    
    def _estudar_dados(self, dados, nome_fonte: str) -> List[Dict]:
        """Método ÚNICO que estuda QUALQUER dado.
        
        Usa PE.tokenizar_universal() para qualquer formato,
        extrai n-gramas + markov + co-ocorrências, e retorna padrões.
        
        Args:
            dados: str / bytes / list / dict — qualquer formato
            nome_fonte: identificador para debug
            
        Returns:
            List[Dict]: padrões descobertos
        """
        padroes = []
        
        # Se não tem PE, não consegue analisar
        if not self._pe:
            return padroes
        
        # ============================================================
        # FASE 1: TOKENIZAÇÃO UNIVERSAL
        # ============================================================
        try:
            tokens = self._pe.tokenizar_universal(dados)
            if not tokens:
                return padroes
        except Exception as e:
            print(f'  [Aprendiz] {nome_fonte}: tokenizar_universal falhou: {e}')
            return padroes
        
        # ============================================================
        # FASE 2: EXTRAÇÃO DE PADRÕES
        # ============================================================
        try:
            padroes_tokens = self._pe.extrair_padroes(tokens)
        except Exception:
            padroes_tokens = {'n_gramas': {}, 'markov': {}, 'entropia': 0.0, 'total': 0}
        
        entropia = padroes_tokens.get('entropia', 1.0)
        n_gramas = padroes_tokens.get('n_gramas', {})
        markov = padroes_tokens.get('markov', {})
        
        # ============================================================
        # FASE 3: DETECÇÃO DE CO-OCORRÊNCIAS
        # ============================================================
        # Para cada entrada que seja uma lista/deques de itens
        if isinstance(dados, list):
            # Co-ocorrência de tipos de token
            tipos_por_item = []
            for item in dados:
                try:
                    t_item = self._pe.tokenizar_universal(item)
                    tipos_por_item.append([t[0] for t in t_item])
                except Exception:
                    continue
            
            if tipos_por_item:
                # N-gramas entre itens
                freq_ng = Counter()
                for tipos in tipos_por_item:
                    for i in range(len(tipos)):
                        for j in range(i+1, min(i+4, len(tipos))):
                            ng = (tipos[i], tipos[j])
                            freq_ng[ng] += 1
                
                for (t1, t2), freq in freq_ng.most_common(10):
                    if freq >= 3:
                        conf = min(0.85, 0.3 + freq * 0.05)
                        padroes.append({
                            'tipo': 'ngrama_tipo',
                            'n_grama': (t1, t2),
                            'freq': freq,
                            'conf': round(conf, 2),
                            'fonte': nome_fonte,
                            'markov': {t1: {t2: freq / max(len(tipos_por_item), 1)}},
                        })
        
        # ============================================================
        # FASE 4: N-GRAMAS DOS TOKENS
        # ============================================================
        for ng, freq in list(n_gramas.items()):
            if isinstance(ng, tuple) and len(ng) >= 2 and freq >= 2:
                conf = min(0.8, 0.3 + freq * 0.08)
                padroes.append({
                    'tipo': 'ngrama_token',
                    'n_grama': ng,
                    'freq': freq,
                    'entropia': round(entropia, 3),
                    'conf': round(conf, 2),
                    'fonte': nome_fonte,
                })
        
        # ============================================================
        # FASE 5: EXTRAÇÃO DE TERMOS CO-OCORRENTES (texto)
        # ============================================================
        if isinstance(dados, str) and len(dados) > 10:
            # Extrai palavras e conta repetições
            palavras = re.findall(r'\b\w{4,}\b', dados.lower())
            freq_palavras = Counter(palavras)
            
            for pal, freq in freq_palavras.most_common(30):
                if freq < 2:
                    continue
                
                # Tenta categorizar
                cat = 'DOM_GENERICO'
                if pal in ('npc', 'personagem', 'vendedor', 'guia', 'ferreiro'):
                    cat = 'DOM_NPC'
                elif pal in ('sistema', 'mecanica', 'dominio', 'progressao'):
                    cat = 'DOM_SYSTEM'
                elif pal in ('fogo', 'gelo', 'terra', 'energia', 'elemental'):
                    cat = 'DOM_ELEMENT'
                elif pal in ('codigo', 'funcao', 'arquivo', 'script'):
                    cat = 'DOM_CODE'
                elif pal in ('missao', 'quest', 'tarefa'):
                    cat = 'DOM_QUEST'
                elif pal in ('habilidade', 'skill', 'combo'):
                    cat = 'DOM_SKILL'
                elif pal in ('lore', 'historia', 'cidade', 'regiao'):
                    cat = 'DOM_LORE'
                elif pal in ('canary', 'servidor', 'client', 'otclient'):
                    cat = 'DOM_SERVER'
                
                conf = min(0.85, 0.3 + freq * 0.05)
                padroes.append({
                    'tipo': 'coocorrencia',
                    'termos': [pal],
                    'freq': freq,
                    'conf': round(conf, 2),
                    'fonte': nome_fonte,
                    'sugestao_ie': {
                        'tipo': cat,
                        'padrao_regex': f"\\b{pal}\\b",
                    }
                })
        
        # ============================================================
        # FASE 6: PADRÕES DE RISCO (se dados têm campo sucesso)
        # ============================================================
        if isinstance(dados, list):
            sucessos = [d for d in dados if isinstance(d, dict) and d.get('sucesso', True)]
            falhas = [d for d in dados if isinstance(d, dict) and not d.get('sucesso', True)]
            
            if falhas and sucessos:
                termos_falha = Counter()
                for f in falhas:
                    if isinstance(f, dict):
                        for v in f.values():
                            if isinstance(v, str):
                                termos_falha.update(re.findall(r'\b\w{4,}\b', v.lower()))
                
                termos_sucesso = Counter()
                for s in sucessos:
                    if isinstance(s, dict):
                        for v in s.values():
                            if isinstance(v, str):
                                termos_sucesso.update(re.findall(r'\b\w{4,}\b', v.lower()))
                
                for termo, freq_f in termos_falha.most_common(15):
                    freq_s = termos_sucesso.get(termo, 0)
                    total = freq_f + freq_s
                    if total >= 3:
                        taxa_risco = freq_f / total if total > 0 else 0
                        if taxa_risco > 0.5:
                            padroes.append({
                                'tipo': 'risco',
                                'termos': [termo],
                                'freq_falha': freq_f,
                                'freq_sucesso': freq_s,
                                'taxa_risco': round(taxa_risco, 3),
                                'conf': round(min(0.75, 0.3 + taxa_risco * 0.4), 2),
                                'fonte': nome_fonte,
                            })
        
        # ============================================================
        # FASE 7: ENRIQUECER PADRÕES com Markov de tipos
        # (para reconstrução via PiEngine.gerar_sequencia())
        # ============================================================
        if tokens:
            # Extrai tipos_markov dos tokens atuais
            tipos_lista = [t[0] for t in tokens]
            tipos_markov_local = {}
            for i in range(len(tipos_lista) - 1):
                t_atual = tipos_lista[i]
                t_prox = tipos_lista[i + 1]
                if t_atual not in tipos_markov_local:
                    tipos_markov_local[t_atual] = {}
                tipos_markov_local[t_atual][t_prox] = tipos_markov_local[t_atual].get(t_prox, 0) + 1
            
            # Normaliza
            for t_atual, trans in tipos_markov_local.items():
                total = sum(trans.values())
                for t_prox in trans:
                    trans[t_prox] = round(trans[t_prox] / total, 3)
            
            # Frequência de palavras por tipo
            tipo_palavra_freq_local = {}
            for t in tokens:
                tipo = t[0]
                palavra = str(t[1]) if len(t) > 1 else ''
                if tipo not in tipo_palavra_freq_local:
                    tipo_palavra_freq_local[tipo] = {}
                tipo_palavra_freq_local[tipo][palavra] = tipo_palavra_freq_local[tipo].get(palavra, 0) + 1
            
            # Adiciona aos padrões de alta confiança
            for p in padroes:
                if p.get('conf', 0) >= 0.6:
                    if 'tipos_markov' not in p:
                        p['tipos_markov'] = tipos_markov_local
                    if 'tipo_palavra_freq' not in p:
                        p['tipo_palavra_freq'] = tipo_palavra_freq_local
        
        return padroes
    
    # ============================================================
    # RECONSTRUÇÃO DE RESPOSTA (0 IA, baseada em Markov de tipos)
    # ============================================================
    
    def reconstruir_resposta(self, fingerprint_input: List[float],
                              ie_intencao: tuple = None,
                              tokens_input: List = None) -> Optional[str]:
        """Tenta reconstruir resposta sem LLM.
        
        1. Busca fingerprint_input similar no KG (via buscar_rotas)
        2. Fallback: match por tipos de token (se fingerprint falhar)
        3. Pega o tipos_markov + tipo_palavra_freq
        4. Gera sequencia de TIPOS via PiEngine.gerar_sequencia()
        5. Preenche PALAVRAS para cada tipo
        6. Se confianca < 0.5, retorna None (fallback LLM)
        
        Args:
            fingerprint_input: fingerprint 64d da pergunta
            ie_intencao: (categoria, tipo, confianca) da IntentionEngine
            tokens_input: tokens da pergunta (para match alternativo)
            
        Returns:
            str: resposta reconstruida, ou None se não conseguiu
        """
        if not self._pe or not self._kg:
            return None
        
        from modulos.pi_engine import PiEngine as _PiEng
        pi = _PiEng(pe=self._pe)
        
        # 1. Busca por FINGERPRINT em TODAS as lessons (nao so ctx='rota')
        lessons_encontradas = []
        
        if fingerprint_input:
            try:
                licoes = self._kg._get_licoes()
                for l in licoes:
                    if l.get('inactive', False):
                        continue
                    fp_l = l.get('fingerprint', [])
                    if not fp_l or len(fp_l) != len(fingerprint_input):
                        continue
                    # Similaridade coseno
                    dot = sum(a * b for a, b in zip(fp_l, fingerprint_input))
                    if dot >= 0.3:
                        l['_sim'] = dot
                        lessons_encontradas.append(l)
                lessons_encontradas.sort(key=lambda x: -x.get('_sim', 0))
            except Exception:
                lessons_encontradas = []
        
        # 1b. Fallback: match por TIPOS DE TOKEN (se fingerprint nao achou nada)
        if not lessons_encontradas and tokens_input:
            tipos_input = [t[0] for t in tokens_input]
            try:
                licoes = self._kg._get_licoes()
                for l in licoes:
                    tm = l.get('tipos_markov')
                    if not tm:
                        continue
                    # Extrai tipos da pergunta original da lesson (campo causa)
                    _causa = l.get('causa', '')
                    _m_tipos = re.search(r'tipos=\[([^\]]+)\]', _causa)
                    if not _m_tipos:
                        continue
                    tipos_lesson = _m_tipos.group(1).split(',')
                    # Match: quantos tipos tem em comum?
                    match = sum(1 for t in tipos_input if t in tipos_lesson)
                    if match >= 2:
                        sim = match / max(max(len(tipos_input), len(tipos_lesson)), 1)
                        l['_sim'] = sim
                        lessons_encontradas.append(l)
                lessons_encontradas.sort(key=lambda x: -x.get('_sim', 0))
            except Exception:
                pass
        
        if not lessons_encontradas:
            return None
        
        # 2. Pega a melhor lesson
        melhor = None
        melhor_score = 0
        
        for l in lessons_encontradas:
            tipos_markov = l.get('tipos_markov')
            nota = l.get('nota', 0)
            sim = l.get('_sim', 0)
            score = (sim * 0.7) + (min(nota, 10) / 10.0 * 0.3) if nota > 0 else sim
            if tipos_markov and score > melhor_score:
                melhor_score = score
                melhor = l
        
        if not melhor or melhor_score < 0.35:
            return None
        
        # 3. Define semente — usa o PRIMEIRO token do Markov como fallback
        tipos_markov = melhor['tipos_markov']
        semente = list(tipos_markov.keys())[0] if tipos_markov else 'INTENT_CREATE'
        
        # Se a IE sugeriu intencao e ela existe no Markov, usa ela
        if ie_intencao:
            cat, params, _ = ie_intencao
            intent_token = f'INTENT_{cat}'
            if intent_token in tipos_markov:
                semente = intent_token
        
        tipo_palavra = melhor.get('tipo_palavra_freq', {})
        tipos_markov = self._limitar_ciclo(tipos_markov)
        
        # 4. Gera sequencia de TIPOS
        tipos_gerados = pi.gerar_sequencia(tipos_markov, semente,
                                            max_passos=10, conf_min=0.1, max_repeticoes=2)
        
        if not tipos_gerados:
            return None
        
        # 5. Preenche PALAVRAS
        palavras = []
        ultimo_tipo = semente
        for tipo in tipos_gerados:
            if tipo in tipo_palavra:
                palavra = max(tipo_palavra[tipo], key=tipo_palavra[tipo].get)
                if palavra:
                    palavras.append(palavra)
            else:
                palavras.append(f'@{tipo}')
            ultimo_tipo = tipo
        
        confianca = melhor_score
        texto = ' '.join(palavras)
        
        return texto
    
    # ============================================================
    # AUTO-VALIDAÇÃO E CORREÇÃO (preenche blanks @TIPO com ferramentas)
    # ============================================================
    
    def preencher_resposta(self, resposta_generica: str, 
                            tipos_gerados: List[str] = None,
                            pergunta_original: str = "",
                            tools=None) -> Optional[str]:
        """Preenche blanks @TIPO em respostas reconstruidas usando ferramentas.
        
        Quando reconstruir_resposta() nao tem tipo_palavra_freq, a resposta
        fica com placeholders @DOM_NPC, @PAL_LONGA etc. Este metodo usa
        ferramentas para extrair palavras reais e substituir.
        
        1. Detecta todos os @TIPO na resposta
        2. Para CADA tipo, busca exemplos reais via ferramentas
        3. Tokeniza exemplos → extrai tipo_palavra_freq
        4. Preenche cada tipo com a palavra mais frequente
        5. Se ainda sobram blanks, fallback LLM pequeno (1.5b)
        
        Args:
            resposta_generica: resposta com @TIPO placeholders
            tipos_gerados: lista de tipos na ordem (opcional)
            pergunta_original: texto da pergunta (para contexto)
            tools: ToolOrchestrator (opcional, para buscas)
            
        Returns:
            str: resposta preenchida, ou None se nao conseguiu
        """
        if not resposta_generica or '@' not in resposta_generica:
            return resposta_generica  # ja esta preenchida
        
        print(f'  [Preencher] Detectados placeholders, corrigindo...')
        
        # 1. Extrai todos os tipos que precisam de preenchimento
        placeholders = set(re.findall(r'@(\w+)', resposta_generica))
        
        if not placeholders:
            return resposta_generica
        
        # 2. Para CADA tipo que precisa de palavra, tenta fontes
        tipo_palavra_extraido = {}  # tipo → {palavra: freq}
        
        for ph in placeholders:
            tipo_base = ph.replace('PAL_', '')  # PAL_LONGA -> LONGA etc
            
            # Tenta buscar termo da pergunta que corresponda a este tipo
            termo_busca = self._extrair_termo_para_tipo(tipo_base, pergunta_original)
            
            if not termo_busca:
                continue
            
            # Fonte A: buscar_estrategico
            if tools:
                try:
                    r = tools.executar('buscar_estrategico', {'termo': termo_busca})
                    if r and r.get('sucesso'):
                        dados = str(r.get('resultado', ''))
                        if dados and len(dados) > 30:
                            tokens = self._pe.tokenizar_universal(dados)
                            self._extrair_palavras(tokens, tipo_base, tipo_palavra_extraido)
                except Exception:
                    pass
            
            # Fonte B: buscar_kg
            if self._kg:
                try:
                    lessons = self._kg.buscar(termo_busca, max_r=3)
                    for l in (lessons or []):
                        sol = l.get('solucao', '')
                        if sol:
                            tokens = self._pe.tokenizar_universal(sol)
                            self._extrair_palavras(tokens, tipo_base, tipo_palavra_extraido)
                except Exception:
                    pass
        
        # 3. Se nao conseguiu dados de ferramentas, usa o proprio tipos_gerados
        if not tipo_palavra_extraido and tipos_gerados:
            for i, tipo in enumerate(tipos_gerados):
                tipo_base = tipo.replace('PAL_', '')
                if tipo_base not in tipo_palavra_extraido:
                    tipo_palavra_extraido[tipo_base] = {}
                # Usa o proprio tipo como fallback
                tipo_palavra_extraido[tipo_base]['@FALLBACK'] = tipo_palavra_extraido[tipo_base].get('@FALLBACK', 0) + 1
        
        # 4. Preenche os blanks
        resultado = resposta_generica
        for ph in placeholders:
            tipo_base = ph.replace('PAL_', '')
            dados = tipo_palavra_extraido.get(tipo_base, {})
            if dados:
                # Palavra mais frequente
                melhor_palavra = max(dados, key=dados.get)
                if melhor_palavra != '@FALLBACK':
                    resultado = resultado.replace(f'@{ph}', melhor_palavra, 1)
                else:
                    resultado = resultado.replace(f'@{ph}', '', 1)  # remove
            else:
                resultado = resultado.replace(f'@{ph}', '', 1)  # remove sem palavra
        
        # Limpa espacos duplicados
        resultado = re.sub(r'\s+', ' ', resultado).strip()
        
        if resultado and len(resultado) > 20 and '@' not in resultado:
            print(f'  [Preencher] OK: {len(resultado)} chars')
            return resultado
        
        # Se ainda tem blanks, fallback
        if '@' in resultado:
            print(f'  [Preencher] Ainda com blanks, fallback LLM')
            return None
        
        return resultado if len(resultado) > 20 else None
    
    def _limitar_ciclo(self, markov: Dict) -> Dict:
        """Limita Markov para evitar loops infinitos.
        
        Adiciona FIM_FRASE com probabilidade minima para tokens que
        so tem 1 saida (causa de loop).
        """
        if not markov:
            return markov
        
        resultado = {}
        for token, transicoes in markov.items():
            nova_trans = dict(transicoes)
            if len(nova_trans) == 1:
                saida_unica = list(nova_trans.keys())[0]
                prob_unica = nova_trans[saida_unica]
                if prob_unica > 0.8:
                    nova_trans[saida_unica] = round(prob_unica * 0.9, 3)
                    nova_trans['FIM_FRASE'] = round(prob_unica * 0.1, 3)
            resultado[token] = nova_trans
        
        return resultado
    
    def _extrair_palavras(self, tokens, tipo_base, acumulador):
        """Extrai palavras de tokens e acumula por tipo_base."""
        for t in tokens:
            tipo = t[0]
            palavra = str(t[1]) if len(t) > 1 else ''
            if not palavra or len(palavra) < 2:
                continue
            # Verifica se o tipo corresponde ao tipo_base
            if tipo == tipo_base or tipo.replace('PAL_', '') == tipo_base:
                if tipo_base not in acumulador:
                    acumulador[tipo_base] = {}
                acumulador[tipo_base][palavra] = acumulador[tipo_base].get(palavra, 0) + 1
            # PAL_* genericos podem ser de qualquer tipo — aceita
            elif tipo.startswith('PAL_'):
                if tipo_base not in acumulador:
                    acumulador[tipo_base] = {}
                acumulador[tipo_base][palavra] = acumulador[tipo_base].get(palavra, 0) + 1
    
    def _extrair_termo_para_tipo(self, tipo_base: str, pergunta: str) -> str:
        """Extrai termo de busca para um tipo baseado na pergunta."""
        if not pergunta:
            return tipo_base.lower()
        
        # Pega palavras da pergunta que NAO sao artigos/preposicoes
        stop = {'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'da', 'do', 'em', 'no',
                'para', 'com', 'e', 'que', 'como', 'por', 'ao', 'dos', 'das'}
        palavras = [p.lower() for p in pergunta.split() if p.lower() not in stop and len(p) > 2]
        
        if not palavras:
            return tipo_base.lower()
        
        # Se tipo parece ser sobre algo na pergunta, usa a palavra mais longa
        if tipo_base in ('LONGA', 'MEDIA'):
            return max(palavras, key=len)
        elif tipo_base in ('CURTA',):
            return min(palavras, key=len) if palavras else (palavras[0] if palavras else tipo_base)
        
        return palavras[0] if palavras else tipo_base.lower()
        """Limita Markov para evitar loops infinitos.
        
        Adiciona FIM_FRASE com probabilidade mínima para tokens que
        só tem 1 saída (causa de loop).
        """
        if not markov:
            return markov
        
        resultado = {}
        for token, transicoes in markov.items():
            nova_trans = dict(transicoes)
            if len(nova_trans) == 1:
                # Se só tem 1 saída, adiciona FIM_FRASE com 10%
                saida_unica = list(nova_trans.keys())[0]
                prob_unica = nova_trans[saida_unica]
                if prob_unica > 0.8:
                    nova_trans[saida_unica] = round(prob_unica * 0.9, 3)
                    nova_trans['FIM_FRASE'] = round(prob_unica * 0.1, 3)
            resultado[token] = nova_trans
        
        return resultado
    # ============================================================
    
    def _listar_fontes(self) -> Dict[str, object]:
        """Mapeia todas as fontes disponíveis.
        
        Cada fonte retorna dados em formato que tokenizar_universal() entende:
        - str (texto de arquivo)
        - bytes (binários)
        - list (itens)
        - dict (estrutura)
        """
        fontes = {}
        
        # KG: diretório com 55 arquivos .json
        kg_dir = os.path.join(self._base, 'sandbox', '.mcr_devia', 'kg')
        if os.path.isdir(kg_dir):
            todas_lessons = []
            for fname in os.listdir(kg_dir):
                if fname.endswith('.json'):
                    try:
                        with open(os.path.join(kg_dir, fname), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        todas_lessons.extend(data.get('licoes', []))
                    except Exception:
                        continue
            # Concatena soluções em 1 string grande (o tokenizador universal analisa)
            texto_kg = ' '.join(
                f"{l.get('erro','')} {l.get('solucao','')}" 
                for l in todas_lessons
            )
            if texto_kg:
                fontes['kg'] = texto_kg
        
        # Conselho: 9 arquivos .jsonl
        conselho_dir = os.path.join(self._base, 'sandbox', '.mcr_devia', 'conselho_memoria')
        if os.path.isdir(conselho_dir):
            linhas_conselho = []
            for fname in os.listdir(conselho_dir):
                if fname.endswith('.jsonl'):
                    try:
                        with open(os.path.join(conselho_dir, fname), 'r', encoding='utf-8') as f:
                            for line in f:
                                try:
                                    entry = json.loads(line.strip())
                                    if entry.get('response'):
                                        linhas_conselho.append(entry['response'])
                                except Exception:
                                    continue
                    except Exception:
                        continue
            if linhas_conselho:
                fontes['conselho'] = linhas_conselho  # list de textos
        
        # Episódios: .json
        epis_path = os.path.join(self._base, 'sandbox', '.mcr_episodios.json')
        if os.path.exists(epis_path):
            try:
                with open(epis_path, 'r', encoding='utf-8') as f:
                    fontes['episodios'] = json.load(f)  # list de dicts
            except Exception:
                pass
        
        # Métricas: .json
        metr_path = os.path.join(self._base, 'sandbox', '.mcr_metricas.json')
        if os.path.exists(metr_path):
            try:
                with open(metr_path, 'r', encoding='utf-8') as f:
                    fontes['metricas'] = json.load(f)  # dict
            except Exception:
                pass
        
        # Testes: sandbox/.mcr_teste_*.json
        textos_teste = []
        for pattern in ['.mcr_teste_completo.json', '.mcr_teste_criacao.json',
                         '.mcr_teste_complexo.json']:
            path = os.path.join(self._base, 'sandbox', pattern)
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, dict) and data.get('pergunta'):
                        textos_teste.append(data['pergunta'])
                    textos_teste.append(json.dumps(data, ensure_ascii=False))
                except Exception:
                    pass
        if textos_teste:
            fontes['testes'] = '\n'.join(textos_teste)
        
        # Conversa: .jsonl
        conv_path = os.path.join(self._base, 'sandbox', '.mcr_conversa.jsonl')
        if os.path.exists(conv_path):
            mensagens = []
            try:
                with open(conv_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if entry.get('msg'):
                                mensagens.append(entry['msg'])
                        except Exception:
                            continue
            except Exception:
                pass
            if mensagens:
                fontes['conversa'] = mensagens  # list de textos
        
        return fontes
    
    # ============================================================
    # EXTRAÇÃO CONTEXTUAL — lê contexto expansivo ao redor de termos
    # ============================================================
    
    def extrair_contexto(self, termo: str, arquivo_path: str,
                          modulo: int = 5, max_modulo: int = 50) -> Optional[str]:
        """Extrai contexto crescente ao redor de um termo em um arquivo.
        
        Começa com N palavras antes/depois, expande até encontrar
        um fragmento coerente (com verbo, sujeito, pontuacao).
        
        Args:
            termo: palavra a buscar (ex: "SPA")
            arquivo_path: caminho do arquivo (ex: "docs/MCR_IDENTITY.md")
            modulo: palavras iniciais antes/depois
            max_modulo: maximo de expansao
            
        Returns:
            str: fragmento extraido, ou None se nao achar
        """
        # Resolve path
        full_path = arquivo_path
        if not os.path.isabs(full_path):
            full_path = os.path.join(self._base, full_path)
        
        if not os.path.exists(full_path):
            return None
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                texto = f.read()
        except Exception:
            return None
        
        # Encontra o termo no texto (case insensitive)
        idx = texto.lower().find(termo.lower())
        if idx < 0:
            return None
        
        palavra_termo = texto[idx:idx + len(termo)]
        
        # Pega o texto ao redor (expansao gradual)
        melhor_fragmento = None
        melhor_score = 0
        
        for modulo_atual in [modulo, modulo * 2, modulo * 3, max_modulo]:
            # Palavras antes
            antes = self._palavras_ao_redor(texto, idx, direcao='antes', n=modulo_atual)
            depois = self._palavras_ao_redor(texto, idx + len(termo), direcao='depois', n=modulo_atual)
            
            fragmento = f"{antes}**{palavra_termo}**{depois}"
            
            score = self._avaliar_coerencia(fragmento)
            if score > melhor_score:
                melhor_score = score
                melhor_fragmento = fragmento
            
            if score >= 0.7:
                break  # fragmento suficientemente coerente
        
        return melhor_fragmento
    
    def _palavras_ao_redor(self, texto: str, idx: int, direcao: str = 'ambas', n: int = 5) -> str:
        """Extrai N palavras antes ou depois de um indice no texto."""
        if direcao == 'antes':
            # Pega N palavras antes do indice
            antes = texto.strip()
            palavras = antes.split()
            return ' '.join(palavras[-n:]) if len(palavras) >= n else antes
        
        elif direcao == 'depois':
            depois = texto[idx:].strip()
            palavras = depois.split()
            return ' '.join(palavras) if len(palavras) >= n else depois
        
        return ''
    
    def _avaliar_coerencia(self, fragmento: str) -> float:
        """Avalia coerencia de um fragmento de texto heuristicamente.
        
        Pontuacao:
        - Tem verbo (e, sao, foi, tem, etc): +0.3
        - Tem pelo menos 5 palavras: +0.2
        - Termina com pontuacao (.!?): +0.2
        - Nao tem @TIPO: +0.3
        - Tem o termo original (nao so @): +0.2
        - Tamanho entre 20 e 200 chars: +0.1
        """
        if not fragmento:
            return 0.0
        
        score = 0.0
        f_lower = fragmento.lower()
        
        # Verbos comuns
        verbos = {'e', 'sao', 'foi', 'era', 'tem', 'ter', 'ser', 'estao',
                  'esta', 'ficam', 'existe', 'criado', 'usado', 'baseado',
                  'significa', 'chamado', 'conhecido', 'define'}
        
        palavras = fragmento.split()
        
        if any(v in f_lower for v in verbos):
            score += 0.3
        
        if len(palavras) >= 5:
            score += 0.2
        
        if fragmento.strip()[-1] in '.!?' if fragmento.strip() else False:
            score += 0.2
        
        if '@' not in fragmento:
            score += 0.3
        
        if '**' in fragmento:  # tem o termo destacado
            score += 0.2
        
        if 20 <= len(fragmento) <= 200:
            score += 0.1
        
        return min(1.0, score)
    
    # ============================================================
    # APRENDIZAGEM DE FRAGMENTOS — salva blocos no KG
    # ============================================================
    
    def aprender_fragmento(self, fragmento: str, fingerprint_pergunta: List[float],
                            pergunta: str = "", nota: int = 8):
        """Aprende um fragmento de texto como bloco reutilizavel.
        
        1. PE.tokeniza o fragmento → extrai tipos
        2. Salva no KG com fingerprint da pergunta
        
        Args:
            fragmento: texto extraido (ex: "SPA = Sistema de Progressao...")
            fingerprint_pergunta: fingerprint 64d da pergunta
            pergunta: texto original da pergunta
            nota: qualidade estimada (8 = bom, 5 = medio, 3 = ruim)
        """
        if not fragmento or not fingerprint_pergunta:
            return
        
        try:
            tokens = self._pe.tokenizar_universal(fragmento)
            if not tokens:
                return
            
            # Tipos unicos
            tipos_unicos = list(dict.fromkeys([t[0] for t in tokens]))
            
            # Salva no KG e força flush do buffer
            self._kg.aprender(
                erro=f"bloco: {pergunta if pergunta else fragmento}",
                causa=f"tipos={','.join(tipos_unicos)}",
                solucao=json.dumps({
                    'fragmento': fragmento,
                    'nota': nota,
                    'tamanho': len(fragmento),
                }),
                ctx='bloco_aprendido',
                fingerprint=fingerprint_pergunta,
            )
            # Força salvamento imediato
            try:
                self._kg.salvar()
            except Exception:
                pass
        except Exception:
            pass
    
    # ============================================================
    # RECONSTRUÇÃO COM BLOCOS — monta resposta de fragmentos aprendidos
    # ============================================================
    
    def reconstruir_com_blocos(self, fingerprint_input: List[float],
                                pergunta: str = "",
                                tokens_input: List = None) -> Optional[str]:
        """Tenta reconstruir resposta usando blocos de fragmentos aprendidos.
        
        1. Busca blocos no KG com fingerprint similar
        2. Adapta o bloco para a pergunta (substitui termos)
        3. Retorna resposta montada
        
        Args:
            fingerprint_input: fingerprint 64d da pergunta
            pergunta: texto da pergunta
            tokens_input: tokens da pergunta
            
        Returns:
            str: resposta montada de blocos, ou None se nao achar
        """
        if not self._pe or not self._kg:
            return None
        
        # 1. Busca blocos com fingerprint similar (disco + buffer)
        import json as _json_rec
        licoes = list(self._kg._get_licoes())
        # Inclui lessons do buffer (ainda nao salvas em disco)
        try:
            from modulos.kg import _LESSONS_BUFFER as _LB
            for _l in _LB:
                if _l not in licoes:
                    licoes.append(_l)
        except (ImportError, AttributeError):
            pass
        
        # DEBUG: quantas lessons tem fingerprint?
        _debug_com_fp = [l for l in licoes if l.get('fingerprint')]
        _debug_bloco = [l for l in licoes if l.get('ctx') == 'bloco_aprendido']
        print(f'    [reconstruir_com_blocos] total lessons: {len(licoes)}, com fingerprint: {len(_debug_com_fp)}, blocos: {len(_debug_bloco)}')
        
        blocos = []
        
        for l in licoes:
            if l.get('inactive') or l.get('ctx') != 'bloco_aprendido':
                continue
            fp_l = l.get('fingerprint', [])
            if not fp_l or len(fp_l) != len(fingerprint_input):
                print(f'    [DB] bloco {l.get("erro","")}... fp_len={len(fp_l)} vs esperado={len(fingerprint_input)}')
                continue
            dot = sum(a * b for a, b in zip(fp_l, fingerprint_input))
            print(f'    [DB] bloco similaridade={dot:.2f} | {l.get("erro","")}')
            if dot >= 0.5:
                l['_sim'] = dot
                blocos.append(l)
        
        if not blocos:
            return None
        
        # 2. Pega o melhor bloco
        melhor = max(blocos, key=lambda x: x.get('_sim', 0))
        solucao_raw = melhor.get('solucao', '')
        
        # solucao pode ser JSON (se salvo por aprender_fragmento) ou texto direto
        try:
            solucao_data = json.loads(solucao_raw)
            fragmento = solucao_data.get('fragmento', solucao_raw)
        except (json.JSONDecodeError, TypeError):
            fragmento = solucao_raw
        
        if not fragmento:
            return None
        
        # 3. Adapta para a pergunta — remove ** do destaque do termo
        resultado = fragmento.replace('**', '')
        resultado = resultado.strip()
        return resultado if len(resultado) > 10 else None
