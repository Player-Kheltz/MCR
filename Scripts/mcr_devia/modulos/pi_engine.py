"""Pi Engine — Preditor Universal de Padroes (0 IA, 0 GPU, 0 Ollama).
Usa PatternEngine + Markov + entropia para extrapolar padroes sem LLM.

Filosofia: Pi e infinito. Tudo existe dentro dele. O padrao revela o proximo passo.
Nao precisamos de bilhoes de parametros — precisamos entender a REGRA do padrao.
"""
import os, sys, re, time
from typing import List, Tuple, Dict, Optional, Any

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class PiEngine:
    """Preditor universal de padroes. Usa Markov + PatternEngine para continuar sequencias.
    
    3 modos de operacao:
      - 'markov': extrapola o padrao atual (entropia baixa, alta confianca)
      - 'kg': busca padrao similar no KG (entropia media)
      - 'auto': decide automaticamente baseado na entropia
    """
    
    def __init__(self, pe=None, kg=None, ia=None):
        self.pe = pe
        self.kg = kg
        self.ia = ia
        self._kg_markov = {}  # Markov construido a partir do KG
        self._markov_entre_fragmentos = {}  # Markov entre fragmentos sequenciais
        self._inicializar_pe()
        self._construir_markov_kg()
    
    def _construir_markov_kg(self):
        """Constroi modelo Markov a partir de TODAS as lessons do KG.
        
        Isso cria um corpus rico o suficiente para o Markov fazer
        predicoes mesmo para entradas curtas.
        """
        if not self.kg:
            return
        try:
            licoes = self.kg._get_licoes()
            # Pega so as lessons ativas
            ativas = [l for l in licoes if not l.get('inactive')]
            
            # Junta todas as solucoes num texto unico
            corpus = ' '.join([
                l.get('solucao', '') + ' ' + l.get('erro', '')
                for l in ativas  # Top 100 lessons
                if l.get('solucao') or l.get('erro')
            ])
            
            if len(corpus) > 50 and self.pe:
                tokens = self.pe.tokenizar(corpus, 'texto')
                padroes = self.pe.extrair_padroes(tokens)
                self._kg_markov = padroes.get('markov', {})
                print(f'  [PiEngine] Markov construido do KG: {len(self._kg_markov)} estados')
        except Exception:
            pass
    
    def _inicializar_pe(self):
        if not self.pe:
            try:
                from modulos.pattern_engine import PatternEngine
                self.pe = PatternEngine()
            except Exception:
                pass
    
    def continuar_padrao(self, texto, max_passos=20, temperatura=0.3):
        """Continua um padrao passo a passo usando Markov extrapolation.
        
        1. Tokeniza o texto atual
        2. Extrai padroes (Markov, n-gramas, entropia)
        3. Se entropia < 0.5: usa Markov para predizer o proximo termo
        4. Se entropia >= 0.5: usa KG ou fallback
        5. Repete ate entropia subir ou max_passos
        
        Returns:
            str: texto original + continuacao prevista
        """
        if not self.pe:
            return texto
        
        t0 = time.time()
        resultado = texto
        passos = 0
        
        for _ in range(max_passos):
            # 1. Tokeniza e extrai padroes
            tokens = self.pe.tokenizar(resultado, 'texto')
            padroes = self.pe.extrair_padroes(tokens)
            entropia = padroes.get('entropia', 0.5)
            markov = padroes.get('markov', {})
            
            # 2. Decide metodo baseado na entropia
            if entropia < 0.4:
                # Entropia BAIXA → Markov extrapolation (0 IA, 0 KG)
                proximo = self._predizer_markov(resultado, markov, temperatura)
                metodo = 'markov'
            elif entropia < 0.65:
                # Entropia MEDIA → tenta Markov, fallback KG
                proximo = self._predizer_markov(resultado, markov, temperatura)
                if not proximo and self.kg:
                    proximo = self._predizer_kg(resultado)
                    metodo = 'kg'
                else:
                    metodo = 'markov'
            else:
                # Entropia ALTA → KG ou fallback
                if self.kg:
                    proximo = self._predizer_kg(resultado)
                    metodo = 'kg'
                else:
                    break  # Nao consegue prever, para
            
            if not proximo or len(proximo) < 3:
                break  # Nada para adicionar
            
            resultado += ' ' + proximo
            passos += 1
            
            # Se entropia subiu muito, para (padrao mudou)
            if entropia > 0.7 and passos > 3:
                break
        
        return resultado
    
    # ===================================================================
    # PREDIZER UNIVERSAL — funciona com QUALQUER tipo de token
    # ===================================================================
    
    def predizer(self, markov: Dict, ultimo_token: Any) -> Tuple[Any, float]:
        """Prediz o PROXIMO token em QUALQUER Markov chain.
        
        Funciona com: str, int, bytes, tuple — qualquer tipo hashable.
        Nao importa se são palavras, tipos de token, ou bytes — o Markov
        é a mesma estrutura {token: {proximo: prob}}.
        
        Args:
            markov: {token: {proximo_token: probabilidade}}
            ultimo_token: qualquer tipo (str, int, bytes, tuple)
        Returns:
            (proximo_token, confianca) ou (None, 0.0)
        """
        if not markov or ultimo_token not in markov:
            return None, 0.0
        proximos = markov[ultimo_token]
        if not proximos:
            return None, 0.0
        melhor = max(proximos, key=proximos.get)
        return melhor, proximos[melhor]
    
    def gerar_sequencia(self, markov: Dict, semente: Any,
                        max_passos: int = 15, conf_min: float = 0.3,
                        max_repeticoes: int = 2) -> List[Any]:
        """Gera uma sequencia de tokens usando Markov chain universal.
        
        Usa predizer() repetidamente para gerar uma corrente de tokens.
        Qualquer tipo de token: str, int, bytes, tuple.
        Inclui limitador de repeticoes para evitar loops.
        
        Args:
            markov: {token: {proximo_token: prob}}
            semente: token inicial (qualquer tipo)
            max_passos: max tokens a gerar
            conf_min: confianca minima p/ aceitar cada passo
            max_repeticoes: max vezes que o mesmo token pode repetir consecutivo
        Returns:
            [token1, token2, ...] — sequencia gerada, vazia se falhar
        """
        sequencia = []
        atual = semente
        repeticoes_consecutivas = 0
        ultimo_token = None
        
        for _ in range(max_passos):
            proximo, conf = self.predizer(markov, atual)
            if proximo is None or conf < conf_min:
                break
            
            # Limitador de repeticoes consecutivas
            if proximo == ultimo_token:
                repeticoes_consecutivas += 1
                if repeticoes_consecutivas >= max_repeticoes:
                    # Tenta o SEGUNDO melhor se disponivel
                    proximos = markov.get(atual, {})
                    if len(proximos) > 1:
                        sorted_prox = sorted(proximos.items(), key=lambda x: -x[1])
                        for prox_alt, conf_alt in sorted_prox:
                            if prox_alt != proximo and conf_alt >= conf_min:
                                proximo = prox_alt
                                conf = conf_alt
                                repeticoes_consecutivas = 0
                                break
                    if repeticoes_consecutivas >= max_repeticoes:
                        break  # loop detectado, para
            else:
                repeticoes_consecutivas = 0
            
            sequencia.append(proximo)
            atual = proximo
            ultimo_token = proximo
        
        return sequencia
    
    def _predizer_markov(self, texto, markov_input, temperatura):
        """Prediz o proximo termo usando Markov chain.
        
        Tenta o Markov do KG primeiro (corpus grande, mais preciso).
        Se nao achar, tenta o Markov do input.
        """
        if not self._kg_markov and not markov_input:
            return ""
        
        # Pega a ultima palavra
        palavras = texto.split()
        if not palavras:
            return ""
        ultima = palavras[-1].lower().strip('.,!?;:()[]{}""''')
        
        # Tenta Markov do KG primeiro
        markov = self._kg_markov or markov_input
        if ultima not in markov and len(palavras) >= 2:
            ultima = palavras[-2].lower().strip('.,!?;:()[]{}""''')
        
        if ultima not in markov:
            return ""
        
        proximas = markov.get(ultima, {})
        if not proximas:
            return ""
        
        # Escolhe a palavra com maior probabilidade
        melhor = max(proximas, key=proximas.get)
        confianca = proximas[melhor]
        
        # So aceita se confianca minima
        if confianca < 0.3:
            return ""
        
        return melhor
    
    def _predizer_kg(self, texto):
        """Busca no KG por padrao similar e retorna a continuacao.
        
        Usa fingerprint do PatternEngine para encontrar a lesson
        mais similar, e extrai o trecho seguinte ao ponto de match.
        """
        if not self.kg:
            return ""
        
        try:
            # Busca lessons similares
            lessons = self.kg.buscar_expandido(texto, max_r=5) if hasattr(self.kg, 'buscar_expandido') else self.kg.buscar(texto, max_r=5)
            if not lessons:
                return ""
            
            # Se tem PatternEngine, calcula similaridade fingerprint
            if self.pe:
                fp_texto = self.pe.fingerprint(self.pe.tokenizar(texto, 'texto'))
                
                for l in lessons:
                    sol = l.get('solucao', '')
                    if sol and len(sol) > 20:
                        fp_lesson = self.pe.fingerprint(self.pe.tokenizar(sol, 'texto'))
                        sim = self.pe.similaridade(fp_texto, fp_lesson)
                        if sim > 0.6:
                            # Extrai a continuacao: o que vem depois do trecho similar
                            return self._extrair_continuacao(texto, sol)
            else:
                # Sem PE, pega a lesson com maior score
                melhor = lessons[0]
                sol = melhor.get('solucao', '')
                if sol:
                    return self._extrair_continuacao(texto, sol)
        except Exception:
            pass
        
        return ""
    
    def _extrair_continuacao(self, texto_original, texto_lesson):
        """Extrai o trecho de continuacao de uma lesson.
        
        Encontra onde o texto_original aparece no texto_lesson
        e retorna o que vem DEPOIS.
        """
        if not texto_lesson:
            return ""
        
        # Pega as primeiras palavras do texto original
        palavras_orig = texto_original.split()
        if not palavras_orig:
            return ""
        
        termo_busca = ' '.join(palavras_orig)
        idx = texto_lesson.lower().find(termo_busca.lower())
        
        if idx < 0:
            return ""
        
        # Pega o que vem depois do match
        depois = texto_lesson[idx + len(termo_busca):].strip()
        if not depois:
            return ""
        
        # Pega a primeira frase ou os primeiros 200 chars
        if '.' in depois:
            continuacao = depois.split('.')[0].strip()
        else:
            continuacao = depois.strip()
        
        if continuacao and len(continuacao) > 5:
            return continuacao
        
        return ""
    
    def avaliar_entropia(self, texto):
        """Avalia a entropia de um texto para decidir o metodo."""
        if not self.pe:
            return 0.5
        try:
            tokens = self.pe.tokenizar(texto, 'texto')
            padroes = self.pe.extrair_padroes(tokens)
            return padroes.get('entropia', 0.5)
        except Exception:
            return 0.5
    
    def decidir_metodo(self, texto):
        """Decide qual metodo usar baseado na entropia.
        
        Returns:
            str: 'markov', 'kg', 'ia', ou 'criativo'
        """
        entropia = self.avaliar_entropia(texto)
        
        if entropia < 0.4:
            return 'markov'
        elif entropia < 0.65:
            return 'kg'
        elif entropia < 0.85:
            return 'ia'
        else:
            return 'criativo'
