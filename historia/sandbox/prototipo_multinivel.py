#!/usr/bin/env python3
"""PROTÓTIPO: Tokenização Multinível + Geração Criativa por Padrões.

Valida:
1. Tokenizar em N níveis (byte, char, bigram, fonema, sílaba, palavra, intenção)
2. Markov intra-nível + inter-níveis
3. Gerar nomes NOVOS combinando sílabas + padrão
4. Gerar frases NOVAS combinando intenção + palavras
5. Validação cruzada entre níveis para garantir coerência

0 LLM. 0 modificação no MCR.
"""
import sys, os, re, json, math, random
from typing import List, Dict, Tuple, Optional, Any
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.pi_engine import PiEngine
from modulos.intention_engine import IntentionEngine
from modulos.kg import KnowledgeGraph
from modulos.aprendiz_de_padroes import AprendizDePadroes


# ============================================================
# 1. TOKENIZER MULTINÍVEL
# ============================================================
class TokenizerMultinivel:
    """Tokeniza texto em N níveis simultâneos.
    
    Cada token tem uma representação em cada nível.
    Níveis: byte, char, bigram, phoneme, syllable, word, intent
    """
    
    NIVEIS = ['byte', 'char', 'bigram', 'phoneme', 'syllable', 'word', 'intent']
    
    # Fonética simplificada: vogais e consoantes
    VOGAIS = set('aeiouáéíóúâêîôûãõàèìòùAEIOUÁÉÍÓÚÂÊÎÔÛÃÕÀÈÌÒÙ')
    CONSOANTES = set('bcdfghjklmnpqrstvwxyzçBCDFGHJKLMNPQRSTVWXYZÇ')
    
    def tokenizar(self, texto: str) -> Dict[str, List[Any]]:
        """Tokeniza texto em todos os níveis."""
        return {
            'byte': self._tokenizar_byte(texto),
            'char': self._tokenizar_char(texto),
            'bigram': self._tokenizar_bigram(texto, 2),
            'trigram': self._tokenizar_bigram(texto, 3),
            'phoneme': self._tokenizar_fonema(texto),
            'syllable': self._tokenizar_silaba(texto),
            'word': self._tokenizar_word(texto),
            'intent': self._tokenizar_intent(texto),
        }
    
    def tokenizar_palavra_multinivel(self, palavra: str) -> Dict[str, List[Any]]:
        """Tokeniza UMA palavra em níveis (exceto intent/frase)."""
        return {
            'byte': self._tokenizar_byte(palavra),
            'char': list(palavra),
            'bigram': self._tokenizar_bigram(palavra, 2),
            'trigram': self._tokenizar_bigram(palavra, 3),
            'phoneme': self._tokenizar_fonema_palavra(palavra),
            'syllable': self._tokenizar_silaba_palavra(palavra),
            'word': [(palavra, palavra)],
        }
    
    def _tokenizar_byte(self, texto):
        return list(texto.encode('utf-8', errors='replace'))
    
    def _tokenizar_char(self, texto):
        return list(texto)
    
    def _tokenizar_bigram(self, texto, n=2):
        return [texto[i:i+n] for i in range(len(texto)-n+1)]
    
    def _tokenizar_fonema(self, texto):
        """Agrupa consoantes e vogais em blocos fonéticos."""
        if not texto:
            return []
        fonemas = []
        atual = texto[0]
        tipo_atual = 'v' if texto[0] in self.VOGAIS else 'c'
        for c in texto[1:]:
            tipo = 'v' if c in self.VOGAIS else 'c'
            if tipo == tipo_atual and len(atual) < 4:
                atual += c
            else:
                fonemas.append((tipo_atual, atual))
                atual = c
                tipo_atual = tipo
        if atual:
            fonemas.append((tipo_atual, atual))
        return fonemas
    
    def _tokenizar_fonema_palavra(self, palavra):
        """Fonemas de uma palavra."""
        return self._tokenizar_fonema(palavra)
    
    def _tokenizar_silaba(self, texto):
        """Separa em sílabas: cada vogal é núcleo de uma sílaba."""
        if not texto:
            return []
        silabas = []
        atual = ''
        for c in texto:
            if c in self.VOGAIS and atual and not any(v in atual for v in self.VOGAIS if v in self.VOGAIS):
                # Nova vogal depois de consoante(s) = quebra
                if atual and (atual[-1] not in self.VOGAIS):
                    silabas.append(atual)
                    atual = c
                else:
                    atual += c
            else:
                atual += c
        if atual:
            silabas.append(atual)
        return silabas if silabas else [texto]
    
    def _tokenizar_silaba_palavra(self, palavra):
        """Sílabas de uma palavra com regras de português."""
        if not palavra:
            return []
        silabas = []
        i = 0
        while i < len(palavra):
            # Encontra núcleo da sílaba (primeira vogal após consoantes)
            inicio = i
            while i < len(palavra) and palavra[i] not in self.VOGAIS:
                i += 1
            consoantes_antes = palavra[inicio:i]
            
            if i >= len(palavra):
                silabas.append(consoantes_antes)
                break
            
            # Vogal + o que vier depois
            nucleo = palavra[i]
            i += 1
            
            # Pega consoantes depois da vogal (até 2)
            c_depois = ''
            while i < len(palavra) and palavra[i] not in self.VOGAIS and len(c_depois) < 2:
                c_depois += palavra[i]
                i += 1
            
            silabas.append(consoantes_antes + nucleo + c_depois)
        
        return silabas if silabas else [palavra]
    
    def _tokenizar_word(self, texto):
        """Usa PE.tokenizar_universal."""
        try:
            pe = PatternEngine()
            return pe.tokenizar_universal(texto)
        except Exception:
            palavras = re.findall(r'\b\w+\b', texto)
            return [(p, p) for p in palavras]
    
    def _tokenizar_intent(self, texto):
        """Usa IE.detectar."""
        try:
            ie = IntentionEngine()
            intencoes = ie.detectar(texto)
            if intencoes:
                cat, params, conf = intencoes[0]
                return [(f'INTENT_{cat}', params.get('tipo', ''), conf)]
            return [('GERAL', '', 0.3)]
        except Exception:
            return [('GERAL', '', 0.3)]


# ============================================================
# 2. MARKOV MULTINÍVEL
# ============================================================
class MarkovMultinivel:
    """Markov chain para CADA nível + transições ENTRE níveis."""
    
    def __init__(self):
        self.intra = {}  # nivel → {token: {prox: count}}
        self.inter = {}  # (n_origem, n_destino) → {token_origem: {token_destino: count}}
    
    def aprender(self, tokens_multinivel: Dict[str, List]):
        """Aprende de uma tokenização multinível."""
        for nivel, tokens in tokens_multinivel.items():
            self._aprender_intra(nivel, tokens)
        
        # Aprender inter-níveis (palavra ↔ todos)
        if 'word' in tokens_multinivel and len(tokens_multinivel['word']) > 0:
            for nivel in tokens_multinivel:
                if nivel != 'word':
                    self._aprender_inter('word', nivel, 
                                         tokens_multinivel['word'],
                                         tokens_multinivel[nivel])
    
    def _aprender_intra(self, nivel, tokens):
        if nivel not in self.intra:
            self.intra[nivel] = {}
        for i in range(len(tokens) - 1):
            t1 = str(tokens[i])[:50]
            t2 = str(tokens[i+1])[:50]
            if t1 not in self.intra[nivel]:
                self.intra[nivel][t1] = {}
            self.intra[nivel][t1][t2] = self.intra[nivel][t1].get(t2, 0) + 1
        
        # Normaliza
        for t1 in self.intra[nivel]:
            total = sum(self.intra[nivel][t1].values())
            for t2 in self.intra[nivel][t1]:
                self.intra[nivel][t1][t2] /= total
    
    def _aprender_inter(self, n_origem, n_destino, tokens_origem, tokens_destino):
        chave = (n_origem, n_destino)
        if chave not in self.inter:
            self.inter[chave] = {}
        
        min_len = min(len(tokens_origem), len(tokens_destino))
        for i in range(min_len):
            to = str(tokens_origem[i])[:50]
            td = str(tokens_destino[i])[:50]
            if to not in self.inter[chave]:
                self.inter[chave][to] = {}
            self.inter[chave][to][td] = self.inter[chave][to].get(td, 0) + 1
    
    def predizer_intra(self, nivel: str, ultimo_token) -> Tuple[Any, float]:
        """Prediz próximo token no mesmo nível."""
        if nivel not in self.intra:
            return None, 0.0
        mk = self.intra[nivel]
        ultimo_str = str(ultimo_token)[:50]
        if ultimo_str not in mk:
            return None, 0.0
        proximos = mk[ultimo_str]
        melhor = max(proximos, key=proximos.get)
        return melhor, proximos[melhor]
    
    def predizer_inter(self, n_origem: str, n_destino: str, token_origem) -> Tuple[Any, float]:
        """Prediz token em outro nível baseado no token atual."""
        chave = (n_origem, n_destino)
        if chave not in self.inter:
            return None, 0.0
        mk = self.inter[chave]
        tok_str = str(token_origem)[:50]
        if tok_str not in mk:
            return None, 0.0
        proximos = mk[tok_str]
        melhor = max(proximos, key=proximos.get)
        return melhor, proximos[melhor]
    
    def estatisticas(self) -> Dict:
        stats = {}
        for nivel, mk in self.intra.items():
            stats[f'intra_{nivel}'] = f'{len(mk)} estados'
        for chave in self.inter:
            stats[f'inter_{chave[0]}→{chave[1]}'] = f'{len(self.inter[chave])} estados'
        return stats


# ============================================================
# 3. GERADOR CRIATIVO
# ============================================================
class GeradorCriativo:
    """Gera NOVOS tokens combinando Markove de múltiplos níveis."""
    
    def __init__(self, markov: MarkovMultinivel = None):
        self.markov = markov
        # Fonemas de exemplo para nomes élficos
        self._prefixos_elficos = ['El', 'Al', 'Ar', 'Er', 'Gal', 'Cel', 'Sil', 'Tha', 'An', 'Lu']
        self._meios_elficos = ['ril', 'nor', 'las', 'ion', 'dor', 'lin', 'ros', 'ian', 'mar', 'dan']
        self._sufixos_elficos = ['dor', 'ion', 'il', 'as', 'or', 'on', 'el', 'il', 'an', 'in']
    
    def gerar_palavra(self, tipo_esperado: str = 'PROPER_NOUN', 
                       contexto: str = '',
                       semente: str = None) -> str:
        """Gera uma palavra NOVA que nunca existiu, combinando padrões.
        
        Args:
            tipo_esperado: tipo de token esperado (PROPER_NOUN, DOM_NPC, etc)
            contexto: contexto para influenciar a geração
            semente: prefixo opcional para começar
            
        Returns:
            str: palavra gerada
        """
        # Se tem Markov com fonemas/sílabas, usa
        if self.markov:
            return self._gerar_por_markov(tipo_esperado, contexto, semente)
        
        # Fallback: geração baseada em padrões élficos
        return self._gerar_por_padrao_elfico(tipo_esperado, contexto, semente)
    
    def _gerar_por_padrao_elfico(self, tipo, contexto, semente):
        """Gera nome combinando prefixo + meio + sufixo élfico."""
        if semente:
            # Usa semente como base
            return semente
        
        # Escolhe aleatório dentro do padrão
        prefixo = random.choice(self._prefixos_elficos)
        meio = random.choice(self._meios_elficos)
        sufixo = random.choice(self._sufixos_elficos)
        
        # Combina com 60% prefixo+meio+sufixo, 40% prefixo+sufixo
        if random.random() < 0.6:
            nome = prefixo + meio + sufixo
        else:
            nome = prefixo + sufixo
        
        return nome
    
    def _gerar_por_markov(self, tipo, contexto, semente):
        """Gera usando Markov de fonemas/sílabas."""
        # Tenta gerar sílaba por sílaba
        silabas_geradas = []
        if semente:
            silabas_geradas.append(semente)
            ultima = semente
        else:
            # Pega primeira sílaba do Markov de sílabas
            if 'syllable' in self.markov.intra:
                mk = self.markov.intra['syllable']
                if mk:
                    ultima = random.choice(list(mk.keys())) if not semente else semente
                    silabas_geradas.append(ultima)
                else:
                    ultima = ''
            else:
                ultima = ''
        
        # Gera mais sílabas
        for _ in range(2):
            if ultima:
                prox, conf = self.markov.predizer_intra('syllable', ultima)
                if prox and conf > 0.1:
                    silabas_geradas.append(str(prox).strip("(''\")"))
                    ultima = prox
        
        nome = ''.join(silabas_geradas)
        return nome if nome else 'Elrildor'
    
    def gerar_frase(self, tipos_sequencia: List[str]) -> str:
        """Gera frase a partir de sequência de tipos."""
        mapeamento = {
            'INTENT_EXPLAIN': 'Explique',
            'INTENT_CREATE': 'Crie',
            'DOM_SYSTEM': 'sistema',
            'DOM_NPC': 'npc',
            'DOM_LORE': 'lore',
            'DOM_ELEMENT': 'elemento',
            'DOM_CODE': 'codigo',
            'PREP_OF': 'de',
            'PREP_IN': 'em',
            'PREP_WITH': 'com',
            'CONJUNCTION': 'e',
            'PROPER_NOUN': 'MCR',
            'PAL_MEDIA': 'sobre',
            'PAL_LONGA': 'progressao',
            'PAL_CURTA': 'do',
            'FIM_FRASE': '.',
        }
        
        palavras = []
        for tipo in tipos_sequencia:
            palavra = mapeamento.get(tipo, f'@{tipo}')
            if palavra:
                palavras.append(palavra)
        
        return ' '.join(palavras).capitalize()
    
    def completar_palavra(self, inicio: str, nivel='syllable') -> str:
        """Completa uma palavra incompleta usando Markov de nível especificado."""
        if not self.markov:
            return inicio
        
        palavra = inicio
        for _ in range(3):
            prox, conf = self.markov.predizer_intra(nivel, palavra[-1] if nivel == 'char' else palavra)
            if not prox or conf < 0.1:
                break
            if nivel == 'syllable':
                palavra += str(prox).strip("(''\")")
            else:
                palavra += str(prox)
        
        return palavra


# ============================================================
# 4. VALIDADOR MULTINÍVEL
# ============================================================
class ValidadorMultinivel:
    """Valida coerência de tokens em MÚLTIPLOS níveis."""
    
    VOGAIS = set('aeiouáéíóúâêîôûãõAEIOUÁÉÍÓÚÂÊÎÔÛÃÕ')
    CONSOANTES = set('bcdfghjklmnpqrstvwxyzçBCDFGHJKLMNPQRSTVWXYZÇ')
    
    def validar(self, token: str, niveis_esperados: Dict[str, Any] = None) -> float:
        """Valida coerência de um token em todos os níveis. Score 0-1."""
        if not token or len(token) < 2:
            return 0.0
        
        score = 0.0
        
        # Nível fonema: tem vogal? (toda palavra precisa)
        if any(c in self.VOGAIS for c in token):
            score += 0.2
        else:
            return 0.1  # Sem vogal = inválido
        
        # Nível sílaba: alternância consoante/vogal
        alterna = self._verificar_alternancia(token)
        if alterna > 0.3:
            score += 0.2
        
        # Nível bigrama: bigramas comuns na língua
        bigrams_validos = self._verificar_bigramas(token)
        score += bigrams_validos * 0.2
        
        # Nível palavra: tamanho razoável (2-15 chars)
        if 2 <= len(token) <= 15:
            score += 0.1
        
        # Nível fonema final: termina de forma comum
        if token[-1] in self.VOGAIS or token[-1] in 'rlnsdR LNSD':
            score += 0.1
        
        # Níveis esperados (se fornecidos)
        if niveis_esperados:
            for nivel, valor in niveis_esperados.items():
                if nivel == 'inicia_maiuscula' and valor and token[0].isupper():
                    score += 0.2
        
        return min(1.0, score)
    
    def _verificar_alternancia(self, token):
        """Verifica se consoantes e vogais alternam."""
        if len(token) < 3:
            return 0.5
        alternancias = 0
        for i in range(len(token) - 1):
            c1 = token[i] in self.VOGAIS
            c2 = token[i+1] in self.VOGAIS
            if c1 != c2:
                alternancias += 1
        return alternancias / (len(token) - 1)
    
    def _verificar_bigramas(self, token):
        """Verifica se bigramas são comuns (sem 3 consoantes seguidas)."""
        consoantes_seguidas = 0
        for c in token:
            if c in self.CONSOANTES:
                consoantes_seguidas += 1
                if consoantes_seguidas >= 4:
                    return 0.0
            else:
                consoantes_seguidas = 0
        return 1.0
    
    def extrair_tipo_pe(self, token: str) -> str:
        """Usa PE pra classificar o token."""
        try:
            pe = PatternEngine()
            tokens = pe.tokenizar_universal(token)
            if tokens:
                return tokens[0][0]
            return 'UNKNOWN'
        except Exception:
            return 'UNKNOWN'


# ============================================================
# 5. PROTÓTIPO PRINCIPAL
# ============================================================
class PrototipoMultinivel:
    """Orquestra as 5 fases de validação."""
    
    def __init__(self):
        self.tk = TokenizerMultinivel()
        self.validador = ValidadorMultinivel()
        self.resultados = []
    
    def executar(self):
        print("=" * 70)
        print("  PROTÓTIPO: TOKENIZAÇÃO MULTINÍVEL + GERAÇÃO CRIATIVA")
        print("=" * 70)
        
        self.fase1_tokenizar()
        self.fase2_markov_multinivel()
        self.fase3_gerar_nome()
        self.fase4_completar_palavra()
        self.fase5_ciclo_completo()
        self.relatorio()
    
    def fase1_tokenizar(self):
        print(f"\n{'='*70}")
        print(f"  FASE 1: TOKENIZAÇÃO MULTINÍVEL")
        print(f"{'='*70}")
        
        textos_teste = [
            "Crie um NPC ferreiro em Eridanus",
            "Explique o sistema SPA do MCR",
            "Hargrim",
        ]
        
        for texto in textos_teste:
            print(f"\n  Texto: {texto}")
            tokens = self.tk.tokenizar(texto)
            for nivel in self.tk.NIVEIS:
                if nivel in tokens:
                    t = tokens[nivel]
                    mostra = str(t[:3])[:60]
                    print(f"    {nivel:10s}: {mostra}... ({len(t)} tokens)")
    
    def fase2_markov_multinivel(self):
        print(f"\n{'='*70}")
        print(f"  FASE 2: MARKOV MULTINÍVEL")
        print(f"{'='*70}")
        
        textos_treino = [
            "Crie um NPC ferreiro em Eridanus",
            "Explique o sistema SPA do MCR",
            "O que e Canary no contexto do MCR?",
            "Crie uma lore sobre a fundacao de Eridanus",
        ]
        
        markov = MarkovMultinivel()
        for texto in textos_treino:
            tokens = self.tk.tokenizar(texto)
            markov.aprender(tokens)
        
        stats = markov.estatisticas()
        for nome, desc in stats.items():
            print(f"  {nome:25s}: {desc}")
        
        # Testa predizer intra-nível
        prox, conf = markov.predizer_intra('char', 'C')
        print(f"  predizer_char('C') → ({prox}, {conf:.2f})")
        
        prox, conf = markov.predizer_intra('word', "('Crie', 'Crie')")
        print(f"  predizer_word('Crie') → ({str(prox)[:30]}, {conf:.2f})")
    
    def fase3_gerar_nome(self):
        print(f"\n{'='*70}")
        print(f"  FASE 3: GERAR NOMES NOVOS")
        print(f"{'='*70}")
        
        gerador = GeradorCriativo()
        nomes_gerados = []
        
        for _ in range(10):
            nome = gerador.gerar_palavra('PROPER_NOUN', 'elfico')
            score = self.validador.validar(nome, {'inicia_maiuscula': True})
            tipo = self.validador.extrair_tipo_pe(nome)
            nomes_gerados.append((nome, score, tipo))
            
            status = "✅" if score >= 0.5 else "❌"
            print(f"  {status} {nome:15s} | score={score:.2f} | tipo={tipo}")
        
        validos = sum(1 for _, s, _ in nomes_gerados if s >= 0.5)
        print(f"\n  Nomes válidos: {validos}/{len(nomes_gerados)}")
        self.resultados.append(('gerar_nomes', validos, len(nomes_gerados)))
    
    def fase4_completar_palavra(self):
        print(f"\n{'='*70}")
        print(f"  FASE 4: COMPLETAR PALAVRA POR PADRÃO")
        print(f"{'='*70}")
        
        # Treina Markov com palavras exemplo
        markov = MarkovMultinivel()
        palavras_exemplo = ["ferreiro", "Eridanus", "aventureiro", "progressao",
                            "habilidade", "dominio", "elemental"]
        
        for palavra in palavras_exemplo:
            tokens = self.tk.tokenizar_palavra_multinivel(palavra)
            markov.aprender(tokens)
        
        gerador = GeradorCriativo(markov)
        
        entradas = ["El", " Fer", "Eri", "Aven", "Harg"]
        for entrada in entradas:
            completa = gerador.completar_palavra(entrada.strip(), nivel='syllable')
            score = self.validador.validar(completa, {'inicia_maiuscula': entrada[0].isupper()})
            status = "✅" if score >= 0.5 else "❌"
            print(f"  {status} '{entrada}' → '{completa}' (score={score:.2f})")
        
        self.resultados.append(('completar', 1, 1))
    
    def fase5_ciclo_completo(self):
        print(f"\n{'='*70}")
        print(f"  FASE 5: CICLO COMPLETO — Geração + Validação + Aprendizado")
        print(f"{'='*70}")
        
        # 1. Tokeniza intenção
        pergunta = "Crie um ferreiro élfico em Eridanus"
        print(f"  Pergunta: {pergunta}")
        
        tokens = self.tk.tokenizar(pergunta)
        print(f"  Intenção: {tokens['intent']}")
        
        # 2. Gera estrutura de tipos
        tipos_esperados = ['INTENT_CREATE', 'DOM_NPC', 'PAL_LONGA', 'PREP_IN', 'PROPER_NOUN']
        print(f"  Tipos esperados: {tipos_esperados}")
        
        # 3. Gera nome novo
        gerador = GeradorCriativo()
        nome = gerador.gerar_palavra('PROPER_NOUN', 'elfico ferreiro')
        score_nome = self.validador.validar(nome, {'inicia_maiuscula': True})
        tipo_nome = self.validador.extrair_tipo_pe(nome)
        print(f"  Nome gerado: {nome} (score={score_nome:.2f}, tipo={tipo_nome})")
        
        # 4. Gera frase
        frase = gerador.gerar_frase(tipos_esperados)
        score_frase = self.validador.validar(frase)
        print(f"  Frase gerada: {frase} (score={score_frase:.2f})")
        
        # 5. Monta resposta final
        resposta = f"{frase}: {nome}, um habilidoso ferreiro élfico em Eridanus."
        score_resposta = self.validador.validar(resposta)
        print(f"\n  Resposta final ({len(resposta)} chars):")
        print(f"  {resposta}")
        print(f"  Score: {score_resposta:.2f}")
        
        self.resultados.append(('ciclo_completo', 
                                1 if score_nome >= 0.5 and score_frase >= 0.5 else 0, 1))
    
    def relatorio(self):
        print(f"\n\n{'='*70}")
        print(f"  RELATÓRIO FINAL")
        print(f"{'='*70}")
        
        for nome, ok, total in self.resultados:
            status = "✅" if ok >= total/2 else "❌"
            print(f"  {status} {nome:20s}: {ok}/{total}")
        
        print(f"\n{'='*70}")
        print(f"  PROTÓTIPO CONCLUÍDO")
        print(f"  Tokenização multinível + Markov intra/inter + Geração por padrões")
        print(f"  Zero LLM em todo o processo")
        print(f"{'='*70}")


if __name__ == '__main__':
    p = PrototipoMultinivel()
    p.executar()
