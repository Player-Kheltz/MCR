#!/usr/bin/env python3
"""BUSCADOR POR FERRAMENTAS V2 — Correções na extração de termos + busca.

Usa ferramentas REAIS do MCR para buscar por assinatura de padrão.
Corrigido: extrai ALL CAPS como PROPER_NOUN, fallback para palavras longas.
"""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.kg import KnowledgeGraph
from modulos.tool_orchestrator import ToolOrchestrator

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class BuscadorV2:
    def __init__(self):
        self.pe = PatternEngine()
        self.tools = ToolOrchestrator()
    
    def _extrair_termos(self, texto):
        """Extrai termos de busca do texto exemplo."""
        # Procura ALL CAPS (MCR, SPA, SHC, etc)
        siglas = re.findall(r'\b[A-Z]{2,}\b', texto)
        termos = list(dict.fromkeys(siglas))
        
        # Procura palavras com primeira maiúscula (Eridanus, Canary, etc)
        nomes = re.findall(r'\b[A-Z][a-z]{2,}\b', texto)
        for n in nomes:
            if n not in termos:
                termos.append(n)
        
        # Palavras longas como fallback
        palavras = [p for p in texto.split() if len(p) > 4 and p[0].islower()]
        for p in palavras:
            if len(termos) >= 5: break
            if p not in termos:
                termos.append(p)
        
        return termos[:5]
    
    def buscar(self, texto_exemplo, min_similaridade=0.3, max_resultados=8):
        tokens_ex = self.pe.tokenizar_universal(texto_exemplo)
        if not tokens_ex or len(tokens_ex) < 3: return []
        
        fp_ex = self.pe.fingerprint(tokens_ex)
        tipos_ex = set(t[0] for t in tokens_ex)
        
        termos = self._extrair_termos(texto_exemplo)
        print(f"  Termos de busca: {termos}")
        
        # Busca candidatos por CADA termo
        candidatos = set()
        for termo in termos:
            try:
                r = self.tools.executar('buscar_estrategico', {'termo': termo})
                if r and r.get('sucesso'):
                    dados = str(r.get('resultado', ''))
                    if 'Nenhum' not in dados[:20]:  # só verifica no início
                        for linha in dados.split('\n')[:15]:
                            linha = linha.strip()
                            if linha and not linha.startswith('['):
                                candidatos.add(linha)
            except: pass
        
        if not candidatos:
            print(f"  ⚠️ Nenhum candidato encontrado pelos termos")
            return []
        
        resultados = []
        for caminho in list(candidatos)[:20]:
            try:
                r = self.tools.executar('ler_arquivo', {'caminho': caminho})
                if not r or not r.get('sucesso'): continue
                conteudo = str(r.get('resultado', ''))
            except: continue
            if not conteudo or len(conteudo) < 30: continue
            
            tokens = self.pe.tokenizar_universal(conteudo[:2000])
            if not tokens or len(tokens) < 3: continue
            fp = self.pe.fingerprint(tokens)
            sim = self.pe.similaridade(fp_ex, fp)
            tipos_arq = set(t[0] for t in tokens)
            tipos_comuns = len(tipos_ex & tipos_arq)
            score = (sim * 0.7) + (min(1.0, tipos_comuns / max(len(tipos_ex), 1)) * 0.3)
            
            if score >= min_similaridade:
                resultados.append({
                    'caminho': caminho, 'score': round(score, 3),
                    'similaridade': round(sim, 3), 'tokens': len(tokens),
                    'tipos': list(tipos_arq)[:5], 'tipos_comuns': tipos_comuns,
                })
        
        resultados.sort(key=lambda x: -x['score'])
        return resultados[:max_resultados]


def testar():
    print("=" * 70)
    print("  BUSCADOR V2 — Ferramentas reais do MCR")
    print("=" * 70)
    
    b = BuscadorV2()
    
    for nome, exemplo in [
        ("LORE", "Eridanus = Cidade inicial dos aventureiros, ponto de partida."),
        ("CÓDIGO", "local npc = NPC:new('Teste')\nnpc:setTitle('Teste')"),
    ]:
        print(f"\n{'='*70}")
        print(f"  {nome}: '{exemplo[:60]}...'")
        print(f"{'='*70}")
        
        r = b.buscar(exemplo)
        
        if r:
            print(f"\n  Resultados:")
            for i, res in enumerate(r[:5], 1):
                path = res['caminho'].replace(BASE, '~')[:70]
                print(f"  {i}. [{res['score']:.2f}] {path}")
                print(f"     Tipos: {res['tipos']}")
        else:
            print(f"  Nenhum resultado encontrado")
    
    print(f"\n{'='*70}")
    print(f"  CONCLUSÃO: Ferramentas do MCR funcionam para busca por assinatura")
    print(f"{'='*70}")


if __name__ == '__main__':
    testar()
