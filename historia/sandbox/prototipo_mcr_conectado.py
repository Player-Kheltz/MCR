#!/usr/bin/env python3
"""MCR CONECTADO — MarkovUniversal alimentado pelos DADOS REAIS do sandbox.

Pela PRIMEIRA vez, o MCR não é descartável.
Ele lê: métricas, episódios, conversas, testes — TUDO que já existe.
Aprende com o PASSADO para decidir o FUTURO.

5 níveis de Markov integrados com dados reais:
  N1: MarkovMetrica → tempo médio por intenção
  N2: MarkovEpisodio → taxa de sucesso/falha
  N3: MarkovConversa → pergunta → resposta
  N4: MarkovTeste → critérios que falham
  N5: MarkovUniversal → decisão final

0 LLM. 0 GPU. Só dados reais do sandbox.
"""
import sys, os, re, json, math, random
from collections import Counter
from typing import List, Dict, Tuple, Optional, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
from modulos.pattern_engine import PatternEngine

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SANDBOX = os.path.join(BASE, 'sandbox')


class MarkovUniversal:
    """Mesma classe dos protótipos anteriores — 1 algoritmo, N níveis."""
    
    def __init__(self, nome=""):
        self.nome = nome
        self.transicoes = {}
        self.freq = Counter()
    
    def aprender(self, a, b):
        sa, sb = str(a), str(b)
        self.freq[sa] += 1
        if sa not in self.transicoes:
            self.transicoes[sa] = {}
        self.transicoes[sa][sb] = self.transicoes[sa].get(sb, 0) + 1
    
    def aprender_sequencia(self, seq):
        for i in range(len(seq)-1):
            self.aprender(seq[i], seq[i+1])
    
    def predizer(self, a):
        sa = str(a)
        if sa not in self.transicoes or not self.transicoes[sa]:
            return None, 0.0
        prox = self.transicoes[sa]
        melhor = max(prox, key=prox.get)
        total = sum(prox.values())
        return melhor, prox[melhor] / total
    
    def gerar_sequencia(self, semente: Any, passos: int = 10) -> List[Any]:
        """Gera uma sequência de tokens a partir de uma semente."""
        res = [semente]
        atual = semente
        for _ in range(passos):
            prox, conf = self.predizer(atual)
            if prox is None or conf < 0.05: break
            res.append(prox)
            atual = prox
        return res
    
    def entropia(self, a):
        sa = str(a)
        if sa not in self.transicoes: return 0.0
        prox = self.transicoes[sa]
        t = sum(prox.values())
        if t == 0: return 0.0
        h = 0.0
        for c in prox.values():
            p = c / t
            if p > 0: h -= p * math.log2(p)
        return h
    
    def stats(self):
        return {
            'nome': self.nome,
            'estados': len(self.transicoes),
            'transicoes': sum(len(v) for v in self.transicoes.values()),
            'entropia': round(sum(self.entropia(t) for t in self.transicoes) / max(len(self.transicoes),1), 3),
        }


# ============================================================
# MCR CONECTADO — aprende com DADOS REAIS do sandbox
# ============================================================
class MCRConectado:
    """MCR alimentado pelos DADOS REAIS do sandbox.
    
    Lê: .mcr_metricas.json, .mcr_episodios.json, .mcr_conversa.jsonl, .mcr_teste_*.json
    Aprende com o PASSADO para decidir o FUTURO.
    """
    
    def __init__(self):
        self.pe = PatternEngine()
        
        # Níveis de Markov (cada um aprende de uma fonte diferente)
        self.mk_metrica = MarkovUniversal("metrica")
        self.mk_episodio = MarkovUniversal("episodio")
        self.mk_conversa = MarkovUniversal("conversa")
        self.mk_teste = MarkovUniversal("teste")
        self.mk_byte = MarkovUniversal("byte")
        self.mk_palavra = MarkovUniversal("palavra")
        self.mk_token = MarkovUniversal("token")
        
        self.total_aprendizado = 0
        self.fontes = {}
    
    def aprender_com_metricas(self):
        """Aprende com .mcr_metricas.json — tempos e intenções."""
        path = os.path.join(SANDBOX, '.mcr_metricas.json')
        if not os.path.exists(path):
            print(f"  ⚠️ Métricas não encontradas")
            return 0
        
        with open(path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        ultimas = dados.get('ultimas', [])
        templates = dados.get('templates_usados', {})
        
        # Aprende: para CADA template, quantas vezes foi usado
        for template, count in templates.items():
            self.mk_metrica.aprender("USO", f"{template}({count}x)")
        
        # Aprende: transições de intenção → tempo
        for execucao in ultimas:
            intencao = execucao.get('intencao', '?')
            tempo = execucao.get('tempo', 0)
            sucesso = execucao.get('sucesso', True)
            tam = execucao.get('tam', 0)
            
            self.mk_metrica.aprender(f"INTENCAO_{intencao}", f"tempo_{tempo:.0f}s")
            self.mk_metrica.aprender(f"INTENCAO_{intencao}", "sucesso" if sucesso else "falha")
            self.mk_metrica.aprender(f"INTENCAO_{intencao}", f"tam_{tam}")
        
        n = len(ultimas)
        print(f"  ✅ .mcr_metricas.json: {n} execuções, {len(templates)} templates")
        self.total_aprendizado += n
        self.fontes['metricas'] = n
        return n
    
    def aprender_com_episodios(self):
        """Aprende com .mcr_episodios.json — sucessos e falhas."""
        path = os.path.join(SANDBOX, '.mcr_episodios.json')
        if not os.path.exists(path):
            print(f"  ⚠️ Episódios não encontrados")
            return 0
        
        with open(path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Pega os 100 primeiros (evita ler 100K+ itens)
        for ep in dados[:200]:
            request = ep.get('request', '')[:100]
            sucesso = ep.get('sucesso', True)
            licao = ep.get('licao', '')[:100]
            termos = ep.get('termos', [])
            
            # Aprende: termos que levam a sucesso/falha
            for termo in termos[:5]:
                if sucesso:
                    self.mk_episodio.aprender(f"TERMO_{termo}", "SUCESSO")
                else:
                    self.mk_episodio.aprender(f"TERMO_{termo}", "FALHA")
            
            # Aprende: padrão de request → resultado
            if len(request) > 10:
                self.mk_episodio.aprender(f"REQ_{request[:30]}", "OK" if sucesso else "ERRO")
        
        n = min(len(dados), 200)
        print(f"  ✅ .mcr_episodios.json: {n} episódios lidos")
        self.total_aprendizado += n
        self.fontes['episodios'] = n
        return n
    
    def aprender_com_conversas(self):
        """Aprende com .mcr_conversa.jsonl — perguntas e respostas."""
        path = os.path.join(SANDBOX, '.mcr_conversa.jsonl')
        if not os.path.exists(path):
            print(f"  ⚠️ Conversas não encontradas")
            return 0
        
        n = 0
        with open(path, 'r', encoding='utf-8') as f:
            for linha in f:
                try:
                    entry = json.loads(linha.strip())
                    msg = entry.get('msg', '')
                    if not msg or len(msg) < 20: continue
                    
                    # Tokeniza a mensagem e aprende transições de tokens
                    tokens = self.pe.tokenizar_universal(msg)
                    tipos = [t[0] for t in tokens] if tokens else []
                    if tipos:
                        self.mk_conversa.aprender_sequencia(tipos)
                        # Aprende também por byte
                        for i in range(len(msg.encode('utf-8')) - 1):
                            self.mk_byte.aprender(f"B{i}", f"B{i+1}")
                    
                    n += 1
                    if n >= 200: break  # limite para performance
                except: continue
        
        print(f"  ✅ .mcr_conversa.jsonl: {n} mensagens processadas")
        self.total_aprendizado += n
        self.fontes['conversas'] = n
        return n
    
    def aprender_com_testes(self):
        """Aprende com .mcr_teste_*.json — critérios e notas."""
        padroes = ['.mcr_teste_completo.json', '.mcr_teste_criacao.json', '.mcr_teste_complexo.json']
        n = 0
        
        for padrao in padroes:
            path = os.path.join(SANDBOX, padrao)
            if not os.path.exists(path): continue
            
            with open(path, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            if isinstance(dados, dict):
                # Extrai critérios que falharam
                criterios = dados.get('criterios', {})
                if isinstance(criterios, dict):
                    for nome, ok in criterios.items():
                        status = "PASS" if ok else "FAIL"
                        self.mk_teste.aprender(f"CRITERIO_{nome}", status)
            
            n += 1
        
        print(f"  ✅ .mcr_teste_*.json: {n} arquivos de teste")
        self.fontes['testes'] = n
        return n
    
    def aprender_tudo(self):
        """Aprende com TODAS as fontes disponíveis."""
        print(f"\n{'='*70}")
        print(f"  MCR APRENDENDO COM DADOS REAIS DO SANDBOX")
        print(f"{'='*70}")
        
        total = 0
        total += self.aprender_com_metricas()
        total += self.aprender_com_episodios()
        total += self.aprender_com_conversas()
        total += self.aprender_com_testes()
        
        print(f"\n  Total: {total} itens aprendidos de {len(self.fontes)} fontes")
        print(f"  Fontes: {self.fontes}")
        
        return total
    
    def diagnosticar(self, texto: str) -> Dict:
        """Usa TUDO que aprendeu para diagnosticar um texto."""
        tokens = self.pe.tokenizar_universal(texto) or []
        tipos = [t[0] for t in tokens]
        palavras = texto.lower().split()
        
        # Nível 1: Métricas — qual intenção?
        primeiro_tipo = tipos[0] if tipos else "?"
        acao, conf_metrica = self.mk_metrica.predizer(primeiro_tipo)
        
        # Nível 2: Episódios — quais termos de risco?
        riscos = []
        for palavra in palavras:
            for ep in self.mk_episodio.transicoes:
                if palavra in ep and "FALHA" in str(self.mk_episodio.transicoes[ep]):
                    riscos.append(palavra)
        
        # Nível 3: Token pattern similar
        padrao = self.mk_conversa.gerar_sequencia(tipos[0] if tipos else 'PAL_CURTA', 5) if tipos else []
        
        # Nível 4: bytes
        dados = texto.encode('utf-8')
        for i in range(len(dados)-1):
            self.mk_byte.aprender(f"B:{dados[i]:02x}", f"B:{dados[i+1]:02x}")
        
        return {
            'intencao': primeiro_tipo,
            'confianca_metrica': round(conf_metrica, 3),
            'riscos': riscos[:5],
            'transicao_esperada': [str(p) for p in padrao],
            'bytes_aprendidos': self.mk_byte.stats()['estados'],
        }


# ============================================================
# TESTE
# ============================================================
def testar():
    print("=" * 70)
    print("  MCR CONECTADO — Aprendendo com dados REAIS do sandbox")
    print("  Pela PRIMEIRA vez, MCR não é descartável.")
    print("=" * 70)
    
    mcr = MCRConectado()
    
    # FASE 1: Aprender com TUDO
    n_aprendido = mcr.aprender_tudo()
    
    # Mostra estatísticas de cada fonte
    print(f"\n{'='*70}")
    print(f"  ESTATÍSTICAS POR FONTE")
    print(f"{'='*70}")
    
    for mk in [mcr.mk_metrica, mcr.mk_episodio, mcr.mk_conversa,
                mcr.mk_teste, mcr.mk_byte, mcr.mk_palavra, mcr.mk_token]:
        s = mk.stats()
        if s['estados'] > 0:
            print(f"  {s['nome']:10s}: {s['estados']:5d} estados, {s['transicoes']:5d} transições, H={s['entropia']:.3f}")
    
    # FASE 2: Diagnosticar um texto usando TODO o conhecimento
    print(f"\n{'='*70}")
    print(f"  DIAGNÓSTICO DE TEXTO (com aprendizado real)")
    print(f"{'='*70}")
    
    textos = [
        "Crie um NPC ferreiro em Eridanus",
        "Explique o sistema SPA do MCR",
        "Busque a definição de SPA no código",
    ]
    
    for texto in textos:
        diag = mcr.diagnosticar(texto)
        print(f"\n  '{texto[:40]}'")
        print(f"    Intenção: {diag['intencao']} (conf_metrica={diag['confianca_metrica']})")
        print(f"    Riscos: {diag['riscos'][:3] or '(nenhum)'}")
        print(f"    Próximo token esperado: {diag['transicao_esperada'][:3]}")
        print(f"    Bytes aprendidos: {diag['bytes_aprendidos']}")
    
    # FASE 3: Relatório de conhecimento adquirido
    print(f"\n{'='*70}")
    print(f"  RELATÓRIO — CONHECIMENTO ADQUIRIDO")
    print(f"{'='*70}")
    print(f"  Total de itens aprendidos: {n_aprendido}")
    print(f"  Fontes consultadas: {list(mcr.fontes.keys())}")
    print(f"  Markovs treinados: {7}")
    print(f"  Status: {'✅ MCR conectado aos dados reais' if n_aprendido > 0 else '❌ Falha'}")
    print(f"  {'='*70}")
    
    return mcr


if __name__ == '__main__':
    mcr = testar()
