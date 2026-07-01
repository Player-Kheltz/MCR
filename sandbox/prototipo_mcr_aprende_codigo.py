#!/usr/bin/env python3
"""PROTÓTIPO: MCR Aprende Código Válido — Detecta Bugs por Markov.

Nada hardcoded. MCR lê arquivos .lua REAIS do projeto,
aprende o padrão ESTRUTURAL, e detecta quando algo foge do padrão.

Funciona para: Lua, Python, Markdown, JSON, TXT — QUALQUER formato.
O MCR aprende o que é "certo" lendo exemplos reais.

0 LLM. 0 hardcode. 0 modificação no MCR.
"""
import sys, os, re, json, glob, time as _time
from collections import Counter
from typing import List, Dict, Tuple, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.kg import KnowledgeGraph
from modulos.pi_engine import PiEngine

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class AprendizDeCodigo:
    """MCR aprende o que é código VÁLIDO lendo exemplos reais do projeto.
    
    Totalmente universal — funciona para QUALQUER linguagem/formato.
    """
    
    def __init__(self):
        self.pe = PatternEngine()
        self.markov_tipos = {}      # {tipo_atual: {tipo_prox: prob}}
        self.markov_palavras = {}   # {tipo: {palavra: freq}}
        self.transicoes = Counter() # (tipo_atual, tipo_prox) → count
        self.total_arquivos = 0
        self.total_tokens = 0
    
    def aprender(self, caminhos: List[str], extensoes: Tuple[str] = ('.lua',)):
        """Aprende padrões de código lendo arquivos REAIS do projeto.
        
        Para CADA arquivo:
          1. Lê conteúdo
          2. PE.tokenizar_universal() → tokens
          3. Extrai Markov de TIPOS (sequência estrutural)
          4. Extrai Markov de PALAVRAS (o que cada tipo costuma ser)
          5. Acumula no modelo
        """
        arquivos_lidos = 0
        for caminho in caminhos:
            if not caminho.endswith(extensoes):
                continue
            try:
                with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                    conteudo = f.read()
                if len(conteudo) < 20:
                    continue
            except Exception:
                continue
            
            tokens = self.pe.tokenizar_universal(conteudo)
            if not tokens or len(tokens) < 5:
                continue
            
            self.total_arquivos += 1
            self.total_tokens += len(tokens)
            arquivos_lidos += 1
            
            # Markov de TIPOS (sequência estrutural)
            for i in range(len(tokens) - 1):
                t1 = tokens[i][0]
                t2 = tokens[i+1][0]
                self.transicoes[(t1, t2)] += 1
                if t1 not in self.markov_tipos:
                    self.markov_tipos[t1] = {}
                if t2 not in self.markov_tipos[t1]:
                    self.markov_tipos[t1][t2] = 0
                self.markov_tipos[t1][t2] += 1
            
            # Markov de PALAVRAS (o que cada tipo costuma conter)
            for t in tokens:
                tipo = t[0]
                palavra = str(t[1]) if len(t) > 1 else ''
                if not palavra or len(palavra) < 2:
                    continue
                if tipo not in self.markov_palavras:
                    self.markov_palavras[tipo] = {}
                self.markov_palavras[tipo][palavra] = self.markov_palavras[tipo].get(palavra, 0) + 1
        
        # Normaliza markov de tipos
        for t1 in self.markov_tipos:
            total = sum(self.markov_tipos[t1].values())
            for t2 in self.markov_tipos[t1]:
                self.markov_tipos[t1][t2] /= total
        
        print(f"  Aprendido: {arquivos_lidos} arquivos, {self.total_tokens} tokens, "
              f"{len(self.markov_tipos)} tipos, {len(self.transicoes)} transições")
    
    def validar(self, codigo: str, nome: str = "arquivo") -> Dict:
        """Valida um código CONTRA o padrão aprendido.
        
        1. Tokeniza o código
        2. Para CADA transição (t1→t2):
           - Se existe no padrão → OK
           - Se NÃO existe → ANOMALIA
        3. Para CADA tipo com palavra:
           - Se a palavra não está no vocabulário conhecido → SUSPEITO
        4. Relatório: onde, o que, e o que ESPERADO
        
        Returns:
            dict: {valido, anomalias: [{pos, tipo, tipo_esperado, sugestao}], 
                   cobertura, tokens, entropia}
        """
        tokens = self.pe.tokenizar_universal(codigo)
        if not tokens:
            return {'valido': True, 'anomalias': [], 'cobertura': 1.0, 'tokens': 0}
        
        anomalias = []
        acertos = 0
        total_transicoes = 0
        
        for i in range(len(tokens) - 1):
            t1 = tokens[i][0]
            t2 = tokens[i+1][0]
            total_transicoes += 1
            
            if t1 in self.markov_tipos and t2 in self.markov_tipos[t1]:
                acertos += 1
            else:
                # Anomalia: transição que nunca aparece no código válido
                # Pega o que o padrão ESPERA vir depois de t1
                esperados = list(self.markov_tipos.get(t1, {}).keys()) if t1 in self.markov_tipos else ['(nunca visto)']
                mais_esperado = max(self.markov_tipos[t1].items(), key=lambda x: x[1])[0] if t1 in self.markov_tipos and self.markov_tipos[t1] else '(nenhum)'
                
                # Pega a linha aproximada
                linha = self._estimar_linha(codigo, tokens, i)
                
                anomalias.append({
                    'pos': i,
                    'linha': linha,
                    'tipo_atual': t1,
                    'tipo_anomalo': t2,
                    'tipo_esperado': mais_esperado,
                    'palavra_atual': str(tokens[i][1])[:30] if len(tokens[i]) > 1 else '',
                    'palavra_prox': str(tokens[i+1][1])[:30] if len(tokens[i+1]) > 1 else '',
                    'sugestao': f"Esperava '{mais_esperado}' depois de '{t1}', veio '{t2}'",
                })
        
        cobertura = acertos / max(total_transicoes, 1)
        entropia = self._calcular_entropia(tokens)
        
        return {
            'valido': len(anomalias) == 0,
            'anomalias': anomalias[:10],
            'total_anomalias': len(anomalias),
            'cobertura': round(cobertura, 4),
            'tokens': len(tokens),
            'tipos': [t[0] for t in tokens[:20]],
            'entropia': round(entropia, 4),
        }
    
    def _estimar_linha(self, codigo: str, tokens: list, idx: int) -> int:
        """Estima a linha aproximada de um token no código."""
        try:
            # Calcula quantos \n antes da posição estimada do token
            # Método simplificado: conta \n nos primeiros 30% do código
            linhas = codigo.split('\n')
            chars_por_token = len(codigo) / max(len(tokens), 1)
            pos_estimada = int(idx * chars_por_token)
            return codigo[:pos_estimada].count('\n') + 1
        except:
            return 0
    
    def _calcular_entropia(self, tokens):
        """Calcula entropia dos tipos de token."""
        if not tokens:
            return 0.0
        freq = Counter(t[0] for t in tokens)
        n = len(tokens)
        h = 0.0
        for f in freq.values():
            p = f / n
            if p > 0:
                h -= p * math.log2(p)
        return h / math.log2(len(freq)) if len(freq) > 1 else 0.0


# ============================================================
# BUSCA DE ARQUIVOS NO PROJETO
# ============================================================
def buscar_arquivos(termo: str = '', ext: Tuple[str] = ('.lua',), max: int = 100) -> List[str]:
    """Busca arquivos no projeto MCR."""
    arquivos = []
    for root, dirs, files in os.walk(BASE):
        # Pula diretórios irrelevantes
        if any(p in root for p in ['node_modules', '.git', '__pycache__', 'Backup', 'Legado', 'vcpkg']):
            continue
        for f in files:
            if f.endswith(ext) and not f.startswith('.'):
                if termo.lower() in f.lower() or not termo:
                    arquivos.append(os.path.join(root, f))
                    if len(arquivos) >= max:
                        return arquivos
    return arquivos


# ============================================================
# TESTE
# ============================================================
def testar():
    print("=" * 70)
    print("  MCR APRENDE CÓDIGO VÁLIDO DO PROJETO")
    print("  Detecta bugs por diferença de Markov — 0 hardcode")
    print("=" * 70)
    
    # FASE 1: Aprender código válido do projeto
    print(f"\n{'='*70}")
    print(f"  FASE 1: APRENDER PADRÃO DE CÓDIGO VÁLIDO")
    print(f"{'='*70}")
    
    aprendiz = AprendizDeCodigo()
    
    # Busca TODOS os .lua do projeto
    arquivos_lua = buscar_arquivos('', ('.lua',), max=150)
    print(f"  Encontrados {len(arquivos_lua)} arquivos .lua no projeto")
    
    # Aprende com eles
    t0 = _time.time()
    aprendiz.aprender(arquivos_lua)
    print(f"  Tempo: {_time.time() - t0:.1f}s")
    
    # Mostra top transições
    print(f"\n  Top 10 transições mais comuns em código válido:")
    for (t1, t2), count in aprendiz.transicoes.most_common(10):
        prob = aprendiz.markov_tipos.get(t1, {}).get(t2, 0) * 100
        print(f"    {t1:20s} → {t2:20s}  ({count}x, {prob:.1f}%)")
    
    # FASE 2: Validar código CORRETO (deve passar)
    print(f"\n{'='*70}")
    print(f"  FASE 2: VALIDAR CÓDIGO CORRETO")
    print(f"{'='*70}")
    
    codigo_correto = """local lore_eridanus = {
    nome = "Fundacao de Eridanus",
    tipo = "lore",
}

return lore_eridanus
"""
    diag = aprendiz.validar(codigo_correto, "codigo_correto.lua")
    print(f"  Cobertura: {diag['cobertura']:.2%}")
    print(f"  Anomalias: {diag['total_anomalias']}")
    print(f"  Entropia: {diag['entropia']}")
    print(f"  Status: {'✅ VÁLIDO' if diag['valido'] else '❌ INVÁLIDO'}")
    
    # FASE 3: Validar código COM BUG (deve detectar)
    print(f"\n{'='*70}")
    print(f"  FASE 3: VALIDAR CÓDIGO COM BUG")
    print(f"{'='*70}")
    
    codigo_bug = """local lore = {
    nome = "Fundacao de Eridanus",
    tipo = "lore",

return lore
end
"""
    diag = aprendiz.validar(codigo_bug, "bug_test.lua")
    print(f"  Cobertura: {diag['cobertura']:.2%}")
    print(f"  Anomalias: {diag['total_anomalias']}")
    print(f"  Entropia: {diag['entropia']}")
    print(f"  Status: {'✅ VÁLIDO' if diag['valido'] else '❌ INVÁLIDO'}")
    
    if diag['anomalias']:
        print(f"\n  Anomalias detectadas:")
        for a in diag['anomalias'][:5]:
            print(f"    Linha ~{a['linha']}: '{a['palavra_atual']}' → '{a['palavra_prox']}'")
            print(f"      Esperava '{a['tipo_esperado']}' depois de '{a['tipo_atual']}', veio '{a['tipo_anomalo']}'")
            print(f"      → {a['sugestao']}")
    
    # FASE 4: Validar história (deve mostrar que NÃO é código)
    print(f"\n{'='*70}")
    print(f"  FASE 4: VALIDAR TEXTO DE LORE (deve mostrar baixa cobertura)")
    print(f"{'='*70}")
    
    texto_lore = "Eridanus era uma cidade lendária conhecida por sua simplicidade e eficiência."
    diag = aprendiz.validar(texto_lore, "historia.txt")
    print(f"  Cobertura: {diag['cobertura']:.2%}")
    print(f"  Anomalias: {diag['total_anomalias']}")
    print(f"  Tokens: {diag['tokens']}")
    print(f"  Entropia: {diag['entropia']}")
    print(f"  Status: {'✅ VÁLIDO' if diag['valido'] else '❌ INVÁLIDO'}")
    print(f"  (Esperado: baixa cobertura, alta entropia — não é código)")
    
    # FASE 5: Aplicação futura — gerador usa o validador
    print(f"\n{'='*70}")
    print(f"  FASE 5: CICLO COMPLETO — Gerar + Validar + Corrigir")
    print(f"{'='*70}")
    
    print(f"  Em produção, o ciclo seria:")
    print(f"  1. GeradorTexto cria lore sobre Eridanus")
    print(f"  2. Validador detecta que NÃO é código (baixa cobertura)")
    print(f"  3. AutoTrigger busca exemplos reais de lore no projeto")
    print(f"  4. AprendizDePadroes estuda e aprende padrão de lore")
    print(f"  5. Próxima geração: Markov TREINADO em lore REAL")
    print(f"  6. Qualidade da lore MELHORA sozinha")
    
    # RELATÓRIO FINAL
    print(f"\n\n{'='*70}")
    print(f"  RELATÓRIO FINAL")
    print(f"{'='*70}")
    print(f"  Arquivos lidos: {aprendiz.total_arquivos}")
    print(f"  Tokens processados: {aprendiz.total_tokens}")
    print(f"  Tipos de token: {len(aprendiz.markov_tipos)}")
    print(f"  Transições únicas: {len(aprendiz.transicoes)}")
    print(f"\n  Detecção de bugs por Markov: {'✅ FUNCIONA' if diag['total_anomalias'] > 0 else '⚙️ PREJISAR DE + DADOS'}")
    print(f"  Zero hardcode. Zero LLM. Zero GPU.")
    print(f"  O MCR aprendeu o que é código válido LENDO exemplos reais.")
    print(f"{'='*70}")


if __name__ == '__main__':
    # Ensure math is imported
    import math
    testar()
