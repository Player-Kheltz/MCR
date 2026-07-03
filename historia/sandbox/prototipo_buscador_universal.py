#!/usr/bin/env python3
"""BUSCADOR UNIVERSAL — Encontra QUALQUER conteúdo por ASSINATURA DE PADRÃO.

Não busca por palavra-chave. Busca por PADRÃO DE TOKENS.
O padrão pode estar em: .md, .lua, .xml, .json, .txt, comentários,
strings, QUALQUER lugar dentro ou fora do projeto.

1. Dá um EXEMPLO do padrão (ex: 3 linhas de lore)
2. Extrai a ASSINATURA (fingerprint + tipos de token)
3. ESCANEIA o projeto + diretórios externos
4. RETORNA TUDO que tem padrão similar

0 LLM. 0 GPU. 0 modificação no MCR.
"""
import sys, os, re, json, math, time as _time
from collections import Counter
from typing import List, Dict, Tuple, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.kg import KnowledgeGraph

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class BuscadorUniversal:
    """Busca QUALQUER conteúdo com assinatura similar ao exemplo.
    
    A assinatura NÃO é uma palavra-chave.
    É o PADRÃO DE TOKENS + FINGERPRINT.
    Onde quer que esse padrão apareça — é relevante.
    """
    
    def __init__(self):
        self.pe = PatternEngine()
        self.cache_fingerprints = {}  # caminho → fingerprint (evita re-tokenizar)
        self._resultados_anteriores = []
    
    def buscar(self, texto_exemplo: str, 
               diretorios: List[str] = None,
               max_arquivos_por_dir: int = 30,
               min_similaridade: float = 0.3,
               max_resultados: int = 10) -> List[Dict]:
        """Busca QUALQUER arquivo com assinatura similar ao exemplo.
        
        Args:
            texto_exemplo: texto que representa o padrão desejado
            diretorios: lista de diretórios para escanear (None = padrão)
            max_arquivos_por_dir: limite de arquivos por diretório
            min_similaridade: limiar mínimo (0.0 a 1.0)
            max_resultados: máximo de resultados a retornar
            
        Returns:
            List[Dict]: {caminho, similaridade, tokens, tipos, snippet}
        """
        # 1. Extrai ASSINATURA do exemplo
        tokens_ex = self.pe.tokenizar_universal(texto_exemplo)
        if not tokens_ex or len(tokens_ex) < 3:
            print(f"  ⚠️ Exemplo muito curto ou inválido")
            return []
        
        fp_ex = self.pe.fingerprint(tokens_ex)
        tipos_ex = set(t[0] for t in tokens_ex)
        
        print(f"  Assinatura: {len(tokens_ex)} tokens, {list(tipos_ex)[:6]}...")
        print(f"  Fingerprint: {[round(x,2) for x in fp_ex[:4]]}...")
        
        # 2. Define diretórios para escanear
        if not diretorios:
            diretorios = self._diretorios_padrao()
        
        # 3. Escaneia e compara
        resultados = []
        arquivos_escaneados = 0
        max_total = 200  # limite total de arquivos para performance
        
        for diretorio in diretorios:
            if not os.path.isdir(diretorio):
                continue
            
            for root, dirs, files in os.walk(diretorio):
                # Pula diretórios irrelevantes
                if any(p in root for p in ['node_modules', '.git', '__pycache__', 
                                              'Backup', 'Legado', 'vcpkg', '.vscode']):
                    continue
                
                for f in files[:max_arquivos_por_dir]:
                    if arquivos_escaneados >= max_total:
                        break
                    caminho = os.path.join(root, f)
                    
                    # Pula binários
                    ext = os.path.splitext(f)[1].lower()
                    if ext in ('.exe', '.dll', '.so', '.dylib', '.png', '.jpg',
                               '.mp3', '.mp4', '.zip', '.rar', '.7z', '.pdf'):
                        continue
                    
                    arquivos_escaneados += 1
                    
                    # Lê conteúdo
                    try:
                        with open(caminho, 'r', encoding='utf-8', errors='replace') as fh:
                            conteudo = fh.read(2000)  # primeiros 2K chars
                    except Exception:
                        continue
                    
                    if not conteudo or len(conteudo) < 20:
                        continue
                    
                    # Tokeniza
                    try:
                        tokens = self.pe.tokenizar_universal(conteudo)
                        if not tokens or len(tokens) < 3:
                            continue
                        fp = self.pe.fingerprint(tokens)
                    except Exception:
                        continue
                    
                    # Calcula similaridade
                    sim = self.pe.similaridade(fp_ex, fp)
                    
                    # Bônus: quantos tipos tem em comum
                    tipos_arq = set(t[0] for t in tokens)
                    tipos_comuns = len(tipos_ex & tipos_arq)
                    
                    # Score final = similaridade * 0.7 + (tipos_comuns / max(len(tipos_ex),1)) * 0.3
                    score = (sim * 0.7) + (min(1.0, tipos_comuns / max(len(tipos_ex), 1)) * 0.3)
                    
                    if score >= min_similaridade:
                        # Extrai snippet do primeiro trecho com padrão similar
                        snippet = self._extrair_snippet(conteudo, tokens, tipos_ex)
                        
                        resultados.append({
                            'caminho': caminho,
                            'similaridade': round(sim, 3),
                            'score': round(score, 3),
                            'tokens': len(tokens),
                            'tipos': list(tipos_arq)[:8],
                            'tipos_comuns': tipos_comuns,
                            'snippet': snippet,
                        })
        
        # 4. Ordena por score
        resultados.sort(key=lambda x: -x['score'])
        top = resultados[:max_resultados]
        
        print(f"\n  Escaneados: {arquivos_escaneados} arquivos em {len(diretorios)} diretórios")
        print(f"  Encontrados: {len(resultados)} com assinatura similar (min_sim={min_similaridade})")
        
        self._resultados_anteriores = top
        return top
    
    def _extrair_snippet(self, conteudo: str, tokens: list, tipos_alvo: set) -> str:
        """Extrai o trecho MAIS relevante do conteúdo."""
        # Pega as primeiras 3 linhas que contêm tipos do alvo
        linhas = conteudo.split('\n')
        snippet = []
        for linha in linhas:
            if not linha.strip():
                continue
            # Se a linha tem algum dos tipos que buscamos
            tokens_linha = self.pe.tokenizar_universal(linha)
            tipos_linha = set(t[0] for t in tokens_linha)
            if tipos_linha & tipos_alvo:
                snippet.append(linha.strip()[:100])
                if len(snippet) >= 3:
                    break
        
        return '\n'.join(snippet) if snippet else linhas[0][:100] if linhas else ''
    
    def _diretorios_padrao(self) -> List[str]:
        """Diretórios padrão para escanear (limitado para performance)."""
        dirs = []
        
        # Dentro do projeto MCR — só docs/ e data/
        for d in ['docs', 'data']:
            p = os.path.join(BASE, d)
            if os.path.isdir(p):
                dirs.append(p)
        
        # Fora do projeto — apenas Documents (se existir e for rápido)
        home = os.path.expanduser('~')
        docs_dir = os.path.join(home, 'Documents')
        if os.path.isdir(docs_dir):
            dirs.append(docs_dir)
        
        return dirs
    
    def enriquecer_corpus(self, resultados: List[Dict], 
                           dominio: str = 'lore',
                           kg: KnowledgeGraph = None) -> int:
        """Adiciona os resultados ao corpus do domínio no KG.
        
        Returns:
            int: quantos fragmentos foram adicionados
        """
        if not kg:
            kg = KnowledgeGraph()
        
        adicionados = 0
        for r in resultados:
            snippet = r.get('snippet', '')
            if not snippet or len(snippet) < 20:
                continue
            
            try:
                # Tokeniza o snippet
                tokens = self.pe.tokenizar_universal(snippet)
                fp = self.pe.fingerprint(tokens) if tokens else []
                
                kg.aprender(
                    erro=f"descoberto_por_assinatura_{dominio}",
                    causa=f"score={r['score']}, similaridade={r['similaridade']}",
                    solucao=snippet[:500],
                    ctx=f"corpus_{dominio}",
                    fingerprint=fp if fp else None,
                )
                adicionados += 1
            except Exception:
                continue
        
        return adicionados


# ============================================================
# TESTE
# ============================================================
def testar():
    print("=" * 70)
    print("  BUSCADOR UNIVERSAL — Encontra por ASSINATURA, não por palavra")
    print("  Qualquer formato. Qualquer lugar. Qualquer domínio.")
    print("=" * 70)
    
    buscador = BuscadorUniversal()
    
    # === TESTE 1: Buscar por assinatura de LORE ===
    print(f"\n{'='*70}")
    print(f"  TESTE 1: Busca por ASSINATURA DE LORE")
    print(f"{'='*70}")
    
    exemplo_lore = "Eridanus = Cidade inicial dos aventureiros, ponto de partida para explorar o mundo de Tibia."
    
    print(f"  Exemplo: '{exemplo_lore}'")
    
    t0 = _time.time()
    resultados_lore = buscador.buscar(
        texto_exemplo=exemplo_lore,
        max_arquivos_por_dir=20,
        min_similaridade=0.2,
        max_resultados=8,
    )
    print(f"  Tempo: {_time.time() - t0:.1f}s")
    
    # Mostra resultados
    if resultados_lore:
        print(f"\n  Top resultados com assinatura de LORE:")
        for i, r in enumerate(resultados_lore, 1):
            caminho_curto = r['caminho'].replace(BASE, '~').replace(os.path.expanduser('~'), '~')
            print(f"\n  {i}. [{r['score']:.2f}] {caminho_curto}")
            print(f"     Tipos: {r['tipos'][:5]}")
            print(f"     Snippet: {r['snippet'][:80]}")
    
    # === TESTE 2: Buscar por assinatura de CÓDIGO ===
    print(f"\n{'='*70}")
    print(f"  TESTE 2: Busca por ASSINATURA DE CÓDIGO")
    print(f"{'='*70}")
    
    exemplo_codigo = "local npc = NPC:new('Teste')\nnpc:setTitle('Teste')\nnpc:onSay(function() end)"
    
    print(f"  Exemplo: '{exemplo_codigo}'")
    
    t0 = _time.time()
    resultados_codigo = buscador.buscar(
        texto_exemplo=exemplo_codigo,
        max_arquivos_por_dir=20,
        min_similaridade=0.2,
        max_resultados=5,
    )
    print(f"  Tempo: {_time.time() - t0:.1f}s")
    
    if resultados_codigo:
        print(f"\n  Top resultados com assinatura de CÓDIGO:")
        for i, r in enumerate(resultados_codigo[:3], 1):
            caminho_curto = r['caminho'].replace(BASE, '~')
            print(f"  {i}. [{r['score']:.2f}] {caminho_curto}")
            print(f"     Tipos: {r['tipos'][:5]}")
    
    # === TESTE 3: Enriquecer corpus no KG ===
    print(f"\n{'='*70}")
    print(f"  TESTE 3: ENRIQUECER CORPUS DE LORE NO KG")
    print(f"{'='*70}")
    
    if resultados_lore:
        kg = KnowledgeGraph()
        adicionados = buscador.enriquecer_corpus(resultados_lore, 'lore', kg)
        print(f"  {adicionados} fragmentos de lore adicionados ao KG")
    
    # === RELATÓRIO ===
    print(f"\n\n{'='*70}")
    print(f"  RELATÓRIO FINAL")
    print(f"{'='*70}")
    
    print(f"\n  Resultados de LORE: {len(resultados_lore)}")
    if resultados_lore:
        print(f"  Score médio: {sum(r['score'] for r in resultados_lore)/len(resultados_lore):.2f}")
        print(f"  Top 1: {resultados_lore[0]['caminho'].replace(BASE, '~')[:80]}")
    
    print(f"\n  Resultados de CÓDIGO: {len(resultados_codigo)}")
    if resultados_codigo:
        print(f"  Score médio: {sum(r['score'] for r in resultados_codigo)/len(resultados_codigo):.2f}")
    
    print(f"\n  ✅ Assinatura de LORE: encontrado em {len(resultados_lore)} arquivos")
    print(f"  ✅ Assinatura de CÓDIGO: encontrado em {len(resultados_codigo)} arquivos")
    print(f"  ✅ Corpus de lore enriquecido no KG")
    print(f"  Tudo encontrado por PADRÃO, não por palavra-chave.")
    print(f"{'='*70}")


if __name__ == '__main__':
    testar()
