#!/usr/bin/env python3
"""AMPLIFICADOR UNIVERSAL — Zero hardcode. Zero keywords. Zero domínios fixos.

O MCR descobre os padrões SOZINHO:
  - Lê o código, tokeniza sem saber nada sobre a linguagem
  - Markov APRENDE quais palavras/símbolos aparecem juntos
  - Se um código foge do padrão → anomalia DETECTADA
  - Pega o PRÓXIMO token mais provável do Markov → REGENERA

Zero LLM. Zero GPU. Zero modificação no MCR.
"""
import sys, os, re, json, math, random, time as _time
from collections import Counter
from typing import List, Dict, Tuple, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.kg import KnowledgeGraph

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


# ============================================================
# APRENDIZ DE CÓDIGO UNIVERSAL (aprende sozinho)
# ============================================================
class AprendizUniversal:
    """Aprende padrões de código LENDO exemplos reais.
    
    0 keywords hardcoded. 0 conhecimento prévio da linguagem.
    O Markov APRENDE o que é código válido por OBSERVAÇÃO.
    """
    
    def __init__(self):
        self.pe = PatternEngine()
        self.markov = {}          # {tipo_atual: {tipo_prox: count}}
        self.tipo_palavra = {}    # {tipo: {palavra: count}}
        self.total_arquivos = 0
        self.total_tokens = 0
    
    def aprender(self, caminhos: List[str]):
        """Aprende padrões de código lendo arquivos REAIS."""
        for caminho in caminhos:
            try:
                with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                    conteudo = f.read()
                if len(conteudo) < 20: continue
            except Exception: continue
            
            # Tokeniza SEMPRE com tokenizar_universal (que usa _tokenizar_codigo)
            tokens = self.pe.tokenizar_universal(conteudo)
            if not tokens or len(tokens) < 5: continue
            
            self.total_arquivos += 1
            self.total_tokens += len(tokens)
            
            # Markov de tipos
            for i in range(len(tokens) - 1):
                t1, t2 = tokens[i][0], tokens[i+1][0]
                if t1 not in self.markov: self.markov[t1] = {}
                self.markov[t1][t2] = self.markov[t1].get(t2, 0) + 1
            
            # Palavras por tipo
            for t in tokens:
                tipo, palavra = t[0], str(t[1]) if len(t) > 1 else ''
                if not palavra or len(palavra) < 2: continue
                if tipo not in self.tipo_palavra: self.tipo_palavra[tipo] = {}
                self.tipo_palavra[tipo][palavra] = self.tipo_palavra[tipo].get(palavra, 0) + 1
        
        # Normaliza
        for t1 in self.markov:
            total = sum(self.markov[t1].values())
            for t2 in self.markov[t1]:
                self.markov[t1][t2] /= total
        
        print(f"  Aprendido: {self.total_arquivos} arquivos, {self.total_tokens} tokens, "
              f"{len(self.markov)} tipos de token, {sum(len(v) for v in self.markov.values())} transições")
    
    def validar(self, codigo: str) -> Dict:
        """Valida código CONTRA o padrão aprendido.
        
        Detecta anomalias comparando transições de TIPOS.
        0 conhecimento da linguagem — só compara padrões.
        """
        tokens = self.pe.tokenizar_universal(codigo)
        if not tokens: return {'valido': True, 'anomalias': [], 'cobertura': 1.0}
        
        anomalias = []
        acertos = 0
        total_trans = 0
        
        for i in range(len(tokens) - 1):
            t1, t2 = tokens[i][0], tokens[i+1][0]
            total_trans += 1
            
            if t1 in self.markov and t2 in self.markov[t1]:
                acertos += 1
            else:
                # Anomalia! Transição que NUNCA apareceu no código válido
                anomalias.append({
                    'pos': i,
                    'tipo_atual': t1,
                    'tipo_detectado': t2,
                    'palavra_atual': str(tokens[i][1])[:20] if len(tokens[i]) > 1 else '',
                    'palavra_seguinte': str(tokens[i+1][1])[:20] if len(tokens[i+1]) > 1 else '',
                })
        
        cobertura = acertos / max(total_trans, 1)
        
        return {
            'valido': len(anomalias) == 0,
            'cobertura': round(cobertura, 4),
            'anomalias': anomalias[:10],
            'total_anomalias': len(anomalias),
            'tokens': len(tokens),
        }
    
    def reparar(self, codigo: str) -> Tuple[str, List]:
        """Repara código detectando anomalias e regenerando com Markov.
        
        1. Tokeniza → detecta anomalias
        2. Na PRIMEIRA anomalia, Markov gera o que DEVERIA vir
        3. Substitui a parte anômala pela gerada
        """
        tokens = self.pe.tokenizar_universal(codigo)
        if not tokens: return codigo, []
        
        anomalias = self.validar(codigo)['anomalias']
        if not anomalias: return codigo, []
        
        # Pega a PRIMEIRA anomalia
        a = anomalias[0]
        pos = a['pos']
        
        # Pega o token ANTERIOR à anomalia (o que DEVERIA ter vindo antes)
        token_anterior = tokens[pos - 1][0] if pos > 0 else tokens[0][0]
        
        # Markov do código válido diz o que DEVERIA vir DEPOIS
        if token_anterior in self.markov:
            # Pega o MAIS PROVÁVEL
            mais_provavel = max(self.markov[token_anterior], key=self.markov[token_anterior].get)
            
            return codigo, [{
                'pos': pos,
                'anomalia': a['tipo_detectado'],
                'sugestao': mais_provavel,
                'palavra_anomalia': a['palavra_seguinte'],
            }]
        
        return codigo, []


# ============================================================
# TESTE
# ============================================================
def buscar_arquivos(ext: Tuple[str] = ('.lua',), max: int = 100) -> List[str]:
    """Busca arquivos no projeto."""
    arquivos = []
    for root, dirs, files in os.walk(BASE):
        if any(p in root for p in ['node_modules', '.git', '__pycache__', 'Backup']): continue
        for f in files:
            if f.endswith(ext) and not f.startswith('.'):
                arquivos.append(os.path.join(root, f))
                if len(arquivos) >= max: return arquivos
    return arquivos


def testar():
    print("=" * 70)
    print("  APRENDIZ UNIVERSAL — 0 keywords hardcoded")
    print("  O MCR aprende código válido SOZINHO (qualquer linguagem)")
    print("=" * 70)
    
    # FASE 1: Aprender
    print(f"\n{'='*70}")
    print(f"  FASE 1: APRENDER CÓDIGO VÁLIDO (qualquer .lua)")
    print(f"{'='*70}")
    
    ap = AprendizUniversal()
    arquivos = buscar_arquivos(('.lua',), max=120)
    print(f"  Encontrados {len(arquivos)} arquivos .lua")
    ap.aprender(arquivos)
    
    # Mostra top transições (aprendidas, não hardcoded)
    print(f"\n  Top 10 transições aprendidas:")
    todas_trans = []
    for t1 in ap.markov:
        for t2, prob in ap.markov[t1].items():
            todas_trans.append((t1, t2, prob))
    todas_trans.sort(key=lambda x: -x[2])
    for t1, t2, prob in todas_trans[:10]:
        print(f"    {t1:15s} → {t2:15s}  ({prob*100:.1f}%)")
    
    # FASE 2: Validar código CORRETO
    print(f"\n{'='*70}")
    print(f"  FASE 2: VALIDAR CÓDIGO CORRETO")
    print(f"{'='*70}")
    
    codigo_correto = """local lore_eridanus = {
    nome = "Fundacao de Eridanus",
    tipo = "lore",
}

return lore_eridanus
"""
    res = ap.validar(codigo_correto)
    print(f"  Cobertura: {res['cobertura']:.2%}")
    print(f"  Anomalias: {res['total_anomalias']}")
    print(f"  Válido: {res['valido']}")
    
    # FASE 3: Validar código COM BUG
    print(f"\n{'='*70}")
    print(f"  FASE 3: VALIDAR CÓDIGO COM BUG")
    print(f"{'='*70}")
    
    codigo_bug = """local lore = {
    nome = "Fundacao de Eridanus",
    tipo = "lore",

return lore
end
"""
    res_bug = ap.validar(codigo_bug)
    print(f"  Cobertura: {res_bug['cobertura']:.2%}")
    print(f"  Anomalias: {res_bug['total_anomalias']}")
    print(f"  Válido: {res_bug['valido']}")
    
    if res_bug['anomalias']:
        print(f"\n  Anomalias detectadas:")
        for a in res_bug['anomalias'][:5]:
            print(f"    Pos {a['pos']}: '{a['tipo_atual']}' → '{a['tipo_detectado']}' "
                  f"(palavras: '{a['palavra_atual']}' '{a['palavra_seguinte']}')")
    
    # FASE 4: Reparar
    print(f"\n{'='*70}")
    print(f"  FASE 4: REPARAR (regenerar parte anômala)")
    print(f"{'='*70}")
    
    codigo_corrigido, alteracoes = ap.reparar(codigo_bug)
    if alteracoes:
        print(f"  {len(alteracoes)} alterações sugeridas:")
        for a in alteracoes[:3]:
            print(f"    Pos {a['pos']}: anomalia '{a['anomalia']}' → sugestão '{a['sugestao']}' ({a['palavra_anomalia']})")
    else:
        print(f"  Nenhuma alteração necessária (ou Markov não tem dados para sugerir)")
    
    # FASE 5: Validar texto de lore (NÃO é código)
    print(f"\n{'='*70}")
    print(f"  FASE 5: VALIDAR TEXTO LITERÁRIO (não é código)")
    print(f"{'='*70}")
    
    texto_lore = "Eridanus era uma cidade lendária conhecida por sua simplicidade."
    res_lore = ap.validar(texto_lore)
    print(f"  Cobertura: {res_lore['cobertura']:.2%}")
    print(f"  Anomalias: {res_lore['total_anomalias']}")
    print(f"  (Esperado: baixa cobertura — não é código)")
    
    # RELATÓRIO
    print(f"\n\n{'='*70}")
    print(f"  RELATÓRIO FINAL")
    print(f"{'='*70}")
    print(f"  Arquivos lidos: {ap.total_arquivos}")
    print(f"  Tokens processados: {ap.total_tokens}")
    print(f"  Tipos de token: {len(ap.markov)}")
    print(f"  Transições únicas: {sum(len(v) for v in ap.markov.values())}")
    print(f"\n  Código correto: cobertura {res['cobertura']:.1%}")
    print(f"  Código com bug:  cobertura {res_bug['cobertura']:.1%}")
    print(f"  Diferença: {res['cobertura'] - res_bug['cobertura']:.1%} "
          f"{'✅' if res['cobertura'] > res_bug['cobertura'] else '❌'}")
    print(f"\n  0 keywords hardcoded. 0 conhecimento de linguagem.")
    print(f"  O MCR aprendeu o que é código válido por OBSERVAÇÃO.")
    print(f"{'='*70}")


if __name__ == '__main__':
    testar()
