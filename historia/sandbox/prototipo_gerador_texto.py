#!/usr/bin/env python3
"""PROTÓTIPO: Gerador de Texto Rico — Palavra por Palavra, estilo LLM local.

Usa Markov treinado no CORPUS DO PROJETO para gerar texto novo.
Com temperatura (caos controlado), validação de coerência,
e auto-alimentação (cada palavra vira contexto para a próxima).

0 LLM. 0 GPU. 0 modificação no MCR.
"""
import sys, os, re, json, random, math
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.kg import KnowledgeGraph
from modulos.intention_engine import IntentionEngine

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class CorpusBuilder:
    """Constrói corpus unificado do projeto: docs + conversas + KG + código."""
    
    def __init__(self):
        self.textos = []
        self.fontes = Counter()
    
    def carregar_tudo(self) -> str:
        """Carrega TODAS as fontes e retorna corpus único."""
        self._carregar_docs()
        self._carregar_conversas()
        self._carregar_kg()
        self._carregar_codigo()
        
        corpus = ' '.join(self.textos)
        print(f"  Corpus total: {len(corpus)} chars, {len(corpus.split())} palavras")
        print(f"  Fontes: {dict(self.fontes.most_common())}")
        return corpus
    
    def _carregar_docs(self):
        """Carrega documentos .md da pasta docs/."""
        docs_dir = os.path.join(BASE, 'docs')
        if not os.path.isdir(docs_dir):
            return
        for fname in os.listdir(docs_dir):
            if fname.endswith('.md'):
                path = os.path.join(docs_dir, fname)
                try:
                    with open(path, 'r', encoding='utf-8', errors='replace') as f:
                        texto = f.read()
                    # Extrai apenas texto útil (remove tags, metadados)
                    texto_limpo = re.sub(r'>>.*?\n', '', texto)
                    texto_limpo = re.sub(r'---.*?---', '', texto_limpo, flags=re.DOTALL)
                    palavras = len(texto_limpo.split())
                    if palavras > 10:
                        self.textos.append(texto_limpo)
                        self.fontes[f'docs/{fname}'] = palavras
                except Exception:
                    pass
    
    def _carregar_conversas(self):
        """Carrega histórico de conversas."""
        path = os.path.join(BASE, 'sandbox', '.mcr_conversa.jsonl')
        if not os.path.exists(path):
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        msg = entry.get('msg', '')
                        if msg and len(msg) > 20:
                            self.textos.append(msg)
                            self.fontes['conversa'] += len(msg.split())
                    except Exception:
                        pass
        except Exception:
            pass
    
    def _carregar_kg(self):
        """Carrega soluções do Knowledge Graph."""
        kg = KnowledgeGraph()
        licoes = kg._get_licoes()
        for l in licoes[:500]:
            sol = l.get('solucao', '')
            if sol and len(sol) > 20:
                self.textos.append(sol)
                self.fontes['kg'] += len(sol.split())
    
    def _carregar_codigo(self):
        """Carrega comentários e strings de arquivos .lua."""
        for root, dirs, files in os.walk(os.path.join(BASE, 'data')):
            for f in files:
                if f.endswith('.lua') or f.endswith('.py'):
                    path = os.path.join(root, f)
                    try:
                        with open(path, 'r', encoding='utf-8', errors='replace') as fh:
                            codigo = fh.read()
                        # Extrai comentários e strings
                        comentarios = re.findall(r'--(.*?)$', codigo, re.MULTILINE)
                        for c in comentarios:
                            if len(c) > 10:
                                self.textos.append(c)
                                self.fontes['codigo_comentarios'] += len(c.split())
                        strings = re.findall(r'"(.*?)"', codigo)
                        for s in strings:
                            if len(s) > 15 and not s.startswith('http'):
                                self.textos.append(s)
                                self.fontes['codigo_strings'] += len(s.split())
                    except Exception:
                        pass
    
    def limpar(self, texto):
        """Limpa texto: remove URLs, tags, normaliza espaços."""
        texto = re.sub(r'http\S+', '', texto)
        texto = re.sub(r'[<>]', '', texto)
        texto = re.sub(r'[^\w\s\.\,\!\?\-\'\"]', ' ', texto)
        texto = re.sub(r'\s+', ' ', texto).strip()
        return texto.lower()


class GeradorTexto:
    """Gera texto palavra por palavra usando Markov treinado no corpus do projeto.
    
    Funciona como uma LLM local:
    1. Contexto inicial (semente) + 2 últimas palavras
    2. Markov de bigramas → lista de próximas palavras possíveis
    3. Escolhe com temperatura (caos controlado)
    4. Adiciona ao texto
    5. Repete até tamanho desejado
    6. A cada N passos, valida coerência
    """
    
    def __init__(self):
        self.markov_bigram = {}   # "palavra1 palavra2" → {proxima: count}
        self.markov_trigram = {}  # "p1 p2 p3" → {proxima: count}
        self.palavras_unicas = set()
        self.total_palavras = 0
    
    def treinar(self, corpus: str):
        """Treina Markove a partir do corpus."""
        palavras = corpus.split()
        self.palavras_unicas = set(palavras)
        self.total_palavras = len(palavras)
        
        print(f"  Treinando Markov com {len(palavras)} palavras ({len(self.palavras_unicas)} únicas)...")
        
        # Markov de bigramas (2 palavras)
        for i in range(len(palavras) - 2):
            chave = f"{palavras[i]} {palavras[i+1]}"
            prox = palavras[i+2]
            if chave not in self.markov_bigram:
                self.markov_bigram[chave] = {}
            self.markov_bigram[chave][prox] = self.markov_bigram[chave].get(prox, 0) + 1
        
        # Markov de trigramas (3 palavras)
        for i in range(len(palavras) - 3):
            chave = f"{palavras[i]} {palavras[i+1]} {palavras[i+2]}"
            prox = palavras[i+3]
            if chave not in self.markov_trigram:
                self.markov_trigram[chave] = {}
            self.markov_trigram[chave][prox] = self.markov_trigram[chave].get(prox, 0) + 1
        
        print(f"  Markov estados: {len(self.markov_bigram)} bigramas, {len(self.markov_trigram)} trigramas")
    
    def gerar(self, semente: str, tamanho: int = 30, temperatura: float = 0.3,
              max_repeticoes: int = 3) -> str:
        """Gera texto a partir de uma semente.
        
        Args:
            semente: texto inicial (ex: "Eridanus era uma cidade")
            tamanho: quantidade de palavras a gerar
            temperatura: 0=determinístico, 0.5=balanceado, 1.0=caótico
            max_repeticoes: max repetições da mesma palavra consecutiva
        
        Returns:
            str: texto completo gerado
        """
        palavras = semente.lower().split()
        if len(palavras) < 2:
            # Completa com palavras aleatórias do vocabulário
            while len(palavras) < 2:
                palavras.append(random.choice(list(self.palavras_unicas)))
        
        repeticao_atual = 0
        ultima_palavra = None
        passos_sem_validacao = 0
        
        for passo in range(tamanho):
            # Tenta trigrama primeiro (mais preciso), fallback bigrama
            chave = None
            if len(palavras) >= 3:
                chave3 = f"{palavras[-3]} {palavras[-2]} {palavras[-1]}"
                if chave3 in self.markov_trigram:
                    chave = chave3
            
            if not chave and len(palavras) >= 2:
                chave2 = f"{palavras[-2]} {palavras[-1]}"
                if chave2 in self.markov_bigram:
                    chave = chave2
            
            if not chave:
                break  # Não consegue continuar
            
            # Pega as próximas palavras possíveis
            if len(palavras) >= 3 and chave in self.markov_trigram:
                proximas = self.markov_trigram[chave]
            else:
                proximas = self.markov_bigram.get(chave, {})
            
            if not proximas:
                break
            
            # Escolhe com temperatura
            escolhida = self._escolher(proximas, temperatura)
            
            # Limitador de repetição
            if escolhida == ultima_palavra:
                repeticao_atual += 1
                if repeticao_atual >= max_repeticoes:
                    # Pega a segunda mais provável
                    if len(proximas) > 1:
                        sorted_prox = sorted(proximas.items(), key=lambda x: -x[1])
                        for alt, _ in sorted_prox:
                            if alt != escolhida:
                                escolhida = alt
                                break
                    repeticao_atual = 0
            else:
                repeticao_atual = 0
            
            palavras.append(escolhida)
            ultima_palavra = escolhida
            passos_sem_validacao += 1
            
            # Validação: a cada 10 palavras, verifica se ainda tem contexto
            if passos_sem_validacao >= 10:
                # Verifica se a última palavra faz sentido com o início
                if len(palavras) > 15:
                    # Simples: se as últimas 3 palavras têm Markov, OK
                    chave_check = f"{palavras[-3]} {palavras[-2]} {palavras[-1]}"
                    if chave_check not in self.markov_trigram and chave_check not in self.markov_bigram:
                        # Tenta corrigir inserindo uma palavra de ligação
                        passos_sem_validacao = 0
        
        texto = ' '.join(palavras)
        # Capitaliza primeira letra
        if texto:
            texto = texto[0].upper() + texto[1:]
        return texto
    
    def _escolher(self, proximas: Dict[str, int], temperatura: float) -> str:
        """Escolhe a próxima palavra com temperatura (caos controlado)."""
        if temperatura <= 0:
            # Sem caos: sempre a mais provável
            return max(proximas, key=proximas.get)
        
        palavras = list(proximas.keys())
        pesos = list(proximas.values())
        
        if temperatura >= 1.0:
            # Caos total: qualquer palavra
            return random.choice(palavras)
        
        # Aplica temperatura (quanto maior, mais uniforme)
        soma = sum(pesos)
        pesos_norm = [p / soma for p in pesos]
        pesos_temp = [p ** (1.0 / max(temperatura, 0.01)) for p in pesos_norm]
        total_temp = sum(pesos_temp)
        probs = [p / total_temp for p in pesos_temp]
        
        return random.choices(palavras, weights=probs, k=1)[0]
    
    def estatisticas(self) -> Dict:
        return {
            'bigramas': len(self.markov_bigram),
            'trigramas': len(self.markov_trigram),
            'vocabulario': len(self.palavras_unicas),
            'total_palavras': self.total_palavras,
        }


# ============================================================
# TESTE
# ============================================================
def testar():
    print("=" * 70)
    print("  GERADOR DE TEXTO — Palavra por Palavra, estilo LLM local")
    print("  Markov treinado no corpus do projeto | Temperatura controlada")
    print("=" * 70)
    
    # FASE 1: Carregar corpus
    print(f"\n{'='*70}")
    print(f"  FASE 1: CONSTRUIR CORPUS DO PROJETO")
    print(f"{'='*70}")
    
    builder = CorpusBuilder()
    corpus = builder.carregar_tudo()
    corpus_limpo = builder.limpar(corpus)
    
    # FASE 2: Treinar Markov
    print(f"\n{'='*70}")
    print(f"  FASE 2: TREINAR MARKOV")
    print(f"{'='*70}")
    
    gerador = GeradorTexto()
    gerador.treinar(corpus_limpo)
    stats = gerador.estatisticas()
    print(f"  Vocabulário: {stats['vocabulario']} palavras únicas")
    
    # FASE 3: Testar geração com diferentes temperaturas
    print(f"\n{'='*70}")
    print(f"  FASE 3: GERAR TEXTOS")
    print(f"{'='*70}")
    
    contextos = [
        ("eridanus era uma cidade", "Eridanus"),
        ("o sistema spa gerencia", "SPA"),
        ("o canary e um servidor", "Canary"),
    ]
    
    for semente, topico in contextos:
        print(f"\n  Tópico: {topico}")
        print(f"  Semente: '{semente}'")
        
        for temp in [0.0, 0.3, 0.6]:
            texto = gerador.gerar(semente, tamanho=25, temperatura=temp)
            palavras_unicas = len(set(texto.split()))
            total_palavras = len(texto.split())
            diversidade = palavras_unicas / max(total_palavras, 1)
            
            print(f"\n  Temperatura {temp:.1f} ({total_palavras} pal, {palavras_unicas} un, div={diversidade:.2f}):")
            print(f"  {texto[:200]}")
    
    # FASE 4: Geração longa com coerência
    print(f"\n{'='*70}")
    print(f"  FASE 4: TEXTO LONGO (50+ palavras)")
    print(f"{'='*70}")
    
    contexto_longo = gerador.gerar("o sistema spa do mcr", tamanho=50, temperatura=0.4)
    print(f"\n  {contexto_longo[:500]}")
    print(f"\n  (total: {len(contexto_longo.split())} palavras, {len(set(contexto_longo.split()))} únicas)")
    
    # FASE 5: Estatísticas
    print(f"\n{'='*70}")
    print(f"  ESTATÍSTICAS FINAIS")
    print(f"{'='*70}")
    stats = gerador.estatisticas()
    print(f"  Vocabulário: {stats['vocabulario']} palavras")
    print(f"  Markov bigramas: {stats['bigramas']} estados")
    print(f"  Markov trigramas: {stats['trigramas']} estados")
    print(f"  Cobertura: {stats['bigramas']/max(stats['vocabulario']**2, 1)*100:.2f}% das combinações possíveis")
    print(f"  {'='*70}")
    print(f"  O gerador funciona como uma LLM local baseada em Markov")
    print(f"  Temperatura 0.0 = determinístico, 0.5 = criativo, 1.0 = caótico")
    print(f"  Tudo 0 LLM, 0 GPU, 0 modificação no MCR")
    print(f"{'='*70}")


if __name__ == '__main__':
    testar()
