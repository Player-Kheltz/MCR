#!/usr/bin/env python3
"""PROTÓTIPO: Blocos Dinâmicos — zero LLM. Ciclo completo com ferramentas."""
import sys, os, re, json, time as _time
from collections import Counter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.kg import KnowledgeGraph
from modulos.aprendiz_de_padroes import AprendizDePadroes
from modulos.intention_engine import IntentionEngine
from modulos.tool_orchestrator import ToolOrchestrator

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class PrototipoBlocos:
    def __init__(self):
        self.pe = PatternEngine()
        self.kg = KnowledgeGraph()
        self.ap = AprendizDePadroes(pe=self.pe, kg=self.kg)
        self.ie = IntentionEngine(pe=self.pe)
        self.tools = ToolOrchestrator()
        self.resultados = []

    def _extrair_termos(self, pergunta, tokens):
        termos = []
        for t in tokens:
            if t[0].startswith('DOM_') or t[0] == 'PROPER_NOUN':
                if t[1] not in termos: termos.append(t[1])
        if not termos:
            termos = [p for p in pergunta.split() if len(p) > 3][:3]
        return termos

    def _buscar_arquivos(self, termo):
        """Busca arquivos contendo o termo. Retorna lista de caminhos."""
        try:
            r = self.tools.executar('buscar_estrategico', {'termo': termo})
            if not r or not r.get('sucesso'):
                return []
            dados = str(r.get('resultado', ''))
            if not dados or 'Nenhum' in dados:
                return []
            ext_validas = ('.md', '.lua', '.py', '.txt', '.json')
            arquivos = []
            for linha in dados.split('\n'):
                l = linha.strip()
                if l.endswith(ext_validas) and not l.startswith('['):
                    arquivos.append(l)
            arquivos.sort(key=lambda x: (0 if x.startswith('docs') and x.endswith('.md') else 1))
            return arquivos
        except:
            return []

    def _extrair_fragmento(self, termo, caminho):
        """Tenta extrair fragmento contextual de um arquivo."""
        try:
            r = self.tools.executar('ler_arquivo', {'caminho': caminho})
            if not r or not r.get('sucesso'):
                return None
            return self.ap.extrair_contexto(termo, caminho, modulo=5, max_modulo=50)
        except:
            return None

    def processar(self, pergunta):
        print(f"\n{'='*70}")
        print(f"  PERGUNTA: {pergunta}")
        print(f"{'='*70}")
        t0 = _time.time()

        # 1. Tokeniza
        tokens = self.pe.tokenizar_universal(pergunta)
        fp = self.pe.fingerprint(tokens) if tokens else []
        intencoes = self.ie.detectar(pergunta)
        cat = intencoes[0][0] if intencoes else "GERAL"
        print(f"  IE: {cat} | FP: {[round(x,2) for x in fp[:4]]}...")

        # 2. Extrai termos
        termos = self._extrair_termos(pergunta, tokens)
        print(f"  Termos: {termos}")

        # 3. Busca fragmentos para cada termo
        fragmentos = []
        for termo in termos[:2]:
            print(f"\n  --- '{termo}' ---")
            
            # Tenta docs/ primeiro
            docs_tentados = ["docs/MCR_IDENTITY.md", "docs/MANIFEST.md", f"docs/{termo}.md"]
            for doc_path in docs_tentados:
                full_path = os.path.join(BASE, doc_path)
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                        conteudo = f.read()
                    if termo.lower() in conteudo.lower():
                        frag = self._extrair_fragmento(termo, doc_path)
                        if frag:
                            score = self.ap._avaliar_coerencia(frag)
                            if score >= 0.5:
                                fragmentos.append({'termo': termo, 'fragmento': frag, 'score': score, 'arquivo': doc_path})
                                print(f"    ✅ Fragmento docs ({score:.2f}): {frag[:80]}...")
                                break

            # Se não achou em docs, tenta buscar_estrategico
            if not any(f['termo'] == termo for f in fragmentos):
                arquivos = self._buscar_arquivos(termo)
                print(f"    Arquivos encontrados: {len(arquivos)}")
                for caminho in arquivos[:5]:
                    frag = self._extrair_fragmento(termo, caminho)
                    if frag:
                        score = self.ap._avaliar_coerencia(frag)
                        if score >= 0.5:
                            fragmentos.append({'termo': termo, 'fragmento': frag, 'score': score, 'arquivo': caminho})
                            print(f"    ✅ Fragmento ({score:.2f}): {frag[:80]}...")
                            break

        # 4. Aprende fragmentos como blocos
        for frag in fragmentos:
            self.ap.aprender_fragmento(frag['fragmento'], fp, pergunta=pergunta, nota=int(frag['score'] * 10))
        print(f"\n  Blocos aprendidos: {len(fragmentos)}")

        # 5. Tenta reconstruir com blocos
        resposta = self.ap.reconstruir_com_blocos(fp, pergunta=pergunta, tokens_input=tokens)
        tempo = _time.time() - t0

        if resposta and len(resposta) > 20:
            print(f"\n  ✅ RECONSTRUÍDA ({len(resposta)} chars, {tempo:.2f}s, 0 LLM)")
            print(f"     {resposta[:200]}")
        else:
            print(f"\n  ❌ Nao reconstruida ({tempo:.2f}s)")

        self.resultados.append({
            'pergunta': pergunta[:50],
            'termos': termos,
            'fragmentos': len(fragmentos),
            'reconstruida': resposta is not None and len(resposta) > 20 if resposta else False,
            'tamanho': len(resposta) if resposta else 0,
            'tempo': round(tempo, 2),
            'resposta': resposta[:200] if resposta else '',
        })

    def relatorio(self):
        print(f"\n\n{'='*70}")
        print(f"  RELATÓRIO FINAL")
        print(f"{'='*70}")
        for r in self.resultados:
            status = "✅" if r['reconstruida'] else "❌"
            print(f"\n  {status} {r['pergunta']}")
            print(f"     Termos: {r['termos']} | Fragmentos: {r['fragmentos']} | Tam: {r['tamanho']} | Tempo: {r['tempo']}s")
        total = sum(1 for r in self.resultados if r['reconstruida'])
        print(f"\n  Total: {total}/{len(self.resultados)} reconstruídas (0 LLM)")
        blocos_kg = len([l for l in self.kg._get_licoes() if l.get('ctx') == 'bloco_aprendido'])
        print(f"  Blocos no KG: {blocos_kg}")


if __name__ == '__main__':
    print("=" * 70)
    print("  BLOCOS DINÂMICOS (0 LLM)")
    print("  Ciclo: termo → docs → fragmento → aprender → bloco → reconstruir")
    print("=" * 70)
    p = PrototipoBlocos()
    for q in ["Explique o sistema SPA do MCR", "O que e Canary no contexto do MCR?"]:
        p.processar(q)
    p.relatorio()
