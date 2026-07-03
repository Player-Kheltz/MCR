#!/usr/bin/env python3
"""PROTÓTIPO: Auto-Aprendizado por Insucesso de Reconstrução.

Quando reconstrução falha (KG sem fingerprint similar), o sistema:
1. Extrai termos-chave da pergunta
2. Busca em múltiplas fontes (local + KG + web)
3. Tokeniza resultados, extrai padrões
4. Salva no KG com o fingerprint da PERGUNTA ORIGINAL
5. Tenta reconstruir de NOVO

NÃO MODIFICA NADA NO MCR.
"""
import sys, os, json, time as _time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.kg import KnowledgeGraph
from modulos.intention_engine import IntentionEngine
from modulos.tool_orchestrator import ToolOrchestrator
from modulos.aprendiz_de_padroes import AprendizDePadroes
from collections import Counter


class AutoAprendizado:
    """Quando reconstrução falha, usa ferramentas para aprender e salvar no KG."""
    
    def __init__(self):
        self.pe = PatternEngine()
        self.kg = KnowledgeGraph()
        self.aprendiz = AprendizDePadroes(pe=self.pe, kg=self.kg)
        self.ie = IntentionEngine(pe=self.pe)
        self.tools = ToolOrchestrator()
        
        self.termos_usados = []
        self.fontes_usadas = []
        self.lessons_salvas = 0
    
    def ciclo_completo(self, pergunta):
        """Tenta reconstruir. Se falhar, aprende. Tenta de novo.
        
        Returns:
            (status, resposta, tempo, fontes_usadas)
            status: 'RECONSTRUIDA' | 'RECONSTRUIDA_APOS_APRENDER' | 'FALHA'
        """
        print(f"\n{'='*70}")
        print(f"  PERGUNTA: {pergunta}")
        print(f"{'='*70}")
        
        t0 = _time.time()
        
        # 1. Tokeniza + IE
        tokens = self.pe.tokenizar_universal(pergunta)
        fp = self.pe.fingerprint(tokens) if tokens else []
        intencoes = self.ie.detectar(pergunta)
        
        if intencoes:
            cat, params, conf = intencoes[0]
            print(f"  IE: {cat}/{params.get('tipo','?')} (conf={conf:.3f})")
        print(f"  Fingerprint: {[round(x,2) for x in fp[:4]]}...")
        
        # 2. PRIMEIRA TENTATIVA de reconstrução
        print(f"\n  --- Tentativa 1: Reconstruir ---")
        resposta = self.aprendiz.reconstruir_resposta(fp, intencoes[0] if intencoes else None, tokens)
        
        if resposta and len(resposta) > 30:
            tempo = _time.time() - t0
            print(f"  ✅ RECONSTRUÍDA de primeira ({len(resposta)} chars, {tempo:.4f}s)")
            return ("RECONSTRUIDA", resposta, round(tempo, 4), [])
        
        # 3. FALHOU → AUTO-APRENDIZADO
        print(f"  ❌ Reconstrução falhou. Disparando auto-aprendizado...")
        
        fontes_aprendidas = self._aprender_para_fingerprint(fp, pergunta, intencoes[0] if intencoes else None)
        
        # 4. SEGUNDA TENTATIVA de reconstrução
        print(f"\n  --- Tentativa 2: Reconstruir (após aprendizado) ---")
        resposta2 = self.aprendiz.reconstruir_resposta(fp, intencoes[0] if intencoes else None, tokens)
        
        tempo = _time.time() - t0
        
        if resposta2 and len(resposta2) > 30:
            print(f"  ✅ RECONSTRUÍDA após aprender ({len(resposta2)} chars, {tempo:.4f}s)")
            return ("RECONSTRUIDA_APOS_APRENDER", resposta2, round(tempo, 4), fontes_aprendidas)
        
        print(f"  ❌ Ainda falhou após aprendizado. LLM precisa assumir.")
        return ("FALHA", None, round(tempo, 4), fontes_aprendidas)
    
    def _aprender_para_fingerprint(self, fingerprint, pergunta, intencao=None):
        """Usa ferramentas para aprender dados e salvar com fingerprint.
        
        Returns:
            list: fontes que conseguiram dados
        """
        # 1. EXTRAI TERMOS da pergunta
        tokens = self.pe.tokenizar_universal(pergunta)
        termos = []
        for t in tokens:
            tipo = t[0]
            if tipo.startswith('DOM_') or tipo == 'PROPER_NOUN':
                termos.append(t[1])
        
        # Fallback: palavras com 4+ chars
        if not termos:
            termos = [p.lower() for p in pergunta.split() if len(p) > 3][:3]
        
        # Remove duplicatas mantendo ordem
        termos = list(dict.fromkeys(termos))
        print(f"  Termos extraídos: {termos}")
        self.termos_usados.extend(termos)
        
        # 2. PARA CADA TERMO, busca em MÚLTIPLAS FONTES
        dados_encontrados = []  # [(fonte, termo, dados)]
        
        for termo in termos[:3]:
            if not termo or len(termo) < 2:
                continue
            
            # Fonte A: KNOWLEDGE GRAPH (definições conceituais)
            try:
                lessons = self.kg.buscar(termo, max_r=3)
                if lessons:
                    textos = '\n'.join(l.get('solucao', '') for l in lessons)
                    if textos and len(textos) > 20:
                        dados_encontrados.append(('kg', termo, textos[:1500]))
                        print(f"    [KG] {termo}: {len(textos)} chars")
            except Exception as e:
                print(f"    [KG] {termo}: erro - {e}")
            
            # Fonte B: BUSCA ESTRATÉGICA LOCAL (paths, arquivos)
            try:
                r = self.tools.executar('buscar_estrategico', {'termo': termo})
                if r and r.get('sucesso'):
                    dados = str(r.get('resultado', ''))
                    if dados and 'Nenhum' not in dados and len(dados) > 30:
                        dados_encontrados.append(('estrategico', termo, dados[:1500]))
                        print(f"    [Busca] {termo}: {len(dados)} chars")
            except Exception as e:
                print(f"    [Busca] {termo}: erro - {e}")
        
        # 3. SALVA TUDO no KG com fingerprint da PERGUNTA
        salvos = 0
        fontes_ativas = []
        
        for fonte, termo, dados in dados_encontrados:
            fontes_ativas.append(fonte)
            
            # Tokeniza os dados → extrai tipos_markov
            try:
                tokens_dados = self.pe.tokenizar_universal(dados)
                tipos_markov = None
                if tokens_dados:
                    tipos_lista = [t[0] for t in tokens_dados]
                    tm = {}
                    for i in range(len(tipos_lista) - 1):
                        t1, t2 = tipos_lista[i], tipos_lista[i + 1]
                        if t1 not in tm: tm[t1] = {}
                        tm[t1][t2] = tm[t1].get(t2, 0) + 1
                    for t in tm:
                        s = sum(tm[t].values())
                        for p in tm[t]:
                            tm[t][p] = round(tm[t][p] / s, 3) if s else 0
                    tipos_markov = tm
                
                # Salva no KG (fingerprint = fingerprint da PERGUNTA)
                self.kg.aprender(
                    erro=f"auto_aprendizado: {pergunta[:80]}",
                    causa=f"fonte={fonte}, termo={termo}",
                    solucao=dados[:500],
                    ctx='aprendido_auto',
                    fingerprint=fingerprint,
                    tipos_markov=tipos_markov,
                )
                salvos += 1
            except Exception as e:
                print(f"    Erro ao salvar: {e}")
        
        self.fontes_usadas.extend(fontes_ativas)
        self.lessons_salvas += salvos
        
        print(f"  → {salvos} lessons salvas no KG com fingerprint da pergunta")
        return fontes_ativas


def testar():
    print("=" * 70)
    print("  PROTÓTIPO: AUTO-APRENDIZADO POR INSUCESSO")
    print("  Falha → Aprende → Reconstroi")
    print("=" * 70)
    
    auto = AutoAprendizado()
    
    perguntas = [
        "Explique o sistema SPA do MCR",
        "Crie um NPC ferreiro em Eridanus",
        "O que e Canary no contexto do MCR?",
    ]
    
    resultados = []
    
    for pergunta in perguntas:
        status, resposta, tempo, fontes = auto.ciclo_completo(pergunta)
        
        resultados.append({
            'pergunta': pergunta[:50],
            'status': status,
            'tempo': tempo,
            'tamanho': len(resposta) if resposta else 0,
            'fontes': fontes,
        })
        
        if resposta and len(resposta) > 30:
            print(f"\n  Resposta: {resposta[:200]}...")
    
    # RELATÓRIO
    print(f"\n\n{'='*70}")
    print(f"  RELATÓRIO FINAL")
    print(f"{'='*70}")
    
    for r in resultados:
        status_icon = "✅" if 'RECONSTRUIDA' in r['status'] else "❌"
        print(f"\n  {status_icon} {r['pergunta']}")
        print(f"     Status: {r['status']}")
        print(f"     Tempo: {r['tempo']:.4f}s")
        print(f"     Tamanho: {r['tamanho']} chars")
        if r.get('fontes'):
            print(f"     Fontes usadas: {r['fontes']}")
    
    print(f"\n  Lessons salvas: {auto.lessons_salvas}")
    print(f"  Termos usados: {list(dict.fromkeys(auto.termos_usados))}")
    
    # KG stats
    licoes = auto.kg._get_licoes()
    com_fp = [l for l in licoes if l.get('fingerprint')]
    com_auto = [l for l in licoes if l.get('ctx') == 'aprendido_auto']
    print(f"\n  KG: {len(licoes)} lessons, {len(com_fp)} com fingerprint, {len(com_auto)} auto-aprendidas")
    
    print(f"\n{'='*70}")
    print(f"  PROTÓTIPO CONCLUÍDO")
    print(f"  Ciclo: falha → aprende → reconstroi → {sum(1 for r in resultados if 'RECONSTRUIDA' in r['status'])}/{len(resultados)}")
    print(f"{'='*70}")


if __name__ == '__main__':
    testar()
